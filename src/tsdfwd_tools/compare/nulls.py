"""Kontrola zerowa (pary zerowe): te same miary dla par przesunietych o +-200 m i z permutacja stacji, oraz
roznica prawda - zero z wspolnym losowaniem sesji (bootstrap sparowany).

zrodlo: C:\\projects\\sql_tsd_fwd\\bak\\e2b2b_extra.py (paired_bootstrap_null), e2b2_agreement.py (build_null_test),
stan c67f7fe / 2026-10-21. Generowanie par zerowych z geometrii (e2b1_pairs.build_null_pairs, seed 20261017) wymaga
trybu `geometry` (E2b) — w trybie `pairs` pary zerowe sa wejsciem (plik z wartosciami TSD dla par zerowych).

Uwaga (Q-N4-1): r w obrebie sesji dla par zerowych zalezy od definicji okna; wartosci z P071 (lustro) i z przeliczenia na
e2b2_null_values rozchodza sie — patrz DZIENNIK."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import pearsonr

from .agreement import ccc_from_logs, within_session_corr


def align_null(pairs: pd.DataFrame, null_df: pd.DataFrame, null_type: str, type_col: str = "null_type",
               tsd_col: str = "d0_w5", valid_col: str | None = "d0_valid_w5", id_col: str = "pair_id") -> pd.Series:
    """Wartosc TSD pary zerowej danego typu dla kazdej pary (NaN gdy brak lub niewazna)."""
    sub = null_df[null_df[type_col] == null_type]
    vals = pd.to_numeric(sub[tsd_col], errors="coerce")
    if valid_col and valid_col in sub:
        vals = vals.where(pd.to_numeric(sub[valid_col], errors="coerce") >= 1)
    mapping = pd.Series(vals.to_numpy(float), index=sub[id_col].to_numpy())
    mapping = mapping[~mapping.index.duplicated(keep="first")]
    return pd.Series(pairs[id_col].map(mapping).to_numpy(float), index=pairs.index)


def paired_bootstrap_null(fwd, tsd_true, tsd_null, session_ids, n_boot: int, seed: int) -> dict:
    """Bootstrap blokowy po sesjach: WSPOLNE losowanie sesji dla pary prawdziwej i zerowej; roznica (prawda - zero)
    r Pearsona i CCC liczona w kazdej probie (skladanie CI skladowych ignorowalo kowariancje)."""
    fwd = np.asarray(fwd, float)
    tsd_true = np.asarray(tsd_true, float)
    tsd_null = np.asarray(tsd_null, float)
    session_ids = np.asarray(session_ids)
    ok = (np.isfinite(fwd) & np.isfinite(tsd_true) & np.isfinite(tsd_null) & (fwd > 0) & (tsd_true > 0) & (tsd_null > 0))
    fwd, tsd_true, tsd_null, sess = fwd[ok], tsd_true[ok], tsd_null[ok], session_ids[ok]
    lf, lt_t, lt_n = np.log(fwd), np.log(tsd_true), np.log(tsd_null)
    r_true = float(pearsonr(lf, lt_t)[0])
    r_null = float(pearsonr(lf, lt_n)[0])
    ccc_true, ccc_null = ccc_from_logs(lf, lt_t), ccc_from_logs(lf, lt_n)
    uniq = np.unique(sess)
    idx_by_sess = {s: np.nonzero(sess == s)[0] for s in uniq}
    rng = np.random.default_rng(seed)
    d_r, d_c = [], []
    for _ in range(n_boot):
        chosen = rng.choice(uniq, size=len(uniq), replace=True)
        idx = np.concatenate([idx_by_sess[s] for s in chosen])
        try:
            d_r.append(float(pearsonr(lf[idx], lt_t[idx])[0]) - float(pearsonr(lf[idx], lt_n[idx])[0]))
            d_c.append(ccc_from_logs(lf[idx], lt_t[idx]) - ccc_from_logs(lf[idx], lt_n[idx]))
        except Exception:
            continue
    d_r, d_c = np.array(d_r, float), np.array(d_c, float)
    ws_true = within_session_corr(fwd, tsd_true, sess)[0]
    ws_null = within_session_corr(fwd, tsd_null, sess)[0]
    return {
        "n": int(len(fwd)), "n_sessions": int(len(uniq)), "r_true": r_true, "r_null": r_null, "delta_r": r_true - r_null,
        "delta_r_lo": float(np.percentile(d_r, 2.5)), "delta_r_hi": float(np.percentile(d_r, 97.5)),
        "ccc_true": ccc_true, "ccc_null": ccc_null, "delta_ccc": ccc_true - ccc_null,
        "delta_ccc_lo": float(np.percentile(d_c, 2.5)), "delta_ccc_hi": float(np.percentile(d_c, 97.5)),
        "within_session_r_true": ws_true, "within_session_r_null": ws_null,
    }
