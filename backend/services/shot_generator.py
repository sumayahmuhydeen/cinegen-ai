"""
Shot Generator Service
=======================
Orchestrates the generation of a single video shot.

Pipeline per shot:
1. Fetch shot data + scene context
2. Build constrained prompt from Bible System
3. Submit to video model (Kling/Runway)
4. Poll until complete
5. Run continuity validation
6. Store result or queue for regeneration
"""
import asyncio
import logging
from typing import Any
from integrations.kling import kling_client
from integrations.runway import runway_client
from services.bible_system import bible_system
from services.continuity_engine import continuity_engine

logger = logging.getLogger(__name__)

class ShotGeneratorService:

    def __init__(self):
        # Primary: Kling, Fallback: Runway
        self.primary = kling_client
        self.fallback = runway_client
        self.max_retries = 3
        self.poll_interval = 10  # seconds between status polls

    async def generate_shot(
        self,
        shot: dict,
        scene: dict,
        character_bible: dict,
        location_bible: dict,
        style_bible: dict,
    ) -> dict:
        """
        Generate a single shot clip end-to-end.
        Returns result dict with video_url, status, continuity_score.
        """
        shot_id = shot.get("shot_id", shot.get("id", "unknown"))
        logger.info(f"Generating shot: {shot_id}")

        # Step 1: Build constrained generation prompt
        prompt = bible_system.build_shot_prompt(
            shot=shot,
            character_bible=character_bible,
            location_bible=location_bible,
            style_bible=style_bible,
            scene_location_id=scene.get("location_id", ""),
        )
        logger.debug(f"Shot prompt ({shot_id}): {prompt[:150]}...")

        # Step 2: Run continuity pre-check
        shot_with_location = {**shot, "scene_location_id": scene.get("location_id")}
        continuity_check = continuity_engine.validate_shot(
            shot_with_location, character_bible, location_bible
        )

        if continuity_check["status"] == "failed":
            logger.warning(f"Shot {shot_id} failed continuity pre-check: {continuity_check['issues']}")
            return {
                "shot_id": shot_id,
                "status": "failed",
                "reason": "continuity_pre_check_failed",
                "issues": continuity_check["issues"],
                "continuity_score": continuity_check["score"],
            }

        # Step 3: Submit to video generation model
        duration = min(shot.get("duration_estimate", 8), 10)  # cap at 10s per shot

        for attempt in range(self.max_retries):
            try:
                result = await self._generate_with_retry(prompt, duration, shot_id, attempt)
                result["generation_prompt"] = prompt
                result["continuity_score"] = continuity_check["score"]
                result["continuity_warnings"] = continuity_check.get("warnings", [])
                logger.info(f"Shot {shot_id} generated: {result.get('status')} (attempt {attempt+1})")
                return result

            except Exception as e:
                logger.error(f"Shot {shot_id} attempt {attempt+1} failed: {e}")
                if attempt == self.max_retries - 1:
                    return {
                        "shot_id": shot_id,
                        "status": "failed",
                        "reason": str(e),
                        "attempts": attempt + 1,
                    }
                await asyncio.sleep(2 ** attempt)  # exponential backoff

    async def _generate_with_retry(
        self, prompt: str, duration: int, shot_id: str, attempt: int
    ) -> dict:
        """Try primary model first, fall back to secondary if needed."""
        client = self.primary if attempt < 2 else self.fallback
        provider = "kling" if attempt < 2 else "runway"

        logger.info(f"Shot {shot_id} using {provider} (attempt {attempt+1})")
        result = await client.generate_clip(
            prompt=prompt,
            duration=duration,
            shot_id=shot_id,
        )

        # If job is async (not immediately complete), poll for result
        if result.get("status") == "submitted" and result.get("job_id"):
            result = await self._poll_for_completion(
                client, result["job_id"], shot_id
            )

        return result

    async def _poll_for_completion(
        self, client, job_id: str, shot_id: str, timeout: int = 300
    ) -> dict:
        """Poll video generation job until complete or timeout."""
        elapsed = 0
        while elapsed < timeout:
            await asyncio.sleep(self.poll_interval)
            elapsed += self.poll_interval

            status = await client.get_clip_status(job_id)
            logger.debug(f"Shot {shot_id} poll: {status.get('status')}")

            if status.get("status") == "completed":
                return status
            elif status.get("status") == "failed":
                raise Exception(f"Video generation failed for job {job_id}")

        raise TimeoutError(f"Shot {shot_id} timed out after {timeout}s")

    async def generate_scene_shots(
        self,
        scene: dict,
        character_bible: dict,
        location_bible: dict,
        style_bible: dict,
        concurrency: int = 2,
    ) -> list[dict]:
        """
        Generate all shots in a scene with limited concurrency.
        Uses a semaphore to avoid hammering the API.
        """
        semaphore = asyncio.Semaphore(concurrency)

        async def generate_one(shot):
            async with semaphore:
                return await self.generate_shot(
                    shot, scene, character_bible, location_bible, style_bible
                )

        shots = scene.get("shots", [])
        logger.info(f"Generating {len(shots)} shots for scene {scene.get('scene_id')}")
        results = await asyncio.gather(*[generate_one(s) for s in shots])
        return list(results)

shot_generator = ShotGeneratorService()
