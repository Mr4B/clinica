"""
Componenti comuni riusabili tra moduli.
Solo per concetti che appaiono in MOLTI moduli.
"""
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import date

class DatiAnagraficiModulo(BaseModel):
    """Dati anagrafici ripetuti in ogni modulo"""
    paziente_nominativo: str = Field(max_length=200)
    anno: int = Field(ge=2000, le=2100)
    numero_progressivo: int = Field(ge=1)
    

class MetadatiModulo(BaseModel):
    """Metadati comuni: intestazione del modulo con inziali e dossier"""
    inizNome: str = Field(max_length=200)
    inizCognome: str = Field(max_length=200)
    dossier: str
    struttura: Literal["R3", "R3D"] = Field(
        description="Tipo struttura: R3 o R3D"
    )


class MetadatiCompilazione(BaseModel):
    """Metadati comuni: chi/quando ha compilato"""
    data_compilazione: date
    compilatore: Literal["mmg", "infermiere"]
    firma: str = Field(max_length=200)
    
    
class StrutturaTipo(str, Enum):
    R3 = "R3"
    R3D = "R3D"
