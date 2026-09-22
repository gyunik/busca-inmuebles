import re
import asyncio
import random
from typing import List, Dict, Any, Optional
from datetime import datetime
import httpx
from bs4 import BeautifulSoup
from backend.app.scrapers.base_scraper import BaseScraper
from backend.app.services.locations_catalog import match_neighborhood

COORDS = {
    "Parque Chas": (-34.5855, -58.4800),
    "Villa Urquiza": (-34.5724, -58.4900),
    "Villa del Parque": (-34.6050, -58.4950),
    "CABA": (-34.6037, -58.3816),
}

class RemaxScraper(BaseScraper):
    def __init__(self):
        super().__init__("remax")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "es-419,es;q=0.9,en;q=0.8",
            "Referer": "https://www.remax.com.ar/",
        }

    async def scrape(
        self, 
        property_type: Optional[str] = None, 
        zone: Optional[str] = None, 
        max_pages: int = 3
    ) -> List[Dict[str, Any]]:
        results = []
        # type 3 = PH in RE/MAX, type 1 = Casa, type 2 = Depto
        type_code = "3"
        if property_type:
            p_low = property_type.lower()
            if "casa" in p_low:
                type_code = "1"
            elif "depto" in p_low or "departamento" in p_low:
                type_code = "2"
            elif "ph" in p_low:
                type_code = "3"

        async with httpx.AsyncClient(headers=self.headers, verify=False, follow_redirects=True, timeout=18.0) as client:
            for page in range(0, max_pages):
                url = f"https://www.remax.com.ar/listings/buy?page={page}&pageSize=24&sort=-createdAt&in:operation_type=1&in:type={type_code}&locations=in:capital-federal"
                try:
                    resp = await client.get(url)
                    if resp.status_code != 200:
                        break
                    
                    soup = BeautifulSoup(resp.text, "html.parser")
                    # RE/MAX card containers
                    cards = soup.select(".card-item, .listing-card, div[data-testid*='listing-card'], a[href*='/listings/']")
                    
                    # Also look for Next.js __NEXT_DATA__ JSON in RE/MAX
                    next_data = soup.find("script", id="__NEXT_DATA__")
                    if next_data and next_data.string:
                        import json
                        try:
                            data = json.loads(next_data.string)
                            props_list = data.get("props", {}).get("pageProps", {}).get("listings", {}).get("data", [])
                            for p in props_list:
                                try:
                                    ext_id = str(p.get("id") or p.get("slug") or "")
                                    url_slug = p.get("slug") or ext_id
                                    item_url = f"https://www.remax.com.ar/listings/{url_slug}"
                                    title = p.get("title") or f"PH en Venta RE/MAX"
                                    price_usd = float(p.get("price") or p.get("price_usd") or 0)
                                    if price_usd <= 0:
                                        continue
                                    
                                    neigh = p.get("neighborhood", {}).get("name") if isinstance(p.get("neighborhood"), dict) else (p.get("neighborhood") or "Capital Federal")
                                    neigh, matched_zone = match_neighborhood(neigh)
                                    
                                    total_m2 = float(p.get("total_area") or p.get("area") or 0) or None
                                    covered_m2 = float(p.get("covered_area") or 0) or None
                                    rooms = p.get("rooms") or p.get("environments")
                                    bedrooms = p.get("bedrooms")
                                    bathrooms = p.get("bathrooms")
                                    
                                    images = [img.get("url") for img in p.get("images", []) if isinstance(img, dict) and img.get("url")]
                                    
                                    base_c = COORDS.get(neigh, COORDS.get("CABA"))
                                    lat = base_c[0] + random.uniform(-0.005, 0.005)
                                    lon = base_c[1] + random.uniform(-0.005, 0.005)
                                    
                                    results.append({
                                        "portal": "remax",
                                        "external_id": f"remax_{ext_id}",
                                        "title": title,
                                        "url": item_url,
                                        "property_type": property_type or "ph",
                                        "operation_type": "venta",
                                        "price_usd": price_usd,
                                        "expenses": p.get("expenses"),
                                        "total_area_m2": total_m2 or covered_m2,
                                        "covered_area_m2": covered_m2,
                                        "price_per_m2": round(price_usd / (total_m2 or covered_m2), 1) if (total_m2 or covered_m2) else None,
                                        "rooms": int(rooms) if rooms else None,
                                        "bedrooms": int(bedrooms) if bedrooms else None,
                                        "bathrooms": int(bathrooms) if bathrooms else None,
                                        "neighborhood": neigh,
                                        "zone": matched_zone or "Capital Federal",
                                        "city": "Buenos Aires",
                                        "address": p.get("address") or neigh,
                                        "latitude": lat,
                                        "longitude": lon,
                                        "description": p.get("description", ""),
                                        "images": images,
                                        "seller_name": "RE/MAX Argentina",
                                        "seller_type": "inmobiliaria",
                                        "publication_date": datetime.utcnow()
                                    })
                                except Exception:
                                    continue
                        except Exception:
                            pass

                    # Fallback HTML parser
                    if not results:
                        for card in cards:
                            try:
                                link_tag = card if card.name == "a" else card.find("a", href=True)
                                if not link_tag:
                                    continue
                                href = link_tag.get("href", "")
                                if "/listings/" not in href:
                                    continue
                                full_url = f"https://www.remax.com.ar{href}" if href.startswith("/") else href
                                
                                match_id = re.search(r'/listings/([^/?]+)', full_url)
                                ext_id = match_id.group(1) if match_id else str(hash(full_url))[:10]
                                
                                card_text = card.get_text(" ", strip=True)
                                price_match = re.search(r'USD\s*([\d\.,]+)', card_text)
                                if not price_match:
                                    price_match = re.search(r'US\$\s*([\d\.,]+)', card_text)
                                if not price_match:
                                    continue
                                    
                                price_usd = float(price_match.group(1).replace(".", "").replace(",", "."))
                                neigh, matched_zone = match_neighborhood(card_text)
                                
                                base_c = COORDS.get(neigh, COORDS.get("CABA"))
                                lat = base_c[0] + random.uniform(-0.005, 0.005)
                                lon = base_c[1] + random.uniform(-0.005, 0.005)
                                
                                results.append({
                                    "portal": "remax",
                                    "external_id": f"remax_{ext_id}",
                                    "title": f"PH en Venta RE/MAX en {neigh}",
                                    "url": full_url,
                                    "property_type": property_type or "ph",
                                    "operation_type": "venta",
                                    "price_usd": price_usd,
                                    "expenses": None,
                                    "total_area_m2": None,
                                    "covered_area_m2": None,
                                    "price_per_m2": None,
                                    "rooms": None,
                                    "bedrooms": None,
                                    "bathrooms": None,
                                    "neighborhood": neigh,
                                    "zone": matched_zone or "Capital Federal",
                                    "city": "Buenos Aires",
                                    "address": neigh,
                                    "latitude": lat,
                                    "longitude": lon,
                                    "description": card_text,
                                    "images": [],
                                    "seller_name": "RE/MAX Argentina",
                                    "seller_type": "inmobiliaria",
                                    "publication_date": datetime.utcnow()
                                })
                            except Exception:
                                continue
                                
                    await asyncio.sleep(0.3)
                except Exception:
                    break
                    
        return results
