import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from app.api.deps import SessionDep, get_current_active_superuser, get_current_user
from app.models import (
    Structure,
    StructureBase,
    StructureCreate,
    StructureUpdate,
    StructuresPublic,
)

router = APIRouter(prefix="/structures", tags=["structures"], dependencies=[Depends(get_current_user)])


@router.get("/", response_model=StructuresPublic)
def read_structures(session: SessionDep, skip: int = 0, limit: int = 100) -> Any:
    structures = session.exec(select(Structure).offset(skip).limit(limit)).all()
    return StructuresPublic(data=structures)


@router.get("/{structure_id}", response_model=StructureBase)
def read_structure(structure_id: int, session: SessionDep) -> Any:
    structure = session.get(Structure, structure_id)
    if not structure:
        raise HTTPException(status_code=404, detail="Structure not found")
    return structure


@router.post("/", response_model=StructureBase)
def create_structure(structure_in: StructureCreate, session: SessionDep) -> Any:
    structure = Structure(**structure_in.model_dump()) # era dict se non dovesse funzionare per qualche motivo
    session.add(structure)
    session.commit()
    session.refresh(structure)
    return structure


@router.put("/{structure_id}", response_model=StructureBase)
def update_structure(structure_id: int, structure_in: StructureUpdate, session: SessionDep) -> Any:
    structure = session.get(Structure, structure_id)
    if not structure:
        raise HTTPException(status_code=404, detail="Structure not found")

    update_data = structure_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(structure, key, value)

    session.add(structure)
    session.commit()
    session.refresh(structure)
    return structure


@router.delete("/{structure_id}")
def delete_structure(structure_id: int, session: SessionDep) -> Any:
    structure = session.get(Structure, structure_id)
    if not structure:
        raise HTTPException(status_code=404, detail="Structure not found")
    session.delete(structure)
    session.commit()
    return {"message": "Structure deleted successfully"}
