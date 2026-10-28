"""Parser per cedolini italiani con layout a colonne fisse (COD. PAS. / DESCRIZIONE / COMPETENZE / TRATTENUTE).

Usa gli stessi item di testo {str,x,y,w} di de_parser (`items_da_pdf`). I dati personali (nome, codice fiscale,
IBAN, matricola) non vengono estratti. Un cedolino può occupare più pagine: le voci e i totali si uniscono.
"""

import re
from typing import Dict, List, Optional

MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre",
        "novembre", "dicembre"]
_COD = re.compile(r"^([A-Z]{1,2}\d{2,3}[A-Z]?)\s+(.*\S)\s*$")
_NUM = re.compile(r"^-?[\d.]*,?\d+-?$")


def senza_spazi(s: str) -> str:
    return re.sub(r"\s+", "", s).upper()


def _isnum(s: str) -> bool:
    """Numero anche con spazi spuri dentro ("1 0.143,05")."""
    return bool(_NUM.match(re.sub(r"\s+", "", s)))


def num(s, centesimi: bool = False) -> Optional[float]:
    """Numero italiano ("1.234,56", ",42"). Con `centesimi=True` un intero senza virgola vale centesimi ("93" = 0,93)."""
    if s is None:
        return None
    t = str(s).strip().replace("*", "")
    neg = t.endswith("-") or t.startswith("-")
    t = re.sub(r"[^0-9.,]", "", t)
    if not t or t in {",", "."}:
        return None
    try:
        if "," in t:
            v = float(t.replace(".", "").replace(",", "."))
        else:
            v = int(t.replace(".", "")) / (100 if centesimi else 1)
    except ValueError:
        return None
    return -v if neg else v


def _righe(items: List[dict], y_min: float, y_max: float) -> List[List[dict]]:
    """Raggruppa gli item con y in (y_min, y_max) per riga (tolleranza 2), ordinati per x."""
    righe: List[List[dict]] = []
    for i in sorted((i for i in items if y_min < i["y"] < y_max), key=lambda i: -i["y"]):
        if righe and abs(righe[-1][0]["y"] - i["y"]) < 2.5:
            righe[-1].append(i)
        else:
            righe.append([i])
    return [sorted(r, key=lambda i: i["x"]) for r in righe]


def _trova(items, testo):
    t = senza_spazi(testo)
    return next((i for i in items if senza_spazi(i["str"]) == t), None)


def _pagina_valida(p) -> bool:
    return any("COD.PAS." in senza_spazi(i["str"]) for i in p) and any("TOTALI" == senza_spazi(i["str"]) for i in p)


def _intestazione(pagina, out: Dict) -> None:
    for i in pagina:
        s = i["str"].strip()
        m = re.match(r"^(" + "|".join(MESI) + r")\s+(\d{4})$", s, re.I)
        if m and "month" not in out:
            out["month"], out["year"] = MESI.index(m.group(1).lower()) + 1, int(m.group(2))
        elif s.lower() in MESI and "month" not in out:  # mese e anno in blocchi separati sulla stessa riga
            anno = next((j for j in pagina if abs(j["y"] - i["y"]) < 2 and j["x"] > i["x"] and re.fullmatch(r"\d{4}", j["str"].strip())), None)
            if anno:
                out["month"], out["year"] = MESI.index(s.lower()) + 1, int(anno["str"])
        if "employer" not in out and i["y"] > 700 and i["x"] < 120 and re.search(r"\b(S\.?P\.?A\.?|S\.?R\.?L\.?|S\.?N\.?C\.?)$", s, re.I):
            out["employer"] = s
        if "qualifica" not in out and re.match(r"^(IMPIEGATO|OPERAIO|QUADRO|DIRIGENTE|APPRENDISTA)$", s, re.I):
            out["qualifica"] = s.capitalize()
            liv = next((j for j in pagina if abs(j["y"] - i["y"]) < 2 and i["x"] < j["x"] < i["x"] + 120
                        and re.match(r"^[A-Z0-9]{1,3}$", j["str"].strip())), None)
            if liv:
                out["livello"] = liv["str"].strip()
        m = re.match(r"^(\d{2})(\d{2})(\d{4})$", s)
        if m and 300 < i["x"] < 460 and 715 < i["y"] < 730:
            d = f"{m.group(1)}.{m.group(2)}.{m.group(3)}"
            if i["x"] < 380:
                out.setdefault("hireDate", d)
            else:
                out.setdefault("endDate", d)
        m = re.match(r"^(\d)\s+(\d{2})(\d{4})$", s)
        if m and 715 < i["y"] < 730:
            out["scatti"] = int(m.group(1))
            out["nextScatto"] = f"{m.group(2)}/{m.group(3)}"
    # elementi retributivi fissi: "MINIMO 2.481,84 SUPERM.COLLET. 141,88 ..."
    fissi = []
    for r in _righe(pagina, 640 - 30, 712):
        riga = " ".join(i["str"].strip() for i in r)
        if riga.startswith("PAGA") or "ELEMENTI" in senza_spazi(riga):
            continue
        for m in re.finditer(r"([A-Z][A-Z.0-9 ]*[A-Z.0-9])\s+(\d[\d.]*,\d{2})", riga):
            fissi.append({"label": m.group(1).strip(), "amount": num(m.group(2))})
    if fissi and "fixed" not in out:
        out["fixed"] = fissi
    for i in pagina:
        if i["y"] < 640 and i["y"] > 625 and re.match(r"^\d[\d.]*,\d{2,5}$", i["str"].strip()):
            pass
    paga = [i for i in pagina if 625 < i["y"] < 640 and re.match(r"^[\d.]+,\d+$", i["str"].strip())]
    paga.sort(key=lambda i: i["x"])
    if len(paga) >= 3 and "hourly" not in out:
        out["hourly"], out["monthlyPay"] = num(paga[0]["str"]), num(paga[-1]["str"])


def _voci(pagina) -> List[Dict]:
    cod = _trova(pagina, "COD. PAS.")
    arrot = next((i for i in pagina if "ARROTONDAMENTI" in senza_spazi(i["str"])), None)
    if not cod or not arrot:
        return []
    voci = []
    for r in _righe(pagina, arrot["y"] + 2, cod["y"] - 3):
        m = _COD.match(r[0]["str"].strip()) if r[0]["x"] < 80 else None
        if not m:
            continue
        v = {"code": m.group(1), "desc": m.group(2), "period": "", "qty": None, "unit": None, "info": None,
             "flag": "", "comp": None, "tratt": None}
        for i in r[1:]:
            s, x = i["str"].strip(), i["x"]
            if re.fullmatch(r"\*+", s):
                v["flag"] = s
            elif x >= 525:
                if re.fullmatch(r"\d{9,}", s):
                    continue
                v["tratt"] = num(s, centesimi=True)
            elif x >= 440:
                v["comp"] = num(s, centesimi=True)
            elif x >= 360:
                if re.fullmatch(r"\d{9,}", s):
                    continue
                v["unit"] = num(s)
                if s.endswith("**"):
                    v["flag"] = "**"
                elif s.endswith("*"):
                    v["flag"] = "*"
            elif x >= 318:
                if re.fullmatch(r"\d{9,}", s):
                    continue
                v["qty"] = num(s)
            elif x >= 275:
                v["period"] = s
            elif x >= 215:
                v["info"] = num(s)
        voci.append(v)
    return voci


def _totali(pagina, out: Dict) -> None:
    tot = _trova(pagina, "TOTALI")
    if tot:
        riga = [i for i in pagina if abs(i["y"] - tot["y"]) < 6 and i["x"] > 440 and _isnum(i["str"])]
        if len(riga) >= 2:
            riga.sort(key=lambda i: i["x"])
            out["totalComp"], out["totalTratt"] = num(riga[0]["str"]), num(riga[-1]["str"])
        arr = [i for i in pagina if abs(i["y"] - (tot["y"] + 14)) < 4 and i["x"] > 440 and _isnum(i["str"])]
        arr.sort(key=lambda i: i["x"])
        if len(arr) >= 2:
            out["roundComp"], out["roundTratt"] = num(arr[0]["str"]) or 0.0, num(arr[-1]["str"]) or 0.0
    euro = _trova(pagina, "EURO")
    if euro:
        n = [i for i in pagina if abs(i["y"] - (euro["y"] - 10)) < 5 and i["x"] > 440 and _isnum(i["str"])]
        d = [i for i in pagina if abs(i["y"] - (euro["y"] - 10)) < 5 and re.match(r"^\d{2}/\d{2}/\d{4}$", i["str"].strip())]
        if n:
            out["netto"] = num(n[0]["str"])
        if d:
            out["payDate"] = d[0]["str"].strip().replace("/", ".")


_ETICHETTE_PROG = {
    "IMPON.PREV": "prevImponibile", "CTRPREVID.": "prevContributi", "IMPON.FISC": "fiscImponibile", "IMPOS.NETTA": "impostaNetta",
    "IMPON.TFRMESE": "tfrBase", "TFRAFONDOPR.": "tfrFondoAnno", "TFRAFONDOMM": "tfrFondoMese", "CTR.C/DIPEND.": "fondoDipendente",
    "CTR.C/AZIENDA": "fondoAzienda", "CTR.C/T.F.R.": "fondoTfr", "CT.C/AZIENDAMM": "fondoAziendaMese", "CT.C/AZIENDAPR": "fondoAziendaAnno",
    "TFRTESORER.PR": "tfrTesoreria", "F.SAN.NONAS": "fondoSanitarioNonAs", "F.I.P.NONAS": "fipNonAs", "BENIINNAT.": "beniInNatura",
    "IM.TS.MNNET": "imponibileTassSeparata",
}


def _progressivi(pagina, out: Dict) -> None:
    alto = next((i for i in pagina if "IMPONIBILIPROGRESSIVI" in senza_spazi(i["str"])), None)
    basso = _trova(pagina, "ISTITUTO")
    if not alto or not basso:
        return
    prog = out.setdefault("progressive", {})
    for r in _righe(pagina, basso["y"] + 3, alto["y"] - 3):
        for g0, g1 in ((0, 225), (225, 405), (405, 700)):
            gr = [i for i in r if g0 <= i["x"] < g1]
            etichetta = next((i for i in gr if not _isnum(i["str"])), None)
            valori = [i for i in gr if _isnum(i["str"])]
            if etichetta and valori:
                k = _ETICHETTE_PROG.get(senza_spazi(etichetta["str"]))
                if k:
                    prog[k] = num(valori[-1]["str"])
            elif etichetta:
                m = re.match(r"^OPZ\.DIP\.\s*([\d,]+)%$", etichetta["str"].strip())
                if m:
                    prog["fondoPercentuale"] = num(m.group(1))
            elif valori and gr:  # valore sulla riga sotto l'etichetta
                pass


def _residui(pagina, out: Dict) -> None:
    testa = _trova(pagina, "ISTITUTO")
    if not testa:
        return
    cols = {k: i for k in ("RESIDUE A.P.", "SPETTANTI ANNO", "GODUTE ANNO", "RESIDUO", "RES. ANNO-2", "RESIDUO 1999")
            if (i := _trova([j for j in pagina if abs(j["y"] - testa["y"]) < 3], k))}
    centri = {k: i["x"] + i["w"] / 2 for k, i in cols.items()}
    nomi = {"RESIDUE A.P.": "prev", "SPETTANTI ANNO": "spettanti", "GODUTE ANNO": "godute", "RESIDUO": "residuo"}
    for r in _righe(pagina, 20, testa["y"] - 3):
        if not r or r[0]["x"] > 120 or _isnum(r[0]["str"]):
            continue
        riga = {}
        for i in r[1:]:
            if not _isnum(i["str"]) or not centri:
                continue
            c = i["x"] + i["w"] / 2
            k = min(centri, key=lambda k: abs(centri[k] - c))
            if k in nomi:
                riga[nomi[k]] = num(i["str"])
        if riga:
            out.setdefault("residui", {})[r[0]["str"].strip().upper()] = riga


def parse(pagine: List[List[dict]]) -> Dict:
    """Restituisce {"ok": bool, ...}. Un cedolino è riconosciuto se ha COD. PAS. e TOTALI."""
    valide = [p for p in pagine if _pagina_valida(p)]
    if not valide:
        return {"ok": False, "reason": "not_it_payslip"}
    out: Dict = {"ok": True, "warnings": [], "lines": []}
    for p in valide:
        _intestazione(p, out)
        out["lines"] += _voci(p)
        _totali(p, out)
        _progressivi(p, out)
        _residui(p, out)
    # controlli di coerenza
    comp = sum(v["comp"] or 0 for v in out["lines"]) + out.get("roundComp", 0.0)
    tratt = sum(v["tratt"] or 0 for v in out["lines"]) + out.get("roundTratt", 0.0)
    if out.get("totalComp") is None or out.get("netto") is None:
        out["warnings"].append("missing_totals")
    else:
        if abs(comp - out["totalComp"]) > 0.02:
            out["warnings"].append("comp_mismatch")
        if abs(tratt - (out.get("totalTratt") or 0)) > 0.02:
            out["warnings"].append("tratt_mismatch")
        if abs(out["totalComp"] - (out.get("totalTratt") or 0) - out["netto"]) > 0.02:
            out["warnings"].append("netto_mismatch")
    return out
