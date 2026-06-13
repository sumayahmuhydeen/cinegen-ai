# CineGen AI — Python Backend

## Phase 2: Script Intelligence Layer

### Quick Start

```bash
cd backend

# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create your .env file
copy .env.example .env       # Windows
cp .env.example .env         # Mac/Linux
# Edit .env and add your ANTHROPIC_API_KEY

# 4. Run the server
python run.py
```

### Server runs at
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health/

### Key Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | /api/v1/projects/ | Create project |
| GET | /api/v1/projects/ | List projects |
| POST | /api/v1/projects/{id}/script | **Analyse script — main Phase 2 endpoint** |
| GET | /api/v1/projects/{id}/blueprint | Get production blueprint |
| GET | /api/v1/projects/{id}/bibles | Get Character/Location/Style bibles |
| PUT | /api/v1/characters/{id}/approve | Approve character |
| GET | /api/v1/shots/project/{id}/continuity | Continuity report |

### Without an API Key
Works in **mock mode** — returns a realistic pre-built blueprint.
Add `ANTHROPIC_API_KEY=your-key` to `.env` to enable real script analysis.

### Services Built (Phase 2)
- `ScriptIntelligenceService` — LLM-powered script parsing
- `BibleSystem` — Character, Location, Style bible creation
- `ContinuityEngine` — Shot validation and drift detection
