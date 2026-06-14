"""
ElevenLabs Voice Generation Integration
=========================================
Generates character voices and narration.
One voice ID is locked per character in the Character Bible
and never changes across the entire film.
"""
import httpx
import asyncio
import logging
import os
from core.config import settings

logger = logging.getLogger(__name__)

ELEVENLABS_BASE = "https://api.elevenlabs.io/v1"

# Default voice IDs — used when no character-specific voice is assigned
DEFAULT_VOICES = {
    "male_deep":       "pNInz6obpgDQGcFmaJgB",  # Adam
    "male_neutral":    "yoZ06aMxZJJ28mfd3POQ",  # Sam
    "female_warm":     "EXAVITQu4vr4xnSDxMaL",  # Bella
    "female_crisp":    "ThT5KcBeYPX3keUQqHPh",  # Dorothy
    "narrator_male":   "VR6AewLTigWG4xSOukaG",  # Arnold
    "narrator_female": "MF3mGyEYCl7XYWbV9V6O",  # Elli
}

class ElevenLabsClient:
    def __init__(self):
        self.api_key = settings.ELEVENLABS_API_KEY
        self.mock_mode = not bool(self.api_key)
        if self.mock_mode:
            logger.warning("ELEVENLABS_API_KEY not set — using mock audio generation")

    async def generate_speech(
        self,
        text: str,
        voice_id: str = "pNInz6obpgDQGcFmaJgB",
        shot_id: str = "",
        stability: float = 0.5,
        similarity_boost: float = 0.75,
        emotion: str = "neutral",
    ) -> dict:
        """
        Generate speech audio for a line of dialogue or narration.
        Returns dict with audio_url and duration_estimate.
        """
        if not text or not text.strip():
            return {"audio_url": None, "shot_id": shot_id, "skipped": True, "reason": "no_text"}

        if self.mock_mode:
            return await self._mock_generate(text, voice_id, shot_id)

        # Adjust style based on emotion
        style = self._emotion_to_style(emotion)

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{ELEVENLABS_BASE}/text-to-speech/{voice_id}",
                    headers={
                        "xi-api-key": self.api_key,
                        "Content-Type": "application/json",
                        "Accept": "audio/mpeg"
                    },
                    json={
                        "text": text,
                        "model_id": "eleven_multilingual_v2",
                        "voice_settings": {
                            "stability": stability,
                            "similarity_boost": similarity_boost,
                            "style": style,
                            "use_speaker_boost": True
                        }
                    }
                )
                response.raise_for_status()

                # In production: upload audio bytes to R2 storage
                # For now return a placeholder with the job details
                audio_size_bytes = len(response.content)
                duration_estimate = audio_size_bytes / 32000  # rough estimate

                return {
                    "shot_id": shot_id,
                    "audio_url": f"https://storage.cinegen.ai/audio/{shot_id}_dialogue.mp3",
                    "duration_seconds": duration_estimate,
                    "voice_id": voice_id,
                    "provider": "elevenlabs",
                    "audio_bytes": response.content,
                }

            except httpx.HTTPError as e:
                logger.error(f"ElevenLabs error for shot {shot_id}: {e}")
                raise

    async def get_available_voices(self) -> list[dict]:
        """Fetch all available voices from ElevenLabs."""
        if self.mock_mode:
            return [{"voice_id": k, "name": v} for k, v in DEFAULT_VOICES.items()]

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{ELEVENLABS_BASE}/voices",
                headers={"xi-api-key": self.api_key}
            )
            response.raise_for_status()
            return response.json().get("voices", [])

    def _emotion_to_style(self, emotion: str) -> float:
        """Map emotion to ElevenLabs style value (0-1)."""
        emotion_map = {
            "angry": 0.8, "tense": 0.7, "excited": 0.7,
            "sad": 0.3, "whisper": 0.1, "neutral": 0.5,
            "happy": 0.6, "fearful": 0.6, "dramatic": 0.8,
        }
        return emotion_map.get(emotion.lower(), 0.5)

    async def _mock_generate(self, text: str, voice_id: str, shot_id: str) -> dict:
        await asyncio.sleep(0.2)
        words = len(text.split())
        duration_estimate = words / 2.5  # ~2.5 words per second
        mock_id = os.urandom(4).hex()
        logger.info(f"[MOCK] ElevenLabs audio: shot={shot_id} words={words}")
        return {
            "shot_id": shot_id,
            "audio_url": f"https://mock-storage.cinegen.ai/audio/{shot_id}_{mock_id}.mp3",
            "duration_seconds": duration_estimate,
            "voice_id": voice_id,
            "provider": "elevenlabs_mock",
            "text_preview": text[:80] + "..." if len(text) > 80 else text,
        }

elevenlabs_client = ElevenLabsClient()
