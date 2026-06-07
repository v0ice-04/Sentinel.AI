from fastapi import APIRouter, Depends, Body
from hindsight_client import Hindsight
from google import genai
import structlog

from app.config import Settings, get_settings
from app.dependencies import get_hindsight, get_gemini
from app.models import DeployEvent, IncidentReport, RiskAnalysis
from app.agent_core import analyze_deploy, report_incident

logger = structlog.get_logger()
router = APIRouter(prefix="/deploy", tags=["deploy"])

@router.post("/analyze", response_model=RiskAnalysis)
async def analyze(
    event: DeployEvent = Body(...),
    hindsight: Hindsight = Depends(get_hindsight),
    gemini: genai.Client = Depends(get_gemini),
    settings: Settings = Depends(get_settings)
):
    result = await analyze_deploy(event, hindsight, gemini, settings)
    logger.info(
        "Deployment analyzed",
        service=event.service,
        risk_level=result.risk_level,
        risk_score=result.risk_score,
        memories_used=result.memories_used
    )
    return result

@router.post("/incident")
async def incident(
    report: IncidentReport = Body(...),
    hindsight: Hindsight = Depends(get_hindsight),
    settings: Settings = Depends(get_settings)
):
    await report_incident(report, hindsight, settings)
    logger.info(
        "Incident reported",
        service=report.service,
        severity=report.severity
    )
    return {"status": "stored", "service": report.service}
