# CineGen AI — Python Backend

## Phase 3: Production-Grade Generation Pipeline

Built with the philosophy of a professional film producer:
every shot is a deliberate creative decision, not just an API call.

---

## Architecture Philosophy

### As a Producer
- Every shot gets the RIGHT model — not the most expensive one
- Character voices are LOCKED before a single line generates
- Audio runs PARALLEL to video — never after
- Continuity is checked BEFORE generation — not discovered after

### As a Developer
- Model-agnostic interfaces — swap Kling for Runway in one line
- JWT auth with token caching — no wasted API calls
- Exponential backoff retry — 3 attempts before declaring failure
- Cost tracking per shot — users always know what they're spending

---

## Quick Start (Windows — Python 3.14)

```bash
cd backend
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip

pip install fastapi==0.115.0
pip install uvicorn==0.30.6
pip install sqlalchemy==2.0.36
pip install pydantic==2.9.2
pip install pydantic-settings==2.5.2
pip install python-multipart==0.0.12
pip install httpx==0.27.2
pip install anthropic==0.40.0
pip install python-dotenv==1.0.1
pip install python-jose==3.3.0
pip install passlib==1.7.4
pip install bcrypt==4.2.0
pip install PyJWT==2.9.0

python run.py
```

## URLs
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health/

---

## Kling 3.0 — Tiered Model Selection

| Shot Type | Model | Cost/sec | Why |
|-----------|-------|----------|-----|
| Wide / Aerial / Establishing | kling-v1-6 | $0.04 | Location context, b-roll |
| Medium / Action / Reaction | kling-v2-6-pro | $0.07 | Movement quality |
| Close-Up / Dialogue / Character | kling-v3 | $0.084 | Face and emotion quality |

Cost for The Last Algorithm (9 shots, 8s avg): ~$4-5 single pass, ~$12-15 realistic

---

## ElevenLabs — Voice Architecture

| Character Type | Voice | Profile |
|---------------|-------|---------|
| Male protagonist | Adam | Deep, measured baritone |
| Male antagonist | Sam | Cold, precise |
| Female protagonist | Bella | Warm, strong |
| Female antagonist | Dorothy | Sharp, crisp |
| Narrator (male) | Arnold | Authoritative |
| Narrator (female) | Elli | Clear, warm |

---

## API Endpoints

### Phase 2 — Script Intelligence
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | /api/v1/projects/ | Create project |
| POST | /api/v1/projects/{id}/script | Analyse script → blueprint |
| GET | /api/v1/projects/{id}/blueprint | Get production blueprint |
| GET | /api/v1/projects/{id}/bibles | Get Character/Location/Style bibles |

### Phase 3 — Generation Pipeline
| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | /api/v1/generation/{id}/start | Start full pipeline |
| GET | /api/v1/generation/{id}/status | Live progress |
| POST | /api/v1/generation/{id}/shot/{shot_id} | Generate single shot |
| POST | /api/v1/generation/{id}/audio | Generate all audio |
| POST | /api/v1/generation/{id}/assemble | Assemble final MP4 |
| GET | /api/v1/generation/{id}/export | Download link |

---

## .env Configuration

```
ANTHROPIC_API_KEY=sk-ant-...      # Script Intelligence (live)
KLING_API_KEY=access_id:secret    # Video generation (live)
ELEVENLABS_API_KEY=...            # Voice + SFX (live)
```

Without keys — full mock pipeline runs with placeholder URLs.

---

## Test Results (Phase 3)
- 7/7 generation endpoints passing
- Single shot: model=kling-v1-6, cost=$0.32 (8s Wide Shot)
- Audio: 3 dialogue lines + 3 SFX tracks generated in parallel
- Assembly: 9 clips, 66s total duration
- Pipeline: 100% progress, status=completed
