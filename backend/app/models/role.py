from __future__ import annotations
import uuid
from typing import TYPE_CHECKING, List, Optional
from sqlmodel import SQLModel, Field, Relationship, Column, JSON
from sqlalchemy.orm import Mapped

# if TYPE_CHECKING:
#     from .user import User

# class Role(SQLModel, table=True):
#     __tablename__ = "role"

#     id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
#     name: str = Field(unique=True, index=True, max_length=100)
#     modules: List[str] = Field(default_factory=list, sa_column=Column(JSON))
#     created_by_user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")

#     # Relazione principale: tutti gli utenti con questo ruolo
#     users: Mapped[List["User"]] = Relationship(
#         back_populates="role",
#         sa_relationship_kwargs={"foreign_keys": "[User.role_id]"}
#     )
    
#     # Relazione per tracciare chi ha creato il ruolo
#     created_by: Mapped[Optional["User"]] = Relationship(
#         sa_relationship_kwargs={
#             "foreign_keys": "[Role.created_by_user_id]",
#             "post_update": True
#         }
#     )

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
    
class RolesPublic(SQLModel):
    data: list[RolePublic]

class AssignRoleIn(SQLModel):
    role_id: uuid.UUID