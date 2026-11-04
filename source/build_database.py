import csv
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
CSV_FILE = ROOT / "exports" / "hevy_import_ready.csv"
DB_FILE = ROOT / "database" / "exercisebase.db"
GIF_DIR = ROOT / "media" / "gifs"

if not CSV_FILE.exists():
    raise FileNotFoundError(f"Не найден CSV: {CSV_FILE}")

if DB_FILE.exists():
    raise FileExistsError(
        f"База уже существует: {DB_FILE}. "
        "Скрипт не будет перезаписывать её."
    )

with CSV_FILE.open("r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    columns = reader.fieldnames or []

required = [
    "dataset_id", "name_en", "name_ru", "exercise_type",
    "equipment_category", "muscle_group"
]

missing_columns = [c for c in required if c not in columns]
if missing_columns:
    raise ValueError(f"В CSV отсутствуют столбцы: {missing_columns}")

ids = [r["dataset_id"].strip() for r in rows]
if len(ids) != len(set(ids)):
    raise ValueError("Обнаружены повторяющиеся dataset_id. База не создана.")

DB_FILE.parent.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(DB_FILE)
conn.execute("PRAGMA foreign_keys = ON")

conn.executescript("""
CREATE TABLE exercises (
    dataset_id TEXT PRIMARY KEY,
    name_ru TEXT NOT NULL,
    name_en TEXT NOT NULL,
    translation_status TEXT,
    exercise_type TEXT,
    equipment_category TEXT,
    muscle_group TEXT,
    instructions_ru TEXT,
    gif_path TEXT,
    attribution TEXT,
    import_to_hevy INTEGER,
    import_status TEXT,
    hevy_id TEXT,
    source_json TEXT,
    created_at TEXT
);

CREATE TABLE exercise_steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_id TEXT NOT NULL,
    step_number INTEGER NOT NULL,
    instruction_ru TEXT NOT NULL,
    FOREIGN KEY(dataset_id) REFERENCES exercises(dataset_id)
        ON DELETE CASCADE
);

CREATE TABLE media (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_id TEXT NOT NULL,
    media_type TEXT NOT NULL,
    relative_path TEXT NOT NULL,
    attribution TEXT,
    FOREIGN KEY(dataset_id) REFERENCES exercises(dataset_id)
        ON DELETE CASCADE
);

CREATE INDEX idx_exercises_name_ru ON exercises(name_ru);
CREATE INDEX idx_exercises_name_en ON exercises(name_en);
CREATE INDEX idx_exercises_muscle ON exercises(muscle_group);
CREATE INDEX idx_exercises_equipment ON exercises(equipment_category);
CREATE INDEX idx_exercises_type ON exercises(exercise_type);
""")

now = datetime.now(timezone.utc).isoformat()
missing_gifs = []
missing_instructions = 0
step_count = 0

try:
    with conn:
        for r in rows:
            dataset_id = r["dataset_id"].strip()
            gif_source = (r.get("gif") or "").strip()
            gif_name = Path(gif_source.replace("\\", "/")).name
            gif_file = GIF_DIR / gif_name
            gif_path = f"media/gifs/{gif_name}" if gif_name else None

            if gif_name and not gif_file.exists():
                missing_gifs.append(gif_name)

            instructions = (r.get("instructions_ru") or "").strip()
            if not instructions:
                missing_instructions += 1

            conn.execute("""
                INSERT INTO exercises (
                    dataset_id, name_ru, name_en, translation_status,
                    exercise_type, equipment_category, muscle_group,
                    instructions_ru, gif_path, attribution,
                    import_to_hevy, import_status, hevy_id,
                    source_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                dataset_id,
                (r.get("name_ru") or "").strip(),
                (r.get("name_en") or "").strip(),
                r.get("translation_status"),
                r.get("exercise_type"),
                r.get("equipment_category"),
                r.get("muscle_group"),
                instructions,
                gif_path,
                r.get("attribution"),
                1 if (r.get("import") or "").strip().upper() == "YES" else 0,
                r.get("status"),
                None,
                json.dumps(r, ensure_ascii=False),
                now
            ))

            steps = (r.get("instruction_steps_ru") or "").strip()
            if steps:
                for number, step in enumerate(steps.split("|"), start=1):
                    step = step.strip()
                    if step:
                        conn.execute("""
                            INSERT INTO exercise_steps
                            (dataset_id, step_number, instruction_ru)
                            VALUES (?, ?, ?)
                        """, (dataset_id, number, step))
                        step_count += 1

            if gif_name and gif_file.exists():
                conn.execute("""
                    INSERT INTO media
                    (dataset_id, media_type, relative_path, attribution)
                    VALUES (?, 'gif', ?, ?)
                """, (dataset_id, gif_path, r.get("attribution")))

    total = conn.execute("SELECT COUNT(*) FROM exercises").fetchone()[0]
    media_total = conn.execute("SELECT COUNT(*) FROM media").fetchone()[0]
    steps_total = conn.execute("SELECT COUNT(*) FROM exercise_steps").fetchone()[0]

    print("\nБАЗА СОЗДАНА УСПЕШНО")
    print(f"Упражнений: {total}")
    print(f"GIF привязано: {media_total}")
    print(f"Шагов инструкций: {steps_total}")
    print(f"Без инструкций: {missing_instructions}")
    print(f"Отсутствующих GIF: {len(missing_gifs)}")
    print(f"Файл базы: {DB_FILE}")

    if missing_gifs:
        print("\nПервые отсутствующие GIF:")
        for name in missing_gifs[:20]:
            print(name)

finally:
    conn.close()
