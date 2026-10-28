"""Pagina cedolino italiano: da RAL a netto mensile con spiegazione di ogni voce."""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pandas as pd
import streamlit as st

from src.it_payslip import calcola

st.set_page_config(page_title="Cedolino italiano", page_icon="🇮🇹", layout="wide")


def eur(v) -> str:
    return f"€ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


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

k = st.columns(4)
k[0].metric("Lordo mensile", eur(r.lordo_mensile))
k[1].metric("Netto mensile", eur(r.netto_mensile))
k[2].metric("Netto annuo", eur(r.netto))
k[3].metric("TFR annuo accantonato", eur(r.tfr), help="RAL / 13,5; resta in azienda o va al fondo pensione.")
if ral > 0:
    st.progress(min(1.0, r.netto / ral), text=f"Su ogni 100 € di RAL, circa {r.netto / ral * 100:.0f} € arrivano sul tuo conto.")
if netto_cedolino:
    diff = netto_cedolino - r.netto_mensile
    (st.success if abs(diff) < 15 else st.warning)(
        f"Il tuo cedolino: {eur(netto_cedolino)}. Differenza dal calcolo: {eur(diff)}. "
        "Piccole differenze sono normali (ritenute mensili progressive, conguaglio, giorni lavorati, familiari a carico).")

st.subheader("Dalla RAL al netto")
righe = [("RAL", r.ral), ("− Contributi INPS (9,19%)", -r.inps), ("= Imponibile IRPEF", r.imponibile),
         ("− IRPEF lorda", -r.irpef_lorda), ("+ Detrazione lavoro dipendente", r.detrazione_lavoro)]
if r.detrazione_cuneo:
    righe.append(("+ Detrazione aggiuntiva (cuneo fiscale)", r.detrazione_cuneo))
righe += [("− Addizionale regionale", -r.add_regionale), ("− Addizionale comunale", -r.add_comunale)]
if r.bonus_cuneo:
    righe.append(("+ Bonus cuneo fiscale in busta", r.bonus_cuneo))
if extra:
    righe.append(("− Trattenute dopo il netto", -r.extra_ded))
righe.append(("= Netto annuo", r.netto))
st.dataframe(pd.DataFrame([(n, eur(v), eur(v / mens)) for n, v in righe], columns=["Passaggio", "Annuo", "Mensile"]),
             hide_index=True, width='stretch')
for n in r.note:
    st.info(n)

c1, c2 = st.columns(2)
with c1:
    with st.expander("Contributi INPS (IVS)", expanded=True):
        st.write(f"Quota a carico del dipendente: 9,19% della RAL = **{eur(r.inps)}** all'anno. Finanzia la pensione. "
                 "L'azienda ne versa circa il triplo a parte, senza che compaia nel netto.")
    with st.expander("IRPEF a scaglioni", expanded=True):
        st.dataframe(pd.DataFrame([
            (f"{eur(s['da'])} – {'oltre' if s['a'] == float('inf') else eur(s['a'])}", f"{s['aliquota'] * 100:.0f}%", eur(s["base"]), eur(s["imposta"]))
            for s in r.scaglioni], columns=["Scaglione", "Aliquota", "Base", "Imposta"]), hide_index=True, width='stretch')
        st.caption(f"Imposta lorda {eur(r.irpef_lorda)} − detrazioni {eur(r.detrazione_lavoro + r.detrazione_cuneo)} = IRPEF netta {eur(r.irpef_netta)}. "
                   f"Aliquota effettiva sull'imponibile: {r.irpef_netta / r.imponibile * 100 if r.imponibile else 0:.1f}%.")
with c2:
    with st.expander("Detrazioni", expanded=True):
        st.write(f"La detrazione per lavoro dipendente (art. 13 TUIR) ti riduce l'imposta di **{eur(r.detrazione_lavoro)}**: "
                 "è massima sotto 15.000 € e si azzera a 50.000 €.")
        if r.detrazione_cuneo:
            st.write(f"Il taglio del cuneo fiscale aggiunge una detrazione di **{eur(r.detrazione_cuneo)}** (redditi 20.000–40.000 €).")
        if r.bonus_cuneo:
            st.write(f"Sotto i 20.000 € di reddito ricevi un bonus in busta di **{eur(r.bonus_cuneo)}** all'anno.")
    with st.expander("Addizionali regionale e comunale", expanded=True):
        st.write(f"Regionale {reg:.2f}% = **{eur(r.add_regionale)}**, comunale {com:.2f}% = **{eur(r.add_comunale)}** "
                 "sull'imponibile IRPEF. Le aliquote dipendono da regione e comune di residenza.")
    with st.expander("Tredicesima, quattordicesima e TFR"):
        st.write("La RAL è divisa in 12, 13 o 14 mensilità: tredicesima e quattordicesima sono tassate come il resto. "
                 f"Il TFR (circa {eur(r.tfr)} all'anno) non è nel netto mensile: lo ricevi a fine rapporto o va al fondo pensione.")

st.caption("Calcolo annuale semplificato: anno intero, nessun familiare a carico, solo reddito da lavoro dipendente. "
           "Non sostituisce il cedolino né una consulenza fiscale.")
