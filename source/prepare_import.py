import csv
from pathlib import Path
from collections import Counter

root = Path(__file__).parent
source = root / "output" / "hevy_import_review_translated.csv"
result = root / "output" / "hevy_import_ready.csv"

with open(source, encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    fields = reader.fieldnames

ready = 0
duplicates = 0
missing = 0

for row in rows:
    status = row.get("status", "").strip().upper()
    name_ru = row.get("name_ru", "").strip()

    if status == "DUPLICATE":
        row["import"] = "NO"
        duplicates += 1
    elif name_ru:
        row["import"] = "YES"
        ready += 1
    else:
        row["import"] = "NO"
        missing += 1

with open(result, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

print("Всего строк:", len(rows))
print("Подготовлено к импорту:", ready)
print("Дубликатов, исключено:", duplicates)
print("Без русского названия:", missing)
print("Файл:", result)