import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from backend.app.core.database import SessionLocal
from backend.app.models.property_model import Property, PriceHistory, ScrapeJob
from backend.app.scrapers.mercadolibre_scraper import MercadoLibreScraper
from backend.app.scrapers.argenprop_scraper import ArgenpropScraper
from backend.app.scrapers.zonaprop_scraper import ZonapropScraper
from backend.app.scrapers.properati_scraper import ProperatiScraper
from backend.app.scrapers.mudafy_scraper import MudafyScraper
from backend.app.scrapers.remax_scraper import RemaxScraper
from backend.app.scrapers.cabaprop_scraper import CabaPropScraper
from backend.app.services.deduplication_service import run_deduplication

SCRAPERS = {
    "mercadolibre": MercadoLibreScraper(),
    "argenprop": ArgenpropScraper(),
    "zonaprop": ZonapropScraper(),
    "remax": RemaxScraper(),
    "cabaprop": CabaPropScraper(),
    "properati": ProperatiScraper(),
    "mudafy": MudafyScraper()
}

def save_scraped_items(db: Session, items: List[Dict[str, Any]]) -> int:
    saved_count = 0
    seen_urls_in_batch = set()
    
    for item in items:
        url = item.get("url")
        if not url or url in seen_urls_in_batch:
            continue
        seen_urls_in_batch.add(url)
        
        try:
            # Check if URL exists in DB
            existing = db.query(Property).filter(Property.url == url).first()
            if existing:
                # Check price change
                if item.get("price_usd") and item["price_usd"] != existing.price_usd:
                    history_entry = PriceHistory(
                        property_id=existing.id,
                        price_usd=existing.price_usd,
                        recorded_at=datetime.utcnow()
                    )
                    db.add(history_entry)
                    existing.price_usd = item["price_usd"]
                    if item.get("total_area_m2") and item["total_area_m2"] > 0:
                        existing.price_per_m2 = round(item["price_usd"] / item["total_area_m2"], 1)
                
                existing.updated_at = datetime.utcnow()
                if item.get("images"):
                    existing.images = item["images"]
                db.commit()
            else:
                new_prop = Property(
                    portal=item["portal"],
                    external_id=item["external_id"],
                    title=item["title"],
                    url=url,
                    property_type=item["property_type"],
                    operation_type=item.get("operation_type", "venta"),
                    price_usd=item["price_usd"],
                    price_currency_orig=item.get("price_currency_orig", "USD"),
                    price_amount_orig=item.get("price_amount_orig", item["price_usd"]),
                    expenses=item.get("expenses"),
                    total_area_m2=item.get("total_area_m2"),
                    covered_area_m2=item.get("covered_area_m2"),
                    price_per_m2=item.get("price_per_m2"),
                    rooms=item.get("rooms"),
                    bedrooms=item.get("bedrooms"),
                    bathrooms=item.get("bathrooms"),
                    garages=item.get("garages"),
                    neighborhood=item["neighborhood"],
                    zone=item["zone"],
                    city=item.get("city", "Buenos Aires"),
                    address=item.get("address"),
                    latitude=item.get("latitude"),
                    longitude=item.get("longitude"),
                    description=item.get("description"),
                    images_json="[]",
                    seller_name=item.get("seller_name"),
                    seller_type=item.get("seller_type", "inmobiliaria"),
                    antiquity=item.get("antiquity"),
                    disposition=item.get("disposition"),
                    orientation=item.get("orientation"),
                    publication_date=item.get("publication_date", datetime.utcnow())
                )
                new_prop.images = item.get("images", [])
                db.add(new_prop)
                db.commit()
                saved_count += 1
        except Exception:
            db.rollback()
            continue
            
    return saved_count

async def execute_scrape_job(job_id: int, portal: str, property_type: Optional[str], zone: Optional[str]):
    db = SessionLocal()
    job = db.query(ScrapeJob).filter(ScrapeJob.id == job_id).first()
    if not job:
        db.close()
        return

    job.status = "running"
    db.commit()

    try:
        scraped_data = []
        if portal == "all":
            for p_name, scraper in SCRAPERS.items():
                try:
                    res = await scraper.scrape(property_type=property_type, zone=zone, max_pages=2)
                    scraped_data.extend(res)
                except Exception:
                    continue
        elif portal in SCRAPERS:
            scraped_data = await SCRAPERS[portal].scrape(property_type=property_type, zone=zone, max_pages=3)
            
        saved = save_scraped_items(db, scraped_data)
        
        # Run duplicate cluster detection
        clusters = run_deduplication(db)

        job.status = "completed"
        job.items_found = len(scraped_data)
        job.items_saved = saved
        job.finished_at = datetime.utcnow()
        job.message = f"Completado exitosamente. {len(scraped_data)} publicaciones reales procesadas, {saved} nuevas guardadas, {clusters} grupos de duplicados actualizados."
        db.commit()
    except Exception as e:
        job.status = "failed"
        job.message = str(e)
        job.finished_at = datetime.utcnow()
        db.commit()
    finally:
        db.close()

def seed_initial_database_if_empty(db: Session):
    # If empty, nothing to do here as offline crawler populates real data
    pass
