# Despliegue en Render y GitHub

## Infraestructura en la Nube
- **Hosting:** Render (Web Service gratuito con reinicio automático).
- **Dominio Público:** `https://busca-inmuebles.onrender.com`
- **Integración Continua:** Conectado a la rama `main` del repositorio `gyunik/busca-inmuebles`.
- **Comando de Build:** `pip install -r requirements.txt`
- **Comando de Inicio:** `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`

## Variables de Entorno Clave
- `PORT`: Asignado dinámicamente por Render.
- `DATABASE_URL`: `sqlite:///./backend/data/inmuebles.db` (o PostgreSQL en tiers superiores).

---
[[index]] | [[Tareas Programadas y Actualización de Base]]
