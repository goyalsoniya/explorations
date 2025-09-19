import requests
import json
from datetime import datetime

URL = "https://my.uscis.gov/appointmentscheduler-appointment/field-offices/state/CA"
OUTPUT_FILE = "appointments.json"

TARGET_CITIES = {"San Jose", "San Francisco", "Oakland"}
CUTOFF_DATE = datetime(2025, 10, 7)  # October 7, 2025

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
                # Only include if on or before cutoff date
                if earliest.date() <= CUTOFF_DATE.date():
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

        # Only output if there is at least one eligible appointment
        if earliest:
            output = {
                "timestamp": datetime.utcnow().isoformat(),
                "results": results,
                "earliest_overall": earliest
            }
            print(json.dumps(output, indent=2))

            with open(OUTPUT_FILE, "w") as f:
                json.dump(output, f, indent=2)

            # Export for GitHub Actions
            github_output = os.getenv("GITHUB_OUTPUT")
            if github_output:
                with open(github_output, "a") as f:
                    f.write(f"earliest={earliest['city']} on {earliest['earliest_datetime']}\n")
                    f.write(f"earliest_date={earliest['earliest_datetime'].split(' ')[0]}\n")

        else:
            print("No appointments available on or before 2025-10-07.")

            # Export for GitHub Actions
            github_output = os.getenv("GITHUB_OUTPUT")
            if github_output:
                with open(github_output, "a") as f:
                    f.write("earliest=None\n")
                    f.write("earliest_date=9999-12-31\n")

    except Exception as e:
        print("Error:", e)
