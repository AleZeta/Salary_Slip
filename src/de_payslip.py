"""Normalizzazione e spiegazione di un cedolino tedesco (da PDF DATEV o inserimento manuale)."""

import re
from typing import Dict, List, Optional

from config.rates import DE_RATES

CAMPI_NUM = ["totalGross", "taxGross", "wageTax", "church", "soli", "kvGross", "rvGross", "avGross", "pvGross",
             "kv", "rv", "av", "pv", "taxTotal", "svTotal", "netIncome", "payout", "agSv", "agAdd", "agTotal",
             "kvRateTotal"]

# Classificazione delle voci lorde: (regex, titolo_it, spiegazione_it, titolo_en, spiegazione_en)
VOCI_LORDE = [
    (r"ag-?pflichtz|arbeitgeberzuschuss|pens\.?sch\.?empl|empl\.?\s*sub", "Contributo del datore alla pensione",
     "Il contributo che il datore aggiunge al tuo versamento nella pensione aziendale (bAV). Non fa parte del lordo e non paghi tasse né contributi.",
     "Employer pension contribution",
     "The contribution your employer adds to your occupational pension (bAV) payment. It is not part of your gross pay and you pay no tax or social contributions on it."),
    (r"gehaltsverzicht|salary cut|geh\.?\s*vz", "Riduzione stipendio (conversione bAV)",
     "Entgeltumwandlung: la parte del lordo che rinunci a ricevere in busta e che va nella pensione aziendale. Riduce l'imponibile fiscale e in parte quello contributivo.",
     "Salary reduction (bAV conversion)",
     "Entgeltumwandlung: the part of your gross pay you give up and that goes into the occupational pension. It lowers your taxable income and, partly, your social-contribution base."),
    (r"betr\.?\s*av|comp\.?\s*pens\.?\s*sal|§\s*3\s*nr", "Versamento nella pensione aziendale",
     "Il tuo versamento nella pensione aziendale (§ 3 Nr. 63 EStG), esente da tasse e contributi entro i limiti di legge.",
     "Occupational pension payment",
     "Your payment into the occupational pension (§ 3 Nr. 63 EStG), exempt from tax and social contributions within the legal limits."),
    (r"wellpass|egym|fitness|palestra|gym", "Wellpass (palestra)",
     "Benefit in natura (Sachbezug) per la palestra: esente da tasse e contributi, ma lo stesso importo viene tolto dopo il netto, più la tua quota.",
     "Wellpass (gym)",
     "Benefit in kind (Sachbezug) for the gym: exempt from tax and social contributions, but the same amount is taken off after net pay, plus your own share."),
    (r"entgeltumwandlung|\bbav\b|direktversicherung|pensionskasse|pensionsfonds|altersvorsorge|deferred", "Pensione aziendale (conversione)",
     "Entgeltumwandlung: parte del lordo versata nella pensione aziendale, esente da tasse e contributi entro i limiti di legge.",
     "Occupational pension (conversion)",
     "Entgeltumwandlung: part of your gross pay paid into the occupational pension, exempt from tax and social contributions within the legal limits."),
    (r"urlaubsgeld|holiday pay", "Indennità ferie", "Urlaubsgeld: pagamento extra legato alle ferie, di solito tassato come una tantum.",
     "Holiday pay", "Urlaubsgeld: an extra payment tied to vacation, usually taxed as a one-off payment."),
    (r"weihnacht|christmas|13\.\s*gehalt", "Tredicesima / gratifica natalizia", "Weihnachtsgeld: extra di fine anno, tassato come una tantum.",
     "Christmas bonus / 13th salary", "Weihnachtsgeld: a year-end extra, taxed as a one-off payment."),
    (r"bonus|prämie|praemie|tantieme|erfolgsbeteiligung|incentive", "Bonus", "Premio tassato come pagamento una tantum (sonstiger Bezug).",
     "Bonus", "A bonus taxed as a one-off payment (sonstiger Bezug)."),
    (r"überstund|ueberstund|overtime|mehrarbeit", "Straordinari", "Ore extra o supplementi pagati questo mese.",
     "Overtime", "Extra hours or supplements paid this month."),
    (r"zuschlag|nacht|sonntag|feiertag", "Maggiorazione", "Supplemento per lavoro notturno, festivo o domenicale.",
     "Premium pay", "Supplement for night, holiday or Sunday work."),
    (r"fahrt|travel|jobticket|deutschlandticket|reise", "Rimborso spese di viaggio",
     "Rimborso per tragitto casa-lavoro o trasferte. Se esente (F), non paghi tasse né contributi.",
     "Travel reimbursement",
     "Reimbursement for commuting or business trips. If exempt (F), you pay no tax or social contributions."),
    (r"vwl|vermögenswirksam|vermoegenswirksam", "Contributo risparmio (VWL)", "Vermögenswirksame Leistungen: contributo del datore a un piano di risparmio.",
     "Savings contribution (VWL)", "Vermögenswirksame Leistungen: an employer contribution to a savings plan."),
    (r"sachbezug|gutschein|benefit|voucher", "Benefit in natura", "Sachbezug: buoni o benefit esenti fino a 50 € al mese.",
     "Benefit in kind", "Sachbezug: vouchers or benefits exempt up to €50 per month."),
    (r"dienstwagen|firmenwagen|company car|geldw|pkw", "Auto aziendale", "Valore dell'uso privato (geldwerter Vorteil): aumenta le tasse, non è pagato in contanti.",
     "Company car", "Value of private use (geldwerter Vorteil): it raises your taxes and is not paid out in cash."),
    (r"gehalt|salary|grundlohn|lohn|stipendio", "Stipendio base", "Il tuo stipendio mensile regolare.",
     "Base salary", "Your regular monthly salary."),
]
VOCI_NETTO = [
    (r"eigenanteil.*(wellpass|egym)|(wellpass|egym).*eigenanteil", "Wellpass: quota tua", "La parte dell'abbonamento palestra che paghi tu, tolta dal netto.",
     "Wellpass: your share", "The part of the gym membership you pay yourself, taken off your net pay."),
    (r"wellpass|egym", "Wellpass: benefit", "Compensa il benefit in natura mostrato nel lordo: l'effetto sul netto è nullo.",
     "Wellpass: benefit", "Offsets the benefit in kind shown in gross pay: the net effect is zero."),
    (r"gehaltsverzicht|bav|entgeltumw", "Versamento pensione aziendale", "Il tuo versamento nella bAV, già escluso da tasse e contributi nel lordo e qui tolto dal netto.",
     "Pension payment", "Your bAV payment, already excluded from tax and contributions in gross pay and deducted here from net pay."),
    (r"lunch|kantine|essen|mensa|canteen|meal", "Mensa", "La tua quota per i pasti in mensa o i buoni pasto.",
     "Canteen", "Your share of canteen meals or meal vouchers."),
    (r"rad|bike|fahrrad|leasing", "Bici aziendale", "Rata del leasing della bici (JobRad) trattenuta dal netto.",
     "Company bike", "Bike lease instalment (JobRad) deducted from net pay."),
    (r"vorschuss|advance|abschlag", "Anticipo", "Restituzione di un anticipo già ricevuto.",
     "Advance", "Repayment of an advance already received."),
    (r"pfändung|pfaendung|garnish", "Pignoramento", "Somma trattenuta per un pignoramento dello stipendio.",
     "Garnishment", "Amount withheld for a wage garnishment."),
]
FLAG = {"F": "Esente da tasse e contributi.", "L": "Regolare, tassata e soggetta a contributi.",
        "S": "Pagamento una tantum: tassato con un metodo annuale.", "E": "Pagamento una tantum: tassato con un metodo annuale.",
        "M": "Pagamento una tantum: tassato con un metodo annuale."}
FLAG_EN = {"F": "Exempt from tax and social contributions.", "L": "Regular pay, taxed and subject to contributions.",
           "S": "One-off payment: taxed with an annual method.", "E": "One-off payment: taxed with an annual method.",
           "M": "One-off payment: taxed with an annual method."}
CLASSI = {1: "Single o separati.", 2: "Genitore single.", 3: "Sposati, coniuge con reddito più alto (l'altro in classe 5).",
          4: "Sposati con redditi simili.", 5: "Sposati, coniuge con reddito più basso.", 6: "Secondo lavoro."}
CLASSI_EN = {1: "Single or separated.", 2: "Single parent.", 3: "Married, spouse with the higher income (the other in class 5).",
             4: "Married with similar incomes.", 5: "Married, spouse with the lower income.", 6: "Second job."}


def classi(lang: str = "it") -> Dict:
    return CLASSI_EN if lang == "en" else CLASSI


def _classifica(label: str, tabella, default, lang: str = "it") -> tuple:
    s = (label or "").lower()
    for rx, t_it, s_it, t_en, s_en in tabella:
        if re.search(rx, s):
            return (t_en, s_en) if lang == "en" else (t_it, s_it)
    return default


def classifica_voce_lorda(label: str, lang: str = "it") -> tuple:
    default = ("Salary item", "Item of gross pay listed on the payslip.") if lang == "en" else ("Voce di stipendio", "Voce del lordo indicata sul cedolino.")
    return _classifica(label, VOCI_LORDE, default, lang)


def classifica_voce_netto(label: str, lang: str = "it") -> tuple:
    default = ("Deduction after net", "Item deducted or added after tax and contributions.") if lang == "en" else \
        ("Trattenuta dopo il netto", "Voce tolta o aggiunta dopo tasse e contributi.")
    return _classifica(label, VOCI_NETTO, default, lang)


def testo_flag(*flags: str, lang: str = "it") -> str:
    tab = FLAG_EN if lang == "en" else FLAG
    return " ".join(dict.fromkeys(tab[f] for f in flags if f in tab))


def normalizza(d: Dict) -> Dict:
    """Completa i campi mancanti e aggiunge `warnings` se i totali non tornano."""
    n = lambda x: None if x is None else float(x)
    for k in CAMPI_NUM:
        d[k] = n(d.get(k))
    d["payments"] = [{"code": p.get("code", ""), "label": p.get("label", ""), "amount": n(p.get("amount")) or 0.0,
                      "tax": (p.get("tax") or "").upper(), "sv": (p.get("sv") or "").upper(),
                      "gb": (p.get("gb") or "").upper()} for p in d.get("payments") or []]
    d["netItems"] = [{"code": p.get("code", ""), "label": p.get("label", ""), "amount": n(p.get("amount")) or 0.0}
                     for p in d.get("netItems") or []]
    for k in ("wageTax", "church", "soli", "kv", "rv", "av", "pv"):
        if d[k] is None:
            d[k] = 0.0
    if d["totalGross"] is None:
        d["totalGross"] = sum(p["amount"] for p in d["payments"] if p["gb"] != "N")
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
        pay.append({"label": "Gehalt", "amount": v["salary"], "tax": "L", "sv": "L"})
    if v.get("other"):
        pay.append({"label": "Sonstige Bezüge", "amount": v["other"], "tax": "S", "sv": "S"})
    if v.get("free"):
        pay.append({"label": "Steuerfreie Bezüge", "amount": v["free"], "tax": "F", "sv": "F"})
    d = {k: v.get(k) for k in ("month", "year", "employer", "taxClass", "kvRateTotal", "childlessFlag",
                                "wageTax", "soli", "church", "kv", "rv", "av", "pv", "payout", "agSv")}
    d.update(source="manual", payments=pay, ytd={},
             taxGross=(v.get("salary") or 0) + (v.get("other") or 0),
             netItems=[{"label": "Abzug nach Netto", "amount": -abs(v["ded"])}] if v.get("ded") else [])
    return normalizza(d)


def aliquota_pv(d: Dict) -> Optional[float]:
    """Aliquota PV effettiva (%) se nota la base contributiva."""
    return d["pv"] / d["pvGross"] * 100 if d.get("pvGross") else None


def tipo_pv(rate: Optional[float], childless_flag: bool = False, lang: str = "it") -> str:
    en = lang == "en"
    if rate is None:
        if not childless_flag:
            return ""
        return "childless (0.6% surcharge, marked Z)" if en else "senza figli (supplemento 0,6%, indicato con Z)"
    if abs(rate - 2.4) < 0.03:
        return "childless (1.8% + 0.6% surcharge, marked Z)" if en else "senza figli (1,8% + 0,6% di supplemento, indicato con Z)"
    if abs(rate - 1.8) < 0.03:
        return "with children (1.8%)" if en else "con figli (1,8%)"
    if abs(rate - 2.3) < 0.03 or abs(rate - 2.9) < 0.03:
        return "Saxony rate" if en else "aliquota della Sassonia"
    if rate < 1.8:
        return "reduced for several children under 25" if en else "ridotta per più figli sotto i 25 anni"
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


def note_tetto(d: Dict, lang: str = "it") -> List[str]:
    """Avvisa quando la base KV/RV è sotto l'imponibile fiscale: sono scattati i tetti contributivi."""
    note = []
    for k, nome_it, nome_en in (("kvGross", "sanitaria (KV/PV)", "health (KV/PV)"), ("rvGross", "pensione (RV/AV)", "pension (RV/AV)")):
        if d.get(k) and d.get("taxGross") and d[k] < d["taxGross"] - 1:
            if lang == "en":
                note.append(f"The base for {nome_en} is €{d[k]:,.2f} and not your whole salary: it is the monthly contribution "
                            "ceiling (Beitragsbemessungsgrenze). Nothing is paid above it.")
            else:
                note.append(f"La base per {nome_it} è {d[k]:,.2f} € e non l'intero stipendio: è il tetto mensile "
                            "di contribuzione (Beitragsbemessungsgrenze). Sopra questa cifra non si paga.")
    return note


def tetti(anno: int) -> Dict:
    return DE_RATES.get(anno, DE_RATES[max(DE_RATES)])


def dati_bav(d: Dict) -> Optional[Dict]:
    """Versamenti nella pensione aziendale: dal dict `bav` (calcolo) o dalle righe del cedolino (flag GB = N)."""
    if d.get("bav"):
        return d["bav"]
    conv = -sum(p["amount"] for p in d["payments"] if p["amount"] < 0 and re.search(r"gehaltsverzicht|salary cut|geh\.?\s*vz|entgeltumw", p["label"].lower()))
    dat = sum(p["amount"] for p in d["payments"] if p["amount"] > 0 and re.search(r"ag-?pflichtz|arbeitgeberzuschuss|pens\.?sch\.?empl|empl\.?\s*sub", p["label"].lower()))
    if conv <= 0 and dat <= 0:
        return None
    return {"conversion": conv, "employer": dat, "total": conv + dat}
