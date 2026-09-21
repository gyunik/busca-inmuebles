import sys
import asyncio
import logging
import random
from datetime import datetime, timedelta

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from backend.app.core.database import SessionLocal
from backend.app.models.property_model import Property
from backend.app.scrapers.mercadolibre_scraper import MercadoLibreScraper
from backend.app.scrapers.zonaprop_scraper import ZonapropScraper
from backend.app.scrapers.argenprop_scraper import ArgenpropScraper
from backend.app.scrapers.mudafy_scraper import MudafyScraper
from backend.app.services.scraper_runner import save_scraped_items
from backend.app.services.deduplication_service import run_deduplication

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("barrido_10k")

async def run_batch(name, scraper, property_type, zone, pages, db):
    print(f"\n---> [{name}] Escaneando {pages} paginas de {property_type.upper()} en {zone}...")
    try:
        items = await scraper.scrape(property_type=property_type, zone=zone, max_pages=pages)
        print(f"     Extraidos: {len(items)} avisos.")
        if items:
            saved = save_scraped_items(db, items)
            print(f"     Guardados/Actualizados en BD: {saved} avisos.")
            return len(items), saved
    except Exception as e:
        logger.error(f"Error con {name} ({property_type}, {zone}): {e}")
    return 0, 0

async def main():
    print("=" * 70)
    print("      INICIANDO MEGA BARRIDO MASIVO DE HASTA 10.000 INMUEBLES")
    print("      Prioridad: PHs en CABA (< USD 200.000 y < 30 dias)")
    print(f"      Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    db = SessionLocal()
    initial_total = db.query(Property).count()
    initial_phs = db.query(Property).filter(Property.property_type == 'ph').count()
    print(f"Estado inicial en Base de Datos: {initial_total} inmuebles ({initial_phs} PHs)\n")

    ml = MercadoLibreScraper()
    zp = ZonapropScraper()
    ap = ArgenpropScraper()
    mf = MudafyScraper()

    # Plan de ejecucion escalonado
    batches = [
        # 1. PRIORIDAD 1: PHs en CABA (Barrido profundo)
        ("Mercado Libre", ml, "ph", "CABA", 40),
        ("Zonaprop", zp, "ph", "CABA", 30),
        ("Argenprop", ap, "ph", "CABA", 30),
        ("Mudafy", mf, "ph", "CABA", 25),

        # 2. PRIORIDAD 2: PHs en GBA (Norte, Oeste, Sur)
        ("Mercado Libre", ml, "ph", "GBA Norte", 25),
        ("Mercado Libre", ml, "ph", "GBA Oeste", 20),
        ("Mercado Libre", ml, "ph", "GBA Sur", 20),
        ("Zonaprop", zp, "ph", "GBA Norte", 20),
        ("Zonaprop", zp, "ph", "GBA Oeste", 15),
        ("Zonaprop", zp, "ph", "GBA Sur", 15),

        # 3. PRIORIDAD 3: Departamentos en CABA (< 200k)
        ("Mercado Libre", ml, "departamento", "CABA", 45),
        ("Zonaprop", zp, "departamento", "CABA", 35),
        ("Argenprop", ap, "departamento", "CABA", 30),
        ("Mudafy", mf, "departamento", "CABA", 30),

        # 4. PRIORIDAD 4: Casas en CABA y GBA Norte
        ("Mercado Libre", ml, "casa", "CABA", 25),
        ("Mercado Libre", ml, "casa", "GBA Norte", 25),
        ("Zonaprop", zp, "casa", "CABA", 20),
        ("Argenprop", ap, "casa", "CABA", 20),
    ]

    total_extracted = 0
    total_new_saved = 0

    for i, (name, scraper, p_type, zone, pages) in enumerate(batches, 1):
        print(f"\n[Paso {i}/{len(batches)}] {name} - {p_type.upper()} ({zone})")
        extracted, saved = await run_batch(name, scraper, p_type, zone, pages, db)
        total_extracted += extracted
        total_new_saved += saved

        current_count = db.query(Property).count()
        print(f"--> Total acumulado en Base de Datos: {current_count} inmuebles")

        # Pausa de cortesia entre lotes
        await asyncio.sleep(random.uniform(1.5, 3.0))

    print("\n" + "=" * 70)
    print("Ejecutando algoritmo inteligente de Deduplicacion...")
    dup_clusters = run_deduplication(db)
    print(f"Deduplicacion finalizada: {dup_clusters} grupos de duplicados detectados.")

    # Normalizacion de tipos
    db.query(Property).filter(Property.property_type == 'departamentos').update({Property.property_type: 'departamento'})
    db.query(Property).filter(Property.property_type == 'casas').update({Property.property_type: 'casa'})
    db.commit()

    final_total = db.query(Property).count()
    final_phs = db.query(Property).filter(Property.property_type == 'ph').count()
    final_caba_phs = db.query(Property).filter(Property.property_type == 'ph', Property.zone == 'CABA').count()
    db.close()

    print("\n" + "=" * 70)
    print("🎉 MEGA BARRIDO MASIVO COMPLETADO!")
    print(f"   • Total avisos analizados y extraídos: {total_extracted}")
    print(f"   • Nuevos guardados/actualizados: {total_new_saved}")
    print(f"   • Total PHs en CABA: {final_caba_phs}")
    print(f"   • Total PHs globales en BD: {final_phs}")
    print(f"   • Total GLOBAL de inmuebles en la Base de Datos: {final_total}")
    print(f"   • Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
