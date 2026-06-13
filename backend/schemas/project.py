from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime

class ProjectCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    style: Optional[str] = None

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    style: Optional[str] = None

class ProjectResponse(BaseModel):
    id: str
    user_id: str
    title: str
    status: str
    style: Optional[str]
    scene_count: int
    character_count: int
    duration_estimate: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ScriptUpload(BaseModel):
    script_text: str = Field(..., min_length=50, description="The full script text to analyse")
    title: Optional[str] = None

class BlueprintResponse(BaseModel):
    project_id: str
    blueprint: dict[str, Any]
    total_scenes: int
    total_shots: int
    total_characters: int
    total_locations: int
    status: str
