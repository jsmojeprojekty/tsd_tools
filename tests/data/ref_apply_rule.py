r"""zrodlo: C:\projects\sql_tsd_fwd\bak\e2aR2_rules.py, apply_rule, stan c67f7fe / 2026-10-26 (kopia bez zmian)."""
import numpy as np


def apply_rule(y, T, form, param):
    if form == 'guideline':
        return y * (1.0 + param * (20.0 - T))
    return y * np.exp(param * (20.0 - T))
