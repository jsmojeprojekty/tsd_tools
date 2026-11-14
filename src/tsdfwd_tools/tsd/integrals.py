"""Calki nachylen TSD od osi kola (P0): ugiecie D(0) - D(x) = calka nachylenia od 0 do x.

zrodlo: C:\\projects\\sql_tsd_fwd\\bak\\e2a2b_beta.py (dense_integral, XS_SORTED, INTSTEP), e2b2_values.py (row_curv_integrals),
e2a_autc_1b.py (autc_front: wariant T), stan c67f7fe / 2026-10-19.

Wariant P0 (glowny, metoda Jacka): nachylenia 9 czujnikow (BEZ 1,51 m) interpolowane monotoniczna funkcja sklejana
(PCHIP), calka numeryczna (trapezy) na siatce 1 mm od osi kola, BEZ wymuszania nachylenia 0 w osi. Wariant T (kontrolny):
trapezy na czujnikach przed kolem z nachyleniem 0 w osi (autc_front). Wartosci <= 0 sa mozliwe (nie logarytmowac).
Implementacja PCHIP jest zwektoryzowana po wierszach (wzory Fritscha-Carlsona jak w scipy.interpolate.PchipInterpolator)."""

from __future__ import annotations

import numpy as np

from .constants import CHANNEL_X, INTEGRAL_NAMES, INTEGRAL_TARGETS_M, INTSTEP_M, XS_SORTED

_X = np.array(XS_SORTED, dtype=float)
_CHUNK = 4000


def _edge_derivative(h0, h1, m0, m1):
    d = ((2 * h0 + h1) * m0 - h0 * m1) / (h0 + h1)
    d = np.where(np.sign(d) != np.sign(m0), 0.0, d)
    flip = (np.sign(m0) != np.sign(m1)) & (np.abs(d) > 3 * np.abs(m0))
    return np.where(flip, 3 * m0, d)


def pchip_derivatives(x, y):
    """Pochodne PCHIP w wezlach dla wielu wierszy naraz. x: (k,) rosnaco, y: (n, k) -> (n, k)."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    hk = np.diff(x)
    mk = np.diff(y, axis=1) / hk
    k = len(x)
    d = np.zeros_like(y)
    smk = np.sign(mk)
    cond = (smk[:, 1:] != smk[:, :-1]) | (mk[:, 1:] == 0) | (mk[:, :-1] == 0)
    w1 = 2 * hk[1:] + hk[:-1]
    w2 = hk[1:] + 2 * hk[:-1]
    with np.errstate(divide="ignore", invalid="ignore"):
        whmean = (w1 / mk[:, :-1] + w2 / mk[:, 1:]) / (w1 + w2)
        inner = np.where(cond, 0.0, 1.0 / whmean)
    d[:, 1:-1] = inner
    d[:, 0] = _edge_derivative(hk[0], hk[1], mk[:, 0], mk[:, 1])
    d[:, -1] = _edge_derivative(hk[-1], hk[-2], mk[:, -1], mk[:, -2])
    return d


def pchip_eval(x, y, d, grid):
    """Wartosci sklejanej szescienna Hermite'a na siatce `grid` (G,) dla wielu wierszy: zwraca (n, G)."""
    x = np.asarray(x, float)
    idx = np.clip(np.searchsorted(x, grid, side="right") - 1, 0, len(x) - 2)
    h = (x[idx + 1] - x[idx])
    t = (grid - x[idx]) / h
    t2, t3 = t * t, t * t * t
    h00 = 2 * t3 - 3 * t2 + 1
    h10 = t3 - 2 * t2 + t
    h01 = -2 * t3 + 3 * t2
    h11 = t3 - t2
    y0, y1 = y[:, idx], y[:, idx + 1]
    d0, d1 = d[:, idx], d[:, idx + 1]
    return h00 * y0 + h10 * h * d0 + h01 * y1 + h11 * h * d1


def _grid(x1: float, step: float) -> np.ndarray:
    """Siatka jak w zrodle (dense_integral): np.arange(0, x1 + step/2, step), z dopisanym x1, gdy brak."""
    grid = np.arange(0.0, x1 + step / 2, step)
    if grid[-1] < x1:
        grid = np.append(grid, x1)
    return grid


def p0_integrals(slopes, targets=INTEGRAL_TARGETS_M, step_m: float = INTSTEP_M) -> dict:
    """Calki nachylen od 0 do x (x w `targets` [m]) dla wierszy. slopes: (n, 9) w kolejnosci CHANNELS_9 [um/m].
    Zwraca {nazwa: (n,) [um]} (np. 'a031'); NaN, gdy jakikolwiek z 9 kanalow jest nieskonczony. Dodatkowo a0361 = a061 - a031
    i a6191 = a091 - a061 (gdy sa oba punkty)."""
    s = np.asarray(slopes, float)
    if s.ndim != 2 or s.shape[1] != len(_X):
        raise ValueError(f"oczekiwano macierzy (n, {len(_X)}) nachylen, otrzymano {s.shape}")
    n = s.shape[0]
    out = {INTEGRAL_NAMES.get(round(t, 2), f"a{int(round(t * 1000)):03d}"): np.full(n, np.nan) for t in targets}
    finite = np.isfinite(s).all(axis=1)
    idx = np.nonzero(finite)[0]
    grids = {t: _grid(t, step_m) for t in targets}
    for start in range(0, len(idx), _CHUNK):
        rows = idx[start:start + _CHUNK]
        y = s[rows]
        d = pchip_derivatives(_X, y)
        for t, g in grids.items():
            vals = pchip_eval(_X, y, d, g)
            out[INTEGRAL_NAMES.get(round(t, 2), f"a{int(round(t * 1000)):03d}")][rows] = np.trapezoid(vals, g, axis=1)
    if "a031" in out and "a061" in out:
        out["a0361"] = out["a061"] - out["a031"]
    if "a061" in out and "a091" in out:
        out["a6191"] = out["a091"] - out["a061"]
    return out


def trapezoid_integrals(slopes) -> dict:
    """Wariant T (kontrolny): trapezy na czujnikach przed kolem z nachyleniem 0 w osi (autc_front).
    Zwraca {'t_a031', 't_a061', 't_a091', 't_a0361', 't_a6191'}; NaN, gdy jakikolwiek kanal nieskonczony."""
    s = np.asarray(slopes, float)
    cols = {c: i for i, c in enumerate(CHANNEL_X)}
    front = {"t_a031": ("0110", "0210", "0310"), "t_a061": ("0110", "0210", "0310", "0460", "0610"),
             "t_a091": ("0110", "0210", "0310", "0460", "0610", "0910")}
    ok = np.isfinite(s).all(axis=1)
    out = {}
    for name, chans in front.items():
        xs = np.array([0.0] + [CHANNEL_X[c] for c in chans])
        ys = np.concatenate([np.zeros((s.shape[0], 1)), s[:, [cols[c] for c in chans]]], axis=1)
        val = np.trapezoid(ys, xs, axis=1)
        out[name] = np.where(ok, val, np.nan)
    out["t_a0361"] = out["t_a061"] - out["t_a031"]
    out["t_a6191"] = out["t_a091"] - out["t_a061"]
    return out
