"""Dane meteo Open-Meteo (archiwum reanalizy): klient HTTP, konwersja czasu, cache plikowy.

zrodlo: C:\\WORK\\DOKTORAT\\temp_model\\src\\fetch_openmeteo.py (om_utc_to_local, fetch), z14lite_fetch_openmeteo.py (cache_name,
plan okien, retry 429), z14lite_validate.py (load_cell), stan 2026-11-13. Test tozsamosci: tests/unit/test_n2_units.py (DST),
tests/regression/test_n2_reference.py (odczyt cache referencyjnego).

Zasady (erratum czasu OM 2026-11-04): zapytanie ZAWSZE z timezone=UTC; etykiety przeliczane jawnie po stronie klienta do czasu
lokalnego Europe/Warsaw (naiwny, z DST). Okno zapytania konczy sie dnia POMIARU + 1 (ogon po 23:00). To jedyne polaczenie
sieciowe pakietu; przy `offline: true` nic nie jest pobierane."""

from __future__ import annotations

import datetime
import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

from .constants import (GRID_DEG, LOCAL_TZ, MAX_RETRY, MERGE_GAP_DAYS, OM_ARCHIVE_URL, OM_HOURLY, OM_TIMEZONE_QUERY,
                        RETRY_WAIT_S, SLEEP_S)

log = logging.getLogger(__name__)

REQUIRED_COLUMNS = ("temperature_2m", "dew_point_2m", "wind_speed_10m", "cloud_cover", "shortwave_radiation")


class MeteoError(RuntimeError):
    """Blad pobierania lub odczytu danych meteo."""


class MeteoUnavailable(MeteoError):
    """Brak pokrycia danymi meteo w cache (tryb offline) albo odmowa serwera."""


def om_utc_to_local(df: pd.DataFrame) -> pd.DataFrame:
    """Etykiety UTC -> czas lokalny Europe/Warsaw z DST (bez strefy). Godzina podwojna (jesien): zostaje PIERWSZE wystapienie;
    godzina brakujaca (wiosna): brak wiersza (interpolacja po czasie przy skladaniu cech)."""
    out = df.copy()
    out.index = df.index.tz_localize("UTC").tz_convert(LOCAL_TZ).tz_localize(None)
    out = out[~out.index.duplicated(keep="first")].sort_index()
    out.index.name = df.index.name
    return out


def quantize(lat: float, lon: float, grid_deg: float = GRID_DEG) -> tuple:
    """Zaokraglenie wspolrzednych zapytania do siatki `grid_deg` (siatka reanalizy jest rzadsza, 0,1-0,25 st.)."""
    return (round(round(float(lat) / grid_deg) * grid_deg, 2), round(round(float(lon) / grid_deg) * grid_deg, 2))


def cache_basename(lat: float, lon: float, start: str, end: str) -> str:
    return f"om_{lat:+.2f}_{lon:+.2f}_{start}_{end}".replace("+", "p").replace("-", "m")


def _cell_prefix(lat: float, lon: float) -> str:
    return "om_" + f"{lat:+.2f}".replace("+", "p").replace("-", "m") + "_" + f"{lon:+.2f}".replace("+", "p").replace("-", "m") + "_"


def _default_http_get(url: str, params: dict, timeout: float) -> dict:
    full = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(full, headers={"User-Agent": "tsdfwd-tools"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:           # noqa: S310 - stale, jawny adres https
        return json.loads(resp.read().decode("utf-8"))


def fetch_open_meteo(lat: float, lon: float, start, end, *, http_get=None, sleep=time.sleep) -> tuple:
    """Pobiera dane godzinowe dla DAT LOKALNYCH [start, end] i zwraca (DataFrame w czasie lokalnym, metadane).

    Zapytanie: timezone=UTC, wind_speed_unit=ms, 6 zmiennych; zakres UTC = [start-1 d, end+1 d] (obcinany po konwersji).
    HTTP 429 -> przerwa RETRY_WAIT_S i ponowienie (max MAX_RETRY); zerwane polaczenie -> krotsza przerwa rosnaca."""
    http_get = http_get or _default_http_get
    s_loc, e_loc = pd.Timestamp(start).normalize(), pd.Timestamp(end).normalize()
    params = {"latitude": float(lat), "longitude": float(lon),
              "start_date": (s_loc - pd.Timedelta(days=1)).date().isoformat(),
              "end_date": (e_loc + pd.Timedelta(days=1)).date().isoformat(),
              "hourly": ",".join(OM_HOURLY), "timezone": OM_TIMEZONE_QUERY, "wind_speed_unit": "ms"}
    js = None
    for attempt in range(1, MAX_RETRY + 1):
        try:
            js = http_get(OM_ARCHIVE_URL, params, 120)
            break
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                log.warning("Open-Meteo HTTP 429 (proba %d/%d) - czekam %.0f s", attempt, MAX_RETRY, RETRY_WAIT_S)
                sleep(RETRY_WAIT_S)
                continue
            raise MeteoUnavailable(f"Open-Meteo: HTTP {exc.code} ({exc.reason})") from exc
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            wait = 5.0 * attempt
            log.warning("Open-Meteo: polaczenie nieudane (%s), proba %d/%d - czekam %.0f s", exc, attempt, MAX_RETRY, wait)
            sleep(wait)
    if js is None:
        raise MeteoUnavailable("Open-Meteo: brak odpowiedzi po maksymalnej liczbie prob (limit/blokada lub brak sieci)")
    if "hourly" not in js or "time" not in js["hourly"]:
        raise MeteoUnavailable(f"Open-Meteo: nieoczekiwana odpowiedz: {str(js)[:200]}")
    h = js["hourly"]
    df = pd.DataFrame({k: pd.to_numeric(pd.Series(h.get(k)), errors="coerce") for k in OM_HOURLY})
    df.index = pd.to_datetime(pd.Series(h["time"]))
    df.index.name = "timestamp"
    df = om_utc_to_local(df.sort_index())
    df = df.loc[s_loc: e_loc + pd.Timedelta(hours=23, minutes=59)]
    meta = {"source": "open-meteo.com archive API (reanaliza)", "models": "best_match (domyslny produkt Open-Meteo)",
            "query_lat": float(lat), "query_lon": float(lon),
            "grid_lat": js.get("latitude"), "grid_lon": js.get("longitude"), "elevation_m": js.get("elevation"),
            "api_timezone_param": OM_TIMEZONE_QUERY, "time_basis": "local_Europe_Warsaw_DST_from_UTC",
            "start": s_loc.date().isoformat(), "end": e_loc.date().isoformat(), "hourly_vars": list(OM_HOURLY),
            "fetched_at": datetime.datetime.now().isoformat(timespec="seconds"), "units": js.get("hourly_units", {}),
            "n_rows": int(len(df)), "n_missing": {c: int(df[c].isna().sum()) for c in df.columns}}
    return df, meta


def _read_frame(base: Path) -> pd.DataFrame:
    pq, csv = Path(str(base) + ".parquet"), Path(str(base) + ".csv")       # nazwa zawiera kropki: bez with_suffix
    if pq.is_file():
        df = pd.read_parquet(pq)
    elif csv.is_file():
        df = pd.read_csv(csv, index_col=0, parse_dates=True)
    else:
        raise MeteoError(f"brak danych cache: {base}.parquet/.csv")
    df.index = pd.DatetimeIndex(df.index).as_unit("ns")
    return df


class MeteoStore:
    """Cache plikowy zapytan Open-Meteo: jedna para plikow (dane + `.json` z oknem i punktem siatki) na zapytanie.

    Czyta cache w formacie parquet (referencyjny, projekt temp_model) i csv (zapisywany przez to narzedzie). Gdy cache nie
    pokrywa okna i `offline` jest falszem, pobiera brakujace okno (jedyne polaczenie sieciowe)."""

    def __init__(self, cache_dir, *, offline: bool = True, grid_deg: float = GRID_DEG, http_get=None, sleep=time.sleep):
        self.cache_dir = Path(cache_dir)
        self.offline = offline
        self.grid_deg = grid_deg
        self._http_get = http_get
        self._sleep = sleep
        self._mem: dict = {}
        self.n_fetched = 0

    def _entries(self, q_lat: float, q_lon: float) -> list:
        out = []
        for jf in sorted(self.cache_dir.glob(_cell_prefix(q_lat, q_lon) + "*.json")):
            try:
                meta = json.loads(jf.read_text(encoding="utf-8"))
                out.append((Path(str(jf)[:-len(".json")]), pd.Timestamp(meta["start"]), pd.Timestamp(meta["end"]), meta))
            except (ValueError, KeyError, OSError):
                log.warning("pominieto uszkodzony wpis cache: %s", jf)
        return out

    @staticmethod
    def _covers(entries: list, lo_day: pd.Timestamp, hi_day: pd.Timestamp) -> bool:
        day = lo_day
        for _, s, e, _ in sorted(entries, key=lambda x: x[1]):
            if s <= day <= e:
                day = e + pd.Timedelta(days=1)
            if day > hi_day:
                return True
        return day > hi_day

    def get(self, lat: float, lon: float, lo, hi) -> tuple:
        """Dane godzinowe (czas lokalny) dla komorki zapytania obejmujacej (lat, lon) w zakresie [lo-1 d, hi+1 d]; zwraca
        (DataFrame, informacje: grid_lat, grid_lon, query_lat/lon, pliki, fetched_at)."""
        lo, hi = pd.Timestamp(lo), pd.Timestamp(hi)
        q_lat, q_lon = quantize(lat, lon, self.grid_deg)
        entries = self._entries(q_lat, q_lon)
        if not self._covers(entries, lo.normalize(), hi.normalize()):
            if self.offline:
                raise MeteoUnavailable(f"cache nie pokrywa okna {lo.date()}..{hi.date()} dla komorki ({q_lat:+.2f}; {q_lon:+.2f}) "
                                       "(tryb offline)")
            self._download(q_lat, q_lon, lo.normalize(), hi.normalize() + pd.Timedelta(days=1))
            entries = self._entries(q_lat, q_lon)
        frames, grid, fetched, files = [], (None, None), None, []
        for base, s, e, meta in entries:
            if e < lo.normalize() or s > hi.normalize():
                continue
            key = str(base)
            if key not in self._mem:
                self._mem[key] = _read_frame(base)
            frames.append(self._mem[key])
            grid = (meta.get("grid_lat"), meta.get("grid_lon"))
            fetched = meta.get("fetched_at", fetched)
            files.append(base.name)
        if not frames:
            raise MeteoUnavailable(f"brak danych meteo dla komorki ({q_lat:+.2f}; {q_lon:+.2f}) w oknie {lo.date()}..{hi.date()}")
        om = pd.concat(frames).sort_index()
        om = om[~om.index.duplicated(keep="first")]
        om = om.loc[lo - pd.Timedelta(days=1): hi + pd.Timedelta(days=1)]
        return om, {"grid_lat": grid[0], "grid_lon": grid[1], "query_lat": q_lat, "query_lon": q_lon, "files": files,
                    "fetched_at": fetched}

    def _download(self, q_lat: float, q_lon: float, start: pd.Timestamp, end: pd.Timestamp) -> None:
        today = pd.Timestamp.now().normalize()
        if end > today - pd.Timedelta(days=5):
            log.warning("Open-Meteo archive: dane z ostatnich ~5 dni moga byc niepelne (okno do %s)", end.date())
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        s, e = start.date().isoformat(), end.date().isoformat()
        log.info("pobieranie Open-Meteo: komorka (%+.2f; %+.2f), okno %s..%s", q_lat, q_lon, s, e)
        df, meta = fetch_open_meteo(q_lat, q_lon, s, e, http_get=self._http_get, sleep=self._sleep)
        base = self.cache_dir / cache_basename(q_lat, q_lon, s, e)
        Path(str(base) + ".csv").write_text(df.to_csv(), encoding="utf-8")
        Path(str(base) + ".json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        self.n_fetched += 1
        self._sleep(SLEEP_S)


def plan_windows(days: list, history_days: int, merge_gap_days: int = MERGE_GAP_DAYS) -> list:
    """Okna [dzien - history, dzien + 1] scalane przy przerwie < merge_gap_days (minimalna liczba zapytan)."""
    wins: list = []
    for day in sorted(set(pd.Timestamp(d).normalize() for d in days)):
        s, e = day - pd.Timedelta(days=history_days), day + pd.Timedelta(days=1)
        if wins and s <= wins[-1][1] + pd.Timedelta(days=merge_gap_days):
            wins[-1] = (wins[-1][0], max(wins[-1][1], e))
        else:
            wins.append((s, e))
    return wins


def last_valid_times(om: pd.DataFrame) -> tuple:
    """Ostatnie etykiety z waznymi danymi: (temperatura, promieniowanie) - do flagi ogona."""
    out = []
    for c in ("temperature_2m", "shortwave_radiation"):
        idx = om[c].last_valid_index() if c in om else None
        out.append(pd.Timestamp(idx) if idx is not None else pd.NaT)
    return tuple(out)


def in_poland(lat: float, lon: float) -> bool:
    return bool(48.9 <= lat <= 55.0 and 14.0 <= lon <= 24.3)


__all__ = ["MeteoError", "MeteoUnavailable", "MeteoStore", "fetch_open_meteo", "om_utc_to_local", "quantize", "cache_basename",
           "plan_windows", "last_valid_times", "in_poland", "REQUIRED_COLUMNS"]
