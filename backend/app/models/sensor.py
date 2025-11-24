from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from uuid import uuid4

from app.database import Base


class Sensor(Base):
    """Sensor model - belongs to a plan."""

    __tablename__ = "sensors"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(255), nullable=False, index=True)
    plan_id = Column(String(36), ForeignKey("plans.id", ondelete="CASCADE"), nullable=False)
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    plan = relationship("Plan", back_populates="sensors")
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        return f"<Sensor(id={self.id}, name={self.name}, plan_id={self.plan_id})>"
