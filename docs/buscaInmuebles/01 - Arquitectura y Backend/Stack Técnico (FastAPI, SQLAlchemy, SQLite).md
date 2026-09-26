# Stack Técnico (FastAPI, SQLAlchemy, SQLite)

## Componentes Principales
- **Framework Web:** FastAPI (ASGI de alto rendimiento).
- **ORM:** SQLAlchemy con soporte para consultas dinámicas y filtros complejos.
- **Base de Datos:** SQLite (`backend/data/inmuebles.db`) con esquema optimizado para búsquedas geoespaciales y filtros multi-campo.
- **Servidor ASGI:** Uvicorn.
- **Tareas en Segundo Plano:** BackgroundTasks de FastAPI para escaneos asíncronos.

```text
FastAPI Endpoints (routes_properties.py)
       │
       ▼
SQLAlchemy Session (database.py)
       │
       ▼
SQLite Database (inmuebles.db) <── Ingesta desde Scrapers
```

---
[[index]] | [[Modelo de Datos de Inmuebles e Historial de Precios]] | [[Especificación de API y Endpoints]]
