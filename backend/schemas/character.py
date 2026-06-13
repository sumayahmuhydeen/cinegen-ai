from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CharacterApprove(BaseModel):
    approved: bool
    reference_image_url: Optional[str] = None

class CharacterResponse(BaseModel):
    id: str
    project_id: str
    name: str
    role: Optional[str]
    description: Optional[str]
    appearance: Optional[str]
    age_range: Optional[str]
    voice_id: Optional[str]
    approved: bool
    reference_image_url: Optional[str]
    prompt_description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class CharacterBibleResponse(BaseModel):
    project_id: str
    characters: list[dict]
    all_approved: bool
    approval_count: int
    total_count: int
