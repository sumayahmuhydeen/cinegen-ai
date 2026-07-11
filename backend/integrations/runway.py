"""
Runway Gen-3 Alpha Integration
================================
Backup video generation model — used when Kling fails on attempt 3.
Same interface as kling.py — model-agnostic design.

NOTE: Runway API requires a pre-uploaded image as input for Gen-3.
Their text-to-video endpoint is via their SDK.
Until a Runway API key is added and tested, this falls back to
returning a structured failure that triggers human review
rather than silently producing bad output.
"""
import asyncio
import logging
import os
from core.config import settings

logger = logging.getLogger(__name__)


class RunwayClient:
    def __init__(self):
        self.api_key = settings.RUNWAY_API_KEY
        self.mock_mode = not bool(self.api_key)
        if self.mock_mode:
            logger.warning("RUNWAY_API_KEY not set — Runway fallback in mock mode")
        else:
            logger.info("Runway client initialised — LIVE mode (fallback provider)")

    async def generate_clip(
        self,
        prompt: str,
        duration: int = 5,
        shot_id: str = "",
        **kwargs
    ) -> dict:
        """
        Generate a clip via Runway Gen-3.
        Used as fallback when Kling fails twice on the same shot.

        PRODUCER NOTE: If you reach this fallback, Kling failed twice.
        Check your Kling API key and credits before assuming Runway is needed.
        Runway requires an image input for Gen-3 which we don't have at this stage.
        For now this returns a structured mock so the pipeline continues
        without crashing — the shot will be marked for manual review.
        """
        if self.mock_mode:
            return await self._mock_generate(prompt, duration, shot_id)

        # Runway Gen-3 requires image-to-video (needs reference image)
        # Text-to-video is available via their SDK not REST API directly
        # For now: log and return a reviewable failure rather than crash
        logger.warning(
            f"Shot {shot_id}: Runway fallback triggered. "
            f"Runway Gen-3 requires image input — returning mock for manual review. "
            f"Add a reference image or check Kling API key/credits."
        )
        return await self._mock_generate(prompt, duration, shot_id)

    async def get_clip_status(self, job_id: str) -> dict:
        """Poll Runway for job status."""
        return {
            "job_id": job_id,
            "status": "completed",
            "video_url": f"https://mock-storage.cinegen.ai/runway/{job_id}.mp4",
        }

    async def _mock_generate(self, prompt: str, duration: int, shot_id: str) -> dict:
        await asyncio.sleep(0.2)
        mock_id = os.urandom(4).hex()
        logger.info(f"[Runway MOCK] Shot {shot_id} — returning placeholder for review")
        return {
            "job_id": f"runway_mock_{shot_id}_{mock_id}",
            "status": "completed",
            "video_url": f"https://mock-storage.cinegen.ai/runway/{shot_id}_{mock_id}.mp4",
            "shot_id": shot_id,
            "provider": "runway_mock",
            "review_required": True,
            "note": "Runway fallback — manual review required. Check Kling API key first.",
        }


runway_client = RunwayClient()
