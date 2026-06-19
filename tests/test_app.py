import pytest

from src import storage
from src.app import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "PERCORSO_DATI", tmp_path / "richieste.json")
    app.config["TESTING"] = True
    return app.test_client()


def nuova_richiesta_pasto(client, **campi):
    dati = {
        "dipendente": "Maria Rossi",
        "data": "2025-10-06",
        "categoria": "pasto",
        "importo": "24.00",
        "giorni": "3",
    }
    dati.update(campi)
    return client.post("/nuova", data=dati)


def test_home_reindirizza_a_elenco(client):
    risposta = client.get("/")
    assert risposta.status_code == 302
    assert "/richieste" in risposta.headers["Location"]


def test_pagine_principali_raggiungibili(client):
    for percorso in ("/richieste", "/nuova", "/riepilogo", "/normativa"):
        assert client.get(percorso).status_code == 200


def test_registrazione_richiesta_valida(client):
    risposta = nuova_richiesta_pasto(client)
    assert risposta.status_code == 200
    assert "registrata" in risposta.get_data(as_text=True)

    richieste = storage.carica()
    assert len(richieste) == 1
    assert richieste[0]["stato"] == "valida"
    assert richieste[0]["quota_esente"] == 24.0
    assert richieste[0]["quota_imponibile"] == 0.0


def test_registrazione_richiesta_respinta(client):
    risposta = nuova_richiesta_pasto(client, importo="-10")
    assert "respinta" in risposta.get_data(as_text=True)
    assert "importo non positivo" in risposta.get_data(as_text=True)

    richieste = storage.carica()
    assert richieste[0]["stato"] == "respinta"
    assert richieste[0]["quota_esente"] == 0.0


def test_eccedenza_oltre_massimale_diventa_imponibile(client):
    nuova_richiesta_pasto(client, importo="30.00", giorni="3")
    richieste = storage.carica()
    assert richieste[0]["quota_esente"] == 24.0
    assert richieste[0]["quota_imponibile"] == 6.0


def test_plafond_mensile_condiviso_tra_richieste(client):
    nuova_richiesta_pasto(
        client, categoria="alloggio", notti="8", importo="1150.00", giorni=""
    )
    nuova_richiesta_pasto(client, importo="80.00", giorni="10")
    richieste = storage.carica()
    assert richieste[0]["quota_esente"] == 1150.0
    # Capienza residua: 1200 - 1150 = 50, quindi del pasto sono esenti solo 50.
    assert richieste[1]["quota_esente"] == 50.0
    assert richieste[1]["quota_imponibile"] == 30.0


def test_elenco_filtra_per_dipendente(client):
    nuova_richiesta_pasto(client, dipendente="Maria Rossi")
    nuova_richiesta_pasto(client, dipendente="Luca Bianchi")
    testo = client.get("/richieste?dipendente=Luca+Bianchi").get_data(as_text=True)
    assert "Luca Bianchi" in testo
    assert "Maria Rossi" not in testo.split("</thead>")[1].split("Clicca")[0]


def test_riepilogo_mostra_totali(client):
    nuova_richiesta_pasto(client)
    nuova_richiesta_pasto(client, importo="16.00", giorni="2")
    testo = client.get("/riepilogo").get_data(as_text=True)
    assert "Maria Rossi" in testo
    assert "40.00" in testo


def test_massimali_2026_applicati(client):
    nuova_richiesta_pasto(
        client, categoria="trasferta_italia", data="2026-02-10", importo="60.00", giorni="1"
    )
    richieste = storage.carica()
    assert richieste[0]["quota_esente"] == 50.0
    assert richieste[0]["quota_imponibile"] == 10.0


def test_lavoro_agile_respinto_prima_del_2026(client):
    risposta = nuova_richiesta_pasto(
        client, categoria="lavoro_agile", data="2025-12-31", importo="10.50", giorni="3"
    )
    testo = risposta.get_data(as_text=True)
    assert "respinta" in testo
    assert "categoria non riconosciuta" in testo


def test_lavoro_agile_valido_dal_2026(client):
    nuova_richiesta_pasto(
        client, categoria="lavoro_agile", data="2026-01-15", importo="10.50", giorni="3"
    )
    richieste = storage.carica()
    assert richieste[0]["stato"] == "valida"
    assert richieste[0]["quota_esente"] == 10.5


def test_incompatibilita_lavoro_agile_trasferta(client):
    # Trasferta nazionale 02-06/03/2026, poi lavoro agile 06-08/03/2026: la
    # giornata del 06/03 si sovrappone -> respinta integralmente (Caso 6.5).
    nuova_richiesta_pasto(
        client, categoria="trasferta_italia", data="2026-03-02", importo="200.00", giorni="5"
    )
    risposta = nuova_richiesta_pasto(
        client, categoria="lavoro_agile", data="2026-03-06", importo="10.50", giorni="3"
    )
    testo = risposta.get_data(as_text=True)
    assert "respinta" in testo
    assert "incompatibilità lavoro agile / trasferta" in testo


def test_lavoro_agile_senza_sovrapposizione_valido(client):
    nuova_richiesta_pasto(
        client, categoria="trasferta_italia", data="2026-03-02", importo="200.00", giorni="3"
    )
    # Trasferta copre 02-04/03; lavoro agile dal 05/03 non si sovrappone.
    nuova_richiesta_pasto(
        client, categoria="lavoro_agile", data="2026-03-05", importo="7.00", giorni="2"
    )
    richieste = storage.carica()
    assert richieste[1]["stato"] == "valida"


def test_plafond_2026_da_1400(client):
    # Alloggio 2026: 9 notti × 170 = 1530 teorico, ma plafond 2026 = 1400.
    nuova_richiesta_pasto(
        client, categoria="alloggio", data="2026-04-10", importo="1530.00", notti="9", giorni=""
    )
    richieste = storage.carica()
    assert richieste[0]["quota_esente"] == 1400.0
    assert richieste[0]["quota_imponibile"] == 130.0


def test_normativa_mostra_massimali_vigenti(client):
    testo = client.get("/normativa").get_data(as_text=True)
    assert "50.00" in testo
    assert "85.00" in testo
    assert "1400.00" in testo
    assert "Indennità lavoro agile" in testo
    assert "Circolare MEF n. 18/2026" in testo
