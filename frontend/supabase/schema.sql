-- ============================================================
-- CineGen AI — Supabase Database Schema
-- Run this in your Supabase SQL editor
-- ============================================================

-- Enable pgvector for character/location embeddings
create extension if not exists vector;

-- ============================================================
-- USERS (extends Supabase auth.users)
-- ============================================================
create table public.profiles (
  id uuid references auth.users(id) on delete cascade primary key,
  full_name text,
  avatar_url text,
  subscription_tier text not null default 'starter' check (subscription_tier in ('starter','pro','studio')),
  credits_used integer not null default 0,
  credits_limit integer not null default 500,
  stripe_customer_id text,
  stripe_subscription_id text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Auto-create profile on signup
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, full_name, avatar_url)
  values (new.id, new.raw_user_meta_data->>'full_name', new.raw_user_meta_data->>'avatar_url');
  return new;
end;
$$ language plpgsql security definer;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- ============================================================
-- PROJECTS
-- ============================================================
create table public.projects (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.profiles(id) on delete cascade not null,
  title text not null,
  status text not null default 'draft' check (status in ('draft','analyzing','storyboard','characters','generating','review','completed','failed')),
  style text,
  script_text text,
  blueprint jsonb,
  scene_count integer default 0,
  character_count integer default 0,
  duration_estimate integer,
  thumbnail_url text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- ============================================================
-- CHARACTERS
-- ============================================================
create table public.characters (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references public.projects(id) on delete cascade not null,
  name text not null,
  role text,
  description text,
  appearance text,
  age_range text,
  voice_id text,
  approved boolean default false,
  reference_image_url text,
  face_embedding vector(512),
  prompt_description text,
  created_at timestamptz default now()
);

-- ============================================================
-- LOCATIONS
-- ============================================================
create table public.locations (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references public.projects(id) on delete cascade not null,
  name text not null,
  description text,
  environment_type text,
  time_of_day text,
  weather text,
  lighting_notes text,
  approved boolean default false,
  reference_image_url text,
  prompt_description text,
  scene_embedding vector(512),
  created_at timestamptz default now()
);

-- ============================================================
-- SCENES
-- ============================================================
create table public.scenes (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references public.projects(id) on delete cascade not null,
  scene_number integer not null,
  title text,
  location_id uuid references public.locations(id),
  emotion text,
  summary text,
  duration_estimate integer,
  approved boolean default false,
  created_at timestamptz default now()
);

-- ============================================================
-- SHOTS
-- ============================================================
create table public.shots (
  id uuid primary key default gen_random_uuid(),
  scene_id uuid references public.scenes(id) on delete cascade not null,
  project_id uuid references public.projects(id) on delete cascade not null,
  shot_number integer not null,
  camera_direction text,
  action_description text,
  dialogue text,
  speaker_character_id uuid references public.characters(id),
  emotion text,
  duration_estimate integer,
  status text default 'pending' check (status in ('pending','generating','completed','failed','flagged')),
  video_url text,
  audio_url text,
  thumbnail_url text,
  generation_prompt text,
  continuity_score float,
  retry_count integer default 0,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- ============================================================
-- AUDIO TRACKS
-- ============================================================
create table public.audio_tracks (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references public.projects(id) on delete cascade not null,
  scene_id uuid references public.scenes(id),
  shot_id uuid references public.shots(id),
  track_type text not null check (track_type in ('narration','dialogue','music','sfx','ambient')),
  character_id uuid references public.characters(id),
  file_url text,
  duration_seconds float,
  status text default 'pending' check (status in ('pending','generating','completed','failed')),
  created_at timestamptz default now()
);

-- ============================================================
-- RENDER JOBS
-- ============================================================
create table public.render_jobs (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references public.projects(id) on delete cascade not null,
  user_id uuid references public.profiles(id) not null,
  job_type text not null check (job_type in ('shot','scene','audio','assembly','export')),
  status text default 'queued' check (status in ('queued','running','completed','failed','cancelled')),
  progress integer default 0,
  error_message text,
  started_at timestamptz,
  completed_at timestamptz,
  credits_used integer default 0,
  metadata jsonb,
  created_at timestamptz default now()
);

-- ============================================================
-- EXPORTS
-- ============================================================
create table public.exports (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references public.projects(id) on delete cascade not null,
  user_id uuid references public.profiles(id) not null,
  resolution text default '1080p',
  format text default 'mp4',
  aspect_ratio text default 'landscape',
  file_url text,
  file_size_bytes bigint,
  duration_seconds float,
  status text default 'pending' check (status in ('pending','rendering','completed','failed')),
  created_at timestamptz default now()
);

-- ============================================================
-- STYLE BIBLE
-- ============================================================
create table public.style_bibles (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references public.projects(id) on delete cascade not null unique,
  cinematic_style text,
  color_palette jsonb,
  camera_style text,
  emotional_intensity integer default 5,
  scene_pace integer default 5,
  approved boolean default false,
  created_at timestamptz default now()
);

-- ============================================================
-- NOTIFICATIONS
-- ============================================================
create table public.notifications (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.profiles(id) on delete cascade not null,
  title text not null,
  body text,
  type text check (type in ('render_complete','render_failed','project_complete','subscription','system')),
  read boolean default false,
  created_at timestamptz default now()
);

-- ============================================================
-- SUBSCRIPTIONS / BILLING
-- ============================================================
create table public.subscriptions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.profiles(id) on delete cascade not null unique,
  stripe_subscription_id text unique,
  plan text not null default 'starter',
  status text default 'active',
  current_period_start timestamptz,
  current_period_end timestamptz,
  cancel_at_period_end boolean default false,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================
alter table public.profiles enable row level security;
alter table public.projects enable row level security;
alter table public.characters enable row level security;
alter table public.locations enable row level security;
alter table public.scenes enable row level security;
alter table public.shots enable row level security;
alter table public.audio_tracks enable row level security;
alter table public.render_jobs enable row level security;
alter table public.exports enable row level security;
alter table public.style_bibles enable row level security;
alter table public.notifications enable row level security;
alter table public.subscriptions enable row level security;

-- Users can only access their own data
create policy "Users own their profile" on public.profiles for all using (auth.uid() = id);
create policy "Users own their projects" on public.projects for all using (auth.uid() = user_id);
create policy "Users own their characters" on public.characters for all using (auth.uid() = (select user_id from public.projects where id = project_id));
create policy "Users own their locations" on public.locations for all using (auth.uid() = (select user_id from public.projects where id = project_id));
create policy "Users own their scenes" on public.scenes for all using (auth.uid() = (select user_id from public.projects where id = project_id));
create policy "Users own their shots" on public.shots for all using (auth.uid() = (select user_id from public.projects where id = project_id));
create policy "Users own their audio" on public.audio_tracks for all using (auth.uid() = (select user_id from public.projects where id = project_id));
create policy "Users own their jobs" on public.render_jobs for all using (auth.uid() = user_id);
create policy "Users own their exports" on public.exports for all using (auth.uid() = user_id);
create policy "Users own their bibles" on public.style_bibles for all using (auth.uid() = (select user_id from public.projects where id = project_id));
create policy "Users own their notifications" on public.notifications for all using (auth.uid() = user_id);
create policy "Users own their subscriptions" on public.subscriptions for all using (auth.uid() = user_id);

-- ============================================================
-- INDEXES for performance
-- ============================================================
create index idx_projects_user_id on public.projects(user_id);
create index idx_projects_status on public.projects(status);
create index idx_scenes_project_id on public.scenes(project_id);
create index idx_shots_scene_id on public.shots(scene_id);
create index idx_shots_status on public.shots(status);
create index idx_shots_project_id on public.shots(project_id);
create index idx_render_jobs_project_id on public.render_jobs(project_id);
create index idx_render_jobs_status on public.render_jobs(status);
create index idx_notifications_user_id on public.notifications(user_id);

-- ============================================================
-- UPDATED_AT triggers
-- ============================================================
create or replace function public.handle_updated_at()
returns trigger as $$
begin new.updated_at = now(); return new; end;
$$ language plpgsql;

create trigger handle_updated_at before update on public.profiles for each row execute procedure public.handle_updated_at();
create trigger handle_updated_at before update on public.projects for each row execute procedure public.handle_updated_at();
create trigger handle_updated_at before update on public.shots for each row execute procedure public.handle_updated_at();
create trigger handle_updated_at before update on public.subscriptions for each row execute procedure public.handle_updated_at();

-- ============================================================
-- DONE — All tables, RLS, indexes, and triggers created
-- ============================================================
