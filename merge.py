"""
Skrypt do scalania danych bezrobociai ludnosci z pliku CSV.

Logika:
- Zachowuje wiersze dla całej Polski, województw i powiatów bez zmian.
- Dla gmin (poziom gminy):
    * Usuwa wiersze typów 4 i 5 (podział na miasto / obszar wiejski).
    * Scala wiersze tej samej gminy, które zmieniły typ (np. (1) → (3)):
      identyfikowane po pierwszych 6 cyfrach kodu — bierze pierwszą
      niepustą wartość dla każdego roku (chronologicznie według kolejności
      w pliku).
    * Z nazwy gminy usuwa przyrostek „(N)".

Użycie:
    python merge_bezrobocie.py input.csv output.csv

Domyślne ścieżki (gdy nie podano argumentów):
    input  → bezrobocie.csv
    output → bezrobocie_merged.csv
"""

import sys
import re
import pandas as pd

# ── konfiguracja ────────────────────────────────────────────────────────────

INPUT_FILE  = sys.argv[1] 
OUTPUT_FILE = sys.argv[2] 

# Kodowania do próby (GUS-owe pliki bywają w cp1250 lub utf-8-sig)
ENCODINGS = ["cp1250", "utf-8-sig", "utf-8", "iso-8859-2"]

# ── wczytanie ────────────────────────────────────────────────────────────────

def load_csv(path: str) -> pd.DataFrame:
    for enc in ENCODINGS:
        try:
            df = pd.read_csv(path, sep=";", encoding=enc, dtype=str)
            # Usuń kolumny z samymi NaN (artefakt końcowego średnika w wierszach)
            df = df.dropna(axis=1, how="all")
            df = df.loc[:, ~df.columns.str.match(r"^Unnamed")]
            print(f"  Wczytano plik ({enc}): {df.shape[0]} wierszy, {df.shape[1]} kolumn")
            return df
        except (UnicodeDecodeError, Exception):
            continue
    raise ValueError(f"Nie udało się wczytać pliku '{path}' żadnym ze znanych kodowań.")


# ── klasyfikacja kodu ─────────────────────────────────────────────────────────

def classify_code(raw_code: str) -> str:
    """
    Zwraca typ wiersza na podstawie kodu GUS:
      'polska'      → 0000000
      'voivodeship' → XX00000
      'powiat'      → XXYYY000
      'gmina'       → XXYYYGGGT (T = 1,2,3)
      'gmina_split' → XXYYYGGGT (T = 4 lub 5) — do usunięcia
    """
    code = str(raw_code).strip().zfill(7)
    if code == "0000000":
        return "polska"
    if code[2:] == "00000":
        return "voivodeship"
    if code[4:] == "000":
        return "powiat"
    typ = code[-1]
    if typ in ("4", "5"):
        return "gmina_split"
    return "gmina"


def base_gmina_code(raw_code: str) -> str:
    """Pierwsze 6 cyfr kodu — identyfikator gminy niezależny od typu."""
    return str(raw_code).strip().zfill(7)[:6]


def strip_type_suffix(name: str) -> str:
    """Usuwa przyrostek „(N)" z końca nazwy gminy."""
    return re.sub(r"\s*\(\d+\)\s*$", "", str(name)).strip()


# ── scalanie gmin ─────────────────────────────────────────────────────────────

def is_empty(val) -> bool:
    """Zwraca True jeśli wartość jest pusta (NaN, pusty string, tylko spacje)."""
    if val is None:
        return True
    if isinstance(val, float) and pd.isna(val):
        return True
    return str(val).strip() == ""


def merge_gmina_group(group: pd.DataFrame, year_cols: list) -> pd.Series:
    """
    Scala grupę wierszy tej samej gminy (różne typy historyczne).
    Dla każdego roku bierze pierwszą niepustą wartość w kolejności wierszy
    (starszy typ wcześniej — zakładamy, że plik jest posortowany wg kodu).
    Działa zarówno z liczbami całkowitymi, jak i zmiennoprzecinkowymi z
    przecinkiem dziesiętnym (format GUS).
    """
    merged = group.iloc[0].copy()

    # Wyczyść nazwę — usuń przyrostek (N)
    merged["Nazwa"] = strip_type_suffix(merged["Nazwa"])

    for col in year_cols:
        merged[col] = ""
        for val in group[col]:
            if not is_empty(val):
                merged[col] = str(val).strip()
                break  # bierzemy pierwszą niepustą wartość

    return merged


# ── główna logika ─────────────────────────────────────────────────────────────

def process(df: pd.DataFrame) -> pd.DataFrame:
    year_cols = [c for c in df.columns if c not in ("Kod", "Nazwa")]

    # Dodaj kolumny pomocnicze
    df = df.copy()
    df["_type"]      = df["Kod"].apply(classify_code)
    df["_base_code"] = df["Kod"].apply(base_gmina_code)

    # ── 1. wiersze niebędące gminami — zachowaj bez zmian ──────────────────
    non_gmina_mask = df["_type"].isin(("polska", "voivodeship", "powiat"))
    non_gmina = df[non_gmina_mask].copy()

    # ── 2. usuń typy 4 i 5 (miasto / obszar wiejski) ───────────────────────
    gmina_df = df[df["_type"] == "gmina"].copy()

    print(f"\n  Wiersze przed scaleniem:")
    print(f"    Polska + województwa + powiaty : {len(non_gmina)}")
    print(f"    Gminy (typy 1-3)               : {len(gmina_df)}")
    print(f"    Gminy usunięte (typy 4-5)       : {len(df[df['_type'] == 'gmina_split'])}")

    # ── 3. scal gminy z tym samym kodem bazowym ─────────────────────────────
    merged_rows = []
    groups = gmina_df.groupby("_base_code", sort=False)

    n_merged = 0
    for base_code, group in groups:
        if len(group) == 1:
            row = group.iloc[0].copy()
            row["Nazwa"] = strip_type_suffix(row["Nazwa"])
            merged_rows.append(row)
        else:
            merged_rows.append(merge_gmina_group(group, year_cols))
            n_merged += 1
            names = " + ".join(group["Nazwa"].tolist())
            print(f"    Scalono: {names}")

    print(f"\n  Scalonych grup: {n_merged}")

    merged_gminas = pd.DataFrame(merged_rows)

    # ── 4. połącz i posortuj ────────────────────────────────────────────────
    result = pd.concat([non_gmina, merged_gminas], ignore_index=True)
    result = result.drop(columns=["_type", "_base_code"])

    # Sortowanie po kodzie (jako string z wiodącymi zerami)
    result = result.sort_values("Kod", key=lambda s: s.str.zfill(7)).reset_index(drop=True)

    # Zamień NaN z powrotem na puste (estetyka)
    result[year_cols] = result[year_cols].fillna("")

    print(f"\n  Wierszy w wyniku: {len(result)}")
    return result


# ── zapis ─────────────────────────────────────────────────────────────────────

def save_csv(df: pd.DataFrame, path: str) -> None:
    df.to_csv(path, sep=";", index=False, encoding="utf-8-sig")
    print(f"\n  Zapisano: {path}")


# ── main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"Wczytuję: {INPUT_FILE}")
    df_raw = load_csv(INPUT_FILE)

    result = process(df_raw)

    save_csv(result, OUTPUT_FILE)
    print("\nGotowe!")