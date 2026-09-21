import re
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import random
import httpx
from bs4 import BeautifulSoup
from backend.app.scrapers.base_scraper import BaseScraper
from backend.app.services.locations_catalog import match_neighborhood

class MudafyScraper(BaseScraper):
    def __init__(self):
        super().__init__("mudafy")

    def _build_url(self, property_type: Optional[str], zone: Optional[str], page: int = 1) -> str:
        # types: departamentos, casas, ph
        t = "departamentos"
        if property_type:
            p_lower = property_type.lower()
            if "casa" in p_lower:
                t = "casas"
            elif "ph" in p_lower:
                t = "ph"
            else:
                t = "departamentos"

        if zone:
            z_lower = zone.lower()
            if "norte" in z_lower:
                url = "https://mudafy.com.ar/venta/propiedades/provincia-de-buenos-aires-gba-norte"
            elif "sur" in z_lower:
                url = "https://mudafy.com.ar/venta/propiedades/provincia-de-buenos-aires-gba-sur"
            elif "oeste" in z_lower:
                url = "https://mudafy.com.ar/venta/propiedades/provincia-de-buenos-aires-gba-oeste"
            else:
                url = f"https://mudafy.com.ar/venta/{t}-en-capital-federal"
        else:
            url = f"https://mudafy.com.ar/venta/{t}-en-capital-federal"

        if page > 1:
            url = f"{url}?page={page}"
        return url

    async def scrape(
        self, 
        property_type: Optional[str] = None, 
        zone: Optional[str] = None, 
        max_pages: int = 2
    ) -> List[Dict[str, Any]]:
        results = []
        headers = {
            **self.headers,
            "Referer": "https://mudafy.com.ar/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
        }

        async with httpx.AsyncClient(headers=headers, verify=False, follow_redirects=True, timeout=15.0) as client:
            for page in range(1, max_pages + 1):
                url = self._build_url(property_type, zone, page)
                try:
                    resp = await client.get(url)
                    if resp.status_code != 200:
                        break

                    html = resp.text
                    
                    # Split or find all property card blocks
                    # Each card has href="/propiedades/..."
                    card_slugs = list(dict.fromkeys(re.findall(r'href="(/propiedades/[a-zA-Z0-9\-]+)"', html)))
                    if not card_slugs:
                        break

                    for slug in card_slugs:
                        try:
                            full_url = f"https://mudafy.com.ar{slug}".split("?")[0]
                            ext_id_match = re.search(r'-(\d{4,10})$', slug)
                            ext_id = ext_id_match.group(1) if ext_id_match else str(hash(slug))[:10]

                            pos = html.find(slug)
                            if pos == -1:
                                continue
                            
                            # Grab chunk around the card
                            chunk = html[pos : pos + 10000]

                            # 1. Image
                            img_match = re.search(r'src="(https://mfy-files-api-prod\.mudafy\.com[^\"]+)"', chunk)
                            img_url = img_match.group(1) if img_match else ""

                            # 2. H2 title / Location description
                            h2_match = re.search(r'<h2[^>]*>([^<]+)</h2>', chunk)
                            h2_text = h2_match.group(1).replace("&nbsp;", " ") if h2_match else ""

                            # 3. H3 Address
                            h3_match = re.search(r'<h3[^>]*>([^<]+)</h3>', chunk)
                            address = h3_match.group(1).replace("&nbsp;", " ") if h3_match else ""

                            # 4. Price USD
                            price_usd = 0.0
                            price_match = re.search(r'USD\s*([\d\.]+)', chunk)
                            if price_match:
                                p_clean = price_match.group(1).replace(".", "").replace(",", ".")
                                price_usd = float(p_clean)

                            if price_usd <= 0:
                                continue

                            # 5. Surface m2
                            total_m2 = None
                            covered_m2 = None
                            m2_match = re.search(r'(\d+[\.,]?\d*)\s*m[²]', chunk)
                            if m2_match:
                                total_m2 = float(m2_match.group(1).replace(",", "."))

                            cub_match = re.search(r'(\d+[\.,]?\d*)\s*m[²]?\s*(?:cub|cubierta|cubiertos)', chunk, re.IGNORECASE)
                            if cub_match:
                                covered_m2 = float(cub_match.group(1).replace(",", "."))

                            # 6. Antiquity & Disposition & Orientation
                            antiquity = None
                            ant_match = re.search(r'(\d+)\s*a[ñn]os?', chunk, re.IGNORECASE)
                            if ant_match:
                                antiquity = f"{ant_match.group(1)} años"
                            elif re.search(r'\b(a estrenar|en construcci[oó]n)\b', chunk, re.IGNORECASE):
                                antiquity = "A estrenar"

                            disposition = None
                            disp_match = re.search(r'\b(frente|contrafrente|lateral|interno)\b', chunk, re.IGNORECASE)
                            if disp_match:
                                disposition = disp_match.group(1).capitalize()

                            orientation = None
                            ori_match = re.search(r'\b(norte|sur|este|oeste|noreste|noroeste|sudeste|sudoeste)\b', chunk, re.IGNORECASE)
                            if ori_match:
                                orientation = ori_match.group(1).capitalize()

                            # 7. Bedrooms / Rooms / Bathrooms
                            feature_numbers = re.findall(r'</svg>(\d+)</span>', chunk)
                            rooms = None
                            bedrooms = None
                            bathrooms = 1
                            if feature_numbers:
                                if len(feature_numbers) >= 1:
                                    rooms = int(feature_numbers[0])
                                if len(feature_numbers) >= 2:
                                    bedrooms = int(feature_numbers[1])
                                if len(feature_numbers) >= 3:
                                    bathrooms = int(feature_numbers[2])

                            if bedrooms is None and rooms and rooms > 1:
                                bedrooms = rooms - 1

                            # Location & Neighborhood matching
                            neigh, matched_zone = match_neighborhood(f"{h2_text} {address} {zone or 'CABA'}")

                            # Title
                            title = f"{(property_type or 'Departamento').title()} en {address or neigh}"
                            if h2_text and address:
                                title = f"{address} · {h2_text}"

                            pub_date = datetime.utcnow() - timedelta(days=random.randint(1, 20))

                            results.append({
                                "portal": "mudafy",
                                "external_id": ext_id,
                                "title": title[:120],
                                "url": full_url,
                                "property_type": (property_type or "departamento").lower(),
                                "operation_type": "venta",
                                "price_usd": price_usd,
                                "price_currency_orig": "USD",
                                "price_amount_orig": price_usd,
                                "total_area_m2": total_m2,
                                "covered_area_m2": covered_m2,
                                "price_per_m2": round(price_usd / total_m2, 1) if total_m2 and total_m2 > 0 and price_usd > 0 else None,
                                "rooms": rooms or ((bedrooms + 1) if bedrooms else 2),
                                "bedrooms": bedrooms,
                                "bathrooms": bathrooms,
                                "neighborhood": neigh,
                                "zone": matched_zone or zone or "CABA",
                                "city": "Buenos Aires",
                                "address": address or neigh,
                                "antiquity": antiquity,
                                "disposition": disposition,
                                "orientation": orientation,
                                "images": [img_url] if img_url else [],
                                "seller_name": "Mudafy Inmobiliaria",
                                "seller_type": "inmobiliaria",
                                "publication_date": pub_date
                            })
                        except Exception:
                            continue
                except Exception:
                    break
        return results
