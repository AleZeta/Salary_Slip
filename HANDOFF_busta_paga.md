# Handoff — “Busta paga spiegata” (German payslip explainer)

Independent project (NOT part of the FIRE simulator). Goal: upload a German payslip PDF → get a friendly HTML page that explains every line (gross, taxes, social security, net), with arithmetic checks. Bilingual IT/EN.

## Current state (v1, working)
- Single self-contained HTML page: `busta-paga-spiegata.html` (CSS + JS inline).
- PDF reading in the browser with **pdf.js 3.11.174** (cdnjs, UMD build). `pdf.worker.min.js` is loaded as a normal `<script>` so pdf.js runs the worker on the main thread (no Worker / CSP issues). Options: `isEvalSupported:false, disableFontFace:true`.
- **DATEV parser** (`datev_parser.js`, also inlined in the page): coordinate-based, uses text items `{str,x,y,w}` per page.
  - Prefers the German page (“Abrechnung der Brutto/Netto-Bezüge”), falls back to the English page (“Pay Advice”). Label dictionaries for both.
  - Values under a header row are matched to the label with the nearest column centre.
  - DATEV prints some columns WITHOUT the decimal comma (e.g. `50249` = 502,49; `5.81250` = 5.812,50) → numbers without a comma are read as cents.
  - Suffix `Z` on the care-insurance value = childless surcharge; trailing `-` = negative.
  - Extracts: month/year, pay date, tax class, birth (ddmmyy, not displayed), KK% total health rate (e.g. `1729101` → 17,29 + PGRS 101), BGRS, insurer, start date, employer, payment lines (code, label, flags St/SV/GB, amount), taxable gross, Lohnsteuer, KiSt, Soli, KV/RV/AV/PV bases and contributions, totals (Gesamt-Brutto, steuer-/SV-rechtliche Abzüge, Netto-Verdienst, Auszahlungsbetrag), Netto-Bezüge/-Abzüge lines, employer cost (SV-AG-Anteil, Zus. AG-Kosten, Gesamtkosten), year-to-date block (Verdienstbescheinigung).
  - Sanity checks: sum of payments = total gross; gross − tax − SV = net; net + net items = payout.
- **Fallbacks**: manual entry form; “Read with Claude” (artifact `sample` capability with page images → JSON in the same schema). In a plain website this must be replaced by a server-side API call (see below).
- **Explainer rendering**: gross panel, deductions panel (with recomputation ✓/⚠ for KV, RV, AV; PV rate detection: 2,4% childless, 1,8% with child, lower = several children, 2,3/2,9% Saxony), contribution-ceiling note when KV/RV base < taxable gross, net panel with flow chips, gross split bar, info cards (tax class, insurer, employer contributions, total cost), YTD table, glossary of codes.
- Rates assumed (2026): RV 9,3%, AV 1,3%, KV = KK%/2, PV 1,8% (+0,6% childless).

## Verified test cases (DATEV, Dcubed GmbH, Techniker Krankenkasse, tax class 1, childless)
Both German and English pages parse to the same values. All sanity checks pass.

| Field | July 2026 | Sept 2026 |
|---|---|---|
| Gehalt (L/L) | 6.250,00 | 6.250,00 |
| Fahrtkosten st-/sv-frei (F/F) | 59,85 | 59,85 |
| Gesamt-Brutto | 6.309,85 | 6.309,85 |
| Lohnsteuer | 1.162,50 | 1.162,50 |
| KV-Brutto / PV-Brutto | 5.812,50 | 5.812,50 |
| RV-/AV-Brutto | 6.250,00 | 6.250,00 |
| KV / RV / AV / PV | 502,49 / 581,25 / 81,25 / 139,50 | same |
| SV-rechtliche Abzüge | 1.304,49 | 1.304,49 |
| Netto-Verdienst | 3.842,86 | 3.842,86 |
| Netto-Abzug “Lunch” | −13,44 | — |
| Auszahlungsbetrag | 3.829,42 | 3.842,86 |
| SV-AG-Anteil / Zus. AG-Kosten / Gesamtkosten | 1.269,62 / 36,88 / 7.616,35 | same |
| YTD Gesamt-Brutto / Lohnsteuer | 9.667,18 / 1.782,34 | 22.286,88 / 4.107,34 |

Do NOT commit real payslip PDFs or personal identifiers (name, tax ID, SV number, IBAN). Create anonymised fixtures (text-item JSON with values only) for tests.

## Data schema (output of parser / AI / manual form)
```json
{"month":7,"year":2026,"payDate":"24.07.2026","employer":"…","taxClass":1,"insurer":"…","kvRateTotal":17.29,"childlessFlag":true,
 "payments":[{"code":"2000","label":"Gehalt","amount":6250,"tax":"L","sv":"L","gb":"J"}],
 "totalGross":6309.85,"taxGross":6250,"wageTax":1162.5,"church":0,"soli":0,
 "kvGross":5812.5,"rvGross":6250,"avGross":6250,"pvGross":5812.5,"kv":502.49,"rv":581.25,"av":81.25,"pv":139.5,
 "taxTotal":1162.5,"svTotal":1304.49,"netIncome":3842.86,
 "netItems":[{"code":"9016","label":"Abzug Lunch","amount":-13.44}],
 "payout":3829.42,"agSv":1269.62,"agAdd":36.88,"agTotal":7616.35,
 "ytd":{"gross":9667.18,"taxGross":9583.33,"taxFree":83.85,"wageTax":1782.34,"church":0,"soli":0,"svGross":9583.33,"kv":770.49,"rv":891.25,"av":124.58,"pv":213.9}}
```

## AI integration (for a standalone site / Streamlit)
- Use the **Claude API** server-side (Anthropic). Suggested models: **Claude Haiku 5.5** (fast, cheap; enough for structured documents) or **Claude Sonnet 5.5** (more robust on unusual layouts / scans). The API accepts PDFs directly.
- Keep the API key on the server (e.g. Streamlit `secrets`), never in client HTML.
- Prompt: ask for ONLY JSON in the schema above; no name/tax ID/SV number/IBAN. Then run the same sanity checks before rendering; show a “check against your payslip” notice for AI-read data.
- Strategy: local DATEV parser first, AI only as fallback.
- Docs: https://docs.claude.com/en/api/overview

## Next steps / TODO
1. Port to the chosen stack (static site, or a Streamlit page) keeping the parser in JS or re-implementing it in Python (e.g. `pdfplumber` gives word coordinates; same anchoring logic).
2. Test on more DATEV payslips: bonus (S/E flags), Urlaubs-/Weihnachtsgeld, Entgeltumwandlung (bAV, e.g. from Oct 2026 ~156 €/month), church tax, Soli > 0, Midijob, Saxony.
3. Handle payslips with several payment pages and corrections (N = Nachberechnung, V = Vorjahr).
4. Make rates configurable per year (2027 draft: KV/PV ceiling 6.375 €/month, RV/AV 8.850 €/month).
5. Optional: Lohnsteuer recomputation (§ 32a EStG + Vorsorgepauschale) to check wage tax too.
6. Unit tests for `num()` and the parser with anonymised fixtures.
