"""Wspolne fixtures. Testy @reference czytaja dane poza repozytorium (tylko do odczytu) wg tests/local_paths.yaml."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

TESTS = Path(__file__).resolve().parent
DATA = TESTS / "data"


@pytest.fixture(scope="session")
def local_paths() -> dict:
    p = TESTS / "local_paths.yaml"
    if not p.is_file():
        pytest.skip("brak tests/local_paths.yaml (testy @reference pominiete)")
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


@pytest.fixture(scope="session")
def sql_root(local_paths) -> Path:
    root = local_paths.get("sql_tsd_fwd_root")
    if not root or not Path(root).is_dir():
        pytest.skip("brak sciezki sql_tsd_fwd_root w tests/local_paths.yaml")
    return Path(root)


@pytest.fixture(scope="session")
def drops_xlsx() -> Path:
    return DATA / "Drops50_1M_1.xlsx"


@pytest.fixture(scope="session")
def stations_xlsx() -> Path:
    return DATA / "stations50_1M_1.xlsx"


def _write_b1510off(path, n=300, a=2000.0, x0=0.0, d0_base=180.0, recal="t4202405210001.raw.pg2", chain_step=1.0,
                    spike_rows=(), temp_road=30.0, gof=0.8, lat0=52.0, lon0=21.0, heading_turn=False, seed=0):
    """Syntetyczny eksport B_1510off: nachylenia liniowe slope(x) = a*(x - x0) [um/m] na wszystkich kanalach,
    d0 = d0_base (+ szum), GPS wzdluz linii (lub z zakretem)."""
    import numpy as np

    rng = np.random.default_rng(seed)
    xs = {"1.510": 1.51, "0.910": 0.91, "0.610": 0.61, "0.460": 0.46, "0.310": 0.31, "0.210": 0.21, "0.110": 0.11,
          "-0.200": -0.2, "-0.300": -0.3, "-0.450": -0.45}
    slope_cols = [f"Slope {k} [µm/m]" for k in xs]
    cols = (["Chainage [m]", "Driving Speed [m/s]", "GyroYaw [rad/s]", "Strain Gauge Right [kg]", "Temp Road [°C]",
             "Temp Air [°C]"] + slope_cols + ["D0 [µm]", "Goodness of fit", "Latitude [dd.dddd]", "Longitude [dd.dddd]",
                                              "GPS time"])
    lines = ["Headers:", f"Re-calibrationfile: {recal}", "", "Parameters:", "Result interval: 1.0000 m",
             "Model type: Asymmetrical model", "GoodNess limit: 0.1500", "", "Data:", ", ".join(cols)]
    lat, lon = lat0, lon0
    heading = 0.0
    for i in range(n):
        chain = i * chain_step
        if heading_turn:
            heading = 0.4 * np.sin(i / 25.0)
        lat += chain_step * np.cos(heading) / 111320.0
        lon += chain_step * np.sin(heading) / (111320.0 * np.cos(np.radians(52.0)))
        sl = [a * (x - x0) for x in xs.values()]
        d0 = d0_base + rng.normal(0, 2.0)
        if i in spike_rows:
            d0 = d0_base * 6.0
        t = 37000 + i                                    # GPS time hhmmss: 10:16:40 + i s (uproszczone)
        sec = 10 * 3600 + 16 * 60 + 40 + i
        hhmmss = (sec // 3600) * 10000 + ((sec % 3600) // 60) * 100 + sec % 60
        vals = [chain, 20.0, 0.0, 5200.0, temp_road, 20.0] + sl + [-d0, gof, lat, lon, float(hhmmss)]
        lines.append(", ".join(f"{v:.6f}" if isinstance(v, float) else str(v) for v in vals))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


@pytest.fixture
def make_tsd(tmp_path):
    def factory(name="T4202504230012.raw.sup.txt", **kw):
        return _write_b1510off(tmp_path / name, **kw)
    return factory
