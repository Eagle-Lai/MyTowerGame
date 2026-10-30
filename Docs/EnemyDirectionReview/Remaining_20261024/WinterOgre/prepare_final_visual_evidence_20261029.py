"""WinterOgre-only native-loop correction and provenance-preserving review boards."""
from session_winterogre import *
from PIL import Image, ImageDraw
import math, shutil
import numpy as np

owner()
RUNS = ['runtime_r01', 'runtime_updeath_r01']
OUT = D / 'visual_review_art_r01_20261029'
BACK = D / 'media_before_native_loop_fix_20261029'
assert not OUT.exists() and not BACK.exists()
OUT.mkdir(); BACK.mkdir()
contract = read(D / 'source_contract_20261029.json')['contract']
clip = next(c for c in contract['clips'] if c['name'] == 'Walk')
seconds = clip['length']
assert clip['loop'] and abs(seconds - 2 / 3) < 1e-5
cycle_ms = round(seconds * 100) * 10  # GIF centisecond resolution: 670 ms.
corrections = []
sources = []
originals = []
gif_samples = []
uncropped = []

def pick(rows, count):
    return [rows[round((len(rows) - 1) * i / (count - 1))] for i in range(count)]

def labeled(folder, record, text):
    im = Image.open(folder / record['file']).convert('RGB')
    im = im.resize((512, 512), Image.Resampling.LANCZOS)
    ImageDraw.Draw(im).text((12, 12), text, fill='white')
    return im

def centisecond_durations(phases):
    marks = [round((p - phases[0]) * seconds * 100) * 10 for p in phases]
    durations = [b - a for a, b in zip(marks, marks[1:] + [cycle_ms])]
    assert all(d >= 10 for d in durations) and sum(durations) == cycle_ms
    return durations

def board(run, tag, rows, columns=6):
    width, height = 220, 248
    sheet = Image.new('RGB', (width * columns, height * math.ceil(len(rows) / columns)), (40, 48, 37))
    for i, record in enumerate(rows):
        path = D / run / record['file']
        im = Image.open(path).convert('RGB')
        # Fixed crop excludes labels and HP only, retaining the complete actor and its motion.
        crop = (160, 270, 620, 750)
        sample = im.crop(crop); sample.thumbnail((210, 218), Image.Resampling.LANCZOS)
        x, y = (i % columns) * width, (i // columns) * height
        sheet.paste(sample, (x + (width - sample.width) // 2, y + 30))
        ImageDraw.Draw(sheet).text((x + 4, y + 3), f"{record['stage']} f{record['frame']}\n{record['facing']} n={record['normalizedTime']:.3f} a={record['alpha']:.2f}", fill='white')
        sources.append({'revision': run, 'source': record['file'], 'source_sha256': sha(path),
                        'board': f'{tag}.png', 'position': i, 'crop': list(crop),
                        'frame': record['frame'], 'stage': record['stage']})
    sheet.save(OUT / f'{tag}.png')

for run in RUNS:
    folder = D / run
    records = [json.loads(l) for l in (folder / 'actual_frames.jsonl').read_text(encoding='utf-8').splitlines() if l]
    groups = {stage: [r for r in records if r['stage'] == stage] for stage in dict.fromkeys(r['stage'] for r in records)}
    backup = BACK / run; backup.mkdir()
    for name in ['UpWalk.gif', 'DownWalk.gif', 'up_down_walk.gif', 'media_manifest.json']:
        shutil.copy2(folder / name, backup / name)
    manifest = read(folder / 'media_manifest.json')
    cycles = {}
    for stage in ['UpWalk', 'DownWalk']:
        rows = [r for r in groups[stage] if r['state'] == 'Walk']
        start = math.ceil(rows[0]['normalizedTime'])
        selected = [r for r in rows if start <= r['normalizedTime'] < start + 1]
        assert len(selected) >= 10
        durations = centisecond_durations([r['normalizedTime'] for r in selected])
        frames = [labeled(folder, r, f"WinterOgre - native Walk {seconds:.3f}s | {stage}") for r in selected]
        name = stage + '.gif'
        frames[0].save(folder / name, save_all=True, append_images=frames[1:], duration=durations,
                       loop=0, optimize=False, disposal=2)
        item = next(m for m in manifest['media'] if m['file'] == name)
        item.update(real_frames=len(selected), first_unity_frame=selected[0]['frame'], last_unity_frame=selected[-1]['frame'],
                    durations_ms=durations, normalized_time_interval=[start, start + 1],
                    source_frames=[r['file'] for r in selected], native_clip_seconds=seconds,
                    encoded_cycle_ms=cycle_ms, note='Actual recorded native cycle; GIF centisecond quantization; no synthesized pose.')
        cycles[stage] = selected
    frames = []; pairs = []
    for i in range(10):
        pair = Image.new('RGB', (1024, 512)); selected_sources = []
        for column, stage in enumerate(['UpWalk', 'DownWalk']):
            def distance(r):
                delta = abs((r['normalizedTime'] % 1) - i / 10)
                return min(delta, 1 - delta)
            r = min(cycles[stage], key=distance)
            pair.paste(labeled(folder, r, f"WinterOgre {r['facing']} - native Walk {seconds:.3f}s"), (column * 512, 0))
            selected_sources.append(r['file'])
        frames.append(pair); pairs.append(selected_sources)
    durations = centisecond_durations([i / 10 for i in range(10)])
    frames[0].save(folder / 'up_down_walk.gif', save_all=True, append_images=frames[1:], duration=durations,
                   loop=0, optimize=False, disposal=2)
    next(m for m in manifest['media'] if m['file'] == 'up_down_walk.gif').update(
        actual_frame_pairs=pairs, durations_ms=durations, native_clip_seconds=seconds, encoded_cycle_ms=cycle_ms,
        note='Nearest actual native phases side by side; no synthesized poses; 670ms GIF represents native 666.667ms.')
    manifest['winterogre_native_loop_correction'] = {'native_clip_path': clip['path'], 'native_seconds': seconds,
        'encoded_cycle_ms': cycle_ms, 'source_contract_sha256': sha(D / 'source_contract_20261029.json'),
        'original_media_backup': backup.relative_to(D).as_posix()}
    write(folder / 'media_manifest.json', manifest)
    for name in ['UpWalk.gif', 'DownWalk.gif', 'up_down_walk.gif']:
        with Image.open(folder / name) as gif:
            encoded_ms = 0
            for j in range(gif.n_frames):
                gif.seek(j); encoded_ms += gif.info['duration']
        assert encoded_ms == cycle_ms
        corrections.append({'revision': run, 'file': name, 'before_sha256': sha(backup / name),
                            'after_sha256': sha(folder / name), 'actual_encoded_cycle_ms': encoded_ms})
    sets = [ ['UpWalk','DownWalk','LeftWalk','RightWalk'], ['Idle','Ready','Walk','Run'],
             ['Attack','Hurt','DeathAutoRecycle','Reuse'], ['Pause','Resume1x','Speed2x','Speed3x'] ]
    for number, stages in enumerate(sets):
        board(run, f'{run}_sequence_{number}', [r for stage in stages for r in pick(groups[stage], 6)])
    board(run, f'{run}_turns_flying', pick(groups['ContinuousTurns'], 12) + pick(groups['Flying'], 6))
    board(run, f'{run}_walk_cycle', cycles['UpWalk'] + cycles['DownWalk'])
    selected = [pick(groups['UpWalk'], 3)[1], pick(groups['DownWalk'], 3)[1],
                next(r for r in groups['Attack'] if r['expression'] == 1),
                next(r for r in groups['DeathAutoRecycle'] if r['alpha'] < 0.85 and r['alpha'] > 0.3)]
    originals.extend(f"{run}/{r['file']}" for r in selected)
    cells = []
    for path in sorted(folder.glob('*.gif')):
        with Image.open(path) as gif:
            indices = sorted(set(round((gif.n_frames - 1) * i / 4) for i in range(5)))
            crop = (95, 175, gif.width - 95, gif.height - 10)
            for index in indices:
                gif.seek(index); im = gif.convert('RGB').crop(crop)
                im.thumbnail((300, 215), Image.Resampling.LANCZOS)
                cell = Image.new('RGB', (320, 250), (40, 48, 37)); cell.paste(im, ((320 - im.width) // 2, 30 + (215 - im.height) // 2))
                ImageDraw.Draw(cell).text((6, 5), f'{path.name} f{index}', fill='white'); cells.append(cell)
                gif_samples.append({'revision':run,'file':path.name,'gif_sha256':sha(path),'frame_index_zero_based':index,
                                    'frame_count':gif.n_frames,'duration_ms':gif.info.get('duration'), 'stable_crop':list(crop),
                                    'sample_sha256':hashlib.sha256(im.tobytes()).hexdigest().upper()})
            if path.name in ['UpWalk.gif', 'attack_death_reuse.gif']:
                index = gif.n_frames // 2; gif.seek(index)
                dest = OUT / (run + '_' + path.stem + '_uncropped.png')
                gif.convert('RGB').save(dest)
                uncropped.append({'source':path.relative_to(D).as_posix(),'source_sha256':sha(path),'frame':index,
                                  'output':dest.relative_to(D).as_posix(),'output_sha256':sha(dest)})
    sheet = Image.new('RGB', (1600, 1500), (40, 48, 37))
    assert len(cells) == 30
    for i, cell in enumerate(cells): sheet.paste(cell, ((i % 5) * 320, (i // 5) * 250))
    sheet.save(OUT / (run + '_gif_samples.png'))

write(D / 'native_walk_media_fix_20261029.json', {'observed_at':now(),'native_clip_seconds':seconds,
    'encoded_cycle_ms':cycle_ms,'changes':corrections,'shared_code_modified':False,'production_modified':False},fresh=True)
write(OUT / 'sources.json', {'sources':sources,'method':'Chronological selection from real PNG; fixed crop; no pose synthesis.'},fresh=True)
write(OUT / 'gif_samples.json', {'samples':gif_samples,'method':'Five encoded frames/file; chronological sampling, not live playback or every-frame review.'},fresh=True)
write(OUT / 'uncropped_gif_sources.json', uncropped,fresh=True)
write(D / 'original_png_selection_20261029.json', originals,fresh=True)
print(json.dumps({'native_seconds':seconds,'encoded_ms':cycle_ms,'boards':len(list(OUT.glob('*.png'))),
                  'board_positions':len(sources),'gif_samples':len(gif_samples),'original_pngs':len(originals)},ensure_ascii=False))
