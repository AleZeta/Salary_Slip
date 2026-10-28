"""Pagina cedolino italiano: PDF del cedolino spiegato voce per voce, oppure calcolo da RAL a netto."""

import io
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import streamlit as st

from src import de_parser, it_cedolino, it_parser
from src.i18n import mesi, selettore_lingua
from src.stampa import bottone_stampa
from src.it_payslip import calcola
from src.it_render import report_html

lang = selettore_lingua()
tr = lambda it, en: en if lang == "en" else it


def tema_scuro():
    """True/False secondo il tema di Streamlit, None se non disponibile (allora segue il sistema)."""
    try:
        return {"dark": True, "light": False}.get(st.context.theme.type)
    except Exception:  # versioni di Streamlit senza st.context.theme
        return None


@st.cache_data(show_spinner=False)
def leggi_pdf(contenuto: bytes) -> dict:
    return it_parser.parse(de_parser.items_da_pdf(io.BytesIO(contenuto)))


st.title(tr("🇮🇹 Cedolino italiano", "🇮🇹 Italian payslip"))
tab_pdf, tab_ral = st.tabs([tr("📄 Carica PDF", "📄 Upload PDF"), tr("🧮 Calcola da RAL", "🧮 Calculate from gross salary (RAL)")])

with tab_pdf:
    f = st.file_uploader(tr("PDF del cedolino", "Payslip PDF"), type="pdf", key="it_pdf")
    st.caption(tr("Il PDF viene letto da uno script nel server dell'app e non viene salvato. Nome, codice fiscale e IBAN non vengono estratti.",
                  "The PDF is read by a script on the app server and is not stored. Name, tax code and IBAN are not extracted."))
    if f is not None:
        try:
            d = leggi_pdf(f.getvalue())
        except Exception as e:  # PDF corrotto, protetto o non leggibile
            st.error(tr(f"Non riesco ad aprire il file ({type(e).__name__}). È un PDF valido e senza password?",
                        f"I can't open this file ({type(e).__name__}). Is it a valid PDF without a password?"))
        else:
            if d.get("ok") and d.get("totalComp") is not None and d.get("netto") is not None:
                st.html(it_cedolino.report_html(d, tema_scuro(), lang))
                periodo = f" {mesi(lang)[d['month'] - 1]} {d.get('year', '')}" if d.get("month") else ""
                bottone_stampa(it_cedolino.report_html(d, False, lang), tr("Cedolino italiano", "Italian payslip") + periodo, lang)
            else:
                st.warning(tr("Non riconosco questo formato di cedolino (o il PDF è una scansione). Prova il calcolo da RAL.",
                              "I don't recognise this payslip format (or the PDF is a scan). Try the calculation from gross salary."))

with tab_ral:
    st.write(tr("Dalla RAL al netto: contributi INPS, IRPEF a scaglioni, detrazioni, addizionali e TFR (anno 2026).",
                "From gross annual salary (RAL) to net pay: INPS contributions, progressive IRPEF, tax credits, surcharges and TFR (2026)."))
    c = st.columns(3)
    ral = c[0].number_input(tr("RAL (lordo annuo, €)", "RAL (annual gross, €)"), 0.0, 1_000_000.0, 40_000.0, step=500.0)
    mens = c[1].selectbox(tr("Mensilità", "Monthly payments"), [12, 13, 14], index=1,
                          help=tr("13 = con tredicesima, 14 = anche quattordicesima", "13 = with 13th month, 14 = also 14th month"))
    extra = c[2].number_input(tr("Trattenute dopo il netto (€/mese)", "Deductions after net pay (€/month)"), 0.0, step=5.0,
                              help=tr("Fondo sanitario, sindacato, ecc.", "Health fund, union fees, etc."))
    c = st.columns(3)
    reg = c[0].number_input(tr("Addizionale regionale (%)", "Regional surcharge (%)"), 0.0, 3.5, 1.73, step=0.01,
                            help=tr("Varia per regione e scaglione", "Varies by region and income bracket"))
    com = c[1].number_input(tr("Addizionale comunale (%)", "Municipal surcharge (%)"), 0.0, 0.9, 0.8, step=0.01)
    netto_cedolino = c[2].number_input(tr("Netto mensile sul tuo cedolino (facoltativo)", "Monthly net pay on your payslip (optional)"), 0.0, step=10.0)
    r = calcola(ral, mens, reg, com, extra_ded_annue=extra * mens)
    st.html(report_html(r, reg, com, netto_cedolino or None, tema_scuro(), lang))
    bottone_stampa(report_html(r, reg, com, netto_cedolino or None, False, lang), tr("Cedolino italiano da RAL", "Italian payslip from gross salary"), lang)
