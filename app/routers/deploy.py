from fastapi import APIRouter, Depends, Body
from hindsight_client import Hindsight
from groq import AsyncGroq
import structlog

from app.config import Settings, get_settings
from app.dependencies import get_hindsight, get_groq, verify_api_key
from app.models import DeployEvent, IncidentReport, RiskAnalysis
from app.agent_core import analyze_deploy, report_incident
from app.routers.ws import manager
from app.db import Project
logger = structlog.get_logger()
router = APIRouter(prefix="/deploy", tags=["deploy"])

@router.post("/analyze", response_model=RiskAnalysis)
async def analyze(
    event: DeployEvent = Body(...),
    hindsight: Hindsight = Depends(get_hindsight),
    groq: AsyncGroq = Depends(get_groq),
    settings: Settings = Depends(get_settings),
    project: Project = Depends(verify_api_key)
):
    result = await analyze_deploy(event, hindsight, groq, settings)
    logger.info(
        "Deployment analyzed",
        service=event.service,
        risk_level=result.risk_level,
        risk_score=result.risk_score,
        memories_used=result.memories_used,
        project_id=project.id
    )
    await manager.broadcast({"type": "refresh_memories", "service": event.service})
    return result

@router.post("/incident")
async def incident(
    report: IncidentReport = Body(...),
    hindsight: Hindsight = Depends(get_hindsight),
    settings: Settings = Depends(get_settings),
    project: Project = Depends(verify_api_key)
):
    await report_incident(report, hindsight, settings)
    logger.info(
        "Incident reported",
        service=report.service,
        severity=report.severity,
        project_id=project.id
    )
    await manager.broadcast({"type": "refresh_memories", "service": report.service})
    return {"status": "stored", "service": report.service}
