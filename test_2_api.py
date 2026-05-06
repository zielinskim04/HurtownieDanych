import requests
import pandas as pd

def wyszukaj_zmienne_dla_podgrupy(subject_id):
    """
    Pobiera listę wszystkich zmiennych (var-id) dla podanego ID tematu/podgrupy.
    """
    url = "https://bdl.stat.gov.pl/api/v1/variables"
    params = {
        'subject-id': subject_id,
        'format': 'json',
        'page-size': 100
    }
    
    wszystkie_zmienne = []
    
    print(f"Pobieranie listy zmiennych dla podgrupy {subject_id}...\n")
    
    while True:
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        dane = response.json()
        wszystkie_zmienne.extend(dane.get('results', []))
        
        # Obsługa paginacji
        if 'links' in dane and 'next' in dane['links']:
            url = dane['links']['next']
            params = {}
        else:
            break
            
    # Tworzymy czytelną tabelę
    df = pd.DataFrame(wszystkie_zmienne)
    
    if not df.empty:
        # Wybieramy tylko najbardziej przydatne kolumny: id oraz wymiary (n1, n2, n3...)
        kolumny_do_wyswietlenia = ['id'] + [col for col in df.columns if col.startswith('n')]
        
        print("ZNALEZIONE ZMIENNE I ICH ID:")
        print("-" * 50)
        # Zwiększamy limit wyświetlanych wierszy, żeby zobaczyć wszystkie opcje w terminalu
        with pd.option_context('display.max_rows', None, 'display.max_columns', None):
            print(df[kolumny_do_wyswietlenia])
        print("-" * 50)
        print(f"Łącznie znaleziono: {len(df)} zmiennych.")
    else:
        print("Nie znaleziono żadnych zmiennych dla tego ID podgrupy.")

# Wrzucamy ID Twojej podgrupy (P3788 -> wpisujemy same cyfry)
wyszukaj_zmienne_dla_podgrupy("P3788")