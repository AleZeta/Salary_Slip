"""Calcolo RAL -> netto per un dipendente tedesco (Steuerklasse 1, assicurazione pubblica GKV).

Imposta calcolata in modo annuale (§ 32a EStG con Vorsorgepauschale semplificata): il Lohnsteuer mensile reale usa il
Programmablaufplan del Ministero delle Finanze e può differire di qualche euro.
"""

import math
from typing import Dict

from config.rates import DE_RATES

GRUNDFREIBETRAG_2026 = 12_348.0
WERBUNGSKOSTEN_PAUSCHALE = 1_230.0
SONDERAUSGABEN_PAUSCHALE = 36.0
SOLI_FREIGRENZE_2026 = 20_350.0
KRANKENGELD_ESCLUSO = 0.003  # metà dello 0,6% di Krankengeld, non deducibile nella Vorsorgepauschale


def einkommensteuer_32a(zve: float) -> float:
    """Grundtarif 2026: imposta in euro interi sul reddito imponibile annuo."""
    x = math.floor(max(zve, 0.0))
    if x <= 12_348:
        t = 0.0
    elif x <= 17_799:
        y = (x - 12_348) / 10_000
        t = (914.51 * y + 1_400) * y
    elif x <= 69_878:
        z = (x - 17_799) / 10_000
        t = (173.10 * z + 2_397) * z + 1_034.87
    elif x <= 277_825:
        t = 0.42 * x - 11_135.63
    else:
        t = 0.45 * x - 19_470.38
    return float(math.floor(t))


def calcola(ral: float, kk_totale: float = 17.29, ha_figli: bool = False, chiesa_pct: float = 0.0, anno: int = 2026) -> Dict:
    """Restituisce il dict del cedolino (stesso schema di de_parser, valori mensili) calcolato da `ral` annua.

    `kk_totale`: aliquota totale KV in % (14,6 + Zusatzbeitrag), divisa a metà. `chiesa_pct`: 0, 8 o 9.
    """
    r = DE_RATES.get(anno, DE_RATES[max(DE_RATES)])
    base_rv = min(ral, r["tetto_rv_av"] * 12)
    base_kv = min(ral, r["tetto_kv_pv"] * 12)
    rv, av = base_rv * r["rv"], base_rv * r["av"]
    kv = base_kv * kk_totale / 200
    pv_rate = r["pv"] + (0.0 if ha_figli else r["pv_senza_figli"])
    pv = base_kv * pv_rate
    # Vorsorgepauschale: RV + KV (senza Krankengeld) + PV; AV non è deducibile in questo schema semplificato
    deducibile_sanita = base_kv * (kk_totale / 200 - KRANKENGELD_ESCLUSO) + pv
    zve = max(0.0, ral - WERBUNGSKOSTEN_PAUSCHALE - SONDERAUSGABEN_PAUSCHALE - rv - deducibile_sanita)
    lst = einkommensteuer_32a(zve)
    soli = min(lst * 0.055, max(0.0, lst - SOLI_FREIGRENZE_2026) * 0.119)
    kist = lst * chiesa_pct / 100
    sv, tasse = kv + rv + av + pv, lst + soli + kist
    m = lambda v: round(v / 12, 2)
    ag_sv = m(base_rv * r["rv"] + base_rv * r["av"] + base_kv * kk_totale / 200 + base_kv * r["pv"])
    d = {
        "source": "calc", "year": anno, "taxClass": 1, "kvRateTotal": kk_totale, "childlessFlag": not ha_figli,
        "payments": [{"code": "", "label": "Gehalt (stipendio)", "amount": m(ral), "tax": "L", "sv": "L"}],
        "totalGross": m(ral), "taxGross": m(ral), "wageTax": m(lst), "soli": m(soli), "church": m(kist),
        "kvGross": m(base_kv), "rvGross": m(base_rv), "avGross": m(base_rv), "pvGross": m(base_kv),
        "kv": m(kv), "rv": m(rv), "av": m(av), "pv": m(pv),
        "taxTotal": m(tasse), "svTotal": m(sv), "netIncome": m(ral - tasse - sv), "payout": m(ral - tasse - sv),
        "netItems": [], "ytd": {}, "agSv": ag_sv, "agAdd": None, "agTotal": round(m(ral) + ag_sv, 2),
        "zve": zve, "lohnsteuer_annua": lst,
    }
    return d
