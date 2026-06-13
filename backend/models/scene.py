from sqlalchemy import Column, String, Integer, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin, get_uuid

class Scene(Base, TimestampMixin):
    __tablename__ = "scenes"

    id = Column(String, primary_key=True, default=get_uuid)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    scene_number = Column(Integer, nullable=False)
    title = Column(String)
    location_name = Column(String)
    emotion = Column(String)
    summary = Column(Text)
    duration_estimate = Column(Integer)
    approved = Column(Boolean, default=False)

    project = relationship("Project", back_populates="scenes")
    shots = relationship("Shot", back_populates="scene", cascade="all, delete-orphan")

class Location(Base, TimestampMixin):
    __tablename__ = "locations"

    id = Column(String, primary_key=True, default=get_uuid)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    environment_type = Column(String)
    time_of_day = Column(String)
    weather = Column(String)
    lighting_notes = Column(Text)
    approved = Column(Boolean, default=False)
    reference_image_url = Column(String)
    prompt_description = Column(Text)

    project = relationship("Project", back_populates="locations")
