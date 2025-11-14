# app/routers/modules_dynamic.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import select, func, and_
from app.api.deps import (
    SessionDep,
    CurrentUser,
    RequestInfo,
)
from app.models import ( ModuleEntry, Role, EntryCreate, EntryResponse, EntryListResponse, EntryUpdate, ModuleInfo,
    ModuleCatalog, ModuleCatalogCreate, ModuleCatalogUpdate, ModuleCatalogResponse, ModuleCatalogListResponse)
from app.services.module_service import ModuleService
from app.module_registry import REGISTRY
from app.services.audit import log_read_access
from app.services.rbac import check_module_access, check_dossier_access
from datetime import datetime, timezone, date
from uuid import UUID
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/modules", tags=["modules"])

#!Sezione dei catalogi

# =========================================================
# CREATE MODULE
# =========================================================

@router.post("/catalogs", response_model=ModuleCatalogResponse, status_code=status.HTTP_201_CREATED) #Per ora il post non lo mettiamo
def create_module(
    data: ModuleCatalogCreate,
    session: SessionDep,
    current_user: CurrentUser,
):
    existing = session.exec(select(ModuleCatalog).where(ModuleCatalog.code == data.code)).first()
    if existing:
        raise HTTPException(400, f"Module with code '{data.code}' already exists")

    obj = ModuleCatalog(**data.model_dump())
    obj.updated_at = date.today()

    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


# =========================================================
# GET SINGLE MODULE
# =========================================================
@router.get("/catalogs/{module_id}", response_model=ModuleCatalogResponse)
def get_module(module_id: int, session: SessionDep, current_user: CurrentUser):
    obj = session.get(ModuleCatalog, module_id)
    if not obj:
        raise HTTPException(404, "Module not found")
    return obj


# =========================================================
# LIST MODULES
# =========================================================
@router.get("/catalogs", response_model=ModuleCatalogListResponse)
def list_modules(
    session: SessionDep,
    current_user: CurrentUser,
    q: str | None = Query(None, description="Filtro per codice o nome"),
    active_only: bool = Query(False, description="Mostra solo moduli attivi"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
):
    stmt = select(ModuleCatalog)
    if active_only:
        stmt = stmt.where(ModuleCatalog.active.is_(True))
    if q:
        qlike = f"%{q.lower()}%"
        stmt = stmt.where(
            func.lower(ModuleCatalog.code).like(qlike)
            | func.lower(ModuleCatalog.name).like(qlike)
        )

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = session.exec(count_stmt).one()

    stmt = stmt.order_by(ModuleCatalog.code.asc()).offset((page - 1) * page_size).limit(page_size)
    items = session.exec(stmt).all()

    return ModuleCatalogListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total,
    )


# =========================================================
# UPDATE MODULE
# =========================================================
@router.patch("/catalogs/{module_id}", response_model=ModuleCatalogResponse)
def update_module(
    module_id: int,
    data: ModuleCatalogUpdate,
    session: SessionDep,
    current_user: CurrentUser,
):
    obj = session.get(ModuleCatalog, module_id)
    if not obj:
        raise HTTPException(404, "Module not found")

    update_data = data.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(obj, k, v)

    obj.updated_at = date.today()

    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


# =========================================================
# DELETE MODULE
# =========================================================
@router.delete("/catalogs/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_module(module_id: int, session: SessionDep, current_user: CurrentUser):
    obj = session.get(ModuleCatalog, module_id)
    if not obj:
        raise HTTPException(404, "Module not found")
    session.delete(obj)
    session.commit()
    return None

#!Sezione delle singole entries

# ============================================================================
# CREATE - Crea nuova entry
# ============================================================================

@router.post("/entries", response_model=EntryResponse, status_code=status.HTTP_201_CREATED)
def create_entry(
    entry_data: EntryCreate,
    current_user: CurrentUser,
    session: SessionDep
):
    """
    Crea una nuova entry di modulo.
    
    **Controlli effettuati:**
    - Dossier esistente e accessibile
    - Permessi RBAC sul modulo (CREATE)
    - Validazione dati con schema Pydantic
    - Crittografia automatica campo data
    - Tracciamento in audit log
    
    **Returns:**
    - Entry creata con dati crittografati
    """
    
    # ✅ Verifica accesso al dossier
    check_dossier_access(session, current_user, entry_data.dossier_id)
    
    # ✅ Controllo RBAC: può l'utente creare questo tipo di modulo?
    check_module_access(session, current_user, entry_data.module_code, "CREATE")
    
    # ✅ Determina versione schema
    version = entry_data.schema_version or REGISTRY.get(entry_data.module_code)
    if version is None:
        raise HTTPException(400, f"No default version for module '{entry_data.module_code}'")
    
    # ✅ Validazione dati con ModuleService
    try:
        validated_data = ModuleService.validate_payload(
            module_code=entry_data.module_code,
            version=version,
            payload=entry_data.data
        )
    except ValueError as e:
        raise HTTPException(400, f"Schema validation failed: {str(e)}")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Data validation failed: {str(e)}"
        )
        
    validated_dict = validated_data.model_dump() if validated_data else {}
    # print(f"DEBUG validated_dict: {validated_dict}")
    
    entry = ModuleEntry(
        dossier_id=entry_data.dossier_id,
        module_code=entry_data.module_code,
        schema_version=version,
        occurred_at=entry_data.occurred_at or datetime.now(timezone.utc),
        created_by_user_id=current_user.id
    )
    
    # ✅ USA IL METODO set_data() invece di assegnazione diretta
    entry.set_data(validated_dict)
    
    # print(f"DEBUG data_encrypted: {entry.data_encrypted[:100] if entry.data_encrypted else None}")
    # if entry.data_encrypted is None:
    #     raise ValueError("data_encrypted is None after set_data()!")
    
    session.add(entry)
    session.commit()
    session.refresh(entry)
    
    # Audit log CREATE è gestito automaticamente dal listener
    
    return entry


# ============================================================================
# READ - Leggi singola entry
# ============================================================================

@router.get("/entries/{entry_id}", response_model=EntryResponse)
def get_entry(
    entry_id: UUID,
    current_user: CurrentUser,
    request_info: RequestInfo,
    session: SessionDep,
    target_version: Optional[int] = Query(None, description="Converti a versione specifica")
):
    """
    Recupera una singola entry.
    
    **Funzionalità:**
    - Decripta automaticamente dati
    - Verifica permessi RBAC (READ)
    - Opzionale: conversione a versione diversa (non salva)
    - Traccia accesso in audit log
    
    **Query Parameters:**
    - `target_version`: Se specificato, converte l'entry a quella versione (solo in memoria)
    """
    
    # Recupera entry
    entry = session.get(ModuleEntry, entry_id)
    if not entry:
        raise HTTPException(404, "Entry not found")
    
    # Verifica soft delete
    if entry.deleted_at:
        raise HTTPException(410, "Entry has been deleted")
    
    # ✅ Verifica accesso al dossier
    check_dossier_access(session, current_user, entry.dossier_id)
    
    # ✅ Controllo RBAC
    check_module_access(session, current_user, entry.module_code, "READ")
    
    # ✅ Conversione versione (se richiesta) - solo in memoria
    if target_version and target_version != entry.schema_version:
        try:
            converted_data = ModuleService.migrate_to_version(
                module_code=entry.module_code,
                from_version=entry.schema_version,
                to_version=target_version,
                data=entry.data
            )
            # Crea entry temporanea con versione convertita
            entry_dict = {
                "id": entry.id,
                "dossier_id": entry.dossier_id,
                "module_code": entry.module_code,
                "schema_version": target_version,
                "occurred_at": entry.occurred_at,
                "data": converted_data,
                "created_at": entry.created_at,
                "created_by_user_id": entry.created_by_user_id,
                "deleted_at": entry.deleted_at
            }
            return EntryResponse(**entry_dict)
        except ValueError as e:
            raise HTTPException(400, f"Version conversion failed: {str(e)}")
    
    # ✅ Log accesso READ
    log_read_access(
        session=session,
        table_name="module_entries",
        record_id=str(entry_id),
        user=current_user,
        request_info=request_info
    )
    session.commit()
    
    return entry


# ============================================================================
# LIST - Lista entries con filtri avanzati
# ============================================================================

@router.get("/entries", response_model=EntryListResponse)
def list_entries(
    current_user: CurrentUser,
    session: SessionDep,
    dossier_id: Optional[UUID] = Query(None, description="Filtra per dossier"),
    module_code: Optional[str] = Query(None, description="Filtra per modulo"),
    from_date: Optional[date] = Query(None, description="Data minima (occurred_at)"),
    to_date: Optional[date] = Query(None, description="Data massima (occurred_at)"),
    page: int = Query(1, ge=1, description="Numero pagina"),
    page_size: int = Query(50, ge=1, le=100, description="Elementi per pagina"),
    include_deleted: bool = Query(False, description="Includi entry cancellate")
):
    """
    Lista entries con filtri multipli e paginazione.
    
    **Filtri disponibili:**
    - `dossier_id`: Filtra per dossier specifico
    - `module_code`: Filtra per tipo modulo
    - `from_date` / `to_date`: Range temporale
    - `include_deleted`: Include entry soft-deleted
    
    **Paginazione:**
    - `page`: Numero pagina (default 1)
    - `page_size`: Elementi per pagina (max 100)
    """
    
    # ✅ Se specificato module_code, verifica permessi
    if module_code:
        check_module_access(session, current_user, module_code, "READ")
    
    # ✅ Se specificato dossier, verifica accesso
    if dossier_id:
        check_dossier_access(session, current_user, dossier_id)
    
    # Costruisci query base
    stmt = select(ModuleEntry)
    
    # Filtro dossier
    if dossier_id:
        stmt = stmt.where(ModuleEntry.dossier_id == dossier_id)
    
    # Filtro modulo
    if module_code:
        stmt = stmt.where(ModuleEntry.module_code == module_code)
    else:
        # Mostra solo moduli per cui ha permesso READ
        role = session.get(Role, current_user.role_id) if current_user.role_id else None
        if role and role.modules:
            stmt = stmt.where(ModuleEntry.module_code.in_(role.modules))
        else:
            # Nessun permesso
            return EntryListResponse(
                items=[], 
                total=0, 
                page=page, 
                page_size=page_size, 
                has_next=False
            )
    
    # Filtro date
    if from_date:
        stmt = stmt.where(
            ModuleEntry.occurred_at >= datetime.combine(from_date, datetime.min.time())
        )
    if to_date:
        stmt = stmt.where(
            ModuleEntry.occurred_at <= datetime.combine(to_date, datetime.max.time())
        )
    
    # Filtro soft delete
    if not include_deleted:
        stmt = stmt.where(ModuleEntry.deleted_at.is_(None))
    
    # Count totale
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = session.exec(count_stmt).one()
    
    # Paginazione e ordinamento
    stmt = stmt.order_by(ModuleEntry.occurred_at.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    
    entries = session.exec(stmt).all()
    
    return EntryListResponse(
        items=entries,
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total
    )


# ============================================================================
# UPDATE - Aggiorna entry esistente ! in teoria non verrà mai utilizzata
# ============================================================================

@router.patch("/entries/{entry_id}", response_model=EntryResponse)
def update_entry(
    entry_id: UUID,
    entry_data: EntryUpdate,
    current_user: CurrentUser,
    session: SessionDep
):
    """
    Aggiorna una entry esistente.
    
    **Operazioni:**
    - Verifica permessi RBAC (UPDATE)
    - Ri-valida dati con schema Pydantic
    - Cripta automaticamente nuovi dati
    - Traccia modifica in audit log (before/after)
    
    **Note:**
    - Non modifica `schema_version` (usa endpoint `/upgrade-version`)
    - Mantiene storia modifiche in audit log
    """
    
    # Recupera entry
    entry = session.get(ModuleEntry, entry_id)
    if not entry:
        raise HTTPException(404, "Entry not found")
    
    # Verifica soft delete
    if entry.deleted_at:
        raise HTTPException(410, "Cannot update deleted entry")
    
    # ✅ Verifica accesso al dossier
    check_dossier_access(session, current_user, entry.dossier_id)
    
    # ✅ Controllo RBAC
    check_module_access(session, current_user, entry.module_code, "UPDATE")
    
    # ✅ Se aggiorna dati, ri-valida con schema
    if entry_data.data is not None:
        try:
            validated_data = ModuleService.validate_payload(
                module_code=entry.module_code,
                version=entry.schema_version,
                payload=entry_data.data
            )
            entry.data = validated_data.model_dump()
        except ValueError as e:
            raise HTTPException(400, f"Schema validation failed: {str(e)}")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Data validation failed: {str(e)}"
            )
    
    # ✅ Aggiorna occurred_at se fornito
    if entry_data.occurred_at is not None:
        entry.occurred_at = entry_data.occurred_at
        
    session.add(entry)
    session.commit()
    session.refresh(entry)
    
    # Audit log UPDATE è gestito automaticamente dal listener
    
    return entry


# ============================================================================
# UPGRADE VERSION - Aggiorna versione schema
# ============================================================================

@router.post("/entries/{entry_id}/upgrade-version", response_model=EntryResponse)
def upgrade_entry_version(
    entry_id: UUID,
    current_user: CurrentUser,
    session: SessionDep,
    target_version: int = Query(..., description="Versione target", ge=1)
):
    """
    Aggiorna permanentemente una entry a una versione più recente dello schema.
    
    **Processo:**
    1. Verifica che target_version > versione corrente
    2. Applica migrazioni sequenziali (v1→v2→v3...)
    3. Salva permanentemente nella nuova versione
    4. Traccia upgrade in audit log
    
    **ATTENZIONE:**
    - Operazione irreversibile (no downgrade)
    - Richiede permesso UPDATE sul modulo
    """
    
    entry = session.get(ModuleEntry, entry_id)
    if not entry:
        raise HTTPException(404, "Entry not found")
    
    if entry.deleted_at:
        raise HTTPException(410, "Cannot upgrade deleted entry")
    
    # ✅ Verifica accesso
    check_dossier_access(session, current_user, entry.dossier_id)
    check_module_access(session, current_user, entry.module_code, "UPDATE")
    
    # Verifica che target_version sia maggiore
    if target_version <= entry.schema_version:
        raise HTTPException(
            400, 
            f"Target version ({target_version}) must be greater than current version ({entry.schema_version})"
        )
    
    # Verifica che target_version esista
    if (entry.module_code, target_version) not in REGISTRY:
        raise HTTPException(
            404, 
            f"Version {target_version} not found for module {entry.module_code}"
        )
    
    # ✅ Applica migrazione con ModuleService
    try:
        migrated_data = ModuleService.migrate_to_version(
            module_code=entry.module_code,
            from_version=entry.schema_version,
            to_version=target_version,
            data=entry.data
        )
    except ValueError as e:
        raise HTTPException(400, f"Migration failed: {str(e)}")
    
    # Salva permanentemente la nuova versione
    entry.schema_version = target_version
    entry.data = migrated_data
    
    session.add(entry)
    session.commit()
    session.refresh(entry)
    
    return entry


# ============================================================================
# DELETE - Soft delete entry
# ============================================================================

@router.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(
    entry_id: UUID,
    current_user: CurrentUser,
    session: SessionDep,
    hard_delete: bool = Query(
        False, 
        description="Elimina definitivamente (solo superuser)"
    )
):
    """
    Elimina una entry.
    
    **Modalità:**
    - **Soft delete** (default): Marca come cancellata, mantiene dati
    - **Hard delete**: Elimina definitivamente (solo superuser)
    
    **Tracciamento:**
    - Registra chi/quando ha eliminato
    - Audit log automatico
    """
    
    entry = session.get(ModuleEntry, entry_id)
    if not entry:
        raise HTTPException(404, "Entry not found")
    
    # ✅ Verifica accesso
    check_dossier_access(session, current_user, entry.dossier_id)
    check_module_access(session, current_user, entry.module_code, "DELETE")
    
    if hard_delete:
        # Hard delete solo per superuser
        if not current_user.is_superuser:
            raise HTTPException(403, "Hard delete requires superuser privileges")
        
        session.delete(entry)
    else:
        # Soft delete
        if entry.deleted_at:
            raise HTTPException(410, "Entry already deleted")
        
        entry.deleted_at = datetime.now(timezone.utc)
        entry.deleted_by_user_id = current_user.id
        session.add(entry)
    
    session.commit()
    
    # Audit log DELETE è gestito automaticamente dal listener
    
    return None


# ============================================================================
# RESTORE - Ripristina entry soft-deleted
# ============================================================================

@router.post("/entries/{entry_id}/restore", response_model=EntryResponse)
def restore_entry(
    entry_id: UUID,
    current_user: CurrentUser,
    session: SessionDep
):
    """
    Ripristina una entry precedentemente eliminata (soft delete).
    
    **Requisiti:**
    - Entry deve essere soft-deleted
    - Richiede permesso UPDATE sul modulo
    """
    
    entry = session.get(ModuleEntry, entry_id)
    if not entry:
        raise HTTPException(404, "Entry not found")
    
    if not entry.deleted_at:
        raise HTTPException(400, "Entry is not deleted")
    
    # ✅ Verifica accesso
    check_dossier_access(session, current_user, entry.dossier_id)
    check_module_access(session, current_user, entry.module_code, "UPDATE")
    
    # Ripristina
    entry.deleted_at = None
    entry.deleted_by_user_id = None
    
    session.add(entry)
    session.commit()
    session.refresh(entry)
    
    return entry


# ============================================================================
# INFO - Moduli disponibili per l'utente
# ============================================================================

@router.get("/available", response_model=list[ModuleInfo])
def get_available_modules(
    current_user: CurrentUser,
    session: SessionDep,
    include_schema: bool = Query(False, description="Includi schema JSON dei moduli")
):
    """
    Lista moduli disponibili per l'utente corrente.
    
    **Filtra per:**
    - Permessi RBAC dell'utente
    - Include info su versioni disponibili
    - Opzionale: schema Pydantic completo
    
    **Utile per:**
    - Popolare UI di selezione moduli
    - Validazione client-side
    - Documentazione dinamica
    """
    
    # Ottieni moduli accessibili dal ruolo
    role = session.get(Role, current_user.role_id) if current_user.role_id else None
    if not role or not role.modules:
        return []
    
    accessible_modules = role.modules
    
    # Costruisci lista moduli
    modules_dict = {}
    for (code, version) in REGISTRY.keys():
        if code not in accessible_modules:
            continue
        
        if code not in modules_dict:
            modules_dict[code] = {
                "code": code,
                "versions": [],
                "latest_version": REGISTRY.get(code, 1),
                "schema_fields": None
            }
        
        modules_dict[code]["versions"].append(version)
        
        # Aggiungi schema fields per ultima versione (se richiesto)
        if include_schema and version == modules_dict[code]["latest_version"]:
            info = REGISTRY[(code, version)]
            modules_dict[code]["schema_fields"] = info.model.model_json_schema()
    
    return list(modules_dict.values())


# ============================================================================
# STATS - Statistiche entries
# ============================================================================

@router.get("/stats/summary")
def get_entries_stats(
    current_user: CurrentUser,
    session: SessionDep,
    dossier_id: Optional[UUID] = Query(None, description="Filtra per dossier"),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None)
):
    """
    Statistiche aggregate sulle entries.
    
    **Metriche:**
    - Count per modulo
    - Totale entries
    - Distribuzione temporale
    
    **Filtri:**
    - Dossier specifico
    - Range temporale
    """
    
    # Ottieni moduli accessibili
    role = session.get(Role, current_user.role_id) if current_user.role_id else None
    if not role or not role.modules:
        return {"modules": [], "total": 0}
    
    # Query base
    stmt = select(
        ModuleEntry.module_code,
        func.count(ModuleEntry.id).label('count')
    ).where(
        ModuleEntry.module_code.in_(role.modules),
        ModuleEntry.deleted_at.is_(None)
    )
    
    # Filtri
    if dossier_id:
        check_dossier_access(session, current_user, dossier_id)
        stmt = stmt.where(ModuleEntry.dossier_id == dossier_id)
    
    if from_date:
        stmt = stmt.where(
            ModuleEntry.occurred_at >= datetime.combine(from_date, datetime.min.time())
        )
    if to_date:
        stmt = stmt.where(
            ModuleEntry.occurred_at <= datetime.combine(to_date, datetime.max.time())
        )
    
    stmt = stmt.group_by(ModuleEntry.module_code)
    
    result = session.exec(stmt).all()
    
    return {
        "modules": [{"code": code, "count": count} for code, count in result],
        "total": sum(count for _, count in result)
    }


# ============================================================================
# BULK OPERATIONS (opzionale)
# ============================================================================

class BulkCreateRequest(BaseModel):
    entries: list[EntryCreate]


@router.post("/entries/bulk", response_model=list[EntryResponse])
def bulk_create_entries(
    bulk_data: BulkCreateRequest,
    current_user: CurrentUser,
    session: SessionDep
):
    """
    Crea multiple entries in una singola transazione.
    
    **Vantaggi:**
    - Performance migliori per inserimenti multipli
    - Transazione atomica (tutto o niente)
    - Audit log per ogni entry
    
    **Limiti:**
    - Max 100 entries per richiesta
    """
    
    if len(bulk_data.entries) > 100:
        raise HTTPException(400, "Max 100 entries per bulk request")
    
    created_entries = []
    
    for entry_data in bulk_data.entries:
        # Riusa logica del CREATE singolo
        check_dossier_access(session, current_user, entry_data.dossier_id)
        check_module_access(session, current_user, entry_data.module_code, "CREATE")
        
        version = entry_data.schema_version or REGISTRY.get(entry_data.module_code)
        if version is None:
            raise HTTPException(400, f"No default version for module '{entry_data.module_code}'")
        
        try:
            validated_data = ModuleService.validate_payload(
                module_code=entry_data.module_code,
                version=version,
                payload=entry_data.data
            )
        except Exception as e:
            session.rollback()
            raise HTTPException(422, f"Validation failed for entry: {str(e)}")
        
        entry = ModuleEntry(
            dossier_id=entry_data.dossier_id,
            module_code=entry_data.module_code,
            schema_version=version,
            occurred_at=entry_data.occurred_at or datetime.now(timezone.utc),
            data=validated_data.model_dump(),
            created_by_user_id=current_user.id
        )
        
        session.add(entry)
        created_entries.append(entry)
    
    # Commit unico per tutte le entries
    session.commit()
    
    # Refresh tutte
    for entry in created_entries:
        session.refresh(entry)
    
    return created_entries