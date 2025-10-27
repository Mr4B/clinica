from __future__ import annotations
import uuid
from typing import TYPE_CHECKING, Optional
from sqlmodel import SQLModel, Field, Relationship, Column, JSON, Index, Integer, UUID, ForeignKey, String, DateTime, Text
from datetime import datetime, timezone, date
from sqlalchemy.ext.hybrid import hybrid_property
from app.services.encryption import field_encryption
from pydantic import BaseModel, field_validator


# ################################
# Gestione del catalogo dei moduli
# ################################

class ModuleCatalog(SQLModel, table=True):
    __tablename__ = "module_catalog"

    module_id: int = Field(primary_key=True)  # SERIAL
    code: str = Field(max_length=10, unique=True, index=True)
    name: Optional[str] = Field(default=None, max_length=100)

    current_schema_version: int = Field(gt=0)  # NOT NULL, >0
    active: bool = Field(default=True)         # NOT NULL DEFAULT true
    updated_at: Optional[date] = Field(default=None)

    __table_args__ = (
        Index("module_catalog_module_code", "code", unique=True),
    )
    

class ModuleCatalogBase(BaseModel):
    code: str
    name: Optional[str] = None
    current_schema_version: int
    active: bool = True
    updated_at: Optional[date] = None

    @field_validator("code")
    @classmethod
    def _code_norm(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("code required")
        if len(v) > 10:
            raise ValueError("code max length 10")
        return v.upper()

    @field_validator("current_schema_version")
    @classmethod
    def _version_pos(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("current_schema_version must be > 0")
        return v

class ModuleCatalogCreate(ModuleCatalogBase):
    pass

class ModuleCatalogUpdate(BaseModel):
    name: Optional[str] = None
    current_schema_version: Optional[int] = None
    active: Optional[bool] = None
    updated_at: Optional[date] = None

    @field_validator("current_schema_version")
    @classmethod
    def _version_pos_opt(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v <= 0:
            raise ValueError("current_schema_version must be > 0")
        return v

class ModuleCatalogResponse(ModuleCatalogBase):
    module_id: int

    model_config = {"from_attributes": True}

class ModuleCatalogListResponse(BaseModel):
    items: list[ModuleCatalogResponse]
    total: int
    page: int
    page_size: int
    has_next: bool


# ############################
# Gestione dei singoli moduli
# ############################

class ModuleEntry(SQLModel, table=True):
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    dossier_id = Column(UUID, ForeignKey("dossiers.id"), nullable=False)
    module_code = Column(String(50), nullable=False, index=True)
    schema_version = Column(Integer, nullable=False)
    
    # Dati del modulo
    _data_encrypted = Column("data", Text, nullable=False)
    
    # Audit trail
    occurred_at = Column(DateTime(timezone=True), nullable=False) # dovrebbe esserci nei data
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    created_by_user_id = Column(UUID, ForeignKey("users.id"))
    
    # Soft delete
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by_user_id = Column(UUID, ForeignKey("users.id"), nullable=True)
    deletion_reason = Column(Text, nullable=True)
    
    # Firma digitale/hash per immutabilità (importante per cartelle cliniche)
    signature_hash = Column(String(64))  # SHA-256 del contenuto
    
    __table_args__ = (
        Index('idx_module_dossier', 'dossier_id', 'module_code', 'occurred_at'),
    )
    
    @hybrid_property
    def data(self) -> dict:
        """Getter: decritta automaticamente"""
        if self._data_encrypted:
            try:
                return field_encryption.decrypt_dict(self._data_encrypted)
            except Exception as e:
                # Log errore di decrittazione
                print(f"Decryption error for entry {self.id}: {e}")
                return {}
        return {}
    
    @data.setter
    def data(self, value: dict):
        """Setter: critta automaticamente"""
        if value is not None:
            self._data_encrypted = field_encryption.encrypt_dict(value)
        else:
            self._data_encrypted = None
    
    def __repr__(self):
        return f"<ModuleEntry {self.module_code} v{self.schema_version}>"
    
    
class EntryCreate(BaseModel):
    """Schema per creare una nuova entry"""
    dossier_id: UUID
    module_code: str = Field(..., description="Codice modulo es. ROG26/1.1")
    schema_version: Optional[int] = Field(None, description="Versione schema (default: ultima)")
    occurred_at: Optional[datetime] = Field(None, description="Timestamp evento clinico")
    data: dict = Field(..., description="Dati del modulo")


class EntryUpdate(BaseModel):
    """Schema per aggiornare una entry esistente"""
    occurred_at: Optional[datetime] = None
    data: Optional[dict] = None


class EntryResponse(BaseModel):
    """Schema risposta entry"""
    id: UUID
    dossier_id: UUID
    module_code: str
    schema_version: int
    occurred_at: datetime
    data: dict
    created_at: datetime
    created_by_user_id: Optional[UUID]
    updated_at: Optional[datetime]
    updated_by_user_id: Optional[UUID]
    deleted_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class EntryListResponse(BaseModel):
    """Schema risposta lista entries"""
    items: list[EntryResponse]
    total: int
    page: int
    page_size: int
    has_next: bool


class ModuleInfo(BaseModel):
    """Info su un modulo disponibile"""
    code: str
    versions: list[int]
    latest_version: int
    schema_fields: Optional[dict] = None