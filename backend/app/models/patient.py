from pydantic import field_validator
from datetime import datetime, date, timezone
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship, Column, JSON, Text
from sqlalchemy.ext.hybrid import hybrid_property
from app.services.encryption import field_encryption
import uuid
from app.models import Dossier

class Patient(SQLModel, table=True):
    """
    Modello paziente (anagrafica).
    Contiene dati anagrafici e clinici di base.
    """
    __tablename__ = "patient"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # Dati anagrafici
    first_name: str = Field(max_length=100, index=True)
    last_name: str = Field(max_length=100, index=True)
    fiscal_code: str = Field(max_length=16, unique=True, index=True)  # Codice fiscale
    date_of_birth: date
    place_of_birth: str = Field(max_length=200)
    gender: str = Field(max_length=1)  # M/F/X
    
    # Contatti
    phone: Optional[str] = Field(default=None, max_length=20)
    email: Optional[str] = Field(default=None, max_length=255)
    address: Optional[str] = Field(default=None, max_length=500)
    city: Optional[str] = Field(default=None, max_length=100)
    postal_code: Optional[str] = Field(default=None, max_length=10)
    province: Optional[str] = Field(default=None, max_length=2)  # PU, RM, MI...
    
    # Dati sanitari base
    # health_card_number: Optional[str] = Field(default=None, max_length=50)  # Tessera sanitaria
    health_card_number_encrypted =  Column("health_card_number", Text, default=None)  # Tessera sanitaria cifrata
    @hybrid_property
    def health_card_number(self) -> str:
        """Getter: decritta automaticamente"""
        if self.health_card_number_encrypted:
            try:
                return field_encryption.decrypt_dict(self.health_card_number_encrypted)
            except Exception as e:
                print(f"Decryption error for entry {self.id}: {e}")
                return {}
        return {}
    
    @health_card_number.setter
    def health_card_number(self, value: str | None):
        """Setter: critta automaticamente"""            
        self.health_card_number_encrypted = field_encryption.encrypt_dict(value) if value else None
            
    # Contatti emergenza
    emergency_contact_name: Optional[str] = Field(default=None, max_length=200)
    emergency_contact_phone: Optional[str] = Field(default=None, max_length=20)
    emergency_contact_relationship: Optional[str] = Field(default=None, max_length=100)
    
    # Allergie e note importanti (JSON per flessibilità)
    allergies: Optional[list[str]] = Field(default=None, sa_column=Column(JSON))
    chronic_conditions: Optional[list[str]] = Field(default=None, sa_column=Column(JSON))
    notes: Optional[str] = Field(default=None)
    
    # Audit
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by_user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")
    updated_at: Optional[datetime] = Field(default=None)
    updated_by_user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")
    
    # Soft delete
    deleted_at: Optional[datetime] = Field(default=None, index=True)
    deleted_by_user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")
    
    # Relationships
    dossiers: list["Dossier"] = Relationship(back_populates="patient")
    




class PatientBase(SQLModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    fiscal_code: str = Field(min_length=16, max_length=16)
    date_of_birth: date
    place_of_birth: str
    gender: str = Field(pattern="^[MFX]$")
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    province: Optional[str] = None
    health_card_number: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    allergies: Optional[list[str]] = None
    chronic_conditions: Optional[list[str]] = None
    notes: Optional[str] = None
    
    @field_validator('fiscal_code')
    def validate_fiscal_code(cls, v):
        # Validazione base codice fiscale italiano
        if not v.isalnum():
            raise ValueError("Fiscal code must be alphanumeric")
        return v.upper()


class PatientCreate(PatientBase):
    pass


class PatientUpdate(SQLModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    province: Optional[str] = None
    health_card_number: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    allergies: Optional[list[str]] = None
    chronic_conditions: Optional[list[str]] = None
    notes: Optional[str] = None


class PatientResponse(PatientBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime]
    deleted_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class PatientListResponse(SQLModel):
    items: list[PatientResponse]
    total: int
    page: int
    page_size: int
    has_next: bool