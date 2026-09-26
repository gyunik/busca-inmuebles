# Motor de Deduplicación Cruzada entre Portales

## 🔍 El Problema
Los propietarios publican la misma propiedad con múltiples inmobiliarias. Cada portal la lista con pequeñas variaciones:
- Títulos diferentes (ej. "Hermoso PH en Parque Chas" vs "PH 3 amb sin expensas Urquiza").
- Precios dispares (ej. USD 135.000 vs USD 142.000).
- Variaciones de $m^2$ de $\pm 5\%$.

## 🧠 El Algoritmo (`deduplication_service.py`)
1. **Filtro de Barrio y Tipo:** Mismo barrio (`neighborhood`) y mismo tipo (`ph`, `departamento`, `casa`).
2. **Proximidad de Metraje:** $|m^2_A - m^2_B| \le \max(3, 0.05 \times m^2_A)$.
3. **Proximidad de Ambientes/Dormitorios:** Mismo número de dormitorios o ambientes.
4. **Distancia Geográfica / Coordenadas:** Distancia euclidiana o Haversine $\le 150\text{ metros}$.
5. **Cluster ID:** Si coinciden las reglas, se les asigna un `cluster_id` unificado.

El frontend permite colapsar duplicados en una sola tarjeta y abre un comparador visual para consultar todos los portales donde está publicada.

---
[[index]] | [[Clustering Geográfico y Normalización de Direcciones]] | [[Sistema de Diseño Google Stitch]]
