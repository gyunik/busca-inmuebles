# LLM Wiki - Contexto del Proyecto

Guía de contexto para asistentes de Inteligencia Artificial que trabajen en este repositorio.

---

## 🎯 Objetivo del Sistema
Plataforma de inteligencia inmobiliaria que consolida la oferta de propiedades en CABA y GBA, detecta inmuebles duplicados publicados en múltiples portales con precios diferentes, y ofrece analítica de mercado en tiempo real.

## 🧱 Arquitectura y Convenciones
1. **Backend:** FastAPI montado en Python 3.11+.
   - Modelos SQLAlchemy en `backend/app/models/`.
   - Endpoints en `backend/app/api/`.
   - Base de datos SQLite local en `backend/data/inmuebles.db`.
2. **Frontend:** React 18 en CDN standalone con Tailwind CSS y Leaflet dentro de `backend/app/static/index.html`.
3. **Scrapers:** Ubicados en `backend/app/scrapers/`. Todos heredan o implementan la interfaz estándar de extracción y guardan en el modelo unificado `Property`.
4. **Despliegue:** Render Free Web Service conectado a `origin/main` en GitHub (`gyunik/busca-inmuebles`).

## 🔑 Parámetros Clave de Filtrado
- `neighborhoods: List[str]` (Soporte multi-barrio mediante `URLSearchParams`).
- `property_types: List[str]` (`ph`, `departamento`, `casa`).
- `portals: List[str]` (`zonaprop`, `mercadolibre`, `remax`, `argenprop`, `mudafy`).
- `min_price` y `max_price` (USD).
- `min_area` y `max_area` ($m^2$).
- `min_bedrooms` y `min_bathrooms`.

---
[[index]]
