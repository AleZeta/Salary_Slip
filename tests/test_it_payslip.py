import pytest

from src.it_payslip import calcola, cuneo_fiscale, detrazione_lavoro_dipendente, irpef_per_scaglioni


def test_irpef_scaglioni_40k():
    # imponibile 36.324 -> 28.000*23% + 8.324*33%
    lorda, _ = irpef_per_scaglioni(36_324)
    assert lorda == pytest.approx(28_000 * 0.23 + 8_324 * 0.33)


def test_detrazione_continua_alle_soglie():
    assert detrazione_lavoro_dipendente(15_000) == pytest.approx(1_955)
    assert detrazione_lavoro_dipendente(15_001) == pytest.approx(3_099.9, abs=0.1)  # salto previsto dalla norma
    assert detrazione_lavoro_dipendente(28_000) == pytest.approx(1_910)
    assert detrazione_lavoro_dipendente(50_000) == 0


def test_cuneo():
    assert cuneo_fiscale(10_000, 9_000)[0] == pytest.approx(530)
    assert cuneo_fiscale(30_000, 27_000)[1] == 1_000
    assert cuneo_fiscale(40_000, 36_000)[1] == pytest.approx(500)
    assert cuneo_fiscale(60_000, 55_000) == (0.0, 0.0)


def test_netto_coerente():
    r = calcola(40_000, 13, 1.73, 0.8)
    assert r.inps == pytest.approx(3_676)
    assert r.netto == pytest.approx(r.ral - r.trattenute + r.bonus_cuneo)
    assert 27_000 < r.netto < 29_000
    assert r.tfr == pytest.approx(40_000 / 13.5)


def test_ral_zero():
    r = calcola(0)
    assert r.netto == 0 and r.irpef_netta == 0


def test_render_italiano_e_formato_importi():
    from src.de_render import eur
    from src.it_render import report_html
    assert eur(-3676.0) == "− € 3.676,00" and eur(1234.5) == "€ 1.234,50"
    html = report_html(calcola(40_000, 13), 1.73, 0.8, 2100.0)
    assert "NETTO A PAGARE" in html and "Il tuo cedolino" in html


def test_parser_cedolino_sintetico():
    from src.it_parser import num, parse
    assert num("93", centesimi=True) == 0.93 and num("3298,15") == 3298.15 and num(",42") == 0.42
    assert num("1 0.143,05") == 10143.05 and num("2.286,00") == 2286.0
    it = lambda s, x, y, w=40: {"str": s, "x": x, "y": y, "w": w}
    pagina = [it("COD. PAS.", 49, 622), it("TOTALI", 360, 277), it("ARROTONDAMENTI", 346, 291),
              it("AA00 RETRIBUZIONE ORDINARIA", 51, 607), it("3298,15", 460, 607), it("AB86 TRATTENUTA MENSA", 51, 595), it("93", 570, 595),
              it("3.298,15", 449, 279), it("0,93", 530, 279), it("EURO", 463, 267), it("3.297,22", 456, 256)]
    r = parse([pagina])
    assert r["ok"] and r["totalComp"] == 3298.15 and r["netto"] == 3297.22 and r["warnings"] == []
    assert parse([[it("altro", 0, 0)]])["ok"] is False
