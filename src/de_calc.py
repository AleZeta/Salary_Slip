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


def calcola(ral: float, kk_totale: float = 17.29, ha_figli: bool = False, chiesa_pct: float = 0.0, anno: int = 2026,
            bav_mensile: float = 0.0, bav_datore_pct: float = 0.0) -> Dict:
    """Restituisce il dict del cedolino (stesso schema di de_parser, valori mensili) calcolato da `ral` annua.

    `kk_totale`: aliquota totale KV in % (14,6 + Zusatzbeitrag), divisa a metà. `chiesa_pct`: 0, 8 o 9.
    `bav_mensile`: tua Entgeltumwandlung mensile (Direktversicherung); `bav_datore_pct`: contributo del datore in % del tuo versamento.
    Limiti (§ 3 Nr. 63 EStG, § 1 SvEV) sul totale dei versamenti: 8% del tetto RV/AV esente da tasse, 4% esente da contributi.
    """
    r = DE_RATES.get(anno, DE_RATES[max(DE_RATES)])
    tetto_rv_annuo = r["tetto_rv_av"] * 12
    bav = max(0.0, bav_mensile) * 12
    bav_datore = bav * max(0.0, bav_datore_pct) / 100
    esente_tasse = min(bav, max(0.0, r["bav_esente_tasse"] * tetto_rv_annuo - bav_datore))
    esente_contributi = min(bav, max(0.0, r["bav_esente_contributi"] * tetto_rv_annuo - bav_datore))
    ral_fiscale = ral - esente_tasse
    ral_contributiva = ral - esente_contributi
    base_rv = min(ral_contributiva, tetto_rv_annuo)
    base_kv = min(ral_contributiva, r["tetto_kv_pv"] * 12)
    rv, av = base_rv * r["rv"], base_rv * r["av"]
    kv = base_kv * kk_totale / 200
    pv_rate = r["pv"] + (0.0 if ha_figli else r["pv_senza_figli"])
    pv = base_kv * pv_rate
    # Vorsorgepauschale: RV + KV (senza Krankengeld) + PV; AV non è deducibile in questo schema semplificato
    deducibile_sanita = base_kv * (kk_totale / 200 - KRANKENGELD_ESCLUSO) + pv
    zve = max(0.0, ral_fiscale - WERBUNGSKOSTEN_PAUSCHALE - SONDERAUSGABEN_PAUSCHALE - rv - deducibile_sanita)
    lst = einkommensteuer_32a(zve)
    soli = min(lst * 0.055, max(0.0, lst - SOLI_FREIGRENZE_2026) * 0.119)
    kist = lst * chiesa_pct / 100
    sv, tasse = kv + rv + av + pv, lst + soli + kist
    m = lambda v: round(v / 12, 2)
    ag_sv = m(base_rv * r["rv"] + base_rv * r["av"] + base_kv * kk_totale / 200 + base_kv * r["pv"])
    d = {
        "source": "calc", "year": anno, "taxClass": 1, "kvRateTotal": kk_totale, "childlessFlag": not ha_figli,
        "payments": [{"code": "", "label": "Gehalt (stipendio)", "amount": m(ral), "tax": "L", "sv": "L"}],
        "totalGross": m(ral), "taxGross": m(ral_fiscale), "wageTax": m(lst), "soli": m(soli), "church": m(kist),
        "kvGross": m(base_kv), "rvGross": m(base_rv), "avGross": m(base_rv), "pvGross": m(base_kv),
        "kv": m(kv), "rv": m(rv), "av": m(av), "pv": m(pv),
        "taxTotal": m(tasse), "svTotal": m(sv), "netIncome": m(ral - tasse - sv), "payout": m(ral - tasse - sv - bav),
        "netItems": [{"code": "", "label": "Versamento pensione aziendale (bAV)", "amount": -m(bav)}] if bav else [], "ytd": {},
        "agSv": ag_sv, "agAdd": None, "agTotal": round(m(ral) + ag_sv + m(bav_datore), 2),
        "zve": zve, "lohnsteuer_annua": lst,
    }
    if bav:
        senza = calcola(ral, kk_totale, ha_figli, chiesa_pct, anno)
        risparmio = (senza["taxTotal"] + senza["svTotal"]) - (d["taxTotal"] + d["svTotal"])
        d["bav"] = {"conversion": m(bav), "employer": m(bav_datore), "total": m(bav + bav_datore), "saving": round(risparmio, 2),
                    "netCost": round(m(bav) - risparmio, 2), "taxFree": m(esente_tasse), "svFree": m(esente_contributi)}
    return d
