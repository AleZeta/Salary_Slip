"""Rendering HTML del cedolino tedesco (stessa grafica di legacy_html/busta-paga-spiegata.html) per st.html."""

from html import escape


def _e(s) -> str:
    return escape(str(s))
from typing import Dict, List, Optional

from src.de_payslip import (CLASSI, aliquota_pv, classifica_voce_lorda, classifica_voce_netto, note_tetto, testo_flag,
                            tipo_pv, verifica_contributi)

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


def eur(v: Optional[float]) -> str:
    if v is None:
        return "–"
    testo = f"{abs(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return ("− € " if v < 0 else "€ ") + testo


def pct(v: float, d: int = 2) -> str:
    return f"{v:.{d}f}".replace(".", ",") + "%"


def _classe_tema(dark: Optional[bool]) -> str:
    """True = scuro, False = chiaro, None = segue le preferenze del sistema."""
    return "" if dark is None else (" dark" if dark else " light")


def _item(n: str, v: str, body: str, de: str = "", zero: bool = False, short: bool = False, cls: str = "") -> str:
    return (f'<details class="item{" zero" if zero else ""}{" " + cls if cls else ""}"><summary>'
            f'<div class="n">{_e(n)}</div>' + (f'<div class="de">{_e(de)}</div>' if de else "") +
            f'<div class="v">{_e(v)}</div><div class="hint">{"Tocca" if short else "Tocca per i dettagli"}</div></summary>'
            f'<div class="body">{body}</div></details>')


def _check(actual: float, atteso: float) -> str:
    if abs(actual - atteso) <= 0.06:
        return '<p class="chk-ok">✓ Il calcolo torna</p>'
    return f'<p class="chk-warn">⚠ Non torna: atteso {_e(eur(atteso))}</p>'


def report_html(d: Dict, dark: Optional[bool] = None) -> str:
    sorgente = {"datev": "letta da PDF DATEV", "manual": "inserita a mano", "calc": "calcolo da stipendio annuo · 2026"}.get(d.get("source"), "")
    periodo = f"{MESI[d['month'] - 1].capitalize()} {d.get('year', '')}" if d.get("month") else str(d.get("year", ""))
    meta = "".join(f"<span>{_e(k)} <b>{_e(v)}</b></span>" for k, v in
                   (("Datore di lavoro", d.get("employer")), ("Pagata il", d.get("payDate")), ("Assunto dal", d.get("startDate"))) if v)
    h = [f'<style>{CSS}</style><div class="ps{_classe_tema(dark)}">',
         f'<div class="rhead"><h2>{_e(periodo)}<span class="src">{_e(sorgente)}</span></h2><div class="meta">{meta}</div></div>']
    if d["warnings"]:
        h.append('<div class="notice">Alcuni totali non tornano esattamente: controlla i valori con il cedolino.</div>')

    # --- lordo
    h.append(f'<div class="top"><section class="panel gross"><div class="head"><div class="ttl">STIPENDIO LORDO</div>'
             f'<div class="sub">Gesamt-Brutto</div><div class="big">{_e(eur(d["totalGross"]))}</div></div><div class="ofwhich">di cui</div>')
    for p in d["payments"]:
        titolo, spiega = classifica_voce_lorda(p["label"])
        fl = testo_flag(p["tax"], p["sv"])
        h.append(_item(titolo, eur(p["amount"]), f"<p>{_e(spiega)}</p>" + (f"<p>{_e(fl)}</p>" if fl else ""),
                       de=f'{p["code"]} {p["label"]}'.strip()))
    h.append("</section>")

    # --- tasse e contributi
    ded = d["taxTotal"] + d["svTotal"]
    h.append(f'<section class="panel ded"><div class="head"><div class="ttl">TASSE E CONTRIBUTI</div>'
             f'<div class="sub">Steuer- und SV-Abzüge</div><div class="big">− {_e(eur(ded))}</div></div><div class="ofwhich">di cui</div>')
    eff = pct(d["wageTax"] / d["taxGross"] * 100, 1) if d["taxGross"] else "–"
    classe = d.get("taxClass")
    h.append(_item("Imposta sul reddito", eur(d["wageTax"]), (
        f"<p>Imposta trattenuta ogni mese e versata al Finanzamt. Calcolata sul lordo imponibile di {_e(eur(d['taxGross']))} "
        f"con la classe d'imposta {_e(classe or '–')}. Aliquota effettiva su questo mese: {_e(eff)}.</p>"
        "<p>È un acconto: con la dichiarazione dei redditi (Steuererklärung) le spese di lavoro possono farti recuperare una parte.</p>"),
        de="Lohnsteuer"))
    ver = verifica_contributi(d)
    kk = d.get("kvRateTotal")
    if kk:
        kv_body = (f"<p>Assicurazione sanitaria pubblica. Aliquota totale {pct(kk)} (14,6% generale + contributo aggiuntivo della cassa), "
                   f"divisa a metà: paghi tu {pct(kk / 2, 3)}.</p>")
        if "kv" in ver:
            r = ver["kv"]
            kv_body += f'<p><span class="calc">{_e(eur(r["base"]))} × {_e(pct(r["aliquota"], 3))} = {_e(eur(r["atteso"]))}</span></p>' + _check(d["kv"], r["atteso"])
    else:
        kv_body = "<p>Assicurazione sanitaria pubblica: l'aliquota totale (14,6% + contributo aggiuntivo) è divisa a metà con il datore di lavoro.</p>"
    cap = "".join(f"<p>{_e(n)}</p>" for n in note_tetto(d))
    h.append(_item("Assicurazione sanitaria", eur(d["kv"]), kv_body + cap, de="KV-Beitrag" + (f" · {d['insurer']}" if d.get("insurer") else "")))
    rv_body = "<p>Contributo alla pensione pubblica (Deutsche Rentenversicherung). Aliquota totale 18,6%, divisa a metà: 9,3% a te e 9,3% al datore di lavoro.</p>"
    if "rv" in ver:
        r = ver["rv"]
        rv_body += f'<p><span class="calc">{_e(eur(r["base"]))} × {_e(pct(9.3, 1))} = {_e(eur(r["atteso"]))}</span></p>' + _check(d["rv"], r["atteso"])
    h.append(_item("Assicurazione pensionistica", eur(d["rv"]), rv_body, de="RV-Beitrag"))

    rate = aliquota_pv(d)
    kind = tipo_pv(rate, d.get("childlessFlag", False))
    pv_body = (f"<p>Copre le cure in caso di non autosufficienza. La tua quota è "
               f"{_e(pct(rate) if rate is not None else '')}{(' – ' + _e(kind)) if kind else ''}.</p>")
    if d.get("pvGross") and rate is not None:
        pv_body += f'<p><span class="calc">{_e(eur(d["pvGross"]))} × {_e(pct(rate))} = {_e(eur(d["pv"]))}</span></p>'
    av_body = "<p>Finanzia l'indennità di disoccupazione (Arbeitslosengeld). Aliquota totale 2,6%, divisa a metà: 1,3% a te.</p>"
    if "av" in ver:
        r = ver["av"]
        av_body += f'<p><span class="calc">{_e(eur(r["base"]))} × {_e(pct(1.3, 1))} = {_e(eur(r["atteso"]))}</span></p>' + _check(d["av"], r["atteso"])
    h.append('<div class="pair">' + _item("Non autosufficienza", eur(d["pv"]), pv_body, de="PV-Beitrag", short=True)
             + _item("Disoccupazione", eur(d["av"]), av_body, de="AV-Beitrag", short=True) + "</div>")
    soli_b = ("<p>Sovrattassa sull'imposta sul reddito, dovuta sopra una certa soglia (con una zona di raccordo graduale).</p>" if d["soli"] else
              "<p>Sovrattassa del 5,5% sull'imposta, dovuta solo dai redditi alti. Sei sotto la soglia, quindi non la paghi.</p>")
    church_b = ("<p>Imposta per gli iscritti a una chiesa: 8% dell'imposta sul reddito in Baviera e Baden-Württemberg, 9% altrove.</p>" if d["church"] else
                "<p>Dovuta solo dagli iscritti a una chiesa che riscuote l'imposta (8–9% dell'imposta sul reddito). Qui non viene trattenuta.</p>")
    h.append('<div class="pair">' + _item("Contributo di solidarietà", eur(d["soli"]), soli_b, de="Solidaritätszuschlag", zero=not d["soli"], short=True)
             + _item("Imposta ecclesiastica", eur(d["church"]), church_b, de="Kirchensteuer", zero=not d["church"], short=True) + "</div></section></div>")

    # --- netto
    chips = [f"Lordo {eur(d['totalGross'])}", f"− Tasse {eur(d['taxTotal'])}", f"− Contributi {eur(d['svTotal'])}", f"= Netto {eur(d['netIncome'])}"]
    chips += [f"{'−' if p['amount'] < 0 else '+'} {classifica_voce_netto(p['label'])[0]} {eur(abs(p['amount']))}" for p in d["netItems"]]
    h.append(f'<section class="net"><div class="ttl">ACCREDITATO SUL CONTO</div><div class="sub">Auszahlungsbetrag</div>'
             f'<div class="big">{_e(eur(d["payout"]))}</div><div class="flow">' + "".join(f"<span>{_e(c)}</span>" for c in chips) + "</div>"
             + ("<p>Le voci dopo il netto (per esempio mensa, bici aziendale, anticipi) vengono tolte o aggiunte dopo tasse e contributi.</p>" if d["netItems"] else "")
             + "</section>")

    # --- barra di ripartizione
    if d["totalGross"] > 0:
        neg = -sum(p["amount"] for p in d["netItems"] if p["amount"] < 0)
        segs = [(max(0.0, d["totalGross"] - d["taxTotal"] - d["svTotal"] - neg), "var(--net)", "Accreditato"),
                (d["taxTotal"], "var(--ded)", "Tasse"), (d["svTotal"], "var(--ded-line)", "Contributi sociali"),
                (neg, "var(--gross)", "Trattenute dopo il netto")]
        segs = [s for s in segs if s[0] > 0.005]
        tot = sum(s[0] for s in segs)
        aria = ", ".join(f"{s[2]} {pct(s[0] / tot * 100, 1)}" for s in segs)
        h.append(f'<section class="section"><h3>Come si divide il lordo</h3><p class="lead">Su ogni 100 € di lordo, circa '
                 f'{round(d["payout"] / d["totalGross"] * 100)} € arrivano sul tuo conto.</p>'
                 f'<div class="stack" role="img" aria-label="{_e(aria)}">'
                 + "".join(f'<div style="width:{s[0] / tot * 100:.2f}%;background:{s[1]}"></div>' for s in segs) + "</div>"
                 '<div class="legend">' + "".join(f'<span><i style="background:{s[1]}"></i>{_e(s[2])} {_e(pct(s[0] / tot * 100, 1))}</span>' for s in segs)
                 + "</div></section>")

    # --- card informative
    info = [_item("Classe d'imposta", str(classe or "–"), f"<p>{_e(CLASSI.get(classe, 'Determina quanta imposta viene trattenuta ogni mese.'))}</p>", de="StKl", short=True),
            _item("Cassa malattia", d.get("insurer") or (pct(kk) if kk else "–"),
                  f"<p>{'Aliquota totale ' + _e(pct(kk)) + ', inclusa la quota aggiuntiva della tua cassa.' if kk else 'La tua cassa malattia pubblica.'}</p>", de="Krankenkasse", short=True)]
    if d.get("agSv") is not None:
        info.append(_item("Contributi dell'azienda", eur(d["agSv"]), "<p>Oltre al tuo lordo, l'azienda paga la sua metà di pensione, sanità, disoccupazione e "
                          "non autosufficienza. Non compare nel netto ma conta per pensione e prestazioni.</p>", de="SV-AG-Anteil", cls="b", short=True))
    if d.get("agTotal") is not None:
        extra = f" + altri oneri {eur(d['agAdd'])} (assicurazioni per malattia, maternità e insolvenza, Umlagen)" if d.get("agAdd") else ""
        info.append(_item("Costo totale per l'azienda", eur(d["agTotal"]),
                          f"<p>Lordo {_e(eur(d['totalGross']))} + contributi azienda {_e(eur(d.get('agSv')))}{_e(extra)}.</p>", de="Gesamtkosten", cls="b", short=True))
    h.append('<div class="info">' + "".join(info) + "</div>")

    # --- da inizio anno
    y = d.get("ytd") or {}
    if y:
        mese = {"gross": d["totalGross"], "taxGross": d["taxGross"], "taxFree": sum(p["amount"] for p in d["payments"] if p["tax"] == "F"),
                "wageTax": d["wageTax"], "soli": d["soli"], "church": d["church"], "svGross": d.get("rvGross"),
                "kv": d["kv"], "rv": d["rv"], "av": d["av"], "pv": d["pv"]}
        nomi = {"gross": ("Lordo totale", "Gesamt-Brutto"), "taxGross": ("Lordo imponibile", "Steuer-Brutto"),
                "taxFree": ("Voci esenti", "Steuerfreie Bezüge"), "wageTax": ("Imposta sul reddito", "Lohnsteuer"),
                "soli": ("Solidarietà", "Solidaritätszuschlag"), "church": ("Imposta ecclesiastica", "Kirchensteuer"),
                "svGross": ("Base contributiva", "SV-Brutto"), "kv": ("Sanitaria", "KV-Beitrag"), "rv": ("Pensionistica", "RV-Beitrag"),
                "av": ("Disoccupazione", "AV-Beitrag"), "pv": ("Non autosufficienza", "PV-Beitrag")}
        righe = [(k, v) for k, v in y.items() if k in nomi and not (v == 0 and not mese.get(k))]
        h.append('<section class="section"><h3>Da inizio anno</h3><p class="lead">Totali progressivi dal blocco Verdienstbescheinigung.</p>'
                 '<div class="tablewrap"><table><thead><tr><th>Voce</th><th>Termine tedesco</th><th class="num">Questo mese</th>'
                 '<th class="num">Da inizio anno</th></tr></thead><tbody>'
                 + "".join(f'<tr><td>{_e(nomi[k][0])}</td><td>{_e(nomi[k][1])}</td><td class="num">{_e(eur(mese.get(k)))}</td>'
                           f'<td class="num">{_e(eur(v))}</td></tr>' for k, v in righe) + "</tbody></table></div></section>")

    h.append('<section class="section"><h3>Le sigle del cedolino</h3><div class="gloss">'
             + "".join(f"<div><b>{_e(a)}</b><span>{_e(b)}</span></div>" for a, b in GLOSSARIO) + "</div></section>")
    h.append('<p class="foot">Spiegazione basata sulle cifre del cedolino e sulle aliquote 2026. Non è consulenza fiscale: '
             "per casi specifici chiedi all'ufficio paghe o a un consulente fiscale (Steuerberater).</p></div>")
    return "".join(h)
