"""
Bible System
============
Manages the three locked reference documents that govern visual consistency:
  - Character Bible  (appearance, voice, face embedding)
  - Location Bible   (environment, lighting, props)
  - Style Bible      (colour palette, cinematic style, pacing)

These bibles are created from the blueprint and APPROVED by the user
before a single frame is generated.
"""
import logging
from typing import Any
from services.script_intelligence import script_intelligence_service

logger = logging.getLogger(__name__)

class BibleSystem:

    def create_character_bible(self, blueprint: dict[str, Any]) -> dict[str, Any]:
        """
        Build the Character Bible from blueprint.
        Each entry includes a locked image generation prompt
        that will be used for every shot containing that character.
        """
        bible = {}
        for char in blueprint.get("characters", []):
            char_id = char["character_id"]
            prompt = script_intelligence_service.generate_character_prompt(char)
            bible[char_id] = {
                **char,
                "locked_prompt": prompt,
                "approved": False,
                "reference_images": [],
                "face_embedding": None,
            }
            logger.debug(f"Character Bible entry created: {char['name']}")
        return bible

    def create_location_bible(self, blueprint: dict[str, Any]) -> dict[str, Any]:
        """
        Build the Location Bible from blueprint.
        Each entry includes a locked image generation prompt
        for environmental consistency across all shots.
        """
        bible = {}
        for loc in blueprint.get("locations", []):
            loc_id = loc["location_id"]
            prompt = script_intelligence_service.generate_location_prompt(loc)
            bible[loc_id] = {
                **loc,
                "locked_prompt": prompt,
                "approved": False,
                "reference_images": [],
            }
            logger.debug(f"Location Bible entry created: {loc['name']}")
        return bible

    def create_style_bible(self, blueprint: dict[str, Any]) -> dict[str, Any]:
        """
        Build the Style Bible from blueprint.
        Controls the overall cinematic look applied to every shot.
        """
        style = blueprint.get("style_bible", {})
        return {
            "cinematic_style": style.get("cinematic_style", "Cinematic"),
            "color_palette": style.get("color_palette", "Natural, balanced tones"),
            "camera_style": style.get("camera_style", "Cinematic"),
            "pacing": style.get("pacing", "Medium"),
            "music_tone": style.get("music_tone", "Dramatic orchestral"),
            "approved": False,
            "global_prompt_suffix": (
                f"{style.get('cinematic_style', 'cinematic')} style, "
                f"{style.get('color_palette', 'natural color grading')}, "
                f"professional film production, photorealistic"
            )
        }

    def build_shot_prompt(
        self,
        shot: dict,
        character_bible: dict,
        location_bible: dict,
        style_bible: dict,
        scene_location_id: str
    ) -> str:
        """
        Assembles the fully constrained video generation prompt for a shot.
        This is the single most important function in the pipeline —
        it injects locked Bible constraints into every generation call.
        """
        # Get locked character descriptions
        char_descriptions = {}
        for char_id in shot.get("characters_present", []):
            if char_id in character_bible:
                char = character_bible[char_id]
                char_descriptions[char_id] = char.get("locked_prompt", char.get("name", ""))

        # Get locked location description
        location_desc = ""
        if scene_location_id in location_bible:
            location_desc = location_bible[scene_location_id].get("locked_prompt", "")

        # Assemble base prompt
        base_prompt = script_intelligence_service.generate_shot_prompt(
            shot, char_descriptions, location_desc
        )

        # Append style suffix
        style_suffix = style_bible.get("global_prompt_suffix", "")
        return f"{base_prompt} {style_suffix}".strip()

    def check_approval_status(
        self,
        character_bible: dict,
        location_bible: dict
    ) -> dict[str, Any]:
        """
        Returns approval status summary.
        Generation cannot start until all bibles are approved.
        """
        chars_approved = all(c.get("approved") for c in character_bible.values())
        locs_approved = all(l.get("approved") for l in location_bible.values())

        unapproved_chars = [
            c["name"] for c in character_bible.values() if not c.get("approved")
        ]
        unapproved_locs = [
            l["name"] for l in location_bible.values() if not l.get("approved")
        ]

        return {
            "ready_for_generation": chars_approved and locs_approved,
            "characters_approved": chars_approved,
            "locations_approved": locs_approved,
            "unapproved_characters": unapproved_chars,
            "unapproved_locations": unapproved_locs,
        }

bible_system = BibleSystem()
