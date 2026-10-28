"""Calcolo del cedolino italiano (lavoratore dipendente privato) da RAL a netto, annuale e mensile.

Semplificazioni: anno intero di lavoro, nessun familiare a carico, nessun reddito oltre al lavoro dipendente,
imposta calcolata in modo annuale (il cedolino mensile reale applica ritenute progressive e il conguaglio a fine anno).
"""

from dataclasses import dataclass, field
from typing import Dict, List

from config.rates import IT_RATES

DIVISORE_TFR = 13.5  # art. 2120 c.c.: quota annua = retribuzione annua / 13,5 (rivalutazione esclusa)


@dataclass
class RisultatoIT:
    ral: float
    mensilita: int
    inps: float
    imponibile: float
    irpef_lorda: float
    scaglioni: List[Dict]
    detrazione_lavoro: float
    detrazione_cuneo: float
    irpef_netta: float
    add_regionale: float
    add_comunale: float
    bonus_cuneo: float
    netto: float
    tfr: float
    extra_ded: float = 0.0
    note: List[str] = field(default_factory=list)

    @property
    def trattenute(self) -> float:
        return self.inps + self.irpef_netta + self.add_regionale + self.add_comunale + self.extra_ded

    @property
    def netto_mensile(self) -> float:
        return self.netto / self.mensilita

    @property
    def lordo_mensile(self) -> float:
        return self.ral / self.mensilita


def irpef_per_scaglioni(imponibile: float, anno: int = 2026) -> tuple:
    """(imposta lorda, dettaglio scaglioni)."""
    prec, tot, det = 0.0, 0.0, []
    for tetto, aliq in IT_RATES[anno]["scaglioni"]:
        parte = max(0.0, min(imponibile, tetto) - prec)
        det.append({"da": prec, "a": tetto, "aliquota": aliq, "base": parte, "imposta": parte * aliq})
        tot += parte * aliq
        prec = tetto
    return tot, det


def detrazione_lavoro_dipendente(reddito: float) -> float:
    """Detrazione per lavoro dipendente (art. 13 TUIR, importi 2025-2026)."""
    r = reddito
    if r <= 15_000:
        return 1_955.0
    if r <= 28_000:
        return 1_910.0 + 1_190.0 * (28_000 - r) / 13_000
    if r <= 50_000:
        return 1_910.0 * (50_000 - r) / 22_000
    return 0.0


def cuneo_fiscale(reddito_lavoro: float, imponibile: float) -> tuple:
    """(bonus in busta, detrazione aggiuntiva) del taglio del cuneo fiscale (L. 207/2024)."""
    bonus = 0.0
    if reddito_lavoro <= 8_500:
        bonus = reddito_lavoro * 0.071
    elif reddito_lavoro <= 15_000:
        bonus = reddito_lavoro * 0.053
    elif reddito_lavoro <= 20_000:
        bonus = reddito_lavoro * 0.048
    detrazione = 0.0
    if 20_000 < imponibile <= 32_000:
        detrazione = 1_000.0
    elif 32_000 < imponibile <= 40_000:
        detrazione = 1_000.0 * (40_000 - imponibile) / 8_000
    return bonus, detrazione


def calcola(ral: float, mensilita: int = 13, add_regionale_pct: float = 1.73, add_comunale_pct: float = 0.8,
            anno: int = 2026, extra_ded_annue: float = 0.0, aliquota_inps: float = None) -> RisultatoIT:
    """RAL -> netto. `extra_ded_annue`: trattenute dopo il netto (fondo sanitario, sindacato, ecc.)."""
    r = IT_RATES[anno]
    inps = ral * (aliquota_inps if aliquota_inps is not None else r["inps_dipendente"])
    imponibile = max(0.0, ral - inps)
    lorda, scaglioni = irpef_per_scaglioni(imponibile, anno)
    det_lav = detrazione_lavoro_dipendente(imponibile)
    bonus, det_cuneo = cuneo_fiscale(ral, imponibile)
    netta = max(0.0, lorda - det_lav - det_cuneo)
    reg = imponibile * add_regionale_pct / 100
    com = imponibile * add_comunale_pct / 100
    netto = ral - inps - netta - reg - com + bonus - extra_ded_annue
    note = []
    if det_lav > lorda:
        note.append("La detrazione supera l'imposta lorda: l'IRPEF netta è zero (la parte eccedente non è rimborsata).")
    return RisultatoIT(ral=ral, mensilita=mensilita, inps=inps, imponibile=imponibile, irpef_lorda=lorda,
                       scaglioni=scaglioni, detrazione_lavoro=det_lav, detrazione_cuneo=det_cuneo, irpef_netta=netta,
                       add_regionale=reg, add_comunale=com, bonus_cuneo=bonus, netto=netto, tfr=ral / DIVISORE_TFR,
                       extra_ded=extra_ded_annue, note=note)
