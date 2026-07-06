"""
Generation Routes — Phase 3
=============================
POST /generation/{project_id}/start         — Start full pipeline
GET  /generation/{project_id}/status        — Live pipeline status
POST /generation/{project_id}/shot/{shot_id} — Generate single shot
POST /generation/{project_id}/audio         — Generate all audio
POST /generation/{project_id}/assemble      — Assemble final video
GET  /generation/{project_id}/export        — Download export
"""
import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from core.database import get_db
from models import Project, Shot, Scene
from services.shot_generator import shot_generator
from services.audio_pipeline import audio_pipeline
from services.assembly import assembly_service

router = APIRouter()
logger = logging.getLogger(__name__)

def mock_user_id(): return "user_demo_001"

def target_shot_num(shot_id: str) -> int:
    """Extract shot number from shot_id like shot_001_002 -> 2"""
    try:
        return int(shot_id.split("_")[-1])
    except (ValueError, IndexError):
        return -1

def get_project_or_404(project_id: str, db: Session) -> Project:
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return p

# ── Full Pipeline ─────────────────────────────────────────────────────────────

@router.post("/{project_id}/start", response_model=dict)
async def start_full_pipeline(
    project_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Start the complete generation pipeline:
    1. Generate all shots (video)
    2. Generate all audio (parallel with video)
    3. Assemble final MP4
    """
    project = get_project_or_404(project_id, db)
    if not project.blueprint:
        raise HTTPException(status_code=400, detail="No blueprint. Upload a script first.")

    bp = project.blueprint
    approval = bp.get("character_bible", {})
    # In production: check all characters approved. Skip check for demo.

    project.status = "generating"
    db.commit()

    # Queue the full pipeline as a background task
    background_tasks.add_task(
        _run_full_pipeline_background,
        project_id=project_id,
        blueprint=bp,
    )

    total_shots = bp.get("total_shots", 0)
    return {
        "project_id": project_id,
        "status": "generating",
        "message": f"Pipeline started. {total_shots} shots queued.",
        "total_shots": total_shots,
        "total_scenes": bp.get("total_scenes", 0),
        "estimated_time_minutes": max(5, total_shots * 2),
        "check_status_at": f"/api/v1/generation/{project_id}/status",
    }

async def _run_full_pipeline_background(project_id: str, blueprint: dict):
    """Background task: runs the full generation pipeline."""
    from core.database import SessionLocal
    db = SessionLocal()
    try:
        character_bible = blueprint.get("character_bible", {})
        location_bible = blueprint.get("location_bible", {})
        style_bible = blueprint.get("style_bible_locked", {})

        logger.info(f"[Pipeline] Starting for project {project_id}")
        all_shot_results = []

        # Generate shots scene by scene
        for scene in blueprint.get("scenes", []):
            logger.info(f"[Pipeline] Generating scene {scene.get('scene_number')}")
            scene_results = await shot_generator.generate_scene(
                scene=scene,
                character_bible=character_bible,
                location_bible=location_bible,
                style_bible=style_bible,
            )
            # Convert ShotResult dataclasses to dicts
            from dataclasses import asdict as _asd, is_dataclass as _isd
            scene_dicts = [_asd(r) if _isd(r) else (r.to_dict() if hasattr(r,"to_dict") else r) for r in scene_results]
            all_shot_results.extend(scene_dicts)

            # Update shot statuses in DB
            shots = db.query(Shot).filter(Shot.project_id == project_id).all()
            for rd in scene_dicts:
                sid_str = rd.get("shot_id", "")
                try:
                    shot_num = int(sid_str.split("_")[-1]) if "_" in sid_str else -1
                except (ValueError, IndexError):
                    shot_num = -1
                for shot in shots:
                    if shot.shot_number == shot_num:
                        shot.status = rd.get("status") or "completed"
                        shot.video_url = rd.get("video_url")
                        shot.continuity_score = rd.get("continuity_score")
            db.commit()

        # Generate all audio in parallel
        logger.info(f"[Pipeline] Generating audio for project {project_id}")
        audio_manifest = await audio_pipeline.generate_project_audio(
            blueprint=blueprint,
            character_bible=character_bible,
        )

        # Assemble final video
        logger.info(f"[Pipeline] Assembling final video for project {project_id}")
        assembly_result = await assembly_service.assemble_project(
            project_id=project_id,
            blueprint=blueprint,
            shot_results=all_shot_results,
            audio_manifest=audio_manifest,
        )

        # Update project status
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = "completed"
            db.commit()

        logger.info(f"[Pipeline] Complete for project {project_id}: {assembly_result.get('status')}")

    except Exception as e:
        logger.error(f"[Pipeline] Failed for project {project_id}: {e}")
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = "failed"
            db.commit()
    finally:
        db.close()

# ── Single Shot Generation ────────────────────────────────────────────────────

@router.post("/{project_id}/shot/{shot_id_param}", response_model=dict)
async def generate_single_shot(
    project_id: str,
    shot_id_param: str,
    db: Session = Depends(get_db)
):
    """Generate or regenerate a single shot without restarting the full pipeline."""
    project = get_project_or_404(project_id, db)
    if not project.blueprint:
        raise HTTPException(status_code=400, detail="No blueprint found.")

    bp = project.blueprint

    # Find the shot in the blueprint
    target_shot = None
    target_scene = None
    for scene in bp.get("scenes", []):
        for shot in scene.get("shots", []):
            if shot.get("shot_id") == shot_id_param:
                target_shot = shot
                target_scene = scene
                break

    if not target_shot:
        raise HTTPException(status_code=404, detail=f"Shot {shot_id_param} not found in blueprint.")

    # Generate the shot
    shot_result = await shot_generator.generate_shot(
        shot=target_shot,
        scene=target_scene,
        character_bible=bp.get("character_bible", {}),
        location_bible=bp.get("location_bible", {}),
        style_bible=bp.get("style_bible_locked", {}),
    )

    # Convert ShotResult dataclass to plain dict safely
    from dataclasses import asdict as dc_asdict, is_dataclass as is_dc
    if is_dc(shot_result):
        r = dc_asdict(shot_result)
    elif hasattr(shot_result, "to_dict"):
        r = shot_result.to_dict()
    elif isinstance(shot_result, dict):
        r = shot_result
    else:
        r = {"status": "completed", "shot_id": shot_id_param}

    # Update DB
    db_shots = db.query(Shot).filter(Shot.project_id == project_id).all()
    for db_shot in db_shots:
        if db_shot.shot_number == target_shot.get("shot_number"):
            db_shot.status = r.get("status") or "completed"
            db_shot.video_url = r.get("video_url")
            db_shot.generation_prompt = (r.get("generation_prompt") or "")[:500]
            db_shot.continuity_score = r.get("continuity_score")
            db_shot.retry_count = (db_shot.retry_count or 0) + 1
    db.commit()

    return {
        "shot_id": shot_id_param,
        "project_id": project_id,
        **r,
        "message": f"Shot {shot_id_param} generated successfully"
    }

# ── Audio Pipeline ────────────────────────────────────────────────────────────

@router.post("/{project_id}/audio", response_model=dict)
async def generate_audio(project_id: str, db: Session = Depends(get_db)):
    """Generate all audio for a project — runs independently of video generation."""
    project = get_project_or_404(project_id, db)
    if not project.blueprint:
        raise HTTPException(status_code=400, detail="No blueprint found.")

    bp = project.blueprint
    manifest = await audio_pipeline.generate_project_audio(
        blueprint=bp,
        character_bible=bp.get("character_bible", {}),
    )
    return {
        "project_id": project_id,
        "status": "audio_complete",
        **manifest,
        "message": "Audio generation complete"
    }

# ── Assembly ──────────────────────────────────────────────────────────────────

@router.post("/{project_id}/assemble", response_model=dict)
async def assemble_video(
    project_id: str,
    payload: dict = {},
    db: Session = Depends(get_db)
):
    """Assemble all generated clips and audio into a final MP4."""
    project = get_project_or_404(project_id, db)
    if not project.blueprint:
        raise HTTPException(status_code=400, detail="No blueprint found.")

    bp = project.blueprint
    shots = db.query(Shot).filter(Shot.project_id == project_id).all()

    shot_results = [
        {
            "shot_id": s.id,
            "status": s.status,
            "video_url": s.video_url,
            "duration": s.duration_estimate or 8,
            "continuity_score": s.continuity_score,
        }
        for s in shots
    ]

    result = await assembly_service.assemble_project(
        project_id=project_id,
        blueprint=bp,
        shot_results=shot_results,
        audio_manifest={"dialogue": [], "music": []},
        output_resolution=payload.get("resolution", "1080p"),
        include_subtitles=payload.get("subtitles", True),
    )

    project.status = "completed"
    db.commit()

    return {
        "project_id": project_id,
        **result,
        "message": "Assembly complete. Your film is ready."
    }

# ── Pipeline Status ───────────────────────────────────────────────────────────

@router.get("/{project_id}/status", response_model=dict)
async def get_pipeline_status(project_id: str, db: Session = Depends(get_db)):
    """Get live generation status for a project."""
    project = get_project_or_404(project_id, db)
    shots = db.query(Shot).filter(Shot.project_id == project_id).all()

    total = len(shots)
    completed = len([s for s in shots if s.status == "completed"])
    generating = len([s for s in shots if s.status == "generating"])
    failed = len([s for s in shots if s.status == "failed"])
    pending = len([s for s in shots if s.status == "pending"])

    progress = int((completed / total * 100)) if total > 0 else 0

    return {
        "project_id": project_id,
        "project_status": project.status,
        "progress_percent": progress,
        "shots": {
            "total": total,
            "completed": completed,
            "generating": generating,
            "failed": failed,
            "pending": pending,
        },
        "ready_for_assembly": completed == total and total > 0,
    }

# ── Export ────────────────────────────────────────────────────────────────────

@router.get("/{project_id}/export", response_model=dict)
async def get_export(project_id: str, db: Session = Depends(get_db)):
    """Get export details for a completed project."""
    project = get_project_or_404(project_id, db)
    if project.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Project not ready for export. Status: {project.status}"
        )
    return {
        "project_id": project_id,
        "title": project.title,
        "status": "ready",
        "video_url": f"https://mock-storage.cinegen.ai/exports/{project_id}/final.mp4",
        "duration_seconds": project.duration_estimate,
        "resolution": "1080p",
        "format": "MP4",
        "message": "Export ready for download"
    }
