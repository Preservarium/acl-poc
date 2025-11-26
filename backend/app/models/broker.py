from datetime import datetime
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from uuid import uuid4

from app.database import Base


class Broker(Base):
    """Broker model - belongs to a plan."""

    __tablename__ = "brokers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(255), nullable=False, index=True)
    protocol = Column(String(50), nullable=False)  # mqtt, coap, etc.
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    plan_id = Column(String(36), ForeignKey("plans.id", ondelete="CASCADE"), nullable=False)
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    plan = relationship("Plan", back_populates="brokers")
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        return f"<Broker(id={self.id}, name={self.name}, protocol={self.protocol}, plan_id={self.plan_id})>"
