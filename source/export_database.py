import csv
import json
import sqlite3
from pathlib import Path

root = Path(__file__).resolve().parent.parent
db = root / "database" / "exercisebase.db"
exports = root / "exports"
exports.mkdir(exist_ok=True)

con = sqlite3.connect(db)
con.row_factory = sqlite3.Row

rows = con.execute("""
    SELECT e.*,
           GROUP_CONCAT(s.instruction_ru, ' | ') AS instruction_steps_ru
    FROM exercises e
    LEFT JOIN exercise_steps s ON s.dataset_id = e.dataset_id
    GROUP BY e.dataset_id
    ORDER BY CAST(e.dataset_id AS INTEGER)
""").fetchall()

fields = [
    "dataset_id", "name_ru", "name_en", "translation_status",
    "exercise_type", "equipment_category", "muscle_group",
    "instructions_ru", "instruction_steps_ru", "gif_path",
    "attribution", "import_to_hevy", "import_status", "hevy_id"
]

csv_path = exports / "exercisebase_export.csv"
with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    for row in rows:
        writer.writerow({key: row[key] for key in fields})

json_path = exports / "exercisebase_export.json"
with json_path.open("w", encoding="utf-8") as f:
    json.dump(
        [dict(row) for row in rows],
        f,
        ensure_ascii=False,
        indent=2
    )

print("Экспорт завершён")
print(f"Упражнений: {len(rows)}")
print(f"CSV: {csv_path}")
print(f"JSON: {json_path}")

con.close()
