# CHANGELOG - Busca Inmuebles AR

Todas las modificaciones notables del proyecto están documentadas aquí.

---

## [1.3.0] - 2026-09-23
### Agregado
- Integración completa del sistema de diseño Google Stitch UI.
- Restauración de filtros en la barra lateral: Rango de Precios, Superficie Total ($m^2$), Dormitorios (1, 2, 3, 4+), Baños (1+, 2+, 3+) y Fecha de Publicación.
- Selector multi-barrio para CABA y GBA con chips de acceso rápido (Parque Chas, Villa Urquiza, Villa del Parque, etc.).
- Conteo dinámico en vivo en la barra lateral para los 5 portales y 3 tipos de inmuebles.
- Reemplazo de capa CartoDB por OpenStreetMap oficial (`tile.openstreetmap.org`) para eliminar marca de agua *API KEY REQUIRED*.

## [1.2.0] - 2026-09-22
### Agregado
- Motor de scraping RE/MAX Argentina (`remax_scraper.py`) conectado a API REST y CDN CloudFront.
- Ingesta de 979 propiedades de RE/MAX alcanzando **6.070 propiedades totales** en base de datos.
- Deduplicación cruzada entre Zonaprop, Mercado Libre, RE/MAX y Argenprop.

## [1.1.0] - 2026-09-21
### Agregado
- Despliegue en Render (`busca-inmuebles.onrender.com`).
- Exportación a Excel (`/api/export/excel`).
- Persistencia de favoritos, notas privadas y descarte de inmuebles.

## [1.0.0] - 2026-09-20
### Inicial
- Creación de arquitectura backend FastAPI y base SQLite.
- Scrapers iniciales para Zonaprop, Mercado Libre, Argenprop y Mudafy.
- Mapa interactivo con clustering Leaflet y badges de precio Zonaprop-style.

---
[[index]]
