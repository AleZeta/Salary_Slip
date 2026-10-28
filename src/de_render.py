"""Rendering HTML del cedolino tedesco (stessa grafica di legacy_html/busta-paga-spiegata.html) per st.html."""

from html import escape


def _e(s) -> str:
    return escape(str(s))
from typing import Dict, List, Optional

from src.i18n import fmt_eur, fmt_pct, mesi
from src.de_payslip import (aliquota_pv, classi, classifica_voce_lorda, classifica_voce_netto, dati_bav, note_tetto,
                            testo_flag, tipo_pv, verifica_contributi)

MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre",
        "novembre", "dicembre"]

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700;800&family=Barlow:wght@400;500;600&display=swap');
.ps{--bg:#ffffff;--ink:#1a1a1a;--muted:#5b5b5b;--card:#f3f3f3;--line:rgba(127,127,127,.25);
  --gross:#ff5a36;--gross-soft:#f8ab87;--gross-line:#ff7a58;--ded:#7c35f5;--ded-soft:#e3d6fd;--ded-line:#9a63f7;
  --net:#2aa878;--ok:#1f8a5f;--warn:#c2410c;--info-y:#f6c64f;--info-b:#2f62e6;--onstrong:#ffffff;
  font-family:"Barlow",system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;font-size:16px;line-height:1.5;color:var(--ink);
  background:var(--bg);padding:22px;border-radius:24px}
.ps.dark{--bg:#16151a;--ink:#f1f0f4;--muted:#b3b0bd;--card:#24222b;--line:rgba(200,200,210,.2);
  --gross-soft:#5a2f22;--ded-soft:#34275a;--ded-line:#a57bf8;--ok:#4ade80;--warn:#fb923c}
@media (prefers-color-scheme: dark){
  .ps:not(.light){--bg:#16151a;--ink:#f1f0f4;--muted:#b3b0bd;--card:#24222b;--line:rgba(200,200,210,.2);
    --gross-soft:#5a2f22;--ded-soft:#34275a;--ded-line:#a57bf8;--ok:#4ade80;--warn:#fb923c}}
.ps *{box-sizing:border-box}
.ps h2,.ps h3,.ps .big,.ps .ttl,.ps .n{font-family:"Barlow Condensed","Arial Narrow",Arial,sans-serif}
.ps .rhead h2{font-size:clamp(30px,5vw,44px);line-height:1.05;margin:0;font-weight:800;color:var(--ink)}
.ps .src{font-family:"Barlow",sans-serif;font-size:12.5px;font-weight:500;border-radius:999px;padding:2px 10px;background:var(--card);color:var(--muted);margin-left:10px;vertical-align:middle}
.ps .meta{display:flex;flex-wrap:wrap;gap:6px 18px;font-size:14px;color:var(--muted);margin:6px 0 16px}
.ps .meta b{color:var(--ink);font-weight:600}
.ps .notice{background:var(--card);border-left:4px solid var(--warn);border-radius:10px;padding:10px 14px;margin:0 0 14px;font-size:14.5px}
.ps .top{display:grid;grid-template-columns:1fr 1fr;gap:22px}
@media (max-width:760px){.ps .top{grid-template-columns:1fr}}
.ps .panel{border-radius:22px;padding:18px}
.ps .panel.gross{background:var(--gross-soft)}.ps .panel.ded{background:var(--ded-soft)}
.ps .head{border-radius:16px;padding:18px 16px;text-align:center;color:var(--onstrong);border:2px solid rgba(255,255,255,.7)}
.ps .gross .head{background:var(--gross)}.ps .ded .head{background:var(--ded)}
.ps .ttl{font-size:26px;font-weight:700;letter-spacing:.01em;line-height:1.1}
.ps .sub{font-size:14px;opacity:.9}
.ps .big{font-size:clamp(38px,7vw,54px);font-weight:800;line-height:1.05;margin-top:6px;font-variant-numeric:tabular-nums}
.ps .ofwhich{text-align:center;margin:10px 0;font-size:15px}
.ps .item{background:var(--card);border-radius:14px;border:2px solid var(--gross-line);margin-top:10px}
.ps .ded .item{border-color:var(--ded-line)}
.ps .item summary{list-style:none;cursor:pointer;padding:12px 14px;text-align:center;border-radius:12px}
.ps .item summary::-webkit-details-marker{display:none}
.ps .item .n{font-weight:700;font-size:19px;line-height:1.15}
.ps .item .de{font-size:13px;color:var(--muted)}
.ps .item .v{font-size:19px;font-variant-numeric:tabular-nums}
.ps .item .hint{font-size:12px;color:var(--muted);margin-top:2px}
.ps .item[open] .hint{display:none}
.ps .item .body{padding:0 16px 14px;font-size:14.5px}
.ps .item .body p{margin:.4em 0}
.ps .calc{font-variant-numeric:tabular-nums;background:rgba(127,127,127,.12);border-radius:8px;padding:6px 10px;display:inline-block;font-size:14px}
.ps .chk-ok{color:var(--ok);font-weight:600}.ps .chk-warn{color:var(--warn);font-weight:600}
.ps .pair{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.ps .zero .v{color:var(--muted)}
.ps .net{margin-top:22px;background:var(--net);color:var(--onstrong);border-radius:22px;padding:22px;text-align:center}
.ps .net .ttl{font-size:32px}.ps .net .big{font-size:clamp(52px,11vw,84px)}
.ps .net p{margin:6px auto 0;max-width:62ch;font-size:15px;opacity:.95}
.ps .flow{display:flex;flex-wrap:wrap;justify-content:center;gap:6px 12px;margin-top:12px;font-size:14.5px;font-variant-numeric:tabular-nums}
.ps .flow span{background:rgba(255,255,255,.18);border-radius:999px;padding:3px 12px}
.ps .section{margin-top:34px}
.ps .section h3{font-size:28px;margin:0 0 4px;font-weight:700;color:var(--ink)}
.ps .lead{margin:0 0 12px;color:var(--muted);max-width:70ch}
.ps .stack{display:flex;height:34px;border-radius:10px;overflow:hidden;background:var(--card)}
.ps .legend{display:flex;flex-wrap:wrap;gap:6px 18px;margin-top:10px;font-size:14px}
.ps .legend i{display:inline-block;width:12px;height:12px;border-radius:3px;margin-right:6px;vertical-align:-1px}
.ps .info{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-top:26px}
@media (max-width:860px){.ps .info{grid-template-columns:repeat(2,1fr)}}
.ps .info .item{border-color:var(--info-y)}.ps .info .item.b{border-color:var(--info-b)}
.ps .tablewrap{overflow-x:auto;border-radius:14px;background:var(--card)}
.ps table{border-collapse:collapse;width:100%;min-width:520px;font-size:14.5px}
.ps th,.ps td{padding:9px 14px;text-align:left;border-bottom:1px solid var(--line);color:var(--ink)}
.ps th{font-weight:600}
.ps td.num,.ps th.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.ps tr:last-child td{border-bottom:none}
.ps .gloss{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:8px 22px}
.ps .gloss div{padding:8px 0;border-bottom:1px solid var(--line)}
.ps .gloss b{display:block}.ps .gloss span{font-size:14px;color:var(--muted)}
.ps .foot{margin-top:30px;font-size:13px;color:var(--muted);max-width:75ch}
"""

GLOSSARIO = [
    ("St / SV: L", "Voce regolare (laufender Bezug), tassata e soggetta a contributi."),
    ("St / SV: F", "Voce esente da tasse e contributi (frei)."),
    ("St / SV: S · E", "Pagamento una tantum (sonstiger Bezug / Einmalbezug), es. bonus."),
    ("GB: J", "La voce fa parte del lordo totale."),
    ("Z", "Supplemento per chi non ha figli nell'assicurazione non autosufficienza."),
    ("KK %", "Aliquota totale della cassa malattia, incluso il contributo aggiuntivo."),
    ("PGRS 101", "Gruppo di persone: dipendente regolare soggetto a contributi."),
    ("BGRS 1111", "Contributi a tutte e quattro le assicurazioni sociali."),
    ("St.-Tg. / SV-Tg.", "Giorni considerati per tasse e contributi nel mese."),
    ("§ 108 GewO", "È il prospetto paga obbligatorio per legge: conservalo."),
]

GLOSSARIO_EN = [
    ("St / SV: L", "Regular item (laufender Bezug), taxed and subject to contributions."),
    ("St / SV: F", "Item exempt from tax and contributions (frei)."),
    ("St / SV: S · E", "One-off payment (sonstiger Bezug / Einmalbezug), e.g. a bonus."),
    ("GB: J", "The item is part of total gross pay."),
    ("Z", "Surcharge for people without children in long-term care insurance."),
    ("KK %", "Total rate of the health insurance fund, including the additional contribution."),
    ("PGRS 101", "Person group: regular employee subject to contributions."),
    ("BGRS 1111", "Contributions to all four social insurances."),
    ("St.-Tg. / SV-Tg.", "Days counted for tax and contributions in the month."),
    ("§ 108 GewO", "This is the payslip required by law: keep it."),
]


def eur(v: Optional[float], lang: str = "it") -> str:
    return fmt_eur(v, lang)


def pct(v: float, d: int = 2, lang: str = "it") -> str:
    return fmt_pct(v, d, lang)


def _classe_tema(dark: Optional[bool]) -> str:
    """True = scuro, False = chiaro, None = segue le preferenze del sistema."""
    return "" if dark is None else (" dark" if dark else " light")


def _item(n: str, v: str, body: str, de: str = "", zero: bool = False, short: bool = False, cls: str = "", lang: str = "it") -> str:
    return (f'<details class="item{" zero" if zero else ""}{" " + cls if cls else ""}"><summary>'
            f'<div class="n">{_e(n)}</div>' + (f'<div class="de">{_e(de)}</div>' if de else "") +
            f'<div class="v">{_e(v)}</div><div class="hint">{("Tap" if short else "Tap for details") if lang == "en" else ("Tocca" if short else "Tocca per i dettagli")}</div></summary>'
            f'<div class="body">{body}</div></details>')


def _check(actual: float, atteso: float, lang: str = "it") -> str:
    if abs(actual - atteso) <= 0.06:
        return '<p class="chk-ok">✓ The calculation checks out</p>' if lang == "en" else '<p class="chk-ok">✓ Il calcolo torna</p>'
    if lang == "en":
        return f'<p class="chk-warn">⚠ Does not add up: expected {_e(eur(atteso, lang))}</p>'
    return f'<p class="chk-warn">⚠ Non torna: atteso {_e(eur(atteso))}</p>'


def _stima_risparmio(d: Dict, b: Dict) -> Optional[float]:
    """Stima il risparmio di tasse e contributi della bAV rifacendo il calcolo annuale con e senza versamento."""
    try:
        from src.de_calc import calcola
        kk = d.get("kvRateTotal") or 17.5
        stip = (d["taxGross"] + b["conversion"]) * 12
        pct_d = b["employer"] / b["conversion"] * 100 if b["conversion"] else 0.0
        con = calcola(stip, kk, not d.get("childlessFlag", True), 0.0, d.get("year") or 2026, b["conversion"], pct_d)
        return con["bav"]["saving"]
    except Exception:  # dati insufficienti per la stima
        return None


def _sezione_bav(d: Dict, lang: str = "it") -> str:
    """Pensione aziendale (bAV): versamenti, contributo del datore e costo reale per il dipendente."""
    b = dati_bav(d)
    if not b:
        return ""
    tr = lambda it, en: en if lang == "en" else it
    eur_ = lambda v: eur(v, lang)
    mese = tr(" / mese", " / month")
    risparmio = b.get("saving") if "saving" in b else _stima_risparmio(d, b)
    stima = "saving" not in b
    cards = [
        _item(tr("Il tuo versamento", "Your contribution"), eur_(b["conversion"]) + mese, tr(
            "<p><i>Entgeltumwandlung</i>: rinunci a una parte del lordo e quel denaro va nella pensione aziendale. "
            "Sul cedolino compare come riduzione dello stipendio e come versamento esente (§ 3 Nr. 63 EStG).</p>"
            "<p>Su questa parte non paghi imposte, e in parte nemmeno contributi sociali (limiti: 8% del tetto RV/AV per le tasse, 4% per i contributi).</p>",
            "<p><i>Entgeltumwandlung</i>: you give up part of your gross pay and that money goes into the occupational pension. "
            "On the payslip it shows up as a salary reduction and as an exempt payment (§ 3 Nr. 63 EStG).</p>"
            "<p>You pay no tax on this part, and partly no social contributions either (limits: 8% of the RV/AV ceiling for tax, 4% for contributions).</p>"),
              de="Gehaltsverzicht", cls="b", short=True, lang=lang),
        _item(tr("Contributo del datore", "Employer contribution"), eur_(b["employer"]) + mese, tr(
            "<p>Il datore aggiunge un suo contributo (per legge almeno il 15% di ciò che converti, se risparmia contributi sociali). "
            "Non è nel lordo e non paghi imposte su di esso.</p>",
            "<p>Your employer adds its own contribution (by law at least 15% of what you convert, if it saves social contributions). "
            "It is not in your gross pay and you pay no tax on it.</p>"), de="AG-Zuschuss", cls="b", short=True, lang=lang),
        _item(tr("Totale in pensione", "Total into pension"), eur_(b["total"]) + mese, tr(
            "<p>La somma di versamento tuo e contributo del datore: è ciò che viene investito ogni mese.</p>",
            "<p>The sum of your contribution and the employer contribution: this is what gets invested every month.</p>"),
              de=tr("Totale versato", "Total paid in"), cls="b", short=True, lang=lang)]
    if risparmio is not None:
        costo = b["conversion"] - risparmio
        stima_t = tr(" (stima)", " (estimate)") if stima else ""
        cards.append(_item(tr("Costo reale per te", "Real cost to you"), eur_(costo) + mese, tr(
            f"<p>Il versamento di {_e(eur_(b['conversion']))} ti riduce il netto di soli circa <b>{_e(eur_(costo))}</b>, "
            f"perché risparmi circa {_e(eur_(risparmio))} tra imposte e contributi{stima_t}.</p>"
            "<p>Contropartita: minori contributi pensionistici pubblici e tassazione della rendita o del capitale al pensionamento.</p>",
            f"<p>The {_e(eur_(b['conversion']))} contribution lowers your net pay by only about <b>{_e(eur_(costo))}</b>, "
            f"because you save about {_e(eur_(risparmio))} in tax and contributions{stima_t}.</p>"
            "<p>Trade-off: lower public pension contributions and taxation of the annuity or lump sum at retirement.</p>"),
            de=tr("Dopo il risparmio fiscale", "After the tax saving"), cls="b", short=True, lang=lang))
    return (f'<section class="section"><h3>{tr("Pensione aziendale (bAV)", "Occupational pension (bAV)")}</h3><p class="lead">'
            + tr("Una parte del lordo va direttamente in una pensione aziendale: su quel versamento non paghi imposte, e il datore aggiunge il suo contributo.",
                 "Part of your gross pay goes straight into an occupational pension: you pay no tax on that contribution, and your employer adds its own.")
            + '</p><div class="info" style="margin-top:14px">' + "".join(cards) + "</div></section>")


def report_html(d: Dict, dark: Optional[bool] = None, lang: str = "it") -> str:
    tr = lambda it, en: en if lang == "en" else it
    eur_ = lambda v: eur(v, lang)
    pct_ = lambda v, dec=2: pct(v, dec, lang)
    sorgente = {"datev": tr("letta da PDF DATEV", "read from DATEV PDF"), "manual": tr("inserita a mano", "entered manually"),
                "calc": tr("calcolo da stipendio annuo · 2026", "calculated from annual salary · 2026")}.get(d.get("source"), "")
    periodo = f"{mesi(lang)[d['month'] - 1].capitalize()} {d.get('year', '')}" if d.get("month") else str(d.get("year", ""))
    meta = "".join(f"<span>{_e(k)} <b>{_e(v)}</b></span>" for k, v in
                   ((tr("Datore di lavoro", "Employer"), d.get("employer")), (tr("Pagata il", "Paid on"), d.get("payDate")),
                    (tr("Assunto dal", "Hired on"), d.get("startDate"))) if v)
    h = [f'<style>{CSS}</style><div class="ps{_classe_tema(dark)}">',
         f'<div class="rhead"><h2>{_e(periodo)}<span class="src">{_e(sorgente)}</span></h2><div class="meta">{meta}</div></div>']
    if d["warnings"]:
        h.append('<div class="notice">' + tr("Alcuni totali non tornano esattamente: controlla i valori con il cedolino.",
                                             "Some totals do not add up exactly: check the values against your payslip.") + "</div>")
    di = tr("di cui", "of which")

    # --- lordo
    h.append(f'<div class="top"><section class="panel gross"><div class="head"><div class="ttl">{tr("STIPENDIO LORDO", "GROSS SALARY")}</div>'
             f'<div class="sub">Gesamt-Brutto</div><div class="big">{_e(eur_(d["totalGross"]))}</div></div><div class="ofwhich">{di}</div>')
    for p in (p for p in d["payments"] if p.get("gb") != "N"):  # N = non fa parte del lordo totale
        titolo, spiega = classifica_voce_lorda(p["label"], lang)
        fl = testo_flag(p["tax"], p["sv"], lang=lang)
        h.append(_item(titolo, eur_(p["amount"]), f"<p>{_e(spiega)}</p>" + (f"<p>{_e(fl)}</p>" if fl else ""),
                       de=f'{p["code"]} {p["label"]}'.strip(), lang=lang))
    h.append("</section>")

    # --- tasse e contributi
    ded = d["taxTotal"] + d["svTotal"]
    h.append(f'<section class="panel ded"><div class="head"><div class="ttl">{tr("TASSE E CONTRIBUTI", "TAXES AND CONTRIBUTIONS")}</div>'
             f'<div class="sub">Steuer- und SV-Abzüge</div><div class="big">− {_e(eur_(ded))}</div></div><div class="ofwhich">{di}</div>')
    eff = pct_(d["wageTax"] / d["taxGross"] * 100, 1) if d["taxGross"] else "–"
    classe = d.get("taxClass")
    h.append(_item(tr("Imposta sul reddito", "Income tax"), eur_(d["wageTax"]), tr(
        f"<p>Imposta trattenuta ogni mese e versata al Finanzamt. Calcolata sul lordo imponibile di {_e(eur_(d['taxGross']))} "
        f"con la classe d'imposta {_e(classe or '–')}. Aliquota effettiva su questo mese: {_e(eff)}.</p>"
        "<p>È un acconto: con la dichiarazione dei redditi (Steuererklärung) le spese di lavoro possono farti recuperare una parte.</p>",
        f"<p>Tax withheld every month and paid to the Finanzamt. Calculated on taxable gross pay of {_e(eur_(d['taxGross']))} "
        f"with tax class {_e(classe or '–')}. Effective rate for this month: {_e(eff)}.</p>"
        "<p>It is an advance payment: with your tax return (Steuererklärung), work-related expenses may let you recover part of it.</p>"),
        de="Lohnsteuer", lang=lang))
    ver = verifica_contributi(d)
    kk = d.get("kvRateTotal")
    if kk:
        kv_body = tr(f"<p>Assicurazione sanitaria pubblica. Aliquota totale {pct_(kk)} (14,6% generale + contributo aggiuntivo della cassa), "
                     f"divisa a metà: paghi tu {pct_(kk / 2, 3)}.</p>",
                     f"<p>Public health insurance. Total rate {pct_(kk)} (14.6% general + the fund's additional contribution), "
                     f"split in half: you pay {pct_(kk / 2, 3)}.</p>")
        if "kv" in ver:
            r = ver["kv"]
            kv_body += f'<p><span class="calc">{_e(eur_(r["base"]))} × {_e(pct_(r["aliquota"], 3))} = {_e(eur_(r["atteso"]))}</span></p>' + _check(d["kv"], r["atteso"], lang)
    else:
        kv_body = tr("<p>Assicurazione sanitaria pubblica: l'aliquota totale (14,6% + contributo aggiuntivo) è divisa a metà con il datore di lavoro.</p>",
                     "<p>Public health insurance: the total rate (14.6% + additional contribution) is split in half with your employer.</p>")
    cap = "".join(f"<p>{_e(n)}</p>" for n in note_tetto(d, lang))
    h.append(_item(tr("Assicurazione sanitaria", "Health insurance"), eur_(d["kv"]), kv_body + cap,
                   de="KV-Beitrag" + (f" · {d['insurer']}" if d.get("insurer") else ""), lang=lang))
    rv_body = tr("<p>Contributo alla pensione pubblica (Deutsche Rentenversicherung). Aliquota totale 18,6%, divisa a metà: 9,3% a te e 9,3% al datore di lavoro.</p>",
                 "<p>Contribution to the public pension (Deutsche Rentenversicherung). Total rate 18.6%, split in half: 9.3% from you and 9.3% from your employer.</p>")
    if "rv" in ver:
        r = ver["rv"]
        rv_body += f'<p><span class="calc">{_e(eur_(r["base"]))} × {_e(pct_(9.3, 1))} = {_e(eur_(r["atteso"]))}</span></p>' + _check(d["rv"], r["atteso"], lang)
    h.append(_item(tr("Assicurazione pensionistica", "Pension insurance"), eur_(d["rv"]), rv_body, de="RV-Beitrag", lang=lang))

    rate = aliquota_pv(d)
    kind = tipo_pv(rate, d.get("childlessFlag", False), lang)
    pv_body = tr(f"<p>Copre le cure in caso di non autosufficienza. La tua quota è "
                 f"{_e(pct_(rate) if rate is not None else '')}{(' – ' + _e(kind)) if kind else ''}.</p>",
                 f"<p>Covers care in case of long-term care need. Your share is "
                 f"{_e(pct_(rate) if rate is not None else '')}{(' – ' + _e(kind)) if kind else ''}.</p>")
    if d.get("pvGross") and rate is not None:
        pv_body += f'<p><span class="calc">{_e(eur_(d["pvGross"]))} × {_e(pct_(rate))} = {_e(eur_(d["pv"]))}</span></p>'
    av_body = tr("<p>Finanzia l'indennità di disoccupazione (Arbeitslosengeld). Aliquota totale 2,6%, divisa a metà: 1,3% a te.</p>",
                 "<p>Funds unemployment benefit (Arbeitslosengeld). Total rate 2.6%, split in half: 1.3% from you.</p>")
    if "av" in ver:
        r = ver["av"]
        av_body += f'<p><span class="calc">{_e(eur_(r["base"]))} × {_e(pct_(1.3, 1))} = {_e(eur_(r["atteso"]))}</span></p>' + _check(d["av"], r["atteso"], lang)
    h.append('<div class="pair">' + _item(tr("Non autosufficienza", "Long-term care"), eur_(d["pv"]), pv_body, de="PV-Beitrag", short=True, lang=lang)
             + _item(tr("Disoccupazione", "Unemployment"), eur_(d["av"]), av_body, de="AV-Beitrag", short=True, lang=lang) + "</div>")
    soli_b = (tr("<p>Sovrattassa sull'imposta sul reddito, dovuta sopra una certa soglia (con una zona di raccordo graduale).</p>",
                 "<p>A surcharge on income tax, due above a certain threshold (with a gradual phase-in zone).</p>") if d["soli"] else
              tr("<p>Sovrattassa del 5,5% sull'imposta, dovuta solo dai redditi alti. Sei sotto la soglia, quindi non la paghi.</p>",
                 "<p>A 5.5% surcharge on tax, due only on high incomes. You are below the threshold, so you do not pay it.</p>"))
    church_b = (tr("<p>Imposta per gli iscritti a una chiesa: 8% dell'imposta sul reddito in Baviera e Baden-Württemberg, 9% altrove.</p>",
                   "<p>Tax for church members: 8% of income tax in Bavaria and Baden-Württemberg, 9% elsewhere.</p>") if d["church"] else
                tr("<p>Dovuta solo dagli iscritti a una chiesa che riscuote l'imposta (8–9% dell'imposta sul reddito). Qui non viene trattenuta.</p>",
                   "<p>Due only from members of a church that collects the tax (8–9% of income tax). It is not withheld here.</p>"))
    h.append('<div class="pair">' + _item(tr("Contributo di solidarietà", "Solidarity surcharge"), eur_(d["soli"]), soli_b, de="Solidaritätszuschlag", zero=not d["soli"], short=True, lang=lang)
             + _item(tr("Imposta ecclesiastica", "Church tax"), eur_(d["church"]), church_b, de="Kirchensteuer", zero=not d["church"], short=True, lang=lang) + "</div></section></div>")

    # --- netto
    chips = [f"{tr('Lordo', 'Gross')} {eur_(d['totalGross'])}", f"− {tr('Tasse', 'Taxes')} {eur_(d['taxTotal'])}",
             f"− {tr('Contributi', 'Contributions')} {eur_(d['svTotal'])}", f"= {tr('Netto', 'Net')} {eur_(d['netIncome'])}"]
    chips += [f"{'−' if p['amount'] < 0 else '+'} {classifica_voce_netto(p['label'], lang)[0]} {eur_(abs(p['amount']))}" for p in d["netItems"]]
    h.append(f'<section class="net"><div class="ttl">{tr("ACCREDITATO SUL CONTO", "PAID INTO YOUR ACCOUNT")}</div><div class="sub">Auszahlungsbetrag</div>'
             f'<div class="big">{_e(eur_(d["payout"]))}</div><div class="flow">' + "".join(f"<span>{_e(c)}</span>" for c in chips) + "</div>"
             + (("<p>" + tr("Le voci dopo il netto (per esempio mensa, bici aziendale, anticipi) vengono tolte o aggiunte dopo tasse e contributi.",
                            "Items after net pay (for example canteen, company bike, advances) are deducted or added after tax and contributions.") + "</p>")
                if d["netItems"] else "")
             + "</section>")

    h.append(_sezione_bav(d, lang))

    # --- barra di ripartizione
    if d["totalGross"] > 0:
        neg = -sum(p["amount"] for p in d["netItems"] if p["amount"] < 0)
        segs = [(max(0.0, d["totalGross"] - d["taxTotal"] - d["svTotal"] - neg), "var(--net)", tr("Accreditato", "Paid out")),
                (d["taxTotal"], "var(--ded)", tr("Tasse", "Taxes")), (d["svTotal"], "var(--ded-line)", tr("Contributi sociali", "Social contributions")),
                (neg, "var(--gross)", tr("Trattenute dopo il netto", "Deductions after net"))]
        segs = [s for s in segs if s[0] > 0.005]
        tot = sum(s[0] for s in segs)
        aria = ", ".join(f"{s[2]} {pct_(s[0] / tot * 100, 1)}" for s in segs)
        quota = round(d["payout"] / d["totalGross"] * 100)
        h.append(f'<section class="section"><h3>{tr("Come si divide il lordo", "How your gross pay is split")}</h3><p class="lead">'
                 + tr(f"Su ogni 100 € di lordo, circa {quota} € arrivano sul tuo conto.", f"Out of every €100 of gross pay, about €{quota} reaches your account.")
                 + f'</p><div class="stack" role="img" aria-label="{_e(aria)}">'
                 + "".join(f'<div style="width:{s[0] / tot * 100:.2f}%;background:{s[1]}"></div>' for s in segs) + "</div>"
                 '<div class="legend">' + "".join(f'<span><i style="background:{s[1]}"></i>{_e(s[2])} {_e(pct_(s[0] / tot * 100, 1))}</span>' for s in segs)
                 + "</div></section>")

    # --- card informative
    if kk:
        kk_body = tr(f"Aliquota totale {_e(pct_(kk))}, inclusa la quota aggiuntiva della tua cassa.",
                     f"Total rate {_e(pct_(kk))}, including your fund's additional contribution.")
    else:
        kk_body = tr("La tua cassa malattia pubblica.", "Your public health insurance fund.")
    info = [_item(tr("Classe d'imposta", "Tax class"), str(classe or "–"),
                  f"<p>{_e(classi(lang).get(classe, tr('Determina quanta imposta viene trattenuta ogni mese.', 'Determines how much tax is withheld every month.')))}</p>",
                  de="StKl", short=True, lang=lang),
            _item(tr("Cassa malattia", "Health fund"), d.get("insurer") or (pct_(kk) if kk else "–"), f"<p>{kk_body}</p>", de="Krankenkasse", short=True, lang=lang)]
    if d.get("agSv") is not None:
        info.append(_item(tr("Contributi dell'azienda", "Employer contributions"), eur_(d["agSv"]), tr(
            "<p>Oltre al tuo lordo, l'azienda paga la sua metà di pensione, sanità, disoccupazione e "
            "non autosufficienza. Non compare nel netto ma conta per pensione e prestazioni.</p>",
            "<p>On top of your gross pay, the company pays its half of pension, health, unemployment and "
            "long-term care insurance. It does not show up in your net pay but counts towards your pension and benefits.</p>"),
            de="SV-AG-Anteil", cls="b", short=True, lang=lang))
    if d.get("agTotal") is not None:
        extra = (tr(f" + altri oneri {eur_(d['agAdd'])} (assicurazioni per malattia, maternità e insolvenza, Umlagen)",
                    f" + other charges {eur_(d['agAdd'])} (sickness, maternity and insolvency insurance, Umlagen)") if d.get("agAdd") else "")
        info.append(_item(tr("Costo totale per l'azienda", "Total cost to the employer"), eur_(d["agTotal"]),
                          tr(f"<p>Lordo {_e(eur_(d['totalGross']))} + contributi azienda {_e(eur_(d.get('agSv')))}{_e(extra)}.</p>",
                             f"<p>Gross pay {_e(eur_(d['totalGross']))} + employer contributions {_e(eur_(d.get('agSv')))}{_e(extra)}.</p>"),
                          de="Gesamtkosten", cls="b", short=True, lang=lang))
    h.append('<div class="info">' + "".join(info) + "</div>")

    # --- da inizio anno
    y = d.get("ytd") or {}
    if y:
        mese = {"gross": d["totalGross"], "taxGross": d["taxGross"], "taxFree": sum(p["amount"] for p in d["payments"] if p["tax"] == "F" and p.get("gb") != "N"),
                "wageTax": d["wageTax"], "soli": d["soli"], "church": d["church"], "svGross": d.get("rvGross"),
                "kv": d["kv"], "rv": d["rv"], "av": d["av"], "pv": d["pv"]}
        nomi = {"gross": (tr("Lordo totale", "Total gross"), "Gesamt-Brutto"), "taxGross": (tr("Lordo imponibile", "Taxable gross"), "Steuer-Brutto"),
                "taxFree": (tr("Voci esenti", "Tax-free items"), "Steuerfreie Bezüge"), "wageTax": (tr("Imposta sul reddito", "Income tax"), "Lohnsteuer"),
                "soli": (tr("Solidarietà", "Solidarity surcharge"), "Solidaritätszuschlag"), "church": (tr("Imposta ecclesiastica", "Church tax"), "Kirchensteuer"),
                "svGross": (tr("Base contributiva", "Contribution base"), "SV-Brutto"), "kv": (tr("Sanitaria", "Health"), "KV-Beitrag"),
                "rv": (tr("Pensionistica", "Pension"), "RV-Beitrag"), "av": (tr("Disoccupazione", "Unemployment"), "AV-Beitrag"),
                "pv": (tr("Non autosufficienza", "Long-term care"), "PV-Beitrag")}
        righe = [(k, v) for k, v in y.items() if k in nomi and not (v == 0 and not mese.get(k))]
        h.append(f'<section class="section"><h3>{tr("Da inizio anno", "Year to date")}</h3><p class="lead">'
                 + tr("Totali progressivi dal blocco Verdienstbescheinigung.", "Running totals from the Verdienstbescheinigung block.") + '</p>'
                 f'<div class="tablewrap"><table><thead><tr><th>{tr("Voce", "Item")}</th><th>{tr("Termine tedesco", "German term")}</th>'
                 f'<th class="num">{tr("Questo mese", "This month")}</th><th class="num">{tr("Da inizio anno", "Year to date")}</th></tr></thead><tbody>'
                 + "".join(f'<tr><td>{_e(nomi[k][0])}</td><td>{_e(nomi[k][1])}</td><td class="num">{_e(eur_(mese.get(k)))}</td>'
                           f'<td class="num">{_e(eur_(v))}</td></tr>' for k, v in righe) + "</tbody></table></div></section>")

    gloss = GLOSSARIO_EN if lang == "en" else GLOSSARIO
    h.append(f'<section class="section"><h3>{tr("Le sigle del cedolino", "Payslip abbreviations")}</h3><div class="gloss">'
             + "".join(f"<div><b>{_e(a)}</b><span>{_e(b)}</span></div>" for a, b in gloss) + "</div></section>")
    h.append('<p class="foot">' + tr("Spiegazione basata sulle cifre del cedolino e sulle aliquote 2026. Non è consulenza fiscale: "
                                     "per casi specifici chiedi all'ufficio paghe o a un consulente fiscale (Steuerberater).",
                                     "Explanation based on the figures on your payslip and the 2026 rates. This is not tax advice: "
                                     "for specific cases ask your payroll department or a tax advisor (Steuerberater).") + "</p></div>")
    return "".join(h)
