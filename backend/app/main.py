from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.app.core.config import APP_TITLE, APP_VERSION
from backend.app.core.database import Base, engine, SessionLocal
from backend.app.api.routes_properties import router as properties_router
from backend.app.api.routes_scraper import router as scraper_router
from backend.app.api.routes_export import router as export_router
from backend.app.services.scraper_runner import seed_initial_database_if_empty

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB schema
    Base.metadata.create_all(bind=engine)
    # Seed initial data if DB is empty
    db = SessionLocal()
    try:
        seed_initial_database_if_empty(db)
    finally:
        db.close()
    yield

app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    lifespan=lifespan
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(properties_router)
app.include_router(scraper_router)
app.include_router(export_router)

from pathlib import Path
from fastapi.staticfiles import StaticFiles

# Mount static web UI if available
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
else:
    @app.get("/")
    def read_root():
        return {
            "app": APP_TITLE,
            "version": APP_VERSION,
            "status": "online",
            "docs_url": "/docs"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
