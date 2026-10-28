import asyncio
import os
import sys
import random

# Ensure root path is accessible
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.app.core.database import SessionLocal, Base, engine
from backend.app.models.property_model import Property
from backend.app.scrapers.mercadolibre_scraper import MercadoLibreScraper
from backend.app.scrapers.argenprop_scraper import ArgenpropScraper
from backend.app.scrapers.zonaprop_scraper import ZonapropScraper
from backend.app.scrapers.remax_scraper import RemaxScraper
from backend.app.scrapers.cabaprop_scraper import CabaPropScraper
from backend.app.services.scraper_runner import save_scraped_items
from backend.app.services.deduplication_service import run_deduplication

async def main():
    print("===================================================")
    print("   ACTUALIZADOR OFFLINE MULTI-PORTAL PROFESIONAL")
    print("   (Mercado Libre + Argenprop + RE/MAX + Zonaprop)")
    print("===================================================\n")
    
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    ml = MercadoLibreScraper()
    ap = ArgenpropScraper()
    rm = RemaxScraper()
    zp = ZonapropScraper()
    
    total = []
    
    # 1. Mercado Libre
    ml_targets = [
        ('departamentos', 'capital-federal', 2),
        ('casas', 'capital-federal', 2),
        ('ph', 'capital-federal', 2),
        ('departamentos', 'bsas-gba-norte', 2),
        ('casas', 'bsas-gba-norte', 2),
        ('departamentos', 'bsas-gba-sur', 2),
        ('departamentos', 'bsas-gba-oeste', 2),
    ]
    print('[1/4] Extrayendo de Mercado Libre...')
    for ptype, zone, pages in ml_targets:
        try:
            print(f'  -> ML {ptype} en {zone} ({pages} pags)...', flush=True)
            res = await ml.scrape(property_type=ptype, zone=zone, max_pages=pages)
            print(f'     Obtenidos: {len(res)}')
            total.extend(res)
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f'     Error: {e}')

    # 2. Argenprop (reparado y verificado)
    ap_targets = [
        ('departamentos', 'capital-federal', 2),
        ('casas', 'capital-federal', 2),
        ('ph', 'capital-federal', 2),
        ('departamentos', 'zona-norte', 2),
        ('casas', 'zona-norte', 2),
        ('departamentos', 'zona-sur', 2),
        ('departamentos', 'zona-oeste', 2),
    ]
    print('\n[2/4] Extrayendo de Argenprop...')
    for ptype, zone, pages in ap_targets:
        try:
            print(f'  -> AP {ptype} en {zone} ({pages} pags)...', flush=True)
            res = await ap.scrape(property_type=ptype, zone=zone, max_pages=pages)
            print(f'     Obtenidos: {len(res)}')
            total.extend(res)
            await asyncio.sleep(1.0)
        except Exception as e:
            print(f'     Error: {e}')

    # 3. RE/MAX (API oficial y CDN CloudFront)
    rm_targets = [
        ('departamento', 'capital-federal', 2),
        ('casa', 'capital-federal', 2),
        ('ph', 'capital-federal', 2),
        ('departamento', 'gba-norte', 1),
    ]
    print('\n[3/4] Extrayendo de RE/MAX...')
    for ptype, zone, pages in rm_targets:
        try:
            print(f'  -> RE/MAX {ptype} en {zone} ({pages} pags)...', flush=True)
            res = await rm.scrape(property_type=ptype, zone=zone, max_pages=pages)
            print(f'     Obtenidos: {len(res)}')
            total.extend(res)
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f'     Error: {e}')

    # 4. Zonaprop (con delays preventivos anti-bot)
    zp_targets = [
        ('departamentos', 'capital-federal', 1),
        ('casas', 'capital-federal', 1),
        ('ph', 'capital-federal', 1),
        ('departamentos', 'gba-norte', 1),
    ]
    print('\n[4/4] Extrayendo de Zonaprop...')
    for ptype, zone, pages in zp_targets:
        try:
            print(f'  -> Zonaprop {ptype} en {zone} ({pages} pag)...', flush=True)
            res = await zp.scrape(property_type=ptype, zone=zone, max_pages=pages)
            print(f'     Obtenidos: {len(res)}')
            total.extend(res)
            await asyncio.sleep(2.0)
        except Exception as e:
            print(f'     Error: {e}')

    print(f'\nTotal recolectados en la sesion: {len(total)}')
    saved = save_scraped_items(db, total)
    print(f'Nuevos guardados en base de datos: {saved}')
    
    print('Ejecutando deduplicador inteligente...')
    clusters = run_deduplication(db)
    print(f'Clusters de duplicados detectados/actualizados: {clusters}')
    
    total_db = db.query(Property).count()
    print(f'\n>>> TOTAL INMUEBLES REALES EN LA BASE DE DATOS: {total_db} <<<')
    db.close()

if __name__ == '__main__':
    asyncio.run(main())
