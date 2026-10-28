"""Pagina cedolino italiano: da RAL a netto mensile con spiegazione di ogni voce."""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import streamlit as st

from src.it_payslip import calcola
from src.it_render import report_html



st.title("🇮🇹 Cedolino italiano")
st.write("Dalla RAL al netto: contributi INPS, IRPEF a scaglioni, detrazioni, addizionali e TFR (anno 2026).")

with st.sidebar:
    st.header("Dati")
    ral = st.number_input("RAL (lordo annuo, €)", 0.0, 1_000_000.0, 40_000.0, step=500.0)
    mens = st.selectbox("Mensilità", [12, 13, 14], index=1, help="13 = con tredicesima, 14 = anche quattordicesima")
    reg = st.number_input("Addizionale regionale (%)", 0.0, 3.5, 1.73, step=0.01, help="Varia per regione e scaglione")
    com = st.number_input("Addizionale comunale (%)", 0.0, 0.9, 0.8, step=0.01)
    extra = st.number_input("Trattenute dopo il netto (€/mese)", 0.0, step=5.0, help="Fondo sanitario, sindacato, ecc.")
    netto_cedolino = st.number_input("Netto mensile sul tuo cedolino (facoltativo)", 0.0, step=10.0)

r = calcola(ral, mens, reg, com, extra_ded_annue=extra * mens)
try:
    tema = st.context.theme.type
    dark = {"dark": True, "light": False}.get(tema)
except Exception:  # versioni di Streamlit senza st.context.theme
    dark = None
st.html(report_html(r, reg, com, netto_cedolino or None, dark))
