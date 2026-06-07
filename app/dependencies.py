from fastapi import Request, Header, HTTPException, status
from hindsight_client import Hindsight
from groq import AsyncGroq
from app.db import SessionLocal, Project

def get_hindsight(request: Request) -> Hindsight:
    return request.app.state.hindsight

def get_groq(request: Request) -> AsyncGroq:
    return request.app.state.groq

def verify_api_key(x_api_key: str = Header(None)):
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing x-api-key header",
        )
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.api_key == x_api_key).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API Key",
            )
        return project
    finally:
        db.close()
