"""Generator zalacznika "Odtwarzalnosc" (docs/ODTWARZALNOSC.md).

Laczy trzy zrodla: opisy i wartosci referencyjne testow z docs/PROJEKT.md (p. 6, tabele T-Nx-yy), rejestr docs/odtwarzalnosc/rejestr.yaml
(punkt raportu, nazwy testow) i wynik biezacego uruchomienia pytest (JUnit XML). Dzieki temu tabela nie rozjezdza sie z kodem:
status kazdego numeru testu pochodzi z faktycznego przebiegu.

Uzycie (z katalogu glownego repozytorium):
    python docs/odtwarzalnosc/zbuduj_odtwarzalnosc.py                 # uruchamia pytest i buduje dokument
    python docs/odtwarzalnosc/zbuduj_odtwarzalnosc.py --junit x.xml   # uzywa gotowego wyniku pytest
"""

from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import platform
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import OrderedDict
from importlib import metadata
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
PROJEKT = ROOT / "docs" / "PROJEKT.md"
REJESTR = Path(__file__).with_name("rejestr.yaml")
OUT = ROOT / "docs" / "ODTWARZALNOSC.md"

ROW = re.compile(r"^\| (T-(?:N[1-4]|D)-\d\d) \| (.*) \|\s*$")


def read_spec() -> "OrderedDict[str, dict]":
    """Wiersze tabel T-Nx-yy z PROJEKT.md: opis, wartosc referencyjna, tolerancja, zrodlo."""
    spec: "OrderedDict[str, dict]" = OrderedDict()
    for line in PROJEKT.read_text(encoding="utf-8").splitlines():
        m = ROW.match(line)
        if not m:
            continue
        parts = m.group(2).split(" | ", 3)
        if len(parts) < 4:
            continue
        spec[m.group(1)] = {"opis": parts[0].strip(), "wartosc": parts[1].strip(), "tol": parts[2].strip(), "zrodlo": parts[3].strip()}
    return spec


def run_pytest(junit: Path) -> int:
    cmd = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", f"--junitxml={junit}"]
    return subprocess.run(cmd, cwd=ROOT).returncode


def read_junit(path: Path) -> list[dict]:
    """Przypadki testowe: modul, funkcja (bez parametrow), status: pass / fail / skip / xfail."""
    out = []
    for tc in ET.parse(path).getroot().iter("testcase"):
        module = tc.get("classname", "").split(".")[-1]
        base = re.sub(r"\[.*\]$", "", tc.get("name", ""))
        status = "pass"
        for ch in tc:
            if ch.tag in ("failure", "error"):
                status = "fail"
            elif ch.tag == "skipped":
                kind = (ch.get("type") or "") + " " + (ch.get("message") or "")
                status = "xfail" if "xfail" in kind.lower() or "expected test failure" in kind.lower() else "skip"
        out.append({"key": f"{module}::{base}", "module": module, "status": status})
    return out


def esc(s: str) -> str:
    return s.replace("|", "\\|")


def git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except Exception:  # noqa: BLE001
        return ""


def verdict(counts: dict) -> str:
    n = sum(counts.values())
    if n == 0:
        return "BRAK TESTU"
    if counts["fail"]:
        return "NIEZGODNY"
    if counts["xfail"]:
        return "znana rozbieznosc"
    if counts["skip"] and counts["pass"]:
        return "zgodny (czesc pominieta: brak danych)"
    if counts["skip"]:
        return "pominiety (brak danych)"
    return "zgodny"


def build(junit: Path) -> str:
    spec = read_spec()
    reg = yaml.safe_load(REJESTR.read_text(encoding="utf-8"))
    cases = read_junit(junit)
    used: set[str] = set()
    rows = []
    for tid, patterns in reg["testy"].items():
        matched = [c for c in cases if any(fnmatch.fnmatch(c["key"], p) for p in patterns)]
        used.update(c["key"] for c in matched)
        counts = {"pass": 0, "fail": 0, "skip": 0, "xfail": 0}
        for c in matched:
            counts[c["status"]] += 1
        rows.append((tid, spec.get(tid, {}), counts, verdict(counts)))
    unmapped = [c for c in cases if c["key"] not in used]

    total = {"pass": 0, "fail": 0, "skip": 0, "xfail": 0}
    for c in cases:
        total[c["status"]] += 1

    head = git("rev-parse", "HEAD")
    dirty = bool(git("status", "--porcelain", "--", "src", "tests", "configs", "pyproject.toml"))
    try:
        ver = metadata.version("tsdfwd_tools")
    except Exception:  # noqa: BLE001
        ver = "?"
    libs = []
    for name in ("numpy", "scipy", "pandas", "pyyaml", "openpyxl"):
        try:
            libs.append(f"{name} {metadata.version(name)}")
        except Exception:  # noqa: BLE001
            pass
    has_ref = (ROOT / "tests" / "local_paths.yaml").is_file()

    L: list[str] = []
    L.append("# Zalacznik: odtwarzalnosc obliczen narzedzi tsdfwd_tools wzgledem raportu PW.S-1063 (Etap II)")
    L.append("")
    L.append("Dokument jest **generowany** (`docs/odtwarzalnosc/zbuduj_odtwarzalnosc.py`) z kodu, planu testow (`docs/PROJEKT.md`, p. 6) i faktycznego "
             "przebiegu testow; nie jest pisany recznie, wiec nie rozjezdza sie z kodem. Narzedzia N1-N4 odtwarzaja metody raportu i sa jednoczesnie "
             "ich dokumentacja wykonawcza: dla wartosci referencyjnych z raportu i z bazy zrodlowej podano test, ktory je odtwarza, wraz z tolerancja i wynikiem.")
    L.append("")
    L.append("## 1. Wersja i srodowisko")
    L.append("")
    L.append(f"- pakiet `tsdfwd_tools` {ver}; commit kodu (HEAD w chwili generowania): `{head[:12] if head else 'brak git'}`"
             f"{' (drzewo robocze zawiera niezatwierdzone zmiany w kodzie)' if dirty else ' (drzewo robocze czyste)'}")
    L.append(f"- data wygenerowania: {dt.date.today().isoformat()}; Python {platform.python_version()} ({platform.system()}); {', '.join(libs)}")
    L.append(f"- testy z danymi referencyjnymi poza repozytorium (@reference): {'wykonane (dostepne dane zrodlowe, tylko odczyt)' if has_ref else 'POMINIETE (brak tests/local_paths.yaml)'}")
    L.append(f"- wynik calego przebiegu: {sum(total.values())} testow: {total['pass']} zaliczonych, {total['fail']} niezaliczonych, "
             f"{total['xfail']} oczekiwanych niepowodzen (znana rozbieznosc), {total['skip']} pominietych")
    L.append("")
    L.append("## 2. Narzedzia i punkty raportu")
    L.append("")
    L.append("| Narzedzie | Modul | Punkty raportu / zrodlo metody |")
    L.append("|---|---|---|")
    for k, v in reg["narzedzia"].items():
        L.append(f"| {k} | `{v['nazwa']}` | {esc(v['punkt_raportu'])} |")
    L.append("")
    L.append("## 3. Macierz odtwarzalnosci")
    L.append("")
    L.append("Kolumny: numer testu | co sprawdza | wartosc referencyjna (z raportu lub bazy zrodlowej) | tolerancja | rodzaj | liczba testow (zaliczone/pominiete/niezaliczone) | wynik. "
             "Rodzaj: `@reference` = porownanie z danymi zrodlowymi projektu (wymaga dostepu do nich); `@unit` = obliczenie analityczne lub dane syntetyczne w repozytorium.")
    L.append("")
    cur, n_sec = "", 0
    for tid, sp, c, v in rows:
        tool = tid.split("-")[1]
        if tool != cur:
            cur = tool
            n_sec += 1
            L.append("")
            L.append(f"### 3.{n_sec} {cur} - {reg['narzedzia'][cur]['nazwa']}")
            L.append("")
            L.append("| Test | Co sprawdza | Wartosc referencyjna | Tolerancja | Rodzaj | Przypadki: ok / xfail / pominiete / fail | Wynik |")
            L.append("|---|---|---|---|---|---|---|")
        L.append(f"| {tid} | {esc(sp.get('opis', '?'))} | {esc(sp.get('wartosc', '?'))} | {esc(sp.get('tol', '?'))} | {esc(sp.get('zrodlo', '?').split(' ')[0])} | "
                 f"{c['pass']} / {c['xfail']} / {c['skip']} / {c['fail']} | **{v}** |")
    L.append("")
    L.append("## 4. Rozbieznosci wzgledem zrodel (wyjasnione)")
    L.append("")
    L.append("| Oznaczenie | Opis | Test |")
    L.append("|---|---|---|")
    for r in reg["roznice"]:
        L.append(f"| {r['id']} | {esc(r['opis'])} | {r['test']} |")
    L.append("")
    L.append("Powyzsze rozbieznosci sa jedynymi znanymi; szczegoly decyzji sa w `docs/DZIENNIK.md` i `docs/PROJEKT.md`.")
    L.append("")
    L.append("## 5. Ograniczenia")
    L.append("")
    for t in reg["ograniczenia"]:
        L.append(f"- {t}")
    L.append("")
    L.append("## 6. Testy uzupelniajace (bez numeru T)")
    L.append("")
    by_mod: "OrderedDict[str, dict]" = OrderedDict()
    for c in unmapped:
        d = by_mod.setdefault(c["module"], {"pass": 0, "fail": 0, "skip": 0, "xfail": 0})
        d[c["status"]] += 1
    if by_mod:
        L.append("Konfiguracja, wejscie/wyjscie, CLI i przypadki brzegowe, ktore nie odpowiadaja liczbie z raportu:")
        L.append("")
        L.append("| Modul testowy | zaliczone | pominiete | niezaliczone |")
        L.append("|---|---|---|---|")
        for m, d in by_mod.items():
            L.append(f"| {m} | {d['pass'] + d['xfail']} | {d['skip']} | {d['fail']} |")
    else:
        L.append("Wszystkie testy sa przypisane do numerow T.")
    L.append("")
    L.append("## 7. Jak odtworzyc")
    L.append("")
    L.append("```bash")
    L.append("python -m pytest                                  # wszystkie testy (testy @reference tylko przy dostepnych danych zrodlowych)")
    L.append("python docs/odtwarzalnosc/zbuduj_odtwarzalnosc.py  # przebieg + odswiezenie tego dokumentu")
    L.append("```")
    L.append("")
    L.append("Testy @reference wymagaja pliku `tests/local_paths.yaml` (wzor: `tests/local_paths.example.yaml`) ze sciezkami do danych projektu; dane sa tylko czytane. "
             "Testy @unit i przyklady w `demo/` dzialaja bez danych zewnetrznych.")
    L.append("")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--junit", type=Path, help="gotowy wynik pytest (JUnit XML); bez tego uruchamia pytest")
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args()
    junit = a.junit
    if junit is None:
        import tempfile

        junit = Path(tempfile.mkdtemp()) / "junit.xml"
        run_pytest(junit)
    if not junit.is_file():
        print("brak wyniku pytest", file=sys.stderr)
        return 2
    text = build(junit)
    a.out.write_text(text + "\n", encoding="utf-8", newline="\n")
    print(f"zapisano {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
