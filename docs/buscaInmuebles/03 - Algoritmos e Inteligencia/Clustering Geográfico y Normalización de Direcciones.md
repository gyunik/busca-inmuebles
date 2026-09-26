# Clustering Geográfico y Normalización de Direcciones

## Coordenadas de Referencia por Barrio
Cuando un portal no suministra latitud y longitud exactas, el sistema utiliza el diccionario de coordenadas barriales (`NEIGHBORHOOD_COORDS`) con un algoritmo de dispersión (*jittering*) para evitar superposiciones directas en el mapa.

## Normalización de Ubicación
- Normalización de acentos y sinónimos (ej. `Monserrat` $\leftrightarrow$ `Montserrat`, `Villa Gral Mitre` $\leftrightarrow$ `Villa General Mitre`).
- Agrupamiento por Zonas:
  - **CABA** (48 barrios oficiales)
  - **GBA Norte** (Vicente López, San Isidro, Tigre, etc.)
  - **GBA Sur** (Quilmes, Lanús, Avellaneda, etc.)
  - **GBA Oeste** (Morón, Ramos Mejía, Castelar, etc.)

---
[[index]] | [[Motor de Deduplicación Cruzada entre Portales]] | [[Componente de Mapa Interactivo (Leaflet y OpenStreetMap)]]
