# Modelo de Datos de Inmuebles e Historial de Precios

## Modelo `Property` (`property_model.py`)

Campos clave de la entidad:
- `id` (PK)
- `portal` (`zonaprop`, `mercadolibre`, `remax`, `argenprop`, `mudafy`)
- `external_id`: ID original en la plataforma fuente.
- `title`: Título de la publicación.
- `property_type`: Tipo normalizado (`ph`, `departamento`, `casa`).
- `operation_type`: `venta` o `alquiler`.
- `price_usd`: Precio en dólares estadounidenses.
- `price_per_m2`: Precio calculado por $m^2$.
- `total_area_m2` y `covered_area_m2`.
- `bedrooms`, `bathrooms`, `has_garage`.
- `neighborhood` y `zone` (CABA, GBA Norte, GBA Sur, GBA Oeste).
- `latitude` y `longitude` (coordenadas georreferenciadas).
- `cluster_id`: Identificador para agrupar duplicados entre portales.
- `is_favorite`: Marcado por el usuario.
- `is_discarded`: Descartado del listado.
- `user_notes`: Notas privadas del usuario.

## Modelo `PriceHistory`
- `property_id` (FK a `properties.id`)
- `price_usd`
- `recorded_at`: Timestamp de variación.

---
[[index]] | [[Stack Técnico (FastAPI, SQLAlchemy, SQLite)]] | [[Motor de Deduplicación Cruzada entre Portales]]
