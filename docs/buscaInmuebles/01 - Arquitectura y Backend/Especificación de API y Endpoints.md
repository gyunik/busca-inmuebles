# Especificación de API y Endpoints

Prefijo base: `/api`

## Inmuebles (`routes_properties.py`)
- `GET /api/properties`: Búsqueda paginada con filtros (`neighborhoods`, `property_types`, `portals`, `min_price`, `max_price`, `min_area`, `max_area`, `min_bedrooms`, `min_bathrooms`, `date_filter`, `group_duplicates`).
- `GET /api/properties/stats`: Retorna resumen en tiempo real del inventario por portal, tipo de propiedad y zona.
- `GET /api/properties/catalog/locations`: Catálogo normalizado de barrios agrupados por CABA y zonas de GBA.
- `GET /api/properties/{id}`: Detalle de una propiedad con historial de precios y duplicados en otros portales.
- `POST /api/properties/{id}/favorite`: Conmuta estado favorito.
- `POST /api/properties/{id}/discard`: Conmuta descarte.
- `POST /api/properties/{id}/notes`: Guarda o actualiza notas privadas.

## Scrapers y Exportación
- `POST /api/scraper/jobs`: Dispara trabajo de scraping en segundo plano.
- `GET /api/export/excel`: Descarga base completa en formato Excel (`.xlsx`).

---
[[index]] | [[Stack Técnico (FastAPI, SQLAlchemy, SQLite)]]
