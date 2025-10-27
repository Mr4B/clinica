# from sqlalchemy import Column, Integer, String, DateTime, UUID, Text, event
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import SQLModel, Column, Index, Integer, UUID, ForeignKey, String, DateTime
from datetime import datetime, timezone


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_log"
    
    audit_id = Column(Integer, primary_key=True, autoincrement=True)
    ts = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    user_id = Column(UUID, nullable=True, index=True)
    username = Column(String(255), nullable=True)
    action = Column(String(20), nullable=False, index=True)  # READ/CREATE/UPDATE/DELETE
    table_name = Column(String(100), nullable=False, index=True)
    record_id = Column(String(50), nullable=False, index=True)
    before = Column(JSONB, nullable=True)
    after = Column(JSONB, nullable=True)
    ip_address = Column(String(45), nullable=True)
    endpoint = Column(String(255), nullable=True)
    
    __table_args__ = (
        Index('idx_audit_user_table', 'user_id', 'table_name'),
        Index('idx_audit_record', 'table_name', 'record_id'),
        Index('idx_audit_ts_action', 'ts', 'action'),
    )