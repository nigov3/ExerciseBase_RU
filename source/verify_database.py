import sqlite3
from pathlib import Path

root = Path(__file__).resolve().parent.parent
db = root / "database" / "exercisebase.db"

con = sqlite3.connect(db)

print("=== ЦЕЛОСТНОСТЬ SQLITE ===")
print(con.execute("PRAGMA integrity_check").fetchone()[0])

print("\n=== КОЛИЧЕСТВО ЗАПИСЕЙ ===")
for table in ("exercises", "exercise_steps", "media"):
    count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"{table}: {count}")

print("\n=== ПРОВЕРКА НАЗВАНИЙ ===")
print("Без русского названия:",
      con.execute("SELECT COUNT(*) FROM exercises WHERE name_ru IS NULL OR TRIM(name_ru)=''").fetchone()[0])
print("Без английского названия:",
      con.execute("SELECT COUNT(*) FROM exercises WHERE name_en IS NULL OR TRIM(name_en)=''").fetchone()[0])

print("\n=== СТАТУСЫ ПЕРЕВОДА ===")
for status, count in con.execute("""
    SELECT translation_status, COUNT(*)
    FROM exercises GROUP BY translation_status
"""):
    print(f"{status}: {count}")

print("\n=== ПОВТОРЯЮЩИЕСЯ РУССКИЕ НАЗВАНИЯ ===")
duplicates = con.execute("""
    SELECT name_ru, COUNT(*) AS n
    FROM exercises
    GROUP BY name_ru
    HAVING n > 1
    ORDER BY n DESC
    LIMIT 15
""").fetchall()
for name, count in duplicates:
    print(f"{count} раз: {name}")
if not duplicates:
    print("Не обнаружены")

print("\n=== ПРОВЕРКА GIF ===")
missing = []
for (path,) in con.execute("SELECT relative_path FROM media"):
    if not (root / path).is_file():
        missing.append(path)
print("Отсутствует файлов:", len(missing))
for path in missing[:10]:
    print(path)

print("\n=== ПРИМЕРЫ УПРАЖНЕНИЙ ===")
for row in con.execute("""
    SELECT dataset_id, name_ru, name_en, muscle_group, gif_path
    FROM exercises ORDER BY CAST(dataset_id AS INTEGER) LIMIT 5
"""):
    print(" | ".join(str(x) for x in row))

con.close()
