import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select, func

from app.api.deps import (
    CurrentUser,
    SessionDep,
    get_current_active_superuser,
)
from app.core.security import get_password_hash, verify_password
from app.models import ( User, UserCreate, UserUpdate, UserPublic, Role )
from app.models import Message, UserUpdateMe, UpdatePassword, UsersPublic, UserRegister, AssignRoleIn

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", dependencies=[Depends(get_current_active_superuser)], response_model=UsersPublic)
def read_users(session: SessionDep, skip: int = 0, limit: int = 100) -> Any:
    count = session.exec(select(func.count()).select_from(User)).one()
    users = session.exec(select(User).offset(skip).limit(limit)).all()
    return UsersPublic(data=users, count=count)


@router.post("/", dependencies=[Depends(get_current_active_superuser)], response_model=UserPublic, status_code=201)
def create_user(*, session: SessionDep, user_in: UserCreate) -> Any:
    # username univoco
    exists = session.exec(select(User).where(User.username == user_in.username)).first()
    if exists:
        raise HTTPException(status_code=400, detail="Username already exists")

    user = User(
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password),
        structure_id=user_in.structure_id,
        role_id=user_in.role_id,
        is_superuser=user_in.is_superuser,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.post("/signup", response_model=UserPublic, status_code=201)
def register_user(session: SessionDep, user_in: UserRegister) -> Any:
    exists = session.exec(select(User).where(User.username == user_in.username)).first()
    if exists:
        raise HTTPException(status_code=400, detail="Username already exists")

    # user_create = UserCreate.model_validate(user_in)
    user = User(
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.get("/me", response_model=UserPublic)
def read_user_me(current_user: CurrentUser) -> Any:
    return current_user


@router.patch("/me", response_model=UserPublic)
def update_user_me(
    *, session: SessionDep, user_in: UserUpdateMe, current_user: CurrentUser
) -> Any:
    if user_in.username and user_in.username != current_user.username:
        exists = session.exec(select(User).where(User.username == user_in.username)).first()
        if exists:
            raise HTTPException(status_code=409, detail="Username already exists")

    current_user.sqlmodel_update(user_in.model_dump(exclude_unset=True))
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user


@router.patch("/me/password", response_model=Message)
def update_password_me(
    *, session: SessionDep, body: UpdatePassword, current_user: CurrentUser
) -> Any:
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect password")
    if body.current_password == body.new_password:
        raise HTTPException(status_code=400, detail="New password cannot be the same as the current one")

    current_user.hashed_password = get_password_hash(body.new_password)
    session.add(current_user)
    session.commit()
    return Message(message="Password updated successfully")


@router.delete("/me", response_model=Message)
def delete_user_me(session: SessionDep, current_user: CurrentUser) -> Any:
    if current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Super users are not allowed to delete themselves")
    session.delete(current_user)
    session.commit()
    return Message(message="User deleted successfully")


@router.get("/{user_id}", response_model=UserPublic)
def read_user_by_id(user_id: uuid.UUID, session: SessionDep, current_user: CurrentUser) -> Any:
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id or current_user.is_superuser:
        return user
    raise HTTPException(status_code=403, detail="Not enough privileges")


@router.patch("/{user_id}", dependencies=[Depends(get_current_active_superuser)], response_model=UserPublic)
def update_user(
    *, session: SessionDep, user_id: uuid.UUID, user_in: UserUpdate
) -> Any:
    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_in.username:
        exists = session.exec(select(User).where(User.username == user_in.username)).first()
        if exists and exists.id != user_id:
            raise HTTPException(status_code=409, detail="Username already exists")

    update_data = user_in.model_dump(exclude_unset=True)
    if "password" in update_data and update_data["password"]:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

    db_user.sqlmodel_update(update_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@router.delete("/{user_id}", dependencies=[Depends(get_current_active_superuser)], response_model=Message)
def delete_user(session: SessionDep, current_user: CurrentUser, user_id: uuid.UUID) -> Message:
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=403, detail="Super users are not allowed to delete themselves")

    session.delete(user)
    session.commit()
    return Message(message="User deleted successfully")


@router.patch("/{user_id}/role", dependencies=[Depends(get_current_active_superuser)], response_model=UserPublic)
def assign_role(
    *, session: SessionDep, user_id: uuid.UUID, body: AssignRoleIn
) -> Any:
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    role = session.get(Role, body.role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    user.role_id = role.id
    session.add(user)
    session.commit()
    session.refresh(user)
    return user