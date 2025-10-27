import uuid
from datetime import datetime, timezone
from typing import Optional
from app.models import Patient, Structure, ModuleEntry
from pydantic import field_validator
from uuid import UUID
from sqlalchemy import Enum
from sqlmodel import Field, Relationship, SQLModel

class CareLevel(str, Enum.Enum):
    R3 = "R3"
    R3D = "R3D"

class Dossier(SQLModel, table=True):
    """
    Modello dossier sanitario.
    Contiene tutti i moduli clinici di un paziente in una struttura.
    """
    __tablename__ = "dossier"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # Riferimenti
    patient_id: uuid.UUID = Field(foreign_key="patient.id", index=True)
    structure_id: uuid.UUID = Field(foreign_key="structure.id", index=True)
    
    # Date ricovero/dimissione
    admission_date: datetime = Field(index=True)
    discharge_date: Optional[datetime] = Field(default=None, index=True)
    
    # livello assistenziale con vincolo R3 o R3D
    care_level: CareLevel = Field(index=True, sa_column_kwargs={"nullable": False})
    
    # Dati del paziente (se non si vuol fare la registrazione del paziente)
    utente: Optional[str] = Field(default=None)
    cod_nome: Optional[str] = Field(default=None)
    cod_cognome: Optional[str] = Field(default=None)
    cod_dossier_n: Optional[str] = Field(default=None)
    data_nascita: Optional[datetime] = Field(default=None)
    sesso: Optional[str] = Field(default=None)
    
    # Note generali
    notes: Optional[str] = Field(default=None)
    
    # Audit
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by_user_id: uuid.UUID = Field(foreign_key="user.id")
    updated_at: Optional[datetime] = Field(default=None)
    updated_by_user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")
    
    # Soft delete
    deleted_at: Optional[datetime] = Field(default=None, index=True)
    deleted_by_user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")
    
    # Relationships
    patient: Patient = Relationship(back_populates="dossiers")
    structure: Structure = Relationship(back_populates="dossiers")
    entries: list["ModuleEntry"] = Relationship(back_populates="dossier")


class DossierBase(SQLModel):
    patient_id: UUID
    structure_id: UUID
    care_level: str
    admission_date: datetime
    discharge_date: Optional[datetime] = None
    utente: Optional[str] = None
    cod_nome: Optional[str] = None
    cod_cognome: Optional[str] = None
    cod_dossier_n: Optional[str] = None
    data_nascita: Optional[datetime] = None
    sesso: Optional[str] = None
    notes: Optional[str] = None

class DossierCreate(DossierBase):
    @classmethod
    def validate_discharge_date(cls, v, values):
        if v and 'admission_date' in values and v < values['admission_date']:
            raise ValueError("Discharge date cannot be before admission date")
        return v

class DossierUpdate(SQLModel):
    patient_id: Optional[UUID] = None
    structure_id: Optional[UUID] = None
    care_level: Optional[str] = None
    admission_date: Optional[datetime] = None
    discharge_date: Optional[datetime] = None
    utente: Optional[str] = None
    cod_nome: Optional[str] = None
    cod_cognome: Optional[str] = None
    cod_dossier_n: Optional[str] = None
    data_nascita: Optional[datetime] = None
    sesso: Optional[str] = None
    notes: Optional[str] = None


class DossierResponse(DossierBase):
    id: uuid.UUID
    created_at: datetime
    created_by_user_id: uuid.UUID
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]
    
    # Nested data (opzionale)
    # patient: Optional[PatientResponse] = None
    
    class Config:
        from_attributes = True


class DossierDetailResponse(DossierResponse):
    """Response con dati completi inclusi entry count"""
    entries_count: int = 0
    last_entry_date: Optional[datetime] = None


class DossierListResponse(SQLModel):
    items: list[DossierResponse]
    total: int
    page: int
    page_size: int
    has_next: bool