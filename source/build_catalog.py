import json
import sqlite3
from pathlib import Path
from collections import Counter
from html import escape

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "database" / "exercisebase.db"
OUT = ROOT / "exports"

OUT.mkdir(exist_ok=True)

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

exercises = []

for row in con.execute("""
    SELECT *
    FROM exercises
    ORDER BY CAST(dataset_id AS INTEGER)
"""):
    item = dict(row)

    steps = con.execute("""
        SELECT step_number, instruction_ru
        FROM exercise_steps
        WHERE dataset_id = ?
        ORDER BY step_number
    """, (item["dataset_id"],)).fetchall()

    item["instruction_steps_ru"] = [
        {"step": s["step_number"], "text": s["instruction_ru"]}
        for s in steps
    ]

    item["media"] = []
    if item.get("gif_path"):
        item["media"].append({
            "type": "gif",
            "path": item["gif_path"]
        })

    item.pop("source_json", None)
    exercises.append(item)

con.close()

# Структурированный JSON для будущих приложений
json_path = OUT / "exercisebase_structured.json"

with json_path.open("w", encoding="utf-8") as f:
    json.dump({
        "name": "ExerciseBase RU",
        "version": "1.0",
        "exercise_count": len(exercises),
        "exercises": exercises
    }, f, ensure_ascii=False, indent=2)

# Данные встраиваются в HTML, чтобы каталог работал
# локально, без сервера и интернета.
data = json.dumps(exercises, ensure_ascii=False)
data = data.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")

html = r'''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ExerciseBase RU</title>
<style>
:root {
  color-scheme: dark;
  --bg: #111318;
  --panel: #1a1d24;
  --panel2: #222630;
  --border: #303642;
  --text: #f1f3f7;
  --muted: #929baa;
  --accent: #b6f36b;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: Arial, sans-serif;
}
header {
  padding: 28px 4%;
  border-bottom: 1px solid var(--border);
  background: #151820;
}
h1 { margin: 0 0 8px; font-size: 28px; }
.subtitle { color: var(--muted); font-size: 14px; }
main { max-width: 1600px; margin: auto; padding: 24px 4%; }
.stats {
  display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 22px;
}
.stat {
  background: var(--panel); border: 1px solid var(--border);
  padding: 13px 17px; border-radius: 12px; min-width: 130px;
}
.stat strong { display: block; font-size: 22px; color: var(--accent); }
.stat span { color: var(--muted); font-size: 12px; }
.filters {
  display: grid;
  grid-template-columns: minmax(220px, 2fr) repeat(3, minmax(150px, 1fr));
  gap: 10px; margin-bottom: 14px;
}
input, select {
  width: 100%; padding: 13px 14px; border-radius: 9px;
  border: 1px solid var(--border); background: var(--panel);
  color: var(--text); font-size: 14px; outline: none;
}
input:focus, select:focus { border-color: var(--accent); }
.toolbar {
  display: flex; justify-content: space-between; gap: 12px;
  align-items: center; margin: 16px 0; color: var(--muted);
  font-size: 13px;
}
button {
  border: 1px solid var(--border); background: var(--panel2);
  color: var(--text); padding: 9px 13px; border-radius: 8px;
  cursor: pointer;
}
button:hover { border-color: var(--accent); }
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
}
.card {
  background: var(--panel); border: 1px solid var(--border);
  border-radius: 13px; overflow: hidden; min-width: 0;
}
.gif {
  width: 100%; aspect-ratio: 1.45;
  object-fit: contain; background: #20242c; display: block;
}
.content { padding: 14px; }
.id { color: var(--accent); font-size: 11px; margin-bottom: 7px; }
.name { font-weight: 700; font-size: 16px; line-height: 1.35; }
.en { color: var(--muted); font-size: 12px; margin-top: 5px; }
.tags { display: flex; flex-wrap: wrap; gap: 6px; margin: 12px 0; }
.tag {
  font-size: 11px; padding: 5px 8px; border-radius: 6px;
  background: var(--panel2); color: #c5ccd7;
}
details {
  border-top: 1px solid var(--border); padding-top: 10px;
  margin-top: 10px; font-size: 13px;
}
summary { cursor: pointer; color: var(--accent); }
.instructions { color: #c5ccd7; line-height: 1.55; margin-top: 10px; }
.instructions ol { padding-left: 20px; }
.instructions li { margin: 7px 0; }
.empty {
  padding: 50px; text-align: center; color: var(--muted);
  grid-column: 1 / -1;
}
@media(max-width: 760px) {
  .filters { grid-template-columns: 1fr 1fr; }
  .filters input { grid-column: 1 / -1; }
  main { padding: 18px 4%; }
}
</style>
</head>
<body>
<header>
  <h1>ExerciseBase RU</h1>
  <div class="subtitle">Библиотека упражнений · Русские названия · GIF-анимации</div>
</header>
<main>
  <section class="stats">
    <div class="stat"><strong id="total">0</strong><span>Всего упражнений</span></div>
    <div class="stat"><strong id="shown">0</strong><span>Найдено</span></div>
    <div class="stat"><strong id="gifCount">0</strong><span>GIF-анимаций</span></div>
  </section>

  <section class="filters">
    <input id="search" placeholder="Поиск по названию на русском или английском...">
    <select id="muscle"><option value="">Все мышцы</option></select>
    <select id="equipment"><option value="">Всё оборудование</option></select>
    <select id="type"><option value="">Все типы</option></select>
  </section>

  <div class="toolbar">
    <span id="resultText">Загрузка...</span>
    <button id="reset">Сбросить фильтры</button>
  </div>

  <section class="grid" id="grid"></section>
</main>

<script id="exercise-data" type="application/json">__DATA__</script>
<script>
const exercises = JSON.parse(document.getElementById("exercise-data").textContent);
const $ = id => document.getElementById(id);

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, c => ({
    "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;"
  })[c]);
}

function fillSelect(id, field, label) {
  const values = [...new Set(exercises.map(x => x[field]).filter(Boolean))].sort();
  values.forEach(value => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    $(id).appendChild(option);
  });
}

fillSelect("muscle", "muscle_group");
fillSelect("equipment", "equipment_category");
fillSelect("type", "exercise_type");

$("total").textContent = exercises.length;
$("gifCount").textContent = exercises.filter(x => x.gif_path).length;

function render() {
  const q = $("search").value.trim().toLocaleLowerCase("ru");
  const muscle = $("muscle").value;
  const equipment = $("equipment").value;
  const type = $("type").value;

  const filtered = exercises.filter(x => {
    const text = [x.name_ru, x.name_en, x.dataset_id]
      .join(" ").toLocaleLowerCase("ru");
    return (!q || text.includes(q))
      && (!muscle || x.muscle_group === muscle)
      && (!equipment || x.equipment_category === equipment)
      && (!type || x.exercise_type === type);
  });

  $("shown").textContent = filtered.length;
  $("resultText").textContent = `Показано ${filtered.length} из ${exercises.length}`;

  if (!filtered.length) {
    $("grid").innerHTML = '<div class="empty">Ничего не найдено. Измените запрос или фильтры.</div>';
    return;
  }

  $("grid").innerHTML = filtered.map(x => {
    const gif = x.gif_path
      ? `<img class="gif" src="../${esc(x.gif_path)}" loading="lazy" alt="${esc(x.name_ru)}">`
      : '<div class="gif"></div>';

    const steps = (x.instruction_steps_ru || [])
      .map(s => `<li>${esc(s.text)}</li>`).join("");

    const instructions = x.instructions_ru
      ? `<p>${esc(x.instructions_ru)}</p>` : "";

    return `
      <article class="card">
        ${gif}
        <div class="content">
          <div class="id">ID ${esc(x.dataset_id)}</div>
          <div class="name">${esc(x.name_ru)}</div>
          <div class="en">${esc(x.name_en)}</div>
          <div class="tags">
            <span class="tag">${esc(x.muscle_group)}</span>
            <span class="tag">${esc(x.equipment_category)}</span>
            <span class="tag">${esc(x.exercise_type)}</span>
          </div>
          <details>
            <summary>Инструкция и техника выполнения</summary>
            <div class="instructions">
              ${instructions}
              ${steps ? `<ol>${steps}</ol>` : ""}
            </div>
          </details>
        </div>
      </article>`;
  }).join("");
}

["search", "muscle", "equipment", "type"].forEach(id => {
  $(id).addEventListener(id === "search" ? "input" : "change", render);
});

$("reset").addEventListener("click", () => {
  $("search").value = "";
  $("muscle").value = "";
  $("equipment").value = "";
  $("type").value = "";
  render();
});

render();
</script>
</body>
</html>'''

html = html.replace("__DATA__", data)
html_path = OUT / "catalog.html"
html_path.write_text(html, encoding="utf-8")

print("КАТАЛОГ СОЗДАН")
print(f"Упражнений: {len(exercises)}")
print(f"JSON: {json_path}")
print(f"HTML: {html_path}")
print("GIF и инструкции включены.")
