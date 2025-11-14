from __future__ import annotations
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Literal
from datetime import date
from app.models.moduli.common import MetadatiModulo, DatiAnagraficiModulo, StrutturaTipo


# -----------------------------
# Sezioni principali
# -----------------------------

class Paziente(DatiAnagraficiModulo, BaseModel):
    model_config = ConfigDict(extra="forbid")
    peso_kg: Optional[float] = None
    altezza_mt: Optional[float] = None
    imc_kg_m2: Optional[float] = None


class RilievoParametriVitali(BaseModel):
    model_config = ConfigDict(extra="forbid")
    frequenza_cardiaca_b_min: Optional[int] = None
    temperatura_corporea_c: Optional[float] = None
    pressione_arteriosa_mmhg: Optional[str] = None
    ecg: Optional[bool] = None
    frequenza_respiratoria_atti_min: Optional[int] = None
    sato2: Optional[float] = None
    altro_parametri_vitali: Optional[str] = None


class ModelloPercezioneGestioneSalute(BaseModel):
    model_config = ConfigDict(extra="forbid")
    consumo_tabacco: bool = False
    quantita_tabacco_die_numero_sigarette: Optional[int] = None
    interrotto_consumo_tabacco: Optional[bool] = None
    data_interruzione_tabacco: Optional[date] = None
    consumo_alcolici: bool = False
    quantita_alcolici_die_cl: Optional[int] = None
    interrotto_consumo_alcolici: Optional[bool] = None
    data_interruzione_alcolici: Optional[date] = None


class AllergieRiferite(BaseModel):
    model_config = ConfigDict(extra="forbid")
    farmaci: Optional[str] = None
    alimenti: Optional[str] = None
    altro_allergie: Optional[str] = None


# -----------------------------
# Anamnesi ed esame obiettivo
# -----------------------------

class Comunicazione(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # ✅ FIX 1: stato_di_coscienza può essere lista o singolo valore
    stato_di_coscienza: Optional[List[Literal["vigile-collaborante", "soporoso", "comatoso", "orientato", "disorientato"]]] = None
    comunicazione: Optional[List[Literal[
        "regolare", "disfonia", "disartria", "afasia", "tracheostomia"
    ]]] = None
    udito: Optional[List[Literal["normoudente", "ipoacusia", "sordità"]]] = None
    sordita_lato: Optional[Literal["dx", "sn"]] = None
    protesi_udito: Optional[bool] = None
    protesi_udito_lato: Optional[Literal["dx", "sn"]] = None
    vista: Optional[List[Literal["normovedente", "riduzione visus", "non vedente"]]] = None
    protesi_vista: Optional[List[Literal["occhiali", "lenti a contatto"]]] = None
    condizioni_psichiche: Optional[List[Literal[
        "tranquillo", "irrequieto/ansioso", "agitazione psicomotoria", "apatia/disinteresse", "deficit cognitivo"
    ]]] = None

class Respirazione(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tipologia: Optional[Literal["eupnea", "dispnea"]] = None
    # ✅ FIX 2: dispnea_tipo può essere lista
    dispnea_tipo: Optional[List[Literal["da sforzo", "a riposo"]]] = None
    presenza_di_tosse: Optional[bool] = None
    trattamento_o2: Optional[bool] = None
    ossigenoterapia_l_min: Optional[float] = None
    aspirazioni_secrezioni: Optional[bool] = None
    allergie_respirazione: Optional[List[Literal["bpco", "asma", "pollini", "epiteli animali", "acari"]]] = None
    presidi_respirazione: Optional[List[Literal["cpap", "respiratore", "ventilatore", "cannula guedel"]]] = None

class CircolazioneETessutiCutanei(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # ✅ FIX 3: Aggiungi "prot. valvolari" come opzione valida
    presidi_protesi: Optional[List[Literal[
        "pace maker", 
        "protesi valvolari",
        "prot. valvolari",  # ← Aggiungi questa variante
        "sistema port", 
        "c.v.c.", 
        "altro"
    ]]] = None
    altro_presidi_protesi: Optional[str] = None
    cute_mucose: Optional[List[Literal["normocromica", "pallida", "cianotica", "itterica", "disidratata"]]] = None
    integrita_cutanea: Optional[List[Literal["ferite chirurgiche", "ulcere distrofiche", "lividi", "edemi"]]] = None
    presenza_lesioni_da_decubito_sede: Optional[str] = None
    stadio_lesioni_da_decubito: Optional[Literal["1°", "2°", "3°", "4°"]] = None
    rischio_lesioni_scala_braden: Optional[Literal["basso", "medio", "elevato", "molto elevato"]] = None

class Stato(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # muscolo scheletrico
    escursione_articolare: Optional[Literal["completa", "altro"]] = None
    altro_escursione_articolare: Optional[str] = None
    presa_delle_mani: Optional[Literal["normale", "debolezza", "paralisi"]] = None
    debolezza_mani_lato: Optional[Literal["dx", "sn"]] = None
    paralisi_mani_lato: Optional[Literal["dx", "sn"]] = None
    presa_arti_inferiori: Optional[Literal["normale", "debolezza", "paralisi"]] = None
    debolezza_arti_inferiori_lato: Optional[Literal["dx", "sn"]] = None
    paralisi_arti_inferiori_lato: Optional[Literal["dx", "sn"]] = None
    # psico comportamentale
    depressione: Optional[bool] = None
    ansia: Optional[Literal["lieve", "moderata", "grave"]] = None
    agitazione: Optional[bool] = None
    riposo_sonno: Optional[List[Literal["regolare", "irregolare", "insonnia"]]] = None
    # ✅ FIX 4: tipo_dolore può essere lista (acuto E cronico insieme)
    tipo_dolore: Optional[List[Literal["acuto", "cronico"]]] = None
    sede_dolore_acuto: Optional[str] = None
    sede_dolore_cronico: Optional[str] = None
    caratteristiche_dolore: Optional[List[Literal["intermittente", "ingravescente", "colico"]]] = None
    terapia_antidolorifica: Optional[List[Literal["analgesici", "antipiretici", "antinfiammatori", "oppioidi"]]] = None

class MovimentoIgiene(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # movimento
    autonomia_movimento: Optional[Literal["autonomo", "con assistenza", "non autonomo"]] = None
    rischio_cadute_conley: Optional[Literal["rischio minimo", "aumento del rischio", "rischio alto"]] = None
    ausili_presidi_movimento: Optional[List[Literal["deambulatore/carrozzina"]]] = None
    # postura
    autonomia_postura: Optional[Literal["autonomo", "postura obbligata"]] = None
    postura_obbligata_causa: Optional[List[Literal["paralisi", "paresi", "allettato"]]] = None
    ausili_presidi_postura: Optional[List[Literal["sponde per letto", "materasso antidecubito", "altro"]]] = None
    altro_ausili_presidi_postura: Optional[str] = None
    # igiene
    lavarsi: Optional[Literal["si lava da solo", "si lava con aiuto", "totale dipendenza"]] = None
    vestirsi: Optional[Literal["si veste da solo", "si veste con aiuto", "totale dipendenza"]] = None
    # uso wc
    autonomia_wc: Optional[Literal["autonomo", "con uso di ausili", "con assistenza", "totale dipendenza"]] = None
    altro_uso_wc: Optional[str] = None
    # bagno/doccia
    autonomia_doccia: Optional[Literal["autonomo", "con uso di ausili", "con assistenza", "totale dipendenza"]] = None

class EliminazioneIntestinale(BaseModel):
    model_config = ConfigDict(extra="forbid")
    grado_autonomia: Optional[Literal["alvo regolare", "incontinente", "diarrea", "stipsi", "utilizzo lassativi", "clisteri evacuativi"]] = None
    frequenza_evacuazioni_n: Optional[int] = None
    data_utlima_evacuazione: Optional[str] = None
    consistenza: Optional[Literal["asciutte-disidratate", "soffici", "semi liquide", "liquide"]] = None
    colore: Optional[Literal["normocromiche", "con tracce di sangue", "con tracce di muco", "melena"]] = None
    presidi: Optional[Literal["sedia comoda", "padella", "pannolone", "colostomia/ilestomia", "enterostomia", "drenaggio"]] = None


class EliminazioneVescicaleUrinaria(BaseModel):
    model_config = ConfigDict(extra="forbid")
    grado_autonomia: Optional[Literal["autonomo", "regolare", "incontinente"]] = None
    incontinente_tipo: Optional[Literal["totale", "parziale"]] = None
    minzione: Optional[Literal["normale", "disuria", "nicturia", "impellente"]] = None
    frequenza_die: Optional[int] = Field(None, ge=0)
    diuresi_ml_24ore: Optional[int] = Field(None, ge=0)
    diuresi_regolarita: Optional[Literal["regolare", "anuria", "oliguria", "poliuria"]] = None
    caratteristiche: Optional[Literal["limpide", "ematuria", "piuria", "con sedimento", "ipercromiche", "torride"]] = None
    presidi_urinaria: Optional[Literal["sedia comoda", "pappagallo", "pannolone", "catetere", "condom", "stomia", "drenaggio"]] = None
    stomia_tipo: Optional[str] = None
    infezioni_urinarie: Optional[bool] = None
    se_si_specificare_segni_e_sintomi: Optional[str] = None


class AlimentazioneEIdratazione(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Autonomia
    autonomia: Optional[Literal["totale", "difficoltà masticazione", "parziale con aiuto", "totale dipendente"]] = None
    deglutizione: Optional[Literal["normale", "disfagia a solidi", "disfagia a liquidi"]] = None
    
    # ✅ FIX 5: protesi può essere lista (superiore + fissa, ecc.)
    protesi: Optional[List[Literal["superiore", "inferiore", "fissa", "mobile"]]] = None
    
    # ✅ FIX 6: presidi può essere lista
    presidi: Optional[List[Literal["sng", "peg/peg-j", "npt", "altro"]]] = None
    altro_presidi: Optional[str] = None

    # Dieta
    dieta: Optional[Literal["dieta comune", "celiachia", "dieta speciale", "restrizioni dietetiche", "intolleranze", "allergie"]] = None
    dieta_speciale_specifica: Optional[str] = None
    restrizioni_dietetiche: Optional[str] = None
    intolleranze: Optional[str] = None
    allergie: Optional[str] = None
    cavo_orale: Optional[Literal["normale", "arrossamenti", "lesioni", "altro"]] = None
    altro_cavo_orale: Optional[str] = None

    # ✅ FIX 7: Aggiungi variante "buono-normale" (senza spazio)
    stato_nutrizionale_scala_mna: Optional[Literal[
        "buono - normale",
        "buono-normale",  # ← Aggiungi questa variante
        "rischio malnutrizione", 
        "malnutrito"
    ]] = None
    
    variazioni_peso_ultimi_mesi: Optional[int] = Field(None, ge=0)
    variazione_peso_kg: Optional[float] = Field(None, ge=-500, le=500)
    tipo_variazione_peso: Optional[Literal["aumento", "perdita"]] = None

    peso_kg: Optional[float] = Field(None, ge=0)
    altezza_mt: Optional[float] = Field(None, ge=0)
    imc: Optional[float] = Field(None, ge=0)
    grado_obesita: Optional[Literal[
        "normale (18,5-25)",
        "1° grado (25-30)",
        "2° grado (30-40)",
        "3° grado (>40)"
    ]] = None

    # ✅ FIX 8: presenza_di può essere lista (più sintomi contemporaneamente)
    presenza_di: Optional[List[Literal[
        "inappetenza",
        "polifagia",
        "disfagia",
        "nausea",
        "conato",
        "vomito",
        "stomatite",
        "cachessia"
    ]]] = None

    # ✅ FIX 9: addome può essere lista (più caratteristiche)
    addome: Optional[List[Literal["peristalsi", "timpanico", "trattabile", "dolente"]]] = None

    # Stato di idratazione
    idratazione_stato: Optional[Literal["idratato", "disidratato", "gravemente disidratato"]] = None
    idratazione_autonomia: Optional[Literal["spontanea", "con aiuto", "dipendente"]] = None


class AnamnesiObiettivo(BaseModel):
    model_config = ConfigDict(extra="forbid")
    comunicazione: Comunicazione
    respirazione: Respirazione
    circolazione_e_tessuti_cutanei: CircolazioneETessutiCutanei
    stato: Stato
    movimento_igiene: MovimentoIgiene
    eliminazione_intestinale: EliminazioneIntestinale
    eliminazione_vescicale_urinaria: EliminazioneVescicaleUrinaria
    alimentazione_e_idratazione: AlimentazioneEIdratazione


# -----------------------------
# Diagnosi e rischio
# -----------------------------

class DiagnosiInfermieristica(BaseModel):
    model_config = ConfigDict(extra="forbid")
    patologia_prevalente: Optional[str] = None
    patologia_secondaria_1: Optional[str] = None
    patologia_secondaria_2: Optional[str] = None

class ValutazioneDelRischio(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rischio_cadute_scala_di_conley: Optional[Literal["assente", "basso", "medio", "alto"]] = None
    rischio_infezioni_ica: Optional[Literal["assente", "basso", "medio", "alto"]] = None


# -----------------------------
# Modello principale
# -----------------------------

class ValutazioneInfermieristicaV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    utente: MetadatiModulo
    paziente: Paziente
    rilievo_parametri_vitali: Optional[RilievoParametriVitali] = None
    modello_di_percezione_e_di_gestione_della_salute: Optional[ModelloPercezioneGestioneSalute] = None
    allergie_riferite: Optional[AllergieRiferite] = None
    attivita_fisiche_sportive: bool = False
    patologie_croniche: bool = False
    quali_patologie_croniche: Optional[str] = None

    anamnesi_ed_esame_obiettivo: Optional[AnamnesiObiettivo] = None
    
    tao: Optional[bool] = None
    ossigenoterapia: Optional[bool] = None
    farmaci_h: Optional[bool] = None

    diagnosi_infermieristica: Optional[DiagnosiInfermieristica] = None
    valutazione_bisogni_infermieristici: Optional[str] = None
    cadenza_monitoraggio_clinico_parametri_vitali: Optional[str] = None
    patologie_da_monitorare: Optional[str] = None
    valutazione_del_rischio: Optional[ValutazioneDelRischio] = None
    scale_utilizzate: Optional[str] = None

    data: Optional[date] = None
    infermiere_compilatore: Optional[str] = None
    firma: Optional[str] = None