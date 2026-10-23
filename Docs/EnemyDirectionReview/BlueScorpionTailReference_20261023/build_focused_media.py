"""Crop/scale actual Play captures; retain native poses and frame provenance."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json, math

HERE = Path(__file__).resolve().parent
BATCH = HERE.parent / 'Batch01_10/BlueScorpion'
FONT = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 19)
SMALL = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 14)
BG = (38, 47, 34)
SOURCES = {}
PROVENANCE = []

def source(revision):
    folder = BATCH / revision
    if 'FAIL ' in (folder / 'actual_runtime_checks.txt').read_text():
        raise ValueError('Failed runtime revision: ' + revision)
    rows = [json.loads(s) for s in (folder / 'actual_frames.jsonl').read_text().splitlines()]
    assert all(b['frame'] > a['frame'] for a, b in zip(rows, rows[1:]))
    first = next(r for r in rows if r['stage'] == 'UpWalk')
    im = Image.open(folder / first['file']).convert('RGB')
    # HP bar is unchanged in world space. Its pixel width removes camera-zoom differences.
    green = [(x, y) for y in range(65, 220) for x in range(im.width)
             if (lambda c: c[0] < 110 and c[1] > 170 and c[2] < 140)(im.getpixel((x, y)))]
    assert green, 'Missing unchanged HP reference'
    xs, ys = zip(*green)
    anchor = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
    width = max(xs) - min(xs) + 1
    SOURCES[revision] = {'folder': folder, 'rows': rows, 'anchor': anchor, 'width': width}
    return SOURCES[revision]

def panel(revision, row, title, width=640, height=700):
    src = SOURCES[revision]
    im = Image.open(src['folder'] / row['file']).convert('RGB')
    # Same HP width = same pixels per world unit in both before/after panels.
    ratio = 230 / src['width']
    scaled = im.resize((round(im.width * ratio), round(im.height * ratio)), Image.Resampling.LANCZOS)
    out = Image.new('RGB', (width, height), BG)
    out.paste(scaled, (round(width / 2 - src['anchor'][0] * ratio), round(86 - src['anchor'][1] * ratio)))
    draw = ImageDraw.Draw(out)
    draw.rectangle((0, 0, width, 62), fill=BG)
    draw.text((16, 12), title, font=FONT, fill='white')
    draw.text((16, 40), 'Unity 实际运行帧 · ' + row['facing'], font=SMALL, fill='#c4cabd')
    draw.rectangle((0, height-32, width, height), fill=BG)
    draw.text((16, height-26), f"{row['stage']} · frame {row['frame']}", font=SMALL, fill='#c4cabd')
    PROVENANCE.append({'revision': revision, 'file': row['file'], 'unity_frame': row['frame'],
                       'native_normalized_time': row['normalizedTime'], 'scale': ratio,
                       'hp_reference_width': src['width'], 'target_hp_width': 230})
    return out

def walk_cycle(src):
    rows = [r for r in src['rows'] if r['stage'] == 'UpWalk' and r['state'] == 'Walk']
    start = math.ceil(rows[0]['normalizedTime'])
    return [r for r in rows if start <= r['normalizedTime'] < start + 1]

old = 'runtime_tailup_r01'
new = 'runtime_tailref_r02'
updeath = 'runtime_tailref_updeath_r02'
for revision in [old, new, updeath]:
    source(revision)

cycles = {rev: walk_cycle(SOURCES[rev]) for rev in [old, new]}
paired = []
for i in range(12):
    sheet = Image.new('RGB', (1280, 700), BG)
    for column, rev, label in [(0, old, '上一轮：尾梢向内扣'), (1, new, '本轮：参考图的高拱后尾')]:
        def distance(r):
            delta = abs(r['normalizedTime'] % 1 - i / 12)
            return min(delta, 1 - delta)
        row = min(cycles[rev], key=distance)
        sheet.paste(panel(rev, row, label), (640 * column, 0))
    paired.append(sheet)
paired[3].save(HERE / 'tail_before_after.png')
paired[0].save(HERE / 'tail_before_after.gif', save_all=True, append_images=paired[1:],
               duration=[40, 40, 40, 40, 50, 40, 40, 40, 40, 50, 40, 40], loop=0, disposal=2)

rows = cycles[new]
frames = [panel(new, r, 'BlueScorpion 朝上行走 · 尾巴修正') for r in rows]
durations = [max(10, round((b['normalizedTime'] - a['normalizedTime']) * 500)) for a, b in zip(rows, rows[1:])]
durations.append(max(10, 500 - sum(durations)))
frames[0].save(HERE / 'up_walk_fixed.gif', save_all=True, append_images=frames[1:], duration=durations, loop=0, disposal=2)
frames[len(frames)//3].save(HERE / 'up_walk_fixed.png')
walk_sheet = Image.new('RGB', (1920, 1400), BG)
for i in range(6):
    walk_sheet.paste(frames[round((len(frames)-1)*i/5)], ((i % 3)*640, (i // 3)*700))
walk_sheet.save(HERE / 'up_walk_fixed_phases.png')

def action(rev, stage, stem, title):
    rows = [r for r in SOURCES[rev]['rows'] if r['stage'] == stage and r['facing'] == 'Up']
    assert len(rows) >= 4
    images = [panel(rev, r, title) for r in rows]
    durations = [max(10, min(500, round((b['realtime']-a['realtime'])*1000))) for a, b in zip(rows, rows[1:])]
    durations.append(500)
    images[0].save(HERE / (stem+'.gif'), save_all=True, append_images=images[1:], duration=durations, loop=0, disposal=2)
    selected = [round((len(rows)-1)*f) for f in [0, .2, .4, .6, .8, 1]]
    sheet = Image.new('RGB', (1920, 1400), BG)
    for i, index in enumerate(selected):
        sheet.paste(images[index], ((i % 3)*640, (i // 3)*700))
    sheet.save(HERE / (stem+'_phases.png'))

action(new, 'Attack', 'up_attack_fixed', '朝上攻击 · 尾根连接检查')
action(updeath, 'DeathAutoRecycle', 'up_death_fixed', '朝上死亡 · 尾部随身体淡出')
(HERE / 'focused_media_manifest.json').write_text(json.dumps({
    'source_type': 'Final installed prefab; actual Unity Play frames',
    'processing': 'Crop, uniform resize and labels only. Old/new world scale normalized using unchanged HP bar; no synthesized poses.',
    'old_revision': old, 'new_revision': new, 'up_death_revision': updeath,
    'frames': PROVENANCE}, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'output': str(HERE), 'placed_actual_frames': len(PROVENANCE)}))
