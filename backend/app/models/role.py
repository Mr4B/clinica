from __future__ import annotations
import uuid
from typing import TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship, Column, JSON

if TYPE_CHECKING:   # import solo per mypy/IDE, non a runtime
    from .user import User

class Role(SQLModel, table=True):
    __tablename__ = "role"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(unique=True, index=True, max_length=100)
    # semplice lista di moduli in JSON per iniziare; potrai normalizzare in seguito
    modules: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    created_by: uuid.UUID | None = Field(default=None, foreign_key="user.id")

    # users: list["User"] = Relationship(back_populates="role")

class RoleCreate(SQLModel):
    name: str
    modules: list[str] = []

class RoleUpdate(SQLModel):
    name: str | None = None
    modules: list[str] | None = None

class RolePublic(SQLModel):
    id: uuid.UUID
    name: str
    modules: list[str]
    created_by: uuid.UUID | None
    
class RolesPublic(SQLModel):
    data: list[RolePublic]

class AssignRoleIn(SQLModel):
    role_id: uuid.UUID