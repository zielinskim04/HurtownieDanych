import requests
import pandas as pd
import time

import requests
import pandas as pd
import time

def fetch_bdl_data(variable_id, unit_level, year_from, year_to, output_file):
    base_url = f"https://bdl.stat.gov.pl/api/v1/data/by-variable/{variable_id}"
    params = {
        "unit-level": unit_level,
        "year": list(range(year_from, year_to + 1)),
        "page-size": 100,
        "format": "json"
    }

    all_data = []
    unit_of_measure = ""
    page = 0

    print(f"Pobieranie danych dla zmiennej {variable_id} do pliku {output_file}...")

    while True:
        params["page"] = page
        response = requests.get(base_url, params=params)

        if response.status_code != 200:
            print(f"Błąd API: {response.status_code} – {response.text}")
            break

        data = response.json()

        # Jednostka miary jest zwykle w measureUnitId lub measureUnit na poziomie zmiennej
        if not unit_of_measure:
            unit_of_measure = data.get("measureUnitName", "")

        for res in data.get("results", []):
            for v in res.get("values", []):
                all_data.append({
                    "Kod": res["id"],
                    "Nazwa": res["name"],
                    "Rok": v["year"],
                    "Wartosc": v.get("val")
                })

        if not data.get("links", {}).get("next"):
            break

        page += 1
        time.sleep(0.1)

    if not all_data:
        print("Brak danych.")
        return

    df_long = pd.DataFrame(all_data)

    # Pivot: wiersze = jednostki, kolumny = lata
    df_wide = df_long.pivot_table(
        index=["Kod", "Nazwa"],
        columns="Rok",
        values="Wartosc",
        aggfunc="first"
    ).reset_index()

    # Nadaj kolumnom format: "ogółem;ROK;[jednostka]"
    unit_label = f"[{unit_of_measure}]" if unit_of_measure else ""
    df_wide.columns = (
        ["Kod", "Nazwa"]
        + [f"ogółem;{rok};{unit_label}" for rok in df_wide.columns[2:]]
    )

    # Konwersja wartości na int tam gdzie możliwe (brak NaN)
    for col in df_wide.columns[2:]:
        df_wide[col] = pd.to_numeric(df_wide[col], errors="coerce")

    df_wide.to_csv(output_file, index=False, sep=";", encoding="utf-8-sig")
    print(f"Zapisano {len(df_wide)} wierszy, {len(df_wide.columns)-2} lat do {output_file}.")


# --- WYWOŁANIA ---
fetch_bdl_data(variable_id=60531,  unit_level=5, year_from=2003, year_to=2025, output_file="bezrobocie2.csv")
fetch_bdl_data(variable_id=64428,  unit_level=4, year_from=2003, year_to=2024, output_file="wynagrodzenie2.csv")
fetch_bdl_data(variable_id=72305,  unit_level=5, year_from=2003, year_to=2024, output_file="ludnosc2.csv")
fetch_bdl_data(variable_id=160538, unit_level=2, year_from=2003, year_to=2025, output_file="inflacja2.csv")
# --- REALIZACJA TWOICH ZAPYTAŃ ---

# 1. Bezrobocie (Gminy - Level 5)
# Zakładając ID dla "Bezrobotni zarejestrowani ogółem"
fetch_bdl_data(variable_id=60531, unit_level=5, year_from=2005, year_to=2025, output_file="bezrobocie2.csv")

# 2. Wynagrodzenia (Powiaty - Level 4)
# Zakładając ID dla "Przeciętne miesięczne wynagrodzenie brutto"
fetch_bdl_data(variable_id=64428, unit_level=4, year_from=2005, year_to=2024, output_file="wynagrodzenie2.csv")

# 3. Ludność i gęstość (Gminy - Level 5)
# Gęstość zaludnienia ogółem
fetch_bdl_data(variable_id=72305, unit_level=5, year_from=2005, year_to=2024, output_file="ludnosc2.csv")

# 4. Inflacja (Województwa - Level 2)
# Wskaźnik cen towarów i usług konsumpcyjnych
fetch_bdl_data(variable_id=160538, unit_level=2, year_from=2005, year_to=2025, output_file="inflacja2.csv")