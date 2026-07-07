"""
Characters Routes — Production Grade
======================================
PRODUCER'S PHILOSOPHY:
Character approval is the most critical gate in the entire pipeline.
A film with inconsistent characters is not a film — it is a collection
of unrelated clips. Every character must be locked and approved before
a single frame generates.

APPROVAL WORKFLOW:
1. Script analysis creates Character Bible entries (unapproved)
2. System generates reference image prompts for each character
3. User reviews character profile and prompt
4. User approves — character is LOCKED for entire production
5. Generation cannot start until ALL characters are approved
6. Voice is assigned and locked at the same time as visual approval

ROUTES:
GET    /characters/project/{id}              List all characters
GET    /characters/{id}                      Get single character detail
PUT    /characters/{id}/approve              Approve character (lock Bible entry)
PUT    /characters/{id}/reject               Reject and request regeneration
POST   /characters/project/{id}/approve-all  Approve all (for testing/demo)
GET    /characters/project/{id}/bible        Get full Character Bible
GET    /characters/project/{id}/voices       Get available voices for assignment
PUT    /characters/{id}/assign-voice         Assign specific voice to character
GET    /characters/project/{id}/status       Approval status summary
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from models import Character, Project
from integrations.elevenlabs import elevenlabs_client, VOICE_LIBRARY
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


def get_project_or_404(project_id: str, db: Session) -> Project:
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return p


def get_character_or_404(character_id: str, db: Session) -> Character:
    c = db.query(Character).filter(Character.id == character_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Character not found")
    return c


# ── List Characters ────────────────────────────────────────────────────────────

@router.get("/project/{project_id}", response_model=list[dict])
async def list_characters(project_id: str, db: Session = Depends(get_db)):
    """
    List all characters for a project.
    Returns full profile including Bible prompt and approval status.
    """
    chars = db.query(Character).filter(
        Character.project_id == project_id
    ).all()

    if not chars:
        raise HTTPException(
            status_code=404,
            detail="No characters found. Run script analysis first."
        )

    return [
        {
            "id": c.id,
            "name": c.name,
            "role": c.role,
            "description": c.description,
            "appearance": c.appearance,
            "age_range": c.age_range,
            "voice_id": c.voice_id,
            "approved": c.approved,
            "reference_image_url": c.reference_image_url,
            "prompt_description": c.prompt_description,
            "created_at": c.created_at.isoformat(),
        }
        for c in chars
    ]


# ── Get Single Character ───────────────────────────────────────────────────────

@router.get("/{character_id}", response_model=dict)
async def get_character(character_id: str, db: Session = Depends(get_db)):
    """Get full details for a single character including Bible entry."""
    char = get_character_or_404(character_id, db)
    project = db.query(Project).filter(Project.id == char.project_id).first()

    # Get Bible entry if blueprint exists
    bible_entry = {}
    if project and project.blueprint:
        char_bible = project.blueprint.get("character_bible", {})
        # Find this character's Bible entry by name match
        for cid, entry in char_bible.items():
            if entry.get("name") == char.name:
                bible_entry = entry
                break

    return {
        "id": char.id,
        "name": char.name,
        "role": char.role,
        "description": char.description,
        "appearance": char.appearance,
        "age_range": char.age_range,
        "voice_id": char.voice_id,
        "approved": char.approved,
        "reference_image_url": char.reference_image_url,
        "prompt_description": char.prompt_description,
        "bible_entry": bible_entry,
        "created_at": char.created_at.isoformat(),
    }


# ── Approve Character ──────────────────────────────────────────────────────────

@router.put("/{character_id}/approve", response_model=dict)
async def approve_character(
    character_id: str,
    payload: dict = {},
    db: Session = Depends(get_db)
):
    """
    PRODUCER'S MOST IMPORTANT ACTION.
    Approve a character — this locks their visual identity and voice
    for the entire production. Cannot be undone without regenerating
    all shots featuring this character.

    Optional payload:
    {
        "reference_image_url": "url to approved reference image",
        "voice_id": "specific ElevenLabs voice ID override"
    }
    """
    char = get_character_or_404(character_id, db)
    project = db.query(Project).filter(Project.id == char.project_id).first()

    # Lock the character
    char.approved = True

    if payload.get("reference_image_url"):
        char.reference_image_url = payload["reference_image_url"]

    if payload.get("voice_id"):
        char.voice_id = payload["voice_id"]

    # Also update the Character Bible in the project blueprint
    if project and project.blueprint:
        char_bible = project.blueprint.get("character_bible", {})
        for cid, entry in char_bible.items():
            if entry.get("name") == char.name:
                char_bible[cid]["approved"] = True
                if payload.get("voice_id"):
                    char_bible[cid]["voice_id"] = payload["voice_id"]
                break

        # SQLAlchemy needs explicit flag for JSON mutation
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(project, "blueprint")

    db.commit()
    db.refresh(char)

    logger.info(f"Character APPROVED and LOCKED: {char.name} (project={char.project_id})")

    return {
        "id": char.id,
        "name": char.name,
        "approved": char.approved,
        "voice_id": char.voice_id,
        "message": f"Character '{char.name}' approved and locked for production.",
        "warning": "This character's visual identity is now locked. Changing it will require regenerating all shots featuring this character."
    }


# ── Reject Character ───────────────────────────────────────────────────────────

@router.put("/{character_id}/reject", response_model=dict)
async def reject_character(
    character_id: str,
    payload: dict = {},
    db: Session = Depends(get_db)
):
    """
    Reject a character's current description.
    Provide feedback so the AI can regenerate a better profile.
    """
    char = get_character_or_404(character_id, db)
    char.approved = False
    char.reference_image_url = None

    # Store rejection notes in description for context
    if payload.get("feedback"):
        char.description = f"[REVISION REQUESTED: {payload['feedback']}] {char.description or ''}"

    db.commit()

    logger.info(f"Character REJECTED for revision: {char.name}")

    return {
        "id": char.id,
        "name": char.name,
        "approved": False,
        "feedback": payload.get("feedback", ""),
        "message": f"Character '{char.name}' rejected. Provide updated description and re-approve."
    }


# ── Approve All (Demo / Testing) ───────────────────────────────────────────────

@router.post("/project/{project_id}/approve-all", response_model=dict)
async def approve_all_characters(
    project_id: str,
    db: Session = Depends(get_db)
):
    """
    Approve all characters at once.

    PRODUCER'S NOTE: Use this for demo and testing ONLY.
    In real production, each character should be individually
    reviewed and approved before locking.
    """
    project = get_project_or_404(project_id, db)
    chars = db.query(Character).filter(
        Character.project_id == project_id
    ).all()

    if not chars:
        raise HTTPException(
            status_code=404,
            detail="No characters found. Run script analysis first."
        )

    approved_names = []
    for char in chars:
        char.approved = True

        # Auto-assign voice if not already set
        if not char.voice_id:
            char_data = {
                "name": char.name,
                "role": char.role or "",
                "voice_style": "",
                "physical_description": char.appearance or "",
                "personality": char.description or "",
            }
            char.voice_id = elevenlabs_client.assign_voice(char_data)

        approved_names.append(char.name)

    # Update Character Bible in blueprint
    if project.blueprint:
        char_bible = project.blueprint.get("character_bible", {})
        for cid, entry in char_bible.items():
            char_bible[cid]["approved"] = True

        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(project, "blueprint")

    db.commit()

    logger.info(f"All characters approved for project {project_id}: {approved_names}")

    return {
        "project_id": project_id,
        "approved_count": len(approved_names),
        "approved_characters": approved_names,
        "message": f"All {len(approved_names)} characters approved and locked for production.",
        "next_step": "Now approve all locations using POST /locations/project/{id}/approve-all, then start generation."
    }


# ── Assign Voice ───────────────────────────────────────────────────────────────

@router.put("/{character_id}/assign-voice", response_model=dict)
async def assign_voice(
    character_id: str,
    payload: dict,
    db: Session = Depends(get_db)
):
    """
    Assign a specific ElevenLabs voice to a character.
    Must be done before or at approval time.
    """
    char = get_character_or_404(character_id, db)
    voice_id = payload.get("voice_id")

    if not voice_id:
        raise HTTPException(
            status_code=400,
            detail="voice_id is required. Get available voices from GET /characters/project/{id}/voices"
        )

    char.voice_id = voice_id
    db.commit()

    return {
        "id": char.id,
        "name": char.name,
        "voice_id": char.voice_id,
        "message": f"Voice assigned to {char.name}"
    }


# ── Get Available Voices ───────────────────────────────────────────────────────

@router.get("/project/{project_id}/voices", response_model=dict)
async def get_available_voices(project_id: str):
    """
    Get the full voice library available for character assignment.
    Each voice has a profile description to help producers choose.
    """
    voices = [
        {"voice_id": vid, "profile": name, "best_for": _voice_guidance(name)}
        for name, vid in VOICE_LIBRARY.items()
    ]
    return {
        "voices": voices,
        "total": len(voices),
        "note": "Assign voices before approving characters for best results."
    }


def _voice_guidance(profile: str) -> str:
    """Producer guidance on which character type suits each voice."""
    guidance = {
        "male_deep":        "Male protagonist, authority figure, detective, hero",
        "male_cold":        "Male antagonist, villain, calculating character",
        "male_natural":     "Supporting male, everyman, neutral character",
        "female_warm":      "Female protagonist, empathetic character, hero",
        "female_crisp":     "Female antagonist, professional, intelligent villain",
        "female_natural":   "Supporting female, conversational character",
        "narrator_male":    "Documentary narrator, omniscient narrator, voiceover",
        "narrator_female":  "Warm narrator, documentary, educational content",
    }
    return guidance.get(profile, "General purpose")


# ── Character Bible ────────────────────────────────────────────────────────────

@router.get("/project/{project_id}/bible", response_model=dict)
async def get_character_bible(project_id: str, db: Session = Depends(get_db)):
    """
    Get the full Character Bible for a project.
    Shows locked prompts, approval status, and voice assignments.
    """
    project = get_project_or_404(project_id, db)

    if not project.blueprint:
        raise HTTPException(
            status_code=404,
            detail="No blueprint found. Run script analysis first."
        )

    char_bible = project.blueprint.get("character_bible", {})
    db_chars = db.query(Character).filter(
        Character.project_id == project_id
    ).all()

    approved_count = sum(1 for c in db_chars if c.approved)
    total_count = len(db_chars)

    return {
        "project_id": project_id,
        "character_bible": char_bible,
        "total_characters": total_count,
        "approved_count": approved_count,
        "all_approved": approved_count == total_count and total_count > 0,
        "generation_blocked": approved_count < total_count,
        "message": (
            "All characters approved. Ready for generation."
            if approved_count == total_count and total_count > 0
            else f"{total_count - approved_count} character(s) still need approval before generation can start."
        )
    }


# ── Approval Status ────────────────────────────────────────────────────────────

@router.get("/project/{project_id}/status", response_model=dict)
async def get_approval_status(project_id: str, db: Session = Depends(get_db)):
    """
    Get a clean approval status summary.
    Use this to know whether you can start generation.
    """
    chars = db.query(Character).filter(
        Character.project_id == project_id
    ).all()

    approved = [c for c in chars if c.approved]
    unapproved = [c for c in chars if not c.approved]

    return {
        "project_id": project_id,
        "total_characters": len(chars),
        "approved": len(approved),
        "unapproved": len(unapproved),
        "approved_names": [c.name for c in approved],
        "unapproved_names": [c.name for c in unapproved],
        "ready_for_generation": len(unapproved) == 0 and len(chars) > 0,
        "next_action": (
            "Characters approved. Now approve locations."
            if len(unapproved) == 0 and len(chars) > 0
            else f"Approve remaining characters: {[c.name for c in unapproved]}"
        )
    }
