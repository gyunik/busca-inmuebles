import re
import hashlib
from typing import List, Dict, Set, Tuple
from sqlalchemy.orm import Session
from backend.app.models.property_model import Property

def normalize_type(t: str) -> str:
    if not t:
        return 'otro'
    t = t.lower().strip()
    if 'casa' in t:
        return 'casa'
    if 'ph' in t:
        return 'ph'
    if 'dep' in t:
        return 'departamento'
    return t

def extract_street_and_number(text: str) -> Tuple[str, str]:
    if not text:
        return ('', '')
    text_clean = text.lower().replace('.', '').replace(',', '')
    match = re.search(r'([a-záéíóúñ\s]{3,30})\s+(\d{2,5})', text_clean)
    if match:
        street = match.group(1).strip()
        num = match.group(2).strip()
        # filter out common words like ambientes, pisos, etc.
        if not any(w in street for w in ['ambiente', 'dormitorio', 'piso', 'cuadra', 'metro', 'venta', 'alquiler']):
            return (street, num)
    return ('', '')

def are_duplicate_pair(p1: Property, p2: Property) -> bool:
    if p1.id == p2.id:
        return False
        
    # 1. Must match normalized property type
    t1 = normalize_type(p1.property_type)
    t2 = normalize_type(p2.property_type)
    if t1 != t2:
        return False

    # 2. Must match neighborhood
    n1 = (p1.neighborhood or '').lower().strip()
    n2 = (p2.neighborhood or '').lower().strip()
    if not n1 or not n2 or n1 != n2:
        return False

    # 3. Price check: MUST be within 10% maximum difference
    if not p1.price_usd or not p2.price_usd or p1.price_usd <= 0 or p2.price_usd <= 0:
        return False
    price_diff = abs(p1.price_usd - p2.price_usd) / max(p1.price_usd, p2.price_usd)
    if price_diff > 0.10:
        return False

    # 4. Bedrooms / Rooms check
    if p1.bedrooms is not None and p2.bedrooms is not None:
        if p1.bedrooms != p2.bedrooms:
            return False
    elif p1.rooms is not None and p2.rooms is not None:
        if abs(p1.rooms - p2.rooms) > 1:
            return False

    # 5. Surface Area check (m2): MUST be within 5% or 3m2
    if p1.total_area_m2 and p2.total_area_m2 and p1.total_area_m2 > 0 and p2.total_area_m2 > 0:
        area_diff = abs(p1.total_area_m2 - p2.total_area_m2) / max(p1.total_area_m2, p2.total_area_m2)
        if area_diff > 0.05 and abs(p1.total_area_m2 - p2.total_area_m2) > 3.0:
            return False
    elif (p1.total_area_m2 and not p2.total_area_m2) or (not p1.total_area_m2 and p2.total_area_m2):
        # One has area and the other doesn't: require tighter price match (<5%)
        if price_diff > 0.05:
            return False

    # 6. Address / Street verification
    st1, num1 = extract_street_and_number(f"{p1.address or ''} {p1.title or ''}")
    st2, num2 = extract_street_and_number(f"{p2.address or ''} {p2.title or ''}")
    
    if st1 and num1 and st2 and num2:
        # Both have numbers: if numbers differ, they are distinct properties!
        if num1 != num2:
            return False
        # If numbers match and street shares words, it is a guaranteed duplicate
        if any(w in st2 for w in st1.split() if len(w) > 3):
            return True

    # 7. If no exact street number, require very strict price and title token similarity
    if price_diff > 0.06:
        return False

    # Check title/description token overlap
    tokens1 = set(re.findall(r'\b[a-záéíóúñ]{4,}\b', (p1.title or '').lower()))
    tokens2 = set(re.findall(r'\b[a-záéíóúñ]{4,}\b', (p2.title or '').lower()))
    
    # Common generic words to ignore
    ignore_words = {'venta', 'departamento', 'excelente', 'oportunidad', 'hermoso', 'luminoso', 'inmueble', 'balcon', 'barrio', 'chico', 'soho', 'norte', 'oeste', 'buenos', 'aires', 'capital', 'federal'}
    tokens1 = tokens1 - ignore_words
    tokens2 = tokens2 - ignore_words
    
    if tokens1 and tokens2:
        overlap = len(tokens1.intersection(tokens2)) / min(len(tokens1), len(tokens2))
        if overlap >= 0.35:
            return True

    # If area and price are virtually identical (<2% price diff, <2m2 area diff)
    if price_diff <= 0.02 and p1.total_area_m2 and p2.total_area_m2 and abs(p1.total_area_m2 - p2.total_area_m2) <= 1.5:
        return True

    return False

def run_deduplication(db: Session):
    properties: List[Property] = db.query(Property).filter(Property.is_discarded == False).all()
    if not properties:
        return 0

    # Reset all existing clusters first
    for p in properties:
        p.cluster_id = None
        p.cluster_confidence = None

    # Group candidates by (type, neighborhood) to avoid O(N^2) comparison across entire DB
    candidate_buckets: Dict[str, List[Property]] = {}
    for p in properties:
        t = normalize_type(p.property_type)
        n = (p.neighborhood or '').lower().strip()
        key = f"{t}_{n}"
        if key not in candidate_buckets:
            candidate_buckets[key] = []
        candidate_buckets[key].append(p)

    clusters_count = 0
    cluster_idx = 1

    # Find connected components in each bucket
    for key, bucket in candidate_buckets.items():
        if len(bucket) < 2:
            continue

        adj: Dict[int, Set[int]] = {p.id: set() for p in bucket}
        prop_map = {p.id: p for p in bucket}

        n_items = len(bucket)
        for i in range(n_items):
            p1 = bucket[i]
            for j in range(i + 1, n_items):
                p2 = bucket[j]
                if are_duplicate_pair(p1, p2):
                    adj[p1.id].add(p2.id)
                    adj[p2.id].add(p1.id)

        # BFS / DFS connected components
        visited = set()
        for p in bucket:
            if p.id not in visited and adj[p.id]:
                component = []
                queue = [p.id]
                visited.add(p.id)
                while queue:
                    curr_id = queue.pop(0)
                    component.append(prop_map[curr_id])
                    for neighbor_id in adj[curr_id]:
                        if neighbor_id not in visited:
                            visited.add(neighbor_id)
                            queue.append(neighbor_id)

                if len(component) > 1:
                    cluster_id = f"c_{cluster_idx:04d}"
                    cluster_idx += 1
                    clusters_count += 1
                    for cp in component:
                        cp.cluster_id = cluster_id
                        cp.cluster_confidence = 0.95

    db.commit()
    return clusters_count
