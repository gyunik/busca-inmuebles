import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from backend.app.services.locations_catalog import CATALOG_BY_ZONE

REAL_ESTATE_IMAGES = [
    "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1600566753190-17f0baa2a6c3?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=800&q=80",
    "https://images.unsplash.com/photo-1502005229762-ee1b2b93e083?auto=format&fit=crop&w=800&q=80"
]

AGENCIES = [
    "Remax Premium", "Toribio Achával", "LJ Ramos Brokers", "Tizado Propiedades",
    "D'Aria Propiedades", "Lepore Propiedades", "Baigun Operaciones", "Korn Propiedades",
    "Izrastzoff Real Estate", "Duarte Propiedades", "Dueño Directo"
]

def generate_sample_listings(count: int = 250) -> List[Dict[str, Any]]:
    listings = []
    types_weights = [("departamento", 0.55), ("casa", 0.25), ("ph", 0.20)]
    portals = ["mercadolibre", "zonaprop", "argenprop", "properati"]
    
    # 1. Generate deliberate duplicate clusters first
    cluster_templates = [
        {
            "p_type": "ph", "neigh": "Palermo", "zone": "CABA", "bedrooms": 2, "bathrooms": 2, "m2": 85,
            "base_price": 165000, "street": "Thames al 1800",
            "desc": "Hermoso PH sin expensas reciclado a nuevo con terraza propia y parrilla en pleno Palermo Soho."
        },
        {
            "p_type": "departamento", "neigh": "Belgrano", "zone": "CABA", "bedrooms": 3, "bathrooms": 2, "m2": 110,
            "base_price": 240000, "street": "Av. Cabildo al 2100",
            "desc": "Semipiso al frente con balcón corrido, cochera fija cubierta y baulera. Vista abierta."
        },
        {
            "p_type": "departamento", "neigh": "Caballito", "zone": "CABA", "bedrooms": 1, "bathrooms": 1, "m2": 48,
            "base_price": 89000, "street": "Av. Pedro Goyena al 900",
            "desc": "2 ambientes moderno con amenities, piscina, sum y solarium sobre la mejor cuadra de Goyena."
        },
        {
            "p_type": "casa", "neigh": "Olivos", "zone": "GBA Norte", "bedrooms": 3, "bathrooms": 3, "m2": 220,
            "base_price": 340000, "street": "Margarita Weild al 1200",
            "desc": "Excelente chalet en dos plantas, jardín parquizado, piscina climatizada y quincho con parrilla."
        },
        {
            "p_type": "ph", "neigh": "Villa Urquiza", "zone": "CABA", "bedrooms": 2, "bathrooms": 1, "m2": 72,
            "base_price": 135000, "street": "Bucarelli al 2400",
            "desc": "PH tipo casa al contrafrente con patio propio, techos altos, muy luminoso y bajas expensas."
        },
        {
            "p_type": "departamento", "neigh": "Recoleta", "zone": "CABA", "bedrooms": 2, "bathrooms": 2, "m2": 95,
            "base_price": 210000, "street": "Av. Callao al 1500",
            "desc": "Elegante departamento estilo francés en edificio señorial. Techos altos, pisos de roble y doble entrada."
        },
        {
            "p_type": "casa", "neigh": "Ramos Mejía", "zone": "GBA Oeste", "bedrooms": 3, "bathrooms": 2, "m2": 180,
            "base_price": 195000, "street": "Av. de Mayo al 800",
            "desc": "Casa sobre lote propio en Ramos Mejía sur con garaje para 2 autos, patio y terraza."
        },
        {
            "p_type": "departamento", "neigh": "Quilmes", "zone": "GBA Sur", "bedrooms": 2, "bathrooms": 1, "m2": 68,
            "base_price": 95000, "street": "Alsina al 200",
            "desc": "Semipiso en centro de Quilmes con vista panorámica, balcón terraza y bajas expensas."
        }
    ]

    item_id_counter = 1000

    # Create duplicates across portals for each template
    for tpl in cluster_templates:
        # Create in 2 to 4 portals
        selected_portals = random.sample(portals, k=random.randint(2, 4))
        for p_idx, portal in enumerate(selected_portals):
            item_id_counter += 1
            # slight variation in price or description
            price_variance = random.choice([0, 2000, -3000, 5000, -1500])
            prop_price = tpl["base_price"] + price_variance
            area_var = random.choice([0, 1, -1, 2])
            prop_m2 = tpl["m2"] + area_var
            agency = random.choice(AGENCIES)
            days_ago = random.randint(1, 28)
            
            listings.append({
                "portal": portal,
                "external_id": f"{portal[:3].upper()}-{item_id_counter}",
                "title": f"{tpl['p_type'].upper()} en Venta {prop_m2}m² - {tpl['neigh']} ({agency})",
                "url": f"https://www.{portal}.com.ar/inmueble/prop-{item_id_counter}",
                "property_type": tpl["p_type"],
                "operation_type": "venta",
                "price_usd": float(prop_price),
                "price_currency_orig": "USD",
                "price_amount_orig": float(prop_price),
                "expenses": random.choice([0, 18000, 35000, 65000, 95000]) if tpl["p_type"] != "casa" else 0,
                "total_area_m2": float(prop_m2),
                "covered_area_m2": float(prop_m2 - 5),
                "price_per_m2": round(prop_price / prop_m2, 1),
                "rooms": tpl["bedrooms"] + 1,
                "bedrooms": tpl["bedrooms"],
                "bathrooms": tpl["bathrooms"],
                "garages": 1 if tpl["p_type"] == "casa" or prop_m2 > 100 else 0,
                "neighborhood": tpl["neigh"],
                "zone": tpl["zone"],
                "city": "Buenos Aires",
                "address": tpl["street"],
                "description": tpl["desc"],
                "images": [random.choice(REAL_ESTATE_IMAGES)],
                "seller_name": agency,
                "seller_type": "inmobiliaria",
                "publication_date": datetime.utcnow() - timedelta(days=days_ago)
            })

    # 2. Generate random distributed listings
    remaining_count = max(count - len(listings), 50)
    for _ in range(remaining_count):
        item_id_counter += 1
        zone = random.choices(["CABA", "GBA Norte", "GBA Sur", "GBA Oeste"], weights=[0.60, 0.20, 0.10, 0.10])[0]
        neigh = random.choice(CATALOG_BY_ZONE[zone])
        
        p_type = random.choices(["departamento", "casa", "ph"], weights=[0.65, 0.20, 0.15])[0]
        portal = random.choice(portals)
        agency = random.choice(AGENCIES)

        if p_type == "departamento":
            bedrooms = random.choices([1, 2, 3, 4], weights=[0.40, 0.40, 0.16, 0.04])[0]
            rooms = bedrooms + 1
            bathrooms = 1 if bedrooms <= 2 else random.choice([2, 3])
            m2 = float(random.randint(32 + bedrooms * 15, 60 + bedrooms * 35))
            # Price per m2 varies between $1400 and $3200 depending on zone
            price_m2_factor = random.uniform(1600, 3100) if zone == "CABA" else random.uniform(1100, 2200)
            price_usd = round((m2 * price_m2_factor) / 1000) * 1000
            expenses = random.randint(15000, 85000)
        elif p_type == "ph":
            bedrooms = random.choices([1, 2, 3], weights=[0.25, 0.55, 0.20])[0]
            rooms = bedrooms + 1
            bathrooms = 1 if bedrooms <= 2 else 2
            m2 = float(random.randint(50 + bedrooms * 15, 90 + bedrooms * 25))
            price_m2_factor = random.uniform(1500, 2600) if zone == "CABA" else random.uniform(1000, 1800)
            price_usd = round((m2 * price_m2_factor) / 1000) * 1000
            expenses = random.choice([0, 0, 12000, 25000])
        else: # casa
            bedrooms = random.choices([2, 3, 4, 5], weights=[0.20, 0.50, 0.25, 0.05])[0]
            rooms = bedrooms + 2
            bathrooms = random.choice([2, 3, 4])
            m2 = float(random.randint(120, 380))
            price_m2_factor = random.uniform(1100, 2200)
            price_usd = round((m2 * price_m2_factor) / 1000) * 1000
            expenses = 0

        days_ago = random.randint(0, 45)
        pub_date = datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(0, 23))

        listings.append({
            "portal": portal,
            "external_id": f"{portal[:3].upper()}-{item_id_counter}",
            "title": f"{p_type.capitalize()} en Venta {int(m2)}m² en {neigh} - {bedrooms} dorm.",
            "url": f"https://www.{portal}.com.ar/propiedad/{p_type}-{item_id_counter}",
            "property_type": p_type,
            "operation_type": "venta",
            "price_usd": float(price_usd),
            "price_currency_orig": "USD",
            "price_amount_orig": float(price_usd),
            "expenses": expenses,
            "total_area_m2": m2,
            "covered_area_m2": round(m2 * 0.9, 1),
            "price_per_m2": round(price_usd / m2, 1),
            "rooms": rooms,
            "bedrooms": bedrooms,
            "bathrooms": bathrooms,
            "garages": 1 if (p_type == "casa" or m2 > 100) else 0,
            "neighborhood": neigh,
            "zone": zone,
            "city": "Buenos Aires",
            "address": f"Calle {random.randint(100, 4500)}",
            "description": f"Excelente oportunidad de {p_type} en {neigh}. Ubicación privilegiada, luminoso, cerca de avenidas principales y medios de transporte.",
            "images": [random.choice(REAL_ESTATE_IMAGES)],
            "seller_name": agency,
            "seller_type": "inmobiliaria",
            "publication_date": pub_date
        })

    return listings
