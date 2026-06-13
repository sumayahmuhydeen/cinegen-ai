"""
Script Intelligence Service
===========================
Converts raw script text into a fully structured production blueprint
using Claude as the LLM brain.

Every shot gets a stable Shot ID. All downstream services reference these IDs.
"""
import json
import logging
import re
from typing import Any
import anthropic
from core.config import settings

logger = logging.getLogger(__name__)

# ─── Strict JSON schema prompt ───────────────────────────────────────────────
SCRIPT_ANALYSIS_PROMPT = """You are a professional film production AI.
Analyse the script below and return ONLY a valid JSON object — no markdown, no explanation, no extra text.

The JSON must follow this exact schema:
{
  "title": "string — inferred film title",
  "genre": "string — Drama/Documentary/Sci-Fi/Thriller/Comedy/Horror/Action/Educational/Corporate",
  "total_duration_estimate": number in seconds,
  "emotional_arc": "string — one sentence describing the overall emotional journey",
  "characters": [
    {
      "character_id": "char_001",
      "name": "string",
      "role": "Protagonist|Antagonist|Supporting|Narrator",
      "age_range": "string e.g. 30-40",
      "physical_description": "string — detailed appearance for image generation",
      "personality": "string",
      "voice_style": "string — e.g. deep authoritative male, soft warm female",
      "wardrobe": "string — clothing description"
    }
  ],
  "locations": [
    {
      "location_id": "loc_001",
      "name": "string",
      "description": "string — detailed for image generation",
      "environment_type": "Interior|Exterior",
      "time_of_day": "Dawn|Morning|Afternoon|Evening|Night",
      "weather": "string",
      "lighting": "string — lighting description for consistency",
      "color_palette": "string — dominant colors"
    }
  ],
  "scenes": [
    {
      "scene_id": "scene_001",
      "scene_number": 1,
      "title": "string",
      "location_id": "loc_001",
      "duration_estimate": number in seconds,
      "emotion": "string — dominant emotion",
      "summary": "string — what happens in this scene",
      "shots": [
        {
          "shot_id": "shot_001_001",
          "shot_number": 1,
          "camera_direction": "Wide Shot|Medium Shot|Close-Up|Extreme Close-Up|Over-Shoulder|POV|Aerial|Tracking",
          "action_description": "string — exactly what happens in the frame",
          "characters_present": ["char_001"],
          "dialogue": "string or null — exact spoken words",
          "speaker_character_id": "char_001 or null",
          "emotion": "string",
          "duration_estimate": number in seconds,
          "visual_notes": "string — lighting, colour grading, mood notes for generation"
        }
      ]
    }
  ],
  "style_bible": {
    "cinematic_style": "Hollywood|Documentary|Indie|Anime|Corporate|Educational",
    "color_palette": "string — overall film color treatment",
    "camera_style": "Static|Dynamic|Handheld|Cinematic",
    "pacing": "Slow|Medium|Fast",
    "music_tone": "string — describe the music mood"
  }
}

Rules:
- shot_id format: shot_{scene_number:03d}_{shot_number:03d} e.g. shot_001_001
- scene_id format: scene_{number:03d}
- character_id format: char_{number:03d}
- location_id format: loc_{number:03d}
- Every shot must reference valid character_ids and location_ids defined above
- duration_estimate for shots: 5-15 seconds each
- Be thorough — extract every scene and shot implied by the script
- Do not invent scenes not in the script

SCRIPT TO ANALYSE:
"""

class ScriptIntelligenceService:
    """
    Converts a raw script into a structured production blueprint.
    Uses Claude claude-sonnet-4-6 for analysis.
    """

    def __init__(self):
        if settings.ANTHROPIC_API_KEY:
            self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        else:
            self.client = None
            logger.warning("No ANTHROPIC_API_KEY set — using mock blueprint")

    async def analyse_script(self, script_text: str, title: str = "") -> dict[str, Any]:
        """
        Main entry point: takes raw script text, returns structured blueprint.
        Falls back to mock data if no API key is set.
        """
        if not self.client:
            logger.info("Using mock blueprint (no API key)")
            return self._mock_blueprint(title or "Untitled Film")

        logger.info(f"Analysing script ({len(script_text)} chars)...")

        try:
            prompt = SCRIPT_ANALYSIS_PROMPT + script_text

            message = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=8000,
                messages=[{"role": "user", "content": prompt}]
            )

            raw = message.content[0].text.strip()

            # Strip markdown code fences if model wraps in them
            raw = re.sub(r'^```(?:json)?\s*', '', raw)
            raw = re.sub(r'\s*```$', '', raw)

            blueprint = json.loads(raw)
            blueprint = self._validate_and_enrich(blueprint, title)

            logger.info(f"Blueprint created: {len(blueprint.get('scenes', []))} scenes, "
                       f"{len(blueprint.get('characters', []))} characters")
            return blueprint

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            raise ValueError(f"Script analysis returned invalid JSON: {e}")
        except Exception as e:
            logger.error(f"Script analysis failed: {e}")
            raise

    def _validate_and_enrich(self, blueprint: dict, title: str) -> dict:
        """Validate IDs, add totals, fill missing fields."""

        # Override title if provided
        if title:
            blueprint["title"] = title

        # Count totals
        total_shots = sum(len(s.get("shots", [])) for s in blueprint.get("scenes", []))
        blueprint["total_shots"] = total_shots
        blueprint["total_scenes"] = len(blueprint.get("scenes", []))

        # Build lookup sets for validation
        valid_char_ids = {c["character_id"] for c in blueprint.get("characters", [])}
        valid_loc_ids = {l["location_id"] for l in blueprint.get("locations", [])}

        # Validate and fix shot references
        for scene in blueprint.get("scenes", []):
            if scene.get("location_id") not in valid_loc_ids and blueprint.get("locations"):
                scene["location_id"] = blueprint["locations"][0]["location_id"]

            for shot in scene.get("shots", []):
                # Remove invalid character references
                shot["characters_present"] = [
                    c for c in shot.get("characters_present", [])
                    if c in valid_char_ids
                ]
                if shot.get("speaker_character_id") not in valid_char_ids:
                    shot["speaker_character_id"] = None

                # Ensure duration
                if not shot.get("duration_estimate"):
                    shot["duration_estimate"] = 8

        return blueprint

    def generate_character_prompt(self, character: dict) -> str:
        """
        Converts a character dict into an optimised image generation prompt.
        Used by the Character Bible to lock visual identity.
        """
        return (
            f"Portrait of {character.get('name', 'a person')}, "
            f"{character.get('age_range', 'adult')}, "
            f"{character.get('physical_description', '')}, "
            f"wearing {character.get('wardrobe', 'casual clothing')}, "
            f"professional film still, cinematic lighting, photorealistic, "
            f"sharp focus, neutral background"
        )

    def generate_location_prompt(self, location: dict) -> str:
        """
        Converts a location dict into an optimised image generation prompt.
        Used by the Location Bible to lock visual identity.
        """
        return (
            f"{location.get('name', 'a location')}, "
            f"{location.get('description', '')}, "
            f"{location.get('environment_type', 'exterior')}, "
            f"{location.get('time_of_day', 'day')}, "
            f"{location.get('lighting', 'natural lighting')}, "
            f"cinematic establishing shot, photorealistic, "
            f"color palette: {location.get('color_palette', 'natural')}"
        )

    def generate_shot_prompt(
        self,
        shot: dict,
        character_descriptions: dict[str, str],
        location_description: str
    ) -> str:
        """
        Assembles a fully constrained video generation prompt for a single shot.
        Injects character descriptions and location from the Bible system.
        This is what gets sent to Kling/Runway.
        """
        chars = []
        for char_id in shot.get("characters_present", []):
            if char_id in character_descriptions:
                chars.append(character_descriptions[char_id])

        char_text = ", ".join(chars) if chars else "empty scene"
        camera = shot.get("camera_direction", "Medium Shot")
        action = shot.get("action_description", "")
        emotion = shot.get("emotion", "neutral")
        notes = shot.get("visual_notes", "")

        prompt = (
            f"{camera}: {action}. "
            f"Characters: {char_text}. "
            f"Location: {location_description}. "
            f"Emotion: {emotion}. "
            f"{notes}. "
            f"Cinematic quality, photorealistic, professional film production."
        )

        return prompt

    def _mock_blueprint(self, title: str) -> dict:
        """
        Returns a realistic mock blueprint for development/testing
        when no Anthropic API key is configured.
        """
        return {
            "title": title,
            "genre": "Drama",
            "total_duration_estimate": 600,
            "total_scenes": 3,
            "total_shots": 9,
            "emotional_arc": "A journey from doubt to conviction through unexpected discovery.",
            "characters": [
                {
                    "character_id": "char_001",
                    "name": "Marcus Cole",
                    "role": "Protagonist",
                    "age_range": "35-42",
                    "physical_description": "tall athletic build, short dark hair with grey temples, strong jawline, brown eyes",
                    "personality": "determined, thoughtful, carries hidden grief",
                    "voice_style": "deep measured baritone, mid-Atlantic accent",
                    "wardrobe": "charcoal grey suit, open collar white shirt, no tie"
                },
                {
                    "character_id": "char_002",
                    "name": "Dr Elena Voss",
                    "role": "Antagonist",
                    "age_range": "40-48",
                    "physical_description": "sharp cheekbones, platinum blonde hair in a precise bob, ice blue eyes, slim",
                    "personality": "brilliant, ruthless, believes the ends justify the means",
                    "voice_style": "crisp precise alto with slight Eastern European inflection",
                    "wardrobe": "tailored black blazer, white blouse, minimal silver jewellery"
                }
            ],
            "locations": [
                {
                    "location_id": "loc_001",
                    "name": "City Rooftop",
                    "description": "high-rise rooftop at dawn, skyline in the background, industrial air vents, concrete",
                    "environment_type": "Exterior",
                    "time_of_day": "Dawn",
                    "weather": "Clear with light mist",
                    "lighting": "golden hour light from the east, long shadows",
                    "color_palette": "warm amber, steel blue, concrete grey"
                },
                {
                    "location_id": "loc_002",
                    "name": "Underground Lab",
                    "description": "sterile white walls, banks of monitors, clinical lighting, high-tech equipment",
                    "environment_type": "Interior",
                    "time_of_day": "Night",
                    "weather": "N/A",
                    "lighting": "cold fluorescent overhead with blue screen glow",
                    "color_palette": "stark white, electric blue, black"
                }
            ],
            "scenes": [
                {
                    "scene_id": "scene_001",
                    "scene_number": 1,
                    "title": "The Confrontation",
                    "location_id": "loc_001",
                    "duration_estimate": 90,
                    "emotion": "Tense",
                    "summary": "Marcus confronts Elena on the rooftop at dawn.",
                    "shots": [
                        {
                            "shot_id": "shot_001_001",
                            "shot_number": 1,
                            "camera_direction": "Wide Shot",
                            "action_description": "Establishing shot of the rooftop. Marcus stands at the edge looking out at the city.",
                            "characters_present": ["char_001"],
                            "dialogue": None,
                            "speaker_character_id": None,
                            "emotion": "Contemplative",
                            "duration_estimate": 8,
                            "visual_notes": "Golden hour light, silhouette against the skyline"
                        },
                        {
                            "shot_id": "shot_001_002",
                            "shot_number": 2,
                            "camera_direction": "Medium Shot",
                            "action_description": "Elena steps out of the rooftop door, her expression unreadable.",
                            "characters_present": ["char_002"],
                            "dialogue": "You came.",
                            "speaker_character_id": "char_002",
                            "emotion": "Calculating",
                            "duration_estimate": 6,
                            "visual_notes": "Backlit by the door light, cool tones"
                        },
                        {
                            "shot_id": "shot_001_003",
                            "shot_number": 3,
                            "camera_direction": "Over-Shoulder",
                            "action_description": "Marcus turns to face Elena. Tension between them.",
                            "characters_present": ["char_001", "char_002"],
                            "dialogue": "You left me no choice.",
                            "speaker_character_id": "char_001",
                            "emotion": "Determined",
                            "duration_estimate": 7,
                            "visual_notes": "Warm vs cool colour contrast between the two characters"
                        }
                    ]
                },
                {
                    "scene_id": "scene_002",
                    "scene_number": 2,
                    "title": "The Discovery",
                    "location_id": "loc_002",
                    "duration_estimate": 120,
                    "emotion": "Shocking",
                    "summary": "Marcus breaks into the underground lab and finds the truth.",
                    "shots": [
                        {
                            "shot_id": "shot_002_001",
                            "shot_number": 1,
                            "camera_direction": "POV",
                            "action_description": "Marcus's POV moving through the darkened lab corridor.",
                            "characters_present": ["char_001"],
                            "dialogue": None,
                            "speaker_character_id": None,
                            "emotion": "Tense",
                            "duration_estimate": 10,
                            "visual_notes": "Handheld feel, blue monitor glow as only light source"
                        },
                        {
                            "shot_id": "shot_002_002",
                            "shot_number": 2,
                            "camera_direction": "Close-Up",
                            "action_description": "Marcus's face lit by the monitor screen. Eyes widening as he reads.",
                            "characters_present": ["char_001"],
                            "dialogue": None,
                            "speaker_character_id": None,
                            "emotion": "Shocked",
                            "duration_estimate": 6,
                            "visual_notes": "Blue screen light on face, deep shadows"
                        },
                        {
                            "shot_id": "shot_002_003",
                            "shot_number": 3,
                            "camera_direction": "Extreme Close-Up",
                            "action_description": "Monitor screen showing classified documents.",
                            "characters_present": [],
                            "dialogue": None,
                            "speaker_character_id": None,
                            "emotion": "Revelatory",
                            "duration_estimate": 5,
                            "visual_notes": "Sharp focus on screen text, rack focus effect"
                        }
                    ]
                },
                {
                    "scene_id": "scene_003",
                    "scene_number": 3,
                    "title": "The Decision",
                    "location_id": "loc_001",
                    "duration_estimate": 90,
                    "emotion": "Resolute",
                    "summary": "Marcus returns to the rooftop and makes his decision.",
                    "shots": [
                        {
                            "shot_id": "shot_003_001",
                            "shot_number": 1,
                            "camera_direction": "Wide Shot",
                            "action_description": "Marcus stands at the rooftop edge. The city stretches before him.",
                            "characters_present": ["char_001"],
                            "dialogue": None,
                            "speaker_character_id": None,
                            "emotion": "Resolute",
                            "duration_estimate": 8,
                            "visual_notes": "Full sunrise now, warm golden light, triumphant feel"
                        },
                        {
                            "shot_id": "shot_003_002",
                            "shot_number": 2,
                            "camera_direction": "Close-Up",
                            "action_description": "Marcus pulls out his phone and dials.",
                            "characters_present": ["char_001"],
                            "dialogue": "It's time.",
                            "speaker_character_id": "char_001",
                            "emotion": "Determined",
                            "duration_estimate": 6,
                            "visual_notes": "Phone screen glow mixed with warm sunlight"
                        },
                        {
                            "shot_id": "shot_003_003",
                            "shot_number": 3,
                            "camera_direction": "Aerial",
                            "action_description": "Aerial pullback from Marcus on the rooftop, revealing the vast city.",
                            "characters_present": ["char_001"],
                            "dialogue": None,
                            "speaker_character_id": None,
                            "emotion": "Epic",
                            "duration_estimate": 10,
                            "visual_notes": "Drone shot, camera rises and pulls back, golden light"
                        }
                    ]
                }
            ],
            "style_bible": {
                "cinematic_style": "Hollywood",
                "color_palette": "High contrast warm vs cool, teal and orange grade",
                "camera_style": "Cinematic",
                "pacing": "Medium",
                "music_tone": "Orchestral tension building to triumphant resolution"
            }
        }

script_intelligence_service = ScriptIntelligenceService()
