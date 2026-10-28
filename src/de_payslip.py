"""Normalizzazione e spiegazione di un cedolino tedesco (da PDF DATEV o inserimento manuale)."""

import re
from typing import Dict, List, Optional

from config.rates import DE_RATES

CAMPI_NUM = ["totalGross", "taxGross", "wageTax", "church", "soli", "kvGross", "rvGross", "avGross", "pvGross",
             "kv", "rv", "av", "pv", "taxTotal", "svTotal", "netIncome", "payout", "agSv", "agAdd", "agTotal",
             "kvRateTotal"]

# Classificazione delle voci lorde: (regex, chiave, titolo, spiegazione)
VOCI_LORDE = [
    (r"entgeltumwandlung|\bbav\b|direktversicherung|pensionskasse|pensionsfonds|altersvorsorge|deferred", "Pensione aziendale (conversione)",
     "Entgeltumwandlung: parte del lordo versata nella pensione aziendale, esente da tasse e contributi entro i limiti di legge."),
    (r"urlaubsgeld|holiday pay", "Indennità ferie", "Urlaubsgeld: pagamento extra legato alle ferie, di solito tassato come una tantum."),
    (r"weihnacht|christmas|13\.\s*gehalt", "Tredicesima / gratifica natalizia", "Weihnachtsgeld: extra di fine anno, tassato come una tantum."),
    (r"bonus|prämie|praemie|tantieme|erfolgsbeteiligung|incentive", "Bonus", "Premio tassato come pagamento una tantum (sonstiger Bezug)."),
    (r"überstund|ueberstund|overtime|mehrarbeit", "Straordinari", "Ore extra o supplementi pagati questo mese."),
    (r"zuschlag|nacht|sonntag|feiertag", "Maggiorazione", "Supplemento per lavoro notturno, festivo o domenicale."),
    (r"fahrt|travel|jobticket|deutschlandticket|reise", "Rimborso spese di viaggio",
     "Rimborso per tragitto casa-lavoro o trasferte. Se esente (F), non paghi tasse né contributi."),
    (r"vwl|vermögenswirksam|vermoegenswirksam", "Contributo risparmio (VWL)", "Vermögenswirksame Leistungen: contributo del datore a un piano di risparmio."),
    (r"sachbezug|gutschein|benefit|voucher", "Benefit in natura", "Sachbezug: buoni o benefit esenti fino a 50 € al mese."),
    (r"dienstwagen|firmenwagen|company car|geldw|pkw", "Auto aziendale", "Valore dell'uso privato (geldwerter Vorteil): aumenta le tasse, non è pagato in contanti."),
    (r"gehalt|salary|grundlohn|lohn|stipendio", "Stipendio base", "Il tuo stipendio mensile regolare."),
]
VOCI_NETTO = [
    (r"lunch|kantine|essen|mensa|canteen|meal", "Mensa", "La tua quota per i pasti in mensa o i buoni pasto."),
    (r"rad|bike|fahrrad|leasing", "Bici aziendale", "Rata del leasing della bici (JobRad) trattenuta dal netto."),
    (r"vorschuss|advance|abschlag", "Anticipo", "Restituzione di un anticipo già ricevuto."),
    (r"pfändung|pfaendung|garnish", "Pignoramento", "Somma trattenuta per un pignoramento dello stipendio."),
]
FLAG = {"F": "Esente da tasse e contributi.", "L": "Regolare, tassata e soggetta a contributi.",
        "S": "Pagamento una tantum: tassato con un metodo annuale.", "E": "Pagamento una tantum: tassato con un metodo annuale.",
        "M": "Pagamento una tantum: tassato con un metodo annuale."}
CLASSI = {1: "Single o separati.", 2: "Genitore single.", 3: "Sposati, coniuge con reddito più alto (l'altro in classe 5).",
          4: "Sposati con redditi simili.", 5: "Sposati, coniuge con reddito più basso.", 6: "Secondo lavoro."}


def _classifica(label: str, tabella, default) -> tuple:
    s = (label or "").lower()
    for rx, titolo, spiega in tabella:
        if re.search(rx, s):
            return titolo, spiega
    return default


def classifica_voce_lorda(label: str) -> tuple:
    return _classifica(label, VOCI_LORDE, ("Voce di stipendio", "Voce del lordo indicata sul cedolino."))


def classifica_voce_netto(label: str) -> tuple:
    return _classifica(label, VOCI_NETTO, ("Trattenuta dopo il netto", "Voce tolta o aggiunta dopo tasse e contributi."))


def testo_flag(*flags: str) -> str:
    return " ".join(dict.fromkeys(FLAG[f] for f in flags if f in FLAG))


def normalizza(d: Dict) -> Dict:
    """Completa i campi mancanti e aggiunge `warnings` se i totali non tornano."""
    n = lambda x: None if x is None else float(x)
    for k in CAMPI_NUM:
        d[k] = n(d.get(k))
    d["payments"] = [{"code": p.get("code", ""), "label": p.get("label", ""), "amount": n(p.get("amount")) or 0.0,
                      "tax": (p.get("tax") or "").upper(), "sv": (p.get("sv") or "").upper()} for p in d.get("payments") or []]
    d["netItems"] = [{"code": p.get("code", ""), "label": p.get("label", ""), "amount": n(p.get("amount")) or 0.0}
                     for p in d.get("netItems") or []]
    for k in ("wageTax", "church", "soli", "kv", "rv", "av", "pv"):
        if d[k] is None:
            d[k] = 0.0
    if d["totalGross"] is None:
        d["totalGross"] = sum(p["amount"] for p in d["payments"])
    if d["taxTotal"] is None:
        d["taxTotal"] = d["wageTax"] + d["church"] + d["soli"]
    if d["svTotal"] is None:
        d["svTotal"] = d["kv"] + d["rv"] + d["av"] + d["pv"]
    if d["netIncome"] is None:
        d["netIncome"] = d["totalGross"] - d["taxTotal"] - d["svTotal"]
    voci_netto = sum(p["amount"] for p in d["netItems"])
    if d["payout"] is None:
        d["payout"] = d["netIncome"] + voci_netto
    if d["taxGross"] is None:
        d["taxGross"] = sum(p["amount"] for p in d["payments"] if p["tax"] != "F")
    if d["agTotal"] is None and d["agSv"] is not None:
        d["agTotal"] = d["totalGross"] + d["agSv"] + (d["agAdd"] or 0.0)
    d.setdefault("ytd", {})
    warn = list(d.get("warnings") or [])
    if abs(d["totalGross"] - d["taxTotal"] - d["svTotal"] - d["netIncome"]) > 0.05 \
            or abs(d["netIncome"] + voci_netto - d["payout"]) > 0.05:
        warn.append("totals")
    d["warnings"] = warn
    return d


def da_inserimento_manuale(v: Dict) -> Dict:
    """Costruisce il dict del cedolino dai valori del form manuale (importi mensili)."""
    pay = []
    if v.get("salary"):
        pay.append({"label": "Gehalt (stipendio)", "amount": v["salary"], "tax": "L", "sv": "L"})
    if v.get("other"):
        pay.append({"label": "Altre voci tassate", "amount": v["other"], "tax": "S", "sv": "S"})
    if v.get("free"):
        pay.append({"label": "Voci esenti", "amount": v["free"], "tax": "F", "sv": "F"})
    d = {k: v.get(k) for k in ("month", "year", "employer", "taxClass", "kvRateTotal", "childlessFlag",
                                "wageTax", "soli", "church", "kv", "rv", "av", "pv", "payout", "agSv")}
    d.update(source="manual", payments=pay, ytd={},
             taxGross=(v.get("salary") or 0) + (v.get("other") or 0),
             netItems=[{"label": "Trattenute dopo il netto", "amount": -abs(v["ded"])}] if v.get("ded") else [])
    return normalizza(d)


def aliquota_pv(d: Dict) -> Optional[float]:
    """Aliquota PV effettiva (%) se nota la base contributiva."""
    return d["pv"] / d["pvGross"] * 100 if d.get("pvGross") else None


def tipo_pv(rate: Optional[float], childless_flag: bool = False) -> str:
    if rate is None:
        return "senza figli (supplemento 0,6%, indicato con Z)" if childless_flag else ""
    if abs(rate - 2.4) < 0.03:
        return "senza figli (1,8% + 0,6% di supplemento, indicato con Z)"
    if abs(rate - 1.8) < 0.03:
        return "con figli (1,8%)"
    if abs(rate - 2.3) < 0.03 or abs(rate - 2.9) < 0.03:
        return "aliquota della Sassonia"
    if rate < 1.8:
        return "ridotta per più figli sotto i 25 anni"
    return ""


def verifica_contributi(d: Dict) -> Dict[str, Dict]:
    """Ricalcola KV/RV/AV dalle basi e confronta con il cedolino. Ritorna {chiave: {base, aliquota, atteso, cedolino, ok}}."""
    righe = {}
    kk = d.get("kvRateTotal")
    voci = []
    if kk and d.get("kvGross"):
        voci.append(("kv", d["kvGross"], kk / 2, d["kv"]))
    if d.get("rvGross"):
        voci.append(("rv", d["rvGross"], 9.3, d["rv"]))
    if d.get("avGross"):
        voci.append(("av", d["avGross"], 1.3, d["av"]))
    for nome, base, aliq, val in voci:
        atteso = round(base * aliq / 100, 2)
        righe[nome] = {"base": base, "aliquota": aliq, "atteso": atteso, "cedolino": val, "ok": abs(atteso - val) <= 0.06}
    return righe


def note_tetto(d: Dict) -> List[str]:
    """Avvisa quando la base KV/RV è sotto l'imponibile fiscale: sono scattati i tetti contributivi."""
    note = []
    for k, nome in (("kvGross", "sanitaria (KV/PV)"), ("rvGross", "pensione (RV/AV)")):
        if d.get(k) and d.get("taxGross") and d[k] < d["taxGross"] - 1:
            note.append(f"La base per {nome} è {d[k]:,.2f} € e non l'intero stipendio: è il tetto mensile "
                        "di contribuzione (Beitragsbemessungsgrenze). Sopra questa cifra non si paga.")
    return note


def tetti(anno: int) -> Dict:
    return DE_RATES.get(anno, DE_RATES[max(DE_RATES)])
