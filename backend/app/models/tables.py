import uuid
from typing import Optional, List
from datetime import datetime, timezone, date
from sqlmodel import SQLModel, Field, Relationship, Column, JSON, Text, String, Integer, Index
from enum import Enum
from sqlalchemy.ext.hybrid import hybrid_property
from app.services.encryption import field_encryption
from sqlalchemy.dialects.postgresql import JSONB


class Role(SQLModel, table=True):
    __tablename__ = "role"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=100, unique=True, index=True)
    description: Optional[str] = Field(default=None, max_length=500)
    modules: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    
    users: list["User"] = Relationship(back_populates="role")


class Structure(SQLModel, table=True):
    __tablename__ = "structure"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=200, index=True)
    code: str = Field(max_length=50, unique=True, index=True)
    type: str = Field(max_length=50)

    address: str = Field(max_length=500)
    city: str = Field(max_length=100)
    postal_code: str = Field(max_length=10)
    province: str = Field(max_length=2)

    phone: Optional[str] = Field(default=None, max_length=20)
    email: Optional[str] = Field(default=None, max_length=255)
    fax: Optional[str] = Field(default=None, max_length=20)

    vat_number: Optional[str] = Field(default=None, max_length=20)
    fiscal_code: Optional[str] = Field(default=None, max_length=16)

    max_capacity: Optional[int] = Field(default=None)
    is_active: bool = Field(default=True)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by_user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")
    updated_at: Optional[datetime] = Field(default=None)
    updated_by_user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")
    deleted_at: Optional[datetime] = Field(default=None, index=True)
    deleted_by_user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")

    dossiers: list["Dossier"] = Relationship(back_populates="structure")
    users: list["User"] = Relationship(
        back_populates="structure",
        sa_relationship_kwargs={"foreign_keys": "[User.structure_id]"}
    )

class User(SQLModel, table=True):
    __tablename__ = "user"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    username: str = Field(unique=True, index=True, max_length=100)
    hashed_password: str
    structure_id: Optional[uuid.UUID] = Field(default=None, foreign_key="structure.id")
    role_id: Optional[uuid.UUID] = Field(default=None, foreign_key="role.id")
    is_superuser: bool = False
    is_active: bool = True

    structure: Optional["Structure"] = Relationship(
        back_populates="users",
        sa_relationship_kwargs={"foreign_keys": "[User.structure_id]"}
    )
    role: Optional["Role"] = Relationship(back_populates="users")
    dossiers: list["Dossier"] = Relationship(
        back_populates="created_by_user",
        sa_relationship_kwargs={"foreign_keys": "[Dossier.created_by_user_id]"}
    )

class CareLevel(str, Enum):
    R3 = "R3"
    R3D = "R3D"

class Dossier(SQLModel, table=True):
    """
    Modello dossier sanitario.
    Contiene tutti i moduli clinici di un paziente in una struttura.
    """
    __tablename__ = "dossiers"
    
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
    status: str = Field(default="active", index=True)
    
    # Audit
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by_user_id: uuid.UUID = Field(foreign_key="user.id")
    updated_at: Optional[datetime] = Field(default=None)
    updated_by_user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")
    
    # Soft delete
    deleted_at: Optional[datetime] = Field(default=None, index=True)
    deleted_by_user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")
    
    # Relationships
    patient:   Optional["Patient"]   = Relationship(back_populates="dossiers")
    structure: Optional["Structure"] = Relationship(back_populates="dossiers")
    entries:   list["ModuleEntry"]   = Relationship(back_populates="dossier")
    
    created_by_user: Optional["User"] = Relationship(
        back_populates="dossiers",
        sa_relationship_kwargs={"foreign_keys": "[Dossier.created_by_user_id]"}
    )


class Patient(SQLModel, table=True):
    """
    Modello paziente (anagrafica).
    Contiene dati anagrafici e clinici di base.
    """
    __tablename__ = "patient"
    
    model_config = {
        "arbitrary_types_allowed": True,
        "ignored_types": (hybrid_property,)
    }
    
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
    health_card_number_encrypted: Optional[str] = Field(default=None, sa_column=Column("health_card_number", Text))
    @hybrid_property
    def health_card_number(self) -> str:
        """Getter: decritta automaticamente"""
        if self.health_card_number_encrypted:
            try:
                return field_encryption.decrypt_str(self.health_card_number_encrypted)
            except Exception as e:
                print(f"Decryption error for entry {self.id}: {e}")
                return None
        return None
    
    @health_card_number.setter
    def health_card_number(self, value: str | None):
        """Setter: critta automaticamente"""            
        self.health_card_number_encrypted = field_encryption.encrypt_str(value) if value else None
            
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


class ModuleEntry(SQLModel, table=True):
    __tablename__ = "module_entry"
    
    model_config = {
        "arbitrary_types_allowed": True,
        "ignored_types": (hybrid_property,)
    }
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    dossier_id: uuid.UUID = Field(foreign_key="dossiers.id")
    module_code: str = Field(max_length=50, index=True)
    schema_version: int
    data_encrypted: str = Field(sa_column=Column("data", Text, nullable=False))
    occurred_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by_user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")
    deleted_at: Optional[datetime] = Field(default=None)
    deleted_by_user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")
    deletion_reason: Optional[str] = Field(default=None)
    signature_hash: Optional[str] = Field(default=None, max_length=64)
    
    dossier: Optional["Dossier"] = Relationship(back_populates="entries")
    
    __table_args__ = (
        Index('idx_module_dossier', 'dossier_id', 'module_code', 'occurred_at'),
    )
    
    @hybrid_property
    def data(self) -> dict:
        """Getter: decripta automaticamente"""
        if self.data_encrypted:
            try:
                return field_encryption.decrypt_dict(self.data_encrypted)
            except Exception as e:
                print(f"Decryption error for entry {self.id}: {e}")
                return {}
        return {}
    
    @data.setter
    def data(self, value: dict):
        """Setter: cripta automaticamente"""
        if value is not None:
            self.data_encrypted = field_encryption.encrypt_dict(value)
        else:
            self.data_encrypted = None
    
    def __repr__(self):
        return f"<ModuleEntry {self.module_code} v{self.schema_version}>"
    

class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_log"
    
    audit_id: Optional[int] = Field(default=None, primary_key=True)
    ts: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True
    )
    user_id: Optional[uuid.UUID] = Field(default=None, index=True)
    username: Optional[str] = Field(default=None, max_length=255)
    action: str = Field(max_length=20, index=True)
    table_name: str = Field(max_length=100, index=True)
    record_id: str = Field(max_length=50, index=True)
    
    before: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True)
    )
    after: Optional[dict] = Field(
        default=None,
        sa_column=Column(JSONB, nullable=True)
    )
    ip_address: Optional[str] = Field(default=None, max_length=45)
    endpoint: Optional[str] = Field(default=None, max_length=255)
    
    __table_args__ = (
        Index('idx_audit_user_table', 'user_id', 'table_name'),
        Index('idx_audit_record', 'table_name', 'record_id'),
        Index('idx_audit_ts_action', 'ts', 'action'),
    )    
    
