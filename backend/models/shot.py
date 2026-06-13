from sqlalchemy import Column, String, Integer, Text, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin, get_uuid

class Shot(Base, TimestampMixin):
    __tablename__ = "shots"

    id = Column(String, primary_key=True, default=get_uuid)
    scene_id = Column(String, ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    shot_number = Column(Integer, nullable=False)
    camera_direction = Column(String)
    action_description = Column(Text)
    dialogue = Column(Text)
    speaker_character_id = Column(String, ForeignKey("characters.id"))
    emotion = Column(String)
    duration_estimate = Column(Integer)
    status = Column(String, default="pending")
    video_url = Column(String)
    audio_url = Column(String)
    thumbnail_url = Column(String)
    generation_prompt = Column(Text)
    continuity_score = Column(Float)
    retry_count = Column(Integer, default=0)

    scene = relationship("Scene", back_populates="shots")

class RenderJob(Base, TimestampMixin):
    __tablename__ = "render_jobs"

    id = Column(String, primary_key=True, default=get_uuid)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, nullable=False)
    job_type = Column(String, nullable=False)
    status = Column(String, default="queued")
    progress = Column(Integer, default=0)
    error_message = Column(Text)
    credits_used = Column(Integer, default=0)

    project = relationship("Project", back_populates="render_jobs")
