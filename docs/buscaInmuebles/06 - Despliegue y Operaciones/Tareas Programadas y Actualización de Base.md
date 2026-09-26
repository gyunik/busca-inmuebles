# Tareas Programadas y Actualización de Base

## Estrategia de Sincronización
1. **Barridos Periódicos:** Actualización nocturna y manual mediante el endpoint `/api/scraper/jobs`.
2. **Detección de Bajas:** Identificación de publicaciones que ya no responden en el portal fuente para marcarlas como inactivas o descartadas.
3. **Persistencia de Precios:** Cada cambio de cotización genera un registro en `PriceHistory` para trazar la curva histórica del inmueble.

---
[[index]] | [[Despliegue en Render y GitHub]]
