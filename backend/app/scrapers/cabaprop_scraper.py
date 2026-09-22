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

class CabaPropScraper(BaseScraper):
    def __init__(self):
        super().__init__("cabaprop")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "es-419,es;q=0.9,en;q=0.8",
            "Referer": "https://cabaprop.com.ar/",
        }

    async def scrape(
        self, 
        property_type: Optional[str] = None, 
        zone: Optional[str] = None, 
        max_pages: int = 3
    ) -> List[Dict[str, Any]]:
        results = []
        # CabaProp portal search
        async with httpx.AsyncClient(headers=self.headers, verify=False, follow_redirects=True, timeout=18.0) as client:
            for page in range(1, max_pages + 1):
                url = f"https://cabaprop.com.ar/propiedades?tipo=ph&operacion=venta&page={page}"
                try:
                    resp = await client.get(url)
                    if resp.status_code != 200:
                        # Try alternate SSR endpoint
                        alt_url = f"https://cabaprop.com.ar/inmuebles/venta/ph?pagina={page}"
                        resp = await client.get(alt_url)
                        if resp.status_code != 200:
                            break
                            
                    soup = BeautifulSoup(resp.text, "html.parser")
                    cards = soup.select(".card, .property-card, .listing-item, article, div[class*='PropertyCard']")
                    if not cards:
                        break
                        
                    for card in cards:
                        try:
                            link = card.find("a", href=True)
                            if not link:
                                continue
                            href = link["href"]
                            full_url = f"https://cabaprop.com.ar{href}" if href.startswith("/") else href
                            
                            match_id = re.search(r'/(\d+)', full_url)
                            ext_id = match_id.group(1) if match_id else str(hash(full_url))[:10]
                            
                            card_text = card.get_text(" ", strip=True)
                            price_match = re.search(r'USD\s*([\d\.,]+)', card_text)
                            if not price_match:
                                price_match = re.search(r'US\$\s*([\d\.,]+)', card_text)
                            if not price_match:
                                continue
                                
                            price_usd = float(price_match.group(1).replace(".", "").replace(",", "."))
                            if price_usd <= 0:
                                continue
                                
                            neigh, matched_zone = match_neighborhood(card_text)
                            
                            base_c = COORDS.get(neigh, COORDS.get("CABA"))
                            lat = base_c[0] + random.uniform(-0.005, 0.005)
                            lon = base_c[1] + random.uniform(-0.005, 0.005)
                            
                            results.append({
                                "portal": "cabaprop",
                                "external_id": f"caba_{ext_id}",
                                "title": f"PH en Venta CabaProp en {neigh}",
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
                                "seller_name": "Corredor Matriculado CPI",
                                "seller_type": "inmobiliaria",
                                "publication_date": datetime.utcnow()
                            })
                        except Exception:
                            continue
                except Exception:
                    break
        return results
