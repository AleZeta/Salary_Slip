"""Parser per cedolini tedeschi DATEV (porting di legacy_html/datev_parser.js).

Input: lista di pagine, ognuna lista di item {"str", "x", "y", "w"} (y dal basso, come in pdf.js).
`items_da_pdf` produce questa struttura da un PDF con pdfplumber.
"""

import re
from typing import Dict, List, Optional

DE_PAGE = re.compile(r"AbrechnungderBrutto/Netto-Bez")
EN_PAGE = re.compile(r"PayAdvice")

MESI = {
    "januar": 1, "februar": 2, "märz": 3, "maerz": 3, "april": 4, "mai": 5, "juni": 6, "juli": 7,
    "august": 8, "september": 9, "oktober": 10, "november": 11, "dezember": 12,
    "january": 1, "february": 2, "march": 3, "may": 5, "june": 6, "july": 7, "october": 10, "december": 12,
}

LABELS = {
    "de": dict(
        taxGross="Steuer-Brutto", wageTax="Lohnsteuer", church="Kirchensteuer", soli="Solidaritätszuschlag",
        kvB="KV-Brutto", rvB="RV-Brutto", avB="AV-Brutto", pvB="PV-Brutto",
        kv="KV-Beitrag", rv="RV-Beitrag", av="AV-Beitrag", pv="PV-Beitrag",
        totalGross="Gesamt-Brutto", taxTot="Steuerrechtliche Abzüge", svTot="SV-rechtliche Abzüge",
        netInc="Netto-Verdienst", payout="Auszahlungsbetrag",
        agSv="SV-AG-Anteil", agAdd="Zus. AG-Kosten", agTot="Gesamtkosten",
        payHead="Lohnart", netHead="Netto-Bezüge/Netto-Abzüge",
        ytd={"Gesamt-Brutto": "gross", "Steuer-Brutto": "taxGross", "Lohnsteuer": "wageTax",
             "Kirchensteuer": "church", "Solidaritätszuschlag": "soli", "Steuerfreie Bezüge": "taxFree",
             "SV-Brutto": "svGross", "KV-Beitrag": "kv", "RV-Beitrag": "rv", "AV-Beitrag": "av", "PV-Beitrag": "pv"},
    ),
    "en": dict(
        taxGross="Taxable gross income", wageTax="Wage tax", church="Church tax", soli="Solidarity surcharge",
        kvB="Contr.income(HI)", rvB="Contr.income(PI)", avB="Contr.income(UI)", pvB="Contr.income(CI)",
        kv="HI Contribution", rv="PI Contribution", av="UI Contribution", pv="CI Contribution",
        totalGross="Total gross income", taxTot="Tax deductions", svTot="Soc. sec. deductions",
        netInc="Net income", payout="Net pay",
        agSv="Emp.soc.sec.contr.", agAdd="Empl. cost, add.", agTot="Total cost",
        payHead="Wag. code", netHead="Non-taxable/non-contributory payments and deductions",
        ytd={"Total gross income": "gross", "Tax. gross income": "taxGross", "Wage tax": "wageTax",
             "Church tax": "church", "Solidarity surcharge": "soli", "Non-tax. payments": "taxFree",
             "Contr. inc. (Soc.sec.)": "svGross", "HI Contribution": "kv", "PI Contribution": "rv",
             "UI Contribution": "av", "CI Contribution": "pv"},
    ),
}

def _senza_spazi(s: str) -> str:
    """Il titolo è stampato con spazi tra le lettere: il confronto ignora gli spazi."""
    return re.sub(r"\s+", "", s)


def _eq(s: str, label: str) -> bool:
    return _senza_spazi(s) == _senza_spazi(label)


_NUM_TOKEN = re.compile(r"^-?[\d.]+(,\d+)?-?(\s*[A-Z])?$")


def num(s) -> Optional[float]:
    """Numero in formato DATEV. Senza virgola decimale il valore è in centesimi (es. 50249 = 502,49)."""
    if s is None:
        return None
    s = str(s).strip()
    neg = s.endswith("-") or s.startswith("-")
    s = re.sub(r"[^0-9.,]", "", s)
    if not s:
        return None
    try:
        if "," in s:
            v = float(s.replace(".", "").replace(",", "."))
        else:
            v = int(s.replace(".", "")) / 100
    except ValueError:
        return None
    return -v if neg else v


def _is_num(s: str) -> bool:
    return bool(_NUM_TOKEN.match(s.strip()))


def _find(items, label, min_y=None, max_y=None, min_x=None):
    for i in items:
        if not _eq(i["str"], label):
            continue
        if min_y is not None and not i["y"] > min_y:
            continue
        if max_y is not None and not i["y"] < max_y:
            continue
        if min_x is not None and not i["x"] > min_x:
            continue
        return i
    return None


def _under_header(items, label, header_y):
    """Valore numerico sotto l'intestazione `label`, assegnato alla colonna più vicina nella riga di intestazione."""
    lab = next((i for i in items if _eq(i["str"], label) and abs(i["y"] - header_y) < 2), None)
    if not lab:
        return None
    row = [i for i in items if abs(i["y"] - header_y) < 2 and len(i["str"].strip()) > 2]
    cands = [i for i in items if header_y - 22 < i["y"] < header_y - 6 and _is_num(i["str"])]
    centro = lambda i: i["x"] + i["w"] / 2
    best = None
    for v in cands:
        nearest = min(row, key=lambda r: abs(centro(r) - centro(v)))
        if nearest is lab and (best is None or abs(centro(v) - centro(lab)) < abs(centro(best) - centro(lab))):
            best = v
    return best


def _same_row_right(items, lab, x_min, x_max):
    c = [i for i in items if abs(i["y"] - lab["y"]) < 3 and x_min <= i["x"] <= x_max and _is_num(i["str"])]
    return min(c, key=lambda i: i["x"]) if c else None


def parse(pages: List[List[dict]]) -> Dict:
    """Restituisce un dict con `ok` True/False. Se False: `reason`."""
    lang = "de"
    page = next((p for p in pages if any(DE_PAGE.search(_senza_spazi(i["str"])) for i in p)), None)
    if page is None:
        page, lang = next((p for p in pages if any(EN_PAGE.search(_senza_spazi(i["str"])) for i in p)), None), "en"
    if page is None:
        return {"ok": False, "reason": "not_datev"}

    T, it = LABELS[lang], page
    out: Dict = {"ok": True, "lang": lang, "warnings": []}

    # intestazione
    per = next((i for i in it if re.match(r"^(für|for)\s+\S+\s+\d{4}$", i["str"].strip(), re.I)), None)
    if per:
        m = re.match(r"^(?:für|for)\s+(\S+)\s+(\d{4})$", per["str"].strip(), re.I)
        out["month"], out["year"] = MESI.get(m.group(1).lower()), int(m.group(2))
    d = next((i for i in it if re.match(r"^\d{2}[./]\d{2}[./]\d{4}$", i["str"].strip())), None)
    out["payDate"] = d["str"].strip().replace("/", ".") if d else None
    r = next((i for i in it if re.match(r"^\d{5}\s+\d{6}\s+\d", i["str"].strip())), None)
    if r:
        out["taxClass"] = int(r["str"].split()[2])
    r = next((i for i in it if re.match(r"^\d{7}\s+\d{4}\s+\d\s+\d{1,2}$", i["str"].strip())), None)
    if r:
        m = re.match(r"^(\d{2})(\d{2})(\d{3})\s+(\d{4})", r["str"].strip())
        out["kvRateTotal"] = float(f"{m.group(1)}.{m.group(2)}")
    r = next((i for i in it if re.match(r"^\d{8}[A-Z]\d{3}\s+", i["str"].strip())), None)
    if r:
        out["insurer"] = re.sub(r"^\S+\s+", "", r["str"].strip())
    r = next((i for i in it if re.match(r"^\d{6}$", i["str"].strip()) and 300 < i["x"] < 360 and i["y"] > 700), None)
    if r:
        s = r["str"].strip()
        out["startDate"] = f"{s[:2]}.{s[2:4]}.20{s[4:]}"
    r = next((i for i in it if "*" in i["str"] and re.search(r"(GmbH|AG|KG|SE|UG|e\.V\.)", i["str"])), None)
    if r:
        out["employer"] = r["str"].split("*")[0].strip()
    # nome e dati personali: volutamente NON estratti

    # imposte
    tg = _find(it, T["taxGross"], min_y=250, max_y=420)
    if tg:
        for k in ("taxGross", "wageTax", "church", "soli"):
            v = _under_header(it, T[k], tg["y"])
            out[k] = num(v["str"]) if v else 0.0

    # contributi sociali
    kvb = _find(it, T["kvB"], min_y=200, max_y=420)
    if kvb:
        y = kvb["y"]
        for k, lab in (("kvGross", "kvB"), ("rvGross", "rvB"), ("avGross", "avB"), ("pvGross", "pvB"),
                       ("kv", "kv"), ("rv", "rv"), ("av", "av"), ("pv", "pv")):
            v = _under_header(it, T[lab], y)
            out[k] = num(v["str"]) if v else 0.0
            if v and re.search(r"Z\s*$", v["str"]):
                out["childlessFlag"] = True
        if any(abs(i["y"] - (y - 14)) < 4 and re.match(r"^\s*Z\s*$", i["str"]) for i in it):
            out["childlessFlag"] = True

    # totali (colonna destra)
    def right_total(lab):
        l = next((i for i in it if _eq(i["str"], lab) and i["x"] > 470), None)
        if not l:
            return None
        c = sorted((i for i in it if i["x"] > 480 and l["y"] - 22 < i["y"] < l["y"] - 4 and _is_num(i["str"])),
                   key=lambda i: -i["y"])
        return num(c[0]["str"]) if c else None

    out["totalGross"], out["taxTotal"], out["svTotal"] = (right_total(T[k]) for k in ("totalGross", "taxTot", "svTot"))
    out["netIncome"], out["payout"] = right_total(T["netInc"]), right_total(T["payout"])

    # costi del datore
    for k, lab in (("agSv", "agSv"), ("agAdd", "agAdd"), ("agTotal", "agTot")):
        l = next((i for i in it if _eq(i["str"], T[lab])), None)
        v = _under_header(it, T[lab], l["y"]) if l else None
        out[k] = num(v["str"]) if v else None

    # voci lorde
    ph = next((i for i in it if _eq(i["str"], T["payHead"]) and i["y"] > 420), None)
    out["payments"] = []
    if ph:
        bottom = (tg["y"] if tg else 350) + 15
        rows = [i for i in it if i["x"] < 120 and bottom < i["y"] < ph["y"] - 4 and re.match(r"^\d{3,4}\s+\S", i["str"].strip())]
        for r in sorted(rows, key=lambda i: -i["y"]):
            amt = next((i for i in it if abs(i["y"] - r["y"]) < 3 and i["x"] > 480 and _is_num(i["str"])), None)
            flags = [i["str"].strip() for i in sorted(it, key=lambda i: i["x"])
                     if abs(i["y"] - r["y"]) < 3 and 420 < i["x"] < 480 and re.match(r"^[A-Z]$", i["str"].strip())]
            m = re.match(r"^(\d{3,4})\s+(.*)$", r["str"].strip())
            out["payments"].append({
                "code": m.group(1), "label": m.group(2), "amount": num(amt["str"]) if amt else None,
                "tax": flags[0] if flags else "", "sv": flags[1] if len(flags) > 1 else "",
                "gb": flags[2] if len(flags) > 2 else "",
            })

    # voci dopo il netto
    nh = next((i for i in it if _eq(i["str"], T["netHead"])), None)
    out["netItems"] = []
    if nh:
        rows = [i for i in it if 280 < i["x"] < 480 and 100 < i["y"] < nh["y"] - 4 and re.match(r"^\d{3,4}\s+\S", i["str"].strip())]
        for r in sorted(rows, key=lambda i: -i["y"]):
            amt = next((i for i in it if abs(i["y"] - r["y"]) < 3 and i["x"] > 480 and _is_num(i["str"])), None)
            m = re.match(r"^(\d{3,4})\s+(.*)$", r["str"].strip())
            out["netItems"].append({"code": m.group(1), "label": m.group(2), "amount": num(amt["str"]) if amt else None})

    # progressivi da inizio anno
    out["ytd"] = {}
    ytd_top = nh["y"] if nh else 260
    for lab, key in T["ytd"].items():
        l = next((i for i in it if _eq(i["str"], lab) and 110 < i["y"] < ytd_top + 2 and i["x"] < 260), None)
        if not l:
            continue
        x_min, x_max = (95, 175) if l["x"] < 100 else (220, 290)
        v = _same_row_right(it, l, x_min, x_max)
        out["ytd"][key] = num(v["str"]) if v else 0.0

    # controlli di coerenza
    if out["totalGross"] is None or out["payout"] is None:
        out["warnings"].append("missing_totals")
    somma = sum(p["amount"] or 0 for p in out["payments"])
    if out["totalGross"] is not None and abs(somma - out["totalGross"]) > 0.02:
        out["warnings"].append("gross_mismatch")
    netto = (out["totalGross"] or 0) - (out["taxTotal"] or 0) - (out["svTotal"] or 0)
    if out["netIncome"] is not None and abs(netto - out["netIncome"]) > 0.02:
        out["warnings"].append("net_mismatch")
    pay = (out["netIncome"] or 0) + sum(p["amount"] or 0 for p in out["netItems"])
    if out["payout"] is not None and abs(pay - out["payout"]) > 0.02:
        out["warnings"].append("payout_mismatch")
    return out


def _chunk_da_chars(chars) -> List[dict]:
    """Raggruppa i caratteri di una pagina in blocchi di testo come fa pdf.js: stessa riga di base, un solo font/corpo,
    nessun salto orizzontale. Gli spazi singoli restano nel blocco (es. "2000 Gehalt"), le sequenze di spazi o i
    salti di posizione separano le colonne."""
    righe: List[list] = []
    for c in sorted(chars, key=lambda c: (-c["matrix"][5], c["x0"])):
        y = c["matrix"][5]
        if righe and abs(righe[-1][0] - y) < 1.5:
            righe[-1][1].append(c)
        else:
            righe.append([y, [c]])
    items = []
    for y, cs in righe:
        cs.sort(key=lambda c: c["x0"])
        blocco: list = []

        def chiudi():
            while blocco and blocco[-1]["text"].isspace():
                blocco.pop()
            testo = "".join(c["text"] for c in blocco).strip()
            if testo:
                items.append({"str": testo, "x": float(blocco[0]["matrix"][4]), "y": float(y),
                              "w": float(blocco[-1]["x1"] - blocco[0]["x0"])})
            blocco.clear()

        for c in cs:
            if c["text"].isspace():
                if not blocco:
                    continue
                blocco.append(c)
                continue
            if blocco:
                prev = next(b for b in reversed(blocco) if not b["text"].isspace())
                gap = c["x0"] - prev["x1"]
                if gap > 0.7 * c["size"] or abs(c["size"] - prev["size"]) > 1.5:
                    chiudi()

            blocco.append(c)
        chiudi()
    return items


def items_da_pdf(file) -> List[List[dict]]:
    """Legge un PDF (path o file-like) in item di testo {str,x,y,w} con y della linea di base dal basso (come pdf.js)."""
    import pdfplumber

    with pdfplumber.open(file) as pdf:
        return [_chunk_da_chars(pg.chars) for pg in pdf.pages[:6]]
