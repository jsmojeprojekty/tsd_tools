# E0_F — Przegląd katalogu `C:\WORK\DOKTORAT\tsd_2_xml` (tylko odczyt)

Stan katalogu: skrypty z 2026-07-01, README "wersja finalna" z 2026-07-01. Wszystko poniżej wynika z lektury kodu oraz z odczytu plików danych
(zapis tylko w scratchpadzie). Liczby (rekordy, zakresy, zgodność pól) zostały **sprawdzone na danych**; wnioski interpretacyjne oznaczono słowem "wniosek/hipoteza".

Skrypty pomocnicze użyte do analizy (scratchpad): `an_xml.py`, `an_xls.py`, `an_xlsx.py`, `an_1m.py`, `an_1m2.py`, `an_temp.py`, `an_align.py`, `an_fwd.py`, `an_verify.py`, `xr.py` (minimalny czytnik xlsx na zipfile, bo na tej maszynie nie ma openpyxl).

---

## 0. Najważniejsze odkrycia (skrót)

1. **Pełna odtwarzalność:** algorytm z `tsd_pipeline.py` + `conversion_coeffs.json` odtwarza pola D_* w `UC_*.2026.xml` z błędem max 0,0005 µm (zaokrąglenie do 3 miejsc), a pozostałe pola (IRI, PREDKOSC, STRAIN, T_*, OBC_KN, LAT/LON, DATA/GODZ, SLOPE, T_DROGI_OBL) zgadzają się z źródłem 1 m w **100%** rekordów (0 niezgodności w 3 odcinkach). Mapowanie niżej jest więc potwierdzone empirycznie.
2. **U_STD w dokumencie formatu UC to NIE D_0.** W przykładzie z `format pliku UC.docx`: D_0 = 122,986, T_DROGI_OBL = 19,5, U_STD = 124,215; 122,986·(1+0,02·(20−19,5)) = 124,2159. Czyli U_STD = D_0 skorygowane temperaturowo do 20 °C (k = 0,02, temperatura = T_DROGI_OBL), bez normalizacji obciążenia (OBC_KN=52,3 nie wchodzi). SCI_200/SCI_300 w przykładzie = różnice nieskorygowanych D (42,928 = 122,986−80,058). Obecny `tsd_to_xml.py` ustawia **U_STD = D_0** (czyli po Tkor+afinicznej) — semantyka inna niż w dokumencie.
3. **'D Tkor' w plikach 1 m jest zaokrąglone do całkowitych µm** (wszystkie 3 pliki 1 m: `integer-valued=True`), a przy małych wartościach (np. D1500 = 0,04 µm) komórka jest pusta, więc odpada cała czasza. Z 6505/4284/2819 poprawnych (Status=Ok) czasz 1 m do średniej wchodzi tylko 6174/3863/2361 (traci się 331/421/458 czasz, 5–16%). Surowe `D* [µm]` w tym samym pliku (i w `.xls` 1 m) są ciągłe — nowe wejście d0 omija ten problem.
4. **Temperatura:** `T_DROGI_OBL` pochodzi z kolumny 21 (`T_XGB(120)`) pliku 1 m `.xlsx` (indeks na sztywno), a NIE jest używana do korekcji ugięć. Wartości `T_XGB(120)` w pliku 10 m i w pliku 1 m różnią się dla tego samego punktu (średnio +0,8 / +2,6 / +0,05 °C, zakres do 3,5 °C), a temperatura "efektywna" ukryta w Tkor (odtworzona z ilorazu Tkor/D przy k=0,02) nie jest funkcją `T_XGB(120)` z tego samego wiersza (odch. std 1,4–1,6 °C dla DK50). Nie ma w plikach kolumny temperatury z BELLS3_BT.
5. **Pułapki układu plików:** preambuła `.xls` ma różną długość (nagłówek danych w wierszu 0-based **60** w pliku 1 m, **61** w pliku 10 m); nazwy slope w pliku 1 m mają kropkę (`Slope 1.510`), w pliku 10 m przecinek (`Slope 1,510`); `tsd_to_xml.py` zakłada `XLS_HDR=60` i kropkę, więc **nie zadziała na eksporcie 10 m bez zmian**. W `.xlsx` 10 m jest 61 pustych wierszy na końcu. W `.xlsx` 1 m kolumna `Dr.Speed` jest na końcu (kol. 47), w `.xls` na pozycji 6.
6. **Brak `P0` / "całek nachyleń" w jakimkolwiek pliku w katalogu** (przeszukane nagłówki `.xls` 10 m, 1 m oraz `.xlsx` 10 m, 1 m, v2). W plikach są tylko surowe `Slope x.xxx [µm/m]` (10 szt.) oraz `D* [µm]` (11 szt., wyjście oprogramowania DigiProf). Zakres wejścia N3 (d0, P0) wymaga definicji od autora.
7. **FWD (Drops/stations):** temperatura asfaltu w `Asphalt`/`AsphaltTemperature` jest **stała dla całego odcinka** (18,0 °C dla obu DK50, 20,0 °C dla S8), a `Surface` zmienia się 18–39 °C; pierwsza stacja ma w `Drops.Asphalt` wartość sentinel −3,4028e38 (float32 min); `Stress`/`Force` są w kPa/kN; 2 zrzuty na stację (używany 2-gi).
8. Środowisko: `__pycache__` jest z CPython 3.10 (sandbox Cowork); lokalnie (miniconda 3.13) brak `openpyxl`, `scipy`, `matplotlib` (jest `xlrd`, `pandas`, `numpy`). Skrypty mają na sztywno ścieżkę zapasową `/sessions/hopeful-great-noether/mnt/outputs` (sandbox).

---

## 1. Zawartość katalogu

| Plik | Rozmiar | Rola |
|---|---|---|
| `README_workflow.md` | 5 kB | opis procedury (cel podstawowy: XML UC; dodatkowy: porównanie TSD–FWD) |
| `tsd_pipeline.py` | 8 kB | silnik (config, geo, FWD, TSD 1 m, Hampel+roll, konwersja afiniczna, KM z Event) |
| `tsd_to_xml.py` | 7 kB | procedura produkcyjna: XML roboczy 1 m + finalny 10 m |
| `calibrate_conversion.py` | 2 kB | kalibracja a,b (MNK) → `conversion_coeffs.json` |
| `conversion_coeffs.json` | 0,2 kB | DK50: a=0,84865 b=24,354; S8: a=0,47290 b=41,717 (`"method":"affine"`) |
| `compare_tsd_fwd.py` | 8 kB | analiza TSD vs FWD, wykresy w `_img/` |
| `compare_sci_agg.py` | 3 kB | SCI w skalach 1 m / 50 m / 1 km, wykresy `sci_agg_*.png` (te pliki jeszcze nie istnieją w `_img`) |
| `inject_dfwd.py` | 3 kB | jednorazowo: wpis D*FWD z XML do `T*.pgc.ibdim_v2.xlsx` |
| `format pliku UC.docx` | 17 kB | jedna tabela 1x1 z przykładowym fragmentem XML z komentarzami (brak opisu jednostek/typów) |
| `UC_<odc>.2026.xml` (3) | 0,9–1,3 MB | finalne, co 10 m |
| `UC_<odc>_temp.2026.xml` (3) | 9–13 MB | robocze, co 1 m |
| `T*.pgc.ibdim.xls/.xlsx` (3+3) | | eksport TSD, krok 10 m |
| `T*.pgc.ibdim_1m.xls/.xlsx` (3+3) | | eksport TSD, krok 1 m |
| `T*.pgc.ibdim_v2.xlsx` (3) | | 10 m .xlsx z wpisanym D*FWD z XML (wynik `inject_dfwd.py`) |
| `Drops*.xlsx`, `stations*.xlsx` (3+3) | | FWD (Dynatest) |
| `.~lock.*.xlsx#` (2) | | pliki blokady LibreOffice (`czasze_FWD_TSD_value5.xlsx`, `porownanie_TSD_FWD.xlsx` — tych arkuszy nie ma w katalogu) |
| `_img/` | | 5 png (profile_D0/SCI200/SCI300, scatter_metryki, scatter_wspolny) |

Brak: `UC_Schema.xsd` (referencja w XML, pliku nie ma w katalogu), brak `requirements.txt`, brak testów.

Odcinki (`tsd_pipeline.SECTIONS`):

| Klucz | Plik TSD (1 m) | Drops / stations | Grupa | DROGA w XML | Wynik |
|---|---|---|---|---|---|
| `50_1M` | `T4202605180002` | `Drops50_1M_1` / `stations50_1M_1` | DK50 | `50` | `UC_50_1_M_1` (kierunek malejących km) |
| `50_1R` | `T4202605180001` | `Drops50_1R_1` / `stations50_1R_1` | DK50 | `50` | `UC_50_1_R_1` (rosnących km) |
| `S8_1R` | `T4202605190001` | `DropsS8_1R_1` / `stationsS8_1R_1` | S8 | `S8l` | `UC_S8l_1_R_1` (rosnących km) |

---

## 2. Skrypty — analiza per plik

### 2.1 `tsd_pipeline.py` (silnik, importowany przez wszystkie pozostałe)

**Zależności:** `os, re, datetime, numpy, pandas, openpyxl` (bez scipy/matplotlib).
**Stałe na sztywno:** `R_EARTH=6371000.0`; `WIN=21` (średnia krocząca "±10 m" **zakłada krok 1 m**, rolling po indeksie wiersza, nie po chainage); `HAMPEL_K=3.0`; `MINP=1`; `SENTINEL=-1e30`; `OFFSETS_POS=[0,200,300,450,600,900,1200,1500]` (są w FWD); `OFFSETS_ALL=[-450,-300,-200,0,200,300,450,600,900,1200,1500]` [mm]; `TK_COL={-450:22 … 1500:32}` (indeksy 0-based kolumn **'D…Tkor' w `.xlsx` 1 m**); `FWD_DCOL={0:'D1',200:'D2',300:'D3',450:'D4',600:'D5',900:'D6',1200:'D7',1500:'D8'}` (D9 — dodatkowy czujnik, nieużywany; D10–D15 same zera); `SECTIONS`, `GROUPS`.

**Funkcje publiczne:**

| Sygnatura | Co robi | Uwagi / pułapki |
|---|---|---|
| `to_local_m(lat, lon, lat0, lon0) -> (x, y)` | rzut równoodległościowy lokalny [m] | tylko do KD-tree; wektorowe |
| `fnum(value, ndigits) -> str` | `f"{float(v):.{n}f}"`, `""` dla None/""/błędu | **NaN → "nan"** (float('nan') nie jest None); w praktyce NaN odfiltrowane wcześniej przez `convert_affine` (zwraca None). Zaokrąglenie Pythona (banker's dla dokładnych połówek binarnych) |
| `split_datetime(value) -> (data, godz)` | `datetime` → `%Y-%m-%d`,`%H:%M:%S`; string → rozdziela po spacji / 'T' | w plikach `DateTime` to tekst `'2026-05-18 13:07:57'`; brak strefy |
| `parse_event_markers(events, chains) -> [(chain_m, km_m)]` | z pola `Event` wyłuskuje tokeny `<chainage>_<km>` (regex z kropką dziesiętną), bierze pierwszy dopasowany token w komórce | **argument `chains` jest ignorowany** (chainage jest w samym ciągu Event, np. `218.466_40`); przecinek dziesiętny rozbiłby token (`replace(",", " ")` → `218` `466_40`); `5183.564_<Empty>` jest pomijany |
| `make_km_function(markers) -> callable(chain)->km` | `km(c) = (km0 + sign·(c − c0))/1000`, gdzie `(c0,km0)` = **pierwszy** marker; `sign=-1`, jeśli dwa pierwsze markery dają malejące km | brak markerów → `km = chain/1000` (fałszywa pikietaż od 0); jeden marker → `sign=+1` (zły dla malejących); drift koła dystansu nie jest korygowany (kotwica = tylko 1. marker): błąd względem markerów do 24 m (50_1M), 10 m (50_1R), 8 m (S8) |
| `load_fwd(base, drops_f, stations_f) -> DataFrame` | kol.: `StationID, km, lat, lon, FWD_0 … FWD_1500` [µm]; bierze **2-gi zrzut** (po `DropID`; jeśli jest tylko 1, to ostatni), `FWD = D·(50/Force)·(1+0,02·(20−Asphalt))`; `Asphalt` z `Drops`, a gdy None/<−1e30 → `AsphaltTemperature` ze `stations` | wynik **sortowany po km rosnąco** (dla 50_1M odwraca kolejność pomiaru); `Force`≤sentinel → NaN; `Station` jest w km (float32 z szumem, np. 43.0250015258789); data Excel-serial nieużywana |
| `load_tsd_bowl(base, t1m) -> DataFrame` | z `.xlsx` 1 m: `chainage, lat, lon, TK_<o>` (11 offsetów) i `km` (z Event kol. 4) | indeksy kolumn na sztywno (0,1,2,4,22..32); filtruje wiersze z `r[1] is None`; **Tkor, nie surowe D**; brak kontroli nagłówków |
| `_hampel_col(s)` | okno 21 centrowane, `NaN` gdy `|x−med|>3·1,4826·MAD` i `thr>0` | `min_periods=1` (okno skrajne = mniej próbek) |
| `smooth_bowl(d, offsets=OFFSETS_ALL, hampel=True) -> DataFrame` | (1) tylko pełne czasze (11 offsetów nie-NaN), (2) Hampel na D0 → odrzut **całej** czaszy, (3) średnia krocząca 21 (`min_periods=1`), kolumny = offsety (int) | wygładzanie po wierszach (przy nierównym kroku chainage okno się zniekształca; na początku pliku kroki 0,33/0,67/0,75); w oknie może zostać 1 czasza → wynik = ta jedna czasza |
| `convert_affine(value, ab) -> float\|None` | `max(0, a·value+b)`; `None`, gdy NaN/inf/None | ten sam (a,b) dla wszystkich offsetów, także ujemnych (ekstrapolacja: kalibracja tylko na 0…1500); `b` dodaje się nawet w polu dalekim |

**Wejścia/wyjścia:** czyta `.xlsx` (openpyxl read_only), nic nie zapisuje.

### 2.2 `tsd_to_xml.py` (procedura produkcyjna)

**Zależności:** `xlrd, openpyxl, numpy, pandas, tsd_pipeline, conversion_coeffs.json`.
**Stałe na sztywno:** `KOD_ODDZ="WA"`, `ROK="2026"`, `JEZDNIA="1"`, `PAS="1"`, `F_P="1.0"`, `KGF_TO_KN=9.80665/1000`, `XLS_HDR=60`, kolejność i nazwy w `DMAP`/`SLOPES` (kropka w `Slope 1.510 [µm/m]`), indeks `xrows[i][21]` (`T_XGB(120)`), `DROGA` z `SECTIONS`.

**Funkcje publiczne:**
- `_hmap(hdr) -> dict` (prywatna): nagłówek → indeks.
- `build_dane(xr, xm, conv, km, sci200, sci300, ustd, droga) -> list[(tag, str)]`: składa 43 pary w stałej kolejności (patrz mapowanie w sekcji 4).
- `convert_section(name) -> (temp_path, out_base)`: czyta `.xls` 1 m (xlrd; pola surowe), `.xlsx` 1 m (czasza Tkor + T_XGB), **zszywa po indeksie wiersza** (`n=min(len)`; sprawdzone: chainage w obu plikach identyczny co do 1e-15, ale brak kontroli w kodzie), wygładza, konwertuje, pisze `UC_*_temp.2026.xml` (1 rekord = 1 wiersz 1 m, wszystkie wiersze, także bez D).
- `sample_10m(temp_path, out_base) -> (final_path, kept)`: iterparse roboczego; zostawia rekordy, gdzie `DYSTANS % 10 == 0`; przepisuje elementy bez zmian (samo próbkowanie); zapis `UC_*.2026.xml`.
- `main()`: pętla po `SECTIONS`.

**Wyjście:** nadpisuje 6 plików XML w katalogu skryptu (UTF-8, LF, bez BOM, bez deklaracji przestrzeni nazw poza `xmlns:xsi`).

**Pułapki:**
- **Pikietaż:** `KM` liczone z `Chainage` (droga koła), nie z GPS; `DYSTANS = int(round(chainage))`. Dla pierwszego wiersza chainage jest ułamkowy (1,67/4,33/5,25), więc w pliku roboczym są **zdublowane DYSTANS** (np. 2,2; sprawdzone: 50_1M ma 1 duplikat różnic = 0), w finalnym duplikatów nie ma.
- **Kierunek:** `M` — KM maleje (48,082 → 39,932) przy rosnącym DYSTANS; `R` — rośnie. Rekordy w kolejności pomiaru (rosnący DYSTANS), nie rosnącego KM.
- **Zaokrąglenia:** KM `.3f` (=1 m), D/SCI/U_STD `.3f`, SLOPE `.4f`, LAT/LON `.6f`, IRI `.6f`, PREDKOSC `.6f`, STRAIN `.3f`, temperatury `.1f`, OBC_KN `.1f`. Zaokrąglenie dopiero w momencie zapisu; SCI liczone z niezaokrąglonych D (sprawdzone: |SCI−(D0−D200)| ≤ 0,0015).
- **Próbkowanie 10 m:** wartości są z **jednego wiersza 1 m** (D: średnia ±10 m wokół punktu, czyli okno 21 m, nie blok 10 m; IRI, prędkość, strain, temperatury, slope: pojedyncza próbka 1 m, bez uśredniania). IRI 1 m ma w pliku roboczym maksima 10–31 m/km (w finalnym 10–15 m/km) — wartości 1 m są bardzo zaszumione.
- **Puste D:** pojawiają się, gdy w oknie ±10 m nie ma żadnej pełnej czaszy (final: 3/816, 1/823, 0/586; temp: 32/8167, 9/8234, 7/5857). Wtedy cały blok D_* i SCI_*, U_STD jest `<TAG></TAG>`. Pola puste zapisywane jako `<TAG></TAG>` (nie `<TAG/>`).
- **Mapowanie kolumn zależy od nagłówka `.xls` w wierszu 60 i od kropki w Slope** — nie działa na eksporcie 10 m (nagłówek w wierszu 61, `Slope 1,510`).
- **Brak walidacji** zgodności długości `.xls`/`.xlsx`, brak obsługi braku kolumn (poza slope → `""`).
- **SCI/U_STD z wartości po konwersji afinicznej** → SCI skalowane przez `a` (0,85/0,47) i przycięte do ≥0 (README uznaje to za wadę dla SCI w analizie porównawczej, ale produkcja tak liczy).
- `T_DROGI_OBL` jest wstawiane w pętli przez ponowne mapowanie par; dla wiersza bez `T_XGB` → puste (1 przypadek w 50_1M temp).

### 2.3 `calibrate_conversion.py`

- Funkcje: `group_pairs(sections) -> (x, y)`; `__main__`: dla grup z `P.GROUPS` MNK `np.polyfit(x, y, 1)`, wypisuje a, b, R², r, n; **zapisuje (nadpisuje) `conversion_coeffs.json`**.
- Zależności: `scipy.spatial.cKDTree` (brak lokalnie), `tsd_pipeline`.
- Co liczy: pary (najbliższy punkt TSD w GPS po wygładzonej czaszy Tkor, wartość FWD znormalizowana 50 kN/20 °C) po wszystkich 8 dodatnich offsetach łącznie; jeden (a,b) na grupę (DK50: 2 odcinki; S8: 1).
- Pułapki: pojedynczy najbliższy punkt bez progu odległości (NaN odpadają `isfinite`); MNK z błędem w zmiennej niezależnej obniża `a` (S8 a=0,47); brak walidacji krzyżowej; kalibracja na `Tkor` (czyli już po korekcji temperaturowej BELLS3 k=0,02) — dla nowego wejścia d0 współczynniki **nie są przenośne**.

### 2.4 `compare_tsd_fwd.py` (cel dodatkowy)

- **Uwaga: kod wykonywany przy imporcie:** `DATA = {name: matched(name) ...}`, `YL = ...` na poziomie modułu — import = pełne obliczenia. `compare_sci_agg.py` robi `import compare_tsd_fwd as S`.
- Funkcje: `save(fig, fname)` (zapis do `_img/`, a przy błędzie do `/sessions/hopeful-great-noether/mnt/outputs`), `rval(a,b)`, `matched(name) -> DataFrame` (km, FWD_/TSD_ D0, SCI200, SCI300), `ylim0`, `profile_fig(metric)`, `scatter_fig()`, `scatter_all_fig()`.
- Co liczy: dla każdej stacji FWD wybiera w promieniu 5 m (KD-tree) punkt TSD o najmniejszej sumie kwadratów różnic na offsetach 0/200/300/450 względem FWD (osobno dla czaszy po afinicznej → D0, osobno dla surowej Tkor → SCI). **Wybór punktu po dopasowaniu wartości = optymistyczne r (selekcja po zmiennej objaśnianej)** — README to nazywa "maksymalną osiągalną zgodnością"; nie nadaje się do testów niezależnych.
- **Zapisuje** PNG do `_img/` — nie uruchamiać na tym katalogu.

### 2.5 `compare_sci_agg.py`

- Funkcje: `save`, `rval`, `agg(d, met, step)` (agregacja po koszykach `floor(km/step)·step+step/2`, `step` w km: 0,05 / 1,0), `section_fig(name)`; `__main__` drukuje r dla skal 1 m/50 m/1 km i zapisuje `sci_agg_<odc>.png`.
- Zależności: `matplotlib`, `compare_tsd_fwd` (import wykonuje całe matching).
- Pułapka: agregacja po `km` FWD (stacje co 25 m → "50 m" = 2 stacje, "1 km" = 40 stacji); dla `M` km malejące (sortowanie tylko w `load_fwd`).

### 2.6 `inject_dfwd.py` (jednorazowy)

- Funkcje: `read_xml(xml_f) -> {chainage_int: {tag: float|None}}`, `process(xml_f, xlsx_f) -> (nazwa, wypełnione, wierszy)`.
- Czyta finalny XML, ładuje oryginalny **10 m** `.xlsx` (openpyxl, pełny tryb) i wpisuje 11 kolumn `D*[µm]FWD` + `SCI300_FWD` (mapa `TAG2COL`) po kluczu `int(round(Chainage))`; wiersze bez rekordu XML dostają `None` (celowo przez `.value=None`); zapisuje `*_v2.xlsx` (nie nadpisuje źródła).
- Efekt: pierwszy wiersz (chainage 4,34/1,70/5,29 → klucz 4/2/5) nie ma pary w XML → pusty; wypełnionych 822/813/586 z 885/878/648 wierszy (reszta = puste wiersze ogonowe + pierwszy). **Zastępuje wcześniejsze, całkowite wartości `D*FWD`** (stare: liczby całkowite, być może z wcześniejszej konwersji; `BB_max` zostaje).
- Zależność: `openpyxl` (zapis z utratą części formatowania niewykluczona).

---

## 3. Struktura plików wejściowych

### 3.1 TSD — eksport 10 m, `T*.pgc.ibdim.xls` (xlrd; arkusz 1: `T…pgc.ibdim`)

- Preambuła (wiersze 0–59): `Headers`, `Assigner=IBDiM`, wersje DigiProf, `Equipment=DigiProf`, `Operator=JS`, nazwy plików pomiarowych; blok `Parameters` (wiersz 24+): `Result interval | 10.0 | m`, `Abs. deflektion | Positive`, `Goodness of fit limit | 0.15`, `Enable vertical slope shift | yes` (tylko w 10 m), `Model type | Asymmetrical model`; wiersz 60 = `Data`; **wiersz 61 = nagłówek**; dane od 62.
- 47 kolumn: `Chainage [m]`, `Latitude [dd.dddd]`, `Longitude [dd.dddd]`, `DateTime`, `Event`, `IRI1 [m/km]`, `Dr.Speed [m/s]`, `Strain Gauge Left [kg]`, `Strain Gauge Right [kg]`, `Temp Road [°C]`, `Temp Air [°C]`, `Slope 1,510 … -0,450 [µm/m]` (10, **przecinek**), `DoppDR … [#]` (11), `SCI200 [µm]`, `SCI300 [µm]`, `D-450 … D1500 [µm]` (11), `Status`, `Goodness of fit`.
- Wierszy danych: 824 / 817 / 587 (180001 / 180002 / 190001); `Status`: wszystkie `Ok` (jeden `No` w S8). Pierwszy wiersz chainage ≈ 4,34 / 1,70 / 5,29, potem 10, 20, 30 …
- Próbka (180001, wiersz 1): chainage 4,3367; lat 52,56402; lon 20,34381; IRI 0,694; v 20,41 m/s; Strain R 4891 kg; T road 26,53; T air 20,38; SCI200 16,72; SCI300 26,04; D0 207,86 µm.

### 3.2 TSD — eksport 1 m, `T*.pgc.ibdim_1m.xls`

- `Result interval | 1.0 | m`, `Goodness of fit limit | 0.5`; **nagłówek w wierszu 60** (0-based), dane od 61.
- 54 kolumny: jak wyżej, ale **bez SCI200/300**, z dodatkowymi `Temp Inside 8.4/3.4/0.5`, `Temp BeamHigh/BeamLow 3.4/2.2/0.5` (6 szt.) i `Slope 1.510 …` (**kropka**), `Strain Gauge Left/Right [kg]`, `DoppDR` (11), `D-450 … D1500 [µm]`, `Status`, `Goodness of fit`.
- Wierszy danych: 8234 / 8167 / 5857. Wiersze `Status=No` (GoF<0,5) mają **puste (`''`) wszystkie D**: Ok = 6505 / 4284 / 2819 (79% / 52% / 48%). IRI, strain, temperatury i slope są w 100% wierszy.
- Chainage: pierwszy ułamkowy, potem 5, 6, 7… (krok 1,000; na początku kroki 0,33–0,75).
- `Event`: 3 / 6 / 3 niepustych komórek: `'218.466_40'`, `'3208.012_43'`, `'6209.969_46'` (50_1R); `'91.830_48','1096.919_47','2097.827_46','3116.227_45','5389.618_42.7','6092.776_42'` (50_1M); `'1403.888_5.5','1895.549_6','5183.564_<Empty>'` (S8).
- Próbka (180001, wiersz 62): chainage 4,334; lat 52,56403; Dr.Speed 20,376 m/s; Strain R 4822,3 kg; T road 26,58; T air 20,38; Slope 1.510 = 65,06; `Status No`; GoF 0,286.

### 3.3 TSD — `.xlsx` 1 m (wejście czaszy, 48 kolumn, 1 arkusz)

Nagłówek w wierszu 1 (openpyxl `min_row=2`). Kolumny (0-based): 0 `Chainage [m]` | 1 `Latitude` | 2 `Longitude` | 3 `DateTime` | 4 `Event` | 5 `IRI1 [m/km]` | 6 `Strain Gauge Right [kg]` | 7 `Temp Road [°C]` | 8 `Temp Air [°C]` | 9–19 `D-450 … D1500 [µm]` (surowe) | 20 `Goodness of fit` | **21 `T_XGB(120)`** | **22–32 `D… [µm]Tkor`** | 33–43 `D… [µm]FWD` | 44 `SCI300_FWD` | 45 `BB_max` | 46 `Picture1` | 47 `Dr.Speed [m/s]`. **Brak kolumn Slope** (stąd konieczność łączenia z `.xls`).
- Wierszy danych: 8234 / 8167 (ostatni wiersz bez chainage i bez T_XGB) / 5857.
- `D…Tkor` i `D…FWD`, `SCI300_FWD`, `BB_max` w pliku 1 m: **liczby całkowite**; `T_XGB(120)` w 1 m: rozdzielczość 0,1 °C (np. 17,9; 18,0; 18,6).
- Zgodność z `.xls` 1 m: chainage, lat, strain, temperatury, IRI, speed, D0 — identyczne do ~1e-13 (wiersz po wierszu).

### 3.4 TSD — `.xlsx` 10 m i `_v2.xlsx`

Identyczny układ 48 kolumn jak 3.3 (nazwy kolumn te same), ale: `Tkor` z **2 miejscami** (np. 214,22), `T_XGB(120)` z 2 miejscami (20,55), 885 / 878 / 648 wierszy (z tego 61 / 61 / 61 pustych na końcu — `len(row)==0`), `D*FWD` = liczby całkowite (stare, ręczne/wcześniejsze), `BB_max` całkowite. `_v2`: `D*FWD` i `SCI300_FWD` wypełnione z XML (float, 3 miejsca).
- Dowód uniwersalności Tkor w pliku 10 m: iloraz `Tkor/D` jest **taki sam dla wszystkich offsetów** w wierszu (maks. różnica 0,0003–0,0005), czyli korekcja = pojedynczy mnożnik na czaszę. W pliku 1 m, ze względu na zaokrąglenie do całkowitych, ten iloraz jest zaszumiony (maks. różnica do 0,37).

### 3.5 FWD — `Drops*.xlsx` (arkusz `Drops`) i `stations*.xlsx` (arkusz `Stations`)

`Drops` (24 kolumny): `StationID, DropID, History(True), DateTime (Excel serial, np. 46161,4430 = 2026-05-18), Asphalt [°C], Surface [°C], Air [°C], Stress [kPa], Force [kN], D1 … D15 [µm]` (D1–D9 wartości, D10–D15 = 0).
- Liczba zrzutów: 242 (121 stacji × 2) dla 50_1M i 50_1R; 274 (137 × 2) dla S8. Zawsze 2 zrzuty na stację; różnice 1. vs 2.: iloraz D1 średnio 1,001–1,006.
- `Asphalt`: stały 18,0 (DK50) / 20,0 (S8); pierwsza stacja ma sentinel **−3,4028e38** (50_1R, S8: 2 zrzuty); `Surface` 18,3–29,0 (50_1R: 21,7–29,0; S8: 19,4–39,4); `Air` = 20,4 stałe; `Stress` 666–713 kPa; `Force` 47,06–50,42 kN.
- Próbka (50_1M, st. 1, drop 1): Asphalt 18,0; Surface 18,4; Force 49,34; D1…D9 = 168,8 / 156,6 / 146,8 / 138,2 / 127,4 / 106,1 / 89,2 / 73,5 / 59,2.
`Stations` (24 kolumny): `SessionID, StationID, Station (km, float32), StationUnit (0), StationDirection (±1), Lane…SlabPositionCode (puste/0), AsphaltTemperature, SurfaceTemperature, AirTemperature, Cracks, Time (Excel serial), GPSStatus, Satellites, UTC (hhmmss), Latitude, Longitude, Height, Comment`.
- Zakresy km: 50_1M 46,000 → 43,000 (malejące, `StationDirection` −1 poza 1. stacją = +1), 50_1R 43,000 → 46,000, S8 6,000 → 9,400; krok 25 m; GPSStatus 1 (S8: jedna stacja 0), liczba satelitów min 3–5.
- **FWD pokrywa tylko część odcinka TSD:** 3 km z 8,2 km (DK50), 3,4 km z 5,9 km (S8).
- D1…D8 ↔ offsety 0/200/300/450/600/900/1200/1500 mm — mapowanie z kodu (`FWD_DCOL`), nie z pliku.

---

## 4. Pełne MAPOWANIE: pole XML ← kolumna źródłowa ← jednostka ← przeliczenie

Oznaczenia kolumny "N3": **K** = da się zachować wprost (ta sama logika/źródło), **P** = pochodne/stałe konfiguracyjne (trzymać jako parametr), **R** = trzeba obliczyć z d0/P0 zamiast 'D Tkor', **?** = wymaga decyzji autora.

Źródła: `xls1m` = `T*.pgc.ibdim_1m.xls`; `xlsx1m` = `T*.pgc.ibdim_1m.xlsx`. Format = sposób zapisu w XML (precyzja potwierdzona na plikach).

| # | Pole XML | Kolumna źródłowa | Jednostka źródła → XML | Przeliczenie / format | N3 |
|---|---|---|---|---|---|
| 1 | `KM` | `xls1m.Event` (tokeny `chain_km`) + `Chainage [m]` | m, km → **km** | `(km0 + sign·(chain − c0))/1000`; 3 miejsca; kotwica = 1. marker | K (logika), ? (pikietaż z sieci) |
| 2 | `DYSTANS` | `Chainage [m]` | m → **m** (liczba całk.) | `int(round(chain))`; final: tylko `%10==0` (10, 20 …) | K |
| 3 | `DROGA` | stałe w `SECTIONS` (`50`, `S8l`) | tekst | — | P |
| 4 | `JEZDNIA` | stałe `"1"` | — | — | P |
| 5 | `PAS` | stałe `"1"` | — | — | P |
| 6 | `LAT` | `Latitude [dd.dddd]` | ° → ° | `.6f` (1 m, bez wygładzania) | K |
| 7 | `LON` | `Longitude [dd.dddd]` | ° → ° | `.6f` | K |
| 8 | `DATA` | `DateTime` (tekst) | `YYYY-MM-DD` | split po spacji | K |
| 9 | `GODZ` | `DateTime` | `HH:MM:SS` | split | K |
| 10 | `IRI_1` | `IRI1 [m/km]` | m/km → m/km | `.6f`, próbka 1 m | K |
| 11 | `PROFIL_1` | — (`Profile=no`) | — | zawsze puste `<PROFIL_1></PROFIL_1>` | K |
| 12 | `PREDKOSC` | `Dr.Speed [m/s]` | m/s → **km/h** | `·3,6`, `.6f` | K |
| 13 | `STRAIN_GAUGE` | `Strain Gauge Right [kg]` | kg → kg | `.3f` (surowe; lewy tensometr pominięty) | K |
| 14 | `T_DROGI` | `Temp Road [°C]` | °C → °C | `.1f`, próbka 1 m (czujnik IR) | K |
| 15 | `T_DROGI_OBL` | **`xlsx1m` kol. 21 `T_XGB(120)`** | °C → °C | `.1f`; indeks na sztywno; w pliku 10 m wartości inne (patrz sekcja 6) | K / ? |
| 16 | `T_POW` | `Temp Air [°C]` | °C → °C | `.1f` | K |
| 17 | `F_P` | stała `"1.0"` | — | — | P |
| 18 | `OBC_KN` | `Strain Gauge Right [kg]` | kg → **kN** | `·9,80665/1000`, `.1f` | K (do potwierdzenia fizycznego) |
| 19 | `OBC_KPA` | — | — | zawsze puste | K |
| 20 | `SCI_200` | (pochodne) | µm → µm | `D0c − D200c`, `.3f`, z wartości po afinicznej; puste gdy brak czaszy | **R** |
| 21 | `SCI_300` | (pochodne) | µm | `D0c − D300c` | **R** |
| 22 | `U_STD` | (pochodne) | µm | = `D0c` (po wygładzeniu i afinicznej); w dok. UC: D0 skorygowane temp. do 20 °C | **R** (+ ?) |
| 23 | `D_minus_450` | `xlsx1m` kol. 22 `D-450 [µm]Tkor` | µm → µm | Hampel(D0)+roll 21 → `max(0,a·T+b)`, `.3f` | **R** |
| 24 | `D_minus_300` | kol. 23 | µm | j.w. | **R** |
| 25 | `D_minus_200` | kol. 24 | µm | j.w. | **R** |
| 26 | `D_0` | kol. 25 `D0 [µm]Tkor` | µm | j.w. | **R** |
| 27 | `D_200` | kol. 26 | µm | j.w. | **R** |
| 28 | `D_300` | kol. 27 | µm | j.w. | **R** |
| 29 | `D_450` | kol. 28 | µm | j.w. | **R** |
| 30 | `D_600` | kol. 29 | µm | j.w. | **R** |
| 31 | `D_900` | kol. 30 | µm | j.w. | **R** |
| 32 | `D_1200` | kol. 31 | µm | j.w. | **R** |
| 33 | `D_1500` | kol. 32 | µm | j.w. | **R** |
| 34 | `SLOPE_1_510` | `xls1m.Slope 1.510 [µm/m]` | µm/m → µm/m | `.4f`, surowa próbka 1 m | K |
| 35 | `SLOPE_0_910` | `Slope 0.910 [µm/m]` | µm/m | j.w. | K |
| 36 | `SLOPE_0_610` | `Slope 0.610` | µm/m | j.w. | K |
| 37 | `SLOPE_0_460` | `Slope 0.460` | µm/m | j.w. | K |
| 38 | `SLOPE_0_310` | `Slope 0.310` | µm/m | j.w. | K |
| 39 | `SLOPE_0_210` | `Slope 0.210` | µm/m | j.w. | K |
| 40 | `SLOPE_0_110` | `Slope 0.110` | µm/m | j.w. | K |
| 41 | `SLOPE_minus_0_200` | `Slope -0.200` | µm/m | j.w. | K |
| 42 | `SLOPE_minus_0_300` | `Slope -0.300` | µm/m | j.w. | K |
| 43 | `SLOPE_minus_0_450` | `Slope -0.450` | µm/m | j.w. | K |

Atrybuty korzenia: `KOD_ODDZ="WA"` (stała; w przykładzie z dokumentu "OP"), `ROK="2026"` (stała), `xsi:noNamespaceSchemaLocation="UC_Schema.xsd"`.

**Pola, które nowe narzędzie musi policzyć z d0/P0 zamiast 'D Tkor' (R):** `D_minus_450 … D_1500` (11), `SCI_200`, `SCI_300`, `U_STD` (14 pól).
**Pola do wprost zachowania (K) lub konfiguracyjne (P):** pozostałe 29 (KM, DYSTANS, DROGA, JEZDNIA, PAS, LAT, LON, DATA, GODZ, IRI_1, PROFIL_1, PREDKOSC, STRAIN_GAUGE, T_DROGI, T_DROGI_OBL, T_POW, F_P, OBC_KN, OBC_KPA, 10×SLOPE).

Dodatkowe uwagi do mapowania:
- Jeśli nowy układ liczy D_* z `d0` i całek nachyleń, to wszystkie 11 pozycji dostaje się z tej samej procedury, a `SLOPE_*` (surowe nachylenia z `.xls`) zostają bez zmian (sprawdzone: XML = źródło 1 m w 100%).
- `D_*` w XML (po afinicznej) są dziś **w skali FWD** (przeliczone na ekwiwalent FWD 50 kN/20 °C), a nie "ugięcia TSD". Dokument formatu nie mówi, w jakiej skali mają być D_* (tylko `U_STD` = standaryzowane).
- Nazwy tagów (43) i ich kolejność są **identyczne** w dokumencie i w XML (sprawdzone programowo).

---

## 5. Format UC — dokument i pliki przykładowe

### 5.1 `format pliku UC.docx`

Jedna tabela 1x1 z nagłówkiem "Przykład fragmentu pliku z danymi — Ugięcia (pomiar mobilny)" i fragmentem XML (jeden `DANE`) z komentarzami `<!-- … -->` po polsku. Brak opisu typów, zakresów, jednostek (poza `[µm/m]` w komentarzach slope) i brak obowiązkowości poza uwagami "dana opcjonalna" (IRI_1, PROFIL_1, STRAIN_GAUGE). Wartości przykładu: KM 100.010, DYSTANS 1, DROGA 1, JEZDNIA 1, PAS 1, LAT 52.221502, LON 21.079828, DATA 2026-04-20, GODZ 12:00:00, IRI_1 2.778105, PROFIL_1 2.584106, PREDKOSC 53.660124, STRAIN_GAUGE 5308.978, T_DROGI 28.5, T_DROGI_OBL 19.5, T_POW 20.6, F_P 1.0 (współczynnik podbudowy), OBC_KN 52.3, OBC_KPA 720, SCI_200 42.928, SCI_300 70.13, U_STD 124.215, D_minus_450 54.578 … D_1500 10.613, slope jak w tabeli. Root: `<UC xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" KOD_ODDZ="OP" ROK="2025" xsi:noNamespaceSchemaLocation="UC_Schema.xsd">`; dokument przykładowy ma `ROK="2025"` przy `DATA 2026-04-20` (przykład ilustracyjny).

**Weryfikacja arytmetyczna przykładu (moje obliczenia):**
- `SCI_200 = D_0 − D_200` = 122,986 − 80,058 = 42,928 ✓; `SCI_300` = 122,986 − 52,856 = 70,130 ✓ (czyli SCI na nieskorygowanych D).
- `U_STD / D_0` = 1,009993 ≈ `1 + 0,02·(20 − 19,5)` = 1,01 ✓ (U_STD = 124,2159 z D_0 = 122,986).
- Obciążenie 52,3 kN nie wpływa (50/52,3 = 0,956 ≠ 1,010).
- Zapis liczb w przykładzie nie ma stałej liczby miejsc (`70.13`, `720`); pliki produkcyjne mają stałe precyzje (patrz tabela).
- DYSTANS=1 przy KM=100.010 sugeruje (hipoteza) numer 10-metrowego kroku od km 100.000, a nie metry; plik produkcyjny wypisuje metry (10, 20, …) — niejednoznaczne.

### 5.2 `UC_*_2026.xml` (finalne, 10 m) — statystyki

| Plik | Rekordów | DYSTANS | KM | Puste D/SCI/U_STD | DATA | GODZ (pierwsza/ostatnia) | DROGA |
|---|---|---|---|---|---|---|---|
| `UC_50_1_M_1.2026.xml` | 816 | 10 … 8160 (krok 10, 815×) | 48,082 → 39,932 (krok −0,010, 815×) | 3 | 2026-05-18 | 13:26:05 / 13:33:04 | 50 |
| `UC_50_1_R_1.2026.xml` | 823 | 10 … 8230 | 39,792 → 48,012 (+0,010) | 1 | 2026-05-18 | 13:07:58 / 13:14:50 | 50 |
| `UC_S8l_1_R_1.2026.xml` | 586 | 10 … 5860 | 4,106 → 9,956 (+0,010) | 0 | 2026-05-19 | 11:17:25 / 11:22:05 | S8l |

Wspólne: 43 elementów `DANE` w stałej kolejności; `PROFIL_1` i `OBC_KPA` zawsze puste; `F_P=1.0`, `JEZDNIA=1`, `PAS=1`; 0 niemonotonicznych czasz po stronie dodatniej offsetów; 0 ujemnych D; `U_STD == D_0` we wszystkich rekordach; plik ASCII, UTF-8 (deklaracja), końce linii LF, wcięcia 4/8 spacji, brak BOM, ostatni znak `\n`, puste elementy `<TAG></TAG>`; atrybuty korzenia w osobnych liniach. Brak przestrzeni nazw domyślnej; jedyna deklaracja: `xmlns:xsi`. Zakresy (50_1M): D_0 57,5–482,0 µm; SCI_200 2,5–144,2; T_DROGI_OBL 19,5–22,2; OBC_KN 38,7–59,4; PREDKOSC 56,9–75,6 km/h.

### 5.3 `UC_*_temp.2026.xml` (robocze, 1 m)

Ta sama struktura i te same 43 tagi; rekordów: **8167 / 8234 / 5857** (= liczba wierszy `.xls` 1 m, 1:1, także dla wierszy bez D); DYSTANS od 2 / 4 / 5 (zaokrąglony ułamkowy chainage), krok 1 (jedna powtórka w 50_1M: 2, 2); KM co 0,001; puste D/SCI/U_STD w 32 / 9 / 7 rekordach (miejsca bez pełnej czaszy w oknie ±10 m); `T_DROGI_OBL` puste w 1 rekordzie 50_1M (ostatni wiersz bez T_XGB). Ostatni rekord DYSTANS=8167/8237/5861. Rozmiar 9–13 MB. Służy tylko jako etap pośredni do `sample_10m` (README: "XML roboczy").

---

## 6. Temperatura w procedurze

1. **Ugięcia:** brak jawnej korekcji temperaturowej w kodzie `tsd_2_xml` — korekcja jest już wykonana poza katalogiem w kolumnach `D… [µm]Tkor` (BELLS3_BT, k=0,02 wg opisu użytkownika). Na wejściu do kodu to są liczby całkowite (1 m) lub 2 miejsca (10 m).
2. **`T_DROGI`** ← `Temp Road [°C]` (czujnik na belce/IR, temp. powierzchni; 1 m, `.1f`).
3. **`T_POW`** ← `Temp Air [°C]`.
4. **`T_DROGI_OBL`** ← `xlsx1m` kol. 21 **`T_XGB(120)`** (nazwa sugeruje model XGBoost, głębokość 120 mm — nigdzie w katalogu nie opisane, hipoteza). W 1 m wartości ze skokami po 0,1 °C (powtarzane, np. 18,0 przez wiele wierszy). Dla 3 odcinków: średnie 18,47 / 20,96 / 16,13 °C (w UC finalnych).
5. **Kolumny temperatur nieużywane**: `Temp Inside 8.4/3.4/0.5` i `Temp BeamHigh/Low 3.4/2.2/0.5` w `xls1m` (6+3 kolumn z czujników wewnątrz belki).
6. **Rozjazd 10 m vs 1 m:** `T_XGB(120)` w `.xlsx` 10 m vs 1 m w punktach co 10 m: różnica (10m−1m) średnio **+0,82 °C** (50_1M, zakres −0,48…+2,24), **+2,56 °C** (50_1R, +0,89…+3,46), +0,05 °C (S8, −1,55…+2,45). Czyli ta sama kolumna ma różne wartości zależnie od wersji eksportu; XML bierze wersję 1 m.
7. **Temperatura efektywna ukryta w Tkor** (moja rekonstrukcja z `T_eff = 20 − (Tkor/D − 1)/0,02`, plik 10 m): średnia T_eff vs średnia T_XGB w pliku 10 m (kolejność 50_1R / 50_1M / S8): 21,03 vs 21,03; 22,36 vs 21,78; 18,08 vs 16,19 (czyli równe tylko w 50_1R, różnica 0,6 i 1,9 °C w pozostałych), lecz w wierszach różnica T_eff − T_XGB ma odch. std. 1,56 / 1,44 / 0,55 °C, a regresja T_eff na T_XGB daje nachylenie 1,1–1,3. Wniosek: Tkor nie jest prostą funkcją `T_XGB(120)` z tego samego wiersza (zgodnie z informacją, że używano BELLS3_BT).
8. **FWD:** temperatura asfaltu `Asphalt` z `Drops` (fallback `AsphaltTemperature`), stała dla odcinka (18 / 18 / 20 °C), współczynnik `1+0,02(20−T)` (czyli 1,04 / 1,04 / 1,00). `Surface` nieużywane.
9. **W XML** temperatura występuje tylko jako 3 pola informacyjne (T_DROGI, T_DROGI_OBL, T_POW); z dokumentu wynika, że `T_DROGI_OBL` jest potrzebne do standaryzacji `U_STD` (patrz sekcja 5.1).

---

## 7. Przepływ i konwencje (podsumowanie)

`T*_1m.xls` (surowe: slope, IRI, prędkość, tensometr, temp., GPS, Event) + `T*_1m.xlsx` (czasza Tkor, T_XGB) → `smooth_bowl` (pełne czasze → Hampel D0 → rolling 21) → `convert_affine(a,b)` (DK50/S8) → SCI/U_STD z wartości po konwersji → `UC_*_temp.2026.xml` (1 m) → `sample_10m` (DYSTANS%10==0) → `UC_*.2026.xml`. Dodatkowo: `calibrate_conversion` (GPS-nearest, MNK) i `compare_*` (analiza), `inject_dfwd` (wpis D*FWD do `_v2.xlsx`).

Jawne uwagi o spójności dokumentacji i kodu:
- README: "SCI_200 = D0−D200 (z ugięć przeliczonych)" = kod; jednocześnie w analizie porównawczej SCI liczone wprost z Tkor — w produkcji i w analizie liczone są dwa różne SCI.
- README mówi "Wejście: pliki 1 m (para xls+xlsx)" — para musi mieć identyczną liczbę wierszy (nie jest to sprawdzane).
- `README`: "puste tylko w realnych lukach (≈0–4/plik)" — zgodne (0–3).
- README podaje a,b tak samo jak JSON.

---

## 8. Wnioski dla projektu (N3 `tsd_network`, N1 korekta FWD)

### 8.1 Moduł eksportu XML (`tsdfwd_tools` — np. `uc_export.py`)

- **Oddzielić** eksport od obliczeń: funkcja `write_uc_xml(path, records, kod_oddz, rok, schema_location="UC_Schema.xsd")` + deklaratywna tabela pól (`tag`, `dtype`, `decimals`, `required`) — kolejność 43 tagów jak w tabeli z sekcji 4 (identyczna z dokumentem).
- `records` jako lista dict/DataFrame z kolumnami o nazwach tagów (np. `D_0`, `SLOPE_1_510`), NaN/None → pusty element `<TAG></TAG>`; nigdy "nan" (w `fnum` NaN daje "nan"!).
- Zachować: UTF-8 bez BOM, LF, wcięcia 4/8, atrybuty korzenia w osobnych liniach (przy ET użyć `short_empty_elements=False`, inaczej `<PROFIL_1 />`), precyzje: KM 3, DYSTANS 0, LAT/LON 6, IRI 6, PREDKOSC 6, STRAIN 3, T_* 1, F_P "1.0", OBC_KN 1, SCI/U_STD/D_* 3, SLOPE 4.
- Parametry konfiguracyjne (nie na sztywno): `KOD_ODDZ`, `ROK`, `DROGA`, `JEZDNIA`, `PAS`, `F_P`, kierunek (rosnące/malejące km), krok (10 m), kotwice pikietażu.
- Kolejność rekordów: rosnący DYSTANS (kolejność pomiaru), KM malejące dla kierunku malejącego — zachować i ustalić z autorem.
- Pikietaż: zamiast kotwicy z 1. markera lepsza interpolacja **odcinkowa** między kolejnymi markerami `Event` (błąd dryfu do 24 m na 50_1M) — ale to zmiana względem wzorca; zrobić jako opcja, domyślnie zachować zachowanie referencyjne dla testu porównawczego.
- Czytnik wejścia: wykrywać wiersz nagłówka po `Chainage [m]` (60 vs 61), normalizować nazwy `Slope 1,510` ↔ `Slope 1.510`, ignorować puste wiersze ogonowe `.xlsx`, mapować kolumny po nagłówkach (nie po indeksach 21/22–32), sprawdzać zgodność chainage `.xls`/`.xlsx` zamiast zszywać po indeksie.
- Zależności: tylko `numpy/pandas` + czytnik xls(x). Lokalnie dostępne: `xlrd`, `pandas`, `numpy`; `openpyxl`, `scipy`, `matplotlib` trzeba dodać do `pyproject` (lub zastąpić `scipy.cKDTree` czymś lokalnym).
- Nie przenosić do N3: `calibrate_conversion`/`conversion_coeffs.json` (kalibracja na Tkor), `compare_*` (selekcja punktów po wartości), `inject_dfwd`.

### 8.2 Test porównawczy struktury z `UC_*.xml` (golden-structure test)

Automatyczny test pary (plik wygenerowany ↔ `UC_50_1_M_1.2026.xml` jako wzorzec struktury), niezależny od wartości:
1. root = `UC`, atrybuty `KOD_ODDZ`, `ROK`, `xsi:noNamespaceSchemaLocation="UC_Schema.xsd"`, deklaracja `xmlns:xsi`; brak innych przestrzeni nazw.
2. wszystkie dzieci root = `DANE`; w każdym `DANE` dokładnie 43 elementy w kolejności wzorca (lista z sekcji 4).
3. format wartości wg tagu (regex + liczba miejsc): KM `\d+\.\d{3}`, DYSTANS `\d+`, LAT/LON `\d+\.\d{6}`, DATA `YYYY-MM-DD`, GODZ `HH:MM:SS`, T_* `-?\d+\.\d`, F_P `1.0`, SLOPE `-?\d+\.\d{4}`, D/SCI/U_STD `\d+\.\d{3}`.
4. puste dozwolone tylko: `PROFIL_1`, `OBC_KPA` oraz blok D_*/SCI_*/U_STD (cały naraz, albo cały zapełniony).
5. DYSTANS rosnący, krok 10 (dla pliku 10 m) bez duplikatów; |ΔKM| = 0,010 ze stałym znakiem; `KM` zgodne z kierunkiem.
6. fizyka: D_0 ≥ D_200 ≥ … ≥ D_1500 > 0; D_minus_* < D_0 (z wyjątkiem przypadków asymetrii); `|SCI_200 − (D_0 − D_200)| ≤ 0,0015`; `U_STD` zgodne z definicją przyjętą z autorem.
7. kodowanie: UTF-8 bez BOM, LF, `<TAG></TAG>` dla pustych.
8. (opcjonalnie) walidacja XSD, gdy autor dostarczy `UC_Schema.xsd`.
9. test regresji liczbowej na polach K (IRI, PREDKOSC, STRAIN, T_*, OBC_KN, LAT/LON, DATA/GODZ, SLOPE, KM, DYSTANS) dla 3 odcinków: wygenerowane z N3 = `UC_*.2026.xml` co do znaku (te pola zgadzają się ze źródłem w 100%, więc N3 powinien dać identyczne wartości). Pola D/SCI/U_STD — tylko test fizyczny (z definicji różne).

### 8.3 Pytania do autora

1. **Czym jest `P0` ("całki nachyleń")?** W żadnym pliku w katalogu nie ma takiej kolumny. Czy to całka ∑slope·Δx od x=0 (do D_x), z jakiego pliku/kolumny, w jakich jednostkach (µm? µm/m·m?), i jak z `d0` i `P0` mają być wyznaczone D_−450…D_1500 (11 pozycji)? Czy `d0` = surowe `D0 [µm]` z DigiProf (jest w `.xls` 1 m i 10 m)?
2. **`U_STD` — definicja:** zgodnie z przykładem w dokumencie UC U_STD = D_0·(1+0,02·(20−T_DROGI_OBL)) (bez normalizacji obciążenia) i D_* są nieskorygowane; obecna procedura daje U_STD = D_0 (po Tkor + afinicznej). Co ma zawierać N3 w D_* (surowe TSD, TSD skorygowane, ekwiwalent FWD)? Jaka temperatura (T_XGB(120), T_DROGI_OBL z modelu, BELLS3_BT) i jakie k wchodzą do U_STD?
3. **`T_DROGI_OBL`:** co to jest `T_XGB(120)` (model, głębokość, krok czasowy) i dlaczego wartości w plikach 10 m i 1 m różnią się (0–3,5 °C)? Którą wersję przyjąć w N3? Czy BELLS3_BT temperatury ma być dostępna w nowym wejściu?
4. **`DYSTANS`:** metry od początku nagrania (jak w produkcji: 10, 20, …) czy numer kroku (jak sugeruje przykład: DYSTANS=1 przy KM=100.010)? Czy ma być od 0/10 od początku odcinka diagnostycznego czy od startu pliku TSD?
5. **Pikietaż `KM`:** kotwica z 1. markera `Event` (obecnie) vs interpolacja po markerach vs km z sieci (N3 "sieć" — czy węzły/odcinki mają własną pikietaż?); precyzja KM (3 miejsca = 1 m); co zrobić, gdy brak markerów/gdy jest jeden marker?
6. **Stałe w XML:** `KOD_ODDZ` (WA vs OP w przykładzie), `ROK` (rok pomiaru czy raportu), `F_P=1.0`, `JEZDNIA`, `PAS`, `DROGA` (`50`, `S8l` — jaki słownik/format); czy ma być `OBC_KPA` i `PROFIL_1` (obecnie puste)? Czy `OBC_KN` = prawy tensometr kg·g (bez lewego) jest poprawnym przeliczeniem?
7. **Dostęp do `UC_Schema.xsd`** (wymagania obowiązkowości/typy/zakresy; czy puste elementy są dopuszczalne w D_*).
8. **Krok i agregacja:** w finalnym XML wartości są z pojedynczego wiersza 1 m (IRI, prędkość, slope, temperatury) i średniej ±10 m dla D. Czy N3 ma uśredniać pozostałe pola do 10 m, czy zostawić próbkę? Czy IRI ma być na bazie 1 m (maks. do 31 m/km w pliku 1 m) czy na dłuższej bazie?
9. **Eksport 10 m vs 1 m:** który eksport jest wejściem N3 (10 m ma `SCI200/300` z DigiProf i GoF 0,15, 1 m — GoF 0,5, 48–79% zapełnienia D)? Czy N3 przejmuje wiersze `Status=No` (puste D)?
10. **FWD (N1):** czy temperatura asfaltu stała dla całego odcinka (18/18/20 °C) jest zamierzona (wpis ręczny)? Sentinel −3,4e38 w `Drops.Asphalt` pierwszej stacji — traktować jako brak (obecnie tak i fallback na stations). Czy D9 (poza 1500 mm) ma być używane (jaka pozycja)? Czy zawsze brać 2-gi zrzut? Czy `StationDirection` ma wpływ na pikietaż?
11. Kolumny `D*FWD`, `SCI300_FWD`, `BB_max` w `.xlsx` 10/1 m (całkowite) — skąd (stara funkcja? BB = belka Benkelmana?) i czy mają być zachowane przy eksporcie `_v2`.
12. `compare_tsd_fwd`: czy dopasowanie "value ±5 m" (wybór najlepszego punktu po wartościach) ma pozostać jedynie w analizie dodatkowej? (Jest optymistyczne.)
13. Czy N3 ma obsługiwać cały zbiór (wiele odcinków/kierunków) i czy `GROUPS` (DK50/S8) mają być w konfiguracji (JSON) zamiast w kodzie?

### 8.4 Ryzyka do uwzględnienia w implementacji

- Brak openpyxl/scipy/matplotlib lokalnie (3.13) — test środowiska przed uruchomieniem.
- Skrypty zapisują do katalogu roboczego (XML, JSON, PNG); w N3 ścieżki wyjściowe jako argument.
- `compare_tsd_fwd` wykonuje obliczenia przy imporcie.
- Okno `WIN=21` zależy od kroku 1 m — przy eksporcie 10 m nie ma sensu; N3 powinien definiować okno w metrach po chainage.
- Dla NaN w polach stosować `""`, nie `fnum(nan)`.
- Tkor 1 m ma 5–16% utraconych czasz przez zaokrąglenie — nowe wejście d0/P0 nie powinno tej utraty powielać; rozważyć, czy nadal wymagać "pełnej czaszy".
