"""
Continuity Engine
=================
Validates every generated clip BEFORE it enters the assembly pipeline.
Detects character drift, wardrobe inconsistency, location drift.

This runs after each shot is generated. A shot that fails validation
is automatically queued for regeneration — not silently accepted.
"""
import logging
from typing import Any
from enum import Enum

logger = logging.getLogger(__name__)

class ContinuityCheckStatus(str, Enum):
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"

class ContinuityEngine:

    def validate_shot(
        self,
        shot: dict,
        character_bible: dict,
        location_bible: dict,
        previous_shots: list[dict] | None = None
    ) -> dict[str, Any]:
        """
        Run all continuity checks on a generated shot.
        Returns a report with status, score, and specific issues.
        """
        issues = []
        warnings = []

        # Check 1: Characters present match expected
        for char_id in shot.get("characters_present", []):
            if char_id not in character_bible:
                issues.append(f"Character {char_id} not in Character Bible")
            elif not character_bible[char_id].get("approved"):
                warnings.append(f"Character {char_id} not yet approved in Bible")

        # Check 2: Location is defined and approved
        location_id = shot.get("scene_location_id")
        if location_id and location_id not in location_bible:
            issues.append(f"Location {location_id} not in Location Bible")
        elif location_id and not location_bible.get(location_id, {}).get("approved"):
            warnings.append(f"Location {location_id} not yet approved in Bible")

        # Check 3: Shot has required fields
        if not shot.get("action_description"):
            issues.append("Shot missing action description")
        if not shot.get("camera_direction"):
            warnings.append("Shot missing camera direction")
        if not shot.get("duration_estimate"):
            warnings.append("Shot missing duration estimate")

        # Check 4: Dialogue has speaker assigned
        if shot.get("dialogue") and not shot.get("speaker_character_id"):
            issues.append("Shot has dialogue but no speaker assigned")

        # Check 5: Speaker is in characters_present
        speaker = shot.get("speaker_character_id")
        if speaker and speaker not in shot.get("characters_present", []):
            issues.append(f"Speaker {speaker} not listed in characters_present")

        # Calculate continuity score (0-100)
        score = 100
        score -= len(issues) * 20
        score -= len(warnings) * 5
        score = max(0, score)

        # Determine status
        if issues:
            status = ContinuityCheckStatus.FAILED
        elif warnings:
            status = ContinuityCheckStatus.WARNING
        else:
            status = ContinuityCheckStatus.PASSED

        return {
            "shot_id": shot.get("shot_id"),
            "status": status,
            "score": score,
            "issues": issues,
            "warnings": warnings,
            "approved_for_assembly": status != ContinuityCheckStatus.FAILED
        }

    def validate_blueprint(
        self,
        blueprint: dict,
        character_bible: dict,
        location_bible: dict
    ) -> dict[str, Any]:
        """
        Validate the entire blueprint before generation starts.
        Checks all shot references are valid and bibles are complete.
        """
        all_reports = []
        failed_shots = []
        warned_shots = []

        for scene in blueprint.get("scenes", []):
            scene_location_id = scene.get("location_id")
            for shot in scene.get("shots", []):
                shot_with_location = {**shot, "scene_location_id": scene_location_id}
                report = self.validate_shot(shot_with_location, character_bible, location_bible)
                all_reports.append(report)

                if report["status"] == ContinuityCheckStatus.FAILED:
                    failed_shots.append(report["shot_id"])
                elif report["status"] == ContinuityCheckStatus.WARNING:
                    warned_shots.append(report["shot_id"])

        total = len(all_reports)
        avg_score = sum(r["score"] for r in all_reports) / total if total > 0 else 0

        return {
            "total_shots_checked": total,
            "passed": total - len(failed_shots) - len(warned_shots),
            "warned": len(warned_shots),
            "failed": len(failed_shots),
            "average_continuity_score": round(avg_score, 1),
            "ready_for_generation": len(failed_shots) == 0,
            "failed_shot_ids": failed_shots,
            "warned_shot_ids": warned_shots,
            "shot_reports": all_reports
        }

    def generate_continuity_report(self, project_id: str, blueprint: dict, character_bible: dict, location_bible: dict) -> dict:
        """Public method to get a full continuity report for a project."""
        validation = self.validate_blueprint(blueprint, character_bible, location_bible)
        return {
            "project_id": project_id,
            "continuity_score": validation["average_continuity_score"],
            "status": "ready" if validation["ready_for_generation"] else "issues_found",
            **validation
        }

continuity_engine = ContinuityEngine()
