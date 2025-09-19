import requests
import json
from datetime import datetime

URL = "https://my.uscis.gov/appointmentscheduler-appointment/field-offices/state/CA"
OUTPUT_FILE = "appointments.json"

TARGET_CITIES = {"San Jose", "San Francisco", "Oakland"}

def fetch_data():
    resp = requests.get(URL)
    resp.raise_for_status()
    return resp.json()

def parse_appointments(data):
    results = []

    for office in data:
        city = office.get("address", {}).get("city")
        if city in TARGET_CITIES and office.get("timeSlots"):
            # Flatten all (date, time) into datetime objects
            all_slots = []
            for slot in office["timeSlots"]:
                date = slot.get("date")
                for t in slot.get("times", []):
                    dt = datetime.strptime(f"{date} {t}", "%Y-%m-%d %H:%M")
                    all_slots.append(dt)

            if all_slots:
                earliest = min(all_slots)
                results.append({
                    "city": city,
                    "earliest_datetime": earliest.strftime("%Y-%m-%d %H:%M")
                })

    return results

def find_earliest(results):
    if not results:
        return None
    return min(
        results,
        key=lambda r: datetime.strptime(r["earliest_datetime"], "%Y-%m-%d %H:%M")
    )

if __name__ == "__main__":
    try:
        data = fetch_data()
        results = parse_appointments(data)
        earliest = find_earliest(results)

        output = {
            "timestamp": datetime.utcnow().isoformat(),
            "results": results,
            "earliest_overall": earliest
        }
        print(json.dumps(output, indent=2))

        with open(OUTPUT_FILE, "w") as f:
            json.dump(output, f, indent=2)

    except Exception as e:
        print("Error:", e)
