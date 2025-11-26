from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from uuid import uuid4

from app.database import Base


class Alarm(Base):
    """Alarm model - belongs to a sensor."""

    __tablename__ = "alarms"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(255), nullable=False, index=True)
    threshold = Column(Float, nullable=False)
    condition = Column(String(50), nullable=False)  # gt, lt, eq, etc.
    active = Column(Boolean, default=True, nullable=False)
    sensor_id = Column(String(36), ForeignKey("sensors.id", ondelete="CASCADE"), nullable=False)
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    sensor = relationship("Sensor", back_populates="alarms")
    creator = relationship("User", foreign_keys=[created_by])
    alerts = relationship("Alert", back_populates="alarm", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Alarm(id={self.id}, name={self.name}, condition={self.condition}, threshold={self.threshold})>"
