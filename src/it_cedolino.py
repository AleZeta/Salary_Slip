"""Spiegazione HTML di un cedolino italiano letto da PDF (stessa grafica degli altri report)."""

import re
from typing import Dict, List, Optional

from src.de_render import CSS, MESI, _classe_tema, _e, _item, eur, pct

# codici di voci informative (non sono soldi in busta): vanno nel dettaglio di altre voci
INFO = {"Z076", "Z082", "Z302", "Z383", "Z993", "Z994", "Z150"}


def _ore(q: Optional[float]) -> float:
    return (q or 0.0) / 100


def _periodo(p: str) -> str:
    """'0426' -> 'aprile 2026'."""
    m = re.fullmatch(r"(\d{2})(\d{2})", p or "")
    if not m or not 1 <= int(m.group(1)) <= 12:
        return ""
    return f"{MESI[int(m.group(1)) - 1]} 20{m.group(2)}"


def _ore_txt(q: float) -> str:
    return f"{q:.2f}".replace(".", ",").rstrip("0").rstrip(",") + " ore"


def _competenza(v: Dict, d: Dict) -> tuple:
    """(titolo, corpo HTML) di una voce a competenza."""
    desc, per = v["desc"].upper(), _periodo(v["period"])
    ore = _ore(v["qty"])
    unit = f" a {eur(v['unit'])} l'ora" if v.get("unit") else ""
    if desc.startswith("RETRIBUZIONE ORDINARIA"):
        parti = "".join(f"<p><span class=\"calc\">{_e(f['label'].title())}: {_e(eur(f['amount']))}</span></p>" for f in d.get("fixed", []))
        paga = f" Paga oraria {_e(eur(d['hourly']))}." if d.get("hourly") else ""
        return "Stipendio base", (f"<p>La tua retribuzione mensile fissa, composta da:</p>{parti}"
                                  f"<p>Totale retribuzione mensile {_e(eur(d.get('monthlyPay') or v['comp']))}.{paga}"
                                  + (f" Scatti di anzianità: {d['scatti']}" + (f" (prossimo a {_e(d['nextScatto'])})" if d.get("nextScatto") else "") + "." if d.get("scatti") else "") + "</p>")
    if desc.startswith("MAGGIORE PRESTAZIONE A Q.O"):
        return "Straordinari (quota oraria)", (f"<p>{_e(_ore_txt(ore))} di lavoro extra pagate alla quota oraria base{_e(unit)}"
                                               + (f", competenza {_e(per)}" if per else "") + ".</p>")
    if desc.startswith("MAGGIORE PRESTAZIONE"):
        return "Maggiorazione straordinari", (f"<p>Maggiorazione del 25% su {_e(_ore_txt(ore))} di straordinario"
                                              + (f", competenza {_e(per)}" if per else "") + ".</p>")
    if "TREDICESIMA" in desc:
        return "Tredicesima mensilità", "<p>Mensilità aggiuntiva (rateo maturato): è tassata come il resto della retribuzione.</p>"
    if "QUATTORDICESIMA" in desc:
        return "Quattordicesima mensilità", "<p>Mensilità aggiuntiva (rateo maturato).</p>"
    if "FERIE NON FRUITE" in desc:
        return "Ferie non godute", f"<p>{_e(_ore_txt(ore))} di ferie non usate, liquidate{_e(unit)}. Succede tipicamente a fine rapporto.</p>"
    if "PAR NON FRUITE" in desc:
        return "Permessi (PAR) non goduti", f"<p>{_e(_ore_txt(ore))} di permessi annui retribuiti non usati, liquidati{_e(unit)}.</p>"
    if "CONTO ORE" in desc:
        return "Banca ore liquidata", f"<p>{_e(_ore_txt(ore))} della tua banca ore (<i>conto ore</i>) pagate{_e(unit)}.</p>"
    if "DOA" in desc:
        return "Ore non godute pagate", (f"<p>{_e(_ore_txt(ore))} di un monte ore non usato, pagate{_e(unit)}. "
                                         "Il significato esatto del codice «DOA» dipende dall'azienda: l'ufficio paghe può confermarlo.</p>")
    if "PREMIO RISULTATO" in desc:
        detass = "NO D" not in desc
        return "Premio di risultato", ("<p>Premio legato ai risultati aziendali." + (
            " Su questa parte si applica un'imposta sostitutiva agevolata invece dell'IRPEF ordinaria.</p>" if detass else
            " Questa parte (<i>no detassazione</i>) è tassata con le aliquote ordinarie.</p>"))
    if "T.F.R." in desc or desc.startswith("TFR"):
        return "TFR liquidato", ("<p><i>Trattamento di fine rapporto</i> pagato in busta (la quota che era in tesoreria INPS). "
                                 "È tassato separatamente, con un'aliquota basata sulla media dei redditi.</p>")
    if "CONG.CONTRIB" in desc:
        return "Conguaglio contributi", "<p>Rimborso o conguaglio di un contributo aggiuntivo calcolato in anni o mesi precedenti.</p>"
    if v["code"] == "Z104":
        return "Credito IRPEF", ("<p>Questo mese l'imposta è a tuo credito: il conguaglio fiscale ti restituisce una somma "
                                 "(ad esempio per detrazioni o per imposta trattenuta in eccesso nei mesi precedenti).</p>")
    if "WELFARE" in desc:
        return "Welfare (beni in natura)", "<p>Valore di un benefit aziendale. Compare come competenza e come trattenuta: l'effetto sul netto è nullo.</p>"
    return v["desc"].title(), "<p>Voce a competenza indicata sul cedolino.</p>"


def _trattenuta(v: Dict, d: Dict) -> Optional[tuple]:
    """(titolo, corpo) di una trattenuta, None se è gestita altrove (IRPEF, INPS)."""
    desc, c = v["desc"].upper(), v["code"]
    if c in {"Z100", "Z104"}:
        return None
    if desc.startswith("TRATTENUTA MENSA"):
        n = _ore(v["qty"])
        return "Mensa", f"<p>La tua quota per {n:g} pasti in mensa, {_e(eur(v['unit']))} l'uno. L'azienda copre il resto.</p>"
    if "COMETA" in desc or "F.P.I" in desc or "FONDO PENS" in desc:
        pc = d.get("progressive", {}).get("fondoPercentuale")
        base = d.get("monthlyPay")
        calc = f'<p><span class="calc">{_e(eur(base))} × {_e(pct(pc, 0 if pc == int(pc) else 2))} = {_e(eur(v["tratt"]))}</span></p>' if pc and base else ""
        return "Fondo pensione", ("<p>Il tuo contributo volontario al fondo pensione complementare. È deducibile dal reddito, quindi riduce l'IRPEF.</p>" + calc)
    if "ADDIZ" in desc and "REGION" in desc:
        pc = f" Aliquota {pct(_ore(v['qty']))}." if v.get("qty") else ""
        per = f" (competenza {_e(_periodo(v['period']))})" if _periodo(v["period"]) else ""
        return "Addizionale regionale", f"<p>Sovrattassa della regione sull'IRPEF{per}, trattenuta a rate.{_e(pc)}</p>"
    if "ADDIZ" in desc and "COMUN" in desc:
        return "Addizionale comunale", "<p>Sovrattassa del comune di residenza sull'IRPEF.</p>"
    if "L.297" in desc:
        return "Contributo TFR", "<p>Contributo trattenuto in relazione al TFR liquidato (L. 297/82).</p>"
    if "ACC.IMP" in desc:
        return "Acconto imposta sul TFR", f"<p>Acconto d'imposta trattenuto sul TFR liquidato, calcolato su {_e(eur(v['info']))}.</p>" if v.get("info") else "<p>Acconto d'imposta sul TFR.</p>"
    if "DETASS" in desc:
        pc = v["tratt"] / v["info"] * 100 if v.get("info") else None
        return "Imposta sostitutiva premio", (f"<p>Imposta agevolata sul premio di risultato: "
                                              + (f'<span class="calc">{_e(eur(v["info"]))} × {_e(pct(pc, 0))} = {_e(eur(v["tratt"]))}</span>' if pc else "") + "</p>")
    if "WELFARE" in desc:
        return "Welfare (beni in natura)", "<p>Contropartita del benefit mostrato nelle competenze.</p>"
    return v["desc"].title(), "<p>Trattenuta indicata sul cedolino.</p>"


def report_html(d: Dict, dark: Optional[bool] = None) -> str:
    righe: List[Dict] = d["lines"]
    per = f"{MESI[d['month'] - 1].capitalize()} {d['year']}" if d.get("month") else ""
    z = {v["code"]: v for v in righe}
    meta = "".join(f"<span>{_e(k)} <b>{_e(v)}</b></span>" for k, v in (
        ("Azienda", d.get("employer")), ("Qualifica", " ".join(x for x in (d.get("qualifica"), d.get("livello")) if x)),
        ("Pagato il", d.get("payDate")), ("Assunto il", d.get("hireDate")), ("Cessazione", d.get("endDate"))) if v)
    h = [f'<style>{CSS}</style><div class="ps{_classe_tema(dark)}">',
         f'<div class="rhead"><h2>{_e(per)}<span class="src">letto da PDF</span></h2><div class="meta">{meta}</div></div>']
    if d["warnings"]:
        h.append('<div class="notice">Alcuni totali non tornano esattamente: controlla i valori con il cedolino.</div>')

    # lordo: voci a competenza (Z104 a competenza è un credito d'imposta, va nell'IRPEF)
    z104_credito = bool(z.get("Z104") and z["Z104"].get("comp") and not z["Z104"].get("tratt"))
    comp = [v for v in righe if v["comp"] and (v["code"] != "Z104" or z104_credito)]
    h.append(f'<div class="top"><section class="panel gross"><div class="head"><div class="ttl">TOTALE COMPETENZE</div>'
             f'<div class="sub">Retribuzione lorda</div><div class="big">{_e(eur(d["totalComp"]))}</div></div><div class="ofwhich">di cui</div>')
    for v in comp:
        t, b = _competenza(v, d)
        h.append(_item(t, eur(v["comp"]), b, de=f"{v['code']} {v['desc']}"))
    if d.get("roundComp"):
        h.append(_item("Arrotondamenti", eur(d["roundComp"]), "<p>Differenza di arrotondamento tra le voci e il totale.</p>", short=True))
    h.append("</section>")

    # trattenute
    h.append(f'<section class="panel ded"><div class="head"><div class="ttl">TRATTENUTE</div><div class="sub">Tasse, contributi e altro</div>'
             f'<div class="big">− {_e(eur(d["totalTratt"]))}</div></div><div class="ofwhich">di cui</div>')
    z104, z100 = z.get("Z104"), z.get("Z100")
    if z104 and not z104_credito:
        irpef = (z104["tratt"] or 0) - (z104["comp"] or 0)
        det = [(z[c]["desc"], z[c]["info"]) for c in ("Z082", "Z076") if c in z and z[c].get("info")]
        corpo = "<p>IRPEF trattenuta sul tuo imponibile fiscale" + (f" di <b>{_e(eur(z104['info']))}</b> (retribuzione meno contributi INPS e fondo pensione, che sono deducibili)" if z104.get("info") else "") + ".</p>"
        if det:
            corpo += "<p>Detrazioni applicate: " + ", ".join(f"{_e(n.title())} {_e(eur(a))}" for n, a in det) + ".</p>"
        if z104.get("comp"):
            corpo += f"<p>Questo mese c'è anche un credito di {_e(eur(z104['comp']))} (conguaglio), già sottratto.</p>"
        if d.get("progressive", {}).get("impostaNetta"):
            corpo += f"<p>Da inizio anno hai pagato {_e(eur(d['progressive']['impostaNetta']))} di imposta netta.</p>"
        h.append(_item("Imposta sul reddito", eur(irpef), corpo, de="IRPEF netta"))
    if z100:
        rate = z100["tratt"] / z100["info"] * 100 if z100.get("info") else None
        corpo = ("<p>La tua quota di contributi previdenziali (pensione e altre assicurazioni obbligatorie) versata all'INPS. "
                 "La sanità è pubblica (SSN) e finanziata dalle tasse, non c'è un'assicurazione sanitaria separata.</p>")
        if rate:
            corpo += f'<p><span class="calc">{_e(eur(z100["info"]))} × {_e(pct(rate))} = {_e(eur(z100["tratt"]))}</span></p>'
            if rate > 9.6:
                corpo += "<p>L'aliquota è più alta del solito (9,19%–9,49%): può dipendere dal contributo aggiuntivo sulla parte di retribuzione sopra la soglia.</p>"
        h.append(_item("Contributi previdenziali", eur(z100["tratt"]), corpo, de="INPS (IMPONIBILE PREV.)"))
    altre = [(v, _trattenuta(v, d)) for v in righe if v["tratt"] and v["code"] not in INFO]
    altre = [(v, t) for v, t in altre if t]
    # accorpa le addizionali regionali (più righe)
    reg = [(v, t) for v, t in altre if t[0] == "Addizionale regionale"]
    resto = [(v, t) for v, t in altre if t[0] != "Addizionale regionale"]
    if reg:
        tot = sum(v["tratt"] for v, _ in reg)
        corpo = "".join(t[1] for _, t in reg)
        h.append(_item("Addizionale regionale", eur(tot), corpo, de="Addizionale regionale IRPEF"))
    for i in range(0, len(resto), 2):
        coppia = resto[i:i + 2]
        voci = "".join(_item(t[0], eur(v["tratt"]), t[1], de=f"{v['code']} {v['desc']}", short=len(coppia) == 2) for v, t in coppia)
        h.append(f'<div class="pair">{voci}</div>' if len(coppia) == 2 else voci)
    if d.get("roundTratt"):
        h.append(_item("Arrotondamenti", eur(d["roundTratt"]), "<p>Differenza di arrotondamento tra le voci e il totale.</p>", short=True))
    h.append("</section></div>")

    # netto
    chips = [f"Competenze {eur(d['totalComp'])}", f"− Trattenute {eur(d['totalTratt'])}"]
    ticket = z.get("NP02")
    note = ""
    if ticket and ticket.get("qty") and ticket.get("unit"):
        n = _ore(ticket["qty"])
        note = (f"<p>Più {n:g} ticket restaurant elettronici da {_e(eur(ticket['unit']))} ciascuno, {_e(eur(n * ticket['unit']))} in totale: "
                "caricati su carta, non pagati in contanti.</p>")
    h.append(f'<section class="net"><div class="ttl">NETTO A PAGARE</div><div class="sub">Accredito del {_e(d.get("payDate", ""))}</div>'
             f'<div class="big">{_e(eur(d["netto"]))}</div><div class="flow">' + "".join(f"<span>{_e(c)}</span>" for c in chips) + f"</div>{note}</section>")

    # barra
    tasse = sum((v["tratt"] or 0) - (v["comp"] or 0) for v in righe if v["code"] == "Z104") + sum(
        v["tratt"] or 0 for v in righe if re.search(r"ADDIZ|DETASS|ACC\.IMP", v["desc"].upper()))
    inps = (z100 or {}).get("tratt") or 0
    resto_t = max(0.0, d["totalTratt"] - tasse - inps)
    if d["totalComp"] > 0:
        segs = [(d["netto"], "var(--net)", "Netto"), (tasse, "var(--ded)", "Tasse"), (inps, "var(--ded-line)", "INPS"), (resto_t, "var(--gross)", "Fondo pensione e altro")]
        segs = [s for s in segs if s[0] > 0.005]
        tot = sum(s[0] for s in segs)
        aria = ", ".join(f"{s[2]} {pct(s[0] / tot * 100, 1)}" for s in segs)
        h.append(f'<section class="section"><h3>Come si divide il lordo</h3><p class="lead">Su ogni 100 € di competenze, circa '
                 f'{round(d["netto"] / d["totalComp"] * 100)} € arrivano sul tuo conto.</p><div class="stack" role="img" aria-label="{_e(aria)}">'
                 + "".join(f'<div style="width:{s[0] / tot * 100:.2f}%;background:{s[1]}"></div>' for s in segs) + "</div>"
                 '<div class="legend">' + "".join(f'<span><i style="background:{s[1]}"></i>{_e(s[2])} {_e(pct(s[0] / tot * 100, 1))}</span>' for s in segs) + "</div></section>")

    # card
    pr, res, info = d.get("progressive", {}), d.get("residui", {}), []
    for chiave, titolo, de in (("FERIE", "Ferie residue", "Ferie"), ("PAR", "Permessi residui", "PAR"), ("CONTO ORE", "Banca ore", "Conto ore")):
        r = res.get(chiave)
        if r and r.get("residuo") is not None:
            info.append(_item(titolo, f"{r['residuo']:g} h · {r['residuo'] / 8:.0f} gg", (
                "<p>" + " · ".join(f"{k} {r[c]:g} h" for k, c in (("Anno precedente", "prev"), ("Spettanti", "spettanti"), ("Godute", "godute")) if r.get(c) is not None) +
                ". I cedolini italiani contano le ore: 8 ore = 1 giorno.</p>"), de=de, short=True))
    if pr.get("tfrFondoMese"):
        info.append(_item("TFR a fondo", eur(pr["tfrFondoMese"]) + " / mese", "<p><i>Trattamento di fine rapporto</i>: circa una mensilità l'anno messa da parte per te, "
                          f"qui versata al fondo pensione. Da inizio anno {_e(eur(pr.get('tfrFondoAnno')))}.</p>", de="TFR", cls="b", short=True))
    if pr.get("fondoAziendaMese"):
        info.append(_item("Contributo azienda al fondo", eur(pr["fondoAziendaMese"]) + " / mese", "<p>Poiché versi al fondo pensione, l'azienda aggiunge il suo contributo, che non appare nel netto.</p>",
                          de="Contributo c/azienda", cls="b", short=True))
    for c, titolo in (("Z302", "Polizza sanitaria"), ("Z383", "Fondo sanitario azienda")):
        if c in z and z[c].get("info"):
            info.append(_item(titolo, eur(z[c]["info"]), "<p>Pagata dall'azienda, mostrata solo a titolo informativo: non è una trattenuta.</p>", de=z[c]["desc"].title(), cls="b", short=True))
    if info:
        h.append('<div class="info">' + "".join(info) + "</div>")

    # progressivi
    tab = [("Imponibile previdenziale", pr.get("prevImponibile"), z100 and z100.get("info")), ("Contributi INPS", pr.get("prevContributi"), z100 and z100.get("tratt")),
           ("Imponibile fiscale", pr.get("fiscImponibile"), z104 and z104.get("info")), ("Imposta netta", pr.get("impostaNetta"), z104 and (z104.get("tratt") or 0) - (z104.get("comp") or 0)),
           ("TFR a fondo", pr.get("tfrFondoAnno"), pr.get("tfrFondoMese")), ("Contributi tuoi al fondo", pr.get("fondoDipendente"), None),
           ("Contributi azienda al fondo", pr.get("fondoAzienda"), None)]
    tab = [t for t in tab if t[1] is not None]
    if tab:
        h.append('<section class="section"><h3>Da inizio anno</h3><p class="lead">Totali progressivi riportati in fondo al cedolino.</p><div class="tablewrap"><table><thead><tr>'
                 '<th>Voce</th><th class="num">Questo mese</th><th class="num">Da inizio anno</th></tr></thead><tbody>'
                 + "".join(f'<tr><td>{_e(a)}</td><td class="num">{_e(eur(m) if m is not None else "–")}</td><td class="num">{_e(eur(y))}</td></tr>' for a, y, m in tab)
                 + "</tbody></table></div></section>")
    h.append('<p class="foot">Spiegazione basata sulle cifre del cedolino. I significati di alcuni codici dipendono dall\'azienda. '
             "Non è consulenza fiscale: per casi specifici chiedi all'ufficio paghe o a un CAF / commercialista.</p></div>")
    return "".join(h)
