"""Temperatura warstwy asfaltowej: symulacja 1-D + kalibracja jednorazowa do pirometru, dla pojedynczej chwili i dla serii.

zrodlo: C:\\WORK\\DOKTORAT\\temp_model\\src\\z14b_single_shot.py oraz z14lite_validate.py (predict_block), stan 2026-11-13;
replika samodzielna z audytu E0 (RMSE 1,7488 na zbiorze H v2). Test tozsamosci: tests/regression/test_n2_reference.py.

Przeplyw dla jednej chwili t: meteo z komorki reanalizy (35 dni historii) -> ramka 10 min -> dolny BC (t50 z OLS) -> symulacja
od t_dnia - 3 d (rozbieg 288 krokow) -> korekta IR do 'masy' -> kalibracja a_sw (brentq, bramka) -> T na zadanej glebokosci.
Symulacja jest przyczynowa (niejawna w czasie), wiec jedna symulacja na (komorka, doba, a_sw) obsluguje wszystkie chwile doby."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .bells3 import bells3, prev_day_air_mean
from .calibrate import Calibration, calibrate_single_shot
from .constants import A_HI, A_LO, DEPTH_MAX_M, DZ_M, HIST_DAYS, LEAD_DAYS, SNOW_MAX_M, STEP
from .flags import LayerFlag
from .frame import at_time, bottom_t50, build_frame, delta_ir, make_index
from .meteo import MeteoError, MeteoStore, REQUIRED_COLUMNS, in_poland, last_valid_times, quantize
from .params import FrozenParams, load_params
from .solver import simulate_eb
from .uncertainty import u95_for_hour

log = logging.getLogger(__name__)

VALIDATED_DEPTHS_CM = (10, 12)
SEASON_MONTHS = (4, 5, 6, 7, 8, 9, 10)
NIGHT_SW_WM2 = 5.0


@dataclass
class QcSettings:
    season_months: tuple = SEASON_MONTHS
    snow_depth_max_m: float = SNOW_MAX_M
    night_sw_wm2: float = NIGHT_SW_WM2


@dataclass
class LayerTempResult:
    value: float                       # temperatura warstwy na zadanej glebokosci po kalibracji [C]
    value_uncal: float                 # fizyka bez kalibracji (a_sw domyslne) [C]
    u95: float
    a_sw: float
    ts_sim: float                      # temperatura powierzchni modelu w chwili pomiaru po kalibracji [C]
    ir_masa: float                     # odczyt pirometru po korekcie IR [C]
    calib_flag: str                    # ok | gate | bound_lo | bound_hi | nosim | none
    flags: int
    grid_lat: float | None = None
    grid_lon: float | None = None
    sw_ma6: float = float("nan")
    bells3: float = float("nan")
    params_hash: str = ""
    extra: dict = field(default_factory=dict)


class CellDay:
    """Ramka forsowania i symulacje dla jednej komorki reanalizy i jednej doby (wspolne dla wszystkich chwil tej doby)."""

    def __init__(self, om: pd.DataFrame, day, t_end, params: FrozenParams, *, history_days: int = HIST_DAYS,
                 lead_days: int = LEAD_DAYS):
        self.params = params
        self.om = om
        self.day = pd.Timestamp(day).normalize()
        self.index = make_index(self.day - pd.Timedelta(days=history_days), t_end)
        self.frame = build_frame(om, self.index)
        self.bottom = bottom_t50(self.frame, params)
        self.delta = delta_ir(self.frame, params).to_numpy()
        start = self.day - pd.Timedelta(days=lead_days)
        end1 = pd.Timestamp(t_end).ceil("10min") + STEP
        self.sub = self.frame.loc[start:end1]
        self.sub_b = self.bottom.loc[self.sub.index]
        self.sub_start = start
        self.last_t, self.last_sw = last_valid_times(om)
        self._pinned: dict = {}
        self.n_sims = 0
        self.pins = {round(float(a), 12) for a in (A_LO, A_HI, params.a_default)}
        self._t1d = None

    def sim(self, a: float) -> np.ndarray:
        key = round(float(a), 12)
        if key in self._pinned:
            return self._pinned[key]
        T = simulate_eb(self.sub, self.sub_b, self.params, a)
        self.n_sims += 1
        if key in self.pins:
            self._pinned[key] = T
        return T

    def value_at(self, a: float, t, node: int) -> float:
        return at_time(self.sub.index, self.sim(a)[:, node], t)

    def t1d_at(self, t) -> float:
        if self._t1d is None:
            self._t1d = prev_day_air_mean(self.frame["temperature_2m"]).to_numpy()
        return at_time(self.index, self._t1d, t)

    def raw_gap(self, t) -> bool:
        """Czy w surowych danych meteo (godzinowych) w oknie symulacji do chwili t sa braki w zmiennych wymaganych."""
        w = self.om.loc[self.sub_start - pd.Timedelta(hours=1): pd.Timestamp(t) + pd.Timedelta(hours=1)]
        if w.empty:
            return True
        cols = [c for c in REQUIRED_COLUMNS if c in w]
        return bool(w[cols].isna().any().any())


def predict_at(ctx: CellDay, t, ir: float, depth_m: float = 0.12, *, calibration: str = "single_shot_ir_mass",
               qc: QcSettings | None = None, lat: float | None = None, lon: float | None = None, grid=(None, None),
               with_bells3: bool = False) -> LayerTempResult:
    """Wynik N2 dla chwili t (lokalny czas naiwny), odczytu pirometru `ir` [C] i glebokosci `depth_m` [m]."""
    qc = qc or QcSettings()
    p = ctx.params
    t = pd.Timestamp(t)
    flags = LayerFlag.NONE
    nan = float("nan")
    depth_cm = depth_m * 100.0
    if not (0.0 <= depth_m <= DEPTH_MAX_M + 1e-9):
        flags |= LayerFlag.DEPTH_OUT_OF_RANGE
    elif not any(abs(depth_cm - d) < 1e-6 for d in VALIDATED_DEPTHS_CM):
        flags |= LayerFlag.DEPTH_NOT_VALIDATED
    if t.month not in qc.season_months:
        flags |= LayerFlag.OUT_OF_SEASON
    if lat is not None and lon is not None and not in_poland(lat, lon):
        flags |= LayerFlag.POSITION_OUT_OF_POLAND
    sw_ma6 = at_time(ctx.index, ctx.frame["sw_ma6"].to_numpy(), t)
    if np.isfinite(sw_ma6) and sw_ma6 < qc.night_sw_wm2:
        flags |= LayerFlag.NIGHT
    snow = at_time(ctx.index, ctx.frame["snow_depth"].to_numpy(), t)
    if np.isfinite(snow) and snow > qc.snow_depth_max_m:
        flags |= LayerFlag.SNOW
    limits = [x for x in (ctx.last_t, ctx.last_sw - pd.Timedelta(minutes=30)) if pd.notna(x)]
    if not limits or t > min(limits):
        flags |= LayerFlag.TAIL_EXTRAPOLATED
    if ctx.raw_gap(t):
        flags |= LayerFlag.METEO_GAP

    ir = float(ir) if ir is not None else nan
    ir_masa = ir - at_time(ctx.index, ctx.delta, t) if np.isfinite(ir) else nan
    bells = nan
    if with_bells3 and np.isfinite(ir):
        t1d = ctx.t1d_at(t)
        bells = float(bells3(ir, t1d, t.hour + t.minute / 60.0, depth_m * 1000.0)) if np.isfinite(t1d) else nan

    node = int(round(depth_m / DZ_M))
    if flags & LayerFlag.DEPTH_OUT_OF_RANGE:
        return LayerTempResult(nan, nan, nan, nan, nan, ir_masa, "none", int(flags), grid[0], grid[1], sw_ma6, bells, p.hash)

    a_def = p.a_default
    if calibration == "none" or not np.isfinite(ir_masa):
        cal = Calibration(a_def, "none", nan, nan)
        flags |= LayerFlag.CALIB_OFF if calibration == "none" else LayerFlag.IR_MISSING
    else:
        cal = calibrate_single_shot(lambda a: ctx.value_at(a, t, 0), ir_masa, a_def, bounds=p.a_bounds)
        flags |= {"gate": LayerFlag.CALIB_GATE, "bound_hi": LayerFlag.CALIB_BOUND_HI, "bound_lo": LayerFlag.CALIB_BOUND_LO,
                  "nosim": LayerFlag.CALIB_NOSIM, "ok": LayerFlag.NONE}[cal.flag]
    value_uncal = ctx.value_at(a_def, t, node)
    value = value_uncal if cal.a_sw == a_def else ctx.value_at(cal.a_sw, t, node)
    ts_sim = ctx.value_at(cal.a_sw, t, 0)
    if not np.isfinite(value):
        flags |= LayerFlag.METEO_GAP | LayerFlag.CALIB_NOSIM
    u95 = u95_for_hour(t.hour + t.minute / 60.0) if np.isfinite(value) else nan
    return LayerTempResult(value, value_uncal, u95, cal.a_sw, ts_sim, ir_masa, cal.flag, int(flags), grid[0], grid[1], sw_ma6,
                           bells, p.hash)


def layer_temperature(ts, lat: float, lon: float, ir: float, air: float | None = None, depth_m: float = 0.12, *,
                      meteo: MeteoStore, params: FrozenParams | None = None, calibration: str = "single_shot_ir_mass",
                      qc: QcSettings | None = None, with_bells3: bool = False) -> LayerTempResult:
    """Temperatura warstwy dla jednej chwili/pozycji/odczytu pirometru. `air` [C] jest przyjmowana dla zgodnosci z formatem
    pomiarow, ale NIE wchodzi do modelu (powietrze pochodzi z reanalizy)."""
    params = params or load_params()
    ts = pd.Timestamp(ts)
    om, info = meteo.get(lat, lon, ts.normalize() - pd.Timedelta(days=HIST_DAYS), ts)
    ctx = CellDay(om, ts.normalize(), ts, params)
    return predict_at(ctx, ts, ir, depth_m, calibration=calibration, qc=qc, lat=lat, lon=lon,
                      grid=(info["grid_lat"], info["grid_lon"]), with_bells3=with_bells3)


def run_survey(df: pd.DataFrame, meteo: MeteoStore, params: FrozenParams, *, depth_cm: float = 12.0,
               calibration: str = "single_shot_ir_mass", qc: QcSettings | None = None, with_bells3: bool = False,
               time_col: str = "measured_at_local", lat_col: str = "latitude", lon_col: str = "longitude",
               ir_col: str = "t_surface", grid_deg: float = 0.05, history_days: int = HIST_DAYS) -> pd.DataFrame:
    """Wynik N2 dla tabeli pomiarow (jeden wiersz = jedna chwila/pozycja/odczyt). Zwraca tabele w kolejnosci wejscia
    (kolumny: t_layer, t_layer_uncal, u95, a_sw, ts_sim, ir_masa, calib_flag, qc_flags, grid_lat, grid_lon, sw_ma6 [, bells3_c]).
    Grupuje wiersze po (komorka, doba): jedna ramka i wspolne symulacje graniczne na grupe."""
    qc = qc or QcSettings()
    ts = pd.to_datetime(df[time_col])
    q = [quantize(a, b, grid_deg) for a, b in zip(df[lat_col], df[lon_col])]
    keys = pd.DataFrame({"qlat": [x[0] for x in q], "qlon": [x[1] for x in q], "day": ts.dt.normalize()}, index=df.index)
    rows: dict = {}
    n_groups = keys.groupby(["qlat", "qlon", "day"]).ngroups
    done = 0
    for (qlat, qlon, day), idx in keys.groupby(["qlat", "qlon", "day"]).groups.items():
        sel = list(idx)
        t_max = ts.loc[sel].max()
        try:
            om, info = meteo.get(qlat, qlon, day - pd.Timedelta(days=history_days), t_max)
            ctx = CellDay(om, day, t_max, params, history_days=history_days)
            grid = (info["grid_lat"], info["grid_lon"])
        except MeteoError as exc:
            log.warning("brak meteo dla (%+.2f; %+.2f) doba %s: %s", qlat, qlon, pd.Timestamp(day).date(), exc)
            ctx, grid = None, (None, None)
        for i in sel:
            if ctx is None:
                nan = float("nan")
                rows[i] = LayerTempResult(nan, nan, nan, nan, nan, nan, "nosim",
                                          int(LayerFlag.METEO_GAP | LayerFlag.CALIB_NOSIM), None, None, nan, nan, params.hash)
                continue
            rows[i] = predict_at(ctx, ts.loc[i], df.at[i, ir_col], depth_cm / 100.0, calibration=calibration, qc=qc,
                                 lat=df.at[i, lat_col], lon=df.at[i, lon_col], grid=grid, with_bells3=with_bells3)
        done += 1
        if done % 25 == 0 or done == n_groups:
            log.info("N2: przetworzono %d/%d grup (komorka x doba)", done, n_groups)
    res = [rows[i] for i in df.index]
    out = pd.DataFrame({
        "t_layer": [r.value for r in res], "t_layer_uncal": [r.value_uncal for r in res], "u95": [r.u95 for r in res],
        "a_sw": [r.a_sw for r in res], "ts_sim": [r.ts_sim for r in res], "ir_masa": [r.ir_masa for r in res],
        "calib_flag": [r.calib_flag for r in res], "qc_flags": [r.flags for r in res],
        "grid_lat": [r.grid_lat for r in res], "grid_lon": [r.grid_lon for r in res], "sw_ma6": [r.sw_ma6 for r in res]},
        index=df.index)
    if with_bells3:
        out["bells3_c"] = [r.bells3 for r in res]
    return out
