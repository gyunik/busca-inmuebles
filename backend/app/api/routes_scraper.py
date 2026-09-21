import asyncio
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from backend.app.core.database import get_db, SessionLocal
from backend.app.models.property_model import ScrapeJob
from backend.app.services.scraper_runner import execute_scrape_job, seed_initial_database_if_empty
from backend.app.services.deduplication_service import run_deduplication

router = APIRouter(prefix="/api/scrape", tags=["scraper"])

class ScrapeRequest(BaseModel):
    portal: str = "all" # "all", "mercadolibre", "zonaprop", "argenprop", "properati"
    property_type: Optional[str] = None # "departamento", "casa", "ph"
    zone: Optional[str] = None # "CABA", "GBA Norte", "GBA Sur", "GBA Oeste"

@router.post("/start")
async def start_scrape(req: ScrapeRequest, db: Session = Depends(get_db)):
    # Create job in database
    job = ScrapeJob(
        portal=req.portal,
        status="pending",
        zone=req.zone,
        property_type=req.property_type,
        message="Iniciando escaneo..."
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Launch background task directly in asyncio loop
    asyncio.create_task(
        execute_scrape_job(
            job_id=job.id,
            portal=req.portal,
            property_type=req.property_type,
            zone=req.zone
        )
    )

    return {
        "job_id": job.id,
        "status": "pending",
        "message": f"Escaneo iniciado para {req.portal}"
    }

@router.get("/jobs")
def get_jobs(limit: int = 10, db: Session = Depends(get_db)):
    jobs = db.query(ScrapeJob).order_by(ScrapeJob.started_at.desc()).limit(limit).all()
    return [j.to_dict() for j in jobs]

@router.post("/deduplicate")
def trigger_deduplication(db: Session = Depends(get_db)):
    clusters = run_deduplication(db)
    return {
        "status": "success",
        "clusters_detected": clusters,
        "message": f"Deduplicación completada. Se detectaron {clusters} grupos de inmuebles duplicados."
    }

@router.post("/seed")
def trigger_seed(db: Session = Depends(get_db)):
    seed_initial_database_if_empty(db)
    return {"status": "success", "message": "Datos de prueba y portales cargados con éxito."}
