from pydantic import BaseModel
from typing import Optional

class ContinuityReport(BaseModel):
    project_id: str
    continuity_score: float
    status: str
    total_shots_checked: int
    passed: int
    warned: int
    failed: int
    ready_for_generation: bool
    failed_shot_ids: list[str]
    warned_shot_ids: list[str]
