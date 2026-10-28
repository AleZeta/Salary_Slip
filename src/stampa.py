"""Pulsante "Stampa / Salva come PDF": apre il report in una finestra pulita e lancia la stampa del browser."""

import json
from html import escape

PRINT_CSS = """
@page{size:A4;margin:12mm}
html,body{margin:0;background:#fff}
*{-webkit-print-color-adjust:exact;print-color-adjust:exact}
.ps{padding:0!important;border-radius:0!important}
.ps .item,.ps .panel .head,.ps .net,.ps .tablewrap,.ps tr{break-inside:avoid}
.ps .section{break-inside:avoid-page}
"""

TESTI = {
    "it": {"btn": "🖨️ Stampa / Salva come PDF", "hint": "Si apre la finestra di stampa: scegli «Salva come PDF» come stampante.",
           "dl": "⬇️ Scarica versione stampabile (HTML)"},
    "en": {"btn": "🖨️ Print / Save as PDF", "hint": "The print dialog opens: choose “Save as PDF” as the printer.",
           "dl": "⬇️ Download printable version (HTML)"},
}


def documento_stampa(report: str, titolo: str, lang: str = "it") -> str:
    """HTML completo da stampare: report in tema chiaro, schede aperte, stampa automatica a font caricati."""
    return (f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><title>{escape(titolo)}</title>'
            f"<style>{PRINT_CSS}</style></head><body>{report}"
            "<script>document.querySelectorAll('details').forEach(function(d){d.open=true});"
            "var go=function(){setTimeout(function(){window.print()},300)};"
            "if(document.fonts&&document.fonts.ready){document.fonts.ready.then(go)}else{window.addEventListener('load',go)}</script>"
            "</body></html>")


def componente_html(report: str, titolo: str, lang: str = "it") -> str:
    """Pagina dell'iframe con il bottone; il documento da stampare è incorporato come stringa JSON."""
    t = TESTI.get(lang, TESTI["it"])
    doc = json.dumps(documento_stampa(report, titolo, lang)).replace("</", r"<\/")
    return (
        "<style>body{margin:0;font-family:system-ui,-apple-system,'Segoe UI',sans-serif}"
        "button{font:inherit;font-weight:600;padding:.55rem 1.1rem;border-radius:.5rem;border:1px solid rgba(127,127,127,.5);"
        "background:transparent;color:inherit;cursor:pointer}button:hover{border-color:#ff4b4b;color:#ff4b4b}"
        "small{display:block;margin-top:.4rem;opacity:.65;font-size:.8rem}</style>"
        f"<button id='b'>{t['btn']}</button><small>{t['hint']}</small>"
        f"<script>var DOC={doc};"
        "document.getElementById('b').addEventListener('click',function(){"
        "var w=window.open('','_blank');if(!w){alert('Popup bloccato / popup blocked');return}"
        "w.document.open();w.document.write(DOC);w.document.close()});</script>"
    )


def bottone_stampa(report_chiaro: str, titolo: str, lang: str = "it") -> None:
    """Mostra il bottone in Streamlit (+ scarico della versione stampabile come alternativa se i popup sono bloccati).

    `report_chiaro`: HTML del report generato con tema chiaro. Il contenuto è nostro e i testi dinamici sono già escapati.
    """
    import streamlit as st
    html = componente_html(report_chiaro, titolo, lang)
    if hasattr(st, "iframe"):
        st.iframe(html, height=90)
    else:  # Streamlit meno recente
        import streamlit.components.v1 as components
        components.html(html, height=90)
    st.download_button(TESTI.get(lang, TESTI["it"])["dl"], documento_stampa(report_chiaro, titolo, lang).encode("utf-8"),
                       file_name=f"{titolo}.html".replace(" ", "_"), mime="text/html", key=f"dl_{abs(hash(titolo + str(len(report_chiaro))))}")
