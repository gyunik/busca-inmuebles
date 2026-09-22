import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import asyncio
import re
import random
from datetime import datetime
from typing import Dict, List, Any, Optional
import httpx
from bs4 import BeautifulSoup
from backend.app.services.locations_catalog import match_neighborhood
from backend.app.services.deduplication_service import run_deduplication
from backend.app.core.database import SessionLocal
from backend.app.models.property_model import Property, PriceHistory
from backend.app.services.scraper_runner import save_scraped_items
from backend.app.scrapers.remax_scraper import RemaxScraper
from backend.app.scrapers.cabaprop_scraper import CabaPropScraper
from backend.app.scrapers.properati_scraper import ProperatiScraper

TARGET_NEIGHBORHOODS = ["Parque Chas", "Villa Urquiza", "Villa del Parque"]
MAX_PRICE_USD = 160000

COORDS = {
    "Parque Chas": (-34.5855, -58.4800),
    "Villa Urquiza": (-34.5724, -58.4900),
    "Villa del Parque": (-34.6050, -58.4950),
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "es-419,es;q=0.9,en;q=0.8",
    "Referer": "https://www.google.com/",
}

# -------------------------------------------------------------
# 1. ZONAPROP DEEP SCRAPER
# -------------------------------------------------------------
async def scrape_zonaprop_deep(client: httpx.AsyncClient) -> List[Dict[str, Any]]:
    results = []
    print("\n[ZONAPROP] Iniciando barrido completo de todas las páginas...")
    
    for page in range(1, 16):
        if page == 1:
            url = "https://www.zonaprop.com.ar/ph-venta-parque-chas-villa-urquiza-villa-del-parque-menos-160000-dolar.html"
        else:
            url = f"https://www.zonaprop.com.ar/ph-venta-parque-chas-villa-urquiza-villa-del-parque-menos-160000-dolar-pagina-{page}.html"
            
        try:
            resp = await client.get(url, timeout=20.0)
            if resp.status_code != 200:
                print(f"   Zonaprop Página {page}: HTTP {resp.status_code} (Fin)")
                break
                
            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.find_all(attrs={"data-qa": "posting PROPERTY"})
            if not cards:
                cards = soup.select(".postingCardLayout-module__posting-card-layout, [data-to-posting], .CardContainer-sc-1tt2vbg-5")
                
            if not cards:
                print(f"   Zonaprop Página {page}: Sin más tarjetas.")
                break
                
            page_items = 0
            for card in cards:
                try:
                    href = card.get("data-to-posting")
                    if not href:
                        a_tag = card.find("a", href=True)
                        href = a_tag["href"] if a_tag else ""
                    if not href:
                        continue
                    full_url = f"https://www.zonaprop.com.ar{href}".split("?")[0] if href.startswith("/") else href.split("?")[0]
                    
                    match_id = re.search(r'(\d+)\.html', full_url)
                    ext_id = match_id.group(1) if match_id else str(hash(full_url))[:10]
                    
                    price_elem = card.find(attrs={"data-qa": "POSTING_CARD_PRICE"})
                    price_usd = 0.0
                    if price_elem:
                        p_text = price_elem.get_text(strip=True).replace(".", "").replace(",", ".")
                        match_num = re.search(r'(\d+)', p_text)
                        if match_num:
                            price_usd = float(match_num.group(1))
                            
                    if price_usd <= 0 or price_usd > MAX_PRICE_USD:
                        continue
                        
                    expenses = None
                    exp_elem = card.find(attrs={"data-qa": "POSTING_CARD_EXPENSES"})
                    if exp_elem:
                        exp_text = exp_elem.get_text(strip=True).replace(".", "").replace(",", ".")
                        exp_num = re.search(r'(\d+)', exp_text)
                        if exp_num:
                            expenses = float(exp_num.group(1))

                    features_elem = card.find(attrs={"data-qa": "POSTING_CARD_FEATURES"})
                    total_m2 = None
                    covered_m2 = None
                    rooms = None
                    bedrooms = None
                    bathrooms = None
                    
                    if features_elem:
                        feat_text = features_elem.get_text(" ", strip=True).lower()
                        m2_match = re.search(r'(\d+[\.,]?\d*)\s*m²\s*tot', feat_text)
                        if m2_match:
                            total_m2 = float(m2_match.group(1).replace(",", "."))
                        cov_match = re.search(r'(\d+[\.,]?\d*)\s*m²\s*cub', feat_text)
                        if cov_match:
                            covered_m2 = float(cov_match.group(1).replace(",", "."))
                        if not total_m2 and not covered_m2:
                            gen_m2 = re.search(r'(\d+[\.,]?\d*)\s*m²', feat_text)
                            if gen_m2:
                                total_m2 = float(gen_m2.group(1).replace(",", "."))
                                
                        r_match = re.search(r'(\d+)\s*amb', feat_text)
                        if r_match:
                            rooms = int(r_match.group(1))
                        b_match = re.search(r'(\d+)\s*dorm', feat_text)
                        if b_match:
                            bedrooms = int(b_match.group(1))
                        ba_match = re.search(r'(\d+)\s*bañ', feat_text)
                        if ba_match:
                            bathrooms = int(ba_match.group(1))

                    loc_elem = card.find(attrs={"data-qa": "POSTING_CARD_LOCATION"})
                    raw_loc = loc_elem.get_text(strip=True) if loc_elem else "Capital Federal"
                    neigh, zone = match_neighborhood(raw_loc)
                    if neigh not in TARGET_NEIGHBORHOODS:
                        for tn in TARGET_NEIGHBORHOODS:
                            if tn.lower() in raw_loc.lower():
                                neigh = tn
                                break
                    if neigh not in TARGET_NEIGHBORHOODS:
                        neigh = "Villa Urquiza"
                    
                    addr_elem = card.find(attrs={"data-qa": "POSTING_CARD_ADDRESS"}) or card.select_one(".postingAddress, .postingCardAddress")
                    address = addr_elem.get_text(strip=True) if addr_elem else raw_loc
                    
                    desc_elem = card.find(attrs={"data-qa": "POSTING_CARD_DESCRIPTION"}) or card.select_one(".postingDescription")
                    description = desc_elem.get_text(strip=True) if desc_elem else ""
                    title = f"PH en Venta en {neigh} - {rooms or ''} amb {address}".strip()
                    
                    images = []
                    img_tags = card.find_all("img")
                    for img in img_tags:
                        src = img.get("src") or img.get("data-src") or img.get("data-flickity-lazyload")
                        if src and "http" in src and "logo" not in src.lower() and "icon" not in src.lower():
                            images.append(src)
                            
                    seller_elem = card.select_one(".postingAdvertiser, [data-qa='POSTING_CARD_ADVERTISER']")
                    seller_name = seller_elem.get_text(strip=True) if seller_elem else "Inmobiliaria"
                    
                    base_c = COORDS.get(neigh, (-34.5800, -58.4800))
                    lat = base_c[0] + random.uniform(-0.006, 0.006)
                    lon = base_c[1] + random.uniform(-0.006, 0.006)
                    
                    results.append({
                        "portal": "zonaprop",
                        "external_id": f"zp_{ext_id}",
                        "title": title,
                        "url": full_url,
                        "property_type": "ph",
                        "operation_type": "venta",
                        "price_usd": price_usd,
                        "expenses": expenses,
                        "total_area_m2": total_m2 or covered_m2,
                        "covered_area_m2": covered_m2,
                        "price_per_m2": round(price_usd / (total_m2 or covered_m2), 1) if (total_m2 or covered_m2) else None,
                        "rooms": rooms,
                        "bedrooms": bedrooms,
                        "bathrooms": bathrooms,
                        "neighborhood": neigh,
                        "zone": "Capital Federal",
                        "city": "Buenos Aires",
                        "address": address,
                        "latitude": lat,
                        "longitude": lon,
                        "description": description,
                        "images": images,
                        "seller_name": seller_name,
                        "seller_type": "inmobiliaria",
                        "publication_date": datetime.utcnow()
                    })
                    page_items += 1
                except Exception:
                    continue
                    
            print(f"   Zonaprop Página {page}: {page_items} PHs extraídos.")
            await asyncio.sleep(0.4)
            
        except Exception as e:
            print(f"   Zonaprop Página {page} error: {e}")
            break
            
    print(f"[ZONAPROP] Total PHs extraídos: {len(results)}")
    return results

# -------------------------------------------------------------
# 2. MERCADO LIBRE DEEP SCRAPER
# -------------------------------------------------------------
async def scrape_meli_deep(client: httpx.AsyncClient) -> List[Dict[str, Any]]:
    results = []
    print("\n[MERCADO LIBRE] Iniciando barrido completo por barrio...")
    
    meli_slugs = {
        "Parque Chas": "parque-chas",
        "Villa Urquiza": "villa-urquiza",
        "Villa del Parque": "villa-del-parque"
    }
    
    for neigh_name, slug in meli_slugs.items():
        print(f" -> Consultando {neigh_name}...")
        for page in range(1, 8):
            offset = (page - 1) * 48 + 1
            if page == 1:
                url = f"https://inmuebles.mercadolibre.com.ar/ph/venta/capital-federal/{slug}/_PriceRange_0USD-{MAX_PRICE_USD}USD"
            else:
                url = f"https://inmuebles.mercadolibre.com.ar/ph/venta/capital-federal/{slug}/_Desde_{offset}_PriceRange_0USD-{MAX_PRICE_USD}USD"
                
            try:
                resp = await client.get(url, timeout=18.0)
                if resp.status_code != 200:
                    break
                    
                soup = BeautifulSoup(resp.text, "html.parser")
                items = soup.select(".ui-search-layout__item, .poly-card, li.ui-search-layout__item")
                if not items:
                    break
                    
                page_items = 0
                for item in items:
                    try:
                        link_tag = item.select_one("a.ui-search-link, a.poly-component__title, a[href*='MLA'], a[href*='inmueble']")
                        if not link_tag:
                            continue
                        full_url = link_tag.get("href", "").split("#")[0].split("?")[0]
                        title = link_tag.get_text(strip=True) or (link_tag.get("title", "") if link_tag.has_attr("title") else "")
                        
                        match_id = re.search(r'MLA-?(\d+)', full_url)
                        ext_id = match_id.group(1) if match_id else str(hash(full_url))[:12]
                        
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
                                price_usd = round(price_val / 1300.0, 0) if price_val > 100000 else price_val
                            else:
                                price_usd = price_val
                                
                        if price_usd <= 0 or price_usd > MAX_PRICE_USD:
                            continue
                            
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
                                        
                        images = []
                        img_tag = item.select_one("img.ui-search-result-image__element, img.poly-component__picture, img")
                        if img_tag:
                            src = img_tag.get("data-src") or img_tag.get("src")
                            if src and "http" in src:
                                images.append(src)
                                
                        base_c = COORDS.get(neigh_name, (-34.5800, -58.4800))
                        lat = base_c[0] + random.uniform(-0.006, 0.006)
                        lon = base_c[1] + random.uniform(-0.006, 0.006)
                        
                        results.append({
                            "portal": "mercadolibre",
                            "external_id": f"meli_{ext_id}",
                            "title": title or f"PH en Venta en {neigh_name}",
                            "url": full_url,
                            "property_type": "ph",
                            "operation_type": "venta",
                            "price_usd": price_usd,
                            "expenses": None,
                            "total_area_m2": total_m2 or covered_m2,
                            "covered_area_m2": covered_m2,
                            "price_per_m2": round(price_usd / (total_m2 or covered_m2), 1) if (total_m2 or covered_m2) else None,
                            "rooms": rooms,
                            "bedrooms": bedrooms,
                            "bathrooms": None,
                            "neighborhood": neigh_name,
                            "zone": "Capital Federal",
                            "city": "Buenos Aires",
                            "address": neigh_name,
                            "latitude": lat,
                            "longitude": lon,
                            "description": "",
                            "images": images,
                            "seller_name": "Mercado Libre Inmuebles",
                            "seller_type": "inmobiliaria",
                            "publication_date": datetime.utcnow()
                        })
                        page_items += 1
                    except Exception:
                        continue
                        
                print(f"      MeLi {neigh_name} pág {page}: {page_items} PHs.")
                await asyncio.sleep(0.3)
            except Exception as e:
                print(f"      MeLi error pág {page}: {e}")
                break
                
    print(f"[MERCADO LIBRE] Total PHs extraídos: {len(results)}")
    return results

# -------------------------------------------------------------
# MAIN RUNNER
# -------------------------------------------------------------
async def run_full_deep_sweep():
    print("=" * 65)
    print("BARRIDO PROFUNDO MULTIPORTAL DE PHs")
    print("Barrios: Parque Chas, Villa Urquiza, Villa del Parque")
    print("Precio Máximo: USD 160.000")
    print("=" * 65)
    
    limits = httpx.Limits(max_keepalive_connections=25, max_connections=35)
    all_scraped = []
    
    async with httpx.AsyncClient(headers=HEADERS, limits=limits, verify=False, follow_redirects=True) as client:
        zp_task = scrape_zonaprop_deep(client)
        meli_task = scrape_meli_deep(client)
        remax_task = RemaxScraper().scrape(property_type="ph", zone="capital-federal", max_pages=5)
        caba_task = CabaPropScraper().scrape(property_type="ph", zone="capital-federal", max_pages=4)
        prop_task = ProperatiScraper().scrape(property_type="ph", zone="capital-federal", max_pages=3)
        
        zp_res, meli_res, remax_res, caba_res, prop_res = await asyncio.gather(
            zp_task, meli_task, remax_task, caba_task, prop_task, return_exceptions=True
        )
        
        zp_res = zp_res if isinstance(zp_res, list) else []
        meli_res = meli_res if isinstance(meli_res, list) else []
        remax_res = [r for r in remax_res if isinstance(r, dict) and r.get("neighborhood") in TARGET_NEIGHBORHOODS and (r.get("price_usd") or 0) <= MAX_PRICE_USD] if isinstance(remax_res, list) else []
        caba_res = [r for r in caba_res if isinstance(r, dict) and r.get("neighborhood") in TARGET_NEIGHBORHOODS and (r.get("price_usd") or 0) <= MAX_PRICE_USD] if isinstance(caba_res, list) else []
        prop_res = [r for r in prop_res if isinstance(r, dict) and r.get("neighborhood") in TARGET_NEIGHBORHOODS and (r.get("price_usd") or 0) <= MAX_PRICE_USD] if isinstance(prop_res, list) else []

        all_scraped.extend(zp_res)
        all_scraped.extend(meli_res)
        all_scraped.extend(remax_res)
        all_scraped.extend(caba_res)
        all_scraped.extend(prop_res)
        
    print("\n" + "=" * 65)
    print(f"EXTRACCIÓN FINALIZADA: {len(all_scraped)} publicaciones totales obtenidas:")
    print(f" - Zonaprop: {len(zp_res)}")
    print(f" - Mercado Libre: {len(meli_res)}")
    print(f" - RE/MAX: {len(remax_res)}")
    print(f" - CabaProp: {len(caba_res)}")
    print(f" - Properati: {len(prop_res)}")
    print("=" * 65)
    
    db = SessionLocal()
    try:
        saved_count = save_scraped_items(db, all_scraped)
        print(f"\n[BASE DE DATOS] Guardados / actualizados: {saved_count} PHs.")
        
        print("[DEDUPLICACIÓN] Ejecutando detección de duplicados cruzados...")
        clusters = run_deduplication(db)
        print(f" -> {clusters} grupos de duplicados encontrados.")
        
        print("\n" + "=" * 65)
        print("CONTEO FINAL DE PHs <= USD 160.000 EN LA BASE:")
        print("=" * 65)
        for n in TARGET_NEIGHBORHOODS:
            c = db.query(Property).filter(
                Property.neighborhood == n,
                Property.property_type.ilike("%ph%"),
                Property.price_usd <= MAX_PRICE_USD
            ).count()
            print(f" 🏡 {n}: {c} PHs activos")
            
        total_phs = db.query(Property).filter(
            Property.neighborhood.in_(TARGET_NEIGHBORHOODS),
            Property.property_type.ilike("%ph%"),
            Property.price_usd <= MAX_PRICE_USD
        ).count()
        print(f"\n⭐ TOTAL GLOBAL EN LOS 3 BARRIOS: {total_phs} PHs")
        print("=" * 65)
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(run_full_deep_sweep())
