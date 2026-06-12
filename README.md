# CineGen AI 🎬

> AI-Powered Long-Form Video Creation Platform

Transform written scripts into complete long-form videos (5–40 minutes) through a coordinated, consistency-first production pipeline.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS, shadcn/ui |
| Auth & DB | Supabase (PostgreSQL + pgvector) |
| Backend (Phase 2) | Python FastAPI |
| Workflows | Temporal.io |
| Video AI | Kling 1.6, Runway Gen-3 |
| Voice | ElevenLabs |
| Music | Suno API |
| Lip Sync | Sync.so |
| Storage | Cloudflare R2 |
| GPU Compute | RunPod / Modal |

---

## Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/sumayahmuhydeen/cinegen-ai.git
cd cinegen-ai
```

### 2. Set up the frontend
```bash
cd frontend
npm install
cp .env.example .env.local
# Fill in your Supabase credentials in .env.local
npm run dev
```

### 3. Set up Supabase
- Create a project at [supabase.com](https://supabase.com)
- Run `supabase/schema.sql` in your Supabase SQL editor
- Copy your Project URL and anon key to `.env.local`

### 4. Open the app
```
http://localhost:3000
```

---

## Project Structure

```
cinegen-ai/
├── frontend/          Next.js 14 app (Phase 1 — complete)
│   ├── app/           Pages and layouts
│   ├── components/    UI components
│   ├── lib/           Supabase client, utilities
│   ├── types/         TypeScript interfaces
│   └── supabase/      Database schema
├── backend/           Python FastAPI (Phase 2 — coming)
├── workflows/         Temporal workflows (Phase 4 — coming)
├── infrastructure/    Docker, CI/CD (Phase 3 — coming)
└── docs/              Architecture documentation
```

---

## Build Phases

| Phase | Focus | Status |
|-------|-------|--------|
| 1 | SaaS Frontend + Supabase | ✅ Complete |
| 2 | Python Backend + Script Intelligence | 🔜 Next |
| 3 | Video + Audio AI Pipeline | 📋 Planned |
| 4 | Continuity Engine + Temporal | 📋 Planned |
| 5 | Scale to 30–40 min | 📋 Planned |

---

## Environment Variables

Copy `.env.example` to `.env.local` and fill in:

```
NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

---

Built with ❤️ by the CineGen AI team.
