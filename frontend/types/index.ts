export type ProjectStatus = 'draft' | 'generating' | 'review' | 'completed' | 'failed'

export interface Project {
  id: string
  user_id: string
  title: string
  status: ProjectStatus
  script_text?: string
  style?: string
  created_at: string
  updated_at: string
  scene_count?: number
  character_count?: number
  duration_estimate?: number
}

export interface Character {
  id: string
  project_id: string
  name: string
  description?: string
  appearance?: string
  voice_id?: string
  approved: boolean
  reference_image_url?: string
  created_at: string
}

export interface Scene {
  id: string
  project_id: string
  scene_number: number
  title?: string
  location?: string
  emotion?: string
  duration_estimate?: number
  summary?: string
}

export interface Shot {
  id: string
  scene_id: string
  shot_number: number
  camera_direction?: string
  action?: string
  dialogue?: string
  status: 'pending' | 'generating' | 'completed' | 'failed'
  video_url?: string
  duration?: number
}

export interface User {
  id: string
  email: string
  full_name?: string
  avatar_url?: string
  subscription_tier: 'starter' | 'pro' | 'studio'
  credits_used: number
  credits_limit: number
}
