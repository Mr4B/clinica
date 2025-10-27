# Qui sono contenute le dipendenze ad esempio per accedere alle rotte

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError
from sqlmodel import Session

from jose import jwt, JWTError   

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
            token,
            settings.SECRET_KEY,
            algorithms=[security.ALGORITHM],  # es. "HS256" o "RS256"
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
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

# Dependency per ottenere request (per audit log READ)
def get_request_info(request: Request) -> dict:
    """Estrae info dalla request per audit log"""
    return {
        "ip": request.client.host if request.client else None,
        "endpoint": f"{request.method} {request.url.path}"
    }

RequestInfo = Annotated[dict, Depends(get_request_info)]

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


# def require_module_access(module_code: str):
#     """
#     Dipendenza FastAPI da usare come:
#         @router.get("/...", dependencies=[Depends(require_module_access("nome_modulo"))])
#     Verifica che l'utente corrente abbia un ruolo con accesso al modulo specificato.
#     """
#     def module_checker(current_user: CurrentUser, session: SessionDep) -> None:
#         if not current_user.role_id:
#             raise HTTPException(status_code=403, detail="User has no role assigned")

#         role = session.get(Role, current_user.role_id)
#         if not role:
#             raise HTTPException(status_code=404, detail="Role not found")

#         if module_code not in (role.modules or []):
#             raise HTTPException(
#                 status_code=403,
#                 detail=f"Access to module '{module_code}' denied for role '{role.name}'",
#             )
#         # Nessun return: è solo una dipendenza di controllo
#     return module_checker

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