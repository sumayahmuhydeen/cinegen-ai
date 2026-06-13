from sqlalchemy import Column, String, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin, get_uuid

class Character(Base, TimestampMixin):
    __tablename__ = "characters"

    id = Column(String, primary_key=True, default=get_uuid)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    role = Column(String)
    description = Column(Text)
    appearance = Column(Text)
    age_range = Column(String)
    voice_id = Column(String)
    approved = Column(Boolean, default=False)
    reference_image_url = Column(String)
    prompt_description = Column(Text)

    project = relationship("Project", back_populates="characters")
