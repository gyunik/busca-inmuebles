import re
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import random
import httpx
from bs4 import BeautifulSoup
from backend.app.scrapers.base_scraper import BaseScraper
from backend.app.services.locations_catalog import match_neighborhood

class ArgenpropScraper(BaseScraper):
    def __init__(self):
        super().__init__("argenprop")

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
                z = "zona-norte"
            elif "sur" in z_lower:
                z = "zona-sur"
            elif "oeste" in z_lower:
                z = "zona-oeste"
            else:
                z = "capital-federal"

        url = f"https://www.argenprop.com/{t}/venta/{z}"
        if page > 1:
            url = f"{url}?pagina-{page}"
        return url

    async def scrape(
        self, 
        property_type: Optional[str] = None, 
        zone: Optional[str] = None, 
        max_pages: int = 2
    ) -> List[Dict[str, Any]]:
        results = []
        async with httpx.AsyncClient(headers=self.headers, verify=False, follow_redirects=True, timeout=15.0) as client:
            for page in range(1, max_pages + 1):
                url = self._build_url(property_type, zone, page)
                try:
                    resp = await client.get(url)
                    if resp.status_code != 200:
                        break
                    
                    soup = BeautifulSoup(resp.text, "html.parser")
                    cards = soup.select(".listing__item, .card")
                    if not cards:
                        break

                    for card in cards:
                        try:
                            # Link and title
                            link_elem = card.select_one("a.card, a[href*='departamento'], a[href*='casa'], a[href*='ph']")
                            if not link_elem:
                                continue
                            href = link_elem.get("href", "")
                            if not href.startswith("http"):
                                href = f"https://www.argenprop.com{href}"
                            
                            title_elem = card.select_one(".card__title, .card__address, h2")
                            title = title_elem.get_text(strip=True) if title_elem else f"Inmueble en {zone or 'CABA'}"

                            # ID
                            id_match = re.search(r'--(\d+)', href)
                            ext_id = id_match.group(1) if id_match else str(hash(href))[:10]

                            # Price
                            price_elem = card.select_one(".card__price, .price")
                            price_usd = 0.0
                            if price_elem:
                                p_text = price_elem.get_text(strip=True).replace(".", "").replace(",", ".")
                                match_num = re.search(r'(\d+)', p_text)
                                if match_num:
                                    price_usd = float(match_num.group(1))

                            # Features (m2, dorms, baños)
                            features = card.select(".card__main-features li, .main-features li")
                            total_m2 = None
                            covered_m2 = None
                            bedrooms = None
                            bathrooms = 1
                            for feat in features:
                                f_text = feat.get_text(strip=True).lower()
                                if "cubie" in f_text or "cub" in f_text:
                                    m_num = re.search(r'(\d+)', f_text)
                                    if m_num:
                                        covered_m2 = float(m_num.group(1))
                                elif "tot" in f_text or "m²" in f_text or "m2" in f_text:
                                    m_num = re.search(r'(\d+)', f_text)
                                    if m_num:
                                        total_m2 = float(m_num.group(1))
                                elif "dorm" in f_text:
                                    d_num = re.search(r'(\d+)', f_text)
                                    if d_num:
                                        bedrooms = int(d_num.group(1))
                                elif "baño" in f_text:
                                    b_num = re.search(r'(\d+)', f_text)
                                    if b_num:
                                        bathrooms = int(b_num.group(1))

                            if total_m2 is None and covered_m2 is not None:
                                total_m2 = covered_m2

                            # Antiquity & Disposition
                            full_card_text = f"{title} {raw_location}".lower()
                            antiquity = None
                            ant_match = re.search(r'(\d+)\s*a[ñn]os?', full_card_text)
                            if ant_match:
                                antiquity = f"{ant_match.group(1)} años"
                            elif "estrenar" in full_card_text or "en pozo" in full_card_text:
                                antiquity = "A estrenar"

                            disposition = None
                            disp_match = re.search(r'\b(frente|contrafrente|lateral|interno)\b', full_card_text)
                            if disp_match:
                                disposition = disp_match.group(1).capitalize()

                            orientation = None
                            ori_match = re.search(r'\b(norte|sur|este|oeste|noreste|noroeste|sudeste|sudoeste)\b', full_card_text)
                            if ori_match:
                                orientation = ori_match.group(1).capitalize()

                            # Location
                            loc_elem = card.select_one(".card__title--primary, .card__location, .card__address")
                            raw_location = loc_elem.get_text(strip=True) if loc_elem else (zone or "CABA")
                            neigh, matched_zone = match_neighborhood(raw_location)

                            # Image
                            img_elem = card.select_one("img[src*='http'], img[data-src*='http']")
                            img_url = ""
                            if img_elem:
                                img_url = img_elem.get("src") or img_elem.get("data-src") or ""

                            # Inmobiliaria
                            seller_elem = card.select_one(".card__agency img, .card__contact-agency")
                            seller_name = seller_elem.get("alt", "") if seller_elem else "Inmobiliaria Argenprop"

                            pub_date = datetime.utcnow() - timedelta(days=random.randint(1, 30))

                            results.append({
                                "portal": "argenprop",
                                "external_id": ext_id,
                                "title": title,
                                "url": href,
                                "property_type": (property_type or "departamento").lower(),
                                "operation_type": "venta",
                                "price_usd": price_usd,
                                "price_currency_orig": "USD",
                                "price_amount_orig": price_usd,
                                "total_area_m2": total_m2,
                                "covered_area_m2": covered_m2,
                                "price_per_m2": round(price_usd / total_m2, 1) if total_m2 and total_m2 > 0 and price_usd > 0 else None,
                                "rooms": (bedrooms + 1) if bedrooms else 2,
                                "bedrooms": bedrooms,
                                "bathrooms": bathrooms,
                                "neighborhood": neigh,
                                "zone": matched_zone or zone or "CABA",
                                "city": "Buenos Aires",
                                "address": raw_location,
                                "antiquity": antiquity,
                                "disposition": disposition,
                                "orientation": orientation,
                                "images": [img_url] if img_url else [],
                                "seller_name": seller_name or "Inmobiliaria",
                                "seller_type": "inmobiliaria",
                                "publication_date": pub_date
                            })
                        except Exception:
                            continue
                except Exception:
                    break
        return results
