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

async def run_caba_15days_sweep():
    start_time = time.time()
    print("=" * 70)
    print("   BARRIDO QUIRÚRGICO CABA: VENTANA ÚLTIMOS 15 DÍAS")
    print("   Tipologías: Departamentos, PHs, Casas")
    print("   Operaciones: Venta y Alquiler")
    print("   Portales: Mercado Libre + Argenprop (Ordenados por Más Nuevos)")
    print("=" * 70 + "\n")
    
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    ml = MercadoLibreScraper()
    ap = ArgenpropScraper()
    
    total_batch = []
    
    # Matriz para cubrir la ventana de los últimos 15 días:
    # 1. Departamentos: ~8 páginas en ML (380 avisos) y ~6 páginas en AP (120 avisos)
    # 2. PHs: ~6 páginas en ML (280 avisos) y ~5 páginas en AP (100 avisos)
    # 3. Casas: ~4 páginas en ML (190 avisos) y ~4 páginas en AP (80 avisos)
    matrix_targets = [
        # (Tipo, Operación, Páginas ML, Páginas AP)
        ('departamentos', 'venta', 8, 6),
        ('departamentos', 'alquiler', 8, 6),
        ('ph', 'venta', 6, 5),
        ('ph', 'alquiler', 5, 4),
        ('casas', 'venta', 4, 4),
        ('casas', 'alquiler', 4, 4),
    ]
    
    # -------------------------------------------------------------
    # 1. MERCADO LIBRE CABA (Últimos 15 Días)
    # -------------------------------------------------------------
    print("[1/2] Extrayendo de Mercado Libre CABA (Ordenados por Más Recientes)...")
    for ptype, op, ml_pages, _ in matrix_targets:
        try:
            print(f"  -> ML {ptype.upper()} ({op.upper()}) [{ml_pages} págs]...", end=" ", flush=True)
            res = await ml.scrape(
                property_type=ptype, 
                zone="capital-federal", 
                max_pages=ml_pages, 
                operation_type=op
            )
            print(f"Obtenidos: {len(res)}")
            total_batch.extend(res)
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"Error: {e}")
            
    # -------------------------------------------------------------
    # 2. ARGENPROP CABA (Últimos 15 Días)
    # -------------------------------------------------------------
    print("\n[2/2] Extrayendo de Argenprop CABA (Ordenados por Más Recientes)...")
    for ptype, op, _, ap_pages in matrix_targets:
        try:
            print(f"  -> AP {ptype.upper()} ({op.upper()}) [{ap_pages} págs]...", end=" ", flush=True)
            res = await ap.scrape(
                property_type=ptype, 
                zone="capital-federal", 
                max_pages=ap_pages, 
                operation_type=op
            )
            print(f"Obtenidos: {len(res)}")
            total_batch.extend(res)
            await asyncio.sleep(0.8)
        except Exception as e:
            print(f"Error: {e}")
            
    # -------------------------------------------------------------
    # PERSISTENCIA, HISTORIAL Y DEDUPLICACIÓN
    # -------------------------------------------------------------
    print("\n" + "-" * 70)
    print(f"Total avisos recolectados en esta ventana: {len(total_batch)}")
    
    saved = save_scraped_items(db, total_batch)
    print(f"Propiedades nuevas incorporadas a la base: {saved}")
    
    print("Ejecutando algoritmo de deduplicación cruzada entre portales...")
    clusters = run_deduplication(db)
    print(f"Clusters consolidados de inmuebles duplicados: {clusters}")
    
    # Conteos actualizados
    total_db = db.query(Property).count()
    total_ph = db.query(Property).filter(Property.property_type == 'ph').count()
    total_deptos = db.query(Property).filter(Property.property_type == 'departamento').count()
    total_casas = db.query(Property).filter(Property.property_type == 'casa').count()
    total_alquiler = db.query(Property).filter(Property.operation_type == 'alquiler').count()
    total_venta = db.query(Property).filter(Property.operation_type == 'venta').count()
    
    elapsed = round(time.time() - start_time, 1)
    print("\n" + "=" * 70)
    print(f"   RESUMEN FINAL DE LA BASE DE DATOS ({elapsed} segs)")
    print(f"   Total Inmuebles en DB: {total_db}")
    print(f"     • Venta: {total_venta} | Alquiler: {total_alquiler}")
    print(f"     • Departamentos: {total_deptos} | PHs: {total_ph} | Casas: {total_casas}")
    print("=" * 70)
    
    db.close()

if __name__ == '__main__':
    asyncio.run(run_caba_15days_sweep())
