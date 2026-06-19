"""Webapp Flask per la gestione dei rimborsi spese dei dipendenti."""

from datetime import date, timedelta

from flask import Flask, redirect, render_template, request, url_for

from src import calculator, rules, storage, validator

app = Flask(__name__)


def _numero(valore):
    try:
        return float(valore)
    except (TypeError, ValueError):
        return None


def _intero(valore):
    try:
        return int(valore)
    except (TypeError, ValueError):
        return None


def _giornate(richiesta):
    """Intervallo (inizio, fine) coperto dalla richiesta, come date contigue."""
    inizio = date.fromisoformat(richiesta["data"])
    giorni = richiesta.get("giorni") or 1
    return inizio, inizio + timedelta(days=giorni - 1)


def _incompatibile(richiesta, richieste):
    """True se la richiesta viola l'incompatibilità lavoro agile / trasferta.

    Regola in vigore dal 01/01/2026 (Sezione 5): nella stessa giornata, per lo
    stesso dipendente, l'indennità di lavoro agile e qualsiasi indennità di
    trasferta sono mutuamente esclusive. Rilevano solo le richieste valide.
    """
    if not rules._del_2026(richiesta["data"]):
        return False
    categoria = richiesta["categoria"]
    if categoria == "lavoro_agile":
        opposte = set(rules.CATEGORIE_TRASFERTA)
    elif categoria in rules.CATEGORIE_TRASFERTA:
        opposte = {"lavoro_agile"}
    else:
        return False

    inizio, fine = _giornate(richiesta)
    for altra in richieste:
        if (
            altra["dipendente"] == richiesta["dipendente"]
            and altra["stato"] == "valida"
            and altra["categoria"] in opposte
        ):
            altra_inizio, altra_fine = _giornate(altra)
            if inizio <= altra_fine and altra_inizio <= fine:
                return True
    return False


def _registra(form):
    """Valida, calcola e registra una nuova richiesta. Restituisce la richiesta salvata."""
    richieste = storage.carica()
    richiesta = {
        "id": storage.prossimo_id(richieste),
        "dipendente": (form.get("dipendente") or "").strip(),
        "data": form.get("data") or "",
        "categoria": form.get("categoria") or "",
        "importo": _numero(form.get("importo")),
        "giorni": _intero(form.get("giorni")),
        "km": _numero(form.get("km")),
        "notti": _intero(form.get("notti")),
    }
    ok, motivazione = validator.valida(richiesta)
    if ok and _incompatibile(richiesta, richieste):
        ok, motivazione = False, "incompatibilità lavoro agile / trasferta"
    if ok:
        mese = storage.mese(richiesta)
        gia_riconosciuta = storage.esente_riconosciuta_nel_mese(
            richieste, richiesta["dipendente"], mese
        )
        giornate_agile_gia = storage.giornate_lavoro_agile_nel_mese(
            richieste, richiesta["dipendente"], mese
        )
        esente, imponibile, dettaglio = calculator.calcola(
            richiesta, gia_riconosciuta, giornate_agile_gia
        )
        richiesta.update(
            stato="valida",
            motivazione="",
            quota_esente=esente,
            quota_imponibile=imponibile,
            dettaglio=dettaglio,
        )
    else:
        richiesta.update(
            stato="respinta",
            motivazione=motivazione,
            quota_esente=0.0,
            quota_imponibile=0.0,
            dettaglio=None,
        )
    richieste.append(richiesta)
    storage.salva(richieste)
    return richiesta


@app.get("/")
def home():
    return redirect(url_for("elenco"))


@app.route("/nuova", methods=["GET", "POST"])
def nuova_richiesta():
    esito = None
    if request.method == "POST":
        esito = _registra(request.form)
    return render_template("nuova_richiesta.html", categorie=rules.CATEGORIE, esito=esito)


@app.get("/richieste")
def elenco():
    richieste = storage.carica()
    dipendente = request.args.get("dipendente", "")
    mese = request.args.get("mese", "")
    filtrate = [
        r
        for r in richieste
        if (not dipendente or r["dipendente"] == dipendente)
        and (not mese or storage.mese(r) == mese)
    ]
    filtrate.sort(key=lambda r: (r["data"], r["id"]), reverse=True)
    return render_template(
        "elenco.html",
        richieste=filtrate,
        categorie=rules.CATEGORIE,
        dipendenti=sorted({r["dipendente"] for r in richieste}),
        mesi=sorted({storage.mese(r) for r in richieste}, reverse=True),
        filtro_dipendente=dipendente,
        filtro_mese=mese,
    )


@app.get("/riepilogo")
def riepilogo():
    richieste = storage.carica()
    gruppi = {}
    for r in richieste:
        if r["stato"] != "valida":
            continue
        chiave = (storage.mese(r), r["dipendente"])
        gruppo = gruppi.setdefault(
            chiave, {"esente": 0.0, "imponibile": 0.0, "richieste": 0}
        )
        gruppo["esente"] = round(gruppo["esente"] + r["quota_esente"], 2)
        gruppo["imponibile"] = round(gruppo["imponibile"] + r["quota_imponibile"], 2)
        gruppo["richieste"] += 1
    righe = [
        {
            "mese": mese,
            "dipendente": dipendente,
            "esente": dati["esente"],
            "imponibile": dati["imponibile"],
            "richieste": dati["richieste"],
            "percentuale_plafond": min(
                round(dati["esente"] / rules.plafond_mensile(mese + "-01") * 100), 100
            ),
        }
        for (mese, dipendente), dati in sorted(gruppi.items(), reverse=True)
    ]
    return render_template(
        "riepilogo.html",
        righe=righe,
        plafond=rules.PLAFOND_2026,
        plafond_previgente=rules.PLAFOND_2025,
    )


@app.get("/normativa")
def normativa():
    return render_template("normativa.html", rules=rules)


if __name__ == "__main__":
    app.run(debug=True)
