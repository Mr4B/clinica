from __future__ import annotations
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime, timezone
import uuid 
from app.models import User, Dossier


class Structure(SQLModel, table=True):
    """
    Modello struttura sanitaria.
    Può essere: RSA, ospedale, centro diurno, etc.
    """
    __tablename__ = "structure"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Dati struttura
    name: str = Field(max_length=200, index=True)
    code: str = Field(max_length=50, unique=True, index=True)  # Codice identificativo
    type: str = Field(max_length=50)  # RSA, R3, R3D, Ospedale...
    
    # Indirizzo
    address: str = Field(max_length=500)
    city: str = Field(max_length=100)
    postal_code: str = Field(max_length=10)
    province: str = Field(max_length=2)
    
    # Contatti
    phone: Optional[str] = Field(default=None, max_length=20)
    email: Optional[str] = Field(default=None, max_length=255)
    fax: Optional[str] = Field(default=None, max_length=20)
    
    # Dati amministrativi
    vat_number: Optional[str] = Field(default=None, max_length=20)  # Partita IVA
    fiscal_code: Optional[str] = Field(default=None, max_length=16)
    
    # Configurazione
    max_capacity: Optional[int] = Field(default=None)  # Posti letto
    is_active: bool = Field(default=True)
    
    # Moduli abilitati per questa struttura (opzionale)
    # enabled_modules: Optional[list[str]] = Field(default=None, sa_column=Column(JSON))
    
    # Audit
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by_user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")
    updated_at: Optional[datetime] = Field(default=None)
    updated_by_user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")
    
    # Soft delete
    deleted_at: Optional[datetime] = Field(default=None, index=True)
    deleted_by_user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")
    
    # Relationships
    dossiers: list["Dossier"] = Relationship(back_populates="structure")
    users: list["User"] = Relationship(back_populates="structure")


class StructureBase(SQLModel):
    name: str = Field(min_length=1, max_length=200)
    code: str = Field(min_length=1, max_length=50)
    type: str
    address: str
    city: str
    postal_code: str
    province: str = Field(max_length=2)
    phone: Optional[str] = None
    email: Optional[str] = None
    fax: Optional[str] = None
    vat_number: Optional[str] = None
    fiscal_code: Optional[str] = None
    max_capacity: Optional[int] = None
    is_active: bool = True
    enabled_modules: Optional[list[str]] = None


class StructureCreate(StructureBase):
    pass


class StructureUpdate(SQLModel):
    name: Optional[str] = None
    type: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    province: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    fax: Optional[str] = None
    max_capacity: Optional[int] = None
    is_active: Optional[bool] = None
    enabled_modules: Optional[list[str]] = None


class StructureResponse(StructureBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# class StructurePublic(SQLModel):
#     id: int
#     name: str
#     location: str
#     n_persone: int


class StructuresPublic(SQLModel):
    data: list[StructureBase]
