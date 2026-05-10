import requests
import pandas as pd

def pobierz_inflacje_bdl():
    # ID zmiennej dla: Wskaźniki cen towarów i usług konsumpcyjnych - ogółem (P2955)
    VAR_ID = "217230" 
    BASE_URL = f"https://bdl.stat.gov.pl/api/v1/data/by-variable/{VAR_ID}"
    
    # Lata 2005-2025
    lata = [str(rok) for rok in range(2005, 2026)]
    
    # Poziom 0 to cała Polska, Poziom 2 to podział na Województwa
    poziomy = ["0", "2"] 
    records = []

    print("Rozpoczynam pobieranie danych z API BDL...")

    for poziom in poziomy:
        params = {
            "unit-level": poziom,
            "year": lata,
            "page-size": "100" # Wystarczające dla 1 (Polska) lub 16 (Województwa) wyników
        }
        
        nazwa_poziomu = "Polska" if poziom == "0" else "Województwa"
        print(f"Pobieranie danych dla: {nazwa_poziomu}...")

        try:
            response = requests.get(BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()

            for unit in data.get('results', []):
                kod = unit.get('id')
                nazwa = unit.get('name')
                
                # Ujednolicenie nazwy dla całego kraju, by ładnie wyglądała w CSV
                if poziom == "0":
                    nazwa = "POLSKA OGÓŁEM"

                for val in unit.get('values', []):
                    records.append({
                        'Kod': kod,
                        'Nazwa': nazwa,
                        'Rok': val.get('year'),
                        'ogółem': val.get('val')
                    })
                    
        except requests.exceptions.RequestException as e:
            print(f"Błąd podczas połączenia z API dla poziomu {poziom}: {e}")

    # Tworzenie DataFrame
    df = pd.DataFrame(records)

    if df.empty:
        print("Nie znaleziono danych dla podanych parametrów.")
        return

    # Sortowanie: Kod Polski to zawsze '000000000000', więc po posortowaniu 
    # według 'Kod' i 'Rok' Polska będzie naturalnie na samej górze pliku.
    df = df.sort_values(by=['Kod', 'Rok'])
    
    # Zapis do CSV
    nazwa_pliku = 'data/inflacja.csv'
    df.to_csv(nazwa_pliku, index=False, sep=';', encoding='utf-8-sig')
    
if __name__ == "__main__":
    pobierz_inflacje_bdl()