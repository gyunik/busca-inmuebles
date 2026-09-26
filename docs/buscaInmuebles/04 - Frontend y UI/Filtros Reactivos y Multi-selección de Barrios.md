# Filtros Reactivos y Multi-selección de Barrios

## Panel de Filtros Lateral
1. **Tipo de Propiedad:** Checkboxes múltiples (Departamentos, Casas, PH) con conteo auditado.
2. **Barrios Multi-Selección:**
   - Chips rápidos de 1 clic: Parque Chas, Villa Urquiza, Villa del Parque, Palermo, Belgrano, Caballito, Villa Devoto, Recoleta.
   - Buscador desplegable por zonas (CABA, GBA Norte, GBA Sur, GBA Oeste).
   - Serialización de queries con `URLSearchParams` para consultar el total de la base SQL.
3. **Precio (USD):** Entradas `Mín` y `Máx` reactivas.
4. **Superficie Total ($m^2$):** Entradas `Mín m²` y `Máx m²`.
5. **Dormitorios:** Botones segmentados `1`, `2`, `3`, `4+`.
6. **Baños:** Botones segmentados `1+`, `2+`, `3+`.
7. **Fecha de Publicación:** Menú desplegable (*Cualquier fecha*, *Últimas 24hs*, *7 días*, *15 días*, *30 días*, *Más de 30 días*).
8. **Portales:** Checkboxes con conteos en tiempo real para Zonaprop, Mercado Libre, RE/MAX, Argenprop y Mudafy.

---
[[index]] | [[Sistema de Diseño Google Stitch]] | [[Especificación de API y Endpoints]]
