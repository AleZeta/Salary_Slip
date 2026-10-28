"""Pagina cedolino tedesco: PDF DATEV o inserimento manuale, con spiegazione di ogni voce."""

import sys
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import streamlit as st

from src import de_parser
from src.de_payslip import da_inserimento_manuale, normalizza
from src.de_render import report_html

MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre",
        "novembre", "dicembre"]


@st.cache_data(show_spinner=False)
def leggi_pdf(contenuto: bytes) -> dict:
    import io
    return de_parser.parse(de_parser.items_da_pdf(io.BytesIO(contenuto)))


def form_manuale() -> dict:
    with st.form("manuale"):
        c = st.columns(4)
        mese = c[0].selectbox("Mese", range(1, 13), index=date.today().month - 1, format_func=lambda m: MESI[m - 1])
        anno = c[1].number_input("Anno", 2020, 2100, date.today().year, step=1)
        classe = c[2].selectbox("Classe d'imposta", [1, 2, 3, 4, 5, 6])
        kk = c[3].number_input("Aliquota totale cassa malattia (KK %)", 14.0, 20.0, 17.5, step=0.01)
        senza_figli = st.checkbox("Nessun figlio (supplemento non autosufficienza)", value=True)
        st.markdown("**Voci lorde**")
        c = st.columns(3)
        salary, other, free = (c[0].number_input("Stipendio base lordo", 0.0, step=10.0),
                               c[1].number_input("Altre voci tassate (bonus…)", 0.0, step=10.0),
                               c[2].number_input("Voci esenti (rimborsi…)", 0.0, step=10.0))
        st.markdown("**Tasse e contributi (quota tua)**")
        c = st.columns(3)
        lst, soli, kist = (c[0].number_input("Lohnsteuer", 0.0, step=1.0), c[1].number_input("Solidaritätszuschlag", 0.0, step=1.0),
                           c[2].number_input("Kirchensteuer", 0.0, step=1.0))
        c = st.columns(4)
        kv, rv, av, pv = (c[0].number_input("KV", 0.0, step=1.0), c[1].number_input("RV", 0.0, step=1.0),
                          c[2].number_input("AV", 0.0, step=1.0), c[3].number_input("PV", 0.0, step=1.0))
        c = st.columns(3)
        ded = c[0].number_input("Trattenute dopo il netto (es. mensa)", 0.0, step=1.0)
        payout = c[1].number_input("Importo accreditato (0 = calcola)", 0.0, step=1.0)
        ag = c[2].number_input("Contributi azienda (0 = non noto)", 0.0, step=1.0)
        ok = st.form_submit_button("Mostra la spiegazione", type="primary")
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
    st.html(report_html(d, dark))


st.title("🇩🇪 Cedolino tedesco")
tab_pdf, tab_man = st.tabs(["📄 Carica PDF", "✍️ Inserisci a mano"])
dati = None
with tab_pdf:
    f = st.file_uploader("PDF del cedolino (ottimizzato per DATEV)", type="pdf")
    st.caption("Il PDF viene letto da uno script nel server dell'app e non viene salvato.")
    if f is not None:
        try:
            r = leggi_pdf(f.getvalue())
        except Exception as e:  # PDF corrotto, protetto o non leggibile
            st.error(f"Non riesco ad aprire il file ({type(e).__name__}). È un PDF valido e senza password?")
        else:
            if r.get("ok") and r.get("totalGross") is not None and r.get("payout") is not None:
                r["source"] = "datev"
                dati = normalizza(r)
            else:
                st.warning("Non riconosco questo formato come cedolino DATEV (o il PDF è una scansione). Usa l'inserimento a mano.")
with tab_man:
    manuale = form_manuale()
    if manuale and dati is None:
        dati = manuale
if dati:
    st.divider()
    mostra(dati)
