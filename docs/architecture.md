# CineGen AI — Architecture Overview

## The 5-Layer Pipeline

1. **Script Intelligence** — LLM converts script to structured production blueprint with Shot IDs
2. **Bible System** — Character, Location, and Style bibles locked before generation starts
3. **Shot Generation** — Each shot generated with constrained prompts + reference images + face validation
4. **Audio Pipeline** — Voice, music, SFX generated in parallel with video
5. **Assembly** — ffmpeg stitches clips + audio into final MP4

## Key Design Decisions

- Every shot has a stable Shot ID — all downstream services reference this
- Character Bible locks face embedding before any frame generates
- Continuity engine validates every clip BEFORE it enters the assembly pipeline
- Temporal durable workflows mean a 200-step pipeline resumes from failure point, not from start
- Model-agnostic interfaces — swap Kling for Runway without touching the pipeline
