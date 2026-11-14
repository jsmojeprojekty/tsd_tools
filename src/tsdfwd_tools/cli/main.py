"""Wiersz polecen: python -m tsdfwd_tools <narzedzie> --config plik.yaml

Narzedzia: fwd_tempcorr (n1). Pozostale (layer_temp/n2, tsd_network/n3, tsd_fwd_compare/n4) powstaja w kolejnych etapach."""

from __future__ import annotations

import argparse
import logging
import sys

from .. import __version__
from ..common.config import ConfigError, load_n1_config
from ..common.logging_setup import setup_logging

TOOLS = {
    "fwd_tempcorr": "n1", "n1": "n1",
    "fwd_fit": "fit", "n1fit": "fit",
    "layer_temp": "n2", "n2": "n2",
    "tsd_network": "n3", "n3": "n3",
    "tsd_fwd_compare": "n4", "n4": "n4",
}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="tsdfwd", description="Narzedzia TSD/FWD (IBDiM)")
    p.add_argument("--version", action="version", version=f"tsdfwd-tools {__version__}")
    p.add_argument("tool", choices=sorted(TOOLS), help="narzedzie: fwd_tempcorr (n1), layer_temp (n2), "
                                                      "tsd_network (n3), tsd_fwd_compare (n4)")
    p.add_argument("--config", required=True, help="plik konfiguracji YAML")
    p.add_argument("--out-dir", default=None, help="nadpisuje output.dir z konfiguracji")
    p.add_argument("--dry-run", action="store_true", help="przetwarza dane bez zapisu wynikow")
    p.add_argument("--log-level", default=None, help="DEBUG | INFO | WARNING | ERROR")
    p.add_argument("--strict", action="store_true",
                   help="kod wyjscia 2, gdy w wynikach sa flagi krytyczne (brak/niewazna temperatura)")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    tool = TOOLS[args.tool]
    if tool == "fit":
        return _main_fit(args)
    if tool == "n4":
        return _main_n4(args)
    if tool != "n1":
        print(f"narzedzie {args.tool} nie jest jeszcze zaimplementowane (kolejne etapy)", file=sys.stderr)
        return 1
    try:
        cfg = load_n1_config(args.config)
        if args.out_dir:
            cfg.output.dir = args.out_dir
        setup_logging(args.log_level or cfg.log_level)
        from ..fwd.pipeline import run_n1
        result = run_n1(cfg, dry_run=args.dry_run)
    except (ConfigError, FileNotFoundError, ValueError, KeyError, RuntimeError) as exc:
        print(f"BLAD: {exc}", file=sys.stderr)
        return 1
    log = logging.getLogger("tsdfwd")
    for fr in result.files:
        log.info("%s: %d stacji, skorygowano %d", fr.summary["file"], fr.summary["n_stations"],
                 fr.summary["n_corrected"])
    for p in result.outputs:
        log.info("zapisano %s", p)
    if args.strict:
        from ..common.flags import Flag
        critical = int(Flag.T_MISSING | Flag.T_BELOW_5C)
        if any((fr.table["flags"].to_numpy() & critical).any() for fr in result.files):
            return 2
    return 0


def _main_n4(args) -> int:
    from ..common.config_n4 import load_n4_config
    from ..compare.pipeline import run_n4
    try:
        cfg = load_n4_config(args.config)
        if args.out_dir:
            cfg.output.dir = args.out_dir
        setup_logging(args.log_level or cfg.log_level)
        result = run_n4(cfg, dry_run=args.dry_run)
    except (ConfigError, FileNotFoundError, ValueError, KeyError, RuntimeError) as exc:
        print(f"BLAD: {exc}", file=sys.stderr)
        return 1
    log = logging.getLogger("tsdfwd")
    meta = result["meta"]
    log.info("N4 (pairs): %d par (wazne %d), %d sesji FWD", meta["n_pairs"], meta["n_valid_pairs"], meta["n_sessions"])
    for p in result["outputs"]:
        log.info("zapisano %s", p)
    if args.strict and meta["n_t12_outside_or_missing"]:
        return 2
    return 0


def _main_fit(args) -> int:
    from ..common.config_fit import load_fit_config
    from ..fwd.fit_pipeline import run_fit
    try:
        cfg = load_fit_config(args.config)
        if args.out_dir:
            cfg.output.dir = args.out_dir
        setup_logging(args.log_level or cfg.log_level)
        result = run_fit(cfg, dry_run=args.dry_run)
    except (ConfigError, FileNotFoundError, ValueError, KeyError, RuntimeError) as exc:
        print(f"BLAD: {exc}", file=sys.stderr)
        return 1
    log = logging.getLogger("tsdfwd")
    log.info("dopasowano %d wskaznikow na %d wizytach", len(result["table"]), result["n_visits"])
    for p in result["outputs"]:
        log.info("zapisano %s", p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
