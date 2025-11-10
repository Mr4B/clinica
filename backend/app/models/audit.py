# from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
# from sqlmodel import SQLModel, Field, Column, Index
# from sqlalchemy import Integer, String, DateTime
# from datetime import datetime, timezone
# from typing import Optional
# import uuid


# class AuditLog(SQLModel, table=True):
#     __tablename__ = "audit_log"
    
#     audit_id: int = Field(
#         default=None,
#         sa_column=Column(Integer, primary_key=True, autoincrement=True)
#     )
#     ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc),sa_column=Column(DateTime(timezone=True), nullable=False, index=True))
#     user_id: Optional[uuid.UUID] = Field(default=None,sa_column=Column(PGUUID(as_uuid=True), nullable=True, index=True))
#     username: Optional[str] = Field(
#         default=None,
#         sa_column=Column(String(255), nullable=True)
#     )
#     action: str = Field(
#         sa_column=Column(String(20), nullable=False, index=True)
#     )
#     table_name: str = Field(
#         sa_column=Column(String(100), nullable=False, index=True)
#     )
#     record_id: str = Field(
#         sa_column=Column(String(50), nullable=False, index=True)
#     )
#     before: Optional[dict] = Field(
#         default=None,
#         sa_column=Column(JSONB, nullable=True)
#     )
#     after: Optional[dict] = Field(
#         default=None,
#         sa_column=Column(JSONB, nullable=True)
#     )
#     ip_address: Optional[str] = Field(
#         default=None,
#         sa_column=Column(String(45), nullable=True)
#     )
#     endpoint: Optional[str] = Field(
#         default=None,
#         sa_column=Column(String(255), nullable=True)
#     )
    
#     __table_args__ = (
#         Index('idx_audit_user_table', 'user_id', 'table_name'),
#         Index('idx_audit_record', 'table_name', 'record_id'),
#         Index('idx_audit_ts_action', 'ts', 'action'),
#     )