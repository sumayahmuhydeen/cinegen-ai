"""
Shot Generator Service — Production Grade
==========================================
PRODUCER'S PHILOSOPHY:
A film is built shot by shot. Each shot has a purpose —
to advance story, reveal character, or establish world.
The Shot Generator treats each shot as a deliberate
creative decision, not just an API call.

PIPELINE PER SHOT:
1. Retrieve shot from blueprint (with Shot ID)
2. Select optimal Kling model for this shot type
3. Enrich prompt with cinematic language
4. Validate continuity pre-check (character + location bibles)
5. Submit to Kling with negative prompt
6. Poll until complete
7. Validate output quality
8. Accept or queue for regeneration (max 3 retries)
9. Log cost and performance metrics

CONCURRENCY:
Generate up to 3 shots simultaneously per scene.
Never more — Kling rate limits and quality suffers above this.
"""
import asyncio
import logging
from dataclasses import dataclass, asdict
from typing import Optional
from integrations.kling import kling_client, GenerationResult
from integrations.runway import runway_client
from services.bible_system import bible_system
from services.continuity_engine import continuity_engine

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
SCENE_CONCURRENCY = 3  # max parallel shots per scene

@dataclass
class ShotResult:
    """Complete result for one generated shot."""
    shot_id: str
    status: str
    video_url: Optional[str]
    generation_prompt: str
    model_used: str
    cost_usd: float
    continuity_score: float
    duration_seconds: float
    provider: str
    attempt_count: int
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


class ShotGeneratorService:
    """
    Orchestrates shot-by-shot video generation with
    continuity validation, model selection, and retry logic.
    """

    def __init__(self):
        self.primary_client = kling_client
        self.fallback_client = runway_client

    async def generate_shot(
        self,
        shot: dict,
        scene: dict,
        character_bible: dict,
        location_bible: dict,
        style_bible: dict,
    ) -> ShotResult:
        """
        Generate a single shot — the core production unit.
        Applies Bible constraints, model selection, and continuity checking.
        """
        shot_id = shot.get("shot_id", shot.get("id", "unknown"))
        camera = shot.get("camera_direction", "Medium Shot")
        emotion = shot.get("emotion", "neutral")

        logger.info(
            f"Generating shot {shot_id} | "
            f"camera={camera} | emotion={emotion} | "
            f"dialogue={'yes' if shot.get('dialogue') else 'no'}"
        )

        # Step 1: Continuity pre-check
        shot_with_loc = {**shot, "scene_location_id": scene.get("location_id")}
        continuity = continuity_engine.validate_shot(
            shot_with_loc, character_bible, location_bible
        )

        if continuity["status"] == "failed":
            logger.warning(f"Shot {shot_id} failed continuity: {continuity['issues']}")
            return ShotResult(
                shot_id=shot_id, status="failed",
                video_url=None, generation_prompt="",
                model_used="none", cost_usd=0.0,
                continuity_score=continuity["score"],
                duration_seconds=0, provider="none",
                attempt_count=0,
                error=f"Continuity failed: {', '.join(continuity['issues'])}",
            )

        # Step 2: Build cinematic prompt from Bibles
        base_prompt = bible_system.build_shot_prompt(
            shot=shot,
            character_bible=character_bible,
            location_bible=location_bible,
            style_bible=style_bible,
            scene_location_id=scene.get("location_id", ""),
        )

        # Step 3: Enrich with cinematic language (producer layer)
        enriched_prompt = kling_client.build_cinematic_prompt(
            base_prompt=base_prompt,
            camera_direction=camera,
            emotion=emotion,
            style_suffix=style_bible.get("global_prompt_suffix", ""),
        )

        # Step 4: Generate with retry logic
        duration = max(5, min(shot.get("duration_estimate", 8), 10))

        for attempt in range(MAX_RETRIES):
            try:
                # Use primary (Kling) for first 2 attempts, fallback (Runway) for 3rd
                if attempt < 2:
                    result = await self.primary_client.generate_and_wait(
                        prompt=enriched_prompt,
                        shot=shot,
                        duration=duration,
                        shot_id=shot_id,
                    )
                    provider = "kling"
                else:
                    logger.warning(f"Shot {shot_id}: switching to Runway fallback")
                    result = await self.fallback_client.generate_clip(
                        prompt=enriched_prompt,
                        duration=duration,
                        shot_id=shot_id,
                    )
                    provider = "runway"

                # Build ShotResult from GenerationResult
                shot_result = ShotResult(
                    shot_id=shot_id,
                    status=result.status if hasattr(result, 'status') else result.get('status', 'completed'),
                    video_url=result.video_url if hasattr(result, 'video_url') else result.get('video_url'),
                    generation_prompt=enriched_prompt,
                    model_used=result.model_used if hasattr(result, 'model_used') else result.get('provider', provider),
                    cost_usd=result.cost_usd if hasattr(result, 'cost_usd') else 0.0,
                    continuity_score=float(continuity["score"]),
                    duration_seconds=result.duration_seconds if hasattr(result, 'duration_seconds') else float(duration),
                    provider=result.provider if hasattr(result, 'provider') else provider,
                    attempt_count=attempt + 1,
                )

                logger.info(
                    f"Shot {shot_id} DONE | "
                    f"status={shot_result.status} | "
                    f"model={shot_result.model_used} | "
                    f"cost=${shot_result.cost_usd:.4f} | "
                    f"attempt={attempt+1}"
                )
                return shot_result

            except Exception as e:
                logger.error(f"Shot {shot_id} attempt {attempt+1} failed: {e}")
                if attempt < MAX_RETRIES - 1:
                    wait = 2 ** attempt  # exponential backoff: 1s, 2s, 4s
                    logger.info(f"Retrying shot {shot_id} in {wait}s...")
                    await asyncio.sleep(wait)
                else:
                    return ShotResult(
                        shot_id=shot_id, status="failed",
                        video_url=None, generation_prompt=enriched_prompt,
                        model_used="failed", cost_usd=0.0,
                        continuity_score=float(continuity["score"]),
                        duration_seconds=0, provider="none",
                        attempt_count=MAX_RETRIES,
                        error=str(e),
                    )

    async def generate_scene(
        self,
        scene: dict,
        character_bible: dict,
        location_bible: dict,
        style_bible: dict,
        progress_callback=None,
    ) -> list[ShotResult]:
        """
        Generate all shots in a scene with controlled concurrency.
        Returns ordered list of ShotResults.
        """
        shots = scene.get("shots", [])
        scene_num = scene.get("scene_number", "?")

        logger.info(
            f"Scene {scene_num}: generating {len(shots)} shots "
            f"(max {SCENE_CONCURRENCY} concurrent)"
        )

        semaphore = asyncio.Semaphore(SCENE_CONCURRENCY)

        async def generate_with_semaphore(shot: dict) -> ShotResult:
            async with semaphore:
                result = await self.generate_shot(
                    shot=shot,
                    scene=scene,
                    character_bible=character_bible,
                    location_bible=location_bible,
                    style_bible=style_bible,
                )
                if progress_callback:
                    await progress_callback(result)
                return result

        results = await asyncio.gather(
            *[generate_with_semaphore(s) for s in shots],
            return_exceptions=False
        )

        completed = len([r for r in results if r.status == "completed"])
        total_cost = sum(r.cost_usd for r in results)

        logger.info(
            f"Scene {scene_num} complete: "
            f"{completed}/{len(shots)} shots | "
            f"total cost ${total_cost:.4f}"
        )

        return list(results)

    async def generate_full_film(
        self,
        blueprint: dict,
        character_bible: dict,
        location_bible: dict,
        style_bible: dict,
        progress_callback=None,
    ) -> dict:
        """
        Generate all scenes in a film sequentially.
        Scenes are sequential (story order matters),
        shots within each scene are parallel.
        Returns a complete production manifest.
        """
        scenes = blueprint.get("scenes", [])
        title = blueprint.get("title", "Untitled")

        logger.info(f"Starting full film generation: '{title}' — {len(scenes)} scenes")

        all_results = []
        total_cost = 0.0

        for scene in scenes:
            scene_results = await self.generate_scene(
                scene=scene,
                character_bible=character_bible,
                location_bible=location_bible,
                style_bible=style_bible,
                progress_callback=progress_callback,
            )
            all_results.extend(scene_results)
            total_cost += sum(r.cost_usd for r in scene_results)

        completed = [r for r in all_results if r.status == "completed"]
        failed = [r for r in all_results if r.status == "failed"]

        manifest = {
            "title": title,
            "total_shots": len(all_results),
            "completed_shots": len(completed),
            "failed_shots": len(failed),
            "success_rate": round(len(completed) / len(all_results) * 100, 1) if all_results else 0,
            "total_cost_usd": round(total_cost, 4),
            "average_continuity_score": round(
                sum(r.continuity_score for r in all_results) / len(all_results), 1
            ) if all_results else 0,
            "shot_results": [r.to_dict() for r in all_results],
            "failed_shot_ids": [r.shot_id for r in failed],
        }

        logger.info(
            f"Film generation complete: "
            f"{len(completed)}/{len(all_results)} shots | "
            f"${total_cost:.4f} total cost"
        )

        return manifest


shot_generator = ShotGeneratorService()
