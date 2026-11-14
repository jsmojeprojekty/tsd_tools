"""Stale wspolne dla narzedzi (jednostki: ugiecia [um], sila [kN], temperatura [C], odleglosci [mm]/[m])."""

T_REF_C = 20.0
LOAD_REF_KN = 50.0

# Czujniki FWD (geofony) i ich odleglosci od srodka obciazenia [mm]; D9 = 1800 mm nie ma odpowiednika w TSD.
GEOPHONES = ("D0", "D200", "D300", "D450", "D600", "D900", "D1200", "D1500", "D1800")
GEOPHONE_OFFSETS_MM = (0.0, 200.0, 300.0, 450.0, 600.0, 900.0, 1200.0, 1500.0, 1800.0)
STANDARD_LAYOUT_MM = GEOPHONE_OFFSETS_MM
OFFSET_TOL_MM = 1.0

# Wskazniki krzywizny liczone wylacznie z ugiec skorygowanych: nazwa -> (czujnik blizszy, czujnik dalszy)
INDICES = {"SCI300": ("D0", "D300"), "BDI": ("D300", "D600"), "BCI": ("D600", "D900")}

# Zakresy waznosci korekty temperaturowej [C] (raport PW.S-1063, 7.1); ponizej 5 C korekta nie ma zastosowania.
RANGE_A_C = (5.0, 25.0)
RANGE_B_C = (5.0, 30.0)
RANGE_LEGACY_C = (5.0, 25.0)
T_MIN_APPLICABLE_C = 5.0
INDICES_MAX_C = 25.0

# Wspolczynniki dotychczasowego wzoru krajowego (tryb porownawczy) wg typu drogi.
LEGACY_K = {"public": 0.02, "highway": 0.01}

# Wartosci zastepcze temperatury zapisywane przez aparat (wpis 22 bazy: 20,4 C).
PLACEHOLDER_TEMPS_C = (20.4,)
PLACEHOLDER_TOL_C = 1e-3
# Wypelniacz float32 spotykany w eksportach Drops (pierwsza stacja).
SENTINEL_MIN = -1.0e30
