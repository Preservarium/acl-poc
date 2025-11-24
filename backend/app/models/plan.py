from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from uuid import uuid4

from app.database import Base


class Plan(Base):
    """Plan model - belongs to a site."""

    __tablename__ = "plans"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(255), nullable=False, index=True)
    site_id = Column(String(36), ForeignKey("sites.id", ondelete="CASCADE"), nullable=False)
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    site = relationship("Site", back_populates="plans")
    creator = relationship("User", foreign_keys=[created_by])
    sensors = relationship("Sensor", back_populates="plan", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Plan(id={self.id}, name={self.name}, site_id={self.site_id})>"
