import csv
import json

def export_csv(path, data):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["category", "value"])

        for key in ["sources", "targets", "intermediate", "column_lineage"]:
            for item in data.get(key, []):
                writer.writerow([key, item])

def export_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
