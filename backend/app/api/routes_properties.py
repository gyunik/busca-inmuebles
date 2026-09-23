from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, asc
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from backend.app.core.database import get_db
from backend.app.models.property_model import Property, PriceHistory
from backend.app.services.locations_catalog import CATALOG_BY_ZONE

router = APIRouter(prefix="/api/properties", tags=["properties"])

class NoteUpdate(BaseModel):
    notes: str

@router.get("")
def get_properties(
    property_types: Optional[List[str]] = Query(None),
    property_type: Optional[str] = None,
    neighborhoods: Optional[List[str]] = Query(None),
    neighborhood: Optional[str] = None,
    zones: Optional[List[str]] = Query(None),
    zone: Optional[str] = None,
    portals: Optional[List[str]] = Query(None),
    portal: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_area: Optional[float] = None,
    max_area: Optional[float] = None,
    min_bedrooms: Optional[int] = None,
    max_bedrooms: Optional[int] = None,
    min_bathrooms: Optional[int] = None,
    days_ago: Optional[int] = None,
    date_filter: Optional[str] = None,
    search_query: Optional[str] = None,
    search: Optional[str] = None,
    only_favorites: bool = False,
    include_discarded: bool = False,
    group_duplicates: bool = False,
    sort_by: str = "newest",
    page: int = 1,
    page_size: int = 30,
    db: Session = Depends(get_db)
):
    query = db.query(Property)

    # Normalize singular vs plural params
    if not property_types and property_type:
        property_types = [property_type]
    if not neighborhoods and neighborhood:
        neighborhoods = [neighborhood]
    if not zones and zone:
        zones = [zone]
    if not portals and portal:
        portals = [portal]
    if not search_query and search:
        search_query = search

    # Discarded filter
    if not include_discarded:
        query = query.filter(Property.is_discarded == False)
        
    # Favorites filter
    if only_favorites:
        query = query.filter(Property.is_favorite == True)

    # Property types
    if property_types:
        cleaned_types = [t.lower() for t in property_types if t]
        if cleaned_types:
            query = query.filter(Property.property_type.in_(cleaned_types))

    # Portals
    if portals:
        cleaned_portals = [p.lower() for p in portals if p]
        if cleaned_portals:
            query = query.filter(Property.portal.in_(cleaned_portals))

    # Neighborhoods (Multi-select)
    if neighborhoods:
        cleaned_neighs = [n for n in neighborhoods if n]
        if cleaned_neighs:
            query = query.filter(Property.neighborhood.in_(cleaned_neighs))

    # Zones
    if zones:
        cleaned_zones = [z for z in zones if z]
        if cleaned_zones:
            query = query.filter(Property.zone.in_(cleaned_zones))

    # Price range
    if min_price is not None:
        query = query.filter(Property.price_usd >= min_price)
    if max_price is not None:
        query = query.filter(Property.price_usd <= max_price)

    # Area range
    if min_area is not None:
        query = query.filter(Property.total_area_m2 >= min_area)
    if max_area is not None:
        query = query.filter(Property.total_area_m2 <= max_area)

    # Bedrooms
    if min_bedrooms is not None:
        if min_bedrooms >= 4:
            query = query.filter(Property.bedrooms >= 4)
        else:
            query = query.filter(Property.bedrooms >= min_bedrooms)
            
    if max_bedrooms is not None and max_bedrooms < 4:
        query = query.filter(Property.bedrooms <= max_bedrooms)

    # Bathrooms
    if min_bathrooms is not None:
        query = query.filter(Property.bathrooms >= min_bathrooms)

    # Publication date filter
    if date_filter == "last_1":
        query = query.filter(Property.publication_date >= datetime.utcnow() - timedelta(days=1))
    elif date_filter == "last_7":
        query = query.filter(Property.publication_date >= datetime.utcnow() - timedelta(days=7))
    elif date_filter == "last_15":
        query = query.filter(Property.publication_date >= datetime.utcnow() - timedelta(days=15))
    elif date_filter == "last_30":
        query = query.filter(Property.publication_date >= datetime.utcnow() - timedelta(days=30))
    elif date_filter == "older_30":
        query = query.filter(Property.publication_date < datetime.utcnow() - timedelta(days=30))
    elif days_ago is not None and days_ago > 0:
        since_date = datetime.utcnow() - timedelta(days=days_ago)
        query = query.filter(Property.publication_date >= since_date)

    # Search keyword
    if search_query and search_query.strip():
        term = f"%{search_query.strip()}%"
        query = query.filter(
            or_(
                Property.title.ilike(term),
                Property.neighborhood.ilike(term),
                Property.address.ilike(term),
                Property.description.ilike(term),
                Property.seller_name.ilike(term)
            )
        )

    # Sorting
    if sort_by == "price_asc":
        query = query.order_by(asc(Property.price_usd))
    elif sort_by == "price_desc":
        query = query.order_by(desc(Property.price_usd))
    elif sort_by == "price_m2_asc":
        query = query.order_by(asc(Property.price_per_m2))
    elif sort_by == "price_m2_desc":
        query = query.order_by(desc(Property.price_per_m2))
    elif sort_by == "area_desc":
        query = query.order_by(desc(Property.total_area_m2))
    elif sort_by == "area_asc":
        query = query.order_by(asc(Property.total_area_m2))
    else: # newest
        query = query.order_by(desc(Property.publication_date), desc(Property.id))

    all_matched = query.all()
    total_count = len(all_matched)

    # Deduplication grouping logic if requested
    if group_duplicates:
        seen_clusters = {}
        unique_results = []
        for p in all_matched:
            p_dict = p.to_dict()
            p_dict["duplicates"] = []
            if p.cluster_id:
                if p.cluster_id in seen_clusters:
                    # Append this item as a duplicate under the cluster's primary item
                    item_copy = p.to_dict()
                    seen_clusters[p.cluster_id]["duplicates"].append(item_copy)
                    # If this duplicate is cheaper, update display price
                    if p.price_usd < seen_clusters[p.cluster_id].get("best_price_usd", seen_clusters[p.cluster_id]["price_usd"]):
                        seen_clusters[p.cluster_id]["best_price_usd"] = p.price_usd
                else:
                    first_copy = p.to_dict()
                    p_dict["duplicates"] = [first_copy]
                    p_dict["best_price_usd"] = p.price_usd
                    seen_clusters[p.cluster_id] = p_dict
                    unique_results.append(p_dict)
            else:
                p_dict["duplicates"] = []
                p_dict["best_price_usd"] = p.price_usd
                unique_results.append(p_dict)
                
        total_count = len(unique_results)
        offset = (page - 1) * page_size
        items = unique_results[offset : offset + page_size]
        return {
            "items": items,
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size if page_size else 1
        }
    else:
        offset = (page - 1) * page_size
        items = []
        for p in all_matched[offset : offset + page_size]:
            d = p.to_dict()
            if p.cluster_id:
                cluster_siblings = db.query(Property).filter(
                    Property.cluster_id == p.cluster_id,
                    Property.is_discarded == False
                ).all()
                d["duplicates"] = [s.to_dict() for s in cluster_siblings]
            else:
                d["duplicates"] = []
            items.append(d)

        return {
            "items": items,
            "total": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size if page_size else 1
        }

@router.get("/catalog/locations")
@router.get("/locations-catalog")
@router.get("/catalog")
def get_locations():
    return CATALOG_BY_ZONE

@router.get("/stats/summary")
@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    total = db.query(Property).filter(Property.is_discarded == False).count()
    favorites = db.query(Property).filter(Property.is_favorite == True).count()
    
    # Counts by property type
    types = {}
    for t, in db.query(Property.property_type).filter(Property.is_discarded == False).all():
        types[t] = types.get(t, 0) + 1

    # Counts by portal
    portals = {}
    for p, in db.query(Property.portal).filter(Property.is_discarded == False).all():
        portals[p] = portals.get(p, 0) + 1

    # Counts by zone
    zones = {}
    for z, in db.query(Property.zone).filter(Property.is_discarded == False).all():
        zones[z] = zones.get(z, 0) + 1

    return {
        "total_properties": total,
        "total_favorites": favorites,
        "by_type": types,
        "by_portal": portals,
        "by_zone": zones
    }

@router.get("/{property_id}")
def get_property(property_id: int, db: Session = Depends(get_db)):
    p = db.query(Property).filter(Property.id == property_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Inmueble no encontrado")
        
    data = p.to_dict()
    # Get price history
    history = db.query(PriceHistory).filter(PriceHistory.property_id == p.id).order_by(PriceHistory.recorded_at.asc()).all()
    data["price_history"] = [{"price_usd": h.price_usd, "recorded_at": h.recorded_at.isoformat()} for h in history]
    
    # Get duplicate copies in other portals if cluster_id is present
    if p.cluster_id:
        duplicates = db.query(Property).filter(Property.cluster_id == p.cluster_id, Property.id != p.id).all()
        data["duplicates"] = [d.to_dict() for d in duplicates]
    else:
        data["duplicates"] = []
        
    return data

@router.post("/{property_id}/favorite")
def toggle_favorite(property_id: int, db: Session = Depends(get_db)):
    p = db.query(Property).filter(Property.id == property_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Inmueble no encontrado")
    p.is_favorite = not p.is_favorite
    db.commit()
    return {"id": p.id, "is_favorite": p.is_favorite}

@router.post("/{property_id}/discard")
def toggle_discard(property_id: int, db: Session = Depends(get_db)):
    p = db.query(Property).filter(Property.id == property_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Inmueble no encontrado")
    p.is_discarded = not p.is_discarded
    db.commit()
    return {"id": p.id, "is_discarded": p.is_discarded}

@router.post("/{property_id}/notes")
def update_notes(property_id: int, note_data: NoteUpdate, db: Session = Depends(get_db)):
    p = db.query(Property).filter(Property.id == property_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Inmueble no encontrado")
    p.user_notes = note_data.notes
    db.commit()
    return {"id": p.id, "user_notes": p.user_notes}
