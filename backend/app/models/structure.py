# from __future__ import annotations

import uuid
from typing import Optional, TYPE_CHECKING, List
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy.orm import Mapped

# if TYPE_CHECKING:
#     from .user import User          # <-- import locale
#     from .dossier import Dossier    # <-- import locale se serve

# class Structure(SQLModel, table=True):
#     __tablename__ = "structure"

#     id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
#     name: str = Field(max_length=200, index=True)
#     code: str = Field(max_length=50, unique=True, index=True)
#     type: str = Field(max_length=50)

#     address: str = Field(max_length=500)
#     city: str = Field(max_length=100)
#     postal_code: str = Field(max_length=10)
#     province: str = Field(max_length=2)

#     phone: Optional[str] = Field(default=None, max_length=20)
#     email: Optional[str] = Field(default=None, max_length=255)
#     fax: Optional[str] = Field(default=None, max_length=20)

#     vat_number: Optional[str] = Field(default=None, max_length=20)
#     fiscal_code: Optional[str] = Field(default=None, max_length=16)

#     max_capacity: Optional[int] = Field(default=None)
#     is_active: bool = Field(default=True)

#     created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
#     created_by_user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")
#     updated_at: Optional[datetime] = Field(default=None)
#     updated_by_user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")
#     deleted_at: Optional[datetime] = Field(default=None, index=True)
#     deleted_by_user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")

#     # Relazioni
#     dossiers: Mapped[List["Dossier"]] = Relationship(back_populates="structure")
    
#     # Relazione principale: tutti gli utenti di questa struttura
#     users: Mapped[List["User"]] = Relationship(
#         back_populates="structure",
#         sa_relationship_kwargs={"foreign_keys": "[User.structure_id]"}
#     )
    
#     # Relazioni per tracciare chi ha fatto modifiche
#     created_by: Mapped[Optional["User"]] = Relationship(
#         sa_relationship_kwargs={
#             "foreign_keys": "[Structure.created_by_user_id]",
#             "post_update": True
#         }
#     )
#     updated_by: Mapped[Optional["User"]] = Relationship(
#         sa_relationship_kwargs={
#             "foreign_keys": "[Structure.updated_by_user_id]",
#             "post_update": True
#         }
#     )
#     deleted_by: Mapped[Optional["User"]] = Relationship(
#         sa_relationship_kwargs={
#             "foreign_keys": "[Structure.deleted_by_user_id]",
#             "post_update": True
#         }
#     )


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
