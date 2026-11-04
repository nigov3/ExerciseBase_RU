#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hevy Library Builder RU: локальная галерея GIF, проверка названий и импорт в Hevy."""
import argparse, csv, html, json, os, re, sys, time, unicodedata
from pathlib import Path
from urllib.parse import quote
import requests

DATA_URL = "https://raw.githubusercontent.com/hasaneyldrm/exercises-dataset/main/data/exercises.json"
RAW_BASE = "https://raw.githubusercontent.com/hasaneyldrm/exercises-dataset/main/"
API_BASE = "https://api.hevyapp.com/v1"
ROOT = Path(__file__).resolve().parent
OUT, GIF_DIR = ROOT / "output", ROOT / "output" / "gifs"
CSV_PATH, HTML_PATH = OUT / "hevy_import_review.csv", OUT / "exercise_gallery.html"
S = requests.Session(); S.headers.update({"User-Agent": "Hevy-Library-Builder-RU/2.0"})

# Словарь намеренно консервативный: если уверенного соответствия нет, упражнение
# получает статус NEEDS_REVIEW и НЕ импортируется автоматически.
EXACT = {
"3/4 sit-up":"Подъём туловища на 3/4 амплитуды", "air bike":"Велосипед лёжа",
"alternating dumbbell curl":"Попеременное сгибание рук с гантелями",
"alternating dumbbell hammer curl":"Попеременное молотковое сгибание рук с гантелями",
"assisted pull-up":"Подтягивания в гравитроне", "back extension":"Гиперэкстензия",
"barbell bench press":"Жим штанги лёжа", "barbell curl":"Подъём штанги на бицепс",
"barbell deadlift":"Становая тяга со штангой", "barbell front squat":"Фронтальный присед со штангой",
"barbell squat":"Приседания со штангой", "bench dip":"Обратные отжимания от скамьи",
"bent over barbell row":"Тяга штанги в наклоне", "bent over dumbbell row":"Тяга гантели в наклоне",
"cable crossover":"Сведение рук в кроссовере", "cable curl":"Сгибание рук на нижнем блоке",
"cable crunch":"Скручивания на верхнем блоке", "cable lateral raise":"Махи рукой в сторону на блоке",
"cable pushdown":"Разгибание рук на верхнем блоке", "chest dip":"Отжимания на брусьях с акцентом на грудь",
"chest press":"Жим от груди в тренажёре", "close grip bench press":"Жим штанги узким хватом",
"concentration curl":"Концентрированное сгибание руки на бицепс", "crunch":"Скручивания на пресс",
"decline bench press":"Жим штанги лёжа на наклонной скамье головой вниз",
"decline crunch":"Скручивания на наклонной скамье головой вниз", "dips":"Отжимания на брусьях",
"dumbbell bench press":"Жим гантелей лёжа", "dumbbell chest fly":"Разведение гантелей лёжа",
"dumbbell curl":"Сгибание рук с гантелями на бицепс", "dumbbell fly":"Разведение гантелей",
"dumbbell hammer curl":"Молотковые сгибания рук с гантелями", "dumbbell lateral raise":"Махи гантелями в стороны",
"dumbbell pullover":"Пуловер с гантелью", "dumbbell romanian deadlift":"Румынская тяга с гантелями",
"dumbbell shoulder press":"Жим гантелей сидя", "dumbbell shrug":"Шраги с гантелями",
"ez bar curl":"Сгибание рук с EZ-грифом", "face pull":"Тяга каната к лицу",
"flat bench press":"Жим штанги лёжа", "front raise":"Подъём рук перед собой",
"glute bridge":"Ягодичный мост", "glute kickback":"Отведение ноги назад", "hip thrust":"Ягодичный мост со штангой",
"incline bench press":"Жим штанги на наклонной скамье", "incline dumbbell bench press":"Жим гантелей на наклонной скамье",
"incline dumbbell curl":"Сгибание рук с гантелями на наклонной скамье",
"incline dumbbell fly":"Разведение гантелей на наклонной скамье", "jumping jack":"Прыжки «джампинг-джек»",
"lat pulldown":"Тяга верхнего блока", "leg extension":"Разгибание ног в тренажёре",
"leg curl":"Сгибание ног в тренажёре", "leg press":"Жим ногами в тренажёре",
"lateral raise":"Махи руками в стороны", "machine chest press":"Жим от груди в тренажёре",
"machine shoulder press":"Жим вверх в тренажёре", "pec deck":"Сведение рук в тренажёре (бабочка)",
"preacher curl":"Сгибание рук на скамье Скотта", "pull up":"Подтягивания",
"push up":"Отжимания от пола", "reverse fly":"Разведение рук в наклоне",
"reverse grip lat pulldown":"Тяга верхнего блока обратным хватом", "romanian deadlift":"Румынская тяга",
" seated cable row":"Тяга горизонтального блока сидя", "seated cable row":"Тяга горизонтального блока сидя",
"seated row":"Горизонтальная тяга в тренажёре", "shoulder press":"Жим вверх",
"shrug":"Шраги", "skullcrusher":"Французский жим лёжа", "standing calf raise":"Подъём на носки стоя",
"triceps dip":"Отжимания на брусьях с акцентом на трицепс", "triceps pushdown":"Разгибание рук на верхнем блоке",
"upright row":"Тяга штанги к подбородку", "wide grip lat pulldown":"Тяга верхнего блока широким хватом",
"wide grip pull up":"Подтягивания широким хватом", "wrist curl":"Сгибание кистей рук",
}

# Небольшие безопасные нормализации распространённых вариантов написания.
ALIASES = {"barbell romanian deadlift":"Румынская тяга со штангой", "dumbbell romanian deadlift":"Румынская тяга с гантелями",
"cable triceps pushdown":"Разгибание рук на верхнем блоке", "rope triceps pushdown":"Разгибание рук с канатом на верхнем блоке",
"rope pushdown":"Разгибание рук с канатом на верхнем блоке", "machine pec deck":"Сведение рук в тренажёре (бабочка)",
"smith machine squat":"Приседания в машине Смита", "smith machine bench press":"Жим лёжа в машине Смита"}

def norm(v):
    v=unicodedata.normalize('NFKD',str(v or '')).casefold()
    v=''.join(c for c in v if not unicodedata.combining(c))
    v=re.sub(r'[^a-zа-яё0-9]+',' ',v,flags=re.I)
    return ' '.join(v.split())

def get_json(url, headers=None, params=None):
    r=S.get(url,headers=headers,params=params,timeout=60); r.raise_for_status(); return r.json()

def headers_hevy():
    key=os.getenv('HEVY_API_KEY','').strip()
    if not key: raise RuntimeError('Не найдена HEVY_API_KEY. Задай переменную в PowerShell в этом же окне.')
    return {'api-key':key,'accept':'application/json','content-type':'application/json'}

def fetch_templates():
    out=[]; page=1
    while page<=100:
        data=get_json(f'{API_BASE}/exercise_templates',headers=headers_hevy(),params={'page':page,'pageSize':100})
        if isinstance(data,list): batch=data; meta={}
        else:
            batch=next((data.get(k) for k in ('exercise_templates','exercises','data','results') if isinstance(data.get(k),list)),None)
            if batch is None: raise RuntimeError('Неожиданный ответ Hevy API: '+str(data)[:700])
            meta=data
        if not batch: break
        out.extend(batch)
        pages=meta.get('page_count') or meta.get('total_pages')
        if (pages and page>=int(pages)) or len(batch)<100: break
        page+=1
    unique=[]; seen=set()
    for x in out:
        k=str(x.get('id') or norm(x.get('title') or x.get('name')))
        if k not in seen: seen.add(k); unique.append(x)
    return unique

# Правила для продуктивных сочетаний. Они покрывают варианты одного движения
# с разным оборудованием, положением тела и хватом. Неизвестные слова блокируют
# автоперевод, чтобы не создавать ложные русские названия.
EQUIP_RU = {
    'barbell':'со штангой', 'dumbbell':'с гантелями', 'cable':'на блоке',
    'machine':'в тренажёре', 'smith machine':'в машине Смита',
    'kettlebell':'с гирей', 'resistance band':'с резиновой лентой',
    'ez bar':'с EZ-грифом', 'ez barbell':'с EZ-грифом',
}
POSITION_RU = {
    'seated':'сидя', 'standing':'стоя', 'lying':'лёжа', 'incline':'на наклонной скамье',
    'decline':'на скамье с отрицательным наклоном', 'bent over':'в наклоне',
    'single arm':'одной рукой', 'one arm':'одной рукой', 'alternating':'попеременно',
    'reverse grip':'обратным хватом', 'wide grip':'широким хватом',
    'close grip':'узким хватом', 'neutral grip':'нейтральным хватом',
    'underhand':'обратным хватом', 'overhand':'прямым хватом',
}
# Основа движения -> русское название. Сначала более длинные фразы.
ACTION_RU = {
    'romanian deadlift':'румынская тяга', 'stiff leg deadlift':'становая тяга на прямых ногах',
    'straight leg deadlift':'становая тяга на прямых ногах', 'sumo deadlift':'становая тяга сумо',
    'deadlift':'становая тяга', 'bench press':'жим лёжа', 'chest press':'жим от груди',
    'shoulder press':'жим вверх', 'overhead press':'жим над головой',
    'incline press':'жим на наклонной скамье', 'decline press':'жим на скамье с отрицательным наклоном',
    'floor press':'жим с пола', 'close grip press':'жим узким хватом',
    'lat pulldown':'тяга верхнего блока', 'pulldown':'тяга верхнего блока',
    'pull down':'тяга верхнего блока', 'seated row':'горизонтальная тяга сидя',
    'cable row':'тяга горизонтального блока', 'bent over row':'тяга в наклоне',
    'upright row':'тяга к подбородку', 'face pull':'тяга каната к лицу',
    'rear delt fly':'разведение на заднюю дельту', 'reverse fly':'обратные разведения',
    'chest fly':'разведение рук на грудь', 'pec fly':'сведение рук на грудь',
    'fly':'разведение рук', 'lateral raise':'подъём рук в стороны',
    'front raise':'подъём рук перед собой', 'rear delt raise':'разведение на заднюю дельту',
    'bicep curl':'сгибание рук на бицепс', 'hammer curl':'молотковые сгибания',
    'preacher curl':'сгибание рук на скамье Скотта', 'concentration curl':'концентрированное сгибание руки',
    'reverse curl':'обратное сгибание рук', 'wrist curl':'сгибание кистей',
    'triceps pushdown':'разгибание рук на трицепс', 'triceps extension':'разгибание рук на трицепс',
    'overhead extension':'разгибание рук из-за головы', 'skull crusher':'французский жим',
    'leg press':'жим ногами', 'leg extension':'разгибание ног', 'leg curl':'сгибание ног',
    'hamstring curl':'сгибание ног на бицепс бедра', 'calf raise':'подъём на носки',
    'standing calf raise':'подъём на носки стоя', 'seated calf raise':'подъём на носки сидя',
    'squat':'приседание', 'front squat':'фронтальное приседание', 'goblet squat':'приседание с гирей у груди',
    'split squat':'раздельное приседание', 'bulgarian split squat':'болгарские выпады',
    'lunge':'выпад', 'reverse lunge':'обратный выпад', 'walking lunge':'выпады в ходьбе',
    'hip thrust':'ягодичный мост с опорой на скамью', 'glute bridge':'ягодичный мост',
    'glute kickback':'отведение ноги назад', 'hip abduction':'отведение бедра',
    'hip adduction':'приведение бедра', 'back extension':'разгибание спины',
    'hyperextension':'гиперэкстензия', 'crunch':'скручивание на пресс',
    'sit up':'подъём туловища', 'leg raise':'подъём ног', 'knee raise':'подъём коленей',
    'hanging leg raise':'подъём ног в висе', 'plank':'планка', 'side plank':'боковая планка',
    'push up':'отжимание', 'pushup':'отжимание', 'pull up':'подтягивание', 'pullup':'подтягивание',
    'chin up':'подтягивание обратным хватом', 'dip':'отжимание на брусьях',
    'shrug':'шраг', 'farmers walk':'прогулка фермера', 'mountain climber':'альпинист',
    'jumping jack':'прыжки «джампинг-джек»', 'burpee':'берпи', 'good morning':'наклон со штангой на плечах',
}

def translate_composite(en):
    raw = re.sub(r'\([^)]*\)', ' ', str(en)).strip()
    k = norm(raw)
    # Сначала ищем известную основу движения в конце названия.
    actions = sorted(ACTION_RU, key=len, reverse=True)
    action = next((a for a in actions if k == a or k.endswith(' '+a)), None)
    if not action:
        return '', 'NEEDS_REVIEW'
    prefix = k[:-len(action)].strip()
    # Порядок слов в исходных названиях обычно: положение + оборудование + движение.
    equipment = next((e for e in sorted(EQUIP_RU, key=len, reverse=True) if e in prefix), None)
    positions = [x for x in sorted(POSITION_RU, key=len, reverse=True) if x in prefix]
    # Удаляем только распознанные фрагменты. Любой остаток делает перевод ручным.
    rest = prefix
    if equipment:
        rest = re.sub(r'(?<![a-z])'+re.escape(equipment)+r'(?![a-z])', ' ', rest)
    for pos in positions:
        rest = re.sub(r'(?<![a-z])'+re.escape(pos)+r'(?![a-z])', ' ', rest)
    rest = re.sub(r'\b(the|with|and|to|for)\b', ' ', rest)
    rest = ' '.join(rest.split())
    # Разрешённые технические уточнения, для которых перевод не меняет сути.
    if rest:
        return '', 'NEEDS_REVIEW'
    base = ACTION_RU[action]
    # Упорядочиваем русские уточнения: положение, оборудование, хват.
    pos_ru=[]
    for pos in positions:
        val=POSITION_RU[pos]
        if val not in pos_ru: pos_ru.append(val)
    if equipment:
        eq=EQUIP_RU[equipment]
        # Естественные русские сочетания для наиболее частых движений.
        if equipment in ('barbell','dumbbell','kettlebell','ez bar','ez barbell','resistance band'):
            base += ' ' + eq
        elif equipment in ('cable','machine','smith machine'):
            base += ' ' + eq
    if pos_ru:
        base += ' (' + ', '.join(pos_ru) + ')'
    # Названия без equipment/position тоже допустимы, если основа однозначна.
    return base[:1].upper()+base[1:], 'RULE'

def translate_title(en):
    key=norm(en)
    if key in EXACT: return EXACT[key], 'DICT'
    if key in ALIASES: return ALIASES[key], 'DICT'
    return translate_composite(en)

def muscle(ex):
    raw=ex.get('target') or ex.get('muscle_group') or ex.get('body_part') or ''
    if isinstance(raw,list): raw=raw[0] if raw else ''
    k=norm(raw)
    m={'chest':'chest','pectorals':'chest','pectoralis major':'chest','biceps':'biceps','triceps':'triceps','lats':'lats','latissimus dorsi':'lats','back':'upper_back','upper back':'upper_back','traps':'traps','trapezius':'traps','shoulders':'shoulders','deltoids':'shoulders','delts':'shoulders','abs':'abdominals','abdominals':'abdominals','quadriceps':'quadriceps','quads':'quadriceps','hamstrings':'hamstrings','glutes':'glutes','calves':'calves','forearms':'forearms','neck':'neck','cardio':'cardio'}
    return m.get(k,'other')

def equipment(ex):
    raw=ex.get('equipment') or ''; k=norm(raw)
    m={'body weight':'none','bodyweight':'none','none':'none','dumbbell':'dumbbell','barbell':'barbell','ez barbell':'barbell','olympic barbell':'barbell','kettlebell':'kettlebell','cable':'machine','leverage machine':'machine','machine':'machine','smith machine':'machine','band':'resistance_band','resistance band':'resistance_band','suspension':'suspension','trx':'suspension','weighted':'plate','weight plate':'plate'}
    return m.get(k,'other')

def ex_type(ex):
    n=norm(ex.get('name')); ins=norm((ex.get('instructions') or {}).get('en',''))
    if any(x in n+' '+ins[:200] for x in ('plank','hold','isometric','wall sit','dead hang')): return 'duration'
    if norm(ex.get('equipment')) in ('body weight','bodyweight','none',''): return 'bodyweight_reps'
    return 'weight_reps'

def download_gif(ex):
    rel=ex.get('gif_url') or ''
    if not rel and ex.get('media_id'): rel='videos/'+str(ex['id'])+'-'+str(ex['media_id'])+'.gif'
    if not rel: return ''
    url=rel if rel.startswith('http') else RAW_BASE+rel.lstrip('/')
    fn=Path(rel.split('?')[0]).name
    if not fn.lower().endswith('.gif'): return url
    safe=re.sub(r'[^A-Za-z0-9._-]+','_',fn); target=GIF_DIR/safe
    if not target.exists():
        for attempt in range(3):
            try:
                r=S.get(url,timeout=60); r.raise_for_status()
                if r.content[:6] not in (b'GIF87a',b'GIF89a'): return url
                target.write_bytes(r.content); break
            except Exception as e:
                if attempt==2: print(f'  GIF пропущен: {fn}: {e}')
                else: time.sleep(2*(attempt+1))
    return 'gifs/'+quote(safe) if target.exists() else url

def apply_existing_csv(limit=0):
    import_csv = OUT / "hevy_import_ready.csv"

    if not import_csv.exists():
        raise RuntimeError(
            'Файл hevy_import_ready.csv не найден. '
            'Сначала запусти: python prepare_import.py'
        )

    with import_csv.open(newline='', encoding='utf-8-sig') as f:
        selected = [
            r for r in csv.DictReader(f)
            if r.get('import', '').strip().upper() == 'YES'
            and r.get('name_ru', '').strip()
        ]

    if limit > 0:
        selected = selected[:limit]

    if not selected:
        print('Нет строк с import=YES и заполненным name_ru.')
        return

    print(f'Будет создано упражнений: {len(selected)}')

    if input('Для подтверждения введи IMPORT: ').strip() != 'IMPORT':
        print('Отменено. Ничего не отправлено в Hevy.')
        return

    h = headers_hevy()
    ok = bad = 0

    for i, r in enumerate(selected, 1):
        payload = {
            'exercise': {
                'title': r['name_ru'],
                'exercise_type': r['exercise_type'],
                'equipment_category': r['equipment_category'],
                'muscle_group': r['muscle_group'],
                'other_muscles': []
            }
        }

        try:
            resp = S.post(
                f'{API_BASE}/exercise_templates',
                headers=h,
                json=payload,
                timeout=45
            )

            if resp.status_code in (200, 201):
                ok += 1
                print(f'[{i}/{len(selected)}] OK: {r["name_ru"]}')
            else:
                bad += 1
                print(f'[{i}/{len(selected)}] ERROR {resp.status_code}: {resp.text[:250]}')

        except Exception as e:
            bad += 1
            print(f'[{i}/{len(selected)}] ERROR: {e}')

        time.sleep(.3)

    print(f'Импорт завершён. Успешно: {ok}; ошибок: {bad}.')
    print('GIF и инструкции остаются в локальной галерее/CSV.')

def main():
    p=argparse.ArgumentParser(); p.add_argument('--no-gifs',action='store_true'); p.add_argument('--apply',action='store_true'); p.add_argument('--limit',type=int,default=0); a=p.parse_args()
    OUT.mkdir(exist_ok=True); GIF_DIR.mkdir(exist_ok=True)
    if a.apply:
        apply_existing_csv(a.limit)
        return
    print('Скачиваю каталог упражнений...'); dataset=get_json(DATA_URL)
    print('В каталоге:',len(dataset)); templates=fetch_templates(); print('Шаблонов в Hevy:',len(templates))
    existing={norm(x.get('title') or x.get('name')) for x in templates}; rows=[]
    for i,ex in enumerate(dataset,1):
        en=str(ex.get('name') or '').strip()
        if not en: continue
        ru,status=translate_title(en); duplicate=norm(en) in existing
        gif=(RAW_BASE+(ex.get('gif_url') or '').lstrip('/')) if a.no_gifs and ex.get('gif_url') else ('' if a.no_gifs else download_gif(ex))
        ins=ex.get('instructions') or {}; steps=ex.get('instruction_steps') or {}
        ins_ru=ins.get('ru','') if isinstance(ins,dict) else ''
        steps_ru=steps.get('ru',[]) if isinstance(steps,dict) else []
        rows.append({'import':'NO' if duplicate or not ru else 'YES','status':'DUPLICATE' if duplicate else ('NEW' if ru else 'NEEDS_REVIEW'),'name_en':en,'name_ru':ru,'translation_status':status,'exercise_type':ex_type(ex),'equipment_category':equipment(ex),'muscle_group':muscle(ex),'instructions_ru':ins_ru,'instruction_steps_ru':' | '.join(steps_ru) if isinstance(steps_ru,list) else '', 'gif':gif,'attribution':ex.get('attribution','© Gym visual — https://gymvisual.com/'),'dataset_id':ex.get('id','')})
        if not duplicate: existing.add(norm(en))
    fields=list(rows[0]) if rows else []
    with CSV_PATH.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
    cards=[]
    for r in rows:
        src=html.escape(r['gif'],quote=True); media=f'<img loading="lazy" src="{src}" alt="">' if src else '<div class="missing">GIF нет</div>'
        title=r['name_ru'] or ('ПЕРЕВОД ПРОВЕРИТЬ: '+r['name_en'])
        cards.append(f'<article data-status="{r["status"]}">{media}<h3>{html.escape(title)}</h3><p>{html.escape(r["name_en"])}</p><small>{r["status"]} · {html.escape(r["muscle_group"])}</small></article>')
    HTML_PATH.write_text('<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Hevy RU</title><style>body{margin:0;background:#111318;color:#eee;font:15px Arial;padding:24px}header{position:sticky;top:0;background:#111318;padding:12px 0;z-index:2}input,select{padding:12px;background:#242832;color:white;border:1px solid #444;border-radius:8px;margin:4px}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:16px}article{background:#1c2029;padding:12px;border-radius:12px;overflow:hidden}img{width:100%;aspect-ratio:1;object-fit:contain;background:#08090c;border-radius:8px}h3{font-size:15px;margin:10px 0 6px}p,small{color:#aab1c0}.missing{height:180px;display:grid;place-items:center;background:#08090c}</style><header><h1>Библиотека упражнений</h1><input id="q" placeholder="Поиск"><select id="f"><option value="">Все</option><option>NEW</option><option>DUPLICATE</option><option>NEEDS_REVIEW</option></select></header><div class="grid">'+''.join(cards)+'</div><script>function filter(){let q=document.getElementById("q").value.toLowerCase(),f=document.getElementById("f").value;document.querySelectorAll("article").forEach(x=>x.style.display=(x.innerText.toLowerCase().includes(q)&&(!f||x.dataset.status===f))?"":"none")}document.getElementById("q").oninput=filter;document.getElementById("f").onchange=filter</script></html>',encoding='utf-8')
    new=sum(x['status']=='NEW' for x in rows); dup=sum(x['status']=='DUPLICATE' for x in rows); review=sum(x['status']=='NEEDS_REVIEW' for x in rows)
    rules=sum(x['translation_status']=='RULE' for x in rows); exact=sum(x['translation_status']=='DICT' for x in rows)
    print(f'Готово: {len(rows)} строк; словарь: {exact}; правила: {rules}; дубликаты: {dup}; требуют проверки: {review}')
    print('CSV:',CSV_PATH); print('Галерея:',HTML_PATH); print('GIF:',GIF_DIR)
    if not a.apply:
        print('\nПредварительный режим. В Hevy ничего не создано.')
        print('В CSV можно вручную заполнить name_ru и поставить import=YES только после проверки.')
        return
    with CSV_PATH.open(newline='',encoding='utf-8-sig') as f: selected=[r for r in csv.DictReader(f) if r['import'].strip().upper()=='YES' and r['name_ru'].strip()]
    if a.limit>0: selected=selected[:a.limit]
    if not selected: print('Нет проверенных строк с import=YES.'); return
    print('Будет создано:',len(selected));
    if input('Для подтверждения введи IMPORT: ').strip()!='IMPORT': print('Отменено.'); return
    h=headers_hevy(); ok=bad=0
    for i,r in enumerate(selected,1):
        payload={'exercise':{'title':r['name_ru'],'exercise_type':r['exercise_type'],'equipment_category':r['equipment_category'],'muscle_group':r['muscle_group'],'other_muscles':[]}}
        try:
            resp=S.post(f'{API_BASE}/exercise_templates',headers=h,json=payload,timeout=45)
            if resp.status_code in (200,201): ok+=1; print(f'[{i}/{len(selected)}] OK: {r["name_ru"]}')
            else: bad+=1; print(f'[{i}/{len(selected)}] ERROR {resp.status_code}: {resp.text[:250]}')
        except Exception as e: bad+=1; print('ERROR:',e)
        time.sleep(.3)
    print(f'Импорт завершён. Успешно: {ok}; ошибок: {bad}. GIF остаются локально, API Hevy не прикрепляет их к карточкам.')

if __name__=='__main__':
    try: main()
    except requests.HTTPError as e:
        print('HTTP ошибка:',e); print(e.response.text[:1000] if e.response is not None else ''); sys.exit(1)
    except Exception as e: print('Ошибка:',e); sys.exit(1)
