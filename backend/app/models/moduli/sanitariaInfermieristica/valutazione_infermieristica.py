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
    # anno: int
    # numero_progressivo: int
    peso_kg: Optional[float]
    altezza_mt: Optional[float]
    imc_kg_m2: Optional[float]


class RilievoParametriVitali(BaseModel):
    model_config = ConfigDict(extra="forbid")
    frequenza_cardiaca_b_min: Optional[int]
    temperatura_corporea_c: Optional[float]
    pressione_arteriosa_mmhg: Optional[str]
    ecg: Optional[bool]
    frequenza_respiratoria_atti_min: Optional[int]
    sato2: Optional[float]
    altro_parametri_vitali: Optional[str]


class ModelloPercezioneGestioneSalute(BaseModel):
    model_config = ConfigDict(extra="forbid")
    consumo_tabacco: bool #Optional[Literal["no", "si"]]
    quantita_tabacco_die_numero_sigarette: Optional[int]
    interrotto_consumo_tabacco: Optional[bool] #[Literal["no", "si"]]
    data_interruzione_tabacco: Optional[date]
    consumo_alcolici: bool #Optional[Literal["no", "si"]]
    quantita_alcolici_die_cl: Optional[int]
    interrotto_consumo_alcolici: Optional[bool] #[Literal["no", "si"]]
    data_interruzione_alcolici: Optional[date]


class AllergieRiferite(BaseModel):
    model_config = ConfigDict(extra="forbid")
    farmaci: Optional[str]
    alimenti: Optional[str]
    altro_allergie: Optional[str]


# -----------------------------
# Anamnesi ed esame obiettivo
# -----------------------------

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

class Comunicazione(BaseModel):
    model_config = ConfigDict(extra="forbid")
    stato_di_coscienza: Optional[Literal["vigile-collaborante", "soporoso", "comatoso"]]
    comunicazione: Optional[List[Literal[
        "orientato", "disorientato", "regolare", "disfonia", "disartria", "afasia", "tracheostomia"
    ]]]
    udito: Optional[List[Literal["normoudente", "ipoacusia", "sordità"]]]
    sordita_lato: Optional[Literal["dx", "sn"]]
    protesi_udito: Optional[bool]
    protesi_udito_lato: Optional[Literal["dx", "sn"]]
    vista: Optional[List[Literal["normovedente", "riduzione visus", "non vedente"]]]
    protesi_vista: Optional[List[Literal["occhiali", "lenti a contatto"]]]
    condizioni_psichiche: Optional[List[Literal[
        "tranquillo", "irrequieto/ansioso", "agitazione psicomotoria", "apatia/disinteresse", "deficit cognitivo"
    ]]]

class Respirazione(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tipologia: Optional[Literal["eupnea", "dispnea"]]
    dispnea_tipo: Optional[Literal["da sforzo", "a riposo"]]
    presenza_di_tosse: Optional[bool] #[Literal["no", "si"]]
    trattamento_o2: Optional[bool] #[Literal["no", "si"]]
    ossigenoterapia_l_min: Optional[float]
    aspirazioni_secrezioni: Optional[bool]
    allergie_respirazione: Optional[List[Literal["bpco", "asma", "pollini", "epiteli animali", "acari"]]]
    presidi_respirazione: Optional[List[Literal["cpap", "respiratore", "ventilatore", "cannula guedel"]]]

class CircolazioneETessutiCutanei(BaseModel):
    model_config = ConfigDict(extra="forbid")
    presidi_protesi: Optional[List[Literal["pace maker", "protesi valvolari", "sistema port", "c.v.c.", "altro"]]]
    altro_presidi_protesi: Optional[str]
    cute_mucose: Optional[List[Literal["normocromica", "pallida", "cianotica", "itterica", "disidratata"]]]
    integrita_cutanea: Optional[List[Literal["ferite chirurgiche", "ulcere distrofiche", "lividi", "edemi"]]]
    presenza_lesioni_da_decubito_sede: Optional[str]
    stadio_lesioni_da_decubito: Optional[Literal["1°", "2°", "3°", "4°"]]
    rischio_lesioni_scala_braden: Optional[Literal["basso", "medio", "elevato", "molto elevato"]]

class Stato(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # muscolo scheletrico
    escursione_articolare: Optional[Literal["completa", "altro"]]
    altro_escursione_articolare: Optional[str]
    presa_delle_mani: Optional[Literal["normale", "debolezza", "paralisi"]]
    debolezza_mani_lato: Optional[Literal["dx", "sn"]]
    paralisi_mani_lato: Optional[Literal["dx", "sn"]]
    presa_arti_inferiori: Optional[Literal["normale", "debolezza", "paralisi"]]
    debolezza_arti_inferiori_lato: Optional[Literal["dx", "sn"]]
    paralisi_arti_inferiori_lato: Optional[Literal["dx", "sn"]]
    # psico comportamentale
    depressione: Optional[bool]
    ansia: Optional[Literal["lieve", "moderata", "grave"]]
    agitazione: Optional[bool]
    riposo_sonno: Optional[List[Literal["regolare", "irregolare", "insonnia"]]]
    # dolore
    tipo_dolore: Optional[Literal["acuto", "cronico"]]
    sede_dolore_acuto: Optional[str]
    sede_dolore_cronico: Optional[str]
    caratteristiche_dolore: Optional[List[Literal["intermittente", "ingravescente", "colico"]]]
    terapia_antidolorifica: Optional[List[Literal["analgesici", "antipiretici", "antinfiammatori", "oppioidi"]]]

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
    #autonomia
    grado_autonomia: Optional[Literal["alvo regolare", "incontinente", "diarrea", "stipsi", "utilizzo lassativi", "clisteri evacuativi"]]
    #frequenza/consistenza
    frequenza_evacuazioni_n: Optional[int]
    data_utlima_evacuazione: Optional[str]
    consistenza: Optional[Literal["asciutte-disidratate", "soffici", "semi liquide", "liquide"]]
    #colore
    colore: Optional[Literal["normocromiche", "con tracce di sangue", "con tracce di muco", "melena"]]
    #presidi
    presidi: Optional[Literal["sedia comoda", "padella", "pannolone", "colostomia/ilestomia", "enterostomia", "drenaggio"]]


class EliminazioneVescicaleUrinaria(BaseModel):
    model_config = ConfigDict(extra="forbid")
    grado_autonomia: Optional[Literal["autonomo", "regolare", "incontinente"]] = None
    incontinente_tipo: Optional[Literal["totale", "parziale"]] = None
    minzione: Optional[Literal["normale", "disuria", "nicturia", "impellente"]] = None

    # Frequenza e quantità
    frequenza_die: Optional[int] = Field(None, ge=0)
    diuresi_ml_24ore: Optional[int] = Field(None, ge=0)
    diuresi_regolarita: Optional[Literal["regolare", "anuria", "oliguria", "poliuria"]] = None

    # Caratteristiche urinarie
    caratteristiche: Optional[
        Literal["limpide", "ematuria", "piuria", "con sedimento", "ipercromiche", "torride"]
    ] = None

    # Presidi e dispositivi
    presidi_urinaria: Optional[
        Literal["sedia comoda", "pappagallo", "pannolone", "catetere", "condom", "stomia", "drenaggio"]
    ] = None
    stomia_tipo: Optional[str] = None

    # Infezioni urinarie
    infezioni_urinarie: Optional[bool]
    se_si_specificare_segni_e_sintomi: Optional[str] = None


class AlimentazioneEIdratazione(BaseModel):
    """
    Sezione 'ALIMENTAZIONE E IDRATAZIONE'
    Modulo 4 - Valutazione infermieristica.
    """
    model_config = ConfigDict(extra="forbid")

    # Autonomia
    autonomia: Optional[
        Literal["totale", "difficoltà masticazione", "parziale con aiuto", "totale dipendente"]
    ] = None
    deglutizione: Optional[
        Literal["normale", "disfagia a solidi", "disfagia a liquidi"]
    ] = None
    
    protesi: Optional[
        Literal["superiore", "inferiore", "fissa", "mobile"]
    ] = None
    
    presidi: Optional[
        Literal["sng", "peg/peg-j", "npt", "altro"]
    ] = None
    altro_presidi: Optional[str] = None
    

    # Dieta
    dieta: Optional[
        Literal["dieta comune", "celiachia", "dieta speciale", "restrizioni dietetiche", "intolleranze", "allergie"]
    ] = None
    dieta_speciale_specifica: Optional[str] = None
    restrizioni_dietetiche: Optional[str] = None
    intolleranze: Optional[str] = None
    allergie: Optional[str] = None
    cavo_orale: Optional[
        Literal["normale", "arrossamenti", "lesioni", "altro"]
    ] = None
    altro_cavo_orale: Optional[str] = None

    # Stato nutrizionale
    stato_nutrizionale_scala_mna: Optional[
        Literal["buono - normale", "rischio malnutrizione", "malnutrito"]
    ] = None
    variazioni_peso_ultimi_mesi: Optional[int] = Field(None, ge=0)
    variazione_peso_kg: Optional[float] = Field(None, ge=-500, le=500)
    tipo_variazione_peso: Optional[Literal["aumento", "perdita"]] = None

    peso_kg: Optional[float] = Field(None, ge=0)
    altezza_mt: Optional[float] = Field(None, ge=0)
    imc: Optional[float] = Field(None, ge=0)
    grado_obesita: Optional[
        Literal[
            "normale (18,5-25)",
            "1° grado (25-30)",
            "2° grado (30-40)",
            "3° grado (>40)"
        ]
    ] = None

    # Condizioni nutrizionali e sintomi
    presenza_di: Optional[
        Literal[
            "inappetenza",
            "polifagia",
            "disfagia",
            "nausea",
            "conato",
            "vomito",
            "stomatite",
            "cachessia"
        ]
    ] = None


    # Addome
    addome: Optional[
        Literal["peristalsi", "timpanico", "trattabile", "dolente"]
    ] = None

    # Stato di idratazione
    idratazione_stato: Optional[
        Literal["idratato", "disidratato", "gravemente disidratato"]
    ] = None
    
    # Idratazione autonomia
    idratazione_autonomia: Optional[
        Literal["spontanea", "con aiuto", "dipendente"]
    ] = None


# -----------------------------
# Diagnosi e rischio
# -----------------------------

class DiagnosiInfermieristica(BaseModel):
    model_config = ConfigDict(extra="forbid")
    patologia_prevalente: Optional[str]
    patologia_secondaria_1: Optional[str]
    patologia_secondaria_2: Optional[str]

class ValutazioneDelRischio(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rischio_cadute_scala_di_conley: Optional[Literal["assente", "basso", "medio", "alto"]]
    rischio_infezioni_ica: Optional[Literal["assente", "basso", "medio", "alto"]]


# -----------------------------
# Modello principale
# -----------------------------

class ValutazioneInfermieristicaV1(BaseModel):
    model_config = ConfigDict(extra="forbid")

    utente: MetadatiModulo
    paziente: Paziente
    rilievo_parametri_vitali: Optional[RilievoParametriVitali]
    modello_di_percezione_e_di_gestione_della_salute: Optional[ModelloPercezioneGestioneSalute]
    allergie_riferite: Optional[AllergieRiferite]
    attivita_fisiche_sportive: bool #Optional[Literal["no", "si"]]
    patologie_croniche: bool #Optional[Literal["no", "si"]]
    quali_patologie_croniche: Optional[str]

    anamnesi_ed_esame_obiettivo: Optional[AnamnesiObiettivo]
    
    tao: Optional[bool]
    ossigenoterapia: Optional[bool]
    farmaci_h: Optional[bool]

    diagnosi_infermieristica: Optional[DiagnosiInfermieristica]
    valutazione_bisogni_infermieristici: Optional[str]
    cadenza_monitoraggio_clinico_parametri_vitali: Optional[str]
    patologie_da_monitorare: Optional[str]
    valutazione_del_rischio: Optional[ValutazioneDelRischio]
    scale_utilizzate: Optional[str]

    data: Optional[date]
    infermiere_compilatore: Optional[str]
    firma: Optional[str]
