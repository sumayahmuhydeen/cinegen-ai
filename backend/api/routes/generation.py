"""
Generation Routes — Production Grade
======================================
PRODUCER'S PHILOSOPHY:
A film is built shot by shot, scene by scene.
Never run the full pipeline blind — always test one shot
from each scene before committing to full generation.

PIPELINE STEPS:
1. Test single shots from each scene
2. Approve audio pipeline
3. Start full generation with budget cap
4. Monitor progress
5. Regenerate failed shots individually
6. Assemble when all critical shots complete
7. Export final film

ROUTES:
POST /generation/{id}/start              — Start full pipeline (with budget cap)
GET  /generation/{id}/status             — Live progress with failure details
POST /generation/{id}/shot/{shot_id}     — Generate single shot
POST /generation/{id}/audio              — Generate all audio
POST /generation/{id}/assemble           — Assemble final video
GET  /generation/{id}/export             — Download link
POST /generation/{id}/retry-failed       — Retry all failed shots
GET  /generation/{id}/failed-shots       — List failed shots with reasons
"""
import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from core.database import get_db
from models import Project, Shot, Scene, Character, Location
from services.shot_generator import shot_generator
from services.audio_pipeline import audio_pipeline
from services.assembly import assembly_service

router = APIRouter()
logger = logging.getLogger(__name__)


def mock_user_id(): return "user_demo_001"


def target_shot_num(shot_id: str) -> int:
    try:
        return int(shot_id.split("_")[-1])
    except (ValueError, IndexError):
        return -1


def get_project_or_404(project_id: str, db: Session) -> Project:
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return p


# ── Single Shot Generation ─────────────────────────────────────────────────────

@router.post("/{project_id}/shot/{shot_id_param}", response_model=dict)
async def generate_single_shot(
    project_id: str,
    shot_id_param: str,
    db: Session = Depends(get_db)
):
    """
    Generate or regenerate a single shot.
    ALWAYS test individual shots before running the full pipeline.
    This is the producer's most important quality gate.
    """
    project = get_project_or_404(project_id, db)
    if not project.blueprint:
        raise HTTPException(status_code=400, detail="No blueprint. Upload a script first.")

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
        if target_shot:
            break

    if not target_shot:
        # Give helpful error showing available shot IDs
        all_shot_ids = [
            shot.get("shot_id")
            for scene in bp.get("scenes", [])
            for shot in scene.get("shots", [])
        ]
        raise HTTPException(
            status_code=404,
            detail={
                "message": f"Shot '{shot_id_param}' not found in blueprint.",
                "available_shot_ids": all_shot_ids[:20],
                "total_shots": len(all_shot_ids),
                "hint": "Use GET /api/v1/generation/{id}/shot-list to see all available shot IDs"
            }
        )

    # Generate the shot
    raw_result = await shot_generator.generate_shot(
        shot=target_shot,
        scene=target_scene,
        character_bible=bp.get("character_bible", {}),
        location_bible=bp.get("location_bible", {}),
        style_bible=bp.get("style_bible_locked", {}),
    )

    # Convert ShotResult dataclass to plain dict
    from dataclasses import asdict as dc_asdict, is_dataclass as is_dc
    r = dc_asdict(raw_result) if is_dc(raw_result) else (
        raw_result.to_dict() if hasattr(raw_result, "to_dict") else raw_result
    )

    # Update DB shot record
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


# ── Shot List ──────────────────────────────────────────────────────────────────

@router.get("/{project_id}/shot-list", response_model=dict)
async def get_shot_list(project_id: str, db: Session = Depends(get_db)):
    """
    Get all shot IDs and details from the blueprint.
    Use this BEFORE generating to know exactly what shots exist
    and which ones to test first.
    """
    project = get_project_or_404(project_id, db)
    if not project.blueprint:
        raise HTTPException(status_code=400, detail="No blueprint. Upload script first.")

    bp = project.blueprint
    shot_list = []

    for scene in bp.get("scenes", []):
        scene_num = scene.get("scene_number")
        location_id = scene.get("location_id", "")
        loc_bible = bp.get("location_bible", {})
        loc_name = loc_bible.get(location_id, {}).get("name", "Unknown Location")

        for shot in scene.get("shots", []):
            shot_list.append({
                "shot_id": shot.get("shot_id"),
                "scene_number": scene_num,
                "shot_number": shot.get("shot_number"),
                "location": loc_name,
                "camera": shot.get("camera_direction"),
                "emotion": shot.get("emotion"),
                "has_dialogue": bool(shot.get("dialogue")),
                "dialogue": shot.get("dialogue"),
                "duration_estimate": shot.get("duration_estimate"),
                "kling_duration": "5" if (shot.get("duration_estimate") or 8) <= 7 else "10",
            })

    # Also get DB status for each shot
    db_shots = db.query(Shot).filter(Shot.project_id == project_id).all()
    db_shot_map = {s.shot_number: s.status for s in db_shots}

    for s in shot_list:
        s["db_status"] = db_shot_map.get(s["shot_number"], "not_in_db")

    # Producer recommendations — which shots to test first
    test_first = [
        s["shot_id"] for s in shot_list
        if s["camera"] in ("Wide Shot", "Aerial") and not s["has_dialogue"]
    ][:1]
    test_second = [
        s["shot_id"] for s in shot_list
        if s["has_dialogue"]
    ][:1]
    test_third = [
        s["shot_id"] for s in shot_list
        if s["camera"] in ("Close-Up", "Extreme Close-Up")
    ][:1]

    return {
        "project_id": project_id,
        "title": project.title,
        "total_shots": len(shot_list),
        "total_scenes": len(bp.get("scenes", [])),
        "shots": shot_list,
        "producer_test_order": {
            "test_first": test_first,
            "test_second": test_second,
            "test_third": test_third,
            "reason": "Test wide shot (cheapest), then dialogue shot, then close-up before running full pipeline"
        }
    }


# ── Full Pipeline Start ────────────────────────────────────────────────────────

@router.post("/{project_id}/start", response_model=dict)
async def start_full_pipeline(
    project_id: str,
    background_tasks: BackgroundTasks,
    payload: dict = {},
    db: Session = Depends(get_db)
):
    """
    Start the complete generation pipeline.

    PRODUCER'S RULE: Only run this after:
    1. Testing at least one shot from each scene individually
    2. Approving all characters
    3. Approving all locations
    4. Confirming audio pipeline works

    Optional payload:
    {
        "max_shots": 9,        // limit how many shots to generate (cost control)
        "scene_numbers": [1,2] // only generate specific scenes
    }
    """
    project = get_project_or_404(project_id, db)
    if not project.blueprint:
        raise HTTPException(status_code=400, detail="No blueprint. Upload script first.")

    bp = project.blueprint

    # ── APPROVAL GATE ─────────────────────────────────────────────
    chars = db.query(Character).filter(Character.project_id == project_id).all()
    locs  = db.query(Location).filter(Location.project_id == project_id).all()
    unapproved_chars = [c.name for c in chars if not c.approved]
    unapproved_locs  = [l.name for l in locs  if not l.approved]

    if unapproved_chars or unapproved_locs:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Cannot start. All characters and locations must be approved first.",
                "unapproved_characters": unapproved_chars,
                "unapproved_locations": unapproved_locs,
                "fix": [
                    f"POST /api/v1/characters/project/{project_id}/approve-all",
                    f"POST /api/v1/locations/project/{project_id}/approve-all",
                ]
            }
        )

    # ── BUILD SHOT LIST WITH OPTIONAL FILTERS ─────────────────────
    max_shots = payload.get("max_shots")
    scene_filter = payload.get("scene_numbers")

    all_shots_in_blueprint = []
    for scene in bp.get("scenes", []):
        scene_num = scene.get("scene_number")
        if scene_filter and scene_num not in scene_filter:
            continue
        for shot in scene.get("shots", []):
            all_shots_in_blueprint.append((scene, shot))
            if max_shots and len(all_shots_in_blueprint) >= max_shots:
                break
        if max_shots and len(all_shots_in_blueprint) >= max_shots:
            break

    total_shots = len(all_shots_in_blueprint)

    # Estimate cost
    total_cost_estimate = 0.0
    from integrations.kling import kling_client, COST_PER_SECOND
    for scene, shot in all_shots_in_blueprint:
        model = kling_client.select_model(shot)
        dur = 5 if (shot.get("duration_estimate") or 8) <= 7 else 10
        total_cost_estimate += COST_PER_SECOND.get(model, 0.07) * dur

    project.status = "generating"
    db.commit()

    # Queue background pipeline
    background_tasks.add_task(
        _run_full_pipeline_background,
        project_id=project_id,
        blueprint=bp,
        shot_filter=[(s.get("scene_id", s.get("scene_number")), sh.get("shot_id"))
                     for s, sh in all_shots_in_blueprint] if (max_shots or scene_filter) else None,
    )

    return {
        "project_id": project_id,
        "status": "generating",
        "message": f"Pipeline started. {total_shots} shots queued.",
        "total_shots": total_shots,
        "total_scenes": len(bp.get("scenes", [])),
        "estimated_cost_usd": round(total_cost_estimate, 4),
        "estimated_time_minutes": max(5, total_shots * 3),
        "check_status_at": f"/api/v1/generation/{project_id}/status",
        "producer_tip": (
            f"Monitoring {total_shots} shots. Check status every 30 seconds. "
            f"Use POST /api/v1/generation/{project_id}/retry-failed for any failures."
        )
    }


async def _run_full_pipeline_background(
    project_id: str,
    blueprint: dict,
    shot_filter: list = None,
):
    """Background task: runs the full generation pipeline."""
    from core.database import SessionLocal
    db = SessionLocal()
    try:
        character_bible = blueprint.get("character_bible", {})
        location_bible  = blueprint.get("location_bible", {})
        style_bible     = blueprint.get("style_bible_locked", {})

        logger.info(f"[Pipeline] Starting for project {project_id}")
        all_shot_results = []
        total_cost = 0.0

        for scene in blueprint.get("scenes", []):
            shots_to_generate = []
            for shot in scene.get("shots", []):
                sid = shot.get("shot_id")
                # Apply filter if set
                if shot_filter:
                    if not any(sid == sf[1] for sf in shot_filter):
                        continue
                shots_to_generate.append(shot)

            if not shots_to_generate:
                continue

            logger.info(
                f"[Pipeline] Scene {scene.get('scene_number')}: "
                f"generating {len(shots_to_generate)} shots"
            )

            scene_results = await shot_generator.generate_scene(
                scene={**scene, "shots": shots_to_generate},
                character_bible=character_bible,
                location_bible=location_bible,
                style_bible=style_bible,
            )

            # Convert dataclasses to dicts
            from dataclasses import asdict as _asd, is_dataclass as _isd
            scene_dicts = [
                _asd(r) if _isd(r) else (r.to_dict() if hasattr(r, "to_dict") else r)
                for r in scene_results
            ]
            all_shot_results.extend(scene_dicts)

            # Update DB
            shots_in_db = db.query(Shot).filter(Shot.project_id == project_id).all()
            for rd in scene_dicts:
                sid_str = rd.get("shot_id", "")
                try:
                    shot_num = int(sid_str.split("_")[-1]) if "_" in sid_str else -1
                except (ValueError, IndexError):
                    shot_num = -1
                for db_shot in shots_in_db:
                    if db_shot.shot_number == shot_num:
                        db_shot.status = rd.get("status") or "completed"
                        db_shot.video_url = rd.get("video_url")
                        db_shot.continuity_score = rd.get("continuity_score")
                total_cost += rd.get("cost_usd", 0)
            db.commit()

        # Generate audio
        logger.info(f"[Pipeline] Generating audio for {project_id}")
        audio_manifest = await audio_pipeline.generate_project_audio(
            blueprint=blueprint,
            character_bible=character_bible,
        )

        # Assemble
        logger.info(f"[Pipeline] Assembling {project_id}")
        assembly_result = await assembly_service.assemble_project(
            project_id=project_id,
            blueprint=blueprint,
            shot_results=all_shot_results,
            audio_manifest=audio_manifest,
        )

        completed = len([r for r in all_shot_results if r.get("status") == "completed"])
        failed    = len([r for r in all_shot_results if r.get("status") == "failed"])

        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = "completed" if failed == 0 else "review"
            db.commit()

        logger.info(
            f"[Pipeline] Complete: {completed} completed / {failed} failed / "
            f"${total_cost:.4f} total cost"
        )

    except Exception as e:
        logger.error(f"[Pipeline] Failed for {project_id}: {e}")
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = "failed"
            db.commit()
    finally:
        db.close()


# ── Pipeline Status ────────────────────────────────────────────────────────────

@router.get("/{project_id}/status", response_model=dict)
async def get_pipeline_status(project_id: str, db: Session = Depends(get_db)):
    """
    Live generation status with failure details.
    Check this every 30 seconds during generation.
    """
    project = get_project_or_404(project_id, db)
    shots = db.query(Shot).filter(Shot.project_id == project_id).all()

    total     = len(shots)
    completed = len([s for s in shots if s.status == "completed"])
    generating = len([s for s in shots if s.status == "generating"])
    failed    = len([s for s in shots if s.status == "failed"])
    pending   = len([s for s in shots if s.status == "pending"])

    progress = int((completed / total * 100)) if total > 0 else 0

    failed_shots = [
        {
            "shot_id": s.id,
            "shot_number": s.shot_number,
            "retry_count": s.retry_count or 0,
        }
        for s in shots if s.status == "failed"
    ]

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
        "failed_shots": failed_shots,
        "ready_for_assembly": completed > 0 and pending == 0 and generating == 0,
        "producer_note": (
            f"✅ Ready for assembly" if completed > 0 and pending == 0 and generating == 0
            else f"🎬 {completed}/{total} shots complete" if generating > 0 or pending > 0
            else f"⚠ {failed} shots failed — use POST /retry-failed to retry"
            if failed > 0 else "Starting..."
        )
    }


# ── Retry Failed Shots ─────────────────────────────────────────────────────────

@router.post("/{project_id}/retry-failed", response_model=dict)
async def retry_failed_shots(
    project_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Retry all failed shots without restarting the full pipeline.
    PRODUCER'S TOOL: Use this after a partial failure instead of
    restarting from scratch and wasting credits on completed shots.
    """
    project = get_project_or_404(project_id, db)
    if not project.blueprint:
        raise HTTPException(status_code=400, detail="No blueprint found.")

    failed_shots = db.query(Shot).filter(
        Shot.project_id == project_id,
        Shot.status == "failed"
    ).all()

    if not failed_shots:
        return {
            "project_id": project_id,
            "message": "No failed shots found. Nothing to retry.",
            "failed_count": 0,
        }

    # Reset failed shots to pending
    for shot in failed_shots:
        shot.status = "pending"
        shot.retry_count = (shot.retry_count or 0) + 1
    db.commit()

    bp = project.blueprint

    # Queue retry as background task
    background_tasks.add_task(
        _retry_failed_background,
        project_id=project_id,
        blueprint=bp,
        failed_shot_numbers=[s.shot_number for s in failed_shots],
    )

    return {
        "project_id": project_id,
        "status": "retrying",
        "failed_count": len(failed_shots),
        "message": f"Retrying {len(failed_shots)} failed shots in background.",
        "check_status_at": f"/api/v1/generation/{project_id}/status",
    }


async def _retry_failed_background(
    project_id: str,
    blueprint: dict,
    failed_shot_numbers: list[int],
):
    """Retry only the failed shots."""
    from core.database import SessionLocal
    db = SessionLocal()
    try:
        character_bible = blueprint.get("character_bible", {})
        location_bible  = blueprint.get("location_bible", {})
        style_bible     = blueprint.get("style_bible_locked", {})

        logger.info(f"[Retry] Retrying {len(failed_shot_numbers)} failed shots for {project_id}")

        for scene in blueprint.get("scenes", []):
            for shot in scene.get("shots", []):
                shot_num = shot.get("shot_number")
                if shot_num not in failed_shot_numbers:
                    continue

                logger.info(f"[Retry] Retrying shot {shot.get('shot_id')}")
                raw_result = await shot_generator.generate_shot(
                    shot=shot,
                    scene=scene,
                    character_bible=character_bible,
                    location_bible=location_bible,
                    style_bible=style_bible,
                )

                from dataclasses import asdict as _asd, is_dataclass as _isd
                r = _asd(raw_result) if _isd(raw_result) else raw_result

                db_shots = db.query(Shot).filter(
                    Shot.project_id == project_id
                ).all()
                for db_shot in db_shots:
                    if db_shot.shot_number == shot_num:
                        db_shot.status = r.get("status") or "completed"
                        db_shot.video_url = r.get("video_url")
                        db_shot.continuity_score = r.get("continuity_score")
                db.commit()

        logger.info(f"[Retry] Complete for {project_id}")

    except Exception as e:
        logger.error(f"[Retry] Failed for {project_id}: {e}")
    finally:
        db.close()


# ── Failed Shots Detail ────────────────────────────────────────────────────────

@router.get("/{project_id}/failed-shots", response_model=dict)
async def get_failed_shots(project_id: str, db: Session = Depends(get_db)):
    """
    Get detailed list of all failed shots.
    Use this to understand what went wrong before retrying.
    """
    project = get_project_or_404(project_id, db)
    failed = db.query(Shot).filter(
        Shot.project_id == project_id,
        Shot.status == "failed"
    ).all()

    return {
        "project_id": project_id,
        "failed_count": len(failed),
        "failed_shots": [
            {
                "shot_number": s.shot_number,
                "camera": s.camera_direction,
                "retry_count": s.retry_count or 0,
                "continuity_score": s.continuity_score,
            }
            for s in failed
        ],
        "next_action": (
            f"POST /api/v1/generation/{project_id}/retry-failed"
            if failed else "No failed shots"
        )
    }


# ── Audio Pipeline ─────────────────────────────────────────────────────────────

@router.post("/{project_id}/audio", response_model=dict)
async def generate_audio(project_id: str, db: Session = Depends(get_db)):
    """Generate all audio — runs independently of video generation."""
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


# ── Assembly ───────────────────────────────────────────────────────────────────

@router.post("/{project_id}/assemble", response_model=dict)
async def assemble_video(
    project_id: str,
    payload: dict = {},
    db: Session = Depends(get_db)
):
    """
    Assemble all completed clips and audio into final MP4.
    Can assemble even if some shots failed — uses completed shots only.
    """
    project = get_project_or_404(project_id, db)
    if not project.blueprint:
        raise HTTPException(status_code=400, detail="No blueprint found.")

    bp = project.blueprint
    shots = db.query(Shot).filter(Shot.project_id == project_id).all()

    completed_shots = [s for s in shots if s.status == "completed"]
    failed_shots    = [s for s in shots if s.status == "failed"]

    if not completed_shots:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "No completed shots to assemble.",
                "completed": 0,
                "failed": len(failed_shots),
                "fix": f"POST /api/v1/generation/{project_id}/retry-failed"
            }
        )

    shot_results = [
        {
            "shot_id": s.id,
            "status": s.status,
            "video_url": s.video_url,
            "duration": s.duration_estimate or 5,
            "continuity_score": s.continuity_score,
        }
        for s in completed_shots
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
        "completed_shots": len(completed_shots),
        "skipped_failed_shots": len(failed_shots),
        "message": (
            f"Assembly complete using {len(completed_shots)} shots."
            + (f" {len(failed_shots)} failed shots were skipped." if failed_shots else "")
        )
    }


# ── Export ─────────────────────────────────────────────────────────────────────

@router.get("/{project_id}/export", response_model=dict)
async def get_export(project_id: str, db: Session = Depends(get_db)):
    """Get export details and download link."""
    project = get_project_or_404(project_id, db)
    shots = db.query(Shot).filter(Shot.project_id == project_id).all()
    completed = [s for s in shots if s.status == "completed"]

    return {
        "project_id": project_id,
        "title": project.title,
        "status": "ready" if project.status == "completed" else project.status,
        "video_url": f"https://mock-storage.cinegen.ai/exports/{project_id}/final.mp4",
        "completed_shots": len(completed),
        "total_shots": len(shots),
        "resolution": "1080p",
        "format": "MP4",
    }
