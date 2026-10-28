"""Rendering HTML del cedolino italiano calcolato da RAL (stessa grafica del cedolino tedesco) per st.html."""

from typing import Optional

from src.de_render import CSS, _classe_tema, _e, _item, eur, pct
from src.it_payslip import NOTE_TESTI, RisultatoIT


def report_html(r: RisultatoIT, reg_pct: float, com_pct: float, netto_cedolino: Optional[float] = None, dark: Optional[bool] = None,
                lang: str = "it") -> str:
    tr = lambda it, en: en if lang == "en" else it
    eur_ = lambda v: eur(v, lang)
    pct_ = lambda v, d=2: pct(v, d, lang)
    anno = tr("l'anno", "per year")
    m = r.mensilita
    mensile = lambda v: v / m
    trattenute = r.inps + r.irpef_netta + r.add_regionale + r.add_comunale + r.extra_ded - r.bonus_cuneo
    det_tot = r.detrazione_lavoro + r.detrazione_cuneo
    h = [f'<style>{CSS}</style><div class="ps{_classe_tema(dark)}">',
         f'<div class="rhead"><h2>{tr("Dalla RAL al netto", "From gross salary to net pay")}'
         f'<span class="src">{tr(f"calcolo 2026 · {m} mensilità", f"2026 calculation · {m} payments per year")}</span></h2>'
         f'<div class="meta"><span>{tr("RAL", "Gross annual salary (<i>RAL</i>)")} <b>{_e(eur_(r.ral))}</b></span>'
         f'<span>{tr("Addizionale regionale", "Regional surtax")} <b>{_e(pct_(reg_pct))}</b></span>'
         f'<span>{tr("Addizionale comunale", "Municipal surtax")} <b>{_e(pct_(com_pct))}</b></span></div></div>']
    if netto_cedolino:
        diff = netto_cedolino - mensile(r.netto)
        ok = abs(diff) < 15
        h.append(f'<div class="notice" style="border-left-color:var({"--ok" if ok else "--warn"})">{tr("Il tuo cedolino", "Your payslip")}: <b>{_e(eur_(netto_cedolino))}</b>. '
                 f'{tr("Differenza dal calcolo", "Difference from the calculation")}: <b>{_e(eur_(diff))}</b>. '
                 + tr("Piccole differenze sono normali (ritenute mensili progressive, conguaglio, giorni lavorati, familiari a carico).",
                      "Small differences are normal (progressive monthly withholding, year-end adjustment, days worked, dependants).") + "</div>")
    for n in r.note:
        testo = NOTE_TESTI.get(n)
        h.append(f'<div class="notice">{_e(testo[lang] if testo and lang in testo else (testo["it"] if testo else n))}</div>')

    # --- lordo
    h.append(f'<div class="top"><section class="panel gross"><div class="head"><div class="ttl">{tr("RETRIBUZIONE LORDA", "GROSS PAY")}</div>'
             f'<div class="sub">{tr(f"Lordo mensile · RAL ÷ {m}", f"Monthly gross · annual gross ÷ {m}")}</div>'
             f'<div class="big">{_e(eur_(mensile(r.ral)))}</div></div><div class="ofwhich">{tr("di cui", "of which")}</div>')
    h.append(_item(tr("Stipendio mensile", "Monthly salary"), eur_(mensile(r.ral)),
                   tr(f"<p>La tua retribuzione annua lorda (RAL) di {_e(eur_(r.ral))} divisa in {m} mensilità.</p>",
                      f"<p>Your gross annual salary (<i>RAL</i>) of {_e(eur_(r.ral))} divided into {m} monthly payments.</p>")
                   + (tr("<p>Tredicesima e quattordicesima sono tassate come il resto dello stipendio, ma nel mese in cui vengono pagate "
                         "il netto appare più alto o più basso per via delle ritenute.</p>",
                         "<p>The 13th and 14th month salaries (<i>tredicesima</i> and <i>quattordicesima</i>) are taxed like the rest of your pay, "
                         "but in the month they are paid the net amount looks higher or lower because of the withholding.</p>") if m > 12 else ""),
                   de=tr("Retribuzione ordinaria", "Ordinary pay"), lang=lang))
    h.append(_item(tr("TFR accantonato", "Severance pay set aside (TFR)"),
                   eur_(mensile(r.tfr)) + tr(" / mese", " / month"),
                   tr(f"<p><i>Trattamento di fine rapporto</i>: circa una mensilità all'anno messa da parte per te ({_e(eur_(r.tfr))} l'anno, "
                      "RAL ÷ 13,5). Non è nel netto: lo ricevi a fine rapporto o va a un fondo pensione.</p>",
                      f"<p><i>Trattamento di fine rapporto</i> (severance pay): about one month of salary per year set aside for you ({_e(eur_(r.tfr))} a year, "
                      "gross annual salary ÷ 13.5). It is not part of your net pay: you receive it when the employment ends, or it goes to a pension fund.</p>"),
                   de=tr("TFR (non in busta)", "TFR (not in the payslip)"), lang=lang))
    h.append("</section>")

    # --- trattenute
    h.append(f'<section class="panel ded"><div class="head"><div class="ttl">{tr("TASSE E CONTRIBUTI", "TAXES AND CONTRIBUTIONS")}</div>'
             f'<div class="sub">{tr("Trattenute", "Deductions")}</div><div class="big">− {_e(eur_(mensile(trattenute)))}</div></div>'
             f'<div class="ofwhich">{tr("di cui", "of which")}</div>')
    scaglioni = "".join(
        f"<p><span class=\"calc\">{_e(eur_(s['base']))} × {s['aliquota'] * 100:.0f}% = {_e(eur_(s['imposta']))}</span></p>"
        for s in r.scaglioni if s["base"] > 0)
    h.append(_item(tr("Imposta sul reddito", "Income tax"), eur_(mensile(r.irpef_netta)), (
        tr(f"<p>IRPEF calcolata sull'imponibile di {_e(eur_(r.imponibile))} (la RAL meno i contributi INPS, che sono deducibili). "
           "Scaglioni annui 2026: 23% fino a 28.000 €, 33% fino a 50.000 €, 43% oltre.</p>",
           f"<p>Income tax (<i>IRPEF</i>) calculated on the taxable income of {_e(eur_(r.imponibile))} (gross salary minus <i>INPS</i> social security contributions, which are deductible). "
           "2026 annual brackets: 23% up to €28,000, 33% up to €50,000, 43% above.</p>") + scaglioni +
        tr(f"<p>Imposta lorda {_e(eur_(r.irpef_lorda))} − detrazioni {_e(eur_(det_tot))} "
           f"(lavoro dipendente {_e(eur_(r.detrazione_lavoro))}" + (f", cuneo fiscale {_e(eur_(r.detrazione_cuneo))}" if r.detrazione_cuneo else "") +
           f") = <b>{_e(eur_(r.irpef_netta))}</b> l'anno.</p>",
           f"<p>Gross tax {_e(eur_(r.irpef_lorda))} − tax credits {_e(eur_(det_tot))} "
           f"(employee credit {_e(eur_(r.detrazione_lavoro))}" + (f", tax wedge cut {_e(eur_(r.detrazione_cuneo))}" if r.detrazione_cuneo else "") +
           f") = <b>{_e(eur_(r.irpef_netta))}</b> per year.</p>")
        + (tr(f"<p>Aliquota effettiva sull'imponibile: {_e(pct_(r.irpef_netta / r.imponibile * 100, 1))}.</p>",
              f"<p>Effective rate on taxable income: {_e(pct_(r.irpef_netta / r.imponibile * 100, 1))}.</p>") if r.imponibile else "")),
        de="IRPEF netta" if lang == "it" else "Net IRPEF", lang=lang))
    h.append(_item(tr("Contributi previdenziali", "Social security"), eur_(mensile(r.inps)), (
        tr("<p>La tua quota di pensione, disoccupazione e malattia versata all'INPS. A differenza della Germania c'è un'unica aliquota "
           "e non esiste un'assicurazione sanitaria separata: la sanità è pubblica (SSN) e finanziata dalle tasse.</p>",
           "<p>Your share of pension, unemployment and sickness contributions paid to <i>INPS</i>. Unlike Germany there is a single rate "
           "and no separate health insurance: healthcare is public (<i>SSN</i>) and funded by taxes.</p>")
        + f'<p><span class="calc">{_e(eur_(r.ral))} × {tr("9,19", "9.19")}% = {_e(eur_(r.inps))} {anno}</span></p>'
        + tr("<p>L'azienda ne versa a parte circa il triplo, senza che compaia nel tuo netto.</p>",
             "<p>The employer pays roughly three times as much on top, which does not appear in your net pay.</p>")),
        de=tr("Contributi INPS (IVS)", "INPS contributions (IVS)"), lang=lang))
    h.append('<div class="pair">'
             + _item(tr("Addizionale regionale", "Regional surtax"), eur_(mensile(r.add_regionale)), (
                 tr(f"<p>Sovrattassa regionale sull'IRPEF: {_e(pct_(reg_pct))} dell'imponibile = {_e(eur_(r.add_regionale))} l'anno. "
                    "Varia per regione e scaglione; di solito viene versata a rate l'anno successivo.</p>",
                    f"<p>Regional surtax on IRPEF: {_e(pct_(reg_pct))} of taxable income = {_e(eur_(r.add_regionale))} per year. "
                    "It varies by region and bracket; it is usually paid in instalments the following year.</p>")),
                 de=tr("Addizionale regionale", "Regional surtax (addizionale regionale)"),
                 short=True, lang=lang)
             + _item(tr("Addizionale comunale", "Municipal surtax"), eur_(mensile(r.add_comunale)), (
                 tr(f"<p>Sovrattassa del comune di residenza: {_e(pct_(com_pct))} dell'imponibile = {_e(eur_(r.add_comunale))} l'anno.</p>",
                    f"<p>Surtax of your municipality of residence: {_e(pct_(com_pct))} of taxable income = {_e(eur_(r.add_comunale))} per year.</p>")),
                 de=tr("Addizionale comunale", "Municipal surtax (addizionale comunale)"), short=True, lang=lang) + "</div>")
    extra_items = []
    if r.bonus_cuneo:
        extra_items.append(_item(tr("Bonus cuneo fiscale", "Tax wedge bonus"), "+ " + eur_(mensile(r.bonus_cuneo)), (
            tr(f"<p>Sotto i 20.000 € di reddito ricevi un bonus in busta di {_e(eur_(r.bonus_cuneo))} l'anno, non tassato.</p>",
               f"<p>Below €20,000 of income you receive a bonus in your payslip of {_e(eur_(r.bonus_cuneo))} per year, untaxed.</p>")),
            de=tr("Trattamento integrativo", "Supplementary allowance (trattamento integrativo)"), short=True, lang=lang))
    if r.extra_ded:
        extra_items.append(_item(tr("Trattenute dopo il netto", "Deductions after net"), eur_(mensile(r.extra_ded)), (
            tr("<p>Voci tolte dopo tasse e contributi (fondo sanitario, sindacato, mensa…).</p>",
               "<p>Items taken off after taxes and contributions (health fund, union dues, canteen…).</p>")),
            de=tr("Altre trattenute", "Other deductions"), short=True, lang=lang))
    if extra_items:
        h.append('<div class="pair">' + "".join(extra_items) + "</div>")
    h.append("</section></div>")

    # --- netto
    chips = [tr(f"Lordo {eur_(mensile(r.ral))}", f"Gross {eur_(mensile(r.ral))}"),
             f"− IRPEF {eur_(mensile(r.irpef_netta))}", f"− INPS {eur_(mensile(r.inps))}",
             tr(f"− Addizionali {eur_(mensile(r.add_regionale + r.add_comunale))}", f"− Surtaxes {eur_(mensile(r.add_regionale + r.add_comunale))}")]
    if r.bonus_cuneo:
        chips.append(f"+ Bonus {eur_(mensile(r.bonus_cuneo))}")
    if r.extra_ded:
        chips.append(tr(f"− Altre {eur_(mensile(r.extra_ded))}", f"− Other {eur_(mensile(r.extra_ded))}"))
    h.append(f'<section class="net"><div class="ttl">{tr("NETTO A PAGARE", "NET PAY")}</div><div class="sub">{tr("Netto mensile", "Monthly net")}</div>'
             f'<div class="big">{_e(eur_(mensile(r.netto)))}</div><div class="flow">' + "".join(f"<span>{_e(c)}</span>" for c in chips) + "</div>"
             + tr(f"<p>Netto annuo {_e(eur_(r.netto))} su {m} mensilità.</p>", f"<p>Annual net {_e(eur_(r.netto))} over {m} payments.</p>") + "</section>")

    # --- barra
    if r.ral > 0:
        segs = [(max(0.0, r.netto), "var(--net)", tr("Netto", "Net")), (r.irpef_netta, "var(--ded)", "IRPEF"),
                (r.inps, "var(--ded-line)", "INPS"),
                (r.add_regionale + r.add_comunale + r.extra_ded - r.bonus_cuneo, "var(--gross)", tr("Addizionali e altro", "Surtaxes and other"))]
        segs = [s for s in segs if s[0] > 0.005]
        tot = sum(s[0] for s in segs)
        aria = ", ".join(f"{s[2]} {pct_(s[0] / tot * 100, 1)}" for s in segs)
        h.append(f'<section class="section"><h3>{tr("Come si divide la RAL", "How your gross salary is split")}</h3>'
                 + tr(f'<p class="lead">Su ogni 100 € di RAL, circa {round(r.netto / r.ral * 100)} € arrivano sul tuo conto.</p>',
                      f'<p class="lead">Out of every €100 of gross salary, about €{round(r.netto / r.ral * 100)} reach your bank account.</p>')
                 + f'<div class="stack" role="img" aria-label="{_e(aria)}">'
                 + "".join(f'<div style="width:{s[0] / tot * 100:.2f}%;background:{s[1]}"></div>' for s in segs) + "</div>"
                 '<div class="legend">' + "".join(f'<span><i style="background:{s[1]}"></i>{_e(s[2])} {_e(pct_(s[0] / tot * 100, 1))}</span>' for s in segs)
                 + "</div></section>")

    # --- card informative
    h.append('<div class="info">'
             + _item(tr("Mensilità", "Payments per year"), str(m),
                     tr("<p>La RAL è divisa in 12, 13 o 14 mensilità. Tredicesima e quattordicesima sono pagate in dicembre e giugno/luglio, "
                        "secondo il contratto collettivo.</p>",
                        "<p>The gross annual salary is split into 12, 13 or 14 payments. The 13th and 14th are paid in December and June/July, "
                        "depending on the collective agreement (<i>CCNL</i>).</p>"),
                     de=tr("Tredicesima / quattordicesima", "13th / 14th month salary"), short=True, lang=lang)
             + _item(tr("Detrazioni", "Tax credits"), eur_(det_tot),
                     tr("<p>Riducono l'IRPEF: la detrazione per lavoro dipendente (art. 13 TUIR) è massima sotto 15.000 € "
                        "e si azzera a 50.000 €.</p>",
                        "<p>They reduce IRPEF: the employee tax credit (art. 13 <i>TUIR</i>) is highest below €15,000 "
                        "and phases out to zero at €50,000.</p>"),
                     de=tr("Detrazioni annue", "Annual tax credits"), short=True, lang=lang)
             + _item(tr("TFR annuo", "Annual TFR"), eur_(r.tfr),
                     tr("<p>RAL ÷ 13,5. Resta in azienda o va al fondo pensione.</p>",
                        "<p>Gross annual salary ÷ 13.5. It stays with the employer or goes to the pension fund.</p>"),
                     de=tr("Trattamento di fine rapporto", "Severance pay (trattamento di fine rapporto)"), cls="b", short=True, lang=lang)
             + _item(tr("Netto annuo", "Annual net"), eur_(r.netto),
                     tr("<p>Somma di tutte le mensilità nette dell'anno.</p>", "<p>Sum of all the net monthly payments of the year.</p>"),
                     de=tr("Netto annuo", "Annual net pay"), cls="b", short=True, lang=lang) + "</div>")

    # --- tabella annuale
    righe = [(tr("RAL", "Gross annual salary (RAL)"), tr("Retribuzione annua lorda", "Retribuzione annua lorda"), r.ral),
             (tr("Contributi INPS", "INPS contributions"), tr("Contributi previdenziali", "Social security"), -r.inps),
             (tr("Imponibile IRPEF", "Taxable income (IRPEF)"), tr("Imponibile fiscale", "Taxable income"), r.imponibile),
             (tr("IRPEF lorda", "Gross IRPEF"), tr("Imposta lorda", "Gross tax"), -r.irpef_lorda),
             (tr("Detrazione lavoro dipendente", "Employee tax credit"), "Art. 13 TUIR", r.detrazione_lavoro)]
    if r.detrazione_cuneo:
        righe.append((tr("Detrazione aggiuntiva", "Additional tax credit"), tr("Cuneo fiscale", "Tax wedge cut"), r.detrazione_cuneo))
    righe += [(tr("Addizionale regionale", "Regional surtax"), tr("Addizionale regionale", "Addizionale regionale"), -r.add_regionale),
              (tr("Addizionale comunale", "Municipal surtax"), tr("Addizionale comunale", "Addizionale comunale"), -r.add_comunale)]
    if r.bonus_cuneo:
        righe.append((tr("Bonus cuneo fiscale", "Tax wedge bonus"), tr("Trattamento integrativo", "Trattamento integrativo"), r.bonus_cuneo))
    if r.extra_ded:
        righe.append((tr("Trattenute dopo il netto", "Deductions after net"), tr("Altre trattenute", "Other deductions"), -r.extra_ded))
    righe.append((tr("Netto", "Net pay"), tr("Netto in busta", "Take-home pay"), r.netto))
    h.append(f'<section class="section"><h3>{tr("Dalla RAL al netto", "From gross salary to net pay")}</h3>'
             f'<p class="lead">{tr("Calcolo annuale e quota mensile.", "Annual calculation and monthly share.")}</p><div class="tablewrap"><table><thead><tr>'
             f'<th>{tr("Passaggio", "Step")}</th><th>{tr("Termine", "Italian term")}</th><th class="num">{tr("Annuo", "Annual")}</th>'
             f'<th class="num">{tr("Mensile", "Monthly")}</th></tr></thead><tbody>'
             + "".join(f'<tr><td>{_e(a)}</td><td>{_e(b)}</td><td class="num">{_e(eur_(v))}</td><td class="num">{_e(eur_(mensile(v)))}</td></tr>' for a, b, v in righe)
             + "</tbody></table></div></section>")
    h.append('<p class="foot">' + tr(
        "Calcolo annuale semplificato con le aliquote 2026: anno intero, nessun familiare a carico, solo reddito da lavoro dipendente. "
        "Non sostituisce il cedolino né una consulenza fiscale: per casi specifici rivolgiti all'ufficio paghe o a un CAF / commercialista.",
        "Simplified annual calculation with 2026 rates: full year, no dependants, employment income only. "
        "It does not replace your payslip or tax advice: for specific cases ask your payroll office or a tax advisor (<i>CAF</i> / <i>commercialista</i>).")
        + "</p></div>")
    return "".join(h)
