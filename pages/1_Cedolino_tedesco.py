"""Pagina cedolino tedesco: PDF DATEV o inserimento manuale, con spiegazione di ogni voce."""

import sys
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import streamlit as st

from src import de_calc, de_parser
from src.de_payslip import da_inserimento_manuale, normalizza
from src.de_render import report_html
from src.i18n import mesi, selettore_lingua
from src.stampa import bottone_stampa

lang = selettore_lingua()
tr = lambda it, en: en if lang == "en" else it


@st.cache_data(show_spinner=False)
def leggi_pdf(contenuto: bytes) -> dict:
    import io
    return de_parser.parse(de_parser.items_da_pdf(io.BytesIO(contenuto)))


def form_manuale() -> dict:
    nomi_mesi = mesi(lang)
    with st.form("manuale"):
        c = st.columns(4)
        mese = c[0].selectbox(tr("Mese", "Month"), range(1, 13), index=date.today().month - 1, format_func=lambda m: nomi_mesi[m - 1])
        anno = c[1].number_input(tr("Anno", "Year"), 2020, 2100, date.today().year, step=1)
        classe = c[2].selectbox(tr("Classe d'imposta", "Tax class"), [1, 2, 3, 4, 5, 6])
        kk = c[3].number_input(tr("Aliquota totale cassa malattia (KK %)", "Health insurer total rate (KK %)"), 14.0, 20.0, 17.5, step=0.01)
        senza_figli = st.checkbox(tr("Nessun figlio (supplemento non autosufficienza)", "No children (long-term care surcharge)"), value=True)
        st.markdown(tr("**Voci lorde**", "**Gross pay lines**"))
        c = st.columns(3)
        salary, other, free = (c[0].number_input(tr("Stipendio base lordo", "Base gross salary"), 0.0, step=10.0),
                               c[1].number_input(tr("Altre voci tassate (bonus…)", "Other taxed items (bonus…)"), 0.0, step=10.0),
                               c[2].number_input(tr("Voci esenti (rimborsi…)", "Tax-free items (reimbursements…)"), 0.0, step=10.0))
        st.markdown(tr("**Tasse e contributi (quota tua)**", "**Taxes and contributions (your share)**"))
        c = st.columns(3)
        lst, soli, kist = (c[0].number_input("Lohnsteuer", 0.0, step=1.0), c[1].number_input("Solidaritätszuschlag", 0.0, step=1.0),
                           c[2].number_input("Kirchensteuer", 0.0, step=1.0))
        c = st.columns(4)
        kv, rv, av, pv = (c[0].number_input("KV", 0.0, step=1.0), c[1].number_input("RV", 0.0, step=1.0),
                          c[2].number_input("AV", 0.0, step=1.0), c[3].number_input("PV", 0.0, step=1.0))
        c = st.columns(3)
        ded = c[0].number_input(tr("Trattenute dopo il netto (es. mensa)", "Deductions after net pay (e.g. canteen)"), 0.0, step=1.0)
        payout = c[1].number_input(tr("Importo accreditato (0 = calcola)", "Amount paid out (0 = calculate)"), 0.0, step=1.0)
        ag = c[2].number_input(tr("Contributi azienda (0 = non noto)", "Employer contributions (0 = unknown)"), 0.0, step=1.0)
        ok = st.form_submit_button(tr("Mostra la spiegazione", "Show the explanation"), type="primary")
    if ok:
        st.session_state["de_manuale"] = da_inserimento_manuale(dict(
        month=mese, year=int(anno), taxClass=classe, kvRateTotal=kk, childlessFlag=senza_figli, salary=salary, other=other,
        free=free, wageTax=lst, soli=soli, church=kist, kv=kv, rv=rv, av=av, pv=pv, ded=ded,
        payout=payout or None, agSv=ag or None))
    return st.session_state.get("de_manuale", {})


def mostra(d: dict) -> None:
    try:
        tema = st.context.theme.type
        dark = {"dark": True, "light": False}.get(tema)
    except Exception:  # versioni di Streamlit senza st.context.theme
        dark = None
    st.html(report_html(d, dark, lang))
    periodo = f" {mesi(lang)[d['month'] - 1]} {d.get('year', '')}" if d.get("month") else f" {d.get('year', '')}"
    bottone_stampa(report_html(d, False, lang), tr("Cedolino tedesco", "German payslip") + periodo, lang)


st.title(tr("🇩🇪 Cedolino tedesco", "🇩🇪 German payslip"))
tab_pdf, tab_calc, tab_man = st.tabs([tr("📄 Carica PDF", "📄 Upload PDF"), tr("🧮 Calcola da stipendio", "🧮 Calculate from salary"), tr("✍️ Inserisci a mano", "✍️ Enter by hand")])
dati = None
with tab_pdf:
    f = st.file_uploader(tr("PDF del cedolino (ottimizzato per DATEV)", "Payslip PDF (optimised for DATEV)"), type="pdf")
    st.caption(tr("Il PDF viene letto da uno script nel server dell'app e non viene salvato.", "The PDF is read by a script on the app server and is not stored."))
    if f is not None:
        try:
            r = leggi_pdf(f.getvalue())
        except Exception as e:  # PDF corrotto, protetto o non leggibile
            st.error(tr(f"Non riesco ad aprire il file ({type(e).__name__}). È un PDF valido e senza password?", f"I can't open this file ({type(e).__name__}). Is it a valid PDF without a password?"))
        else:
            if r.get("ok") and r.get("totalGross") is not None and r.get("payout") is not None:
                r["source"] = "datev"
                dati = normalizza(r)
            else:
                st.warning(tr("Non riconosco questo formato come cedolino DATEV (o il PDF è una scansione). Usa l'inserimento a mano.", "I don't recognise this as a DATEV payslip (or the PDF is a scan). Use manual entry."))
with tab_calc:
    st.write(tr("Dallo stipendio lordo annuo al netto mensile: Lohnsteuer, contributi sociali e costo per l'azienda (Steuerklasse 1, assicurazione pubblica, anno 2026).", "From annual gross salary to monthly net pay: Lohnsteuer, social security and employer cost (Steuerklasse 1, public health insurance, 2026)."))
    c = st.columns(4)
    ral = c[0].number_input(tr("Stipendio lordo annuo (€)", "Annual gross salary (€)"), 0.0, 1_000_000.0, 75_000.0, step=1_000.0)
    kk = c[1].number_input(tr("Aliquota totale cassa malattia (%)", "Health insurer total rate (%)"), 14.0, 20.0, 17.5, step=0.01,
                           help=tr("14,6% + contributo aggiuntivo della tua cassa (Zusatzbeitrag). Sul cedolino: KK %.", "14.6% + your insurer's additional contribution (Zusatzbeitrag). On the payslip: KK %."))
    figli = c[2].checkbox(tr("Ho figli", "I have children"), help=tr("Senza figli l'assicurazione non autosufficienza ha un supplemento dello 0,6%.", "Without children, long-term care insurance has a 0.6% surcharge."))
    chiesa = c[3].selectbox("Kirchensteuer", [0, 8, 9], format_func=lambda v: tr("Nessuna", "None") if v == 0 else f"{v}% (Bayern/BW)" if v == 8 else f"{v}% " + tr("(altrove)", "(elsewhere)"))
    c = st.columns(2)
    bav = c[0].number_input(tr("Pensione aziendale bAV: il tuo versamento (€/mese)", "Company pension bAV: your contribution (€/month)"), 0.0, 2_000.0, 0.0, step=10.0,
                            help=tr("Entgeltumwandlung, es. in una Direktversicherung. Esente da tasse fino all'8% e da contributi fino al 4% del tetto RV/AV.", "Entgeltumwandlung, e.g. into a Direktversicherung. Tax-free up to 8% and contribution-free up to 4% of the RV/AV ceiling."))
    dat = c[1].number_input(tr("Contributo del datore (% del tuo versamento)", "Employer contribution (% of your contribution)"), 0.0, 100.0, 15.0, step=5.0,
                            help=tr("Per legge almeno il 15% se il datore risparmia contributi sociali; molte aziende danno di più.", "At least 15% by law if the employer saves social security; many companies give more."))
    st.caption(tr("Calcolo annuale con la tariffa § 32a EStG: il Lohnsteuer mensile reale può differire di qualche euro.", "Annual calculation using the § 32a EStG tariff: the actual monthly Lohnsteuer can differ by a few euros."))
    mostra(normalizza(de_calc.calcola(ral, kk, figli, chiesa, bav_mensile=bav, bav_datore_pct=dat)))
with tab_man:
    manuale = form_manuale()
    if manuale and dati is None:
        dati = manuale
if dati:
    st.divider()
    mostra(dati)
