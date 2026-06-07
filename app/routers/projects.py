import secrets
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import SessionLocal, Project
from app.models import ProjectCreate, ProjectResponse

router = APIRouter(prefix="/projects", tags=["projects"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=ProjectResponse)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    # Check if project name exists (optional, keeping it simple)
    # Generate API key: 'sentinel_' + 32 random chars
    raw_key = secrets.token_urlsafe(32)
    api_key = f"sentinel_{raw_key}"
    
    db_project = Project(name=project.name, api_key=api_key)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@router.get("/", response_model=list[ProjectResponse])
def get_projects(db: Session = Depends(get_db)):
    return db.query(Project).all()
