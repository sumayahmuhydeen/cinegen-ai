"""
Projects Routes
===============
POST   /projects              — Create project
GET    /projects              — List user projects
GET    /projects/{id}         — Get project details
PUT    /projects/{id}         — Update project
DELETE /projects/{id}         — Delete project
POST   /projects/{id}/script  — Upload + analyse script
GET    /projects/{id}/blueprint — Get production blueprint
GET    /projects/{id}/bibles  — Get all bibles
POST   /projects/{id}/generate — Trigger full generation pipeline
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any
import logging

from core.database import get_db
from models import Project, Character, Scene, Location, Shot
from schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, ScriptUpload, BlueprintResponse
from services.script_intelligence import script_intelligence_service
from services.bible_system import bible_system
from services.continuity_engine import continuity_engine

router = APIRouter()
logger = logging.getLogger(__name__)

# ── Helpers ──────────────────────────────────────────────────────────────────

def get_project_or_404(project_id: str, user_id: str, db: Session) -> Project:
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == user_id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

def mock_user_id() -> str:
    """Returns a mock user ID — replaced by real JWT auth in Phase 3."""
    return "user_demo_001"

# ── Routes ───────────────────────────────────────────────────────────────────

@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    """Create a new project."""
    user_id = mock_user_id()
    project = Project(
        user_id=user_id,
        title=payload.title,
        style=payload.style,
        status="draft"
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    logger.info(f"Project created: {project.id} — '{project.title}'")
    return {
        "id": project.id,
        "title": project.title,
        "status": project.status,
        "style": project.style,
        "user_id": project.user_id,
        "created_at": project.created_at.isoformat(),
        "message": "Project created successfully"
    }

@router.get("/", response_model=list[dict])
async def list_projects(db: Session = Depends(get_db)):
    """List all projects for the current user."""
    user_id = mock_user_id()
    projects = db.query(Project).filter(Project.user_id == user_id).order_by(Project.updated_at.desc()).all()
    return [
        {
            "id": p.id,
            "title": p.title,
            "status": p.status,
            "style": p.style,
            "scene_count": p.scene_count or 0,
            "character_count": p.character_count or 0,
            "duration_estimate": p.duration_estimate,
            "created_at": p.created_at.isoformat(),
            "updated_at": p.updated_at.isoformat(),
        }
        for p in projects
    ]

@router.get("/{project_id}", response_model=dict)
async def get_project(project_id: str, db: Session = Depends(get_db)):
    """Get full project details."""
    project = get_project_or_404(project_id, mock_user_id(), db)
    characters = db.query(Character).filter(Character.project_id == project_id).all()
    scenes = db.query(Scene).filter(Scene.project_id == project_id).order_by(Scene.scene_number).all()
    return {
        "id": project.id,
        "title": project.title,
        "status": project.status,
        "style": project.style,
        "scene_count": project.scene_count or 0,
        "character_count": project.character_count or 0,
        "duration_estimate": project.duration_estimate,
        "blueprint": project.blueprint,
        "characters": [{"id": c.id, "name": c.name, "role": c.role, "approved": c.approved} for c in characters],
        "scenes": [{"id": s.id, "scene_number": s.scene_number, "title": s.title, "emotion": s.emotion} for s in scenes],
        "created_at": project.created_at.isoformat(),
        "updated_at": project.updated_at.isoformat(),
    }

@router.put("/{project_id}", response_model=dict)
async def update_project(project_id: str, payload: ProjectUpdate, db: Session = Depends(get_db)):
    """Update project details."""
    project = get_project_or_404(project_id, mock_user_id(), db)
    if payload.title: project.title = payload.title
    if payload.status: project.status = payload.status
    if payload.style: project.style = payload.style
    db.commit()
    return {"id": project.id, "title": project.title, "status": project.status, "message": "Updated"}

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: str, db: Session = Depends(get_db)):
    """Delete a project and all its data."""
    project = get_project_or_404(project_id, mock_user_id(), db)
    db.delete(project)
    db.commit()
    logger.info(f"Project deleted: {project_id}")

@router.post("/{project_id}/script", response_model=dict)
async def upload_and_analyse_script(
    project_id: str,
    payload: ScriptUpload,
    db: Session = Depends(get_db)
):
    """
    Upload script text and trigger AI analysis.
    This is the main Phase 2 endpoint — calls Script Intelligence Service.
    """
    project = get_project_or_404(project_id, mock_user_id(), db)

    # Update project with script
    project.script_text = payload.script_text
    project.status = "analyzing"
    db.commit()

    try:
        # Run Script Intelligence analysis
        logger.info(f"Running script analysis for project {project_id}")
        blueprint = await script_intelligence_service.analyse_script(
            payload.script_text,
            title=payload.title or project.title
        )

        # Build bibles from blueprint
        character_bible = bible_system.create_character_bible(blueprint)
        location_bible = bible_system.create_location_bible(blueprint)
        style_bible = bible_system.create_style_bible(blueprint)

        # Attach bibles to blueprint
        blueprint["character_bible"] = character_bible
        blueprint["location_bible"] = location_bible
        blueprint["style_bible_locked"] = style_bible

        # Run continuity pre-check
        continuity_report = continuity_engine.validate_blueprint(
            blueprint, character_bible, location_bible
        )
        blueprint["continuity_pre_check"] = continuity_report

        # Save blueprint to project
        project.blueprint = blueprint
        project.title = blueprint.get("title", project.title)
        project.scene_count = blueprint.get("total_scenes", 0)
        project.character_count = len(blueprint.get("characters", []))
        project.duration_estimate = blueprint.get("total_duration_estimate")
        project.status = "storyboard"

        # Persist characters to DB
        for char_data in blueprint.get("characters", []):
            char = Character(
                project_id=project_id,
                name=char_data["name"],
                role=char_data.get("role"),
                description=char_data.get("personality"),
                appearance=char_data.get("physical_description"),
                age_range=char_data.get("age_range"),
                prompt_description=character_bible.get(char_data["character_id"], {}).get("locked_prompt")
            )
            db.add(char)

        # Persist locations to DB
        for loc_data in blueprint.get("locations", []):
            loc = Location(
                project_id=project_id,
                name=loc_data["name"],
                description=loc_data.get("description"),
                environment_type=loc_data.get("environment_type"),
                time_of_day=loc_data.get("time_of_day"),
                weather=loc_data.get("weather"),
                lighting_notes=loc_data.get("lighting"),
                prompt_description=location_bible.get(loc_data["location_id"], {}).get("locked_prompt")
            )
            db.add(loc)

        # Persist scenes and shots to DB
        for scene_data in blueprint.get("scenes", []):
            scene = Scene(
                project_id=project_id,
                scene_number=scene_data["scene_number"],
                title=scene_data.get("title"),
                location_name=scene_data.get("location_id"),
                emotion=scene_data.get("emotion"),
                summary=scene_data.get("summary"),
                duration_estimate=scene_data.get("duration_estimate"),
            )
            db.add(scene)
            db.flush()

            for shot_data in scene_data.get("shots", []):
                shot = Shot(
                    scene_id=scene.id,
                    project_id=project_id,
                    shot_number=shot_data["shot_number"],
                    camera_direction=shot_data.get("camera_direction"),
                    action_description=shot_data.get("action_description"),
                    dialogue=shot_data.get("dialogue"),
                    emotion=shot_data.get("emotion"),
                    duration_estimate=shot_data.get("duration_estimate"),
                    status="pending"
                )
                db.add(shot)

        db.commit()
        logger.info(f"Script analysis complete for {project_id}: {project.scene_count} scenes")

        return {
            "project_id": project_id,
            "status": "analysis_complete",
            "title": blueprint.get("title"),
            "total_scenes": blueprint.get("total_scenes"),
            "total_shots": blueprint.get("total_shots"),
            "total_characters": len(blueprint.get("characters", [])),
            "total_locations": len(blueprint.get("locations", [])),
            "duration_estimate_seconds": blueprint.get("total_duration_estimate"),
            "continuity_pre_check": continuity_report,
            "message": "Script analysed successfully. Review the blueprint and approve characters and locations before generating."
        }

    except Exception as e:
        project.status = "failed"
        db.commit()
        logger.error(f"Script analysis failed for {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Script analysis failed: {str(e)}")

@router.get("/{project_id}/blueprint", response_model=dict)
async def get_blueprint(project_id: str, db: Session = Depends(get_db)):
    """Get the full production blueprint for a project."""
    project = get_project_or_404(project_id, mock_user_id(), db)
    if not project.blueprint:
        raise HTTPException(status_code=404, detail="No blueprint found. Upload a script first.")
    return {
        "project_id": project_id,
        "title": project.title,
        "blueprint": project.blueprint,
        "status": project.status,
    }

@router.get("/{project_id}/bibles", response_model=dict)
async def get_bibles(project_id: str, db: Session = Depends(get_db)):
    """Get all three bibles for a project."""
    project = get_project_or_404(project_id, mock_user_id(), db)
    if not project.blueprint:
        raise HTTPException(status_code=404, detail="No blueprint found. Upload a script first.")

    bp = project.blueprint
    approval_status = bible_system.check_approval_status(
        bp.get("character_bible", {}),
        bp.get("location_bible", {})
    )

    return {
        "project_id": project_id,
        "character_bible": bp.get("character_bible", {}),
        "location_bible": bp.get("location_bible", {}),
        "style_bible": bp.get("style_bible_locked", {}),
        "approval_status": approval_status,
    }

@router.post("/{project_id}/generate", response_model=dict)
async def trigger_generation(project_id: str, db: Session = Depends(get_db)):
    """
    Trigger the full video generation pipeline.
    Phase 3 will wire this to real AI models.
    Currently returns a mock response showing the pipeline would start.
    """
    project = get_project_or_404(project_id, mock_user_id(), db)
    if not project.blueprint:
        raise HTTPException(status_code=400, detail="No blueprint found. Upload a script first.")

    bp = project.blueprint
    approval = bible_system.check_approval_status(
        bp.get("character_bible", {}),
        bp.get("location_bible", {})
    )

    if not approval["ready_for_generation"]:
        raise HTTPException(
            status_code=400,
            detail=f"Not ready for generation. Unapproved: characters={approval['unapproved_characters']}, locations={approval['unapproved_locations']}"
        )

    project.status = "generating"
    db.commit()

    total_shots = bp.get("total_shots", 0)
    return {
        "project_id": project_id,
        "status": "generating",
        "message": f"Generation pipeline started. {total_shots} shots queued.",
        "total_shots": total_shots,
        "estimated_time_minutes": total_shots * 2,
        "note": "Phase 3 will connect this to real AI video generation models."
    }
