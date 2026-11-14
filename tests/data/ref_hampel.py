r"""zrodlo: C:\WORK\DOKTORAT\tsd_2_xml\tsd_pipeline.py, _hampel_col (WIN = 21, HAMPEL_K = 3.0), stan 2026-07-01 (kopia bez zmian)."""
import numpy as np

WIN = 21
HAMPEL_K = 3.0


def _hampel_col(s):
    """Filtr Hampela na serii: NaN gdy |x-med_okna| > k*1.4826*MAD_okna."""
    med = s.rolling(WIN, center=True, min_periods=1).median()
    mad = s.rolling(WIN, center=True, min_periods=1).apply(
        lambda w: np.nanmedian(np.abs(w - np.nanmedian(w))), raw=True)
    thr = HAMPEL_K * 1.4826 * mad
    return s.where(~((np.abs(s - med) > thr) & (thr > 0)))
