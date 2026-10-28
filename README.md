# Salary Slip

App Streamlit (stesso approccio del FireCalculator) per capire la busta paga voce per voce.

- **🇩🇪 Cedolino tedesco** – carichi il PDF DATEV (o inserisci i valori a mano): lo script legge le voci, spiega ogni riga e ricalcola KV/RV/AV.
- **🇮🇹 Cedolino italiano** – inserisci la RAL: INPS, IRPEF a scaglioni, detrazioni, cuneo fiscale, addizionali, netto mensile, TFR.

Nessuna chiamata a Claude/API: tutto è calcolato da script locali.

## Avvio

```
pip install -r requirements.txt
streamlit run app.py
```

Deploy: Streamlit Community Cloud, main file `app.py`.

## Struttura

- `src/de_parser.py` – parser DATEV (porting di `legacy_html/datev_parser.js`, coordinate con pdfplumber)
- `src/de_payslip.py` – normalizzazione, controlli di coerenza, classificazione voci
- `src/it_payslip.py` – calcolo RAL → netto Italia
- `config/rates.py` – aliquote e tetti per anno
- `legacy_html/` – prototipo HTML originale; `HANDOFF_busta_paga.md` – note di partenza
- `tests/` – `pytest`

## Note

- Non committare PDF reali o dati personali (il parser non estrae nome, codice fiscale, IBAN).
- Il parser PDF è stato portato dal JS ma verificato solo sui valori del caso di test (non su PDF reali nel repo): provalo con un tuo cedolino.
- Da fare: altri cedolini DATEV (bonus, bAV, Kirchensteuer, Midijob), ricalcolo Lohnsteuer, aliquote 2027, lettura PDF cedolino italiano.
