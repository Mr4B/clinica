# Qui sono contenute le dipendenze ad esempio per accedere alle rotte

from collections.abc import Generator
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlmodel import Session

from app.core import security
from app.core.config import settings
from app.core.db import engine
from app.models import TokenPayload, User, Role

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]


def get_current_user(session: SessionDep, token: TokenDep) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = session.get(User, token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]

# Sarebbe l'admin il superuser
def get_current_active_superuser(current_user: CurrentUser) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user


# Passargli il ruolo che richiede per accedere alla rotta
def require_role(role_name: str):
    def role_checker(current_user: CurrentUser, session: SessionDep) -> User:
        role = session.get(Role, current_user.role_id) if current_user.role_id else None
        if not role or role.name.lower() != role_name.lower():
            raise HTTPException(
                status_code=403,
                detail=f"Requires role: {role_name}",
            )
        return current_user
    return role_checker

# Devi essere admin per accedere
# def get_current_admin(
#     current_user: CurrentUser, session: SessionDep
# ) -> User:
#     # recupera il ruolo associato all'utente
#     role = session.get(Role, current_user.role_id) if current_user.role_id else None
#     if not role or role.name.lower() != "admin":
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="You don't have permission to access this resource",
#         )
#     return current_user