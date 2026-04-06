import csv
import os
import threading

lock = threading.Lock()

FILES = {
    "customers": "customers.csv",
    "encounters": "encounters.csv",
    "symptoms": "symptom_reports.csv",
    "ai": "ai_results.csv",
    "fhir": "fhir_resources.csv"
}

HEADERS = {
    "customers": ["customer_id", "name"],
    "encounters": ["encounter_id", "customer_id"],
    "symptoms": ["encounter_id", "symptoms"],
    "ai": ["encounter_id", "results"],
    "fhir": ["encounter_id", "resource_type", "resource_json"]
}

def init_csv():
    for key, file in FILES.items():
        if not os.path.exists(file):
            with open(file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(HEADERS[key])

def safe_write(file_key, row):
    with lock:
        with open(FILES[file_key], "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(row)

def read_all(file_key):
    if not os.path.exists(FILES[file_key]):
        return []

    with open(FILES[file_key], "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)

def find_one(file_key, column_name, value):
    rows = read_all(file_key)
    for row in rows:
        if row.get(column_name) == value:
            return row
    return None

def find_all(file_key, column_name, value):
    rows = read_all(file_key)
    return [row for row in rows if row.get(column_name) == value]