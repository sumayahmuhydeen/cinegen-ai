"""
Kling Video Generation Integration
====================================
Wraps the Kling 1.6 API for short video clip generation.
Each shot generates a 5-15 second clip using a constrained prompt
assembled by the Bible System.

Model-agnostic interface: swap Kling for Runway without touching the pipeline.
"""
import httpx
import asyncio
import logging
import os
from typing import Optional
from core.config import settings

logger = logging.getLogger(__name__)

KLING_API_BASE = "https://api.klingai.com/v1"

class KlingClient:
    """
    Async client for Kling 1.6 video generation API.
    Falls back to mock mode if no API key is set.
    """

    def __init__(self):
        self.api_key = settings.KLING_API_KEY
        self.mock_mode = not bool(self.api_key)
        if self.mock_mode:
            logger.warning("KLING_API_KEY not set — using mock video generation")

    async def generate_clip(
        self,
        prompt: str,
        duration: int = 5,
        aspect_ratio: str = "16:9",
        shot_id: str = "",
    ) -> dict:
        """
        Generate a video clip from a prompt.
        Returns dict with job_id and status.
        Phase 3: real Kling API call.
        Phase 3 mock: returns a placeholder response immediately.
        """
        if self.mock_mode:
            return await self._mock_generate(prompt, duration, shot_id)

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{KLING_API_BASE}/videos/text2video",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "kling-v1-6",
                        "prompt": prompt,
                        "duration": str(duration),
                        "aspect_ratio": aspect_ratio,
                        "cfg_scale": 0.5,
                        "mode": "std",
                    }
                )
                response.raise_for_status()
                data = response.json()
                return {
                    "job_id": data.get("data", {}).get("task_id"),
                    "status": "submitted",
                    "shot_id": shot_id,
                    "provider": "kling",
                }
            except httpx.HTTPError as e:
                logger.error(f"Kling API error for shot {shot_id}: {e}")
                raise

    async def get_clip_status(self, job_id: str) -> dict:
        """Poll Kling for job status and video URL when complete."""
        if self.mock_mode:
            return {
                "job_id": job_id,
                "status": "completed",
                "video_url": f"https://mock-storage.cinegen.ai/clips/{job_id}.mp4",
                "duration": 5,
            }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{KLING_API_BASE}/videos/text2video/{job_id}",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            response.raise_for_status()
            data = response.json().get("data", {})
            status = data.get("task_status", "processing")
            video_url = None
            if status == "succeed":
                works = data.get("task_result", {}).get("videos", [])
                if works:
                    video_url = works[0].get("url")
            return {
                "job_id": job_id,
                "status": "completed" if status == "succeed" else "processing",
                "video_url": video_url,
            }

    async def _mock_generate(self, prompt: str, duration: int, shot_id: str) -> dict:
        """Simulates a Kling API call for local development."""
        await asyncio.sleep(0.5)
        mock_job_id = f"mock_kling_{shot_id}_{os.urandom(4).hex()}"
        logger.info(f"[MOCK] Kling job created: {mock_job_id}")
        return {
            "job_id": mock_job_id,
            "status": "completed",
            "video_url": f"https://mock-storage.cinegen.ai/clips/{mock_job_id}.mp4",
            "shot_id": shot_id,
            "provider": "kling_mock",
            "prompt_preview": prompt[:100] + "..." if len(prompt) > 100 else prompt,
        }

kling_client = KlingClient()
