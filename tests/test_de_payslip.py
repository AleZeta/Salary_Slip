import pytest

from src.de_parser import num
from src.de_payslip import da_inserimento_manuale, normalizza, tipo_pv, verifica_contributi

# Valori del caso di test del HANDOFF (luglio 2026), senza dati personali
LUGLIO = dict(
    kvRateTotal=17.29, childlessFlag=True,
    payments=[{"label": "Gehalt", "amount": 6250.0, "tax": "L", "sv": "L"},
              {"label": "Fahrtkosten", "amount": 59.85, "tax": "F", "sv": "F"}],
    totalGross=6309.85, taxGross=6250.0, wageTax=1162.5, kvGross=5812.5, rvGross=6250.0, avGross=6250.0, pvGross=5812.5,
    kv=502.49, rv=581.25, av=81.25, pv=139.5, taxTotal=1162.5, svTotal=1304.49, netIncome=3842.86,
    netItems=[{"label": "Abzug Lunch", "amount": -13.44}], payout=3829.42,
)


def test_num_formati_datev():
    assert num("50249") == 502.49          # senza virgola = centesimi
    assert num("5.81250") == 5812.50
    assert num("1.162,50") == 1162.50
    assert num("139,50 Z") == 139.50
    assert num("13,44-") == -13.44
    assert num("") is None and num(None) is None


def test_normalizza_caso_luglio_torna():
    d = normalizza(dict(LUGLIO))
    assert d["warnings"] == []
    assert d["agTotal"] is None


def test_normalizza_segnala_totali_errati():
    d = normalizza({**LUGLIO, "netIncome": 4000.0})
    assert "totals" in d["warnings"]


def test_verifica_contributi_ok():
    ver = verifica_contributi(normalizza(dict(LUGLIO)))
    assert ver["kv"]["atteso"] == 502.49 and all(v["ok"] for v in ver.values())


def test_pv_senza_figli():
    assert "senza figli" in tipo_pv(2.4)
    assert "con figli" in tipo_pv(1.8)


def test_manuale():
    d = da_inserimento_manuale(dict(month=7, year=2026, salary=6250.0, free=59.85, wageTax=1162.5, kv=502.49, rv=581.25,
                                    av=81.25, pv=139.5, ded=13.44))
    assert d["totalGross"] == pytest.approx(6309.85)
    assert d["payout"] == pytest.approx(6309.85 - 1162.5 - 1304.49 - 13.44)
    assert d["warnings"] == []


def test_etichette_con_spazi_tra_le_lettere():
    # DATEV stampa titoli e alcune etichette con spazi tra le lettere
    from src.de_parser import DE_PAGE, _eq, _senza_spazi
    assert DE_PAGE.search(_senza_spazi("A  b re c h n u n g   d e r  B r u tt o /N  e tt o -B e z ü g e"))
    assert _eq("S te u er- Br ut to", "Steuer-Brutto")


def test_parse_pagina_sintetica():
    from src.de_parser import parse
    it = lambda s, x, y, w=40: {"str": s, "x": x, "y": y, "w": w}
    pagina = [it("Abrechnung der Brutto/Netto-Bezüge", 48, 798), it("für August 2026", 246, 798),
              it("00090 090296 1", 48, 773), it("Gesamt-Brutto", 525, 379), it("Auszahlungsbetrag", 513, 91)]
    r = parse([pagina])
    assert r["ok"] and r["month"] == 8 and r["year"] == 2026 and r["taxClass"] == 1
    assert parse([[it("altro", 0, 0)]])["ok"] is False


def test_calcolo_da_stipendio_coincide_col_cedolino():
    from src.de_calc import calcola, einkommensteuer_32a
    d = calcola(75_000, 17.29, ha_figli=False)
    # valori stampati sul cedolino (stipendio 6.250 €/mese, Steuerklasse 1, senza figli)
    assert (d["wageTax"], d["kv"], d["rv"], d["av"], d["pv"]) == (1162.50, 502.49, 581.25, 81.25, 139.50)
    assert d["svTotal"] == 1304.49 and d["agSv"] == 1269.62
    assert einkommensteuer_32a(12_000) == 0
    assert normalizza(d)["warnings"] == []
    assert calcola(0)["payout"] == 0


def test_calcolo_con_bav_coincide_col_cedolino_di_ottobre():
    from src.de_calc import calcola
    d = calcola(75_000, 17.29, False, 0, 2026, bav_mensile=156.15, bav_datore_pct=30)
    assert (d["taxGross"], d["wageTax"], d["rv"], d["av"], d["kv"], d["pv"]) == (6093.85, 1108.58, 566.73, 79.22, 502.49, 139.50)
    assert d["svTotal"] == 1287.94
    assert d["bav"]["total"] == 203.0 and 85 < d["bav"]["netCost"] < 87
    assert normalizza(d)["warnings"] == []


def test_dati_bav_e_lordo_con_flag_n():
    from src.de_payslip import dati_bav
    d = normalizza({"payments": [
        {"label": "Gehalt", "amount": 6250.0, "tax": "L", "sv": "L", "gb": "J"},
        {"label": "Gehaltsverzicht, mtl.", "amount": -156.15, "tax": "L", "sv": "L", "gb": "N"},
        {"label": "Betr.AV,Geh.vz.lfd,§3Nr.63EStG", "amount": 156.15, "tax": "F", "sv": "F", "gb": "N"},
        {"label": "bAV AG-Pflichtz,lfd", "amount": 46.85, "tax": "F", "sv": "F", "gb": "N"}]})
    assert d["totalGross"] == 6250.0 and d["taxGross"] == 6093.85
    assert dati_bav(d) == {"conversion": 156.15, "employer": 46.85, "total": 203.0}


def test_report_html_in_inglese():
    from src.de_calc import calcola
    from src.de_render import report_html
    d = normalizza(calcola(75_000, 17.29, False, 0, 2026, bav_mensile=156.15, bav_datore_pct=30))
    en = report_html(d, lang="en")
    assert "Gross" in en and "Tap for details" in en and "€ 6,250.00" in en
    for parola in ("Stipendio", "Tocca", "Tasse e contributi", "Accreditato", "Pensione aziendale", "Imposta", "Lordo"):
        assert parola not in en
    assert "Tocca per i dettagli" in report_html(d, lang="it")
    assert "Tocca per i dettagli" in report_html(d)
