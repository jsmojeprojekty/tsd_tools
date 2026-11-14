"""Metody niepewnosci przy malej liczbie klastrow (sesji FWD): dziki bootstrap klastrowy (wagi Webba), CR2
(Bell-McCaffrey + stopnie swobody Satterthwaite), bootstrap klastrowy sredniej, bootstrap sparowany po sesjach.

zrodlo: C:\\projects\\sql_tsd_fwd\\bak\\e2x_uncertainty_methods.py (WEBB_WEIGHTS, _ols, cr1_se, wild_cluster_bootstrap,
wcu_dual_ci, wcr_test, cr2_interval, cr2_dual_ci, cluster_bootstrap_pairs_mean, iso_week_of),
z15_temp_correction.py (paired_session_bootstrap), stan c67f7fe / 2026-11-07. Zmiany: bez globalnego loggera i
kontroli 'ctrl_stop'. Losowanie pojedynczych rekordow jest zabronione — zawsze cale klastry."""

from __future__ import annotations

import datetime
import math

import numpy as np
from scipy import stats as sstats

WEBB_WEIGHTS = np.array([-np.sqrt(1.5), -1.0, -np.sqrt(0.5), np.sqrt(0.5), 1.0, np.sqrt(1.5)])
ALPHA_95 = 0.05
ALPHA_90 = 0.10
BOOT_SEED_PAIRED = 20261107


def _ols(X, y):
    xtx_inv = np.linalg.inv(X.T @ X)
    beta = xtx_inv @ (X.T @ y)
    return beta, y - X @ beta, xtx_inv


def _cluster_index(cluster_ids):
    uniq = np.unique(cluster_ids)
    return uniq, [np.nonzero(cluster_ids == g)[0] for g in uniq]


def cr1_se(X, resid, xtx_inv, cluster_rows, j: int) -> float:
    """CR1 (Liang-Zeger z poprawka malej proby), blad standardowy wspolczynnika j; uzywany WEWNATRZ replik bootstrapu."""
    n, p = X.shape
    g = len(cluster_rows)
    c = np.zeros(p)
    c[j] = 1.0
    cx = c @ xtx_inv
    meat = 0.0
    for rows in cluster_rows:
        s = cx @ (X[rows].T @ resid[rows])
        meat += s * s
    return float(np.sqrt((g / (g - 1.0)) * ((n - 1.0) / (n - p)) * meat))


def wild_cluster_bootstrap(X, y, cluster_ids, j: int, n_boot: int, seed: int, mode: str = "WCU",
                           ref_value: float = 0.0) -> dict:
    """Dziki bootstrap klastrowy (wagi Webba, 6 punktow). WCU: reszty modelu nieograniczonego (zwraca T*);
    WCR: model z narzuconym H0 beta_j = ref_value (zwraca p-wartosc dwustronna)."""
    rng = np.random.default_rng(seed)
    n, p = X.shape
    uniq, cluster_rows = _cluster_index(cluster_ids)
    g = len(uniq)
    row_group = np.searchsorted(uniq, cluster_ids)
    beta_hat, resid_u, xtx_inv = _ols(X, y)
    se_hat = cr1_se(X, resid_u, xtx_inv, cluster_rows, j)
    if mode == "WCU":
        fitted_base, resid_base, center = X @ beta_hat, resid_u, beta_hat[j]
    elif mode == "WCR":
        mask_other = np.ones(p, dtype=bool)
        mask_other[j] = False
        xo = X[:, mask_other]
        y_star = y - ref_value * X[:, j]
        if xo.shape[1] == 0:
            fitted_base = ref_value * X[:, j]
        else:
            beta_o, _, _ = _ols(xo, y_star)
            fitted_base = xo @ beta_o + ref_value * X[:, j]
        resid_base, center = y - fitted_base, ref_value
    else:
        raise ValueError(mode)
    w = rng.choice(WEBB_WEIGHTS, size=(g, n_boot))
    y_boot = fitted_base[:, None] + resid_base[:, None] * w[row_group, :]
    beta_boot = xtx_inv @ (X.T @ y_boot)
    resid_boot = y_boot - X @ beta_boot
    c = np.zeros(p)
    c[j] = 1.0
    cx = c @ xtx_inv
    phi_sum_sq = np.zeros(n_boot)
    for rows in cluster_rows:
        sg = cx @ (X[rows].T @ resid_boot[rows, :])
        phi_sum_sq += sg * sg
    se_boot = np.sqrt((g / (g - 1.0)) * ((n - 1.0) / (n - p)) * phi_sum_sq)
    nz = se_boot > 0
    t_star = np.full(n_boot, np.nan)
    t_star[nz] = (beta_boot[j, :][nz] - center) / se_boot[nz]
    if mode == "WCU":
        return {"beta_hat": beta_hat[j], "se_hat": se_hat, "T": t_star}
    t_obs = (beta_hat[j] - ref_value) / se_hat
    pval = float(np.mean(np.abs(t_star[~np.isnan(t_star)]) >= abs(t_obs)))
    return {"beta_hat": beta_hat[j], "se_hat": se_hat, "T_obs": t_obs, "p_value": pval}


def wcr_test(X, y, cluster_ids, j: int, n_boot: int, seed: int, ref_value: float) -> dict:
    return wild_cluster_bootstrap(X, y, cluster_ids, j, n_boot, seed, mode="WCR", ref_value=ref_value)


def wcu_dual_ci(X, y, cluster_ids, j: int, n_boot: int, seed: int):
    """WCU bootstrap-t: (punkt, lo90, hi90, lo95, hi95) z jednego ciagu replik."""
    if len(np.unique(cluster_ids)) < 2:
        return (float("nan"),) * 5
    r = wild_cluster_bootstrap(X, y, cluster_ids, j, n_boot, seed, mode="WCU")
    t = r["T"][~np.isnan(r["T"])]
    q90lo, q90hi = np.percentile(t, [5.0, 95.0])
    q95lo, q95hi = np.percentile(t, [2.5, 97.5])
    b, se = r["beta_hat"], r["se_hat"]
    return b, b - se * q90hi, b - se * q90lo, b - se * q95hi, b - se * q95lo


def _sym_sqrt_pinv(a, tol: float = 1e-10):
    w, v = np.linalg.eigh(a)
    w = np.clip(w, 0.0, None)
    thr = tol * max(w.max(), 1.0) if w.size else tol
    inv_sqrt = np.where(w > thr, 1.0 / np.sqrt(np.where(w > thr, w, 1.0)), 0.0)
    return (v * inv_sqrt) @ v.T


def cr2_interval(X, y, cluster_ids, j: int, alpha: float):
    """CR2 (Bell-McCaffrey 2002) + dof typu Satterthwaite (Imbens-Kolesar 2016). Zwraca (beta, lo, hi, se, dof)."""
    n, p = X.shape
    beta_hat, resid, xtx_inv = _ols(X, y)
    h = X @ xtx_inv @ X.T
    _, cluster_rows = _cluster_index(cluster_ids)
    c = np.zeros(p)
    c[j] = 1.0
    cx = c @ xtx_inv
    se2 = 0.0
    phi_norm2 = []
    for rows in cluster_rows:
        ag = _sym_sqrt_pinv(np.eye(len(rows)) - h[np.ix_(rows, rows)])
        phi_g = (cx @ X[rows].T) @ ag
        term = float(phi_g @ resid[rows])
        se2 += term * term
        phi_norm2.append(float(phi_g @ phi_g.T))
    se = float(np.sqrt(se2))
    phi_norm2 = np.array(phi_norm2)
    dof = float((phi_norm2.sum() ** 2) / np.sum(phi_norm2 ** 2))
    tcrit = sstats.t.ppf(1 - alpha / 2, dof)
    b = beta_hat[j]
    return b, b - tcrit * se, b + tcrit * se, se, dof


def cr2_dual_ci(X, y, cluster_ids, j: int):
    """CR2: (punkt, lo90, hi90, lo95, hi95, dof95)."""
    if len(np.unique(cluster_ids)) < 2:
        return (float("nan"),) * 6
    _, lo90, hi90, _, _ = cr2_interval(X, y, cluster_ids, j, ALPHA_90)
    point, lo95, hi95, _, dof95 = cr2_interval(X, y, cluster_ids, j, ALPHA_95)
    return point, lo90, hi90, lo95, hi95, dof95


def cluster_bootstrap_pairs_mean(values, cluster_ids, n_boot: int, seed: int, alpha: float = ALPHA_95,
                                 log_transform: bool = False):
    """Bootstrap klastrowy sredniej (klastry ze zwracaniem, przedzial percentylowy); log_transform: srednia geometryczna."""
    rng = np.random.default_rng(seed)
    v = np.log(values) if log_transform else np.asarray(values, dtype=float)
    _, cluster_rows = _cluster_index(cluster_ids)
    g = len(cluster_rows)

    def stat(idx_clusters):
        return v[np.concatenate([cluster_rows[i] for i in idx_clusters])].mean()

    point = stat(np.arange(g))
    boots = np.empty(n_boot)
    for b in range(n_boot):
        boots[b] = stat(rng.integers(0, g, size=g))
    lo, hi = np.percentile(boots, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    if log_transform:
        return float(np.exp(point)), float(np.exp(lo)), float(np.exp(hi))
    return float(point), float(lo), float(hi)


def iso_week_of(date_str) -> str:
    """'RRRR-MM-DD' -> klaster tygodniowy ISO 'RRRR-Www'."""
    d = datetime.date.fromisoformat(str(date_str)[:10])
    iy, iw, _ = d.isocalendar()
    return f"{iy}-W{iw:02d}"


def multiplier_intervals(log_ratio, clusters, n_boot: int, seed_tag: str, seed_for, h0_multiplier: float | None = 1.6,
                         methods=("session_bootstrap", "wild_cluster_webb", "cr2")) -> list:
    """Przedzialy 95 % dla mnoznika (mediana/srednia geometryczna ilorazu FWD/TSD) trzema metodami przy malej
    liczbie klastrow. Seedy: seed_for(seed_tag, 'm0lin'|'wcu'|'wcr') jak w zrodle."""
    log_ratio = np.asarray(log_ratio, float)
    clusters = np.asarray(clusters)
    X = np.ones((len(log_ratio), 1))
    n_cl = int(len(np.unique(clusters)))
    rows = []
    ref_width = float("nan")
    if "session_bootstrap" in methods:
        p0, lo0, hi0 = cluster_bootstrap_pairs_mean(np.exp(log_ratio), clusters, n_boot, seed_for(seed_tag, "m0lin"),
                                                    ALPHA_95, log_transform=True)
        ref_width = hi0 - lo0
        rows.append(dict(method="M0_session_bootstrap", n_clusters=n_cl, point=p0, lo=lo0, hi=hi0, width=ref_width,
                         width_ratio_M0=1.0, note="srednia geometryczna ilorazu"))
    if "wild_cluster_webb" in methods:
        p1, _, _, lo95, hi95 = wcu_dual_ci(X, log_ratio, clusters, 0, n_boot, seed_for(seed_tag, "wcu"))
        note = ""
        if h0_multiplier:
            wcr = wcr_test(X, log_ratio, clusters, 0, n_boot, seed_for(seed_tag, "wcr"), math.log(h0_multiplier))
            note = (f"{h0_multiplier:g} w CI95: {'TAK' if lo95 <= math.log(h0_multiplier) <= hi95 else 'NIE'}; "
                    f"WCR p={wcr['p_value']:.4f}")
        rows.append(dict(method="M1_wild_cluster_webb", n_clusters=n_cl, point=math.exp(p1), lo=math.exp(lo95),
                         hi=math.exp(hi95), width=math.exp(hi95) - math.exp(lo95),
                         width_ratio_M0=(math.exp(hi95) - math.exp(lo95)) / ref_width if ref_width == ref_width else float("nan"),
                         note=note))
    if "cr2" in methods:
        p2, _, _, lo95, hi95, dof = cr2_dual_ci(X, log_ratio, clusters, 0)
        note = f"dof={dof:.1f}"
        if h0_multiplier:
            note += f"; {h0_multiplier:g} w CI95: {'TAK' if lo95 <= math.log(h0_multiplier) <= hi95 else 'NIE'}"
        rows.append(dict(method="M2_cr2", n_clusters=n_cl, point=math.exp(p2), lo=math.exp(lo95), hi=math.exp(hi95),
                         width=math.exp(hi95) - math.exp(lo95),
                         width_ratio_M0=(math.exp(hi95) - math.exp(lo95)) / ref_width if ref_width == ref_width else float("nan"),
                         note=note))
    return rows


def paired_session_bootstrap(fwd_before, tsd_before, fwd_after, tsd_after, device_group, session_ids, n_boot: int,
                             seed: int = BOOT_SEED_PAIRED) -> dict:
    """Bootstrap sparowany po sesjach FWD (te same losowania dla 'przed' i 'po'): roznica SD log-ilorazu (po - przed),
    rozstep i SD median grup (aparat x rok). Zredukowane, gdy caly przedzial 95 % < 0."""
    fb, tb = np.asarray(fwd_before, float), np.asarray(tsd_before, float)
    fa, ta = np.asarray(fwd_after, float), np.asarray(tsd_after, float)
    ok = (np.isfinite(fb) & np.isfinite(tb) & (fb > 0) & (tb > 0) & np.isfinite(fa) & np.isfinite(ta) & (fa > 0) & (ta > 0))
    fb, tb, fa, ta = fb[ok], tb[ok], fa[ok], ta[ok]
    dg = np.asarray(device_group)[ok]
    sess = np.asarray(session_ids)[ok]
    uniq = np.unique(sess)
    idx_by_sess = {s: np.nonzero(sess == s)[0] for s in uniq}
    groups = sorted(set(dg.tolist()))
    rng = np.random.default_rng(seed)

    def sd_log(idx, f, t):
        return float(np.std(np.log(f[idx]) - np.log(t[idx]), ddof=1))

    def group_disp(idx, f, t):
        logr = np.log(f[idx]) - np.log(t[idx])
        g = dg[idx]
        meds = [np.median(logr[g == gr]) for gr in groups if (g == gr).sum() >= 3]
        if len(meds) < 2:
            return float("nan"), float("nan")
        meds = np.array(meds, float)
        return float(meds.max() - meds.min()), float(np.std(meds, ddof=1))

    d_sd, d_range, d_sdg = [], [], []
    for _ in range(n_boot):
        chosen = rng.choice(uniq, size=len(uniq), replace=True)
        idx = np.concatenate([idx_by_sess[s] for s in chosen])
        d_sd.append(sd_log(idx, fa, ta) - sd_log(idx, fb, tb))
        r_a, s_a = group_disp(idx, fa, ta)
        r_b, s_b = group_disp(idx, fb, tb)
        d_range.append(r_a - r_b)
        d_sdg.append(s_a - s_b)

    def ci(v):
        v = np.array(v, float)
        v = v[np.isfinite(v)]
        return (float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))) if len(v) >= 10 else (float("nan"), float("nan"))

    allidx = np.arange(len(fb))
    r_a, s_a = group_disp(allidx, fa, ta)
    r_b, s_b = group_disp(allidx, fb, tb)
    return {
        "q1_sd_log_diff": sd_log(allidx, fa, ta) - sd_log(allidx, fb, tb), "q1_sd_log_diff_ci": ci(d_sd),
        "q2_range_before": r_b, "q2_range_after": r_a, "q2_range_diff": r_a - r_b, "q2_range_diff_ci": ci(d_range),
        "q2_sdgroup_before": s_b, "q2_sdgroup_after": s_a, "q2_sdgroup_diff": s_a - s_b, "q2_sdgroup_diff_ci": ci(d_sdg),
    }
