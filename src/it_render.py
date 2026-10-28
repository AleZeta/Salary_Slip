"""Rendering HTML del cedolino italiano calcolato da RAL (stessa grafica del cedolino tedesco) per st.html."""

from typing import Optional

from src.de_render import CSS, _e, _item, eur, pct
from src.it_payslip import RisultatoIT


def report_html(r: RisultatoIT, reg_pct: float, com_pct: float, netto_cedolino: Optional[float] = None, dark: bool = False) -> str:
    m = r.mensilita
    mensile = lambda v: v / m
    trattenute = r.inps + r.irpef_netta + r.add_regionale + r.add_comunale + r.extra_ded - r.bonus_cuneo
    det_tot = r.detrazione_lavoro + r.detrazione_cuneo
    h = [f'<style>{CSS}</style><div class="ps{" dark" if dark else ""}">',
         f'<div class="rhead"><h2>Dalla RAL al netto<span class="src">calcolo 2026 · {m} mensilità</span></h2>'
         f'<div class="meta"><span>RAL <b>{_e(eur(r.ral))}</b></span><span>Addizionale regionale <b>{_e(pct(reg_pct))}</b></span>'
         f'<span>Addizionale comunale <b>{_e(pct(com_pct))}</b></span></div></div>']
    if netto_cedolino:
        diff = netto_cedolino - mensile(r.netto)
        ok = abs(diff) < 15
        h.append(f'<div class="notice" style="border-left-color:var({"--ok" if ok else "--warn"})">Il tuo cedolino: <b>{_e(eur(netto_cedolino))}</b>. '
                 f'Differenza dal calcolo: <b>{_e(eur(diff))}</b>. Piccole differenze sono normali (ritenute mensili progressive, '
                 "conguaglio, giorni lavorati, familiari a carico).</div>")
    for n in r.note:
        h.append(f'<div class="notice">{_e(n)}</div>')

    # --- lordo
    h.append(f'<div class="top"><section class="panel gross"><div class="head"><div class="ttl">RETRIBUZIONE LORDA</div>'
             f'<div class="sub">Lordo mensile · RAL ÷ {m}</div><div class="big">{_e(eur(mensile(r.ral)))}</div></div><div class="ofwhich">di cui</div>')
    h.append(_item("Stipendio mensile", eur(mensile(r.ral)),
                   f"<p>La tua retribuzione annua lorda (RAL) di {_e(eur(r.ral))} divisa in {m} mensilità.</p>"
                   + ("<p>Tredicesima e quattordicesima sono tassate come il resto dello stipendio, ma nel mese in cui vengono pagate "
                      "il netto appare più alto o più basso per via delle ritenute.</p>" if m > 12 else ""), de="Retribuzione ordinaria"))
    h.append(_item("TFR accantonato", eur(mensile(r.tfr)) + " / mese",
                   f"<p><i>Trattamento di fine rapporto</i>: circa una mensilità all'anno messa da parte per te ({_e(eur(r.tfr))} l'anno, "
                   "RAL ÷ 13,5). Non è nel netto: lo ricevi a fine rapporto o va a un fondo pensione.</p>", de="TFR (non in busta)"))
    h.append("</section>")

    # --- trattenute
    h.append(f'<section class="panel ded"><div class="head"><div class="ttl">TASSE E CONTRIBUTI</div>'
             f'<div class="sub">Trattenute</div><div class="big">− {_e(eur(mensile(trattenute)))}</div></div><div class="ofwhich">di cui</div>')
    scaglioni = "".join(
        f"<p><span class=\"calc\">{_e(eur(s['base']))} × {s['aliquota'] * 100:.0f}% = {_e(eur(s['imposta']))}</span></p>"
        for s in r.scaglioni if s["base"] > 0)
    h.append(_item("Imposta sul reddito", eur(mensile(r.irpef_netta)), (
        f"<p>IRPEF calcolata sull'imponibile di {_e(eur(r.imponibile))} (la RAL meno i contributi INPS, che sono deducibili). "
        "Scaglioni annui 2026: 23% fino a 28.000 €, 33% fino a 50.000 €, 43% oltre.</p>" + scaglioni +
        f"<p>Imposta lorda {_e(eur(r.irpef_lorda))} − detrazioni {_e(eur(det_tot))} "
        f"(lavoro dipendente {_e(eur(r.detrazione_lavoro))}" + (f", cuneo fiscale {_e(eur(r.detrazione_cuneo))}" if r.detrazione_cuneo else "") +
        f") = <b>{_e(eur(r.irpef_netta))}</b> l'anno.</p>"
        + (f"<p>Aliquota effettiva sull'imponibile: {_e(pct(r.irpef_netta / r.imponibile * 100, 1))}.</p>" if r.imponibile else "")),
        de="IRPEF netta"))
    h.append(_item("Contributi previdenziali", eur(mensile(r.inps)), (
        "<p>La tua quota di pensione, disoccupazione e malattia versata all'INPS. A differenza della Germania c'è un'unica aliquota "
        "e non esiste un'assicurazione sanitaria separata: la sanità è pubblica (SSN) e finanziata dalle tasse.</p>"
        f'<p><span class="calc">{_e(eur(r.ral))} × 9,19% = {_e(eur(r.inps))} l\'anno</span></p>'
        "<p>L'azienda ne versa a parte circa il triplo, senza che compaia nel tuo netto.</p>"), de="Contributi INPS (IVS)"))
    h.append('<div class="pair">'
             + _item("Addizionale regionale", eur(mensile(r.add_regionale)), (
                 f"<p>Sovrattassa regionale sull'IRPEF: {_e(pct(reg_pct))} dell'imponibile = {_e(eur(r.add_regionale))} l'anno. "
                 "Varia per regione e scaglione; di solito viene versata a rate l'anno successivo.</p>"), de="Addizionale regionale", short=True)
             + _item("Addizionale comunale", eur(mensile(r.add_comunale)), (
                 f"<p>Sovrattassa del comune di residenza: {_e(pct(com_pct))} dell'imponibile = {_e(eur(r.add_comunale))} l'anno.</p>"),
                 de="Addizionale comunale", short=True) + "</div>")
    extra_items = []
    if r.bonus_cuneo:
        extra_items.append(_item("Bonus cuneo fiscale", "+ " + eur(mensile(r.bonus_cuneo)), (
            f"<p>Sotto i 20.000 € di reddito ricevi un bonus in busta di {_e(eur(r.bonus_cuneo))} l'anno, non tassato.</p>"), de="Trattamento integrativo", short=True))
    if r.extra_ded:
        extra_items.append(_item("Trattenute dopo il netto", eur(mensile(r.extra_ded)), (
            "<p>Voci tolte dopo tasse e contributi (fondo sanitario, sindacato, mensa…).</p>"), de="Altre trattenute", short=True))
    if extra_items:
        h.append('<div class="pair">' + "".join(extra_items) + "</div>")
    h.append("</section></div>")

    # --- netto
    chips = [f"Lordo {eur(mensile(r.ral))}", f"− IRPEF {eur(mensile(r.irpef_netta))}", f"− INPS {eur(mensile(r.inps))}",
             f"− Addizionali {eur(mensile(r.add_regionale + r.add_comunale))}"]
    if r.bonus_cuneo:
        chips.append(f"+ Bonus {eur(mensile(r.bonus_cuneo))}")
    if r.extra_ded:
        chips.append(f"− Altre {eur(mensile(r.extra_ded))}")
    h.append(f'<section class="net"><div class="ttl">NETTO A PAGARE</div><div class="sub">Netto mensile</div>'
             f'<div class="big">{_e(eur(mensile(r.netto)))}</div><div class="flow">' + "".join(f"<span>{_e(c)}</span>" for c in chips) + "</div>"
             f"<p>Netto annuo {_e(eur(r.netto))} su {m} mensilità.</p></section>")

    # --- barra
    if r.ral > 0:
        segs = [(max(0.0, r.netto), "var(--net)", "Netto"), (r.irpef_netta, "var(--ded)", "IRPEF"),
                (r.inps, "var(--ded-line)", "INPS"), (r.add_regionale + r.add_comunale + r.extra_ded - r.bonus_cuneo, "var(--gross)", "Addizionali e altro")]
        segs = [s for s in segs if s[0] > 0.005]
        tot = sum(s[0] for s in segs)
        aria = ", ".join(f"{s[2]} {pct(s[0] / tot * 100, 1)}" for s in segs)
        h.append(f'<section class="section"><h3>Come si divide la RAL</h3><p class="lead">Su ogni 100 € di RAL, circa '
                 f'{round(r.netto / r.ral * 100)} € arrivano sul tuo conto.</p><div class="stack" role="img" aria-label="{_e(aria)}">'
                 + "".join(f'<div style="width:{s[0] / tot * 100:.2f}%;background:{s[1]}"></div>' for s in segs) + "</div>"
                 '<div class="legend">' + "".join(f'<span><i style="background:{s[1]}"></i>{_e(s[2])} {_e(pct(s[0] / tot * 100, 1))}</span>' for s in segs)
                 + "</div></section>")

    # --- card informative
    h.append('<div class="info">'
             + _item("Mensilità", str(m), "<p>La RAL è divisa in 12, 13 o 14 mensilità. Tredicesima e quattordicesima sono pagate in dicembre e giugno/luglio, "
                     "secondo il contratto collettivo.</p>", de="Tredicesima / quattordicesima", short=True)
             + _item("Detrazioni", eur(det_tot), "<p>Riducono l'IRPEF: la detrazione per lavoro dipendente (art. 13 TUIR) è massima sotto 15.000 € "
                     "e si azzera a 50.000 €.</p>", de="Detrazioni annue", short=True)
             + _item("TFR annuo", eur(r.tfr), "<p>RAL ÷ 13,5. Resta in azienda o va al fondo pensione.</p>", de="Trattamento di fine rapporto", cls="b", short=True)
             + _item("Netto annuo", eur(r.netto), "<p>Somma di tutte le mensilità nette dell'anno.</p>", de="Netto annuo", cls="b", short=True) + "</div>")

    # --- tabella annuale
    righe = [("RAL", "Retribuzione annua lorda", r.ral), ("Contributi INPS", "Contributi previdenziali", -r.inps),
             ("Imponibile IRPEF", "Imponibile fiscale", r.imponibile), ("IRPEF lorda", "Imposta lorda", -r.irpef_lorda),
             ("Detrazione lavoro dipendente", "Art. 13 TUIR", r.detrazione_lavoro)]
    if r.detrazione_cuneo:
        righe.append(("Detrazione aggiuntiva", "Cuneo fiscale", r.detrazione_cuneo))
    righe += [("Addizionale regionale", "Addizionale regionale", -r.add_regionale), ("Addizionale comunale", "Addizionale comunale", -r.add_comunale)]
    if r.bonus_cuneo:
        righe.append(("Bonus cuneo fiscale", "Trattamento integrativo", r.bonus_cuneo))
    if r.extra_ded:
        righe.append(("Trattenute dopo il netto", "Altre trattenute", -r.extra_ded))
    righe.append(("Netto", "Netto in busta", r.netto))
    h.append('<section class="section"><h3>Dalla RAL al netto</h3><p class="lead">Calcolo annuale e quota mensile.</p><div class="tablewrap"><table><thead><tr>'
             '<th>Passaggio</th><th>Termine</th><th class="num">Annuo</th><th class="num">Mensile</th></tr></thead><tbody>'
             + "".join(f'<tr><td>{_e(a)}</td><td>{_e(b)}</td><td class="num">{_e(eur(v))}</td><td class="num">{_e(eur(mensile(v)))}</td></tr>' for a, b, v in righe)
             + "</tbody></table></div></section>")
    h.append('<p class="foot">Calcolo annuale semplificato con le aliquote 2026: anno intero, nessun familiare a carico, solo reddito da lavoro dipendente. '
             "Non sostituisce il cedolino né una consulenza fiscale: per casi specifici rivolgiti all'ufficio paghe o a un CAF / commercialista.</p></div>")
    return "".join(h)
