"""Pagina cedolino italiano: PDF del cedolino spiegato voce per voce, oppure calcolo da RAL a netto."""

import io
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import streamlit as st

from src import de_parser, it_cedolino, it_parser
from src.it_payslip import calcola
from src.it_render import report_html


def tema_scuro():
    """True/False secondo il tema di Streamlit, None se non disponibile (allora segue il sistema)."""
    try:
        return {"dark": True, "light": False}.get(st.context.theme.type)
    except Exception:  # versioni di Streamlit senza st.context.theme
        return None


@st.cache_data(show_spinner=False)
def leggi_pdf(contenuto: bytes) -> dict:
    return it_parser.parse(de_parser.items_da_pdf(io.BytesIO(contenuto)))


st.title("🇮🇹 Cedolino italiano")
tab_pdf, tab_ral = st.tabs(["📄 Carica PDF", "🧮 Calcola da RAL"])

with tab_pdf:
    f = st.file_uploader("PDF del cedolino", type="pdf", key="it_pdf")
    st.caption("Il PDF viene letto da uno script nel server dell'app e non viene salvato. Nome, codice fiscale e IBAN non vengono estratti.")
    if f is not None:
        try:
            d = leggi_pdf(f.getvalue())
        except Exception as e:  # PDF corrotto, protetto o non leggibile
            st.error(f"Non riesco ad aprire il file ({type(e).__name__}). È un PDF valido e senza password?")
        else:
            if d.get("ok") and d.get("totalComp") is not None and d.get("netto") is not None:
                st.html(it_cedolino.report_html(d, tema_scuro()))
            else:
                st.warning("Non riconosco questo formato di cedolino (o il PDF è una scansione). Prova il calcolo da RAL.")

with tab_ral:
    st.write("Dalla RAL al netto: contributi INPS, IRPEF a scaglioni, detrazioni, addizionali e TFR (anno 2026).")
    c = st.columns(3)
    ral = c[0].number_input("RAL (lordo annuo, €)", 0.0, 1_000_000.0, 40_000.0, step=500.0)
    mens = c[1].selectbox("Mensilità", [12, 13, 14], index=1, help="13 = con tredicesima, 14 = anche quattordicesima")
    extra = c[2].number_input("Trattenute dopo il netto (€/mese)", 0.0, step=5.0, help="Fondo sanitario, sindacato, ecc.")
    c = st.columns(3)
    reg = c[0].number_input("Addizionale regionale (%)", 0.0, 3.5, 1.73, step=0.01, help="Varia per regione e scaglione")
    com = c[1].number_input("Addizionale comunale (%)", 0.0, 0.9, 0.8, step=0.01)
    netto_cedolino = c[2].number_input("Netto mensile sul tuo cedolino (facoltativo)", 0.0, step=10.0)
    r = calcola(ral, mens, reg, com, extra_ded_annue=extra * mens)
    st.html(report_html(r, reg, com, netto_cedolino or None, tema_scuro()))
