from src import validator


def richiesta(**campi):
    base = {
        "dipendente": "Maria Rossi",
        "data": "2025-10-06",
        "categoria": "pasto",
        "importo": 10.0,
        "giorni": 1,
        "km": None,
        "notti": None,
    }
    base.update(campi)
    return base


def test_richiesta_valida():
    assert validator.valida(richiesta()) == (True, "")


def test_dipendente_mancante():
    ok, motivazione = validator.valida(richiesta(dipendente=""))
    assert not ok
    assert motivazione == "dipendente mancante"


def test_categoria_non_riconosciuta():
    ok, motivazione = validator.valida(richiesta(categoria="parcheggio"))
    assert not ok
    assert motivazione == "categoria non riconosciuta"


def test_importo_zero():
    ok, motivazione = validator.valida(richiesta(importo=0))
    assert not ok
    assert motivazione == "importo non positivo"


def test_importo_negativo():
    ok, motivazione = validator.valida(richiesta(importo=-5.0))
    assert not ok
    assert motivazione == "importo non positivo"


def test_importo_mancante():
    ok, motivazione = validator.valida(richiesta(importo=None))
    assert not ok
    assert motivazione == "importo non positivo"


def test_data_mancante():
    ok, motivazione = validator.valida(richiesta(data=""))
    assert not ok
    assert motivazione == "data mancante o non valida"


def test_data_non_valida():
    ok, motivazione = validator.valida(richiesta(data="06/10/2025"))
    assert not ok
    assert motivazione == "data mancante o non valida"


def test_giornate_mancanti_per_trasferta():
    ok, motivazione = validator.valida(
        richiesta(categoria="trasferta_italia", giorni=None)
    )
    assert not ok
    assert motivazione == "numero di giornate non valido"


def test_giornate_zero_per_pasto():
    ok, motivazione = validator.valida(richiesta(categoria="pasto", giorni=0))
    assert not ok
    assert motivazione == "numero di giornate non valido"


def test_chilometri_non_validi():
    ok, motivazione = validator.valida(
        richiesta(categoria="chilometrico", km=0)
    )
    assert not ok
    assert motivazione == "numero di chilometri non valido"


def test_notti_non_valide():
    ok, motivazione = validator.valida(
        richiesta(categoria="alloggio", notti=None)
    )
    assert not ok
    assert motivazione == "numero di notti non valido"


def test_chilometrico_valido():
    assert validator.valida(
        richiesta(categoria="chilometrico", km=120, giorni=None)
    ) == (True, "")


def test_alloggio_valido():
    assert validator.valida(
        richiesta(categoria="alloggio", notti=3, giorni=None)
    ) == (True, "")


def test_lavoro_agile_valido_dal_2026():
    assert validator.valida(
        richiesta(categoria="lavoro_agile", data="2026-01-15", giorni=3)
    ) == (True, "")


def test_lavoro_agile_non_ammesso_prima_del_2026():
    ok, motivazione = validator.valida(
        richiesta(categoria="lavoro_agile", data="2025-12-31", giorni=3)
    )
    assert not ok
    assert motivazione == "categoria non riconosciuta"


def test_lavoro_agile_giornate_non_valide():
    ok, motivazione = validator.valida(
        richiesta(categoria="lavoro_agile", data="2026-01-15", giorni=0)
    )
    assert not ok
    assert motivazione == "numero di giornate non valido"
