"""
Runway Gen-3 Alpha Integration
================================
Backup video generation model.
Same interface as kling.py — swap providers without touching the pipeline.
"""
import httpx
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
            logger.warning("RUNWAY_API_KEY not set — using mock mode")

    async def generate_clip(self, prompt: str, duration: int = 5, shot_id: str = "") -> dict:
        if self.mock_mode:
            await asyncio.sleep(0.3)
            job_id = f"mock_runway_{shot_id}_{os.urandom(4).hex()}"
            return {
                "job_id": job_id,
                "status": "completed",
                "video_url": f"https://mock-storage.cinegen.ai/clips/{job_id}.mp4",
                "shot_id": shot_id,
                "provider": "runway_mock",
            }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.runwayml.com/v1/image_to_video",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "X-Runway-Version": "2024-09-13",
                },
                json={
                    "promptText": prompt,
                    "duration": int(duration),
                    "ratio": "1280:720",
                }
            )
            response.raise_for_status()
            data = response.json()
            return {
                "job_id": data.get("id"),
                "status": "submitted",
                "shot_id": shot_id,
                "provider": "runway",
            }

runway_client = RunwayClient()
