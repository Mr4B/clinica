from __future__ import annotations

import uuid
from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel

from typing import TYPE_CHECKING, Optional
# if TYPE_CHECKING:
#     from .item import Item

# ---- User schemas (base/in/out) ----
# class UserBase(SQLModel):
#     email: EmailStr = Field(unique=True, index=True, max_length=255)
#     is_active: bool = True
#     is_superuser: bool = False
#     full_name: str | None = Field(default=None, max_length=255)

# class UserCreate(UserBase):
#     password: str = Field(min_length=8, max_length=40)

# class UserRegister(SQLModel):
#     email: EmailStr = Field(max_length=255)
#     password: str = Field(min_length=8, max_length=40)
#     full_name: str | None = Field(default=None, max_length=255)

# class UserUpdate(UserBase):
#     email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
#     password: str | None = Field(default=None, min_length=8, max_length=40)

# class UserUpdateMe(SQLModel):
#     full_name: str | None = Field(default=None, max_length=255)
#     email: EmailStr | None = Field(default=None, max_length=255)



# ---- User DB model ----
# class User(UserBase, table=True):
#     id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
#     hashed_password: str
#     # forward ref to Item, defined in item.py
#     items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)

# # ---- User public schemas ----
# class UserPublic(UserBase):
#     id: uuid.UUID

# class UsersPublic(SQLModel):
#     data: list[UserPublic]
#     count: int


if TYPE_CHECKING:   # import solo per type checking
    from .role import Role

# ---- DB model ----
class User(SQLModel, table=True):
    __tablename__ = "user"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    username: str = Field(unique=True, index=True, max_length=100)
    hashed_password: str  # conserva l'hash, non la password in chiaro
    # se non hai ancora la tabella 'structure', non mettere foreign_key per ora
    structure_id: uuid.UUID | None = Field(default=None, foreign_key="structure.id")
    role_id: uuid.UUID | None = Field(default=None, foreign_key="role.id")
    is_superuser: bool = False

    # role: "Role" = Relationship(back_populates="users")

# ---- Schemi API ----
class UserCreate(SQLModel):
    first_name: str
    last_name: str
    username: str
    password: str  # in input; verrà trasformata in hashed_password

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