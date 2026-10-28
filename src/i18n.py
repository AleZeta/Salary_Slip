"""Lingua dell'interfaccia (it/en): scelta salvata in sessione e formati numerici."""

LINGUE = ("it", "en")
MESI_LINGUA = {
    "it": ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"],
    "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
}


def mesi(lang: str = "it"):
    return MESI_LINGUA.get(lang, MESI_LINGUA["it"])


def fmt_eur(v, lang: str = "it") -> str:
    """'€ 1.234,56' (it) o '€ 1,234.56' (en); negativi con '− € '."""
    if v is None:
        return "–"
    testo = f"{abs(v):,.2f}"
    if lang != "en":
        testo = testo.replace(",", "X").replace(".", ",").replace("X", ".")
    return ("− € " if v < 0 else "€ ") + testo


def fmt_pct(v: float, d: int = 2, lang: str = "it") -> str:
    testo = f"{v:.{d}f}"
    return (testo if lang == "en" else testo.replace(".", ",")) + "%"


def lingua_corrente() -> str:
    """Lingua scelta dall'utente (default italiano)."""
    import streamlit as st
    return st.session_state.get("lang", "it")


def selettore_lingua() -> str:
    """Bottoni IT / EN nella barra laterale; ritorna la lingua attiva."""
    import streamlit as st
    lang = st.session_state.setdefault("lang", "it")
    with st.sidebar:
        c1, c2 = st.columns(2)
        for col, code, label in ((c1, "it", "🇮🇹 Italiano"), (c2, "en", "🇬🇧 English")):
            if col.button(label, key=f"lang_{code}", type="primary" if lang == code else "secondary", use_container_width=True):
                st.session_state["lang"] = code
                st.rerun()
    return st.session_state["lang"]
