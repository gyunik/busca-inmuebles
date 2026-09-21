import sys
import asyncio
import logging
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from backend.app.core.database import SessionLocal
from backend.app.models.property_model import Property
from backend.app.scrapers.mercadolibre_scraper import MercadoLibreScraper
from backend.app.scrapers.zonaprop_scraper import ZonapropScraper
from backend.app.scrapers.argenprop_scraper import ArgenpropScraper
from backend.app.scrapers.mudafy_scraper import MudafyScraper
from backend.app.services.scraper_runner import save_scraped_items
from backend.app.services.deduplication_service import run_deduplication

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("barrido_masivo_phs")

async def main():
    print("=" * 60)
    print("INICIANDO BARRIDO MASIVO DE PHs EN CAPITAL FEDERAL (CABA)")
    print("Portales: Mercado Libre, Zonaprop, Argenprop, Mudafy")
    print(f"Fecha/Hora de inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    db = SessionLocal()
    initial_count = db.query(Property).count()
    initial_phs = db.query(Property).filter(Property.property_type == 'ph').count()
    print(f"Estado inicial en BD: {initial_count} inmuebles totales ({initial_phs} PHs)")

    scrapers_config = [
        ("Mercado Libre", MercadoLibreScraper(), 15),
        ("Zonaprop", ZonapropScraper(), 15),
        ("Argenprop", ArgenpropScraper(), 15),
        ("Mudafy", MudafyScraper(), 15)
    ]

    total_scraped = 0
    total_saved = 0

    for name, scraper, pages in scrapers_config:
        print(f"\nExtrayendo {pages} páginas de PHs en CABA desde {name}...")
        try:
            items = await scraper.scrape(property_type="ph", zone="CABA", max_pages=pages)
            print(f"   [OK] {name}: {len(items)} inmuebles extraídos.")
            total_scraped += len(items)
            
            if items:
                saved = save_scraped_items(db, items)
                total_saved += saved
                print(f"   [OK] {saved} inmuebles nuevos o actualizados en la base de datos.")
        except Exception as e:
            logger.error(f"Error extrayendo desde {name}: {e}")

    print("\nEjecutando algoritmo inteligente de detección de duplicados...")
    try:
        dup_groups = run_deduplication(db)
        print(f"   [OK] Deduplicación finalizada: {dup_groups} grupos de duplicados detectados.")
    except Exception as e:
        logger.error(f"Error en deduplicación: {e}")

    final_count = db.query(Property).count()
    final_phs = db.query(Property).filter(Property.property_type == 'ph').count()
    db.close()

    print("\n" + "=" * 60)
    print("BARRIDO MASIVO COMPLETADO EXITOSAMENTE")
    print(f"   - Total extraído: {total_scraped} avisos")
    print(f"   - Nuevos guardados: {total_saved} avisos")
    print(f"   - Total PHs ahora en Base de Datos: {final_phs} PHs")
    print(f"   - Total global de inmuebles en BD: {final_count} inmuebles")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
