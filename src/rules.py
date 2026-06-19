"""Parametri normativi per il calcolo dei rimborsi spese.

Il regime applicabile a ciascuna richiesta è selezionato in base alla data di
sostenimento (per le trasferte: data di inizio):

- fino al 31/12/2025  -> Circolare MEF n. 41/2024 (massimali 2025)
- dal 01/01/2026      -> Circolare MEF n. 18/2026 (massimali 2026)
"""

from datetime import date

DECORRENZA_2026 = date(2026, 1, 1)

# Regime fino al 31/12/2025 — Circolare MEF 41/2024
MASSIMALI_GIORNALIERI_2025 = {
    "trasferta_italia": 46.48,
    "trasferta_estero": 77.47,
    "pasto": 8.00,
}
MASSIMALE_KM_2025 = 0.42
MASSIMALE_NOTTE_2025 = 150.00
PLAFOND_2025 = 1200.00

# Regime dal 01/01/2026 — Circolare MEF 18/2026
MASSIMALI_GIORNALIERI_2026 = {
    "trasferta_italia": 50.00,
    "trasferta_estero": 85.00,
    "pasto": 10.00,
    "lavoro_agile": 3.50,
}
MASSIMALE_KM_2026 = 0.45
MASSIMALE_NOTTE_2026 = 170.00
PLAFOND_2026 = 1400.00

# Riduzione progressiva trasferta estero oltre 5 giornate (Sezione 4)
SOGLIA_ESTERO_PIENO = 5  # giornate 1-5: massimale pieno
SOGLIA_ESTERO_RIDOTTO = 10  # giornate 6-10: -10%; dalla 11ª: -20%
MASSIMALE_ESTERO_RIDOTTO_10 = 76.50
MASSIMALE_ESTERO_RIDOTTO_20 = 68.00

# Indennità lavoro agile (Sezione 3)
MAX_GIORNATE_LAVORO_AGILE = 12

# Etichette di tutte le categorie disciplinate (display). L'ammissibilità per
# data è gestita da categorie_ammesse().
CATEGORIE = {
    "trasferta_italia": "Trasferta in Italia",
    "trasferta_estero": "Trasferta all'estero",
    "pasto": "Rimborso pasto",
    "chilometrico": "Rimborso chilometrico",
    "alloggio": "Rimborso alloggio",
    "lavoro_agile": "Indennità lavoro agile",
}

CATEGORIE_A_GIORNATE = ("trasferta_italia", "trasferta_estero", "pasto", "lavoro_agile")
CATEGORIE_TRASFERTA = ("trasferta_italia", "trasferta_estero")

RIFERIMENTO_NORMATIVO = "Circolare MEF n. 18/2026"
RIFERIMENTO_NORMATIVO_PREVIGENTE = "Circolare MEF n. 41/2024"


def _del_2026(data_iso) -> bool:
    """True se la data di sostenimento ricade nel regime 2026 (>= 01/01/2026).

    Robusta a date assenti o non valide (restituisce False), così può essere
    invocata anche prima della validazione formale della data.
    """
    try:
        return date.fromisoformat(data_iso or "") >= DECORRENZA_2026
    except (TypeError, ValueError):
        return False


def massimali_giornalieri(data_iso):
    return MASSIMALI_GIORNALIERI_2026 if _del_2026(data_iso) else MASSIMALI_GIORNALIERI_2025


def massimale_km(data_iso):
    return MASSIMALE_KM_2026 if _del_2026(data_iso) else MASSIMALE_KM_2025


def massimale_notte(data_iso):
    return MASSIMALE_NOTTE_2026 if _del_2026(data_iso) else MASSIMALE_NOTTE_2025


def plafond_mensile(data_iso):
    return PLAFOND_2026 if _del_2026(data_iso) else PLAFOND_2025


def categorie_ammesse(data_iso):
    """Codici categoria validi alla data.

    La categoria `lavoro_agile` è ammessa solo dal 01/01/2026 (Sezione 7): per
    date anteriori le relative richieste sono respinte come categoria non
    riconosciuta.
    """
    if _del_2026(data_iso):
        return set(CATEGORIE)
    return set(CATEGORIE) - {"lavoro_agile"}
