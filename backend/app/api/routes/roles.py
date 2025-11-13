# app/api/routes/roles.py
import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlalchemy.exc import IntegrityError
from app.api.deps import SessionDep, get_current_active_superuser, get_current_user
from app.models import Role, RoleCreate, RoleUpdate, RolePublic, RolesPublic

router = APIRouter(prefix="/roles", tags=["roles"], dependencies=[Depends(get_current_user)])


# ---- CRUD ----
@router.get("/", response_model=RolesPublic)
def read_roles(session: SessionDep, skip: int = 0, limit: int = 100) -> Any:
    roles = session.exec(select(Role).offset(skip).limit(limit)).all()
    return RolesPublic(data=roles)


@router.get("/{role_id}", response_model=RolePublic)
def read_role(role_id: uuid.UUID, session: SessionDep) -> Any:
    role = session.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


@router.post("/", response_model=RolePublic)
def create_role(
    role_in: RoleCreate, 
    session: SessionDep, 
    current_user=Depends(get_current_user)
) -> Any:
    # Opzione 1: Controllo preventivo (consigliato)
    existing = session.exec(
        select(Role).where(Role.name == role_in.name)
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Un ruolo con il nome '{role_in.name}' esiste già"
        )
    
    role = Role(
        name=role_in.name, 
        modules=role_in.modules, 
        created_by=current_user.id
    )
    session.add(role)
    
    try:
        session.commit()
        session.refresh(role)
        return role
    except IntegrityError as e:
        session.rollback()
        # Fallback per altri vincoli di unicità
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Violazione del vincolo di unicità"
        )


@router.put("/{role_id}", response_model=RolePublic)
def update_role(role_id: uuid.UUID, role_in: RoleUpdate, session: SessionDep) -> Any:
    role = session.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    if role_in.name is not None:
        role.name = role_in.name
    if role_in.modules is not None:
        role.modules = role_in.modules

    session.add(role)
    session.commit()
    session.refresh(role)
    return role


@router.delete("/{role_id}")
def delete_role(role_id: uuid.UUID, session: SessionDep) -> Any:
    role = session.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    session.delete(role)
    session.commit()
    return {"message": "Role deleted successfully"}



# ---- Dipendenza di autorizzazione ----
def check_role_access(role_id: uuid.UUID, module_code: str, session: SessionDep) -> bool:
    """
    Controlla se un ruolo ha accesso a un dato modulo.
    Ritorna True se il modulo è nella lista dei modules del ruolo.
    """
    role = session.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return module_code in role.modules

# ---- Rotta di verifica accesso ----
@router.get("/check/{role_id}/{module_code}")
def check_access(role_id: uuid.UUID, module_code: str, session: SessionDep) -> Any:
    allowed = check_role_access(role_id, module_code, session)
    return {"role_id": role_id, "module_code": module_code, "allowed": allowed}
