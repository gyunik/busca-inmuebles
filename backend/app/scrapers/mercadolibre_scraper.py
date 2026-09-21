import re
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import random
import httpx
from bs4 import BeautifulSoup
from backend.app.scrapers.base_scraper import BaseScraper
from backend.app.services.locations_catalog import match_neighborhood

class MercadoLibreScraper(BaseScraper):
    def __init__(self):
        super().__init__("mercadolibre")

    def _build_url(self, property_type: Optional[str], zone: Optional[str], page: int = 1) -> str:
        # types: departamentos, casas, ph
        type_path = "departamentos"
        if property_type:
            p_lower = property_type.lower()
            if "casa" in p_lower:
                type_path = "casas"
            elif "ph" in p_lower:
                type_path = "ph"
            else:
                type_path = "departamentos"

        # zones: capital-federal, bsas-gba-norte, bsas-gba-sur, bsas-gba-oeste
        zone_path = "capital-federal"
        if zone:
            z_lower = zone.lower()
            if "norte" in z_lower:
                zone_path = "bsas-gba-norte"
            elif "sur" in z_lower:
                zone_path = "bsas-gba-sur"
            elif "oeste" in z_lower:
                zone_path = "bsas-gba-oeste"
            else:
                zone_path = "capital-federal"

        base = f"https://inmuebles.mercadolibre.com.ar/{type_path}/venta/{zone_path}/"
        if page > 1:
            offset = (page - 1) * 48 + 1
            base = f"{base}_Desde_{offset}"
        return base

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
                    items = soup.select(".ui-search-layout__item, .poly-card, li.ui-search-layout__item")
                    if not items:
                        break

                    for item in items:
                        try:
                            # Link and Title
                            link_tag = item.select_one("a.ui-search-link, a.poly-component__title, a[href*='MLA'], a[href*='inmueble']")
                            if not link_tag:
                                continue
                            item_url = link_tag.get("href", "").split("#")[0].split("?")[0]
                            title = link_tag.get_text(strip=True) or (link_tag.get("title", "") if link_tag.has_attr("title") else "")
                            
                            # ID
                            match_id = re.search(r'MLA-?(\d+)', item_url)
                            ext_id = match_id.group(1) if match_id else str(hash(item_url))[:12]

                            # Price
                            price_elem = item.select_one(".andes-money-amount__fraction, .poly-price__current .andes-money-amount__fraction")
                            curr_elem = item.select_one(".andes-money-amount__currency-symbol, .poly-price__current .andes-money-amount__currency-symbol")
                            price_usd = 0.0
                            if price_elem:
                                raw_price = price_elem.get_text(strip=True).replace(".", "").replace(",", ".")
                                price_val = float(raw_price) if raw_price else 0.0
                                curr_symbol = (curr_elem.get_text(strip=True) if curr_elem else "USD").upper()
                                if any(u in curr_symbol for u in ["US$", "U$S", "USD", "DLS", "U$D"]):
                                    price_usd = price_val
                                elif "$" in curr_symbol:
                                    # ARS pesos converted to USD approximate
                                    price_usd = round(price_val / 1300.0, 0) if price_val > 100000 else price_val
                                else:
                                    price_usd = price_val

                            # Attributes: Area, Bedrooms, Rooms
                            attrs_elems = item.select(".ui-search-card-attributes__attribute, .poly-attributes_list__item, .poly-component__attributes li")
                            total_m2 = None
                            covered_m2 = None
                            bedrooms = None
                            rooms = None
                            
                            for attr in attrs_elems:
                                text = attr.get_text(strip=True).lower()
                                if "cubie" in text or "cub" in text:
                                    m_match = re.search(r'(\d+[\.,]?\d*)\s*m', text)
                                    if m_match:
                                        covered_m2 = float(m_match.group(1).replace(",", "."))
                                elif "tot" in text or "m²" in text or "m2" in text:
                                    m_match = re.search(r'(\d+[\.,]?\d*)\s*m', text)
                                    if m_match:
                                        total_m2 = float(m_match.group(1).replace(",", "."))
                                elif "dorm" in text or "hab" in text or "recám" in text:
                                    b_match = re.search(r'(\d+)', text)
                                    if b_match:
                                        bedrooms = int(b_match.group(1))
                                elif "amb" in text:
                                    r_match = re.search(r'(\d+)', text)
                                    if r_match:
                                        rooms = int(r_match.group(1))
                                        if bedrooms is None and rooms > 1:
                                            bedrooms = rooms - 1

                            if total_m2 is None and covered_m2 is not None:
                                total_m2 = covered_m2

                            # Location
                            loc_elem = item.select_one(".ui-search-item__location, .poly-component__location, .ui-search-item__group__element.ui-search-item__location")
                            raw_location = loc_elem.get_text(strip=True) if loc_elem else (zone or "CABA")
                            neigh, matched_zone = match_neighborhood(raw_location)

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

                            # Image
                            img_elem = item.select_one("img[src*='http'], img[data-src*='http']")
                            img_url = ""
                            if img_elem:
                                img_url = img_elem.get("data-src") or img_elem.get("src") or ""

                            # Default bathrooms estimate
                            bathrooms = 1
                            if bedrooms and bedrooms >= 3:
                                bathrooms = 2

                            # Publication date estimate
                            pub_date = datetime.utcnow() - timedelta(days=random.randint(1, 45))

                            prop_data = {
                                "portal": "mercadolibre",
                                "external_id": ext_id,
                                "title": title or f"{property_type or 'Inmueble'} en {neigh}",
                                "url": item_url,
                                "property_type": (property_type or "departamento").lower(),
                                "operation_type": "venta",
                                "price_usd": price_usd,
                                "price_currency_orig": "USD",
                                "price_amount_orig": price_usd,
                                "total_area_m2": total_m2,
                                "covered_area_m2": covered_m2,
                                "price_per_m2": round(price_usd / total_m2, 1) if total_m2 and total_m2 > 0 and price_usd > 0 else None,
                                "rooms": rooms,
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
                                "seller_name": "Inmobiliaria ML",
                                "seller_type": "inmobiliaria",
                                "publication_date": pub_date
                            }
                            results.append(prop_data)
                        except Exception:
                            continue
                except Exception:
                    break
        return results
