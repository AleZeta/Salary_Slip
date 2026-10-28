"""Home dell'app Salary Slip: cedolino tedesco (da PDF) e italiano (da RAL), spiegati voce per voce."""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import streamlit as st

st.set_page_config(page_title="Salary Slip", page_icon="🧾", layout="wide")

st.title("🧾 Salary Slip")
st.write("Capisci ogni voce della tua busta paga: lordo, tasse, contributi e netto.")

c1, c2 = st.columns(2)
with c1:
    st.subheader("🇩🇪 Cedolino tedesco")
    st.write("Carica il PDF DATEV: lo leggo in locale con uno script, spiego ogni voce e ricalcolo i contributi.")
    st.page_link("pages/1_Cedolino_tedesco.py", label="Apri", icon="🇩🇪")
with c2:
    st.subheader("🇮🇹 Cedolino italiano")
    st.write("Inserisci la RAL: calcolo INPS, IRPEF, addizionali, detrazioni, netto mensile e TFR.")
    st.page_link("pages/2_Cedolino_italiano.py", label="Apri", icon="🇮🇹")

st.caption("Il PDF viene elaborato solo nel server dell'app e non viene salvato. Non è consulenza fiscale.")
