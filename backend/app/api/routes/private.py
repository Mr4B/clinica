# app/api/routes/private.py
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import select

from app.api.deps import SessionDep, get_current_active_superuser
from app.core.security import get_password_hash
from app.models import User, UserPublic

router = APIRouter(tags=["private"], prefix="/private")


class PrivateUserCreate(BaseModel):
    first_name: str
    last_name: str
    username: str
    password: str
    is_superuser: bool = False


@router.post(
    "/users/",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
    # dependencies=[Depends(get_current_active_superuser)],
)
def create_user(user_in: PrivateUserCreate, session: SessionDep) -> Any:
    # username univoco
    exists = session.exec(select(User).where(User.username == user_in.username)).first()
    if exists:
        raise HTTPException(status_code=400, detail="Username already exists")

    user = User(
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password),
        is_superuser=user_in.is_superuser,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
