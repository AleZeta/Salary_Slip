"""Spiegazione HTML di un cedolino italiano letto da PDF (stessa grafica degli altri report)."""

import re
from typing import Dict, List, Optional

from src.de_render import CSS, _classe_tema, _e, _item, eur, pct
from src.i18n import mesi

# codici di voci informative (non sono soldi in busta): vanno nel dettaglio di altre voci
INFO = {"Z076", "Z082", "Z302", "Z383", "Z993", "Z994", "Z150"}


def _ore(q: Optional[float]) -> float:
    return (q or 0.0) / 100


def _periodo(p: str, lang: str = "it") -> str:
    """'0426' -> 'aprile 2026' (o 'April 2026')."""
    m = re.fullmatch(r"(\d{2})(\d{2})", p or "")
    if not m or not 1 <= int(m.group(1)) <= 12:
        return ""
    return f"{mesi(lang)[int(m.group(1)) - 1]} 20{m.group(2)}"


def _ore_txt(q: float, lang: str = "it") -> str:
    if lang == "en":
        return f"{q:.2f}".rstrip("0").rstrip(".") + " hours"
    return f"{q:.2f}".replace(".", ",").rstrip("0").rstrip(",") + " ore"


def _competenza(v: Dict, d: Dict, lang: str = "it") -> tuple:
    """(titolo, corpo HTML) di una voce a competenza."""
    tr = lambda it, en: en if lang == "en" else it
    eur_ = lambda x: eur(x, lang)
    desc, per = v["desc"].upper(), _periodo(v["period"], lang)
    ore = _ore(v["qty"])
    ore_t = _ore_txt(ore, lang)
    unit = tr(f" a {eur_(v['unit'])} l'ora", f" at {eur_(v['unit'])} per hour") if v.get("unit") else ""
    comp_per = (tr(f", competenza {_e(per)}", f", for the period {_e(per)}") if per else "")
    if desc.startswith("RETRIBUZIONE ORDINARIA"):
        parti = "".join(f"<p><span class=\"calc\">{_e(f['label'].title())}: {_e(eur_(f['amount']))}</span></p>" for f in d.get("fixed", []))
        paga = tr(f" Paga oraria {_e(eur_(d['hourly']))}.", f" Hourly rate {_e(eur_(d['hourly']))}.") if d.get("hourly") else ""
        scatti = ""
        if d.get("scatti"):
            nxt = d.get("nextScatto")
            scatti = (tr(f" Scatti di anzianità: {d['scatti']}", f" Seniority increments (<i>scatti di anzianità</i>): {d['scatti']}")
                      + (tr(f" (prossimo a {_e(nxt)})", f" (next one at {_e(nxt)})") if nxt else "") + ".")
        return tr("Stipendio base", "Base salary"), (
            tr("<p>La tua retribuzione mensile fissa, composta da:</p>", "<p>Your fixed monthly pay, made up of:</p>") + parti
            + tr(f"<p>Totale retribuzione mensile {_e(eur_(d.get('monthlyPay') or v['comp']))}.", f"<p>Total monthly pay {_e(eur_(d.get('monthlyPay') or v['comp']))}.")
            + paga + scatti + "</p>")
    if desc.startswith("MAGGIORE PRESTAZIONE A Q.O"):
        return tr("Straordinari (quota oraria)", "Overtime (base hourly portion)"), (
            tr(f"<p>{_e(ore_t)} di lavoro extra pagate alla quota oraria base{_e(unit)}", f"<p>{_e(ore_t)} of extra work paid at the base hourly rate{_e(unit)}")
            + comp_per + ".</p>")
    if desc.startswith("MAGGIORE PRESTAZIONE"):
        return tr("Maggiorazione straordinari", "Overtime premium"), (
            tr(f"<p>Maggiorazione del 25% su {_e(ore_t)} di straordinario", f"<p>25% premium on {_e(ore_t)} of overtime")
            + comp_per + ".</p>")
    if "TREDICESIMA" in desc:
        return (tr("Tredicesima mensilità", "13th month salary"),
                tr("<p>Mensilità aggiuntiva (rateo maturato): è tassata come il resto della retribuzione.</p>",
                   "<p>Additional monthly salary (<i>tredicesima</i>, accrued portion): it is taxed like the rest of your pay.</p>"))
    if "QUATTORDICESIMA" in desc:
        return (tr("Quattordicesima mensilità", "14th month salary"),
                tr("<p>Mensilità aggiuntiva (rateo maturato).</p>", "<p>Additional monthly salary (<i>quattordicesima</i>, accrued portion).</p>"))
    if "FERIE NON FRUITE" in desc:
        return (tr("Ferie non godute", "Unused holidays paid out"),
                tr(f"<p>{_e(ore_t)} di ferie non usate, liquidate{_e(unit)}. Succede tipicamente a fine rapporto.</p>",
                   f"<p>{_e(ore_t)} of unused holidays (<i>ferie</i>) paid out{_e(unit)}. This typically happens when employment ends.</p>"))
    if "PAR NON FRUITE" in desc:
        return (tr("Permessi (PAR) non goduti", "Unused paid leave (PAR) paid out"),
                tr(f"<p>{_e(ore_t)} di permessi annui retribuiti non usati, liquidati{_e(unit)}.</p>",
                   f"<p>{_e(ore_t)} of unused annual paid leave (<i>PAR</i>, <i>permessi annui retribuiti</i>) paid out{_e(unit)}.</p>"))
    if "CONTO ORE" in desc:
        return (tr("Banca ore liquidata", "Hours bank paid out"),
                tr(f"<p>{_e(ore_t)} della tua banca ore (<i>conto ore</i>) pagate{_e(unit)}.</p>",
                   f"<p>{_e(ore_t)} from your hours bank (<i>conto ore</i>) paid out{_e(unit)}.</p>"))
    if "DOA" in desc:
        return (tr("Ore non godute pagate", "Unused hours paid out"),
                tr(f"<p>{_e(ore_t)} di un monte ore non usato, pagate{_e(unit)}. "
                   "Il significato esatto del codice «DOA» dipende dall'azienda: l'ufficio paghe può confermarlo.</p>",
                   f"<p>{_e(ore_t)} from an unused hours allowance, paid out{_e(unit)}. "
                   "The exact meaning of the code “DOA” depends on the employer: the payroll office can confirm it.</p>"))
    if "PREMIO RISULTATO" in desc:
        detass = "NO D" not in desc
        return tr("Premio di risultato", "Performance bonus"), (
            tr("<p>Premio legato ai risultati aziendali.", "<p>Bonus linked to company results (<i>premio di risultato</i>).") + (
                tr(" Su questa parte si applica un'imposta sostitutiva agevolata invece dell'IRPEF ordinaria.</p>",
                   " A reduced flat-rate substitute tax applies to this part instead of ordinary income tax (IRPEF).</p>") if detass else
                tr(" Questa parte (<i>no detassazione</i>) è tassata con le aliquote ordinarie.</p>",
                   " This part (<i>no detassazione</i>, not eligible for the reduced rate) is taxed at ordinary rates.</p>")))
    if "T.F.R." in desc or desc.startswith("TFR"):
        return tr("TFR liquidato", "Severance pay paid out (TFR)"), (
            tr("<p><i>Trattamento di fine rapporto</i> pagato in busta (la quota che era in tesoreria INPS). "
               "È tassato separatamente, con un'aliquota basata sulla media dei redditi.</p>",
               "<p><i>Trattamento di fine rapporto</i> (severance pay) paid in your payslip (the portion that was held at the <i>INPS</i> treasury fund). "
               "It is taxed separately, at a rate based on your average income.</p>"))
    if "CONG.CONTRIB" in desc:
        return (tr("Conguaglio contributi", "Contribution adjustment"),
                tr("<p>Rimborso o conguaglio di un contributo aggiuntivo calcolato in anni o mesi precedenti.</p>",
                   "<p>Refund or adjustment of an additional contribution calculated in previous years or months.</p>"))
    if v["code"] == "Z104":
        return tr("Credito IRPEF", "IRPEF credit"), (
            tr("<p>Questo mese l'imposta è a tuo credito: il conguaglio fiscale ti restituisce una somma "
               "(ad esempio per detrazioni o per imposta trattenuta in eccesso nei mesi precedenti).</p>",
               "<p>This month the tax is in your favour: the tax adjustment (<i>conguaglio</i>) gives you money back "
               "(for example for tax credits or tax withheld in excess in previous months).</p>"))
    if "WELFARE" in desc:
        return (tr("Welfare (beni in natura)", "Welfare (benefits in kind)"),
                tr("<p>Valore di un benefit aziendale. Compare come competenza e come trattenuta: l'effetto sul netto è nullo.</p>",
                   "<p>Value of a company benefit. It appears both as an earning and as a deduction, so the effect on net pay is zero.</p>"))
    return v["desc"].title(), tr("<p>Voce a competenza indicata sul cedolino.</p>", "<p>Earnings item shown on the payslip.</p>")


def _trattenuta(v: Dict, d: Dict, lang: str = "it") -> Optional[tuple]:
    """(titolo, corpo) di una trattenuta, None se è gestita altrove (IRPEF, INPS)."""
    tr = lambda it, en: en if lang == "en" else it
    eur_ = lambda x: eur(x, lang)
    pct_ = lambda x, dd=2: pct(x, dd, lang)
    desc, c = v["desc"].upper(), v["code"]
    if c in {"Z100", "Z104"}:
        return None
    if desc.startswith("TRATTENUTA MENSA"):
        n = _ore(v["qty"])
        return tr("Mensa", "Canteen"), tr(f"<p>La tua quota per {n:g} pasti in mensa, {_e(eur_(v['unit']))} l'uno. L'azienda copre il resto.</p>",
                                          f"<p>Your share for {n:g} canteen meals (<i>mensa</i>), {_e(eur_(v['unit']))} each. The employer covers the rest.</p>")
    if "COMETA" in desc or "F.P.I" in desc or "FONDO PENS" in desc:
        pc = d.get("progressive", {}).get("fondoPercentuale")
        base = d.get("monthlyPay")
        calc = f'<p><span class="calc">{_e(eur_(base))} × {_e(pct_(pc, 0 if pc == int(pc) else 2))} = {_e(eur_(v["tratt"]))}</span></p>' if pc and base else ""
        return tr("Fondo pensione", "Pension fund"), (
            tr("<p>Il tuo contributo volontario al fondo pensione complementare. È deducibile dal reddito, quindi riduce l'IRPEF.</p>",
               "<p>Your voluntary contribution to the supplementary pension fund (<i>fondo pensione</i>). It is deductible from income, so it reduces IRPEF.</p>") + calc)
    if "ADDIZ" in desc and "REGION" in desc:
        pc = tr(f" Aliquota {pct_(_ore(v['qty']))}.", f" Rate {pct_(_ore(v['qty']))}.") if v.get("qty") else ""
        pr_ = _periodo(v["period"], lang)
        per = tr(f" (competenza {_e(pr_)})", f" (for the period {_e(pr_)})") if pr_ else ""
        return tr("Addizionale regionale", "Regional surtax"), tr(f"<p>Sovrattassa della regione sull'IRPEF{per}, trattenuta a rate.{_e(pc)}</p>",
                                                                  f"<p>Regional surtax on IRPEF{per}, withheld in instalments.{_e(pc)}</p>")
    if "ADDIZ" in desc and "COMUN" in desc:
        return (tr("Addizionale comunale", "Municipal surtax"),
                tr("<p>Sovrattassa del comune di residenza sull'IRPEF.</p>", "<p>Surtax of your municipality of residence on IRPEF.</p>"))
    if "L.297" in desc:
        return (tr("Contributo TFR", "TFR contribution"),
                tr("<p>Contributo trattenuto in relazione al TFR liquidato (L. 297/82).</p>",
                   "<p>Contribution withheld in connection with the severance pay (<i>TFR</i>) paid out (Law 297/82).</p>"))
    if "ACC.IMP" in desc:
        return tr("Acconto imposta sul TFR", "Tax advance on TFR"), (
            tr(f"<p>Acconto d'imposta trattenuto sul TFR liquidato, calcolato su {_e(eur_(v['info']))}.</p>", f"<p>Tax advance withheld on the severance pay (<i>TFR</i>) paid out, calculated on {_e(eur_(v['info']))}.</p>")
            if v.get("info") else tr("<p>Acconto d'imposta sul TFR.</p>", "<p>Tax advance on the severance pay (<i>TFR</i>).</p>"))
    if "DETASS" in desc:
        pc = v["tratt"] / v["info"] * 100 if v.get("info") else None
        return tr("Imposta sostitutiva premio", "Flat tax on bonus"), (
            tr("<p>Imposta agevolata sul premio di risultato: ", "<p>Reduced flat-rate tax on the performance bonus (<i>imposta sostitutiva</i>): ")
            + (f'<span class="calc">{_e(eur_(v["info"]))} × {_e(pct_(pc, 0))} = {_e(eur_(v["tratt"]))}</span>' if pc else "") + "</p>")
    if "WELFARE" in desc:
        return (tr("Welfare (beni in natura)", "Welfare (benefits in kind)"),
                tr("<p>Contropartita del benefit mostrato nelle competenze.</p>", "<p>Offsetting entry for the benefit shown under earnings.</p>"))
    return v["desc"].title(), tr("<p>Trattenuta indicata sul cedolino.</p>", "<p>Deduction shown on the payslip.</p>")


def report_html(d: Dict, dark: Optional[bool] = None, lang: str = "it") -> str:
    tr = lambda it, en: en if lang == "en" else it
    eur_ = lambda v: eur(v, lang)
    pct_ = lambda v, dd=2: pct(v, dd, lang)
    righe: List[Dict] = d["lines"]
    per = f"{mesi(lang)[d['month'] - 1].capitalize()} {d['year']}" if d.get("month") else ""
    z = {v["code"]: v for v in righe}
    meta = "".join(f"<span>{_e(k)} <b>{_e(v)}</b></span>" for k, v in (
        (tr("Azienda", "Employer"), d.get("employer")),
        (tr("Qualifica", "Job title"), " ".join(x for x in (d.get("qualifica"), d.get("livello")) if x)),
        (tr("Pagato il", "Paid on"), d.get("payDate")), (tr("Assunto il", "Hired on"), d.get("hireDate")),
        (tr("Cessazione", "Termination"), d.get("endDate"))) if v)
    h = [f'<style>{CSS}</style><div class="ps{_classe_tema(dark)}">',
         f'<div class="rhead"><h2>{_e(per)}<span class="src">{tr("letto da PDF", "read from PDF")}</span></h2><div class="meta">{meta}</div></div>']
    if d["warnings"]:
        h.append(f'<div class="notice">{tr("Alcuni totali non tornano esattamente: controlla i valori con il cedolino.", "Some totals do not add up exactly: check the values against your payslip.")}</div>')

    # lordo: voci a competenza (Z104 a competenza è un credito d'imposta, va nell'IRPEF)
    z104_credito = bool(z.get("Z104") and z["Z104"].get("comp") and not z["Z104"].get("tratt"))
    comp = [v for v in righe if v["comp"] and (v["code"] != "Z104" or z104_credito)]
    h.append(f'<div class="top"><section class="panel gross"><div class="head"><div class="ttl">{tr("TOTALE COMPETENZE", "TOTAL EARNINGS")}</div>'
             f'<div class="sub">{tr("Retribuzione lorda", "Gross pay")}</div><div class="big">{_e(eur_(d["totalComp"]))}</div></div>'
             f'<div class="ofwhich">{tr("di cui", "of which")}</div>')
    for v in comp:
        t, b = _competenza(v, d, lang)
        h.append(_item(t, eur_(v["comp"]), b, de=f"{v['code']} {v['desc']}", lang=lang))
    if d.get("roundComp"):
        h.append(_item(tr("Arrotondamenti", "Rounding"), eur_(d["roundComp"]),
                       tr("<p>Differenza di arrotondamento tra le voci e il totale.</p>", "<p>Rounding difference between the items and the total.</p>"), short=True, lang=lang))
    h.append("</section>")

    # trattenute
    h.append(f'<section class="panel ded"><div class="head"><div class="ttl">{tr("TRATTENUTE", "DEDUCTIONS")}</div>'
             f'<div class="sub">{tr("Tasse, contributi e altro", "Taxes, contributions and other")}</div>'
             f'<div class="big">− {_e(eur_(d["totalTratt"]))}</div></div><div class="ofwhich">{tr("di cui", "of which")}</div>')
    z104, z100 = z.get("Z104"), z.get("Z100")
    if z104 and not z104_credito:
        irpef = (z104["tratt"] or 0) - (z104["comp"] or 0)
        det = [(z[c]["desc"], z[c]["info"]) for c in ("Z082", "Z076") if c in z and z[c].get("info")]
        corpo = (tr("<p>IRPEF trattenuta sul tuo imponibile fiscale", "<p>Income tax (<i>IRPEF</i>) withheld on your taxable income")
                 + (tr(f" di <b>{_e(eur_(z104['info']))}</b> (retribuzione meno contributi INPS e fondo pensione, che sono deducibili)",
                       f" of <b>{_e(eur_(z104['info']))}</b> (pay minus <i>INPS</i> contributions and pension fund, which are deductible)") if z104.get("info") else "") + ".</p>")
        if det:
            corpo += tr("<p>Detrazioni applicate: ", "<p>Tax credits applied: ") + ", ".join(f"{_e(n.title())} {_e(eur_(a))}" for n, a in det) + ".</p>"
        if z104.get("comp"):
            corpo += tr(f"<p>Questo mese c'è anche un credito di {_e(eur_(z104['comp']))} (conguaglio), già sottratto.</p>",
                        f"<p>This month there is also a credit of {_e(eur_(z104['comp']))} (<i>conguaglio</i>, year-end adjustment), already subtracted.</p>")
        if d.get("progressive", {}).get("impostaNetta"):
            corpo += tr(f"<p>Da inizio anno hai pagato {_e(eur_(d['progressive']['impostaNetta']))} di imposta netta.</p>",
                        f"<p>Year to date you have paid {_e(eur_(d['progressive']['impostaNetta']))} of net tax.</p>")
        h.append(_item(tr("Imposta sul reddito", "Income tax"), eur_(irpef), corpo, de="IRPEF netta" if lang == "it" else "Net IRPEF", lang=lang))
    if z100:
        rate = z100["tratt"] / z100["info"] * 100 if z100.get("info") else None
        corpo = tr("<p>La tua quota di contributi previdenziali (pensione e altre assicurazioni obbligatorie) versata all'INPS. "
                   "La sanità è pubblica (SSN) e finanziata dalle tasse, non c'è un'assicurazione sanitaria separata.</p>",
                   "<p>Your share of social security contributions (pension and other compulsory insurance) paid to <i>INPS</i>. "
                   "Healthcare is public (<i>SSN</i>) and funded by taxes, so there is no separate health insurance.</p>")
        if rate:
            corpo += f'<p><span class="calc">{_e(eur_(z100["info"]))} × {_e(pct_(rate))} = {_e(eur_(z100["tratt"]))}</span></p>'
            if rate > 9.6:
                corpo += tr("<p>L'aliquota è più alta del solito (9,19%–9,49%): può dipendere dal contributo aggiuntivo sulla parte di retribuzione sopra la soglia.</p>",
                            "<p>The rate is higher than usual (9.19%–9.49%): it may be due to the additional contribution on the part of pay above the threshold.</p>")
        h.append(_item(tr("Contributi previdenziali", "Social security"), eur_(z100["tratt"]), corpo, de="INPS (IMPONIBILE PREV.)", lang=lang))
    altre = [(v, _trattenuta(v, d, lang)) for v in righe if v["tratt"] and v["code"] not in INFO]
    altre = [(v, t) for v, t in altre if t]
    # accorpa le addizionali regionali (più righe)
    is_reg = lambda v: "ADDIZ" in v["desc"].upper() and "REGION" in v["desc"].upper()
    reg = [(v, t) for v, t in altre if is_reg(v)]
    resto = [(v, t) for v, t in altre if not is_reg(v)]
    if reg:
        tot = sum(v["tratt"] for v, _ in reg)
        corpo = "".join(t[1] for _, t in reg)
        h.append(_item(tr("Addizionale regionale", "Regional surtax"), eur_(tot), corpo, de=tr("Addizionale regionale IRPEF", "Regional IRPEF surtax"), lang=lang))
    for i in range(0, len(resto), 2):
        coppia = resto[i:i + 2]
        voci = "".join(_item(t[0], eur_(v["tratt"]), t[1], de=f"{v['code']} {v['desc']}", short=len(coppia) == 2, lang=lang) for v, t in coppia)
        h.append(f'<div class="pair">{voci}</div>' if len(coppia) == 2 else voci)
    if d.get("roundTratt"):
        h.append(_item(tr("Arrotondamenti", "Rounding"), eur_(d["roundTratt"]),
                       tr("<p>Differenza di arrotondamento tra le voci e il totale.</p>", "<p>Rounding difference between the items and the total.</p>"), short=True, lang=lang))
    h.append("</section></div>")

    # netto
    chips = [tr(f"Competenze {eur_(d['totalComp'])}", f"Earnings {eur_(d['totalComp'])}"),
             tr(f"− Trattenute {eur_(d['totalTratt'])}", f"− Deductions {eur_(d['totalTratt'])}")]
    ticket = z.get("NP02")
    note = ""
    if ticket and ticket.get("qty") and ticket.get("unit"):
        n = _ore(ticket["qty"])
        note = tr(f"<p>Più {n:g} ticket restaurant elettronici da {_e(eur_(ticket['unit']))} ciascuno, {_e(eur_(n * ticket['unit']))} in totale: "
                  "caricati su carta, non pagati in contanti.</p>",
                  f"<p>Plus {n:g} electronic meal vouchers (<i>ticket restaurant</i>) of {_e(eur_(ticket['unit']))} each, {_e(eur_(n * ticket['unit']))} in total: "
                  "loaded onto a card, not paid in cash.</p>")
    h.append(f'<section class="net"><div class="ttl">{tr("NETTO A PAGARE", "NET PAY")}</div>'
             f'<div class="sub">{tr("Accredito del", "Paid on")} {_e(d.get("payDate", ""))}</div>'
             f'<div class="big">{_e(eur_(d["netto"]))}</div><div class="flow">' + "".join(f"<span>{_e(c)}</span>" for c in chips) + f"</div>{note}</section>")

    # barra
    tasse = sum((v["tratt"] or 0) - (v["comp"] or 0) for v in righe if v["code"] == "Z104") + sum(
        v["tratt"] or 0 for v in righe if re.search(r"ADDIZ|DETASS|ACC\.IMP", v["desc"].upper()))
    inps = (z100 or {}).get("tratt") or 0
    resto_t = max(0.0, d["totalTratt"] - tasse - inps)
    if d["totalComp"] > 0:
        segs = [(d["netto"], "var(--net)", tr("Netto", "Net")), (tasse, "var(--ded)", tr("Tasse", "Taxes")), (inps, "var(--ded-line)", "INPS"),
                (resto_t, "var(--gross)", tr("Fondo pensione e altro", "Pension fund and other"))]
        segs = [s for s in segs if s[0] > 0.005]
        tot = sum(s[0] for s in segs)
        aria = ", ".join(f"{s[2]} {pct_(s[0] / tot * 100, 1)}" for s in segs)
        h.append(f'<section class="section"><h3>{tr("Come si divide il lordo", "How your gross pay is split")}</h3>'
                 + tr(f'<p class="lead">Su ogni 100 € di competenze, circa {round(d["netto"] / d["totalComp"] * 100)} € arrivano sul tuo conto.</p>',
                      f'<p class="lead">Out of every €100 of earnings, about €{round(d["netto"] / d["totalComp"] * 100)} reach your bank account.</p>')
                 + f'<div class="stack" role="img" aria-label="{_e(aria)}">'
                 + "".join(f'<div style="width:{s[0] / tot * 100:.2f}%;background:{s[1]}"></div>' for s in segs) + "</div>"
                 '<div class="legend">' + "".join(f'<span><i style="background:{s[1]}"></i>{_e(s[2])} {_e(pct_(s[0] / tot * 100, 1))}</span>' for s in segs) + "</div></section>")

    # card
    pr, res, info = d.get("progressive", {}), d.get("residui", {}), []
    giorni = tr("gg", "d")
    for chiave, titolo, de in (("FERIE", tr("Ferie residue", "Holidays left"), tr("Ferie", "Holidays (ferie)")),
                               ("PAR", tr("Permessi residui", "Leave left"), "PAR"),
                               ("CONTO ORE", tr("Banca ore", "Hours bank"), tr("Conto ore", "Hours bank (conto ore)"))):
        r = res.get(chiave)
        if r and r.get("residuo") is not None:
            etichette = ((tr("Anno precedente", "Previous year"), "prev"), (tr("Spettanti", "Entitled"), "spettanti"), (tr("Godute", "Taken"), "godute"))
            info.append(_item(titolo, f"{r['residuo']:g} h · {r['residuo'] / 8:.0f} {giorni}", (
                "<p>" + " · ".join(f"{k} {r[c]:g} h" for k, c in etichette if r.get(c) is not None) +
                tr(". I cedolini italiani contano le ore: 8 ore = 1 giorno.</p>", ". Italian payslips count hours: 8 hours = 1 day.</p>")), de=de, short=True, lang=lang))
    if pr.get("tfrFondoMese"):
        info.append(_item(tr("TFR a fondo", "TFR to pension fund"), eur_(pr["tfrFondoMese"]) + tr(" / mese", " / month"),
                          tr("<p><i>Trattamento di fine rapporto</i>: circa una mensilità l'anno messa da parte per te, "
                             f"qui versata al fondo pensione. Da inizio anno {_e(eur_(pr.get('tfrFondoAnno')))}.</p>",
                             "<p><i>Trattamento di fine rapporto</i> (severance pay): about one month of salary per year set aside for you, "
                             f"here paid into the pension fund. Year to date {_e(eur_(pr.get('tfrFondoAnno')))}.</p>"),
                          de="TFR", cls="b", short=True, lang=lang))
    if pr.get("fondoAziendaMese"):
        info.append(_item(tr("Contributo azienda al fondo", "Employer contribution to the fund"), eur_(pr["fondoAziendaMese"]) + tr(" / mese", " / month"),
                          tr("<p>Poiché versi al fondo pensione, l'azienda aggiunge il suo contributo, che non appare nel netto.</p>",
                             "<p>Because you pay into the pension fund, the employer adds its own contribution, which does not appear in your net pay.</p>"),
                          de=tr("Contributo c/azienda", "Employer contribution (contributo c/azienda)"), cls="b", short=True, lang=lang))
    for c, titolo in (("Z302", tr("Polizza sanitaria", "Health insurance policy")), ("Z383", tr("Fondo sanitario azienda", "Company health fund"))):
        if c in z and z[c].get("info"):
            info.append(_item(titolo, eur_(z[c]["info"]),
                              tr("<p>Pagata dall'azienda, mostrata solo a titolo informativo: non è una trattenuta.</p>",
                                 "<p>Paid by the employer and shown for information only: it is not a deduction.</p>"),
                              de=z[c]["desc"].title(), cls="b", short=True, lang=lang))
    if info:
        h.append('<div class="info">' + "".join(info) + "</div>")

    # progressivi
    tab = [(tr("Imponibile previdenziale", "Social security taxable base"), pr.get("prevImponibile"), z100 and z100.get("info")),
           (tr("Contributi INPS", "INPS contributions"), pr.get("prevContributi"), z100 and z100.get("tratt")),
           (tr("Imponibile fiscale", "Taxable income"), pr.get("fiscImponibile"), z104 and z104.get("info")),
           (tr("Imposta netta", "Net tax"), pr.get("impostaNetta"), z104 and (z104.get("tratt") or 0) - (z104.get("comp") or 0)),
           (tr("TFR a fondo", "TFR to pension fund"), pr.get("tfrFondoAnno"), pr.get("tfrFondoMese")),
           (tr("Contributi tuoi al fondo", "Your contributions to the fund"), pr.get("fondoDipendente"), None),
           (tr("Contributi azienda al fondo", "Employer contributions to the fund"), pr.get("fondoAzienda"), None)]
    tab = [t for t in tab if t[1] is not None]
    if tab:
        h.append(f'<section class="section"><h3>{tr("Da inizio anno", "Year to date")}</h3>'
                 f'<p class="lead">{tr("Totali progressivi riportati in fondo al cedolino.", "Running totals shown at the bottom of the payslip.")}</p>'
                 f'<div class="tablewrap"><table><thead><tr><th>{tr("Voce", "Item")}</th><th class="num">{tr("Questo mese", "This month")}</th>'
                 f'<th class="num">{tr("Da inizio anno", "Year to date")}</th></tr></thead><tbody>'
                 + "".join(f'<tr><td>{_e(a)}</td><td class="num">{_e(eur_(m) if m is not None else "–")}</td><td class="num">{_e(eur_(y))}</td></tr>' for a, y, m in tab)
                 + "</tbody></table></div></section>")
    h.append('<p class="foot">' + tr(
        "Spiegazione basata sulle cifre del cedolino. I significati di alcuni codici dipendono dall'azienda. "
        "Non è consulenza fiscale: per casi specifici chiedi all'ufficio paghe o a un CAF / commercialista.",
        "Explanation based on the figures on the payslip. The meaning of some codes depends on the employer. "
        "This is not tax advice: for specific cases ask your payroll office or a tax advisor (<i>CAF</i> / <i>commercialista</i>).") + "</p></div>")
    return "".join(h)
