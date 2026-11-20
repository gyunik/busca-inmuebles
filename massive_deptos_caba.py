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

# Lista ampliada de los 25 barrios que concentran el 90% de los departamentos de CABA
BARRIOS_CABA_DEPTOS = [
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
    'puerto-madero',
    'barracas',
    'monserrat',
    'coghlan',
    'chacarita',
    'villa-del-parque',
    'villa-devoto',
    'floresta',
    'boedo',
    'san-cristobal',
    'parque-patricios'
]

async def sweep_all_caba_deptos():
    start_time = time.time()
    print("=" * 75)
    print("   ESCALADO MASIVO DE DEPARTAMENTOS CABA (VENTANA 15 DÍAS)")
    print(f"   Barrios auditados: {len(BARRIOS_CABA_DEPTOS)} barrios")
    print("   Meta: Incorporar miles de departamentos para equilibrar la realidad de CABA")
    print("=" * 75 + "\n")
    
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    ml = MercadoLibreScraper()
    
    total_saved_all = 0
    
    # 1. DEPARTAMENTOS EN VENTA (Barrio por Barrio, 6 páginas cada uno = ~288 deptos/barrio)
    print("[1/2] Extrayendo DEPARTAMENTOS EN VENTA por Barrio...")
    for i, barrio in enumerate(BARRIOS_CABA_DEPTOS, 1):
        zone_slug = f"capital-federal/{barrio}"
        try:
            print(f"  [{i}/{len(BARRIOS_CABA_DEPTOS)}] Venta en {barrio.upper()} (hasta 6 págs)...", end=" ", flush=True)
            res = await ml.scrape(
                property_type="departamento",
                zone=zone_slug,
                max_pages=6,
                operation_type="venta"
            )
            saved = save_scraped_items(db, res)
            total_saved_all += saved
            print(f"Recolectados: {len(res)} | Nuevos en DB: {saved}")
            await asyncio.sleep(0.4)
        except Exception as e:
            print(f"Error: {e}")
            
    # 2. DEPARTAMENTOS EN ALQUILER (Top 15 Barrios con más alquileres, 4 páginas cada uno)
    print("\n[2/2] Extrayendo DEPARTAMENTOS EN ALQUILER por Barrio...")
    for i, barrio in enumerate(BARRIOS_CABA_DEPTOS[:15], 1):
        zone_slug = f"capital-federal/{barrio}"
        try:
            print(f"  [{i}/15] Alquiler en {barrio.upper()} (hasta 4 págs)...", end=" ", flush=True)
            res = await ml.scrape(
                property_type="departamento",
                zone=zone_slug,
                max_pages=4,
                operation_type="alquiler"
            )
            saved = save_scraped_items(db, res)
            total_saved_all += saved
            print(f"Recolectados: {len(res)} | Nuevos en DB: {saved}")
            await asyncio.sleep(0.4)
        except Exception as e:
            print(f"Error: {e}")
            
    print("\n" + "-" * 75)
    print(f"Total departamentos nuevos agregados a la base: {total_saved_all}")
    
    print("Ejecutando consolidación y deduplicación inteligente...")
    clusters = run_deduplication(db)
    print(f"Clusters consolidados de duplicados: {clusters}")
    
    total_db = db.query(Property).count()
    deptos_db = db.query(Property).filter(Property.property_type == 'departamento').count()
    phs_db = db.query(Property).filter(Property.property_type == 'ph').count()
    casas_db = db.query(Property).filter(Property.property_type == 'casa').count()
    alquiler_db = db.query(Property).filter(Property.operation_type == 'alquiler').count()
    venta_db = db.query(Property).filter(Property.operation_type == 'venta').count()
    
    elapsed = round(time.time() - start_time, 1)
    print("\n" + "=" * 75)
    print(f"   NUEVA ESTRUCTURA DE LA BASE DE DATOS CABA ({elapsed} segs)")
    print(f"   Total Inmuebles en DB: {total_db}")
    print(f"     • Departamentos: {deptos_db} ({round(deptos_db/total_db*100, 1)}%)")
    print(f"     • PHs: {phs_db} ({round(phs_db/total_db*100, 1)}%)")
    print(f"     • Casas: {casas_db} ({round(casas_db/total_db*100, 1)}%)")
    print(f"     • Operaciones -> Venta: {venta_db} | Alquiler: {alquiler_db}")
    print("=" * 75)
    
    db.close()

if __name__ == '__main__':
    asyncio.run(sweep_all_caba_deptos())
