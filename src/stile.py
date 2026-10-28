"""Stile globale dell'app (palette e font del report) e card del menu."""

import streamlit as st

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700;800&family=Barlow:wght@400;500;600&display=swap');
.stApp, .stApp p, .stApp label, .stApp li, .stApp input, .stApp textarea, .stApp button, .stApp [data-baseweb="select"]{font-family:"Barlow",system-ui,-apple-system,"Segoe UI",sans-serif}
.stApp h1,.stApp h2,.stApp h3,[data-testid="stHeading"] *{font-family:"Barlow Condensed","Arial Narrow",Arial,sans-serif!important;font-weight:800;letter-spacing:.01em}
.stApp h1{font-size:clamp(34px,5vw,52px)}
button[data-baseweb="tab"]{font-family:"Barlow Condensed","Arial Narrow",sans-serif;font-size:1.15rem;font-weight:700;letter-spacing:.02em}
[data-testid="stFileUploaderDropzone"]{border:2px dashed #9a63f7;border-radius:22px;background:rgba(124,53,245,.10);padding:26px}
[data-baseweb="input"],[data-baseweb="select"]>div,[data-testid="stNumberInput"] input{border-radius:12px}
.stButton button,.stDownloadButton button,[data-testid="stPageLink"] a{border-radius:999px;font-weight:600}
[data-testid="stSidebar"] .stButton button{border-radius:999px}
[data-testid="stPageLink"] a{border:1.5px solid rgba(124,53,245,.55);padding:.45rem 1.2rem}
[data-testid="stPageLink"] a:hover{background:rgba(124,53,245,.14)}
.mc{border-radius:22px;padding:16px;margin-bottom:10px}
.mc.de{background:rgba(248,171,135,.35)}.mc.it{background:rgba(124,53,245,.16)}
.mc .head{border-radius:16px;padding:16px;text-align:center;color:#fff;border:2px solid rgba(255,255,255,.7)}
.mc.de .head{background:#ff5a36}.mc.it .head{background:#7c35f5}
.mc .ttl{font-family:"Barlow Condensed","Arial Narrow",sans-serif;font-size:28px;font-weight:700;line-height:1.1}
.mc .sub{font-size:14px;opacity:.92}
.mc p{margin:.8rem .2rem .5rem;font-size:15px}
.mc .chips{display:flex;flex-wrap:wrap;gap:6px;margin:.2rem 0 .1rem}
.mc .chips span{background:rgba(127,127,127,.18);border-radius:999px;padding:2px 12px;font-size:13px}
"""


def applica_stile() -> None:
    """Inietta il CSS globale (font Barlow, riquadro di caricamento, tab, bottoni a pillola)."""
    st.html(f"<style>{CSS}</style>")


def card_menu(classe: str, titolo: str, sottotitolo: str, descrizione: str, chips: list) -> str:
    """Card del menu: stessa grafica dei pannelli del report (`classe`: 'de' arancione, 'it' viola)."""
    return (f'<div class="mc {classe}"><div class="head"><div class="ttl">{titolo}</div><div class="sub">{sottotitolo}</div></div>'
            f'<p>{descrizione}</p><div class="chips">' + "".join(f"<span>{c}</span>" for c in chips) + "</div></div>")
