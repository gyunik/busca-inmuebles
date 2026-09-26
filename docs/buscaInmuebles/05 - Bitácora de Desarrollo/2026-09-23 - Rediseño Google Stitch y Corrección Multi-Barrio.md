# 2026-09-23 - Rediseño Google Stitch y Corrección Multi-Barrio

- Adaptación del frontend a la estética Google Stitch UI (paleta cromática, tipografía Plus Jakarta Sans y Material Symbols).
- Solución al problema de conteos en cero `(0)` en la barra lateral mediante desacople del endpoint `/api/properties/stats`.
- Corrección del filtrado multi-barrio: paso a `URLSearchParams` para enviar arrays a FastAPI (`Property.neighborhood.in_(neighborhoods)`).
- Verificación de consulta conjunta: Parque Chas + Villa Urquiza + Villa del Parque retornando 672 propiedades.

---
[[index]] | [[2026-09-22 - Integración de RE-MAX y 6.070 Inmuebles]] | [[2026-09-23 - Restauración de Filtros y Capa de Mapa]]
