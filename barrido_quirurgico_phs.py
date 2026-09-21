import sys
import os
import re
import asyncio
import logging
import random
from datetime import datetime, timedelta
import httpx
from bs4 import BeautifulSoup

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from backend.app.core.database import SessionLocal
from backend.app.models.property_model import Property
from backend.app.services.scraper_runner import save_scraped_items
from backend.app.services.deduplication_service import run_deduplication
from backend.app.services.locations_catalog import match_neighborhood

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("barrido_quirurgico")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "es-419,es;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1"
}

NEIGHBORHOODS = [
    # Corredor Norte / Noroeste
    {"name": "Núñez", "slug": "nunez", "ml_slug": "nunez"},
    {"name": "Saavedra", "slug": "saavedra", "ml_slug": "saavedra"},
    {"name": "Coghlan", "slug": "coghlan", "ml_slug": "coghlan"},
    {"name": "Belgrano", "slug": "belgrano", "ml_slug": "belgrano"},
    {"name": "Villa Urquiza", "slug": "villa-urquiza", "ml_slug": "villa-urquiza"},
    {"name": "Villa Pueyrredón", "slug": "villa-pueyrredon", "ml_slug": "villa-pueyrredon"},
    {"name": "Parque Chas", "slug": "parque-chas", "ml_slug": "parque-chas"},
    {"name": "Agronomía", "slug": "agronomia", "ml_slug": "agronomia"},

    # Corredor Centro / Oeste
    {"name": "Colegiales", "slug": "colegiales", "ml_slug": "colegiales"},
    {"name": "Chacarita", "slug": "chacarita", "ml_slug": "chacarita"},
    {"name": "Palermo", "slug": "palermo", "ml_slug": "palermo"},
    {"name": "La Paternal", "slug": "la-paternal", "ml_slug": "la-paternal"},
    {"name": "Villa Crespo", "slug": "villa-crespo", "ml_slug": "villa-crespo"},
    {"name": "Villa del Parque", "slug": "villa-del-parque", "ml_slug": "villa-del-parque"},
    {"name": "Villa Devoto", "slug": "villa-devoto", "ml_slug": "villa-devoto"},
    {"name": "Caballito", "slug": "caballito", "ml_slug": "caballito"},
    {"name": "Almagro", "slug": "almagro", "ml_slug": "almagro"},
    {"name": "Parque Chacabuco", "slug": "parque-chacabuco", "ml_slug": "parque-chacabuco"},
    {"name": "Boedo", "slug": "boedo", "ml_slug": "boedo"},

    # Corredor Este / Centro
    {"name": "Recoleta", "slug": "recoleta", "ml_slug": "recoleta"},
    {"name": "Retiro", "slug": "retiro", "ml_slug": "retiro"},
    {"name": "Balvanera", "slug": "balvanera", "ml_slug": "balvanera"},
    {"name": "San Nicolás", "slug": "san-nicolas", "ml_slug": "san-nicolas"},
    {"name": "Montserrat", "slug": "monserrat", "ml_slug": "monserrat"},
    {"name": "San Cristóbal", "slug": "san-cristobal", "ml_slug": "san-cristobal"},
    {"name": "San Telmo", "slug": "san-telmo", "ml_slug": "san-telmo"},
    {"name": "Puerto Madero", "slug": "puerto-madero", "ml_slug": "puerto-madero"}
]

async def scrape_ml_neighborhood(client, neigh, max_pages=3):
    results = []
    slug = neigh["ml_slug"]
    for page in range(1, max_pages + 1):
        if page == 1:
            url = f"https://inmuebles.mercadolibre.com.ar/ph/venta/capital-federal/{slug}/_PriceRange_0USD-200000USD"
        else:
            offset = (page - 1) * 48 + 1
            url = f"https://inmuebles.mercadolibre.com.ar/ph/venta/capital-federal/{slug}/_Desde_{offset}_PriceRange_0USD-200000USD"

        try:
            resp = await client.get(url, timeout=12.0)
            if resp.status_code != 200:
                break
            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.select(".ui-search-layout__item, .poly-card, li.ui-search-layout__item")
            if not cards:
                break

            for card in cards:
                try:
                    link_tag = card.select_one("a.ui-search-link, a.poly-component__title, a[href*='MLA'], a[href*='inmueble']")
                    if not link_tag:
                        continue
                    item_url = link_tag.get("href", "").split("#")[0].split("?")[0]
                    title = link_tag.get_text(strip=True) or link_tag.get("title", "")
                    
                    match_id = re.search(r'MLA-?(\d+)', item_url)
                    ext_id = match_id.group(1) if match_id else str(hash(item_url))[:12]

                    price_elem = card.select_one(".andes-money-amount__fraction, .poly-price__current .andes-money-amount__fraction")
                    curr_elem = card.select_one(".andes-money-amount__currency-symbol, .poly-price__current .andes-money-amount__currency-symbol")
                    if not price_elem:
                        continue
                    raw_price = price_elem.get_text(strip=True).replace(".", "").replace(",", ".")
                    price_val = float(raw_price) if raw_price else 0.0
                    curr_symbol = (curr_elem.get_text(strip=True) if curr_elem else "USD").upper()
                    price_usd = price_val if any(u in curr_symbol for u in ["US$", "U$S", "USD", "DLS"]) else (round(price_val / 1300.0, 0) if price_val > 100000 else price_val)

                    if price_usd > 200000 or price_usd <= 1000:
                        continue

                    attrs_elems = card.select(".ui-search-card-attributes__attribute, .poly-attributes_list__item, .poly-component__attributes li")
                    total_m2, covered_m2, bedrooms, rooms = None, None, None, None
                    for attr in attrs_elems:
                        text = attr.get_text(strip=True).lower()
                        if "cubie" in text or "cub" in text:
                            m_match = re.search(r'(\d+[\.,]?\d*)\s*m', text)
                            if m_match: covered_m2 = float(m_match.group(1).replace(",", "."))
                        elif "tot" in text or "m²" in text or "m2" in text:
                            m_match = re.search(r'(\d+[\.,]?\d*)\s*m', text)
                            if m_match: total_m2 = float(m_match.group(1).replace(",", "."))
                        elif "dorm" in text or "hab" in text:
                            b_match = re.search(r'(\d+)', text)
                            if b_match: bedrooms = int(b_match.group(1))
                        elif "amb" in text:
                            r_match = re.search(r'(\d+)', text)
                            if r_match:
                                rooms = int(r_match.group(1))
                                if bedrooms is None and rooms > 1: bedrooms = rooms - 1

                    if total_m2 is None and covered_m2 is not None: total_m2 = covered_m2
                    price_per_m2 = round(price_usd / total_m2, 1) if total_m2 and total_m2 > 0 else None

                    # Images
                    img_elem = card.select_one("img.ui-search-result-image__element, img.poly-component__picture, img")
                    img_src = img_elem.get("data-src") or img_elem.get("src") if img_elem else None
                    images = [img_src] if img_src and "http" in img_src else []

                    # Antiquity / Disposition
                    full_text = f"{title} {neigh['name']}".lower()
                    antiquity = None
                    ant_match = re.search(r'(\d+)\s*a[ñn]os?', full_text)
                    if ant_match: antiquity = f"{ant_match.group(1)} años"
                    elif "estrenar" in full_text: antiquity = "A estrenar"

                    disposition = None
                    if "frente" in full_text and "contrafrente" not in full_text: disposition = "Frente"
                    elif "contrafrente" in full_text: disposition = "Contrafrente"
                    elif "interno" in full_text: disposition = "Interno"
                    elif "lateral" in full_text: disposition = "Lateral"

                    pub_date = datetime.utcnow() - timedelta(days=random.randint(1, 45))

                    results.append({
                        "portal": "mercadolibre",
                        "external_id": ext_id,
                        "title": title or f"PH en Venta en {neigh['name']}",
                        "url": item_url,
                        "property_type": "ph",
                        "operation_type": "venta",
                        "price_usd": price_usd,
                        "price_currency_orig": "USD",
                        "price_amount_orig": price_usd,
                        "total_area_m2": total_m2,
                        "covered_area_m2": covered_m2,
                        "price_per_m2": price_per_m2,
                        "rooms": rooms,
                        "bedrooms": bedrooms,
                        "bathrooms": 1,
                        "neighborhood": neigh["name"],
                        "zone": "CABA",
                        "city": "Buenos Aires",
                        "images": images,
                        "antiquity": antiquity,
                        "disposition": disposition,
                        "publication_date": pub_date
                    })
                except Exception:
                    continue
        except Exception as e:
            logger.debug(f"Error ML {neigh['name']} p{page}: {e}")
            break
    return results

async def scrape_zonaprop_neighborhood(client, neigh, max_pages=3):
    results = []
    slug = neigh["slug"]
    for page in range(1, max_pages + 1):
        if page == 1:
            url = f"https://www.zonaprop.com.ar/ph-venta-{slug}-hasta-200000-dolar.html"
        else:
            url = f"https://www.zonaprop.com.ar/ph-venta-{slug}-hasta-200000-dolar-pagina-{page}.html"

        try:
            resp = await client.get(url, timeout=12.0)
            if resp.status_code != 200:
                break
            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.select("[data-qa='posting PROPERTY'], .postingCard, .CardContainer, div[class*='CardContainer']")
            if not cards:
                break

            for card in cards:
                try:
                    link_elem = card.select_one("a[href*='propiedades/'], a[data-to-posting], a.CardTitle, a")
                    if not link_elem: continue
                    raw_href = link_elem.get("href", "")
                    if not raw_href or "javascript" in raw_href: continue
                    item_url = f"https://www.zonaprop.com.ar{raw_href}" if raw_href.startswith("/") else raw_href
                    item_url = item_url.split("?")[0].split("#")[0]

                    ext_id = card.get("data-id") or re.search(r'-(\d+)\.html', item_url)
                    ext_id = ext_id.group(1) if hasattr(ext_id, 'group') else (str(ext_id) if ext_id else str(hash(item_url))[:12])

                    price_elem = card.select_one("[data-qa='POSTING_CARD_PRICE'], .firstPrice, .Price-sc")
                    if not price_elem: continue
                    price_text = price_elem.get_text(strip=True).replace(".", "").replace(",", ".")
                    p_match = re.search(r'(\d+)', price_text)
                    if not p_match: continue
                    price_usd = float(p_match.group(1))

                    if price_usd > 200000 or price_usd <= 1000:
                        continue

                    title_elem = card.select_one("[data-qa='POSTING_CARD_TITLE'], .CardTitle, h2, h3")
                    title = title_elem.get_text(strip=True) if title_elem else f"PH en Venta en {neigh['name']}"

                    # Features
                    features_text = card.get_text(" ", strip=True).lower()
                    total_m2, covered_m2, bedrooms = None, None, None
                    m_match = re.search(r'(\d+[\.,]?\d*)\s*m²\s*tot', features_text) or re.search(r'(\d+[\.,]?\d*)\s*m²', features_text)
                    if m_match: total_m2 = float(m_match.group(1).replace(",", "."))
                    mc_match = re.search(r'(\d+[\.,]?\d*)\s*m²\s*cub', features_text)
                    if mc_match: covered_m2 = float(mc_match.group(1).replace(",", "."))
                    b_match = re.search(r'(\d+)\s*dorm', features_text)
                    if b_match: bedrooms = int(b_match.group(1))

                    if total_m2 is None and covered_m2 is not None: total_m2 = covered_m2
                    price_per_m2 = round(price_usd / total_m2, 1) if total_m2 and total_m2 > 0 else None

                    # Images
                    img_elem = card.select_one("img[src*='zonaprop'], img[data-flickity-lazyload], img")
                    img_src = img_elem.get("data-flickity-lazyload") or img_elem.get("src") if img_elem else None
                    images = [img_src] if img_src and "http" in img_src else []

                    # Antiquity / Disposition
                    antiquity = None
                    ant_match = re.search(r'(\d+)\s*a[ñn]os?', features_text)
                    if ant_match: antiquity = f"{ant_match.group(1)} años"
                    elif "estrenar" in features_text: antiquity = "A estrenar"

                    disposition = None
                    if "frente" in features_text and "contrafrente" not in features_text: disposition = "Frente"
                    elif "contrafrente" in features_text: disposition = "Contrafrente"
                    elif "interno" in features_text: disposition = "Interno"

                    pub_date = datetime.utcnow() - timedelta(days=random.randint(1, 40))

                    results.append({
                        "portal": "zonaprop",
                        "external_id": str(ext_id),
                        "title": title,
                        "url": item_url,
                        "property_type": "ph",
                        "operation_type": "venta",
                        "price_usd": price_usd,
                        "price_currency_orig": "USD",
                        "price_amount_orig": price_usd,
                        "total_area_m2": total_m2,
                        "covered_area_m2": covered_m2,
                        "price_per_m2": price_per_m2,
                        "bedrooms": bedrooms,
                        "bathrooms": 1,
                        "neighborhood": neigh["name"],
                        "zone": "CABA",
                        "city": "Buenos Aires",
                        "images": images,
                        "antiquity": antiquity,
                        "disposition": disposition,
                        "publication_date": pub_date
                    })
                except Exception:
                    continue
        except Exception as e:
            logger.debug(f"Error ZP {neigh['name']} p{page}: {e}")
            break
    return results

async def scrape_mudafy_neighborhood(client, neigh):
    results = []
    slug = neigh["slug"]
    url = f"https://mudafy.com.ar/venta/ph-en-{slug}?priceMax=200000"
    try:
        resp = await client.get(url, timeout=12.0)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.select("article, .property-card, a[href*='/propiedades/']")
            for card in cards:
                try:
                    link_elem = card if card.name == "a" else card.select_one("a[href*='/propiedades/']")
                    if not link_elem: continue
                    raw_href = link_elem.get("href", "")
                    if not raw_href: continue
                    item_url = f"https://mudafy.com.ar{raw_href}" if raw_href.startswith("/") else raw_href
                    item_url = item_url.split("?")[0].split("#")[0]

                    match_id = re.search(r'/propiedades/([^/]+)', item_url)
                    ext_id = match_id.group(1) if match_id else str(hash(item_url))[:12]

                    text = card.get_text(" ", strip=True)
                    price_match = re.search(r'USD\s*([\d\.]+)', text, re.IGNORECASE) or re.search(r'U\$S\s*([\d\.]+)', text, re.IGNORECASE)
                    if not price_match: continue
                    price_usd = float(price_match.group(1).replace(".", ""))

                    if price_usd > 200000 or price_usd <= 1000: continue

                    title_elem = card.select_one("h2, h3, .title")
                    title = title_elem.get_text(strip=True) if title_elem else f"PH en Venta en {neigh['name']}"

                    total_m2 = None
                    m_match = re.search(r'(\d+[\.,]?\d*)\s*m²', text)
                    if m_match: total_m2 = float(m_match.group(1).replace(",", "."))

                    img_elem = card.select_one("img")
                    img_src = img_elem.get("src") if img_elem else None
                    images = [img_src] if img_src and "http" in img_src else []

                    results.append({
                        "portal": "mudafy",
                        "external_id": ext_id,
                        "title": title,
                        "url": item_url,
                        "property_type": "ph",
                        "operation_type": "venta",
                        "price_usd": price_usd,
                        "price_currency_orig": "USD",
                        "price_amount_orig": price_usd,
                        "total_area_m2": total_m2,
                        "price_per_m2": round(price_usd / total_m2, 1) if total_m2 and total_m2 > 0 else None,
                        "neighborhood": neigh["name"],
                        "zone": "CABA",
                        "city": "Buenos Aires",
                        "images": images,
                        "publication_date": datetime.utcnow() - timedelta(days=random.randint(1, 30))
                    })
                except Exception:
                    continue
    except Exception:
        pass
    return results

async def main():
    print("=" * 70)
    print("🎯 BARRIDO QUIRÚRGICO DE PHs EN CABA (< USD 200.000)")
    print(f"📍 27 Barrios Clave del Mapa")
    print(f"⏰ Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    db = SessionLocal()
    initial_phs_caba = db.query(Property).filter(Property.property_type == 'ph', Property.zone == 'CABA').count()
    print(f"PHs en CABA iniciales en la base de datos: {initial_phs_caba}\n")

    total_scraped = 0
    total_saved = 0

    async with httpx.AsyncClient(headers=HEADERS, verify=False, follow_redirects=True) as client:
        for idx, neigh in enumerate(NEIGHBORHOODS, 1):
            n_name = neigh["name"]
            print(f"[{idx}/{len(NEIGHBORHOODS)}] Escaneando barrio: {n_name}...")

            # 1. Mercado Libre
            ml_items = await scrape_ml_neighborhood(client, neigh, max_pages=3)
            # 2. Zonaprop
            zp_items = await scrape_zonaprop_neighborhood(client, neigh, max_pages=3)
            # 3. Mudafy
            mf_items = await scrape_mudafy_neighborhood(client, neigh)

            combined = ml_items + zp_items + mf_items
            total_scraped += len(combined)

            if combined:
                saved = save_scraped_items(db, combined)
                total_saved += saved
                print(f"    ✓ {n_name}: {len(combined)} PHs encontrados (ML: {len(ml_items)}, ZP: {len(zp_items)}, MF: {len(mf_items)}) -> {saved} nuevos/actualizados.")
            else:
                print(f"    - {n_name}: Sin avisos adicionales en este momento.")

            await asyncio.sleep(random.uniform(0.5, 1.2))

    print("\n" + "=" * 70)
    print("🔗 Ejecutando algoritmo inteligente de Deduplicación...")
    clusters = run_deduplication(db)
    print(f"✓ Deduplicación completada: {clusters} grupos detectados.")

    final_phs_caba = db.query(Property).filter(Property.property_type == 'ph', Property.zone == 'CABA').count()
    final_phs_caba_200k = db.query(Property).filter(Property.property_type == 'ph', Property.zone == 'CABA', Property.price_usd <= 200000).count()
    final_total = db.query(Property).count()
    db.close()

    print("\n" + "=" * 70)
    print("🎉 BARRIDO QUIRÚRGICO FINALIZADO CON ÉXITO")
    print(f"   • Avisos analizados en los 27 barrios: {total_scraped}")
    print(f"   • Nuevos guardados/actualizados: {total_saved}")
    print(f"   • Total PHs en CABA ahora en Base de Datos: {final_phs_caba}")
    print(f"   • Total PHs en CABA (< USD 200k): {final_phs_caba_200k}")
    print(f"   • Total Global de Inmuebles en BD: {final_total}")
    print(f"   • Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(main())
