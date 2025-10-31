from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Tuple, Type, Optional
from pydantic import BaseModel
from app.models.moduli import ValutazioneInfermieristicaV1

class SchemaInfo:
    model: Type[BaseModel]
    migrate_from_previous: Callable | None = None

def migrate_presa_in_carico_v1_to_v2(old_data: dict) -> dict:
    """Esempio: campo 'diagnosi' → 'diagnosi_principale'"""
    new_data = old_data.copy()
    new_data['diagnosi_principale'] = old_data.pop('diagnosi')
    return new_data

REGISTRY: Dict[tuple[str,int], SchemaInfo] = {
    # ("ROG26/1.1", 1): SchemaInfo(model=PresaInCaricoV1),
    # ("ROG26/1.1", 2): SchemaInfo(model=PresaInCaricoV2, migrate_from_previous=migrate_presa_in_carico_v1_to_v2),
    ("ROG26/1.4", 1): SchemaInfo(model=ValutazioneInfermieristicaV1),
}

""" 
if target_version and target_version > current_version:
        for v in range(current_version, target_version):
            schema_info = REGISTRY.get((entry.module_code, v+1))
            if schema_info and schema_info.migrate_from_previous:
                data = schema_info.migrate_from_previous(data)
"""