# app/utils/audit.py
from sqlalchemy import event, inspect
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import AuditLog
from app.models import User
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Optional
import json

# Context var per tracciare utente corrente nella request
current_user_context: ContextVar[dict] = ContextVar('current_user_context', default={})

def set_audit_context(
    user_id: str, 
    username: str, 
    ip: str = None, 
    endpoint: str = None
):
    """Chiamata dal middleware all'inizio di ogni request"""
    current_user_context.set({
        "user_id": user_id,
        "username": username,
        "ip_address": ip,
        "endpoint": endpoint
    })

def get_audit_context() -> dict:
    return current_user_context.get({})

def serialize_model(instance) -> dict:
    """Serializza un modello SQLAlchemy in dict"""
    result = {}
    mapper = inspect(instance.__class__)
    for column in mapper.columns:
        value = getattr(instance, column.name)
        
        # Gestisci tipi non serializzabili
        if isinstance(value, datetime):
            value = value.isoformat()
        elif isinstance(value, bytes):
            value = "<binary data>"
        elif hasattr(value, '__str__') and not isinstance(value, (str, int, float, bool, type(None))):
            value = str(value)
        
        # NON loggare dati sensibili crittografati
        if column.name in ['_data_encrypted', 'password', 'hashed_password']:
            value = "<encrypted>"
        
        result[column.name] = value
    return result

async def log_read_access(
    session: AsyncSession,
    table_name: str,
    record_id: str,
    user: User,
    request_info: dict
):
    """Log manuale per accessi in lettura"""
    audit = AuditLog(
        user_id=str(user.id),
        username=user.username,  # adatta al tuo User model
        action='READ',
        table_name=table_name,
        record_id=str(record_id),
        before=None,
        after=None,
        ip_address=request_info.get('ip'),
        endpoint=request_info.get('endpoint')
    )
    session.add(audit)
    # Non fare commit, sarà fatto dal chiamante

def setup_audit_listeners(models_to_audit: list):
    """Registra listener per tutti i modelli specificati"""
    
    for model in models_to_audit:
        
        @event.listens_for(model, 'after_insert')
        def audit_insert(mapper, connection, target):
            context = get_audit_context()
            if not context:  # Se non c'è contesto (es. script batch), skippa
                return
                
            connection.execute(
                AuditLog.__table__.insert().values(
                    ts=datetime.now(timezone.utc),
                    user_id=context.get('user_id'),
                    username=context.get('username'),
                    action='CREATE',
                    table_name=target.__tablename__,
                    record_id=str(getattr(target, 'id', 'unknown')),
                    before=None,
                    after=serialize_model(target),
                    ip_address=context.get('ip_address'),
                    endpoint=context.get('endpoint')
                )
            )
        
        @event.listens_for(model, 'after_update')
        def audit_update(mapper, connection, target):
            context = get_audit_context()
            if not context:
                return
                
            state = inspect(target)
            before_data = {}
            
            for attr in state.attrs:
                hist = attr.load_history()
                if hist.has_changes():
                    old_val = hist.deleted[0] if hist.deleted else None
                    # Serializza il valore precedente
                    if isinstance(old_val, datetime):
                        old_val = old_val.isoformat()
                    before_data[attr.key] = old_val
            
            connection.execute(
                AuditLog.__table__.insert().values(
                    ts=datetime.now(timezone.utc),
                    user_id=context.get('user_id'),
                    username=context.get('username'),
                    action='UPDATE',
                    table_name=target.__tablename__,
                    record_id=str(getattr(target, 'id', 'unknown')),
                    before=before_data if before_data else None,
                    after=serialize_model(target),
                    ip_address=context.get('ip_address'),
                    endpoint=context.get('endpoint')
                )
            )
        
        @event.listens_for(model, 'after_delete')
        def audit_delete(mapper, connection, target):
            context = get_audit_context()
            if not context:
                return
                
            connection.execute(
                AuditLog.__table__.insert().values(
                    ts=datetime.now(timezone.utc),
                    user_id=context.get('user_id'),
                    username=context.get('username'),
                    action='DELETE',
                    table_name=target.__tablename__,
                    record_id=str(getattr(target, 'id', 'unknown')),
                    before=serialize_model(target),
                    after=None,
                    ip_address=context.get('ip_address'),
                    endpoint=context.get('endpoint')
                )
            )
            
            
# Esempio di utilizzo:
"""
@router.post("/entries")
async def upsert_entry(
    payload: dict,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session)
):
    ""
    Crea un nuovo entry - l'audit è automatico tramite listener
    ""
    try:
        code = payload["module_code"]
        data = payload["data"]
        dossier_id = payload["dossier_id"]
    except KeyError as e:
        raise HTTPException(400, f"Missing required field: {e}")
    
    version = payload.get("schema_version") or DEFAULT_VERSION.get(code)
    if version is None or (code, version) not in REGISTRY:
        raise HTTPException(400, f"Unknown schema for {code} v{version}")
    
    # Validazione con Pydantic
    Model = REGISTRY[(code, version)]
    validated = Model(**data)
    
    # Crea entry (data viene crittografato automaticamente)
    entry = models.ModuleEntry(
        dossier_id=dossier_id,
        module_code=code,
        schema_version=version,
        occurred_at=payload.get("occurred_at") or datetime.now(timezone.utc),
        data=validated.model_dump()  # ← crittografato in automatico dal setter
    )
    
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    
    # L'audit log CREATE è stato creato automaticamente dal listener!
    
    return {
        "id": str(entry.id),
        "module_code": code,
        "schema_version": version,
        "created_at": entry.created_at.isoformat()
    }


@router.get("/entries/{entry_id}")
async def get_entry(
    entry_id: UUID,
    current_user: CurrentUser,
    request_info: RequestInfo,
    session: AsyncSession = Depends(get_session)
):
    ""
    Legge un entry - audit manuale per READ
    ""
    entry = await session.get(models.ModuleEntry, entry_id)
    if not entry:
        raise HTTPException(404, detail="Entry not found")
    
    # Verifica permessi (esempio: solo dossier dell'utente o ruolo admin)
    # if entry.dossier.user_id != current_user.id and not current_user.is_admin:
    #     raise HTTPException(403, detail="Access denied")
    
    # Log accesso in lettura
    await log_read_access(
        session=session,
        table_name="module_entries",
        record_id=str(entry_id),
        user=current_user,
        request_info=request_info
    )
    await session.commit()
    
    return {
        "id": str(entry.id),
        "dossier_id": str(entry.dossier_id),
        "module_code": entry.module_code,
        "schema_version": entry.schema_version,
        "occurred_at": entry.occurred_at.isoformat(),
        "data": entry.data,  # ← decrittografato automaticamente dal getter
        "created_at": entry.created_at.isoformat()
    }

"""