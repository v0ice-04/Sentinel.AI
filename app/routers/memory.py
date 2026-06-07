from fastapi import APIRouter, Depends, Query
from datetime import datetime, timezone
from hindsight_client import Hindsight
import structlog

from app.config import Settings, get_settings
from app.dependencies import get_hindsight
from app.models import MemoryItem, HealthResponse
from app.agent_core import get_service_memories

logger = structlog.get_logger()
router = APIRouter(prefix="/memory", tags=["memory"])

@router.get("/memories", response_model=list[MemoryItem])
async def memories(
    service: str = Query(...),
    hindsight: Hindsight = Depends(get_hindsight),
    settings: Settings = Depends(get_settings)
):
    result = await get_service_memories(service, hindsight, settings)
    logger.info("Retrieved service memories", service=service, count=len(result))
    return result

@router.get("/health", response_model=HealthResponse)
async def health(
    settings: Settings = Depends(get_settings)
):
    return HealthResponse(
        status="ok",
        memory_bank=settings.bank_id,
        timestamp=datetime.now(timezone.utc)
    )
