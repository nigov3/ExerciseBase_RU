import csv
from pathlib import Path
from collections import Counter, defaultdict

source = Path(__file__).parent / "output" / "hevy_import_review_translated.csv"

with open(source, encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print("=" * 55)
print("АУДИТ БИБЛИОТЕКИ HEVY")
print("=" * 55)

print("\nВсего упражнений:", len(rows))

for field in ["import", "status", "translation_status",
              "exercise_type", "equipment_category", "muscle_group"]:

    if field not in rows[0]:
        print(f"\nНет столбца: {field}")
        continue

    counts = Counter(
        (r.get(field) or "").strip() or "[ПУСТО]"
        for r in rows
    )

    print(f"\n--- {field} ---")
    for value, count in counts.most_common():
        print(f"{value}: {count}")

print("\n" + "=" * 55)
print("СОЧЕТАНИЯ СТАТУСОВ И ИМПОРТА")
print("=" * 55)

groups = defaultdict(list)

for r in rows:
    key = (
        (r.get("status") or "").strip() or "[ПУСТО]",
        (r.get("import") or "").strip() or "[ПУСТО]"
    )
    groups[key].append(r)

for (status, imp), items in sorted(groups.items()):
    print(f"\nstatus={status} | import={imp}: {len(items)}")
    for r in items[:5]:
        print("  ", r.get("name_en"), "->", r.get("name_ru"))

print("\n" + "=" * 55)
print("ПРИМЕРЫ НЕОТМЕЧЕННЫХ УПРАЖНЕНИЙ")
print("=" * 55)

not_selected = [
    r for r in rows
    if (r.get("import") or "").strip().upper() != "YES"
]

for r in not_selected[:40]:
    print(
        f"{r.get('name_en')} | "
        f"status={r.get('status')} | "
        f"import={r.get('import')}"
    )

print("\nВсего не отмечено:", len(not_selected))