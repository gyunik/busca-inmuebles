import re
import asyncio
import random
from typing import List, Dict, Any, Optional
from datetime import datetime
import httpx
from backend.app.scrapers.base_scraper import BaseScraper
from backend.app.services.locations_catalog import match_neighborhood

CDN_BASE = "https://d1acdg20u0pmxj.cloudfront.net"

class RemaxScraper(BaseScraper):
    def __init__(self):
        super().__init__("remax")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://www.remax.com.ar",
            "Referer": "https://www.remax.com.ar/",
        }

    async def scrape(
        self, 
        property_type: Optional[str] = None, 
        zone: Optional[str] = None, 
        max_pages: int = 5
    ) -> List[Dict[str, Any]]:
        results = []
        
        # RE/MAX numeric type mapping: ph=12, departamento_estandar=2, departamento_duplex=1, departamento_monoambiente=4, casa=9, casa_duplex=10
        type_filter = ""
        if property_type:
            p_low = property_type.lower()
            if "ph" in p_low:
                type_filter = "&in:type=12"
            elif "casa" in p_low:
                type_filter = "&in:type=9,10,11"
            elif "depto" in p_low or "departamento" in p_low:
                type_filter = "&in:type=1,2,4,8"

        async with httpx.AsyncClient(headers=self.headers, verify=False, follow_redirects=True, timeout=20.0) as client:
            for page in range(0, max_pages):
                url = f"https://api-ar.redremax.com/remaxweb-ar/api/listings/findAll?page={page}&pageSize=100&sort=-createdAt&in:operation_type=1{type_filter}"
                try:
                    resp = await client.get(url)
                    if resp.status_code != 200:
                        break
                        
                    data = resp.json()
                    items = data.get("data", {}).get("data", [])
                    if not items:
                        break
                        
                    for it in items:
                        try:
                            # Coordinates: [lon, lat]
                            coords = it.get("location", {}).get("coordinates") if isinstance(it.get("location"), dict) else []
                            lat = coords[1] if len(coords) >= 2 else None
                            lon = coords[0] if len(coords) >= 2 else None
                            
                            # Geographic filtering for CABA / GBA
                            is_in_target_region = False
                            if lat and lon and (-35.1 <= lat <= -34.2) and (-59.2 <= lon <= -58.1):
                                is_in_target_region = True
                                
                            addr = it.get("displayAddress") or ""
                            geo = it.get("geoLabel") or ""
                            title = it.get("title") or ""
                            
                            neigh, matched_zone = match_neighborhood(f"{geo} {addr} {title}")
                            
                            # If not matched by name, check coordinates
                            if not neigh and not is_in_target_region:
                                continue
                                
                            neigh = neigh or "Capital Federal"
                            matched_zone = matched_zone or ("Capital Federal" if "capital" in geo.lower() else "GBA")
                            
                            # Property type
                            t_obj = it.get("type")
                            t_val = (t_obj.get("value") if isinstance(t_obj, dict) else str(t_obj)).lower()
                            
                            p_type = "ph" if "ph" in t_val else ("casa" if "casa" in t_val else "departamento")
                            if property_type and property_type.lower() not in p_type.lower():
                                continue
                                
                            # Price & Currency
                            price_val = float(it.get("price") or 0.0)
                            if price_val <= 0:
                                continue
                                
                            curr = (it.get("currency", {}).get("value") if isinstance(it.get("currency"), dict) else "USD").upper()
                            price_usd = price_val
                            if curr == "ARS" and price_val > 100000:
                                price_usd = round(price_val / 1300.0, 0)
                                
                            # Photos
                            photos = []
                            for p in it.get("photos", []):
                                val = p.get("value") or p.get("rawValue")
                                if val:
                                    photos.append(f"{CDN_BASE}/{val}")
                                    
                            slug = it.get("slug") or str(it.get("id"))
                            item_url = f"https://www.remax.com.ar/listings/{slug}"
                            
                            tot_m2 = it.get("dimensionTotalBuilt") or it.get("dimensionCovered") or it.get("dimensionLand")
                            cov_m2 = it.get("dimensionCovered")
                            
                            results.append({
                                "portal": "remax",
                                "external_id": f"remax_{it.get('id')}",
                                "title": title or f"{p_type.upper()} en Venta en {neigh}",
                                "url": item_url,
                                "property_type": p_type,
                                "operation_type": "venta",
                                "price_usd": price_usd,
                                "expenses": it.get("expensesPrice"),
                                "total_area_m2": float(tot_m2) if tot_m2 else None,
                                "covered_area_m2": float(cov_m2) if cov_m2 else None,
                                "price_per_m2": round(price_usd / float(tot_m2), 1) if tot_m2 else None,
                                "rooms": it.get("totalRooms"),
                                "bedrooms": it.get("bedrooms"),
                                "bathrooms": it.get("bathrooms"),
                                "neighborhood": neigh,
                                "zone": matched_zone,
                                "city": "Buenos Aires",
                                "address": addr or neigh,
                                "latitude": lat,
                                "longitude": lon,
                                "description": it.get("title", ""),
                                "images": photos,
                                "seller_name": it.get("associate", {}).get("officeName") or "RE/MAX Argentina",
                                "seller_type": "inmobiliaria",
                                "publication_date": datetime.utcnow()
                            })
                        except Exception:
                            continue
                            
                    await asyncio.sleep(0.3)
                except Exception:
                    break
                    
        return results
