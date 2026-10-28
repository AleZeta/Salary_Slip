"""Aliquote e soglie per anno (Germania e Italia). Aggiungere un anno = aggiungere una voce al dizionario."""

# Germania: contributi del dipendente (metà dell'aliquota totale) e tetti mensili
DE_RATES = {
    2026: {
        "rv": 0.093,            # pensione: 18,6% totale
        "av": 0.013,            # disoccupazione: 2,6% totale
        "pv": 0.018,            # non autosufficienza, con figli
        "pv_senza_figli": 0.006,
        "tetto_rv_av": 8_450.0,   # Beitragsbemessungsgrenze mensile RV/AV
        "tetto_kv_pv": 5_812.5,   # Beitragsbemessungsgrenze mensile KV/PV
        "bav_esente_tasse": 0.08,        # % del tetto RV/AV annuo: versamenti bAV esenti da tasse
        "bav_esente_contributi": 0.04,   # idem per i contributi sociali
    },
    2027: {  # bozza
        "rv": 0.093, "av": 0.013, "pv": 0.018, "pv_senza_figli": 0.006,
        "tetto_rv_av": 8_850.0, "tetto_kv_pv": 6_375.0, "bav_esente_tasse": 0.08, "bav_esente_contributi": 0.04,
    },
}

# Italia
IT_RATES = {
    2026: {
        "inps_dipendente": 0.0919,
        "scaglioni": [(28_000.0, 0.23), (50_000.0, 0.33), (float("inf"), 0.43)],
    },
}
