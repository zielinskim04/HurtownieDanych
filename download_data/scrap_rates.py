import pandas as pd

url = "https://www.firma.egospodarka.pl/niezbednik-firmowy/podstawowe-stopy-procentowe-nbp"

# Pobieramy wszystkie tabele ze strony
# Dodajemy storage_options, aby ominąć ewentualne blokady serwera
tables = pd.read_html(url, decimal=',', thousands=' ', flavor='bs4')

# Interesuje Cię druga tabela na stronie (indeks 1)
df_history = tables[1]

# Usuwamy wiersze, które są tylko "latami" (np. 2026, 2025) 
# Te wiersze w kolumnie 'Stopa referencyjna' mają zazwyczaj wartość NaN po wczytaniu
df_history = df_history.dropna(subset=['Stopa referencyjna'])

# Wyświetlamy całość
print(df_history.to_string(index=False))

# Opcjonalnie: zapisz do Excela
df_history.to_csv("data/stopy_nbp_historia.csv", index=False, sep=';', encoding='utf-8-sig')
