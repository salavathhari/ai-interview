from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.database import Base


class SystemHealthLog(Base):
    __tablename__ = "system_health_logs"

    id = Column(Integer, primary_key=True, index=True)
    service_name = Column(String, index=True)   # "database", "ai_service", "websocket", "storage"
    status = Column(String, default="online")   # "online", "offline", "warning"
    response_time_ms = Column(Float, nullable=True)
    checked_at = Column(DateTime(timezone=True), server_default=func.now())
