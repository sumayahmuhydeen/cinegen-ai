# CineGen AI — Python Backend

## Phase 3: Video Generation Pipeline

### Quick Start (Windows)

```bash
cd backend
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip

# Install one by one (Python 3.14 compatible)
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

python run.py
```

### URLs
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health/

### Phase 3 Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | /api/v1/generation/{id}/start | Start full pipeline |
| GET | /api/v1/generation/{id}/status | Live progress |
| POST | /api/v1/generation/{id}/shot/{shot_id} | Generate single shot |
| POST | /api/v1/generation/{id}/audio | Generate all audio |
| POST | /api/v1/generation/{id}/assemble | Assemble final MP4 |
| GET | /api/v1/generation/{id}/export | Get download link |

### Enable Real AI Generation
Add these to `backend/.env`:
```
ANTHROPIC_API_KEY=your-key        # Script Intelligence (live)
KLING_API_KEY=your-key            # Video generation (live)
RUNWAY_API_KEY=your-key           # Video fallback (live)
ELEVENLABS_API_KEY=your-key       # Voice generation (live)
SUNO_API_KEY=your-key             # Music generation (live)
```
Without keys = mock mode (full pipeline still runs with placeholder URLs).

### Services Built
- Phase 2: ScriptIntelligenceService, BibleSystem, ContinuityEngine
- Phase 3: ShotGeneratorService, AudioPipelineService, AssemblyService
- Integrations: Kling, Runway, ElevenLabs, Suno, Cloudflare R2
