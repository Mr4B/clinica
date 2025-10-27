# app/routers/dossiers.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select, func, or_, SQLModel
from app.api.deps import SessionDep, CurrentUser, RequestInfo
from app.models import Dossier, Patient, Structure, ModuleEntry, User
from app.models import (
    DossierCreate,
    DossierUpdate,
    DossierResponse,
    DossierDetailResponse,
    DossierListResponse
)
from app.services.rbac import check_dossier_access, check_structure_access
from app.services.audit import log_read_access
from datetime import datetime, timezone, date
from uuid import UUID
from typing import Optional

router = APIRouter(prefix="/dossiers", tags=["dossiers"])


# ============================================================================
# CREATE DOSSIER
# ============================================================================

@router.post("", response_model=DossierResponse, status_code=status.HTTP_201_CREATED)
def create_dossier(
    dossier_data: DossierCreate,
    session: SessionDep,
    current_user: CurrentUser
):
    """
    Crea un nuovo dossier per un paziente.
    
    **Controlli:**
    - Paziente deve esistere
    - Struttura deve esistere e utente deve averne accesso
    - Non ci devono essere dossier attivi per stesso paziente/struttura
    
    **Permessi:**
    - Utente deve appartenere alla struttura
    - O essere superuser
    """
    
    # ✅ Verifica paziente esiste
    patient = session.get(Patient, dossier_data.patient_id)
    if not patient:
        raise HTTPException(404, "Patient not found")
    if patient.deleted_at:
        raise HTTPException(410, "Patient has been deleted")
    
    # ✅ Verifica struttura e accesso
    check_structure_access(session, current_user, dossier_data.structure_id)
    
    # ✅ Verifica che non esista già dossier attivo
    stmt = select(Dossier).where(
        Dossier.patient_id == dossier_data.patient_id,
        Dossier.structure_id == dossier_data.structure_id,
        Dossier.status == "active",
        Dossier.deleted_at.is_(None)
    )
    existing = session.exec(stmt).first()
    if existing:
        raise HTTPException(
            400,
            f"Active dossier already exists for this patient in this structure (ID: {existing.id})"
        )
    
    # ✅ Crea dossier
    dossier = Dossier(
        **dossier_data.model_dump(),
        created_by_user_id=current_user.id
    )
    
    session.add(dossier)
    session.commit()
    session.refresh(dossier)
    
    return dossier


# ============================================================================
# READ SINGLE DOSSIER
# ============================================================================

@router.get("/{dossier_id}", response_model=DossierDetailResponse)
def get_dossier(
    dossier_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
    request_info: RequestInfo,
    include_patient: bool = Query(False, description="Include patient data")
):
    """
    Recupera un singolo dossier con dettagli.
    
    **Include:**
    - Dati base dossier
    - Count entries
    - Data ultima entry
    - Opzionale: dati paziente
    """
    
    # ✅ Verifica accesso
    dossier = check_dossier_access(session, current_user, dossier_id, "READ")
    
    # ✅ Conta entries
    entries_stmt = select(func.count(ModuleEntry.id)).where(
        ModuleEntry.dossier_id == dossier_id,
        ModuleEntry.deleted_at.is_(None)
    )
    entries_count = session.exec(entries_stmt).one()
    
    # ✅ Ultima entry
    last_entry_stmt = select(ModuleEntry.occurred_at).where(
        ModuleEntry.dossier_id == dossier_id,
        ModuleEntry.deleted_at.is_(None)
    ).order_by(ModuleEntry.occurred_at.desc()).limit(1)
    last_entry_date = session.exec(last_entry_stmt).first()
    
    # ✅ Patient data (se richiesto)
    patient_data = None
    if include_patient:
        patient = session.get(Patient, dossier.patient_id)
        patient_data = patient
    
    # ✅ Log accesso
    log_read_access(
        session=session,
        table_name="dossier",
        record_id=str(dossier_id),
        user=current_user,
        request_info=request_info
    )
    session.commit()
    
    response_data = dossier.model_dump()
    response_data["entries_count"] = entries_count
    response_data["last_entry_date"] = last_entry_date
    if include_patient:
        response_data["patient"] = patient_data
    
    return DossierDetailResponse(**response_data)


# ============================================================================
# LIST DOSSIERS
# ============================================================================

@router.get("", response_model=DossierListResponse)
def list_dossiers(
    session: SessionDep,
    current_user: CurrentUser,
    utente: Optional[str] = Query(None, description="Filtra per utente"),
    structure_id: Optional[UUID] = Query(None, description="Filtra per struttura"),
    patient_id: Optional[UUID] = Query(None, description="Filtra per paziente"),
    status: Optional[str] = Query(None, description="Filtra per status (active/discharged/transferred)"),
    from_admission: Optional[date] = Query(None, description="Data ammissione minima"),
    to_admission: Optional[date] = Query(None, description="Data ammissione massima"),
    from_discharge: Optional[date] = Query(None, description="Data dimissione minima"),
    to_discharge: Optional[date] = Query(None, description="Data dimissione massima"),
    include_discharged: bool = Query(True, description="Includi dimessi"),
    include_deleted: bool = Query(False, description="Includi soft-deleted"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
):
    """
    Lista dossiers con filtri multipli.
    
    **Filtri:**
    - Struttura (se non superuser, solo la propria)
    - Paziente
    - Status
    - Range date ammissione/dimissione
    """
    
    # ✅ Base query
    stmt = select(Dossier)
    
    # ✅ Filtro struttura
    if structure_id:
        check_structure_access(session, current_user, structure_id)
        stmt = stmt.where(Dossier.structure_id == structure_id)
    elif not (hasattr(current_user, 'is_superuser') and current_user.is_superuser):
        # Non-superuser: solo la propria struttura
        if not current_user.structure_id:
            raise HTTPException(403, "User not assigned to any structure")
        stmt = stmt.where(Dossier.structure_id == current_user.structure_id)
    
    # ✅ Filtro paziente
    if patient_id:
        stmt = stmt.where(Dossier.patient_id == patient_id)
        
    # ✅ Filtro utente
    if utente:
        stmt = stmt.where(Dossier.utente == utente)
    
    # ✅ Filtro status
    # if status:
    #     stmt = stmt.where(Dossier.status == status)
    # elif not include_discharged:
    #     stmt = stmt.where(Dossier.status == "active")
    
    # ✅ Filtro date ammissione
    if from_admission:
        stmt = stmt.where(Dossier.admission_date >= datetime.combine(from_admission, datetime.min.time()))
    if to_admission:
        stmt = stmt.where(Dossier.admission_date <= datetime.combine(to_admission, datetime.max.time()))
    
    # ✅ Filtro date dimissione
    if from_discharge:
        stmt = stmt.where(Dossier.discharge_date >= datetime.combine(from_discharge, datetime.min.time()))
    if to_discharge:
        stmt = stmt.where(Dossier.discharge_date <= datetime.combine(to_discharge, datetime.max.time()))
    
    # ✅ Filtro soft delete
    if not include_deleted:
        stmt = stmt.where(Dossier.deleted_at.is_(None))
    
    # Count totale
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = session.exec(count_stmt).one()
    
    # Paginazione
    stmt = stmt.order_by(Dossier.admission_date.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    
    dossiers = session.exec(stmt).all()
    
    return DossierListResponse(
        items=dossiers,
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total
    )


# ============================================================================
# UPDATE DOSSIER
# ============================================================================

@router.patch("/{dossier_id}", response_model=DossierResponse)
def update_dossier(
    dossier_id: UUID,
    dossier_data: DossierUpdate,
    session: SessionDep,
    current_user: CurrentUser
):
    """
    Aggiorna un dossier esistente.
    
    **Campi modificabili:**
    - Date ammissione/dimissione
    - Status
    - Diagnosi principale
    - Motivo ammissione/dimissione
    - Note
    """
    
    # ✅ Verifica accesso
    dossier = check_dossier_access(session, current_user, dossier_id, "UPDATE")
    
    # ✅ Validazione date
    if dossier_data.discharge_date:
        admission = dossier_data.admission_date or dossier.admission_date
        if dossier_data.discharge_date < admission:
            raise HTTPException(400, "Discharge date cannot be before admission date")
    
    # ✅ Validazione status
    # if dossier_data.status:
    #     valid_statuses = ["active", "discharged", "transferred"]
    #     if dossier_data.status not in valid_statuses:
    #         raise HTTPException(400, f"Status must be one of: {valid_statuses}")
        
    #     # Se status diventa "discharged" o "transferred", richiedi discharge_date
    #     if dossier_data.status in ["discharged", "transferred"]:
    #         if not dossier_data.discharge_date and not dossier.discharge_date:
    #             raise HTTPException(400, f"Discharge date required when status is '{dossier_data.status}'")
    
    # ✅ Applica modifiche
    update_data = dossier_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(dossier, field, value)
    
    # Traccia modifica
    dossier.updated_at = datetime.now(timezone.utc)
    dossier.updated_by_user_id = current_user.id
    
    session.add(dossier)
    session.commit()
    session.refresh(dossier)
    
    return dossier


# ============================================================================
# DELETE DOSSIER (Soft delete)
# ============================================================================

@router.delete("/{dossier_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dossier(
    dossier_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
    hard_delete: bool = Query(False, description="Elimina definitivamente (solo superuser)")
):
    """
    Elimina un dossier.
    
    **Modalità:**
    - Soft delete (default): Marca come cancellato
    - Hard delete: Elimina definitivamente (solo superuser)
    
    **ATTENZIONE:**
    - Elimina anche tutte le entries associate (cascade)
    """
    
    # ✅ Verifica accesso
    dossier = check_dossier_access(session, current_user, dossier_id, "DELETE")
    
    if hard_delete:
        # Hard delete solo per superuser
        if not current_user.is_superuser:
            raise HTTPException(403, "Hard delete requires superuser privileges")
        
        # Elimina anche entries associate
        entries_stmt = select(ModuleEntry).where(ModuleEntry.dossier_id == dossier_id)
        entries = session.exec(entries_stmt).all()
        for entry in entries:
            session.delete(entry)
        
        session.delete(dossier)
    else:
        # Soft delete
        if dossier.deleted_at:
            raise HTTPException(410, "Dossier already deleted")
        
        dossier.deleted_at = datetime.now(timezone.utc)
        dossier.deleted_by_user_id = current_user.id
        
        # Soft delete anche entries associate
        entries_stmt = select(ModuleEntry).where(
            ModuleEntry.dossier_id == dossier_id,
            ModuleEntry.deleted_at.is_(None)
        )
        entries = session.exec(entries_stmt).all()
        for entry in entries:
            entry.deleted_at = datetime.now(timezone.utc)
            entry.deleted_by_user_id = current_user.id
            session.add(entry)
        
        session.add(dossier)
    
    session.commit()
    return None


# ============================================================================
# RESTORE DOSSIER
# ============================================================================

@router.post("/{dossier_id}/restore", response_model=DossierResponse)
def restore_dossier(
    dossier_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
    restore_entries: bool = Query(True, description="Ripristina anche le entries")
):
    """
    Ripristina un dossier soft-deleted.
    
    **Opzioni:**
    - `restore_entries`: Se true, ripristina anche tutte le entries associate
    """
    
    dossier = session.get(Dossier, dossier_id)
    if not dossier:
        raise HTTPException(404, "Dossier not found")
    
    if not dossier.deleted_at:
        raise HTTPException(400, "Dossier is not deleted")
    
    # ✅ Verifica accesso alla struttura
    check_structure_access(session, current_user, dossier.structure_id)
    
    # Ripristina dossier
    dossier.deleted_at = None
    dossier.deleted_by_user_id = None
    dossier.updated_at = datetime.now(timezone.utc)
    dossier.updated_by_user_id = current_user.id
    
    # Ripristina entries se richiesto
    if restore_entries:
        entries_stmt = select(ModuleEntry).where(
            ModuleEntry.dossier_id == dossier_id,
            ModuleEntry.deleted_at.is_not(None)
        )
        entries = session.exec(entries_stmt).all()
        for entry in entries:
            entry.deleted_at = None
            entry.deleted_by_user_id = None
            entry.updated_at = datetime.now(timezone.utc)
            entry.updated_by_user_id = current_user.id
            session.add(entry)
    
    session.add(dossier)
    session.commit()
    session.refresh(dossier)
    
    return dossier


# ============================================================================
# DISCHARGE DOSSIER (Dimissione)
# ============================================================================

@router.post("/{dossier_id}/discharge", response_model=DossierResponse)
def discharge_dossier(
    dossier_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
    discharge_date: datetime = Query(..., description="Data dimissione"),
    discharge_reason: Optional[str] = Query(None, description="Motivo dimissione")
):
    """
    Dimetti un paziente (imposta status=discharged).
    
    **Operazioni:**
    - Imposta discharge_date
    - Imposta status = "discharged"
    - Opzionale: discharge_reason
    
    **Validazioni:**
    - Dossier deve essere attivo
    - Discharge date >= admission date
    """
    
    # ✅ Verifica accesso
    dossier = check_dossier_access(session, current_user, dossier_id, "UPDATE")
    
    # Validazioni
    # if dossier.status != "active":
    #     raise HTTPException(400, f"Cannot discharge: dossier status is '{dossier.status}'")
    
    if discharge_date < dossier.admission_date:
        raise HTTPException(400, "Discharge date cannot be before admission date")
    
    # Applica dimissione
    dossier.discharge_date = discharge_date
    dossier.updated_at = datetime.now(timezone.utc)
    dossier.updated_by_user_id = current_user.id
    
    session.add(dossier)
    session.commit()
    session.refresh(dossier)
    
    return dossier


# ============================================================================
# TRANSFER DOSSIER (Trasferimento)
# ============================================================================

class TransferRequest(SQLModel):
    target_structure_id: UUID
    transfer_date: datetime
    transfer_reason: Optional[str] = None
    discharge_current: bool = True  # Se true, dimetti dal dossier corrente


@router.post("/{dossier_id}/transfer", response_model=dict)
def transfer_dossier(
    dossier_id: UUID,
    transfer_data: TransferRequest,
    session: SessionDep,
    current_user: CurrentUser
):
    """
    Trasferisci un paziente ad altra struttura.
    
    **Operazioni:**
    1. Chiude dossier corrente (status=transferred)
    2. Crea nuovo dossier nella struttura target
    3. Copia dati rilevanti
    
    **Returns:**
    - old_dossier_id: ID dossier originale
    - new_dossier_id: ID nuovo dossier
    """
    
    # ✅ Verifica accesso dossier corrente
    current_dossier = check_dossier_access(session, current_user, dossier_id, "UPDATE")
    
    # Validazioni
    # if current_dossier.status != "active":
    #     raise HTTPException(400, f"Cannot transfer: dossier status is '{current_dossier.status}'")
    
    if transfer_data.transfer_date < current_dossier.admission_date:
        raise HTTPException(400, "Transfer date cannot be before admission date")
    
    # ✅ Verifica struttura target esiste
    target_structure = session.get(Structure, transfer_data.target_structure_id)
    if not target_structure:
        raise HTTPException(404, "Target structure not found")
    
    if target_structure.deleted_at:
        raise HTTPException(410, "Target structure has been deleted")
    
    # ✅ Chiudi dossier corrente
    if transfer_data.discharge_current:
        current_dossier.discharge_date = transfer_data.transfer_date
        current_dossier.updated_at = datetime.now(timezone.utc)
        current_dossier.updated_by_user_id = current_user.id
        session.add(current_dossier)
    
    # ✅ Crea nuovo dossier nella struttura target
    new_dossier = Dossier(
        patient_id=current_dossier.patient_id,
        structure_id=transfer_data.target_structure_id,
        admission_date=transfer_data.transfer_date,
        status="active",
        admission_reason=f"Transfer from {current_dossier.structure.name if current_dossier.structure else 'previous structure'}",
        notes=f"Transferred from dossier {current_dossier.id}",
        created_by_user_id=current_user.id
    )
    
    session.add(new_dossier)
    session.commit()
    session.refresh(new_dossier)
    
    return {
        "message": "Transfer completed successfully",
        "old_dossier_id": str(current_dossier.id),
        "new_dossier_id": str(new_dossier.id),
        "transfer_date": transfer_data.transfer_date.isoformat()
    }


# ============================================================================
# STATS - Statistiche dossier
# ============================================================================

@router.get("/stats/summary")
def get_dossier_stats(
    session: SessionDep,
    current_user: CurrentUser,
    structure_id: Optional[UUID] = Query(None),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None)
):
    """
    Statistiche aggregate sui dossier.
    
    **Metriche:**
    - Totale dossier attivi
    - Totale dimessi nel periodo
    - Media giorni degenza
    - Distribuzione per status
    """
    
    # Base query
    stmt = select(Dossier).where(Dossier.deleted_at.is_(None))
    
    # Filtro struttura
    if structure_id:
        check_structure_access(session, current_user, structure_id)
        stmt = stmt.where(Dossier.structure_id == structure_id)
    elif not current_user.is_superuser:
        if not current_user.structure_id:
            raise HTTPException(403, "User not assigned to any structure")
        stmt = stmt.where(Dossier.structure_id == current_user.structure_id)
    
    # Filtro date
    if from_date:
        stmt = stmt.where(Dossier.admission_date >= datetime.combine(from_date, datetime.min.time()))
    if to_date:
        stmt = stmt.where(Dossier.admission_date <= datetime.combine(to_date, datetime.max.time()))
    
    dossiers = session.exec(stmt).all()
    
    # Calcola statistiche
    total = len(dossiers)
    active = sum(1 for d in dossiers if d.status == "active")
    discharged = sum(1 for d in dossiers if d.status == "discharged")
    transferred = sum(1 for d in dossiers if d.status == "transferred")
    
    # Media giorni degenza per dimessi
    avg_stay_days = None
    if discharged > 0:
        total_days = sum(
            (d.discharge_date - d.admission_date).days 
            for d in dossiers 
            if d.status == "discharged" and d.discharge_date
        )
        avg_stay_days = total_days / discharged if discharged > 0 else 0
    
    return {
        "total": total,
        "by_status": {
            "active": active,
            "discharged": discharged,
            "transferred": transferred
        },
        "avg_stay_days": round(avg_stay_days, 1) if avg_stay_days else None,
        "filters_applied": {
            "structure_id": str(structure_id) if structure_id else None,
            "from_date": from_date.isoformat() if from_date else None,
            "to_date": to_date.isoformat() if to_date else None
        }
    }


# ============================================================================
# GET DOSSIER ENTRIES - Lista entries di un dossier
# ============================================================================

@router.get("/{dossier_id}/entries")
def get_dossier_entries(
    dossier_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
    module_code: Optional[str] = Query(None, description="Filtra per modulo"),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
):
    """
    Lista tutte le entries di un dossier.
    
    **Utile per:**
    - Timeline clinica del paziente
    - Report completo dossier
    - Export dati
    """
    
    # ✅ Verifica accesso
    check_dossier_access(session, current_user, dossier_id, "READ")
    
    # Query entries
    stmt = select(ModuleEntry).where(
        ModuleEntry.dossier_id == dossier_id,
        ModuleEntry.deleted_at.is_(None)
    )
    
    # Filtri
    if module_code:
        stmt = stmt.where(ModuleEntry.module_code == module_code)
    if from_date:
        stmt = stmt.where(ModuleEntry.occurred_at >= datetime.combine(from_date, datetime.min.time()))
    if to_date:
        stmt = stmt.where(ModuleEntry.occurred_at <= datetime.combine(to_date, datetime.max.time()))
    
    # Count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = session.exec(count_stmt).one()
    
    # Paginazione
    stmt = stmt.order_by(ModuleEntry.occurred_at.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    
    entries = session.exec(stmt).all()
    
    return {
        "dossier_id": str(dossier_id),
        "items": entries,
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_next": (page * page_size) < total
    }


# ============================================================================
# SEARCH - Ricerca dossier avanzata
# ============================================================================

@router.get("/search/advanced")
def search_dossiers(
    session: SessionDep,
    current_user: CurrentUser,
    q: Optional[str] = Query(None, description="Cerca per nome/cognome paziente o codice fiscale"),
    diagnosis: Optional[str] = Query(None, description="Cerca per diagnosi"),
    structure_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
):
    """
    Ricerca avanzata dossier con filtri multipli.
    
    **Ricerca per:**
    - Nome/cognome paziente
    - Codice fiscale
    - Diagnosi
    - Struttura
    - Status
    """
    
    # Base query con join Patient
    stmt = select(Dossier).join(Patient, Dossier.patient_id == Patient.id)
    
    # Filtro struttura (RBAC)
    if structure_id:
        check_structure_access(session, current_user, structure_id)
        stmt = stmt.where(Dossier.structure_id == structure_id)
    elif not current_user.is_superuser:
        if not current_user.structure_id:
            raise HTTPException(403, "User not assigned to any structure")
        stmt = stmt.where(Dossier.structure_id == current_user.structure_id)
    
    # Ricerca testo (nome, cognome, CF)
    if q:
        search_term = f"%{q.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Patient.first_name).like(search_term),
                func.lower(Patient.last_name).like(search_term),
                func.lower(Patient.fiscal_code).like(search_term)
            )
        )
    
    # Ricerca diagnosi
    if diagnosis:
        diag_term = f"%{diagnosis.lower()}%"
        stmt = stmt.where(func.lower(Dossier.primary_diagnosis).like(diag_term))
    
    # Filtro status
    if status:
        stmt = stmt.where(Dossier.status == status)
    
    # Escludi soft-deleted
    stmt = stmt.where(
        Dossier.deleted_at.is_(None),
        Patient.deleted_at.is_(None)
    )
    
    # Count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = session.exec(count_stmt).one()
    
    # Paginazione
    stmt = stmt.order_by(Dossier.admission_date.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    
    dossiers = session.exec(stmt).all()
    
    return {
        "items": dossiers,
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_next": (page * page_size) < total,
        "search_query": q
    }