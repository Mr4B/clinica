from .valutazione_infermieristica import ValutazioneInfermieristicaV1
from .valutazione_livelli_assistenziali import ValutazioneLivelliAssistenzialiV1

modules_sanInf = [
    ValutazioneInfermieristicaV1,
    ValutazioneLivelliAssistenzialiV1
]

__all__ = [cls.__name__ for cls in modules_sanInf]