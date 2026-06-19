from src import calculator


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


class TestMassimaleTeorico:
    def test_trasferta_italia(self):
        r = richiesta(categoria="trasferta_italia", giorni=4)
        assert calculator.massimale_teorico(r) == 185.92

    def test_trasferta_estero(self):
        r = richiesta(categoria="trasferta_estero", giorni=3)
        assert calculator.massimale_teorico(r) == 232.41

    def test_pasto(self):
        r = richiesta(categoria="pasto", giorni=5)
        assert calculator.massimale_teorico(r) == 40.0

    def test_chilometrico(self):
        r = richiesta(categoria="chilometrico", km=250)
        assert calculator.massimale_teorico(r) == 105.0

    def test_alloggio(self):
        r = richiesta(categoria="alloggio", notti=2)
        assert calculator.massimale_teorico(r) == 300.0


class TestCalcola:
    def test_importo_sotto_massimale_tutto_esente(self):
        r = richiesta(categoria="pasto", giorni=5, importo=35.0)
        esente, imponibile, _ = calculator.calcola(r, esente_gia_riconosciuta=0.0)
        assert esente == 35.0
        assert imponibile == 0.0

    def test_importo_sopra_massimale_eccedenza_imponibile(self):
        r = richiesta(categoria="trasferta_italia", giorni=2, importo=120.0)
        esente, imponibile, _ = calculator.calcola(r, esente_gia_riconosciuta=0.0)
        assert esente == 92.96
        assert imponibile == 27.04

    def test_plafond_incapiente_limita_la_quota_esente(self):
        r = richiesta(categoria="alloggio", notti=2, importo=300.0)
        esente, imponibile, _ = calculator.calcola(r, esente_gia_riconosciuta=1100.0)
        assert esente == 100.0
        assert imponibile == 200.0

    def test_plafond_esaurito_tutto_imponibile(self):
        r = richiesta(categoria="pasto", giorni=1, importo=8.0)
        esente, imponibile, _ = calculator.calcola(r, esente_gia_riconosciuta=1200.0)
        assert esente == 0.0
        assert imponibile == 8.0

    def test_dettaglio_del_calcolo(self):
        r = richiesta(categoria="trasferta_estero", giorni=2, importo=200.0)
        _, _, dettaglio = calculator.calcola(r, esente_gia_riconosciuta=1100.0)
        assert dettaglio == {
            "massimale_teorico": 154.94,
            "esente_teorica": 154.94,
            "capienza_plafond": 100.0,
        }


def richiesta_2026(**campi):
    return richiesta(data="2026-03-09", **campi)


class TestMassimaleTeorico2026:
    def test_trasferta_italia(self):
        r = richiesta_2026(categoria="trasferta_italia", giorni=4)
        assert calculator.massimale_teorico(r) == 200.0

    def test_trasferta_estero_fino_a_5_giorni(self):
        r = richiesta_2026(categoria="trasferta_estero", giorni=3)
        assert calculator.massimale_teorico(r) == 255.0

    def test_pasto(self):
        r = richiesta_2026(categoria="pasto", giorni=5)
        assert calculator.massimale_teorico(r) == 50.0

    def test_chilometrico(self):
        r = richiesta_2026(categoria="chilometrico", km=250)
        assert calculator.massimale_teorico(r) == 112.5

    def test_alloggio(self):
        r = richiesta_2026(categoria="alloggio", notti=2)
        assert calculator.massimale_teorico(r) == 340.0


class TestTrasfertaEsteroRiduzioneProgressiva:
    def test_12_giornate(self):
        # (5×85) + (5×76.50) + (2×68) = 425 + 382.50 + 136 = 943.50
        r = richiesta_2026(categoria="trasferta_estero", giorni=12)
        assert calculator.massimale_teorico(r) == 943.5

    def test_6_giornate_a_cavallo_soglia(self):
        # (5×85) + (1×76.50) = 501.50  (Caso 6.2)
        r = richiesta_2026(categoria="trasferta_estero", giorni=6)
        assert calculator.massimale_teorico(r) == 501.5

    def test_5_giornate_esatte_nessuna_riduzione(self):
        r = richiesta_2026(categoria="trasferta_estero", giorni=5)
        assert calculator.massimale_teorico(r) == 425.0

    def test_inizio_2025_resta_massimale_costante(self):
        # Trasferta estera con inizio nel 2025: massimale previgente, nessuna riduzione.
        r = richiesta(data="2025-12-30", categoria="trasferta_estero", giorni=8)
        assert calculator.massimale_teorico(r) == round(8 * 77.47, 2)


class TestLavoroAgile:
    def test_oltre_il_limite_mensile(self):
        # 15 giornate, nessun pregresso: ammesse 12, teorico 42.00 (Caso 6.4)
        r = richiesta_2026(categoria="lavoro_agile", giorni=15, importo=52.50)
        esente, imponibile, _ = calculator.calcola(r, esente_gia_riconosciuta=0.0)
        assert esente == 42.0
        assert imponibile == 10.5

    def test_residuo_mensile(self):
        # 6 richieste, 8 già rimborsate: ammesse min(6, 12-8)=4, teorico 14.00 (Sez. 3)
        r = richiesta_2026(categoria="lavoro_agile", giorni=6, importo=21.0)
        esente, imponibile, _ = calculator.calcola(
            r, esente_gia_riconosciuta=0.0, giornate_agile_gia=8
        )
        assert esente == 14.0
        assert imponibile == 7.0


class TestPlafond2026:
    def test_caso_6_1_capienza_residua(self):
        r = richiesta_2026(categoria="pasto", giorni=5, importo=50.0)
        esente, imponibile, _ = calculator.calcola(r, esente_gia_riconosciuta=1350.0)
        assert esente == 50.0
        assert imponibile == 0.0

    def test_caso_6_1_variante_capienza_ridotta(self):
        r = richiesta_2026(categoria="pasto", giorni=5, importo=50.0)
        esente, imponibile, _ = calculator.calcola(r, esente_gia_riconosciuta=1380.0)
        assert esente == 20.0
        assert imponibile == 30.0


class TestRegimeTransitorioBoundary:
    def test_ultimo_giorno_2025_massimale_previgente(self):
        r = richiesta(data="2025-12-31", categoria="pasto", giorni=1, importo=10.0)
        esente, imponibile, _ = calculator.calcola(r, esente_gia_riconosciuta=0.0)
        assert esente == 8.0
        assert imponibile == 2.0

    def test_primo_giorno_2026_massimale_nuovo(self):
        r = richiesta(data="2026-01-01", categoria="pasto", giorni=1, importo=10.0)
        esente, imponibile, _ = calculator.calcola(r, esente_gia_riconosciuta=0.0)
        assert esente == 10.0
        assert imponibile == 0.0
