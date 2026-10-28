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
