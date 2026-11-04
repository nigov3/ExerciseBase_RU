
import csv
from pathlib import Path

base = Path(__file__).parent
source = base / "output" / "hevy_import_review.csv"
translations_file = base / "translations_ru.tsv"
result = base / "output" / "hevy_import_review_translated.csv"

translations = {}

with open(translations_file, encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f, delimiter="\t")
    for row in reader:
        en = row["name_en"].strip()
        ru = row["name_ru"].strip()
        if en and ru:
            translations[en] = ru

updated = 0

with open(source, encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    fields = reader.fieldnames

for row in rows:
    en = row["name_en"].strip()
    ru = translations.get(en)

    if ru:
        row["name_ru"] = ru
        row["translation_status"] = "MANUAL_TRANSLATION"
        updated += 1

with open(result, "w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

print("Переводов в словаре:", len(translations))
print("Обновлено строк:", updated)
print("Результат:", result)
