import asyncio
import os
import sys
import time
from datetime import datetime

# Ensure root path is accessible
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.app.core.database import SessionLocal, Base, engine
from backend.app.models.property_model import Property
from backend.app.scrapers.mercadolibre_scraper import MercadoLibreScraper
from backend.app.services.scraper_runner import save_scraped_items
from backend.app.services.deduplication_service import run_deduplication

# Los 15 barrios con más oferta y demanda de departamentos en CABA
TOP_BARRIOS_CABA = [
    'palermo',
    'belgrano',
    'caballito',
    'recoleta',
    'almagro',
    'villa-urquiza',
    'villa-crespo',
    'nunez',
    'barrio-norte',
    'flores',
    'san-telmo',
    'colegiales',
    'saavedra',
    'balvanera',
    'puerto-madero'
]

async def sweep_deptos_by_neighborhood(pages_per_barrio: int = 5):
    start_time = time.time()
    print("=" * 70)
    print("   BARRIDO MASIVO DE DEPARTAMENTOS POR BARRIO (CABA)")
    print(f"   Objetivo: Escalar departamentos en los {len(TOP_BARRIOS_CABA)} barrios clave")
    print(f"   Profundidad: {pages_per_barrio} páginas por barrio (~240 deptos/barrio)")
    print("=" * 70 + "\n")
    
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    ml = MercadoLibreScraper()
    
    total_deptos = []
    
    # 1. Ventas por Barrio
    print("[1/2] Extrayendo DEPARTAMENTOS EN VENTA por Barrio...")
    for barrio in TOP_BARRIOS_CABA:
        zone_slug = f"capital-federal/{barrio}"
        try:
            print(f"  -> Venta en {barrio.upper()}...", end=" ", flush=True)
            res = await ml.scrape(
                property_type="departamento",
                zone=zone_slug,
                max_pages=pages_per_barrio,
                operation_type="venta"
            )
            print(f"Obtenidos: {len(res)}")
            total_deptos.extend(res)
            await asyncio.sleep(0.4)
        except Exception as e:
            print(f"Error: {e}")
            
    # 2. Alquileres por Barrio
    print("\n[2/2] Extrayendo DEPARTAMENTOS EN ALQUILER por Barrio...")
    for barrio in TOP_BARRIOS_CABA[:10]: # Top 10 alquileres
        zone_slug = f"capital-federal/{barrio}"
        try:
            print(f"  -> Alquiler en {barrio.upper()}...", end=" ", flush=True)
            res = await ml.scrape(
                property_type="departamento",
                zone=zone_slug,
                max_pages=3,
                operation_type="alquiler"
            )
            print(f"Obtenidos: {len(res)}")
            total_deptos.extend(res)
            await asyncio.sleep(0.4)
        except Exception as e:
            print(f"Error: {e}")
            
    # Persistencia
    print("\n" + "-" * 70)
    print(f"Total avisos de departamentos recolectados: {len(total_deptos)}")
    
    saved = save_scraped_items(db, total_deptos)
    print(f"Nuevos departamentos incorporados a la base: {saved}")
    
    print("Ejecutando deduplicador inteligente...")
    clusters = run_deduplication(db)
    print(f"Clusters consolidados: {clusters}")
    
    # Métricas finales
    total_db = db.query(Property).count()
    deptos_db = db.query(Property).filter(Property.property_type == 'departamento').count()
    phs_db = db.query(Property).filter(Property.property_type == 'ph').count()
    casas_db = db.query(Property).filter(Property.property_type == 'casa').count()
    
    elapsed = round(time.time() - start_time, 1)
    print("\n" + "=" * 70)
    print(f"   ESTRUCTURA ACTUALIZADA DE LA BASE DE DATOS ({elapsed} segs)")
    print(f"   Total Inmuebles: {total_db}")
    print(f"     • Departamentos: {deptos_db} ({round(deptos_db/total_db*100, 1)}%)")
    print(f"     • PHs: {phs_db} ({round(phs_db/total_db*100, 1)}%)")
    print(f"     • Casas: {casas_db} ({round(casas_db/total_db*100, 1)}%)")
    print("=" * 70)
    
    db.close()

if __name__ == '__main__':
    asyncio.run(sweep_deptos_by_neighborhood(pages_per_barrio=4))
