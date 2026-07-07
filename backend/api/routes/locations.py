"""
Locations Routes — Production Grade
======================================
PRODUCER'S PHILOSOPHY:
Location consistency is what makes a film feel like one world
rather than a collection of disconnected scenes.
The Underground Lab in Scene 1 must look identical to
the Underground Lab in Scene 3 — same server racks,
same lighting temperature, same color palette.

This is enforced through the Location Bible approval gate.

ROUTES:
GET    /locations/project/{id}              List all locations
GET    /locations/{id}                      Get single location detail
PUT    /locations/{id}/approve              Approve location (lock Bible entry)
PUT    /locations/{id}/reject               Reject and request regeneration
POST   /locations/project/{id}/approve-all  Approve all (demo/testing)
GET    /locations/project/{id}/bible        Get full Location Bible
GET    /locations/project/{id}/status       Approval status summary
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from models import Location, Project
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


def get_project_or_404(project_id: str, db: Session) -> Project:
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return p


def get_location_or_404(location_id: str, db: Session) -> Location:
    loc = db.query(Location).filter(Location.id == location_id).first()
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")
    return loc


@router.get("/project/{project_id}", response_model=list[dict])
async def list_locations(project_id: str, db: Session = Depends(get_db)):
    """List all locations for a project with approval status."""
    locs = db.query(Location).filter(Location.project_id == project_id).all()
    if not locs:
        raise HTTPException(
            status_code=404,
            detail="No locations found. Run script analysis first."
        )
    return [
        {
            "id": loc.id,
            "name": loc.name,
            "description": loc.description,
            "environment_type": loc.environment_type,
            "time_of_day": loc.time_of_day,
            "weather": loc.weather,
            "lighting_notes": loc.lighting_notes,
            "approved": loc.approved,
            "reference_image_url": loc.reference_image_url,
            "prompt_description": loc.prompt_description,
            "created_at": loc.created_at.isoformat(),
        }
        for loc in locs
    ]


@router.get("/{location_id}", response_model=dict)
async def get_location(location_id: str, db: Session = Depends(get_db)):
    """Get full details for a single location including Bible entry."""
    loc = get_location_or_404(location_id, db)
    project = db.query(Project).filter(Project.id == loc.project_id).first()

    bible_entry = {}
    if project and project.blueprint:
        loc_bible = project.blueprint.get("location_bible", {})
        for lid, entry in loc_bible.items():
            if entry.get("name") == loc.name:
                bible_entry = entry
                break

    return {
        "id": loc.id,
        "name": loc.name,
        "description": loc.description,
        "environment_type": loc.environment_type,
        "time_of_day": loc.time_of_day,
        "weather": loc.weather,
        "lighting_notes": loc.lighting_notes,
        "approved": loc.approved,
        "reference_image_url": loc.reference_image_url,
        "prompt_description": loc.prompt_description,
        "bible_entry": bible_entry,
    }


@router.put("/{location_id}/approve", response_model=dict)
async def approve_location(
    location_id: str,
    payload: dict = {},
    db: Session = Depends(get_db)
):
    """
    Approve a location — locks its visual identity for the entire film.
    Every scene set in this location will use this locked description.
    """
    loc = get_location_or_404(location_id, db)
    project = db.query(Project).filter(Project.id == loc.project_id).first()

    loc.approved = True
    if payload.get("reference_image_url"):
        loc.reference_image_url = payload["reference_image_url"]

    # Update Location Bible in blueprint
    if project and project.blueprint:
        loc_bible = project.blueprint.get("location_bible", {})
        for lid, entry in loc_bible.items():
            if entry.get("name") == loc.name:
                loc_bible[lid]["approved"] = True
                break
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(project, "blueprint")

    db.commit()
    logger.info(f"Location APPROVED and LOCKED: {loc.name}")

    return {
        "id": loc.id,
        "name": loc.name,
        "approved": loc.approved,
        "message": f"Location '{loc.name}' approved and locked for production."
    }


@router.put("/{location_id}/reject", response_model=dict)
async def reject_location(
    location_id: str,
    payload: dict = {},
    db: Session = Depends(get_db)
):
    """Reject a location and request revision with feedback."""
    loc = get_location_or_404(location_id, db)
    loc.approved = False
    loc.reference_image_url = None

    if payload.get("feedback"):
        loc.description = f"[REVISION: {payload['feedback']}] {loc.description or ''}"

    db.commit()
    return {
        "id": loc.id,
        "name": loc.name,
        "approved": False,
        "message": f"Location '{loc.name}' rejected for revision."
    }


@router.post("/project/{project_id}/approve-all", response_model=dict)
async def approve_all_locations(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    Approve all locations at once.
    PRODUCER NOTE: For demo and testing only.
    In real production, review each location individually.
    """
    project = get_project_or_404(project_id, db)
    locs = db.query(Location).filter(Location.project_id == project_id).all()

    if not locs:
        raise HTTPException(
            status_code=404,
            detail="No locations found. Run script analysis first."
        )

    approved_names = []
    for loc in locs:
        loc.approved = True
        approved_names.append(loc.name)

    # Update Location Bible
    if project.blueprint:
        loc_bible = project.blueprint.get("location_bible", {})
        for lid in loc_bible:
            loc_bible[lid]["approved"] = True
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(project, "blueprint")

    db.commit()
    logger.info(f"All locations approved for project {project_id}: {approved_names}")

    return {
        "project_id": project_id,
        "approved_count": len(approved_names),
        "approved_locations": approved_names,
        "message": f"All {len(approved_names)} locations approved and locked.",
        "next_step": "All bibles locked. Ready to start generation using POST /generation/{id}/start"
    }


@router.get("/project/{project_id}/bible", response_model=dict)
async def get_location_bible(project_id: str, db: Session = Depends(get_db)):
    """Get the full Location Bible for a project."""
    project = get_project_or_404(project_id, db)
    if not project.blueprint:
        raise HTTPException(status_code=404, detail="No blueprint found.")

    loc_bible = project.blueprint.get("location_bible", {})
    db_locs = db.query(Location).filter(Location.project_id == project_id).all()
    approved_count = sum(1 for l in db_locs if l.approved)
    total_count = len(db_locs)

    return {
        "project_id": project_id,
        "location_bible": loc_bible,
        "total_locations": total_count,
        "approved_count": approved_count,
        "all_approved": approved_count == total_count and total_count > 0,
        "message": (
            "All locations approved. Ready for generation."
            if approved_count == total_count and total_count > 0
            else f"{total_count - approved_count} location(s) still need approval."
        )
    }


@router.get("/project/{project_id}/status", response_model=dict)
async def get_location_approval_status(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Get location approval status summary."""
    locs = db.query(Location).filter(Location.project_id == project_id).all()
    approved = [l for l in locs if l.approved]
    unapproved = [l for l in locs if not l.approved]

    return {
        "project_id": project_id,
        "total_locations": len(locs),
        "approved": len(approved),
        "unapproved": len(unapproved),
        "approved_names": [l.name for l in approved],
        "unapproved_names": [l.name for l in unapproved],
        "ready_for_generation": len(unapproved) == 0 and len(locs) > 0,
        "next_action": (
            "All locations locked. Start generation."
            if len(unapproved) == 0 and len(locs) > 0
            else f"Approve remaining: {[l.name for l in unapproved]}"
        )
    }
