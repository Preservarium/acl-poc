from datetime import datetime
from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from uuid import uuid4

from app.database import Base


class Alert(Base):
    """Alert model - triggered by an alarm."""

    __tablename__ = "alerts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    message = Column(String(1000), nullable=False)
    severity = Column(String(50), nullable=False)  # info, warning, critical
    triggered_at = Column(DateTime, nullable=False)
    acknowledged = Column(Boolean, default=False, nullable=False)
    alarm_id = Column(String(36), ForeignKey("alarms.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    alarm = relationship("Alarm", back_populates="alerts")

    def __repr__(self):
        return f"<Alert(id={self.id}, severity={self.severity}, acknowledged={self.acknowledged})>"
