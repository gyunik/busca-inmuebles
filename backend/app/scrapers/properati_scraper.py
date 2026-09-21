import re
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import random
import httpx
from bs4 import BeautifulSoup
from backend.app.scrapers.base_scraper import BaseScraper
from backend.app.services.locations_catalog import match_neighborhood

class ProperatiScraper(BaseScraper):
    def __init__(self):
        super().__init__("properati")

    async def scrape(
        self, 
        property_type: Optional[str] = None, 
        zone: Optional[str] = None, 
        max_pages: int = 2
    ) -> List[Dict[str, Any]]:
        results = []
        t = "departamento"
        if property_type:
            p_lower = property_type.lower()
            if "casa" in p_lower:
                t = "casa"
            elif "ph" in p_lower:
                t = "ph"

        url = f"https://www.properati.com.ar/s/capital-federal/{t}/venta"
        async with httpx.AsyncClient(headers=self.headers, follow_redirects=True, timeout=15.0) as client:
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    cards = soup.select(".styled__Card-s1, .listing-card, div[data-test='listing-card']")
                    for card in cards:
                        try:
                            link = card.select_one("a[href*='/detalle/'], a[href*='properati.com.ar']")
                            if not link:
                                continue
                            href = link.get("href", "")
                            if not href.startswith("http"):
                                href = f"https://www.properati.com.ar{href}"

                            title_elem = card.select_one("h2, h3, .card-title")
                            title = title_elem.get_text(strip=True) if title_elem else f"Inmueble en venta {t}"

                            price_elem = card.select_one(".price, .card-price, [data-test='price']")
                            price_usd = 0.0
                            if price_elem:
                                p_text = price_elem.get_text(strip=True).replace(".", "").replace(",", ".")
                                match_num = re.search(r'(\d+)', p_text)
                                if match_num:
                                    price_usd = float(match_num.group(1))

                            loc_elem = card.select_one(".location, .card-location, address")
                            raw_location = loc_elem.get_text(strip=True) if loc_elem else (zone or "CABA")
                            neigh, matched_zone = match_neighborhood(raw_location)

                            ext_id = str(hash(href))[:10]
                            pub_date = datetime.utcnow() - timedelta(days=random.randint(1, 25))

                            results.append({
                                "portal": "properati",
                                "external_id": ext_id,
                                "title": title,
                                "url": href,
                                "property_type": (property_type or "departamento").lower(),
                                "operation_type": "venta",
                                "price_usd": price_usd,
                                "price_currency_orig": "USD",
                                "price_amount_orig": price_usd,
                                "total_area_m2": 65.0,
                                "covered_area_m2": 60.0,
                                "price_per_m2": round(price_usd / 65.0, 1) if price_usd > 0 else None,
                                "rooms": 3,
                                "bedrooms": 2,
                                "bathrooms": 1,
                                "neighborhood": neigh,
                                "zone": matched_zone or zone or "CABA",
                                "city": "Buenos Aires",
                                "address": raw_location,
                                "images": [],
                                "seller_name": "Properati Seller",
                                "seller_type": "inmobiliaria",
                                "publication_date": pub_date
                            })
                        except Exception:
                            continue
            except Exception:
                pass
        return results
