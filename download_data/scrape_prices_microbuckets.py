import requests
import time
import random
import csv
import re
import json
import os

PROGRESS_FILE = 'progress_buckets.json'
CSV_FILE = 'deweloperuch_ceny_w_polsce.csv'
LOCATIONS_FILE = 'locations_list.txt'

def get_saved_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_progress(loc_index, bucket_index, page):
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump({"loc_index": loc_index, "bucket_index": bucket_index, "page": page}, f)

def load_locations():
    if not os.path.exists(LOCATIONS_FILE):
        print(f"❌ Cannot find '{LOCATIONS_FILE}'.")
        return []
    with open(LOCATIONS_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def generate_micro_buckets():
    buckets = []
    
    # Very cheap / unusual transactions (50k steps)
    for price in range(0, 200000, 50000):
        buckets.append(f"{price}-{price + 50000}")
        
    # The "Bell Curve" where 80% of data lives (20k steps to guarantee < 2000 results)
    for price in range(200000, 1500000, 20000):
        buckets.append(f"{price}-{price + 20000}")
        
    # Expensive properties (100k steps)
    for price in range(1500000, 3000000, 100000):
        buckets.append(f"{price}-{price + 100000}")
        
    # Luxury properties (Massive step, rarely hits 2,000 limit)
    buckets.append("3000000-50000000")
    
    return buckets

PRICE_BUCKETS = generate_micro_buckets()

def scrape_all_data():
    locations = load_locations()
    if not locations:
        return

    base_url = "https://deweloperuch.pl/ceny-transakcyjne/{}/mieszkania"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
        "Accept-Language": "pl-PL,pl;q=0.9",
        "Referer": "https://deweloperuch.pl/"
    }

    progress = get_saved_progress()
    start_loc_idx = 0
    start_bucket_idx = 0
    start_page = 1

    if progress:
        start_loc_idx = progress.get("loc_index", 0)
        start_bucket_idx = progress.get("bucket_index", 0)
        start_page = progress.get("page", 1)
        print(f"🔄 Resuming... City #{start_loc_idx}, Bucket #{start_bucket_idx}, Page {start_page}")

    file_exists = os.path.isfile(CSV_FILE)
    
    with open(CSV_FILE, mode='a', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        
        if not file_exists or os.path.getsize(CSV_FILE) == 0:
            writer.writerow(['Adres', 'Data_transakcji', 'Cena', 'Cena/m2', 'Metraz', 'Izby', 'Kondygnacja', 'TERYT_Kod'])
            
        for loc_i in range(start_loc_idx, len(locations)):
            location = locations[loc_i]
            print(f"\n🏙️ --- CITY: {location.upper()} ---")
            
            curr_start_bucket = start_bucket_idx if loc_i == start_loc_idx else 0
            
            for bucket_i in range(curr_start_bucket, len(PRICE_BUCKETS)):
                bucket = PRICE_BUCKETS[bucket_i]
                print(f"  💰 Price Bucket: {bucket} zł")
                
                curr_start_page = start_page if (loc_i == start_loc_idx and bucket_i == curr_start_bucket) else 1
                
                for page in range(curr_start_page, 21):
                    # Injecting the price filter into the URL
                    url = base_url.format(location) + f"?page={page}&perPage=100&filterPrice={bucket}"
                    
                    try:
                        response = requests.get(url, headers=headers)
                    except Exception as e:
                        print(f"  ❌ Connection error: {e}")
                        return
                    
                    if response.status_code == 403:
                        print("  ❌ Blocked by Cloudflare! Pausing.")
                        return
                    elif response.status_code != 200:
                        print(f"  ❌ Failed to fetch. Status: {response.status_code}")
                        return
                    
                    json_data = None
                    chunks = re.findall(r'self\.__next_f\.push\(\[\d+,\s*(".*?")\]\)', response.text)
                    
                    for chunk in chunks:
                        if 'initialData' in chunk:
                            clean_text = json.loads(chunk)
                            data_match = re.search(r'"initialData":\{"data":(\[.*?\]),"pagination"', clean_text)
                            if data_match:
                                json_data = json.loads(data_match.group(1))
                                break
                    
                    # If this price bucket has no more pages, move to the next price bucket
                    if not json_data:
                        save_progress(loc_i, bucket_i + 1, 1)
                        break
                        
                    for item in json_data:
                        invest = item.get("invest") or {}
                        street = invest.get("name", "").strip()
                        city = invest.get("city", "").strip()
                        address = f"{street}, {city}" if street and city else (city or "N/A")
                        
                        data_transakcji = item.get("creation_date", "N/A")
                        cena = f"{item.get('amount', 'N/A')} zł"
                        cena_m2 = f"{item.get('amount_sqm', 'N/A')} zł"
                        metraz = f"{item.get('size', 'N/A')} m2"
                        izby = str(item.get("rooms", "N/A"))
                        kond = str(item.get("floor", "N/A"))
                        
                        full_id = str(item.get("name", ""))
                        teryt_code = full_id.split("_")[0] if "_" in full_id else "N/A"
                        
                        writer.writerow([address, data_transakcji, cena, cena_m2, metraz, izby, kond, teryt_code])
                    
                    if page == 20 and len(json_data) == 100:
                        print(f"  ⚠️ Warning: Bucket {bucket} in {location} is too full! Might miss a few properties.")

                    file.flush()
                    save_progress(loc_i, bucket_i, page + 1)
                    
                    # Log progress cleanly
                    print(f"    ✓ Scraped page {page} ({len(json_data)} properties)")
                    time.sleep(random.uniform(0.7, 1.5))

    print("\n🎉 ALL DATA SCRAPED!")
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)

if __name__ == "__main__":
    scrape_all_data()