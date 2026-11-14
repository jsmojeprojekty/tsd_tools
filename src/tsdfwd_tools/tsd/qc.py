"""Kontrole jakosci przejazdu TSD: test spojnosci GPS z zyroskopem (przesuniecie przypisania kanalow / pozycji) i poprawnosc GPS.

zrodlo: C:\\projects\\sql_tsd_fwd\\bak\\qc_gyro_gps.py (omega_from_gps, _xc, xcorr_pearson, signal_metrics, verdict),
stan c67f7fe / 2026-10-08 (wartosci domyslne skalibrowane na 424 eksportach: okno [-10, -2] wierszy, r_min = 0,5,
omega_std_min = 0,0017). Test: kurs z kolejnych pozycji GPS -> predkosc katowa omega = (dpsi/ds) * V, korelacja z kanalem
zyroskopu dla wszystkich przesuniec; werdykt OK / PRZESUNIETY / NIEROZSTRZYGNIETY / BRAK_ZYROSKOPU.
Korekta polozenia TSD -4,8 m (+-1,5 m) jest GLOBALNA (nie per plik); opoznienie zyroskop-GPS sluzy tylko QC."""

from __future__ import annotations

import numpy as np
import pandas as pd

HALF = 10
MIN_OVERLAP = 2000
OMEGA_SIGN = 1.0
JUMP_TOL_M = 0.5
OMEGA_ABS_MAX = 1.0
SMALL_OVERLAP = 0.2
WINDOW = (-10, -2)
R_MIN = 0.5
OMEGA_STD_MIN = 0.0017


def omega_from_gps(chain, lat, lon, speed, half: int = HALF):
    """omega_gps = (dpsi/ds) * V; kurs psi = azymut z roznicy centralnej +-half wierszy (rzut lokalny). Zwraca
    (omega, kappa, liczba wierszy ze skokiem GPS)."""
    chain, lat, lon, speed = (np.asarray(a, float) for a in (chain, lat, lon, speed))
    n = len(lat)
    ok = np.isfinite(lat) & np.isfinite(lon) & (np.abs(lat) > 1) & (np.abs(lon) > 1)
    lat0 = np.nanmedian(np.where(ok, lat, np.nan)) if ok.any() else 52.0
    x = np.where(ok, lon, np.nan) * 111320.0 * np.cos(np.radians(lat0))
    y = np.where(ok, lat, np.nan) * 111320.0
    bad = np.zeros(n, dtype=bool)
    if n > 1:
        step = np.hypot(np.diff(x), np.diff(y))
        dch = np.diff(chain)
        jump = ~(np.abs(step - dch) <= JUMP_TOL_M)
        for i in np.nonzero(jump)[0]:
            bad[max(0, i + 1 - half):min(n, i + half + 1)] = True
    psi = np.full(n, np.nan)
    if n > 2 * half:
        dx = x[2 * half:] - x[:-2 * half]
        dy = y[2 * half:] - y[:-2 * half]
        psi[half:n - half] = np.arctan2(dx, dy)
        psi[bad] = np.nan
    kappa = np.full(n, np.nan)
    if n > 2:
        dpsi = np.angle(np.exp(1j * (psi[2:] - psi[:-2])))
        ds = chain[2:] - chain[:-2]
        with np.errstate(invalid="ignore", divide="ignore"):
            kappa[1:-1] = np.where(ds > 0, dpsi / ds, np.nan)
    omega = OMEGA_SIGN * kappa * speed
    omega[~(np.abs(omega) <= OMEGA_ABS_MAX)] = np.nan
    return omega, kappa, int(bad.sum())


def _xc(u, v, nfft, n_u, n_v):
    c = np.fft.irfft(np.conj(np.fft.rfft(u, nfft)) * np.fft.rfft(v, nfft), nfft)
    return np.concatenate([c[nfft - (n_u - 1):], c[:n_v]]) if n_u > 1 else c[:n_v]


def xcorr_pearson(a, b):
    """Wspolczynnik Pearsona r(L) = corr(a[i], b[i+L]) dla wszystkich przesuniec (FFT). Zwraca (lags, r, n_par)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    ma, mb = np.isfinite(a), np.isfinite(b)
    a0 = np.where(ma, a - np.nanmean(a), 0.0)
    b0 = np.where(mb, b - np.nanmean(b), 0.0)
    fa, fb = ma.astype(float), mb.astype(float)
    n_a, n_b = len(a), len(b)
    nfft = 1 << (n_a + n_b - 1).bit_length()
    n = np.rint(_xc(fa, fb, nfft, n_a, n_b))
    sa = _xc(a0, fb, nfft, n_a, n_b)
    sb = _xc(fa, b0, nfft, n_a, n_b)
    saa = _xc(a0 * a0, fb, nfft, n_a, n_b)
    sbb = _xc(fa, b0 * b0, nfft, n_a, n_b)
    sab = _xc(a0, b0, nfft, n_a, n_b)
    with np.errstate(invalid="ignore", divide="ignore"):
        den = np.sqrt(np.clip(n * saa - sa * sa, 0, None) * np.clip(n * sbb - sb * sb, 0, None))
        r = np.where(den > 0, (n * sab - sa * sb) / den, np.nan)
    return np.arange(-(n_a - 1), n_b), r, n


def signal_metrics(chain, lat, lon, speed, gyro, window=WINDOW) -> dict:
    omega, _, n_jump = omega_from_gps(chain, lat, lon, speed)
    gyro = np.asarray(gyro, float)
    nv = int((np.isfinite(omega) & np.isfinite(gyro)).sum())
    out = dict(n_rows=len(gyro), n_valid=nv, n_gps_jump_rows=n_jump,
               omega_std=float(np.nanstd(omega)) if np.isfinite(omega).any() else float("nan"),
               gyro_std=float(np.nanstd(gyro)) if np.isfinite(gyro).any() else float("nan"),
               r0=float("nan"), r_main=float("nan"), lag_main=None, overlap_main=0,
               r_any=float("nan"), lag_any=None, overlap_any=0, r_win=float("nan"), lag_win=None)
    if nv < 50:
        return out
    lags, r, npairs = xcorr_pearson(omega, gyro)
    i0 = int(np.where(lags == 0)[0][0])
    out["r0"] = float(r[i0]) if np.isfinite(r[i0]) else float("nan")

    def peak(min_ov):
        rr = np.where(npairs >= min_ov, r, np.nan)
        if not np.isfinite(rr).any():
            return float("nan"), None, 0
        k = int(np.nanargmax(rr))
        return float(rr[k]), int(lags[k]), int(npairs[k])

    any_min = min(MIN_OVERLAP, max(100, nv // 2))
    main_min = max(any_min, int(SMALL_OVERLAP * nv))
    out["r_main"], out["lag_main"], out["overlap_main"] = peak(main_min)
    out["r_any"], out["lag_any"], out["overlap_any"] = peak(any_min)
    if window is not None:
        w = (lags >= window[0]) & (lags <= window[1]) & np.isfinite(r) & (npairs >= any_min)
        if w.any():
            k = int(np.nanargmax(np.where(w, r, -np.inf)))
            out.update(r_win=float(r[k]), lag_win=int(lags[k]))
    return out


def verdict(m: dict, window=WINDOW, r_min: float = R_MIN, omega_std_min: float = OMEGA_STD_MIN):
    """(werdykt, r, lag, nakladka, poziom). OK: maksimum w oknie sygnatury poprawnej i r >= r_min; PRZESUNIETY: poza oknem;
    NIEROZSTRZYGNIETY: za malo lukow lub niski r; BRAK_ZYROSKOPU: kanal zyroskopu pusty."""
    lvl1 = (m.get("r_main", float("nan")), m.get("lag_main"), m.get("overlap_main", 0), "poziom1")
    lvl2 = (m.get("r_any", float("nan")), m.get("lag_any"), m.get("overlap_any", 0), "poziom2")
    if not np.isfinite(m.get("gyro_std", float("nan"))):
        return ("BRAK_ZYROSKOPU",) + lvl2
    if lvl2[1] is None:
        return ("NIEROZSTRZYGNIETY",) + lvl2
    if not (m["omega_std"] >= omega_std_min):
        return ("NIEROZSTRZYGNIETY",) + (lvl1 if lvl1[1] is not None else lvl2)
    if lvl1[1] is not None and lvl1[0] >= r_min:
        in_win = window[0] <= lvl1[1] <= window[1]
        return ("OK" if in_win else "PRZESUNIETY",) + lvl1
    r_win = m.get("r_win")
    no_sig = r_win is None or not (r_win >= r_min)
    if lvl2[0] >= r_min and no_sig and not (window[0] <= lvl2[1] <= window[1]):
        return ("PRZESUNIETY",) + lvl2
    return ("NIEROZSTRZYGNIETY",) + (lvl1 if lvl1[1] is not None else lvl2)


def gps_gyro_qc(data: pd.DataFrame, window=WINDOW, r_min: float = R_MIN, omega_std_min: float = OMEGA_STD_MIN) -> dict:
    """Test GPS-zyroskop dla przejazdu (kolumny: chainage_m, lat, lon, speed_ms, gyro_yaw)."""
    m = signal_metrics(data["chainage_m"], data["lat"], data["lon"], data["speed_ms"], data["gyro_yaw"], window)
    v = verdict(m, window, r_min, omega_std_min)
    m.update(verdict=v[0], r_max=v[1], lag_max=v[2], overlap_max=v[3], peak_source=v[4])
    return m


def gps_valid(lat, lon) -> np.ndarray:
    """Pozycja GPS poprawna: skonczona i niezerowa."""
    lat, lon = np.asarray(lat, float), np.asarray(lon, float)
    return np.isfinite(lat) & np.isfinite(lon) & (np.abs(lat) > 1) & (np.abs(lon) > 1)
