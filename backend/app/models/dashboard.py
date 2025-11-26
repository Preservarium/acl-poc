from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from uuid import uuid4

from app.database import Base


class Dashboard(Base):
    """Dashboard model - customizable dashboard configuration."""

    __tablename__ = "dashboards"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(255), nullable=False, index=True)
    config = Column(JSON, default=dict, nullable=False)
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        return f"<Dashboard(id={self.id}, name={self.name})>"
