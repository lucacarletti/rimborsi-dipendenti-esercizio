from src import rules


def test_del_2026_soglia():
    assert rules._del_2026("2025-12-31") is False
    assert rules._del_2026("2026-01-01") is True


def test_del_2026_data_assente_o_invalida():
    assert rules._del_2026("") is False
    assert rules._del_2026(None) is False
    assert rules._del_2026("non-una-data") is False


def test_selettori_regime_previgente():
    assert rules.massimali_giornalieri("2025-12-31")["trasferta_italia"] == 46.48
    assert rules.massimale_km("2025-12-31") == 0.42
    assert rules.massimale_notte("2025-12-31") == 150.00
    assert rules.plafond_mensile("2025-12-31") == 1200.00


def test_selettori_regime_2026():
    assert rules.massimali_giornalieri("2026-01-01")["trasferta_italia"] == 50.00
    assert rules.massimale_km("2026-01-01") == 0.45
    assert rules.massimale_notte("2026-01-01") == 170.00
    assert rules.plafond_mensile("2026-01-01") == 1400.00


def test_categorie_ammesse_lavoro_agile_solo_dal_2026():
    assert "lavoro_agile" not in rules.categorie_ammesse("2025-12-31")
    assert "lavoro_agile" in rules.categorie_ammesse("2026-01-01")
