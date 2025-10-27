# app/routers/patients.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select, func, or_
from app.api.deps import SessionDep, CurrentUser, RequestInfo
from app.models import Patient, Dossier, User
from app.models import (
    PatientCreate,
    PatientUpdate,
    PatientResponse,
    PatientListResponse
)
# from app.services.rbac import check_patient_access
from app.services.audit import log_read_access
from datetime import datetime, timezone, date
from uuid import UUID
from typing import Optional

router = APIRouter(prefix="/patients", tags=["patients"])


# ============================================================================
# CREATE PATIENT
# ============================================================================

@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
def create_patient(
    patient_data: PatientCreate,
    session: SessionDep,
    current_user: CurrentUser
):
    """
    Crea un nuovo paziente.
    
    **Validazioni:**
    - Codice fiscale univoco
    - Data nascita valida
    
    **Permessi:**
    - Tutti gli utenti autenticati possono creare pazienti
    """
    
    # ✅ Verifica codice fiscale univoco
    existing = session.exec(
        select(Patient).where(
            Patient.fiscal_code == patient_data.fiscal_code.upper(),
            Patient.deleted_at.is_(None)
        )
    ).first()
    
    if existing:
        raise HTTPException(
            400,
            f"Patient with fiscal code '{patient_data.fiscal_code}' already exists (ID: {existing.id})"
        )
    
    # ✅ Validazione età
    today = date.today()
    age = today.year - patient_data.date_of_birth.year
    if age < 0 or age > 120:
        raise HTTPException(400, "Invalid date of birth")
    
    # Crea paziente
    patient = Patient(
        **patient_data.model_dump(),
        created_by_user_id=current_user.id
    )
    
    session.add(patient)
    session.commit()
    session.refresh(patient)
    
    return patient


# ============================================================================
# READ SINGLE PATIENT
# ============================================================================

@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient(
    patient_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
    request_info: RequestInfo
):
    """
    Recupera un singolo paziente.
    
    **Controllo accesso:**
    - Paziente deve avere almeno un dossier nella struttura dell'utente
    - Oppure utente è superuser
    """
    
    patient = session.get(Patient, patient_id)
    if not patient:
        raise HTTPException(404, "Patient not found")
    
    # ✅ Log accesso
    log_read_access(
        session=session,
        table_name="patient",
        record_id=str(patient_id),
        user=current_user,
        request_info=request_info
    )
    session.commit()
    
    return patient


# ============================================================================
# LIST PATIENTS
# ============================================================================

@router.get("", response_model=PatientListResponse)
def list_patients(
    session: SessionDep,
    current_user: CurrentUser,
    q: Optional[str] = Query(None, description="Cerca nome/cognome/CF"),
    has_active_dossier: Optional[bool] = Query(None, description="Solo con dossier attivo"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
):
    """
    Lista pazienti accessibili all'utente.
    
    **Filtri:**
    - Ricerca testuale (nome, cognome, CF)
    - Solo con dossier attivo
    
    **RBAC:**
    - Non-superuser: solo pazienti con dossier nella propria struttura
    - Superuser: tutti i pazienti
    """
    
    # Base query
    stmt = select(Patient).where(Patient.deleted_at.is_(None))
    
    # ✅ RBAC: filtra per struttura se non superuser
    if not current_user.is_superuser:
        if not current_user.structure_id:
            raise HTTPException(403, "User not assigned to any structure")
        
        # Subquery: patient_ids con dossier nella struttura dell'utente
        dossier_subq = select(Dossier.patient_id).where(
            Dossier.structure_id == current_user.structure_id,
            Dossier.deleted_at.is_(None)
        ).distinct()
        
        stmt = stmt.where(Patient.id.in_(dossier_subq))
    
    # Ricerca testuale
    if q:
        search_term = f"%{q.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Patient.first_name).like(search_term),
                func.lower(Patient.last_name).like(search_term),
                func.lower(Patient.fiscal_code).like(search_term)
            )
        )
    
    # Filtro dossier attivo
    if has_active_dossier is not None:
        if has_active_dossier:
            active_dossier_subq = select(Dossier.patient_id).where(
                Dossier.status == "active",
                Dossier.deleted_at.is_(None)
            ).distinct()
            stmt = stmt.where(Patient.id.in_(active_dossier_subq))
        else:
            active_dossier_subq = select(Dossier.patient_id).where(
                Dossier.status == "active",
                Dossier.deleted_at.is_(None)
            ).distinct()
            stmt = stmt.where(Patient.id.not_in(active_dossier_subq))
    
    # Count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = session.exec(count_stmt).one()
    
    # Paginazione
    stmt = stmt.order_by(Patient.last_name, Patient.first_name)
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    
    patients = session.exec(stmt).all()
    
    return PatientListResponse(
        items=patients,
        total=total,
        page=page,
        page_size=page_size,
        has_next=(page * page_size) < total
    )


# ============================================================================
# UPDATE PATIENT
# ============================================================================

@router.patch("/{patient_id}", response_model=PatientResponse)
def update_patient(
    patient_id: UUID,
    patient_data: PatientUpdate,
    session: SessionDep,
    current_user: CurrentUser
):
    """
    Aggiorna dati paziente.
    
    **Note:**
    - Non è possibile modificare: fiscal_code, date_of_birth (campi immutabili)
    - Richiedono creazione nuovo paziente se errati
    """
    
    
    patient = session.get(Patient, patient_id)
    if not patient:
        raise HTTPException(404, "Patient not found")
    
    if patient.deleted_at:
        raise HTTPException(410, "Patient has been deleted")
    
    # Applica modifiche
    update_data = patient_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(patient, field, value)
    
    patient.updated_at = datetime.now(timezone.utc)
    patient.updated_by_user_id = current_user.id
    
    session.add(patient)
    session.commit()
    session.refresh(patient)
    
    return patient


# ============================================================================
# DELETE PATIENT (Soft delete)
# ============================================================================

@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient(
    patient_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
    delete_dossiers: bool = Query(False, description="Elimina anche i dossier associati")
):
    """
    Elimina un paziente (soft delete).
    
    **Opzioni:**
    - `delete_dossiers`: Se true, elimina anche tutti i dossier del paziente
    
    **ATTENZIONE:**
    - Operazione delicata, richiede conferma
    - Solo superuser può eliminare se paziente ha dossier attivi
    """
    
    patient = session.get(Patient, patient_id)
    if not patient:
        raise HTTPException(404, "Patient not found")
    
    if patient.deleted_at:
        raise HTTPException(410, "Patient already deleted")
    
    # ✅ Verifica dossier attivi
    active_dossiers = session.exec(
        select(Dossier).where(
            Dossier.patient_id == patient_id,
            Dossier.status == "active",
            Dossier.deleted_at.is_(None)
        )
    ).all()
    
    if active_dossiers and not current_user.is_superuser:
        raise HTTPException(
            403,
            f"Cannot delete patient with {len(active_dossiers)} active dossier(s). Requires superuser."
        )
    
    # Soft delete paziente
    patient.deleted_at = datetime.now(timezone.utc)
    patient.deleted_by_user_id = current_user.id
    session.add(patient)
    
    # Elimina dossier se richiesto
    if delete_dossiers:
        all_dossiers = session.exec(
            select(Dossier).where(
                Dossier.patient_id == patient_id,
                Dossier.deleted_at.is_(None)
            )
        ).all()
        
        for dossier in all_dossiers:
            dossier.deleted_at = datetime.now(timezone.utc)
            dossier.deleted_by_user_id = current_user.id
            session.add(dossier)
    
    session.commit()
    return None
