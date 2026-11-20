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
from backend.app.scrapers.argenprop_scraper import ArgenpropScraper
from backend.app.services.scraper_runner import save_scraped_items
from backend.app.services.deduplication_service import run_deduplication

async def run_caba_sweep():
    start_time = time.time()
    print("=" * 65)
    print("   BARRIDO QUIRÚRGICO DE ALTA VELOCIDAD - CABA")
    print("   Tipos: PH, Casas, Departamentos")
    print("   Operaciones: Venta y Alquiler")
    print("   Portales activos: Mercado Libre + Argenprop (Más Recientes)")
    print("=" * 65 + "\n")
    
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    ml = MercadoLibreScraper()
    ap = ArgenpropScraper()
    
    total_batch = []
    
    # Matriz quirúrgica CABA: (Tipo Inmueble, Operación, Páginas)
    # Cubrimos toda la oferta nueva sin generar cientos de peticiones innecesarias
    caba_matrix = [
        # 1. PHs (La joya escasa - Máxima prioridad)
        ('ph', 'venta', 2),
        ('ph', 'alquiler', 2),
        
        # 2. Departamentos (Mayor volumen - Más recientes)
        ('departamentos', 'venta', 2),
        ('departamentos', 'alquiler', 2),
        
        # 3. Casas (Pocas en CABA - Cubiertas en 2 páginas)
        ('casas', 'venta', 2),
        ('casas', 'alquiler', 2),
    ]
    
    # -------------------------------------------------------------
    # 1. MERCADO LIBRE CABA (Venta + Alquiler)
    # -------------------------------------------------------------
    print("[1/2] Extrayendo de Mercado Libre (CABA - Novedades)...")
    for ptype, op, pages in caba_matrix:
        try:
            print(f"  -> ML {ptype.upper()} ({op.upper()}) [hasta {pages} págs]...", end=" ", flush=True)
            res = await ml.scrape(property_type=ptype, zone="capital-federal", max_pages=pages, operation_type=op)
            print(f"Obtenidos: {len(res)}")
            total_batch.extend(res)
            await asyncio.sleep(0.4)
        except Exception as e:
            print(f"Error: {e}")
            
    # -------------------------------------------------------------
    # 2. ARGENPROP CABA (Venta + Alquiler - Orden Más Nuevos)
    # -------------------------------------------------------------
    print("\n[2/2] Extrayendo de Argenprop (CABA - Novedades ordenadas)...")
    for ptype, op, pages in caba_matrix:
        try:
            print(f"  -> AP {ptype.upper()} ({op.upper()}) [hasta {pages} págs]...", end=" ", flush=True)
            res = await ap.scrape(property_type=ptype, zone="capital-federal", max_pages=pages, operation_type=op)
            print(f"Obtenidos: {len(res)}")
            total_batch.extend(res)
            await asyncio.sleep(0.8)
        except Exception as e:
            print(f"Error: {e}")
            
    # -------------------------------------------------------------
    # PERSISTENCIA, HISTORIAL Y DEDUPLICACIÓN
    # -------------------------------------------------------------
    print("\n" + "-" * 65)
    print(f"Total avisos recolectados en el ciclo: {len(total_batch)}")
    
    saved = save_scraped_items(db, total_batch)
    print(f"Propiedades nuevas incorporadas a la base: {saved}")
    
    print("Ejecutando algoritmo de deduplicación cruzada entre portales...")
    clusters = run_deduplication(db)
    print(f"Clusters consolidados de inmuebles duplicados: {clusters}")
    
    total_db = db.query(Property).count()
    total_ph = db.query(Property).filter(Property.property_type == 'ph').count()
    total_deptos = db.query(Property).filter(Property.property_type == 'departamento').count()
    total_casas = db.query(Property).filter(Property.property_type == 'casa').count()
    total_alquiler = db.query(Property).filter(Property.operation_type == 'alquiler').count()
    total_venta = db.query(Property).filter(Property.operation_type == 'venta').count()
    
    elapsed = round(time.time() - start_time, 1)
    print("\n" + "=" * 65)
    print(f"   RESUMEN FINAL DE LA BASE DE DATOS ({elapsed} segs)")
    print(f"   Total Inmuebles en DB: {total_db}")
    print(f"     • Venta: {total_venta} | Alquiler: {total_alquiler}")
    print(f"     • Departamentos: {total_deptos} | PHs: {total_ph} | Casas: {total_casas}")
    print("=" * 65)
    
    db.close()

if __name__ == '__main__':
    asyncio.run(run_caba_sweep())
