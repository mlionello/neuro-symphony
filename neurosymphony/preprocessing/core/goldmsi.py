from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

import numpy as np

# NOTE: This is the Italian adaptation used in the project.
# The scoring here follows the original repository code: simple sums per subscale
# after reversing "opp" items and mapping multiple-choice duration items.

GOLDMSI_ITEMS = [
    {"ae": 0.6, "gf": 0.97, "text": "1. Trascorro molto del mio tempo libero a fare attività relative alla musica."},
    {"em": 0.5, "text": "2. A volte scelgo musica che mi fa venire i brividi lungo la schiena."},
    {"ae": 0.69, "gf": 0.88, "text": "3. Mi piace scrivere a proposito di musica, per esempio su blog o forum."},
    {"sa": 0.58, "gf": 0.90, "text": "4. Se qualcuno inizia a cantare una canzone che non conosco, di solito sono in grado di unirmi."},
    {"pa": 0.41, "text": "5. Sono in grado di giudicare se qualcuno è un bravo cantante oppure no."},
    {"pa": 0.21, "text": "6. Di solito so quando sto ascoltando una canzone per la prima volta."},
    {"sa": 0.48, "gf": 1.1, "text": "7. So cantare o suonare musica a memoria."},
    {"ae": 0.34, "text": "8. Sono incuriosito/a da stili musicali a me non familiari e voglio saperne di più."},
    {"em": 0.53, "text": "9. È raro che brani musicali mi suscitino emozioni.", "opp": True},
    {"sa": 0.87, "gf": 1.08, "text": "10. Sono capace di prendere le note giuste quando canto su un brano registrato."},
    {"pa": 0.4, "text": "11. Trovo difficile individuare gli errori in una performance di una canzone anche se conosco la melodia.", "opp": True},
    {"pa": 0.04, "text": "12. So confrontare due performance o versioni dello stesso brano musicale e discutere delle loro differenze."},
    {"pa": 0.18, "text": "13. Faccio fatica a riconoscere una canzone familiare quando è suonata in modo diverso o da un altro esecutore/esecutrice.", "opp": True},
    {"mt": 0.72, "gf": 1.3, "text": "14. Non ho mai ricevuto complimenti per il mio talento come performer musicale.", "opp": True},
    {"ae": 0.76, "gf": 0.92, "text": "15. Spesso leggo o cerco su internet cose relative alla musica."},
    {"em": 0.76, "gf": 0.92, "text": "16. Spesso scelgo un certo tipo di musica per motivarmi o entusiasmarmi."},
    {"sa": 0.81, "gf": 0.91, "text": "17. Quando qualcuno canta una melodia familiare, non so armonizzare (es. fare la seconda voce o il controcanto).", "opp": True},
    {"pa": 0.49, "text": "18. Mi accorgo quando le persone cantano o suonano fuori tempo."},
    {"em": 0.18, "gf": 0.93, "text": "19. So identificare quello che un determinato brano musicale ha di particolare."},
    {"em": 0.54, "text": "20. Sono in grado di parlare delle emozioni che un brano musicale mi suscita."},
    {"ae": 0.75, "text": "21. Non spendo molto del mio reddito disponibile per cose musicali.", "opp": True},
    {"pa": 0.63, "text": "22. Mi accorgo quando le persone cantano o suonano in modo stonato."},
    {"pa": 0.42, "gf": 0.96, "text": "23. Quando canto, non ho idea se io sia intonato/a oppure no.", "opp": True},
    {"ae": 0.77, "gf": 0.94, "text": "24. La musica è una sorta di dipendenza per me - non saprei vivere senza."},
    {"sa": 0.88, "gf": 0.94, "text": "25. Non mi piace cantare in pubblico perché temo che sbaglierei le note.", "opp": True},
    {"pa": 0.1, "text": "26. Quando sento un brano, di solito sono in grado di identificare il suo genere musicale."},
    {"mt": 0.90, "gf": 1.40, "text": "27. Non mi considererei un/una musicista.", "opp": True},
    {"ae": 0.72, "text": "28. Tengo traccia della nuova musica in cui mi imbatto (es. di nuovi artisti o di nuove registrazioni)."},
    {"sa": 0.53, "gf": 0.91, "text": "29. Dopo aver sentito una canzone nuova per due o tre volte, di solito sono in grado di cantarla da solo/a."},
    {"sa": 0.52, "text": "30. Mi basta sentire una melodia nuova una sola volta e riesco a ricantarla ore dopo."},
    {"em": 0.48, "text": "31. La musica mi evoca ricordi di persone e luoghi passati."},
    {"mt": 1.57, "gf": 1.11, "text": "32. Mi sono impegnato/a nella pratica regolare e quotidiana di uno strumento musicale (inclusa la voce) per "},
    {"mt": 0.71, "gf": 1.11, "text": "33. All’apice del mio interesse, mi sono esercitato/a per "},
    {"ae": 0.52, "text": "34. Ho partecipato a "},
    {"mt": 1.43, "text": "35. Ho ricevuto un’istruzione formale in teoria musicale per "},
    {"mt": 1.67, "text": "36. Ho ricevuto un’istruzione formale in uno strumento musicale (inclusa la voce) per "},
    {"mt": 0.82, "gf": 0.97, "text": "37. So suonare "},
    {"ae": 0.97, "text": "38. Ascolto musica con attenzione per "},
    {"text": "39. Lo strumento che suono meglio (compresa la voce) è"},
]

MULTIPLE_OPTION_ITEMS = [
    ["0", "1", "2", "3", "4-5", "6-9", "10 o più"],
    ["0", "0.5", "1", "1.5", "2", "3-4", "5 o più"],
    ["0", "1", "2", "3", "4-6", "7-10", "11 o più"],
    ["0", "0.5", "1", "2", "3", "4-6", "7 o più"],
    ["0", "0.5", "1", "2", "3-5", "6-9", "10 o più"],
    ["0", "1", "2", "3", "4", "5", "6 o più"],
    ["0-15 minuti", "15-30 minuti", "30-60 minuti", "60-90 minuti", "2 ore", "3-5 ore", "4 ore o più"],
]


def _map_multiple_choice_answer(raw: str, options: Sequence[str]) -> int:
    """Return the index of `raw` inside `options`.

    Raises ValueError if `raw` is not found.
    """
    for idx, opt in enumerate(options):
        if str(raw).strip() == str(opt).strip():
            return idx
    raise ValueError(f"Unknown multiple-choice answer: {raw!r}. Expected one of: {options}")


def compute_goldmsi_scores(answers: Sequence[str | int | float]) -> dict[str, float]:
    """Compute Gold-MSI subscale sums.

    Parameters
    ----------
    answers:
        Sequence of length >= 39 containing the answers as stored by the web app.

    Returns
    -------
    dict
        Keys: ae_score, pa_score, sa_score, mt_score, em_score, gf_score

    Notes
    -----
    This function mirrors the original project code: it uses **simple sums**
    per subscale (not weighted sums), after reversing 'opp' items and mapping the
    7 multiple-choice items (indices 31..37, zero-based) to their option index.
    """
    if len(answers) < 39:
        raise ValueError(f"Expected at least 39 Gold-MSI answers, got {len(answers)}")

    # Work on a copy
    vals = [None] * 39
    for i in range(39):
        vals[i] = answers[i]

    # Map multiple-choice items (32..38 in human numbering -> indices 31..37)
    for j, idx in enumerate(range(31, 38)):
        vals[idx] = _map_multiple_choice_answer(vals[idx], MULTIPLE_OPTION_ITEMS[j])

    # Reverse 'opp' items (1..31 are Likert 1..7; reverse uses 8-x)
    for i, item in enumerate(GOLDMSI_ITEMS):
        if item.get("opp"):
            try:
                vals[i] = 8 - float(vals[i])
            except Exception as e:
                raise ValueError(f"Invalid numeric Gold-MSI answer at index {i}: {vals[i]!r}") from e

    def idx_with(key: str) -> list[int]:
        return [i for i, item in enumerate(GOLDMSI_ITEMS) if key in item]

    scores = {
        "ae_score": float(np.sum([float(vals[i]) for i in idx_with("ae") if vals[i] is not None])),
        "pa_score": float(np.sum([float(vals[i]) for i in idx_with("pa") if vals[i] is not None])),
        "sa_score": float(np.sum([float(vals[i]) for i in idx_with("sa") if vals[i] is not None])),
        "mt_score": float(np.sum([float(vals[i]) for i in idx_with("mt") if vals[i] is not None])),
        "em_score": float(np.sum([float(vals[i]) for i in idx_with("em") if vals[i] is not None])),
        "gf_score": float(np.sum([float(vals[i]) for i in idx_with("gf") if vals[i] is not None])),
    }
    return scores
