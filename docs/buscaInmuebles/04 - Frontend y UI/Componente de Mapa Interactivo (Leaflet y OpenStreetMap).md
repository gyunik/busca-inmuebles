# Componente de Mapa Interactivo (Leaflet y OpenStreetMap)

## Implementación (`MapView`)
- **Librería de Mapa:** Leaflet 1.9.4 con `Leaflet.markercluster 1.5.3`.
- **Servidor de Tiles:** OpenStreetMap oficial (`https://tile.openstreetmap.org/{z}/{x}/{y}.png`). No requiere API key ni expone marcas de agua.
- **Badges de Precio Zonaprop-Style:** Píldoras con formato `USD 120K` en fondo naranja (`#ff5a00`), bordes blancos y sombra.
- **Estados de Badges:**
  - `fav-pill`: Fondo carmesí (`#e11d48`) para favoritos.
  - `selected-pill`: Fondo negro con aro dorado al hacer clic.
- **FlyTo y Popups:** Animación suave al seleccionar un inmueble desde la lista y apertura de popup con fotos, precio, expensas y enlace directo al portal.

---
[[index]] | [[Sistema de Diseño Google Stitch]] | [[Clustering Geográfico y Normalización de Direcciones]]
