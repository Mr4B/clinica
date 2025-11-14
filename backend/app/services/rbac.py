# app/utils/rbac.py
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User, Role, Dossier, Structure
from typing import Literal

from sqlmodel import Session
from uuid import UUID

ActionType = Literal["READ", "CREATE", "UPDATE", "DELETE"]

def check_module_access(
    session: Session,
    user: User,
    module_code: str,
    action: ActionType = "READ"
) -> Role:
    """
    Verifica che l'utente abbia accesso al modulo specificato.
    Ritorna il ruolo se ha accesso, altrimenti solleva HTTPException.
    
    Args:
        session: Sessione database
        user: Utente corrente
        module_code: Codice del modulo (es. "ROG26/1.1")
        action: Tipo di operazione
        
    Returns:
        Role: Il ruolo dell'utente
        
    Raises:
        HTTPException: Se l'utente non ha accesso
    """
    # Super admin bypass
    if hasattr(user, 'is_superuser') and user.is_superuser:
        return None
    
    if not user.role_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User has no role assigned"
        )
    
    role = session.get(Role, user.role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    if module_code not in (role.modules or []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"{action} access to module '{module_code}' denied for role '{role.name}'"
        )
    
    return role


def check_dossier_access(
    session: Session,
    user: User,
    dossier_id: UUID,
    action: ActionType = "READ"
) -> Dossier:
    """
    Verifica che l'utente possa accedere al dossier.
    
    Logica di accesso:
    1. Superuser: accesso totale
    2. Stessa struttura: accesso basato su action
    3. Struttura diversa: negato
    
    Args:
        session: Sessione database
        user: Utente corrente
        dossier_id: ID del dossier
        action: Tipo di operazione (READ/CREATE/UPDATE/DELETE)
        
    Returns:
        Dossier se accessibile
        
    Raises:
        HTTPException: Se dossier non trovato o accesso negato
    """
    dossier = session.get(Dossier, dossier_id)
    if not dossier:
        raise HTTPException(404, "Dossier not found")
    
    # Verifica soft delete
    if dossier.deleted_at:
        if action != "READ" or not (hasattr(user, 'is_superuser') and user.is_superuser):
            raise HTTPException(410, "Dossier has been deleted")
    
    # Superuser può tutto
    if hasattr(user, 'is_superuser') and user.is_superuser:
        return dossier
    
    # Verifica stessa struttura
    if not user.structure_id:
        raise HTTPException(403, "User not assigned to any structure")
    
    if dossier.structure_id != user.structure_id:
        raise HTTPException(
            403,
            "Cannot access dossier from different structure"
        )
    
    # Verifica permessi per azione (opzionale, personalizza)
    # Es: alcuni ruoli possono solo leggere, non modificare
    # !Questa cosa per ora la rimuoviamo
    # if action in ["UPDATE", "DELETE"]:
    #     role = session.get(Role, user.role_id) if user.role_id else None
    #     if role and hasattr(role, 'can_edit_dossiers'):
    #         if not role.can_edit_dossiers:
    #             raise HTTPException(403, f"Role '{role.name}' cannot {action} dossiers")
    
    return dossier


def check_structure_access(
    session: Session,
    user: User,
    structure_id: UUID
) -> Structure:
    """
    Verifica che l'utente possa accedere alla struttura.
    
    Logica:
    1. Superuser: può vedere tutte le strutture
    2. User normale: solo la propria struttura
    """
    structure = session.get(Structure, structure_id)
    if not structure:
        raise HTTPException(404, "Structure not found")
    
    if structure.deleted_at:
        raise HTTPException(410, "Structure has been deleted")
    
    # Superuser può vedere tutto
    if hasattr(user, 'is_superuser') and user.is_superuser:
        return structure
    
    # User normale: solo la propria struttura
    if user.structure_id != structure_id:
        raise HTTPException(403, "Cannot access this structure")
    
    return structure


"""
    
    from app.utils.rbac import check_module_access

@router.post("/entries")
async def create_entry(
    payload: dict,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session)
):
    try:
        code = payload["module_code"]
        data = payload["data"]
        dossier_id = payload["dossier_id"]
    except KeyError as e:
        raise HTTPException(400, f"Missing required field: {e}")
    
    # ✅ Controllo RBAC in una riga
    await check_module_access(session, current_user, code, "CREATE")
"""