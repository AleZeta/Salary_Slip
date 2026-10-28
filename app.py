"""Menu dell'app Salary Slip: cedolino tedesco (da PDF) e italiano (da PDF o RAL), spiegati voce per voce."""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import streamlit as st

from src.i18n import lingua_corrente, selettore_lingua
from src.stile import applica_stile, card_menu

st.set_page_config(page_title="Menu · Salary Slip", page_icon="🧾", layout="wide")


def menu() -> None:
    lang = selettore_lingua()
    tr = lambda it, en: en if lang == "en" else it
    st.title("🧾 " + tr("Menu", "Menu"))
    st.write(tr("Capisci ogni voce della tua busta paga: lordo, tasse, contributi e netto.",
                "Understand every line of your payslip: gross pay, taxes, contributions and net pay."))
    c1, c2 = st.columns(2)
    with c1:
        st.html(card_menu("de", tr("CEDOLINO TEDESCO", "GERMAN PAYSLIP"), "Brutto/Netto-Abrechnung",
                          tr("Carica il PDF DATEV o calcola dallo stipendio lordo: spiego ogni voce e ricalcolo i contributi.",
                             "Upload the DATEV PDF or calculate from gross salary: I explain every line and recheck the contributions."),
                          ["PDF DATEV", tr("Calcolo da stipendio", "Salary calculator"), "bAV", "Wellpass"]))
        st.page_link("pages/1_Cedolino_tedesco.py", label=tr("Apri", "Open"), icon="🇩🇪")
    with c2:
        st.html(card_menu("it", tr("CEDOLINO ITALIANO", "ITALIAN PAYSLIP"), tr("Busta paga · Cedolino", "Cedolino"),
                          tr("Carica il PDF del cedolino o inserisci la RAL: INPS, IRPEF, addizionali, detrazioni, netto mensile e TFR.",
                             "Upload the payslip PDF or enter your gross salary (RAL): INPS, IRPEF, surcharges, tax credits, monthly net pay and TFR."),
                          ["PDF", tr("Calcolo da RAL", "RAL calculator"), "IRPEF", "TFR"]))
        st.page_link("pages/2_Cedolino_italiano.py", label=tr("Apri", "Open"), icon="🇮🇹")
    st.caption(tr("Il PDF viene elaborato solo nel server dell'app e non viene salvato. Non è consulenza fiscale.",
                  "The PDF is processed only on the app server and is not stored. This is not tax advice."))


def pagine():
    lang = lingua_corrente()
    return [
        st.Page(menu, title="Menu", icon="🧾", default=True, url_path="menu"),
        st.Page("pages/1_Cedolino_tedesco.py", title="Cedolino tedesco" if lang == "it" else "German payslip", icon="🇩🇪", url_path="tedesco"),
        st.Page("pages/2_Cedolino_italiano.py", title="Cedolino italiano" if lang == "it" else "Italian payslip", icon="🇮🇹", url_path="italiano"),
    ]


applica_stile()
pagina = st.navigation(pagine())
pagina.run()
