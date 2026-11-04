
import csv
import json
import re
import time
import unicodedata
from pathlib import Path

import requests

from hevy_builder import API_BASE, headers_hevy, fetch_templates

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "output" / "hevy_import_ready.csv"
LOG = ROOT / "output" / "import_progress.csv"
ERRORS = ROOT / "output" / "import_errors.csv"

BATCH_SIZE = 100
PAUSE_SECONDS = 0.5

VALID_TYPES = {
    "weight_reps", "reps_only", "bodyweight_reps",
    "bodyweight_assisted_reps", "duration", "weight_duration",
    "distance_duration", "short_distance_weight"
}

VALID_EQUIPMENT = {
    "none", "barbell", "dumbbell", "kettlebell", "machine",
    "plate", "resistance_band", "suspension", "other"
}

VALID_MUSCLES = {
    "abdominals", "shoulders", "biceps", "triceps", "forearms",
    "quadriceps", "hamstrings", "calves", "glutes", "abductors",
    "adductors", "lats", "upper_back", "traps", "lower_back",
    "chest", "cardio", "neck", "full_body", "other"
}


def normalize(value):
    value = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return re.sub(r"[\W_]+", "", value, flags=re.UNICODE)


def read_csv(path):
    if not path.exists():
        raise RuntimeError(f"Не найден файл: {path}")

    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def save_error(row, message):
    exists = ERRORS.exists()

    with ERRORS.open("a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["name_ru", "name_en", "error"]
        )
        if not exists:
            writer.writeheader()

        writer.writerow({
            "name_ru": row.get("name_ru", ""),
            "name_en": row.get("name_en", ""),
            "error": message
        })


def main():
    headers = headers_hevy()
    rows = read_csv(SOURCE)

    selected = [
        r for r in rows
        if r.get("import", "").strip().upper() == "YES"
        and r.get("name_ru", "").strip()
    ]

    print("Строк в исходном CSV:", len(rows))
    print("Отмечено для импорта:", len(selected))

    # Проверяем допустимые значения API.
    valid = []
    invalid = []

    for r in selected:
        if (
            r.get("exercise_type") not in VALID_TYPES
            or r.get("equipment_category") not in VALID_EQUIPMENT
            or r.get("muscle_group") not in VALID_MUSCLES
        ):
            invalid.append(r)
        else:
            valid.append(r)

    if invalid:
        print("\nНедопустимые значения:", len(invalid))
        for r in invalid:
            save_error(r, "Недопустимый тип, оборудование или группа мышц")

    # Загружаем актуальную библиотеку Hevy.
    print("\nПолучаю текущую библиотеку Hevy...")
    templates = fetch_templates()

    existing = {
        normalize(x.get("title") or x.get("name"))
        for x in templates
    }

    print("Шаблонов в Hevy:", len(templates))

    # Дополнительно учитываем журнал предыдущих запусков.
    if LOG.exists():
        for r in read_csv(LOG):
            if r.get("result") == "OK":
                existing.add(normalize(r.get("name_ru")))

    # Убираем уже созданные упражнения.
    remaining = []
    skipped = 0

    for r in valid:
        key = normalize(r["name_ru"])

        if key in existing:
            skipped += 1
        else:
            remaining.append(r)
            existing.add(key)

    print("Уже существуют или ранее импортированы:", skipped)
    print("Готовы к импорту:", len(remaining))

    if not remaining:
        print("Новых упражнений нет.")
        return

    print("\nПервые 5 упражнений:")
    for r in remaining[:5]:
        print("-", r["name_ru"])

    if input("\nДля начала импорта введи IMPORT: ").strip() != "IMPORT":
        print("Отменено.")
        return

    session = requests.Session()
    session.headers.update(headers)

    success = 0
    failed = 0

    for start in range(0, len(remaining), BATCH_SIZE):
        batch = remaining[start:start + BATCH_SIZE]

        print(
            f"\nПартия {start // BATCH_SIZE + 1}. "
            f"Упражнений: {len(batch)}"
        )

        for r in batch:
            title = r["name_ru"]

            payload = {
                "exercise": {
                    "title": title,
                    "exercise_type": r["exercise_type"],
                    "equipment_category": r["equipment_category"],
                    "muscle_group": r["muscle_group"],
                    "other_muscles": []
                }
            }

            try:
                response = session.post(
                    f"{API_BASE}/exercise_templates",
                    json=payload,
                    timeout=45
                )

                if response.status_code in (200, 201):
                    success += 1

                    with LOG.open(
                        "a", encoding="utf-8-sig", newline=""
                    ) as f:
                        writer = csv.DictWriter(
                            f,
                            fieldnames=["name_ru", "name_en", "result", "api_id"]
                        )
                        if f.tell() == 0:
                            writer.writeheader()

                        try:
                            api_id = response.json().get("id", "")
                        except ValueError:
                            api_id = ""

                        writer.writerow({
                            "name_ru": title,
                            "name_en": r.get("name_en", ""),
                            "result": "OK",
                            "api_id": api_id
                        })

                    print(f"OK: {title}")

                else:
                    failed += 1
                    message = f"HTTP {response.status_code}: {response.text[:400]}"
                    save_error(r, message)
                    print(f"ERROR: {title} | {message}")

            except Exception as e:
                failed += 1
                save_error(r, str(e))
                print(f"ERROR: {title} | {e}")

            time.sleep(PAUSE_SECONDS)

        print(
            f"\nРезультат партии: успешно {success}, "
            f"ошибок {failed}"
        )

        if start + BATCH_SIZE < len(remaining):
            if input("Для следующей партии введи NEXT: ").strip() != "NEXT":
                print("Импорт остановлен. Прогресс сохранён.")
                break

    print("\nИмпорт завершён или остановлен.")
    print("Успешно:", success)
    print("Ошибок:", failed)
    print("Журнал:", LOG)
    print("Ошибки:", ERRORS)


if __name__ == "__main__":
    main()
