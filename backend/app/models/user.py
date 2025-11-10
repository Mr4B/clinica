# from __future__ import annotations

import uuid
from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped

# if TYPE_CHECKING:
#     from .structure import Structure  # <-- import locale, non via app.models
#     from .role import Role  # <-- import locale, non via app.models

# class User(SQLModel, table=True):
#     __tablename__ = "user"

#     id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
#     first_name: str = Field(max_length=100)
#     last_name: str = Field(max_length=100)
#     username: str = Field(unique=True, index=True, max_length=100)
#     hashed_password: str
#     structure_id: uuid.UUID | None = Field(default=None, foreign_key="structure.id")
#     role_id: uuid.UUID | None = Field(default=None, foreign_key="role.id")
#     is_superuser: bool = False

#     structure: Mapped[Optional["Structure"]] = Relationship(
#         back_populates="users",
#         sa_relationship_kwargs={"foreign_keys": "[User.structure_id]"}
#     )
#     role: Mapped[Optional["Role"]] = Relationship(back_populates="users")
    

# ---- Schemi API ----
class UserCreate(SQLModel):
    first_name: str
    last_name: str
    username: str
    password: str  # in input; verrà trasformata in hashed_password
    structure_id: uuid.UUID | None = None
    role_id: uuid.UUID | None = None
    is_superuser: bool = False

class UserUpdate(SQLModel):
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    password: str | None = None
    structure_id: uuid.UUID | None = None
    role_id: uuid.UUID | None = None
    is_superuser: bool | None = None

class UserPublic(SQLModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    username: str
    structure_id: uuid.UUID | None
    role_id: uuid.UUID | None
    is_superuser: bool

class UserRegister(SQLModel):
    first_name: str
    last_name: str
    username: str
    password: str

class UserUpdateMe(SQLModel):
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None

class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int
    
class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)