import requests
import pandas as pd

def pobierz_dane_bdl(var_id, rok, poziom=5):
    """
    Pobiera dane z API BDL GUS. Zwraca DataFrame lub pustą tabelę, jeśli danych brak.
    """
    url = f"https://bdl.stat.gov.pl/api/v1/data/by-variable/{var_id}"
    params = {
        'unit-level': poziom,
        'year': rok,
        'format': 'json',
        'page-size': 100
    }
    
    wszystkie_dane = []
    
    while True:
        response = requests.get(url, params=params)
        
        # --- OBSŁUGA BŁĘDU 404 ---
        if response.status_code == 404:
            print(f" -> [UWAGA] Brak danych dla ID {var_id} na poziomie {poziom} w {rok} roku.")
            return pd.DataFrame() # Zwraca pustą tabelę zamiast błędu krytycznego
            
        # Jeśli wystąpi inny błąd (np. brak internetu, błąd serwera 500), wyrzuci wyjątek
        response.raise_for_status() 
        
        dane = response.json()
        wszystkie_dane.extend(dane.get('results', []))
        
        if 'links' in dane and 'next' in dane['links']:
            url = dane['links']['next']
            params = {} 
        else:
            break 
            
    df = pd.DataFrame(wszystkie_dane)
    
    if not df.empty and 'values' in df.columns:
        df['wartosc'] = df['values'].apply(lambda x: x[0]['val'] if x else None)
        df = df.drop(columns=['values'])
        
    return df

# --- KONFIGURACJA ZAPYTANIA ---

ID_WYNAGRODZENIA = 64428 # To ID działa dla powiatów (level 5)
ID_NIERUCHOMOSCI = 336173 # To ID wyrzuci 404
ID_BEZROBOCIE = 60370 # To ID (Stopa bezrobocia) działa dla powiatów (level 5) jako test

ROK_BADAWCZY = 2022 

# --- WYKONANIE ---

print("1. Pobieranie danych o wynagrodzeniach...")
df_wynagrodzenia = pobierz_dane_bdl(ID_WYNAGRODZENIA, ROK_BADAWCZY)
if not df_wynagrodzenia.empty:
    print(df_wynagrodzenia[['name', 'wartosc']].head())

print("\n------------------\n")

print("2. Pobieranie danych o cenach nieruchomości (to powinno zwrócić nasz nowy komunikat)...")
df_nieruchomosci = pobierz_dane_bdl(633692, ROK_BADAWCZY, poziom=5)
if not df_nieruchomosci.empty:
    print(df_nieruchomosci[['name', 'wartosc']].head())

print("\n------------------\n")

print("3. Pobieranie danych o bezrobociu (TEST)...")
df_bezrobocie = pobierz_dane_bdl(ID_BEZROBOCIE, ROK_BADAWCZY)
if not df_bezrobocie.empty:
    print(df_bezrobocie[['name', 'wartosc']].head())