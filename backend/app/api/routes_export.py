from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from datetime import datetime, timedelta

from backend.app.core.database import get_db
from backend.app.models.property_model import Property
from backend.app.services.export_service import export_properties_to_excel

router = APIRouter(prefix="/api/export", tags=["export"])

@router.get("/excel")
def export_excel(
    property_types: Optional[List[str]] = Query(None),
    neighborhoods: Optional[List[str]] = Query(None),
    zones: Optional[List[str]] = Query(None),
    portals: Optional[List[str]] = Query(None),
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_area: Optional[float] = None,
    max_area: Optional[float] = None,
    min_bedrooms: Optional[int] = None,
    max_bedrooms: Optional[int] = None,
    days_ago: Optional[int] = None,
    date_filter: Optional[str] = None,
    search_query: Optional[str] = None,
    only_favorites: bool = False,
    include_discarded: bool = False,
    db: Session = Depends(get_db)
):
    query = db.query(Property)

    if not include_discarded:
        query = query.filter(Property.is_discarded == False)
        
    if only_favorites:
        query = query.filter(Property.is_favorite == True)

    if property_types:
        cleaned_types = [t.lower() for t in property_types]
        query = query.filter(Property.property_type.in_(cleaned_types))

    if portals:
        cleaned_portals = [p.lower() for p in portals]
        query = query.filter(Property.portal.in_(cleaned_portals))

    if neighborhoods:
        query = query.filter(Property.neighborhood.in_(neighborhoods))

    if zones:
        query = query.filter(Property.zone.in_(zones))

    if min_price is not None:
        query = query.filter(Property.price_usd >= min_price)
    if max_price is not None:
        query = query.filter(Property.price_usd <= max_price)

    if min_area is not None:
        query = query.filter(Property.total_area_m2 >= min_area)
    if max_area is not None:
        query = query.filter(Property.total_area_m2 <= max_area)

    if min_bedrooms is not None:
        if min_bedrooms >= 4:
            query = query.filter(Property.bedrooms >= 4)
        else:
            query = query.filter(Property.bedrooms >= min_bedrooms)
            
    if max_bedrooms is not None and max_bedrooms < 4:
        query = query.filter(Property.bedrooms <= max_bedrooms)

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

    if search_query and search_query.strip():
        term = f"%{search_query.strip()}%"
        query = query.filter(
            or_(
                Property.title.ilike(term),
                Property.neighborhood.ilike(term),
                Property.address.ilike(term)
            )
        )

    properties = query.order_by(Property.price_usd.asc()).all()
    excel_stream = export_properties_to_excel(properties)

    filename = f"inmuebles_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    headers = {
        "Content-Disposition": f"attachment; filename={filename}"
    }

    return StreamingResponse(
        excel_stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers
    )
