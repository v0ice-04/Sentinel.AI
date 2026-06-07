import os
import certifi
import aiohttp
import asyncio

os.environ["SSL_CERT_FILE"] = certifi.where()

# Monkey-patch missing aiohttp attributes for compatibility with aiohttp 3.9.x
if not hasattr(aiohttp, "ClientConnectorDNSError"):
    aiohttp.ClientConnectorDNSError = aiohttp.ClientConnectorError  # type: ignore
if not hasattr(aiohttp, "ClientProxyConnectionError"):
    aiohttp.ClientProxyConnectionError = aiohttp.ClientConnectorError  # type: ignore

import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from hindsight_client import Hindsight
from groq import AsyncGroq
import structlog

# Configure structlog to output JSON format
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)
logger = structlog.get_logger()

from app.config import get_settings
from app.routers import deploy, memory

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    
    # Initialize Hindsight client
    app.state.hindsight = Hindsight(
        base_url=settings.hindsight_base_url,
        api_key=settings.hindsight_api_key or None,
    )
    
    # Initialize Groq client
    app.state.groq = AsyncGroq(api_key=settings.groq_api_key)
    
    # Create memory bank if not exists — run sync call in thread to avoid event loop conflict
    def _create_bank():
        app.state.hindsight.create_bank(
            bank_id=settings.bank_id,
            name="DevOps Risk Agent",
            mission=(
                "I am a DevOps risk analyst specializing in deployment "
                "incident tracking. I remember past failures, root causes, "
                "and patterns that predict deployment risk. I prioritize "
                "preventing repeat incidents."
            ),
        )

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _create_bank)
        logger.info("Memory bank created", bank_id=settings.bank_id)
    except Exception as e:
        logger.info("Memory bank already exists or creation skipped", bank_id=settings.bank_id, error=str(e))
        
    logger.info("DevOps Agent started")
    yield
    
    # Shutdown logic
    app.state.hindsight.close()
    logger.info("DevOps Agent shutdown")

app = FastAPI(
    title="DevOps Pipeline Risk Agent",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start_time) * 1000
    logger.info(
        "request_processed",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=round(duration_ms, 2)
    )
    return response

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": str(exc), "path": request.url.path}
    )

# Include routers
app.include_router(deploy.router, prefix="/api/v1")
app.include_router(memory.router, prefix="/api/v1")
