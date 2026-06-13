"""
Shots Routes
============
GET    /shots/project/{project_id}        — List all shots
GET    /shots/{shot_id}                   — Get shot details
GET    /shots/{shot_id}/status            — Live generation status
POST   /shots/{shot_id}/regenerate        — Regenerate single shot
GET    /shots/{shot_id}/prompt            — Get the generation prompt
GET    /shots/project/{project_id}/continuity — Continuity report
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from models import Shot, Scene, Project
from services.continuity_engine import continuity_engine
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/project/{project_id}", response_model=list[dict])
async def list_shots(project_id: str, db: Session = Depends(get_db)):
    shots = db.query(Shot).filter(Shot.project_id == project_id).all()
    return [
        {
            "id": s.id, "scene_id": s.scene_id, "shot_number": s.shot_number,
            "camera_direction": s.camera_direction, "action_description": s.action_description,
            "dialogue": s.dialogue, "emotion": s.emotion,
            "duration_estimate": s.duration_estimate, "status": s.status,
            "video_url": s.video_url, "continuity_score": s.continuity_score,
            "retry_count": s.retry_count
        }
        for s in shots
    ]

@router.get("/{shot_id}", response_model=dict)
async def get_shot(shot_id: str, db: Session = Depends(get_db)):
    shot = db.query(Shot).filter(Shot.id == shot_id).first()
    if not shot:
        raise HTTPException(status_code=404, detail="Shot not found")
    return {
        "id": shot.id, "scene_id": shot.scene_id, "shot_number": shot.shot_number,
        "camera_direction": shot.camera_direction, "action_description": shot.action_description,
        "dialogue": shot.dialogue, "emotion": shot.emotion,
        "duration_estimate": shot.duration_estimate, "status": shot.status,
        "video_url": shot.video_url, "generation_prompt": shot.generation_prompt,
        "continuity_score": shot.continuity_score, "retry_count": shot.retry_count
    }

@router.get("/{shot_id}/status", response_model=dict)
async def get_shot_status(shot_id: str, db: Session = Depends(get_db)):
    """Live generation status for a single shot."""
    shot = db.query(Shot).filter(Shot.id == shot_id).first()
    if not shot:
        raise HTTPException(status_code=404, detail="Shot not found")
    return {
        "shot_id": shot_id, "status": shot.status,
        "video_url": shot.video_url, "continuity_score": shot.continuity_score,
        "retry_count": shot.retry_count
    }

@router.post("/{shot_id}/regenerate", response_model=dict)
async def regenerate_shot(shot_id: str, db: Session = Depends(get_db)):
    """
    Regenerate a single shot without restarting the full pipeline.
    Phase 3 will connect this to real video generation.
    """
    shot = db.query(Shot).filter(Shot.id == shot_id).first()
    if not shot:
        raise HTTPException(status_code=404, detail="Shot not found")

    shot.status = "pending"
    shot.retry_count = (shot.retry_count or 0) + 1
    shot.video_url = None
    db.commit()

    logger.info(f"Shot {shot_id} queued for regeneration (attempt {shot.retry_count})")
    return {
        "shot_id": shot_id, "status": "pending",
        "retry_count": shot.retry_count,
        "message": "Shot queued for regeneration"
    }

@router.get("/project/{project_id}/continuity", response_model=dict)
async def get_continuity_report(project_id: str, db: Session = Depends(get_db)):
    """Get the full continuity report for a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project or not project.blueprint:
        raise HTTPException(status_code=404, detail="Project or blueprint not found")

    bp = project.blueprint
    report = continuity_engine.generate_continuity_report(
        project_id,
        bp,
        bp.get("character_bible", {}),
        bp.get("location_bible", {})
    )
    return report
