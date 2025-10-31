from __future__ import annotations

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Literal
from datetime import date
from app.models.moduli.common import MetadatiModulo, DatiAnagraficiModulo, MetadatiCompilazione, StrutturaTipo

# ---------------------------
# Sezioni di intestazione #! riprendere da common
# ---------------------------

# class Utente(BaseModel): #metamodulo
#     model_config = ConfigDict(extra="forbid")
#     iniziali_cognome: str = Field(...)
#     iniziali_nome: str = Field(...)
#     codice_dossier_utente_numero: str = Field(...)


# class Paziente(BaseModel):
#     model_config = ConfigDict(extra="forbid")
#     nominativo: str = Field(...)
#     anno: int = Field(ge=1900, le=2100)
#     numero_progressivo: int = Field(ge=1)


# Nota: nel template JSON "strutt" è una lista con i valori ammessi.
# Qui rispettiamo il template accettando la lista di opzioni.
# StrutturaOpzioni = List[Literal["R3", "R3D"]]


# ---------------------------
# Opzioni comuni alle sezioni
# ---------------------------

class SezioneOpzione(BaseModel):
    """
    Opzione generica con campi opzionali che compaiono
    solo in alcune sezioni (Braden, SPMSQ, BPSD).
    """
    model_config = ConfigDict(extra="forbid")
    descrizione: str
    punteggio: int

    # Solo dove previsto dal template
    braden_punteggio: Optional[int] = None

    spmsq_punteggio: Optional[int] = None
    spmsq_range: Optional[str] = None

    # Solo per BPSD
    sintomi_bpsd: Optional[List[str]] = None


class SezioneConOpzioni(BaseModel):
    """
    Sezione standard: punteggio massimo + elenco opzioni.
    Il template prevede solo la lista opzioni, senza scelta esplicita.
    """
    model_config = ConfigDict(extra="forbid")
    punteggio_massimo: int
    opzioni: List[SezioneOpzione]


# ---------------------------
# Sezioni specifiche del modulo
# ---------------------------

class CapacitaDiMovimento(SezioneConOpzioni):
    pass


class IgienePersonale(SezioneConOpzioni):
    pass


class IntegritaCutanea(SezioneConOpzioni):
    pass


class Alimentazione(SezioneConOpzioni):
    pass


class StatoCognitivoComunicazione(SezioneConOpzioni):
    pass


class EliminazioneUrinaria(SezioneConOpzioni):
    pass


class StatoDiCoscienza(SezioneConOpzioni):
    pass


class EliminazioneIntestinale(SezioneConOpzioni):
    pass


class FunzioniSensoriali(SezioneConOpzioni):
    pass


class RitmoSonnoVeglia(SezioneConOpzioni):
    pass


class FunzioniRespiratorie(SezioneConOpzioni):
    pass


class ProblematicheTerapeutiche(SezioneConOpzioni):
    pass


class CompatibilitaLivelliAssistenzialiTipologiaStruttura(BaseModel):
    model_config = ConfigDict(extra="forbid")
    punteggio_0_150: str
    punteggio_151_300: str


# ---------------------------
# Schema principale del modulo
# ---------------------------

class ValutazioneLivelliAssistenzialiV1(BaseModel):
    """
    CARTELLA INFERMIERISTICA – MODULO 3: Valutazione livelli assistenziali.
    Rispecchia il template JSON e le voci del modulo.
    """
    model_config = ConfigDict(extra="forbid")

    utente: MetadatiModulo
    strutt: StrutturaTipo
    paziente: DatiAnagraficiModulo

    capacita_di_movimento: CapacitaDiMovimento
    igiene_personale: IgienePersonale
    integrita_cutanea: IntegritaCutanea
    alimentazione: Alimentazione
    stato_cognitivo_comunicazione: StatoCognitivoComunicazione
    eliminazione_urinaria: EliminazioneUrinaria
    stato_di_coscienza: StatoDiCoscienza
    eliminazione_intestinale: EliminazioneIntestinale
    funzioni_sensoriali: FunzioniSensoriali
    ritmo_sonno_veglia: RitmoSonnoVeglia
    funzioni_respiratorie: FunzioniRespiratorie
    problematiche_terapeutiche: ProblematicheTerapeutiche

    punteggio_totale: int
    compatibilita_livelli_assistenziali_tipologia_struttura: CompatibilitaLivelliAssistenzialiTipologiaStruttura

    compilazione: MetadatiCompilazione
