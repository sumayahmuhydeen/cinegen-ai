"""
Suno Music Generation Integration
====================================
Generates per-scene background music from emotional tone metadata.
Each scene gets its own music bed matched to the emotional arc.
"""
import asyncio
import logging
import os
from core.config import settings

logger = logging.getLogger(__name__)

class SunoClient:
    def __init__(self):
        self.api_key = settings.SUNO_API_KEY
        self.mock_mode = not bool(self.api_key)
        if self.mock_mode:
            logger.warning("SUNO_API_KEY not set — using mock music generation")

    async def generate_music(
        self,
        emotion: str,
        style: str = "cinematic orchestral",
        duration_seconds: int = 60,
        scene_id: str = "",
    ) -> dict:
        """
        Generate background music for a scene.
        Prompt is built from the scene's emotional tone and film style.
        """
        prompt = self._build_music_prompt(emotion, style)

        if self.mock_mode:
            return await self._mock_generate(prompt, duration_seconds, scene_id)

        # Suno API integration (add when API key available)
        # Currently Suno's API is invite-only — placeholder for when available
        logger.info(f"Suno API: generating music for scene {scene_id}")
        return await self._mock_generate(prompt, duration_seconds, scene_id)

    def _build_music_prompt(self, emotion: str, style: str) -> str:
        emotion_map = {
            "tense":        "suspenseful tension building, low strings, staccato brass",
            "inspiring":    "uplifting orchestral swell, rising strings, triumphant horns",
            "sad":          "melancholic piano, sparse strings, minor key",
            "action":       "intense percussion, driving rhythm, urgent brass",
            "mysterious":   "ambient pads, subtle percussion, mysterious woodwinds",
            "romantic":     "warm strings, gentle piano, soft crescendo",
            "shocking":     "sudden brass hit, dissonant chord, building dread",
            "resolute":     "determined march rhythm, full orchestra, major key",
            "contemplative":"sparse piano, atmospheric pads, slow tempo",
            "epic":         "full orchestra, choir, dramatic percussion",
        }
        mood_desc = emotion_map.get(emotion.lower(), "neutral cinematic background music")
        return f"{style}, {mood_desc}, no lyrics, film score quality"

    async def _mock_generate(self, prompt: str, duration: int, scene_id: str) -> dict:
        await asyncio.sleep(0.2)
        mock_id = os.urandom(4).hex()
        return {
            "scene_id": scene_id,
            "audio_url": f"https://mock-storage.cinegen.ai/music/{scene_id}_{mock_id}.mp3",
            "duration_seconds": duration,
            "prompt": prompt,
            "provider": "suno_mock",
        }

suno_client = SunoClient()
