import urllib.request
import urllib.parse
import json
import csv
import sys
import time
from pathlib import Path

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

# Constants
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
OUTPUT_FILE = DATA_DIR / "asos_historical_weather.csv"

# 11 Representative Weather Stations matching provinces
STATIONS = [108, 112, 119, 114, 131, 133, 146, 156, 143, 159, 184]
YEARS = list(range(2010, 2025))

def load_service_key():
    # Try to load from loaders
    try:
        sys.path.append(str(BASE_DIR / "backend"))
        from recommendations.loaders import load_public_service_key
        key = load_public_service_key()
        if key:
            return key
    except Exception:
        pass
    return "73ce8e698c1b754946f872a92f08830722398936fb3569a9d07024f4db0b39ff"

def fetch_year_station_weather(station_id, year, service_key):
    url = "https://apis.data.go.kr/1360000/AsosHourlyInfoService/getWthrDataList"
    all_items = []
    page = 1
    while True:
        query = {
            "serviceKey": service_key,
            "pageNo": str(page),
            "numOfRows": "999",  # Under 1000 limit
            "dataType": "JSON",
            "dataCd": "ASOS",
            "dateCd": "HR",
            "startDt": f"{year}0101",
            "startHh": "00",
            "endDt": f"{year}1231",
            "endHh": "23",
            "stnIds": str(station_id)
        }

        full_url = f"{url}?{urllib.parse.urlencode(query)}"
        
        try:
            req = urllib.request.Request(full_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as response:
                res_body = response.read()
                data = json.loads(res_body.decode('utf-8', errors='replace'))
                
                header = data.get("response", {}).get("header", {})
                code = header.get("resultCode")
                msg = header.get("resultMsg")
                
                if code != "00":
                    print(f"[Error] Station {station_id}, Year {year}, Page {page}: {code} - {msg}")
                    break
                    
                items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
                if not items:
                    break
                
                all_items.extend(items)
                if len(items) < 999:
                    break
                page += 1
                time.sleep(0.1) # Brief politeness delay between pages
        except Exception as e:
            print(f"[Error] Failed to fetch Station {station_id}, Year {year}, Page {page}: {e}")
            break
            
    return all_items

def main():
    service_key = load_service_key()
    print("Using Service Key:", service_key[:8] + "...")
    print(f"Target Stations: {STATIONS}")
    print(f"Target Years: {YEARS[0]} ~ {YEARS[-1]}")
    
    # Check if we should append or overwrite
    # To be safe, we overwrite or create new
    print(f"Output will be saved to: {OUTPUT_FILE}")
    
    # We write headers first
    headers = ['date', 'hour', 'station_id', 'temp', 'rain', 'wind', 'humidity']
    
    # Let's read existing progress if file exists to resume
    processed = set()
    if OUTPUT_FILE.exists():
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None) # skip header
                for row in reader:
                    if row:
                        # Record that we have some data
                        dt = row[0]
                        yr = dt.split('-')[0]
                        st = row[2]
                        processed.add((int(st), int(yr)))
            print(f"Resuming: found {len(processed)} station-years already downloaded.")
        except Exception:
            pass

    mode = 'a' if processed else 'w'
    with open(OUTPUT_FILE, mode, encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        if mode == 'w':
            writer.writerow(headers)
            
        success_count = 0
        for station in STATIONS:
            for year in YEARS:
                if (station, year) in processed:
                    continue
                    
                print(f"Fetching Station {station}, Year {year}...")
                items = fetch_year_station_weather(station, year, service_key)
                if not items:
                    # Wait a bit before retry or skip
                    time.sleep(1)
                    continue
                    
                rows_written = 0
                for item in items:
                    tm = item.get("tm", "")
                    if not tm:
                        continue
                    try:
                        # tm format: "2024-06-01 01:00"
                        parts = tm.split()
                        date_str = parts[0]
                        hour_val = int(parts[1].split(':')[0])
                        
                        temp = item.get("ta")
                        rain = item.get("rn")
                        wind = item.get("ws")
                        humidity = item.get("hm")
                        
                        # Clean values
                        temp = float(temp) if temp else 15.0
                        rain = float(rain) if rain else 0.0
                        wind = float(wind) if wind else 1.5
                        humidity = float(humidity) if humidity else 50.0
                        
                        writer.writerow([date_str, hour_val, station, temp, rain, wind, humidity])
                        rows_written += 1
                    except Exception:
                        continue
                
                print(f"--> Saved {rows_written} hourly records.")
                success_count += 1
                f.flush()
                time.sleep(0.5) # Politeness delay
                
    print(f"Finished. Successfully downloaded {success_count} station-years.")

if __name__ == "__main__":
    main()
