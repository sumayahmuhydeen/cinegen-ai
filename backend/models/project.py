from sqlalchemy import Column, String, Integer, Text, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin, get_uuid
import enum

class ProjectStatus(str, enum.Enum):
    DRAFT = "draft"
    ANALYZING = "analyzing"
    STORYBOARD = "storyboard"
    CHARACTERS = "characters"
    GENERATING = "generating"
    REVIEW = "review"
    COMPLETED = "completed"
    FAILED = "failed"

class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=get_uuid)
    user_id = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    status = Column(String, default=ProjectStatus.DRAFT)
    style = Column(String)
    script_text = Column(Text)
    blueprint = Column(JSON)
    scene_count = Column(Integer, default=0)
    character_count = Column(Integer, default=0)
    duration_estimate = Column(Integer)
    thumbnail_url = Column(String)

    scenes = relationship("Scene", back_populates="project", cascade="all, delete-orphan")
    characters = relationship("Character", back_populates="project", cascade="all, delete-orphan")
    locations = relationship("Location", back_populates="project", cascade="all, delete-orphan")
    render_jobs = relationship("RenderJob", back_populates="project", cascade="all, delete-orphan")
