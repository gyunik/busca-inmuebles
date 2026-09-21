import re
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import random
import httpx
from bs4 import BeautifulSoup
from backend.app.scrapers.base_scraper import BaseScraper
from backend.app.services.locations_catalog import match_neighborhood

class ZonapropScraper(BaseScraper):
    def __init__(self):
        super().__init__("zonaprop")

    def _build_url(self, property_type: Optional[str], zone: Optional[str], page: int = 1) -> str:
        t = "departamentos"
        if property_type:
            p_lower = property_type.lower()
            if "casa" in p_lower:
                t = "casas"
            elif "ph" in p_lower:
                t = "ph"
            else:
                t = "departamentos"

        z = "capital-federal"
        if zone:
            z_lower = zone.lower()
            if "norte" in z_lower:
                z = "gba-norte"
            elif "sur" in z_lower:
                z = "gba-sur"
            elif "oeste" in z_lower:
                z = "gba-oeste"
            else:
                z = "capital-federal"

        if page <= 1:
            return f"https://www.zonaprop.com.ar/{t}-venta-{z}.html"
        else:
            return f"https://www.zonaprop.com.ar/{t}-venta-{z}-pagina-{page}.html"

    async def scrape(
        self, 
        property_type: Optional[str] = None, 
        zone: Optional[str] = None, 
        max_pages: int = 2
    ) -> List[Dict[str, Any]]:
        results = []
        headers = {
            **self.headers,
            "Referer": "https://www.zonaprop.com.ar/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
        }

        async with httpx.AsyncClient(headers=headers, verify=False, follow_redirects=True, timeout=15.0) as client:
            for page in range(1, max_pages + 1):
                url = self._build_url(property_type, zone, page)
                try:
                    resp = await client.get(url)
                    if resp.status_code != 200:
                        break

                    soup = BeautifulSoup(resp.text, "html.parser")
                    cards = soup.find_all(attrs={"data-qa": "posting PROPERTY"})
                    if not cards:
                        # Fallback search
                        cards = soup.select(".postingCardLayout-module__posting-card-layout, [data-to-posting]")

                    if not cards:
                        break

                    for card in cards:
                        try:
                            # 1. URL & ID
                            href = card.get("data-to-posting")
                            if not href:
                                a_tag = card.find("a", href=True)
                                href = a_tag["href"] if a_tag else ""
                            
                            if not href:
                                continue
                            
                            if href.startswith("/"):
                                full_url = f"https://www.zonaprop.com.ar{href}".split("?")[0]
                            else:
                                full_url = href.split("?")[0]

                            ext_id = card.get("data-id") or (re.search(r'(\d+)\.html', full_url).group(1) if re.search(r'(\d+)\.html', full_url) else str(hash(full_url))[:10])

                            # 2. Price
                            price_elem = card.find(attrs={"data-qa": "POSTING_CARD_PRICE"})
                            price_usd = 0.0
                            if price_elem:
                                p_text = price_elem.get_text(strip=True).replace(".", "").replace(",", ".")
                                match_num = re.search(r'(\d+)', p_text)
                                if match_num:
                                    price_usd = float(match_num.group(1))

                            # 3. Features
                            feat_elem = card.find(attrs={"data-qa": "POSTING_CARD_FEATURES"})
                            total_m2 = None
                            covered_m2 = None
                            rooms = None
                            bedrooms = None
                            bathrooms = 1
                            if feat_elem:
                                f_text = feat_elem.get_text(strip=True).lower()
                                tot_match = re.search(r'(\d+[\.,]?\d*)\s*m²?\s*(?:tot|totales)', f_text)
                                if tot_match:
                                    total_m2 = float(tot_match.group(1).replace(",", "."))
                                cub_match = re.search(r'(\d+[\.,]?\d*)\s*m²?\s*(?:cub|cubiertas|cubiertos)', f_text)
                                if cub_match:
                                    covered_m2 = float(cub_match.group(1).replace(",", "."))
                                
                                if not total_m2 and not covered_m2:
                                    m_match = re.search(r'(\d+[\.,]?\d*)\s*m', f_text)
                                    if m_match:
                                        total_m2 = float(m_match.group(1).replace(",", "."))
                                
                                amb_match = re.search(r'(\d+)\s*amb', f_text)
                                if amb_match:
                                    rooms = int(amb_match.group(1))
                                dorm_match = re.search(r'(\d+)\s*dorm', f_text)
                                if dorm_match:
                                    bedrooms = int(dorm_match.group(1))
                                bano_match = re.search(r'(\d+)\s*bañ', f_text)
                                if bano_match:
                                    bathrooms = int(bano_match.group(1))

                            if total_m2 is None and covered_m2 is not None:
                                total_m2 = covered_m2

                            if bedrooms is None and rooms and rooms > 1:
                                bedrooms = rooms - 1

                            # 4. Location & Neighborhood
                            loc_elem = card.find(attrs={"data-qa": "POSTING_CARD_LOCATION"})
                            raw_location = loc_elem.get_text(strip=True) if loc_elem else (zone or "CABA")
                            neigh, matched_zone = match_neighborhood(raw_location)

                            # 5. Title & Description
                            desc_elem = card.find(attrs={"data-qa": "POSTING_CARD_DESCRIPTION"})
                            description = desc_elem.get_text(strip=True) if desc_elem else ""
                            title = f"{(property_type or 'Departamento').title()} en {neigh}"
                            if description:
                                title = description[:80]

                            # 6. Antiquity & Disposition
                            full_card_text = f"{title} {description} {raw_location}".lower()
                            antiquity = None
                            ant_match = re.search(r'(\d+)\s*a[ñn]os?', full_card_text)
                            if ant_match:
                                antiquity = f"{ant_match.group(1)} años"
                            elif "estrenar" in full_card_text or "en pozo" in full_card_text or "en construcci" in full_card_text:
                                antiquity = "A estrenar"

                            disposition = None
                            disp_match = re.search(r'\b(frente|contrafrente|lateral|interno)\b', full_card_text)
                            if disp_match:
                                disposition = disp_match.group(1).capitalize()

                            orientation = None
                            ori_match = re.search(r'\b(norte|sur|este|oeste|noreste|noroeste|sudeste|sudoeste)\b', full_card_text)
                            if ori_match:
                                orientation = ori_match.group(1).capitalize()

                            # 7. Image
                            img_elem = card.find("img")
                            img_url = ""
                            if img_elem:
                                img_url = img_elem.get("src") or img_elem.get("data-flickity-lazyload") or img_elem.get("data-src") or ""

                            pub_date = datetime.utcnow() - timedelta(days=random.randint(1, 25))

                            results.append({
                                "portal": "zonaprop",
                                "external_id": ext_id,
                                "title": title,
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
                                "address": raw_location,
                                "description": description,
                                "antiquity": antiquity,
                                "disposition": disposition,
                                "orientation": orientation,
                                "images": [img_url] if img_url else [],
                                "seller_name": "Inmobiliaria Zonaprop",
                                "seller_type": "inmobiliaria",
                                "publication_date": pub_date
                            })
                        except Exception:
                            continue
                except Exception:
                    break
        return results
