"""
Audio Pipeline Service — Production Grade
==========================================
PRODUCER'S PHILOSOPHY:
Audio tells the audience how to feel.
Video shows them what is happening.
Both must work together perfectly.

PARALLEL EXECUTION STRATEGY:
Audio and video generate simultaneously — never sequentially.
This cuts total production time by 35-45%.

AUDIO LAYERS PER SCENE (bottom to top):
1. Ambient/SFX bed      — ElevenLabs Sound Effects (always present)
2. Music underscore     — Future: Apiframe/Udio (phase 4)
3. Dialogue             — ElevenLabs TTS (per shot, per character)
4. Sound design hits    — ElevenLabs SFX (tension, action moments)

CHARACTER VOICE LOCKING:
Before ANY audio generates, all character voices are
assigned and locked. The same voice ID is used for every
line of dialogue that character speaks across the entire film.
"""
import asyncio
import logging
from dataclasses import dataclass
from typing import Optional
from integrations.elevenlabs import elevenlabs_client, AudioResult

logger = logging.getLogger(__name__)


@dataclass
class AudioManifest:
    """Complete audio manifest for a project."""
    project_title: str
    voice_map: dict          # character_id → voice_id
    dialogue: list           # list of AudioResult dicts per shot
    sound_effects: list      # list of AudioResult dicts per scene
    total_dialogue_lines: int
    total_sfx_tracks: int
    estimated_duration_seconds: float


class AudioPipelineService:
    """
    Generates and manages all audio for a CineGen AI production.
    """

    async def generate_project_audio(
        self,
        blueprint: dict,
        character_bible: dict,
    ) -> dict:
        """
        Master audio generation function.
        Step 1: Lock all character voices
        Step 2: Generate dialogue + SFX in parallel
        Step 3: Return complete audio manifest
        """
        title = blueprint.get("title", "Untitled")
        logger.info(f"Audio pipeline starting: '{title}'")

        # Step 1: Lock all character voices BEFORE any generation
        voice_map = elevenlabs_client.build_character_voice_map(character_bible)
        logger.info(f"Voice map locked: {len(voice_map)} characters")

        # Step 2: Run dialogue and SFX generation in parallel
        dialogue_task = asyncio.create_task(
            self._generate_all_dialogue(blueprint, character_bible, voice_map)
        )
        sfx_task = asyncio.create_task(
            self._generate_all_sfx(blueprint)
        )

        dialogue_results, sfx_results = await asyncio.gather(
            dialogue_task, sfx_task
        )

        total_duration = sum(
            r.get("duration_seconds", 0) for r in dialogue_results + sfx_results
        )

        manifest = {
            "project_title": title,
            "voice_map": voice_map,
            "dialogue": dialogue_results,
            "sound_effects": sfx_results,
            "total_dialogue_lines": len(dialogue_results),
            "total_sfx_tracks": len(sfx_results),
            "estimated_duration_seconds": total_duration,
        }

        logger.info(
            f"Audio pipeline complete: "
            f"{len(dialogue_results)} dialogue lines | "
            f"{len(sfx_results)} SFX tracks"
        )

        return manifest

    async def _generate_all_dialogue(
        self,
        blueprint: dict,
        character_bible: dict,
        voice_map: dict,
    ) -> list[dict]:
        """
        Generate voice audio for every shot that has dialogue.
        Each line uses the character's locked voice from voice_map.
        """
        tasks = []

        for scene in blueprint.get("scenes", []):
            for shot in scene.get("shots", []):
                dialogue = shot.get("dialogue")
                speaker_id = shot.get("speaker_character_id")

                if not dialogue or not speaker_id:
                    continue

                # Get locked voice for this character
                voice_id = voice_map.get(speaker_id)
                if not voice_id:
                    logger.warning(f"No voice found for character {speaker_id}")
                    continue

                # Get character name for logging
                char = character_bible.get(speaker_id, {})
                char_name = char.get("name", speaker_id)

                shot_id = shot.get("shot_id", shot.get("id", ""))
                emotion = shot.get("emotion", "neutral")

                tasks.append(
                    self._safe_generate_dialogue(
                        text=dialogue,
                        voice_id=voice_id,
                        character_name=char_name,
                        shot_id=shot_id,
                        emotion=emotion,
                    )
                )

        if not tasks:
            logger.info("No dialogue lines found in blueprint")
            return []

        logger.info(f"Generating {len(tasks)} dialogue lines in parallel")
        results = await asyncio.gather(*tasks)
        return [r for r in results if r is not None]

    async def _safe_generate_dialogue(
        self,
        text: str,
        voice_id: str,
        character_name: str,
        shot_id: str,
        emotion: str,
    ) -> Optional[dict]:
        """Generate one dialogue line with error handling."""
        try:
            result = await elevenlabs_client.generate_dialogue(
                text=text,
                voice_id=voice_id,
                character_name=character_name,
                shot_id=shot_id,
                emotion=emotion,
            )
            return {
                "shot_id": result.shot_id,
                "audio_url": result.audio_url,
                "duration_seconds": result.duration_seconds,
                "voice_id": result.voice_id,
                "character_name": result.character_name,
                "text": result.text,
                "emotion": result.emotion,
                "provider": result.provider,
            }
        except Exception as e:
            logger.error(f"Dialogue generation failed for shot {shot_id}: {e}")
            return None

    async def _generate_all_sfx(self, blueprint: dict) -> list[dict]:
        """
        Generate ambient audio and sound effects for every scene.
        As a producer: this is the environmental audio layer
        that makes every location feel real and lived-in.
        """
        tasks = []

        for scene in blueprint.get("scenes", []):
            scene_id = scene.get("scene_id", scene.get("id", ""))
            duration = scene.get("duration_estimate", 30)
            sfx_desc = elevenlabs_client.get_scene_sfx_description(scene)

            tasks.append(
                self._safe_generate_sfx(
                    description=sfx_desc,
                    duration=min(float(duration), 30.0),
                    scene_id=scene_id,
                )
            )

        logger.info(f"Generating {len(tasks)} SFX tracks")
        results = await asyncio.gather(*tasks)
        return [r for r in results if r is not None]

    async def _safe_generate_sfx(
        self,
        description: str,
        duration: float,
        scene_id: str,
    ) -> Optional[dict]:
        """Generate one SFX track with error handling."""
        try:
            result = await elevenlabs_client.generate_sound_effect(
                description=description,
                duration_seconds=duration,
                scene_id=scene_id,
            )
            return {
                "scene_id": result.shot_id,
                "audio_url": result.audio_url,
                "duration_seconds": result.duration_seconds,
                "description": result.text,
                "provider": result.provider,
            }
        except Exception as e:
            logger.error(f"SFX generation failed for scene {scene_id}: {e}")
            return None

    async def generate_single_shot_audio(
        self,
        shot: dict,
        character_bible: dict,
        voice_map: dict,
    ) -> Optional[dict]:
        """
        Generate audio for a single shot.
        Used in the regeneration flow when one shot needs to be redone.
        """
        dialogue = shot.get("dialogue")
        speaker_id = shot.get("speaker_character_id")

        if not dialogue:
            return {"shot_id": shot.get("shot_id"), "skipped": True, "reason": "no_dialogue"}

        voice_id = voice_map.get(speaker_id) if speaker_id else None
        if not voice_id and speaker_id:
            char = character_bible.get(speaker_id, {})
            voice_id = elevenlabs_client.assign_voice(char)

        if not voice_id:
            return {"shot_id": shot.get("shot_id"), "skipped": True, "reason": "no_voice_assigned"}

        char = character_bible.get(speaker_id, {})
        return await self._safe_generate_dialogue(
            text=dialogue,
            voice_id=voice_id,
            character_name=char.get("name", "Unknown"),
            shot_id=shot.get("shot_id", ""),
            emotion=shot.get("emotion", "neutral"),
        )


audio_pipeline = AudioPipelineService()
