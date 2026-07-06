"""
ElevenLabs Voice + Sound Design Integration — Production Grade
===============================================================
PRODUCER'S PHILOSOPHY:
Audio is 50% of film. A great score with mediocre visuals
still feels like a film. Mediocre audio with great visuals
feels like a rough cut. We treat audio as a first-class citizen.

TWO ROLES FOR ELEVENLABS IN CINEGEN AI:
1. CHARACTER VOICES — Each character gets one locked voice ID.
   That voice NEVER changes across the entire film.
   This is the audio equivalent of the Character Bible.

2. SOUND DESIGN — Ambient audio, tension stings, environmental
   sounds. For thriller/drama, this is more powerful than music.

VOICE SELECTION STRATEGY:
┌──────────────────────┬─────────────────┬────────────────────────────┐
│ Character Type       │ Voice Profile   │ ElevenLabs Voice ID        │
├──────────────────────┼─────────────────┼────────────────────────────┤
│ Male protagonist     │ Deep, measured  │ pNInz6obpgDQGcFmaJgB (Adam)│
│ Male antagonist      │ Cold, precise   │ yoZ06aMxZJJ28mfd3POQ (Sam) │
│ Female protagonist   │ Warm, strong    │ EXAVITQu4vr4xnSDxMaL (Bella)│
│ Female antagonist    │ Sharp, crisp    │ ThT5KcBeYPX3keUQqHPh (Dorothy)│
│ Narrator (male)      │ Authoritative   │ VR6AewLTigWG4xSOukaG (Arnold)│
│ Narrator (female)    │ Clear, warm     │ MF3mGyEYCl7XYWbV9V6O (Elli) │
│ Supporting (male)    │ Natural         │ TxGEqnHWrfWFTfGW9XjX (Josh) │
│ Supporting (female)  │ Conversational  │ jBpfuIE2acCO8z3wKNLl (Gigi) │
└──────────────────────┴─────────────────┴────────────────────────────┘
"""

import httpx
import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Optional
from core.config import settings

logger = logging.getLogger(__name__)

ELEVENLABS_BASE = "https://api.elevenlabs.io/v1"

# Locked voice library — these are stable production voices
VOICE_LIBRARY = {
    "male_deep":        "pNInz6obpgDQGcFmaJgB",  # Adam — deep, authoritative
    "male_cold":        "yoZ06aMxZJJ28mfd3POQ",  # Sam  — precise, measured
    "male_natural":     "TxGEqnHWrfWFTfGW9XjX",  # Josh — natural, versatile
    "female_warm":      "EXAVITQu4vr4xnSDxMaL",  # Bella — warm, strong
    "female_crisp":     "ThT5KcBeYPX3keUQqHPh",  # Dorothy — sharp, intelligent
    "female_natural":   "jBpfuIE2acCO8z3wKNLl",  # Gigi — conversational
    "narrator_male":    "VR6AewLTigWG4xSOukaG",  # Arnold — documentary authority
    "narrator_female":  "MF3mGyEYCl7XYWbV9V6O",  # Elli — clear, warm narrator
}

# Emotion → voice settings mapping (stability, similarity, style)
EMOTION_SETTINGS = {
    "neutral":      (0.50, 0.75, 0.00),
    "tense":        (0.35, 0.80, 0.60),
    "angry":        (0.25, 0.85, 0.80),
    "sad":          (0.60, 0.70, 0.30),
    "happy":        (0.45, 0.75, 0.50),
    "shocked":      (0.30, 0.80, 0.65),
    "determined":   (0.55, 0.80, 0.45),
    "calculating":  (0.70, 0.75, 0.20),
    "whisper":      (0.75, 0.65, 0.10),
    "dramatic":     (0.30, 0.85, 0.75),
    "contemplative":(0.65, 0.70, 0.15),
}

@dataclass
class AudioResult:
    """Structured result from an ElevenLabs generation."""
    shot_id: str
    audio_url: str
    duration_seconds: float
    voice_id: str
    character_name: str
    text: str
    emotion: str
    provider: str
    audio_bytes: Optional[bytes] = None
    error: Optional[str] = None


class ElevenLabsClient:
    """
    Production-grade ElevenLabs client for CineGen AI.
    Handles character voices, narration, and sound design.
    """

    def __init__(self):
        self.api_key = settings.ELEVENLABS_API_KEY
        self.mock_mode = not bool(self.api_key)
        if self.mock_mode:
            logger.warning("ELEVENLABS_API_KEY not set — running in mock mode")
        else:
            logger.info("ElevenLabs client initialised — LIVE mode")

    def _headers(self) -> dict:
        return {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }

    # ── Voice Assignment (Producer Logic) ─────────────────────────────────────

    def assign_voice(self, character: dict) -> str:
        """
        As a producer: assign the best voice to a character
        based on their profile in the Character Bible.
        Returns a locked voice ID.
        """
        # If character already has a voice assigned — respect it
        if character.get("voice_id") and character["voice_id"] in VOICE_LIBRARY.values():
            return character["voice_id"]

        role = (character.get("role") or "").lower()
        voice_style = (character.get("voice_style") or "").lower()
        description = (character.get("physical_description") or "").lower()
        personality = (character.get("personality") or "").lower()

        # Narrator characters
        if "narrator" in role:
            return VOICE_LIBRARY["narrator_male"]

        # Female characters
        is_female = any(word in description + voice_style for word in
                       ["female", "woman", "her ", "she ", "lady"])

        if is_female:
            if any(w in voice_style + personality for w in ["crisp", "sharp", "cold", "precise", "antagonist"]):
                return VOICE_LIBRARY["female_crisp"]
            elif any(w in voice_style + personality for w in ["warm", "soft", "kind", "protagonist"]):
                return VOICE_LIBRARY["female_warm"]
            return VOICE_LIBRARY["female_natural"]

        # Male characters (default)
        if any(w in voice_style + personality for w in ["deep", "baritone", "authoritative", "powerful"]):
            return VOICE_LIBRARY["male_deep"]
        elif any(w in voice_style + personality for w in ["cold", "precise", "calculated", "antagonist"]):
            return VOICE_LIBRARY["male_cold"]

        return VOICE_LIBRARY["male_natural"]

    def build_character_voice_map(self, character_bible: dict) -> dict[str, str]:
        """
        Build a locked voice map for all characters before generation.
        character_id → voice_id
        This is the audio equivalent of locking the Character Bible.
        """
        voice_map = {}
        for char_id, char in character_bible.items():
            voice_id = self.assign_voice(char)
            voice_map[char_id] = voice_id
            logger.info(f"Voice assigned: {char.get('name')} → {voice_id}")
        return voice_map

    # ── Dialogue Generation ────────────────────────────────────────────────────

    async def generate_dialogue(
        self,
        text: str,
        voice_id: str,
        character_name: str = "",
        shot_id: str = "",
        emotion: str = "neutral",
    ) -> AudioResult:
        """
        Generate voice audio for one line of dialogue.
        Uses emotion-matched voice settings for authentic delivery.
        """
        if not text or not text.strip():
            return AudioResult(
                shot_id=shot_id, audio_url="", duration_seconds=0,
                voice_id=voice_id, character_name=character_name,
                text=text, emotion=emotion, provider="elevenlabs",
                error="no_text"
            )

        if self.mock_mode:
            return await self._mock_dialogue(text, voice_id, character_name, shot_id, emotion)

        stability, similarity, style = EMOTION_SETTINGS.get(
            emotion.lower(), EMOTION_SETTINGS["neutral"]
        )

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{ELEVENLABS_BASE}/text-to-speech/{voice_id}?output_format=mp3_44100_128",
                    headers=self._headers(),
                    json={
                        "text": text,
                        "model_id": "eleven_multilingual_v2",
                        "voice_settings": {
                            "stability": stability,
                            "similarity_boost": similarity,
                            "style": style,
                            "use_speaker_boost": True,
                        }
                    }
                )
                response.raise_for_status()
                audio_bytes = response.content
                duration = self._estimate_duration(text)

                logger.info(
                    f"Dialogue generated: shot={shot_id} "
                    f"char={character_name} emotion={emotion} "
                    f"duration~{duration:.1f}s"
                )

                return AudioResult(
                    shot_id=shot_id,
                    audio_url=f"memory://{shot_id}_dialogue.mp3",
                    duration_seconds=duration,
                    voice_id=voice_id,
                    character_name=character_name,
                    text=text,
                    emotion=emotion,
                    provider="elevenlabs",
                    audio_bytes=audio_bytes,
                )

            except httpx.HTTPStatusError as e:
                logger.error(f"ElevenLabs HTTP error: {e.response.status_code}")
                raise

    # ── Sound Design ───────────────────────────────────────────────────────────

    async def generate_sound_effect(
        self,
        description: str,
        duration_seconds: float = 5.0,
        scene_id: str = "",
    ) -> AudioResult:
        """
        Generate ambient audio and sound effects.
        As a producer: this is what makes scenes feel real.
        The lab hum, the wind on the rooftop, the server sounds.
        """
        if self.mock_mode:
            return await self._mock_sfx(description, duration_seconds, scene_id)

        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{ELEVENLABS_BASE}/sound-generation",
                    headers={
                        "xi-api-key": self.api_key,
                        "Content-Type": "application/json",
                    },
                    json={
                        "text": description,
                        "duration_seconds": duration_seconds,
                        "prompt_influence": 0.3,
                    }
                )
                response.raise_for_status()
                audio_bytes = response.content

                logger.info(f"SFX generated: scene={scene_id} desc={description[:50]}")

                return AudioResult(
                    shot_id=scene_id,
                    audio_url=f"memory://{scene_id}_sfx.mp3",
                    duration_seconds=duration_seconds,
                    voice_id="sfx",
                    character_name="",
                    text=description,
                    emotion="ambient",
                    provider="elevenlabs_sfx",
                    audio_bytes=audio_bytes,
                )

            except Exception as e:
                logger.error(f"SFX generation failed: {e}")
                return await self._mock_sfx(description, duration_seconds, scene_id)

    def get_scene_sfx_description(self, scene: dict) -> str:
        """
        As a producer: generate the right ambient audio description
        based on scene location and emotion.
        """
        location = (scene.get("location_name") or "").lower()
        emotion = (scene.get("emotion") or "neutral").lower()

        sfx_map = {
            "lab":          "sterile laboratory ambient hum, computer fans, electrical equipment, subtle beeping monitors",
            "rooftop":      "urban rooftop wind, distant city traffic, occasional siren, air conditioning units",
            "office":       "office ambient, quiet keyboard typing, distant phone, air conditioning",
            "street":       "busy city street, traffic, footsteps, urban crowd murmur",
            "forest":       "forest ambience, birds, wind through trees, rustling leaves",
            "interior":     "quiet interior room tone, subtle air movement",
        }

        # Match location to SFX description
        for key, desc in sfx_map.items():
            if key in location:
                if emotion in ("tense", "shocked", "dramatic"):
                    desc += ", subtle low-frequency tension drone"
                return desc

        # Default
        return f"ambient room tone, {emotion} atmosphere, subtle background sounds"

    # ── Utility ────────────────────────────────────────────────────────────────

    def _estimate_duration(self, text: str) -> float:
        """Estimate audio duration from word count (2.5 words/second average)."""
        words = len(text.split())
        return max(1.0, words / 2.5)

    async def get_available_voices(self) -> list[dict]:
        """Fetch all available voices — useful for UI voice picker."""
        if self.mock_mode:
            return [{"voice_id": v, "name": k} for k, v in VOICE_LIBRARY.items()]

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                f"{ELEVENLABS_BASE}/voices",
                headers={"xi-api-key": self.api_key}
            )
            response.raise_for_status()
            return response.json().get("voices", [])

    # ── Mock Mode ──────────────────────────────────────────────────────────────

    async def _mock_dialogue(
        self, text: str, voice_id: str, character_name: str,
        shot_id: str, emotion: str
    ) -> AudioResult:
        await asyncio.sleep(0.15)
        duration = self._estimate_duration(text)
        mock_id = os.urandom(4).hex()
        logger.info(f"[MOCK] Dialogue: {character_name} ({emotion}) — {text[:40]}...")
        return AudioResult(
            shot_id=shot_id,
            audio_url=f"https://mock-storage.cinegen.ai/audio/{shot_id}_{mock_id}.mp3",
            duration_seconds=duration,
            voice_id=voice_id,
            character_name=character_name,
            text=text,
            emotion=emotion,
            provider="elevenlabs_mock",
        )

    async def _mock_sfx(
        self, description: str, duration: float, scene_id: str
    ) -> AudioResult:
        await asyncio.sleep(0.1)
        mock_id = os.urandom(4).hex()
        return AudioResult(
            shot_id=scene_id,
            audio_url=f"https://mock-storage.cinegen.ai/sfx/{scene_id}_{mock_id}.mp3",
            duration_seconds=duration,
            voice_id="sfx",
            character_name="",
            text=description,
            emotion="ambient",
            provider="elevenlabs_sfx_mock",
        )


elevenlabs_client = ElevenLabsClient()
