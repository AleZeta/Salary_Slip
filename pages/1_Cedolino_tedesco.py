"""Pagina cedolino tedesco: PDF DATEV o inserimento manuale, con spiegazione di ogni voce."""

import sys
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pandas as pd
import streamlit as st

from src import de_parser
from src.de_payslip import (CLASSI, aliquota_pv, classifica_voce_lorda, classifica_voce_netto, da_inserimento_manuale,
                            normalizza, note_tetto, testo_flag, tipo_pv, verifica_contributi)

st.set_page_config(page_title="Cedolino tedesco", page_icon="🇩🇪", layout="wide")
MESI = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre",
        "novembre", "dicembre"]


def eur(v) -> str:
    return "–" if v is None else f"€ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pct(v, d=2) -> str:
    return f"{v:.{d}f}".replace(".", ",") + "%"


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
    sorgente = {"datev": "letta da PDF DATEV", "manual": "inserita a mano"}.get(d.get("source"), "")
    periodo = f"{MESI[d['month'] - 1].capitalize()} {d.get('year', '')}" if d.get("month") else str(d.get("year", ""))
    st.header(f"{periodo}  ·  :gray[{sorgente}]")
    meta = [f"**Datore di lavoro** {d['employer']}" if d.get("employer") else None,
            f"**Pagata il** {d['payDate']}" if d.get("payDate") else None,
            f"**Assunto dal** {d['startDate']}" if d.get("startDate") else None]
    st.caption("  ·  ".join(m for m in meta if m))
    if d["warnings"]:
        st.warning("Alcuni totali non tornano esattamente: controlla i valori con il cedolino.")

    lordo, tasse, sv = d["totalGross"], d["taxTotal"], d["svTotal"]
    k = st.columns(3)
    k[0].metric("Stipendio lordo (Gesamt-Brutto)", eur(lordo))
    k[1].metric("Tasse e contributi", "− " + eur(tasse + sv), help="Steuer- und SV-Abzüge")
    k[2].metric("Accreditato sul conto (Auszahlungsbetrag)", eur(d["payout"]))
    if lordo > 0:
        st.progress(min(1.0, d["payout"] / lordo), text=f"Su ogni 100 € di lordo, circa {d['payout'] / lordo * 100:.0f} € arrivano sul tuo conto.")

    sx, dx = st.columns(2)
    with sx:
        st.subheader("Lordo")
        for p in d["payments"]:
            titolo, spiega = classifica_voce_lorda(p["label"])
            with st.expander(f"{titolo} — {eur(p['amount'])}"):
                st.write(spiega)
                if (f := testo_flag(p["tax"], p["sv"])):
                    st.caption(f)
                st.caption(f"Sul cedolino: {p['code']} {p['label']}".strip())
    with dx:
        st.subheader("Tasse e contributi")
        eff = pct(d["wageTax"] / d["taxGross"] * 100, 1) if d["taxGross"] else "–"
        with st.expander(f"Imposta sul reddito (Lohnsteuer) — {eur(d['wageTax'])}"):
            st.write(f"Trattenuta ogni mese e versata al Finanzamt. Calcolata sul lordo imponibile di {eur(d['taxGross'])} "
                     f"con classe d'imposta {d.get('taxClass', '–')}. Aliquota effettiva questo mese: {eff}.")
            if d.get("taxClass") in CLASSI:
                st.caption(f"Classe {d['taxClass']}: {CLASSI[d['taxClass']]}")
            st.caption("È un acconto: con la dichiarazione dei redditi (Steuererklärung) puoi recuperarne una parte.")
        ver = verifica_contributi(d)
        for chiave, nome, de in (("kv", "Assicurazione sanitaria", "KV-Beitrag"), ("rv", "Pensione", "RV-Beitrag"),
                                 ("av", "Disoccupazione", "AV-Beitrag"), ("pv", "Non autosufficienza", "PV-Beitrag")):
            with st.expander(f"{nome} ({de}) — {eur(d[chiave])}"):
                if chiave == "pv":
                    rate = aliquota_pv(d)
                    st.write("Copre le cure in caso di non autosufficienza. "
                             + (f"Tua quota {pct(rate)}: {tipo_pv(rate, d.get('childlessFlag', False))}." if rate else ""))
                else:
                    r = ver.get(chiave)
                    st.write({"kv": "Assicurazione sanitaria pubblica: l'aliquota totale (14,6% + contributo aggiuntivo della cassa) è divisa a metà con il datore.",
                              "rv": "Pensione pubblica (Deutsche Rentenversicherung): 18,6% totale, 9,3% a te e 9,3% al datore.",
                              "av": "Finanzia l'indennità di disoccupazione: 2,6% totale, 1,3% a te."}[chiave])
                    if r:
                        st.code(f"{eur(r['base'])} × {pct(r['aliquota'], 3)} = {eur(r['atteso'])}")
                        (st.success if r["ok"] else st.error)("Il calcolo torna" if r["ok"] else f"Non torna: atteso {eur(r['atteso'])}")
        for n in note_tetto(d):
            st.info(n)
        c = st.columns(2)
        c[0].metric("Solidaritätszuschlag", eur(d["soli"]), help="Sovrattassa 5,5% sull'imposta, solo redditi alti.")
        c[1].metric("Kirchensteuer", eur(d["church"]), help="Solo per gli iscritti a una chiesa che riscuote l'imposta (8–9%).")

    st.subheader("Dal lordo al netto")
    righe = [("Lordo", lordo), ("− Tasse", -tasse), ("− Contributi", -sv), ("= Netto (Netto-Verdienst)", d["netIncome"])]
    righe += [(f"{'+' if p['amount'] >= 0 else '−'} {classifica_voce_netto(p['label'])[0]}", p["amount"]) for p in d["netItems"]]
    righe.append(("= Accreditato", d["payout"]))
    st.dataframe(pd.DataFrame([(n, eur(v)) for n, v in righe], columns=["Passaggio", "Importo"]), hide_index=True, width='stretch')
    if d["netItems"]:
        st.caption("Le voci dopo il netto (mensa, bici aziendale, anticipi) sono tolte o aggiunte dopo tasse e contributi.")

    if d.get("agSv") is not None:
        st.subheader("Costo per l'azienda")
        c = st.columns(3)
        c[0].metric("Contributi azienda (SV-AG-Anteil)", eur(d["agSv"]))
        c[1].metric("Altri oneri (Umlagen)", eur(d.get("agAdd")))
        c[2].metric("Costo totale (Gesamtkosten)", eur(d.get("agTotal")))
        st.caption("Non compaiono nel netto ma contano per pensione e prestazioni.")

    y = d.get("ytd") or {}
    if y:
        st.subheader("Da inizio anno")
        mese = {"gross": lordo, "taxGross": d["taxGross"], "taxFree": sum(p["amount"] for p in d["payments"] if p["tax"] == "F"),
                "wageTax": d["wageTax"], "soli": d["soli"], "church": d["church"], "svGross": d.get("rvGross"),
                "kv": d["kv"], "rv": d["rv"], "av": d["av"], "pv": d["pv"]}
        nomi = {"gross": "Lordo totale", "taxGross": "Lordo imponibile", "taxFree": "Voci esenti", "wageTax": "Imposta sul reddito",
                "soli": "Solidarietà", "church": "Imposta ecclesiastica", "svGross": "Base contributiva", "kv": "Sanitaria",
                "rv": "Pensionistica", "av": "Disoccupazione", "pv": "Non autosufficienza"}
        st.dataframe(pd.DataFrame([(nomi[k], eur(mese.get(k)), eur(v)) for k, v in y.items() if k in nomi],
                                  columns=["Voce", "Questo mese", "Da inizio anno"]), hide_index=True, width='stretch')

    with st.expander("Le sigle del cedolino"):
        st.markdown("- **St / SV: L** regolare · **F** esente · **S / E** una tantum\n- **GB: J** fa parte del lordo totale\n"
                    "- **Z** supplemento senza figli (non autosufficienza)\n- **KK %** aliquota totale della cassa malattia\n"
                    "- **PGRS 101 / BGRS 1111** dipendente regolare, contributi a tutte e quattro le assicurazioni\n"
                    "- **§ 108 GewO** prospetto paga obbligatorio: conservalo")
    st.caption("Spiegazione basata sulle cifre del cedolino e sulle aliquote 2026. Non è consulenza fiscale.")


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
