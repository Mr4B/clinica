# app/services/module_service.py
from datetime import datetime
from pydantic import BaseModel
from __future__ import annotations

from app.models import ModuleEntry
from app.module_registry import REGISTRY

from sqlalchemy.ext.asyncio import AsyncSession
# from app.api.deps import SessionDep # non so se come sessione va usato questo o quel che c'è

class ModuleService:
    @staticmethod
    def validate_payload(module_code: str, version: int, payload: dict) -> BaseModel:
        key = (module_code, version)
        info = REGISTRY.get(key)
        if not info:
            raise ValueError(f"Schema non registrato: {key}")
        return info.model.model_validate(payload)

    @staticmethod
    def migrate_to_version(module_code: str, from_version: int, to_version: int, data: dict) -> dict:
        if from_version == to_version:
            return data
        step = from_version + 1
        while step <= to_version:
            info = REGISTRY.get((module_code, step))
            if not info or not info.migrate_from_previous:
                raise ValueError(f"Migrazione mancante: {module_code} {step-1}->{step}")
            data = info.migrate_from_previous(data)
            step += 1
        return data