"""Calcolo della quota esente e della quota imponibile di una richiesta."""

from src import rules


def _massimale_estero(data_iso, giorni):
    """Massimale teorico per trasferta estera.

    Dal 01/01/2026, per durata superiore a 5 giornate, si applica la riduzione
    progressiva della Sezione 4. Per le trasferte previgenti (data di inizio
    fino al 31/12/2025) il massimale resta costante per qualsiasi durata.
    """
    cap = rules.massimali_giornalieri(data_iso)["trasferta_estero"]
    if not rules._del_2026(data_iso) or giorni <= rules.SOGLIA_ESTERO_PIENO:
        return round(cap * giorni, 2)
    g_pieno = rules.SOGLIA_ESTERO_PIENO
    g_ridotto_10 = min(giorni - rules.SOGLIA_ESTERO_PIENO, rules.SOGLIA_ESTERO_RIDOTTO - rules.SOGLIA_ESTERO_PIENO)
    g_ridotto_20 = max(giorni - rules.SOGLIA_ESTERO_RIDOTTO, 0)
    totale = (
        g_pieno * cap
        + g_ridotto_10 * rules.MASSIMALE_ESTERO_RIDOTTO_10
        + g_ridotto_20 * rules.MASSIMALE_ESTERO_RIDOTTO_20
    )
    return round(totale, 2)


def massimale_teorico(richiesta, giornate_agile_gia=0):
    """Massimale di esenzione applicabile alla richiesta, in base alla categoria.

    `giornate_agile_gia` è il numero di giornate di lavoro agile già rimborsate
    al dipendente nel mese, usato per applicare il tetto mensile di 12 giornate.
    """
    data_iso = richiesta["data"]
    categoria = richiesta["categoria"]
    if categoria == "trasferta_estero":
        return _massimale_estero(data_iso, richiesta["giorni"])
    if categoria == "lavoro_agile":
        ammesse = min(
            richiesta["giorni"],
            max(rules.MAX_GIORNATE_LAVORO_AGILE - giornate_agile_gia, 0),
        )
        return round(rules.massimali_giornalieri(data_iso)["lavoro_agile"] * ammesse, 2)
    if categoria in rules.CATEGORIE_A_GIORNATE:
        return round(rules.massimali_giornalieri(data_iso)[categoria] * richiesta["giorni"], 2)
    if categoria == "chilometrico":
        return round(rules.massimale_km(data_iso) * richiesta["km"], 2)
    if categoria == "alloggio":
        return round(rules.massimale_notte(data_iso) * richiesta["notti"], 2)
    raise ValueError(f"categoria non gestita: {categoria}")


def calcola(richiesta, esente_gia_riconosciuta, giornate_agile_gia=0):
    """Restituisce (quota_esente, quota_imponibile, dettaglio).

    `esente_gia_riconosciuta` è la quota esente già riconosciuta al dipendente
    nel mese della richiesta, ai fini del plafond mensile.
    `giornate_agile_gia` è il numero di giornate di lavoro agile già rimborsate
    nel mese (rilevante solo per la categoria `lavoro_agile`).
    """
    importo = richiesta["importo"]
    teorico = massimale_teorico(richiesta, giornate_agile_gia)
    esente_teorica = min(importo, teorico)
    capienza = max(rules.plafond_mensile(richiesta["data"]) - esente_gia_riconosciuta, 0.0)
    esente = round(min(esente_teorica, capienza), 2)
    imponibile = round(importo - esente, 2)
    dettaglio = {
        "massimale_teorico": teorico,
        "esente_teorica": round(esente_teorica, 2),
        "capienza_plafond": round(capienza, 2),
    }
    return esente, imponibile, dettaglio
