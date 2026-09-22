import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import asyncio
import re
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
import httpx
from bs4 import BeautifulSoup
from backend.app.services.locations_catalog import match_neighborhood
from backend.app.services.deduplication_service import run_deduplication
from backend.app.core.database import SessionLocal
from backend.app.models.property_model import Property, PriceHistory
from backend.app.services.scraper_runner import SCRAPERS, save_scraped_items

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "es-419,es;q=0.9,en;q=0.8",
}

TARGET_NEIGHBORHOODS = ["Parque Chas", "Villa Urquiza", "Villa del Parque"]
MAX_PRICE_USD = 160000

async def verify_listing_active(client: httpx.AsyncClient, prop_id: int, portal: str, url: str, old_price: float) -> Tuple[int, str, Optional[float], str]:
    """
    Returns (prop_id, status ['active', 'inactive', 'price_changed'], new_price, reason)
    """
    try:
        resp = await client.get(url, timeout=12.0)
        
        if resp.status_code == 404:
            return prop_id, "inactive", None, "HTTP 404 (Página eliminada)"
        if resp.status_code >= 400:
            return prop_id, "inactive", None, f"HTTP {resp.status_code}"
            
        final_url = str(resp.url)
        html = resp.text.lower()
        
        # Inactive patterns per portal
        if portal == "mercadolibre":
            if "publicación finalizada" in html or "publicacion finalizada" in html:
                return prop_id, "inactive", None, "Publicación finalizada"
            if "publicación pausada" in html or "publicacion pausada" in html:
                return prop_id, "inactive", None, "Publicación pausada"
            if "no encontramos publicaciones" in html or ("inmuebles.mercadolibre.com.ar/ph/" in final_url and "_JM" not in final_url):
                return prop_id, "inactive", None, "Redirigido a listado general (aviso dado de baja)"
                
            price_match = re.search(r'data-price="(\d+)"', resp.text)
            if not price_match:
                price_match = re.search(r'"price":\s*(\d+)', resp.text)
            if price_match:
                current_price = float(price_match.group(1))
                if current_price != old_price:
                    return prop_id, "price_changed", current_price, f"Precio actualizado: USD {old_price} -> USD {current_price}"

        elif portal == "zonaprop":
            if "aviso no disponible" in html or "ya no está disponible" in html or "no esta disponible" in html or "aviso finalizado" in html:
                return prop_id, "inactive", None, "Aviso no disponible en Zonaprop"
            if "/propiedades/" not in final_url:
                return prop_id, "inactive", None, "Redirigido a home/búsqueda"
                
        elif portal == "argenprop":
            if "aviso no disponible" in html or "propiedad no disponible" in html or "la publicación no existe" in html:
                return prop_id, "inactive", None, "Aviso no disponible en Argenprop"

        return prop_id, "active", old_price, "Activo"

    except Exception as e:
        return prop_id, "active", old_price, f"Nota de red: {str(e)[:40]}"

async def run_verification_and_sweep():
    print("=" * 60)
    print("Iniciando Verificacion y Barrido de PHs:")
    print("Barrios: Parque Chas, Villa Urquiza, Villa del Parque")
    print("Rango: <= USD 160.000 | Portales: MercadoLibre, Argenprop, Zonaprop, Properati, Mudafy")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # 1. Obtener los PHs actuales en esos 3 barrios
        existing_phs = db.query(Property).filter(
            Property.neighborhood.in_(TARGET_NEIGHBORHOODS),
            Property.property_type.ilike("%ph%"),
            Property.price_usd <= MAX_PRICE_USD
        ).all()
        
        print(f"\n[PASO 1] Verificando estado en vivo de los {len(existing_phs)} PHs en base de datos...")
        
        active_count = 0
        inactive_items = []
        price_updates = []
        
        limits = httpx.Limits(max_keepalive_connections=20, max_connections=30)
        async with httpx.AsyncClient(headers=HEADERS, limits=limits, verify=False, follow_redirects=True) as client:
            tasks = [
                verify_listing_active(client, p.id, p.portal, p.url, p.price_usd)
                for p in existing_phs
            ]
            results = await asyncio.gather(*tasks)
            
            for prop_id, status, new_val, reason in results:
                if status == "inactive":
                    inactive_items.append((prop_id, reason))
                elif status == "price_changed":
                    price_updates.append((prop_id, new_val))
                    active_count += 1
                else:
                    active_count += 1
                    
        print(f" -> Confirmados activos: {active_count}")
        print(f" -> Dados de baja / inactivos a depurar: {len(inactive_items)}")
        print(f" -> Precios actualizados en vivo: {len(price_updates)}")
        
        # Eliminar inactivos de la base
        deleted_details = []
        if inactive_items:
            for pid, reason in inactive_items:
                prop = db.query(Property).filter(Property.id == pid).first()
                if prop:
                    detail = f"[{prop.portal.upper()}] USD {prop.price_usd:,.0f} - {prop.neighborhood}: {prop.title[:40]} ({reason})"
                    deleted_details.append(detail)
                    print(f"   [-] Eliminando ID {pid}: {detail}")
                    db.query(PriceHistory).filter(PriceHistory.property_id == pid).delete()
                    db.delete(prop)
            db.commit()
            
        # Actualizar precios cambiados
        for pid, new_price in price_updates:
            prop = db.query(Property).filter(Property.id == pid).first()
            if prop and new_price:
                history = PriceHistory(
                    property_id=prop.id,
                    price_usd=prop.price_usd,
                    recorded_at=datetime.utcnow()
                )
                db.add(history)
                prop.price_usd = new_price
                if prop.total_area_m2 and prop.total_area_m2 > 0:
                    prop.price_per_m2 = round(new_price / prop.total_area_m2, 1)
                prop.updated_at = datetime.utcnow()
                print(f"   [*] Precio actualizado ID {pid}: Nuevo valor USD {new_price:,.0f}")
        db.commit()
        
        # [PASO 2] Barrido de nuevos PHs en los portales
        print(f"\n[PASO 2] Ejecutando barrido en vivo en portales inmobiliarios...")
        new_scraped_items = []
        
        for name, scraper in SCRAPERS.items():
            print(f" -> Consultando {name.upper()}...")
            try:
                # Scrape PHs in Capital Federal
                res = await scraper.scrape(property_type="ph", zone="capital-federal", max_pages=3)
                # Filter only relevant neighborhoods and price
                filtered = [
                    item for item in res 
                    if item.get("neighborhood") in TARGET_NEIGHBORHOODS 
                    and (item.get("price_usd") or 0) <= MAX_PRICE_USD
                ]
                new_scraped_items.extend(filtered)
                print(f"    Encontradas {len(res)} publicaciones totales ({len(filtered)} en barrios objetivo <= 160k)")
            except Exception as e:
                print(f"    Error en {name}: {e}")
                
        # Guardar nuevos items
        saved_count = save_scraped_items(db, new_scraped_items)
        print(f" -> Nuevas publicaciones incorporadas a la base: {saved_count}")
        
        # [PASO 3] Deduplicación y agrupación de ofertas cruzadas
        print(f"\n[PASO 3] Recalculando clusters de duplicados y mejores precios...")
        clusters = run_deduplication(db)
        print(f" -> Grupos de duplicados activos: {clusters}")
        
        # Resumen final por barrio
        print("\n" + "=" * 60)
        print("ESTADO FINAL DE LA BASE DE DATOS (PHs <= USD 160.000):")
        print("=" * 60)
        
        for n in TARGET_NEIGHBORHOODS:
            count = db.query(Property).filter(
                Property.neighborhood == n,
                Property.property_type.ilike("%ph%"),
                Property.price_usd <= MAX_PRICE_USD
            ).count()
            print(f" * {n}: {count} PHs activos")
            
        total_final = db.query(Property).filter(
            Property.neighborhood.in_(TARGET_NEIGHBORHOODS),
            Property.property_type.ilike("%ph%"),
            Property.price_usd <= MAX_PRICE_USD
        ).count()
        print(f"\nTOTAL PHs ACTIVOS Y VERIFICADOS: {total_final}")
        print("=" * 60)
        
        return {
            "verified_active": active_count,
            "deleted_inactive": len(inactive_items),
            "deleted_details": deleted_details,
            "price_updates": len(price_updates),
            "new_saved": saved_count,
            "total_active": total_final
        }
        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(run_verification_and_sweep())
