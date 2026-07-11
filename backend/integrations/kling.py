"""
Kling Video Generation Integration — v3.0
==========================================
PRODUCER'S PHILOSOPHY:
Every shot in a film has a specific cinematic purpose.
A wide establishing shot needs different treatment than a close-up
dialogue scene. This integration uses a tiered model selection
strategy — matching the right Kling model to the right shot type
to balance quality, consistency, and cost.

TIERED MODEL STRATEGY (as a producer):
┌─────────────────────┬──────────────────┬─────────────┬──────────────────────────┐
│ Shot Type           │ Model            │ Cost/sec    │ Why                      │
├─────────────────────┼──────────────────┼─────────────┼──────────────────────────┤
│ Wide/Establishing   │ kling-v1-6       │ $0.04/sec   │ Location context, b-roll │
│ Standard Action     │ kling-v2-6-pro   │ $0.07/sec   │ Movement, reaction shots │
│ Dialogue/Character  │ kling-v3         │ $0.084/sec  │ Character face quality   │
│ Hero/Key Moments    │ kling-v3         │ $0.084/sec  │ Critical story beats     │
│ With Audio          │ kling-v3         │ $0.14/sec   │ Dialogue sync scenes     │
└─────────────────────┴──────────────────┴─────────────┴──────────────────────────┘

COST TRACKING:
Every generation is tracked with exact credit cost so the
platform can report per-project spend to users accurately.
"""

import httpx
import asyncio
import logging
import os
import time
import jwt  # PyJWT for Kling auth
from typing import Optional
from dataclasses import dataclass
from core.config import settings

logger = logging.getLogger(__name__)

# ── Kling API Configuration ───────────────────────────────────────────────────
KLING_API_BASE = "https://api.klingai.com"  # primary
KLING_API_SINGAPORE = "https://api-singapore.klingai.com"  # fallback region

# Model registry — producer's tiered selection
KLING_MODELS = {
    "standard":    "kling-v1-6",      # $0.04/sec — wide shots, b-roll
    "professional":"kling-v2-6-pro",  # $0.07/sec — action, reaction
    "cinematic":   "kling-v3",        # $0.084/sec — character, dialogue
    "hero":        "kling-v3",        # $0.084/sec — key story moments
}

# Cost per second per model (USD)
COST_PER_SECOND = {
    "kling-v1-6":      0.04,
    "kling-v2-6-pro":  0.07,
    "kling-v3":        0.084,
    "kling-v3-audio":  0.14,   # when audio generation included
}

# Camera directions that warrant higher quality models
CINEMATIC_CAMERAS = {"Close-Up", "Extreme Close-Up", "Over-Shoulder", "POV"}
WIDE_CAMERAS = {"Wide Shot", "Aerial", "Establishing"}
ACTION_CAMERAS = {"Tracking", "Medium Shot"}

@dataclass
class GenerationResult:
    """Structured result from a Kling generation job."""
    shot_id: str
    job_id: str
    status: str
    video_url: Optional[str]
    duration_seconds: float
    model_used: str
    cost_usd: float
    provider: str
    prompt_used: str
    error: Optional[str] = None


class KlingClient:
    """
    Production-grade Kling 3.0 client.

    As a producer: selects the right model per shot type.
    As a developer: handles auth, polling, retries, cost tracking.
    """

    def __init__(self):
        self.api_key = settings.KLING_API_KEY
        self.mock_mode = not bool(self.api_key)
        self._token_cache = {"token": None, "expires_at": 0}

        if self.mock_mode:
            logger.warning("KLING_API_KEY not set — running in mock mode")
        else:
            logger.info("Kling 3.0 client initialised — LIVE mode")

    # ── Authentication ────────────────────────────────────────────────────────

    def _get_auth_token(self) -> str:
        """
        Kling uses JWT tokens, not raw API keys in headers.
        The API key format is 'access_key_id:access_key_secret'.
        We generate a short-lived JWT and cache it.
        """
        now = time.time()

        # Return cached token if still valid (with 30s buffer)
        if self._token_cache["token"] and now < self._token_cache["expires_at"] - 30:
            return self._token_cache["token"]

        # Parse the API key
        if ":" not in self.api_key:
            # Some Kling keys are plain bearer tokens
            return self.api_key

        access_key_id, access_key_secret = self.api_key.split(":", 1)

        payload = {
            "iss": access_key_id,
            "exp": int(now) + 1800,  # 30 minute expiry
            "nbf": int(now) - 5,
        }

        token = jwt.encode(payload, access_key_secret, algorithm="HS256")
        self._token_cache = {"token": token, "expires_at": int(now) + 1800}
        return token

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._get_auth_token()}",
            "Content-Type": "application/json",
        }

    # ── Model Selection (Producer Logic) ─────────────────────────────────────

    def select_model(self, shot: dict) -> str:
        """
        As a producer: select the right model based on shot type.
        Match visual quality requirement to cost efficiency.
        """
        camera = shot.get("camera_direction", "Medium Shot")
        has_dialogue = bool(shot.get("dialogue"))
        characters_present = shot.get("characters_present", [])
        emotion = (shot.get("emotion") or "").lower()

        # Close-up character shots with dialogue → highest quality
        if camera in CINEMATIC_CAMERAS and has_dialogue:
            return KLING_MODELS["cinematic"]

        # Close-up character shots without dialogue → cinematic
        if camera in CINEMATIC_CAMERAS and characters_present:
            return KLING_MODELS["cinematic"]

        # Wide/aerial shots → standard (location doesn't need face quality)
        if camera in WIDE_CAMERAS:
            return KLING_MODELS["standard"]

        # High emotion moments → professional minimum
        if emotion in {"shocked", "dramatic", "epic", "revelatory", "tense"}:
            return KLING_MODELS["professional"]

        # Default: professional for everything else
        return KLING_MODELS["professional"]

    def calculate_cost(self, model: str, duration_seconds: float, has_audio: bool = False) -> float:
        """Calculate exact USD cost for a generation."""
        model_key = f"{model}-audio" if has_audio and model == "kling-v3" else model
        rate = COST_PER_SECOND.get(model_key, COST_PER_SECOND.get(model, 0.07))
        return round(rate * duration_seconds, 4)

    # ── Core Generation ───────────────────────────────────────────────────────

    async def generate_clip(
        self,
        prompt: str,
        shot: dict,
        duration: int = 5,
        aspect_ratio: str = "16:9",
        shot_id: str = "",
        negative_prompt: str = "",
    ) -> GenerationResult:
        """
        Generate a video clip for a single shot.
        Automatically selects the optimal model for this shot type.
        """
        if self.mock_mode:
            return await self._mock_generate(prompt, shot, duration, shot_id)

        model = self.select_model(shot)
        # Kling only accepts "5" or "10" as valid duration strings
        kling_duration = "5" if int(duration) <= 7 else "10"
        cost = self.calculate_cost(model, int(kling_duration))

        logger.info(f"Shot {shot_id}: model={model} duration={kling_duration}s cost=${cost}")

        # ── Kling hard limits ─────────────────────────────────────────
        # prompt: 0-2500 chars, negative_prompt: 0-2500 chars
        MAX_CHARS = 2400  # 100 char buffer below the 2500 limit
        safe_prompt = prompt[:MAX_CHARS] if len(prompt) > MAX_CHARS else prompt
        safe_neg    = (negative_prompt or self._default_negative_prompt())[:MAX_CHARS]

        if len(prompt) > MAX_CHARS:
            logger.warning(
                f"Shot {shot_id}: prompt truncated "
                f"{len(prompt)} → {MAX_CHARS} chars (Kling 2500 limit)"
            )

        payload = {
            "model_name": model,
            "prompt": safe_prompt,
            "negative_prompt": safe_neg,
            "cfg_scale": 0.5,
            "mode": "std",
            "aspect_ratio": aspect_ratio,
            "duration": kling_duration,
        }

        # Try primary endpoint first, then Singapore region
        endpoints = [KLING_API_BASE, KLING_API_SINGAPORE]

        async with httpx.AsyncClient(timeout=120.0) as client:
            last_error = None
            for endpoint in endpoints:
                try:
                    response = await client.post(
                        f"{endpoint}/v1/videos/text2video",
                        headers=self._headers(),
                        json=payload,
                    )

                    if response.status_code == 200:
                        data = response.json()
                        if data.get("code") != 0:
                            raise Exception(f"Kling API error: {data.get('message', 'Unknown error')}")

                        task_id = data["data"]["task_id"]
                        logger.info(f"Shot {shot_id}: Kling job submitted — task_id={task_id}")

                        return GenerationResult(
                            shot_id=shot_id,
                            job_id=task_id,
                            status="submitted",
                            video_url=None,
                            duration_seconds=int(kling_duration),
                            model_used=model,
                            cost_usd=cost,
                            provider="kling",
                            prompt_used=prompt[:200],
                        )
                    else:
                        error_text = response.text[:200]
                        logger.warning(f"Kling {endpoint} returned {response.status_code}: {error_text}")
                        last_error = Exception(f"HTTP {response.status_code}: {error_text}")

                except httpx.HTTPStatusError as e:
                    logger.warning(f"Kling endpoint {endpoint} failed: {e}")
                    last_error = e
                    continue

            # Both endpoints failed
            raise last_error or Exception("All Kling endpoints failed")

    async def poll_until_complete(
        self,
        job_id: str,
        shot_id: str,
        timeout_seconds: int = 600,
        poll_interval: int = 8,
    ) -> GenerationResult:
        """
        Poll Kling until the job completes or times out.
        Producer note: Kling 3.0 typically takes 90-180 seconds per clip.
        """
        if self.mock_mode:
            await asyncio.sleep(1)
            return GenerationResult(
                shot_id=shot_id,
                job_id=job_id,
                status="completed",
                video_url=f"https://mock-storage.cinegen.ai/clips/{job_id}.mp4",
                duration_seconds=5,
                model_used="kling-v3-mock",
                cost_usd=0.0,
                provider="kling_mock",
                prompt_used="",
            )

        elapsed = 0
        async with httpx.AsyncClient(timeout=30.0) as client:
            while elapsed < timeout_seconds:
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval

                try:
                    response = await client.get(
                        f"{KLING_API_BASE}/v1/videos/text2video/{job_id}",
                        headers=self._headers(),
                    )

                    # Try Singapore if primary fails
                    if response.status_code != 200:
                        response = await client.get(
                            f"{KLING_API_SINGAPORE}/v1/videos/text2video/{job_id}",
                            headers=self._headers(),
                        )

                    response.raise_for_status()
                    data = response.json()

                    if data.get("code") != 0:
                        raise Exception(f"Poll error: {data.get('message')}")

                    task = data["data"]
                    task_status = task.get("task_status", "processing")

                    logger.debug(f"Shot {shot_id} poll [{elapsed}s]: {task_status}")

                    if task_status == "succeed":
                        videos = task.get("task_result", {}).get("videos", [])
                        video_url = videos[0].get("url") if videos else None
                        duration = videos[0].get("duration", 5) if videos else 5

                        logger.info(f"Shot {shot_id} COMPLETED in {elapsed}s — {video_url}")

                        return GenerationResult(
                            shot_id=shot_id,
                            job_id=job_id,
                            status="completed",
                            video_url=video_url,
                            duration_seconds=float(duration),
                            model_used=task.get("model_name", "kling-v3"),
                            cost_usd=self.calculate_cost(
                                task.get("model_name", "kling-v3"), float(duration)
                            ),
                            provider="kling",
                            prompt_used="",
                        )

                    elif task_status == "failed":
                        error_msg = task.get("task_status_msg", "Unknown failure")
                        logger.error(f"Shot {shot_id} FAILED: {error_msg}")
                        return GenerationResult(
                            shot_id=shot_id,
                            job_id=job_id,
                            status="failed",
                            video_url=None,
                            duration_seconds=0,
                            model_used="kling-v3",
                            cost_usd=0.0,  # Failed jobs don't cost credits
                            provider="kling",
                            prompt_used="",
                            error=error_msg,
                        )

                except httpx.HTTPError as e:
                    logger.warning(f"Poll HTTP error for {shot_id}: {e} — retrying")
                    continue

        raise TimeoutError(f"Shot {shot_id} timed out after {timeout_seconds}s")

    async def generate_and_wait(
        self,
        prompt: str,
        shot: dict,
        duration: int = 5,
        shot_id: str = "",
        negative_prompt: str = "",
    ) -> GenerationResult:
        """
        Convenience method: submit and poll in one call.
        This is what the ShotGeneratorService calls per shot.
        """
        result = await self.generate_clip(
            prompt=prompt,
            shot=shot,
            duration=duration,
            shot_id=shot_id,
            negative_prompt=negative_prompt,
        )

        # If already complete (mock mode or immediate response)
        if result.status == "completed":
            return result

        # Poll for real jobs
        return await self.poll_until_complete(
            job_id=result.job_id,
            shot_id=shot_id,
        )

    # ── Prompt Engineering (Producer Logic) ──────────────────────────────────

    def _default_negative_prompt(self) -> str:
        """
        As a producer: what we never want in our shots.
        These negatives prevent the most common AI video artifacts.
        """
        return (
            "blurry, low quality, distorted faces, morphing body parts, "
            "extra limbs, duplicate people, watermark, text overlay, "
            "cartoon, anime, painting, illustration, oversaturated, "
            "shaky camera unless specified, jump cuts, flash cuts, "
            "inconsistent lighting, green screen artifacts"
        )

    def build_cinematic_prompt(
        self,
        base_prompt: str,
        camera_direction: str,
        emotion: str,
        style_suffix: str = "",
    ) -> str:
        """
        As a producer: enrich the base prompt with cinematic language
        that Kling 3.0 responds well to.
        """
        camera_language = {
            "Wide Shot": "wide establishing shot, full scene visible",
            "Medium Shot": "medium shot, waist up framing",
            "Close-Up": "tight close-up, face filling frame, shallow depth of field",
            "Extreme Close-Up": "extreme close-up, eyes and expression only",
            "Over-Shoulder": "over-shoulder shot, two-person framing",
            "POV": "first-person point of view shot, immersive perspective",
            "Aerial": "aerial drone shot, bird's eye view, slowly pulling back",
            "Tracking": "smooth tracking shot, camera follows subject",
        }

        emotion_language = {
            "tense": "dramatic tension, intense atmosphere",
            "shocked": "moment of revelation, stunned expression",
            "determined": "resolute and focused, strong posture",
            "calculating": "cold intelligence, measured movement",
            "contemplative": "quiet introspection, stillness",
            "epic": "grand and powerful, cinematic scope",
            "sad": "melancholic, subdued colour grading",
            "angry": "fierce intensity, aggressive energy",
        }

        cam = camera_language.get(camera_direction, camera_direction.lower())
        emo = emotion_language.get(emotion.lower(), emotion.lower())

        enriched = (
            f"{cam}, {base_prompt}, "
            f"{emo}, "
            f"cinematic film production quality, "
            f"professional colour grading, "
            f"photorealistic, "
            f"8K resolution film look"
        )

        if style_suffix:
            enriched += f", {style_suffix}"

        return enriched

    # ── Mock Mode ─────────────────────────────────────────────────────────────

    async def _mock_generate(
        self,
        prompt: str,
        shot: dict,
        duration: int,
        shot_id: str,
    ) -> GenerationResult:
        """
        Realistic mock that simulates the full Kling pipeline
        including model selection and cost calculation.
        """
        await asyncio.sleep(0.5)

        model = self.select_model(shot)
        cost = self.calculate_cost(model, duration)
        mock_job_id = f"mock_kling_{shot_id}_{os.urandom(4).hex()}"

        logger.info(
            f"[MOCK] Shot {shot_id}: model={model} "
            f"duration={duration}s cost=${cost} job={mock_job_id}"
        )

        return GenerationResult(
            shot_id=shot_id,
            job_id=mock_job_id,
            status="completed",
            video_url=f"https://mock-storage.cinegen.ai/clips/{mock_job_id}.mp4",
            duration_seconds=float(duration),
            model_used=model,
            cost_usd=cost,
            provider="kling_mock",
            prompt_used=prompt[:200],
        )

    # ── Account Info ──────────────────────────────────────────────────────────

    async def get_account_info(self) -> dict:
        """Check remaining credits and account status."""
        if self.mock_mode:
            return {
                "mode": "mock",
                "credits_remaining": "unlimited (mock)",
                "models_available": list(KLING_MODELS.values()),
            }

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.get(
                    f"{KLING_API_BASE}/v1/account/costs",
                    headers=self._headers(),
                )
                response.raise_for_status()
                return response.json().get("data", {})
            except Exception as e:
                logger.error(f"Failed to get Kling account info: {e}")
                return {"error": str(e)}


kling_client = KlingClient()
