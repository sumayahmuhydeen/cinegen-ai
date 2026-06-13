"""
Characters Routes
=================
GET    /characters/{project_id}         — List characters
PUT    /characters/{character_id}/approve — Approve character
GET    /characters/{project_id}/bible   — Get Character Bible
POST   /characters/{project_id}/generate-prompt — Generate image prompt
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from models import Character, Project
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

def mock_user_id(): return "user_demo_001"

@router.get("/project/{project_id}", response_model=list[dict])
async def list_characters(project_id: str, db: Session = Depends(get_db)):
    characters = db.query(Character).filter(Character.project_id == project_id).all()
    return [
        {
            "id": c.id, "name": c.name, "role": c.role,
            "description": c.description, "appearance": c.appearance,
            "age_range": c.age_range, "approved": c.approved,
            "reference_image_url": c.reference_image_url,
            "prompt_description": c.prompt_description,
            "voice_id": c.voice_id
        }
        for c in characters
    ]

@router.put("/{character_id}/approve", response_model=dict)
async def approve_character(
    character_id: str,
    payload: dict,
    db: Session = Depends(get_db)
):
    """Approve or reject a character's reference image."""
    char = db.query(Character).filter(Character.id == character_id).first()
    if not char:
        raise HTTPException(status_code=404, detail="Character not found")

    char.approved = payload.get("approved", True)
    if payload.get("reference_image_url"):
        char.reference_image_url = payload["reference_image_url"]

    db.commit()
    logger.info(f"Character {char.name} {'approved' if char.approved else 'rejected'}")
    return {
        "id": char.id, "name": char.name,
        "approved": char.approved,
        "message": f"Character {'approved' if char.approved else 'rejected'} successfully"
    }

@router.get("/project/{project_id}/bible", response_model=dict)
async def get_character_bible(project_id: str, db: Session = Depends(get_db)):
    """Get the full Character Bible for a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project or not project.blueprint:
        raise HTTPException(status_code=404, detail="Project or blueprint not found")

    char_bible = project.blueprint.get("character_bible", {})
    db_chars = db.query(Character).filter(Character.project_id == project_id).all()
    approved_ids = {c.id for c in db_chars if c.approved}

    return {
        "project_id": project_id,
        "character_bible": char_bible,
        "total_characters": len(char_bible),
        "approved_count": len([c for c in char_bible.values() if c.get("approved")]),
        "all_approved": all(c.get("approved") for c in char_bible.values())
    }
