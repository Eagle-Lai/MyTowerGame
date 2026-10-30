from session_current import *
from PIL import Image, ImageDraw, ImageFilter
from collections import deque
import numpy as np, shutil, subprocess

owner()
for p in ['art_selection.json', 'layout_adjustments.json', 'parts_clean.png', 'offline_Up.png', 'offline_Down.png', 'offline_rig_proof.png', 'processing.json']:
    shutil.copy2(HERE / p, HERE / (Path(p).stem + '_before_local02' + Path(p).suffix))
shutil.copytree(HERE / 'staged_art', HERE / 'staged_art_before_local02')
for direction, source in [('Up', 'generation/Up/raw.png'), ('Down', 'generation/Down/revision_01/raw.png')]:
    src = HERE / source
    out = src.parent / 'local_revision_02'
    out.mkdir(exist_ok=False)
    image = Image.open(src).convert('RGBA')
    a = np.array(image)[:, :, :3].copy()
    b = a.astype(np.int16)
    fg = ((b[:, :, 2] <= b[:, :, 1] + 8) & (b[:, :, 2] <= b[:, :, 0] + 12) & ((b[:, :, 0] - b[:, :, 1]) <= (b[:, :, 1] - b[:, :, 2]) + 26)) if direction == 'Up' else np.array(image)[:, :, 3] >= 128
    interior = np.asarray(Image.fromarray(fg.astype('uint8') * 255).filter(ImageFilter.MinFilter(11))) > 0
    operations = []
    if direction == 'Up':
        warm = (b[:, :, 0] > 90) & (b[:, :, 0] > b[:, :, 1] * 1.25) & (b[:, :, 1] > b[:, :, 2] * 1.25) & (b[:, :, 2] < 120)
        for seed in [(224, 126), (224, 285)]:
            q = deque([seed]); connected = np.zeros(fg.shape, bool); connected[seed] = True
            while q:
                y, x = q.popleft()
                for yy, xx in [(y-1, x), (y+1, x), (y, x-1), (y, x+1)]:
                    if 0 <= yy < a.shape[0] and 0 <= xx < a.shape[1] and warm[yy, xx] and not connected[yy, xx]:
                        connected[yy, xx] = True; q.append((yy, xx))
            mask = np.asarray(Image.fromarray(connected.astype('uint8') * 255).filter(ImageFilter.MaxFilter(5))) > 0
            mask &= interior
            ys, xs = np.where(mask)
            # Match the outer ear fur; connected pad only, neighbouring original forehead spike preserved.
            a[mask] = [77, 66, 39]
            operations.append({'region': [int(xs.min()), int(ys.min()), int(xs.max()+1), int(ys.max()+1)], 'pixels': len(xs), 'method': 'Connected gold ear-pad recolor with two-pixel antialias margin; complete pad removed and real crown spikes retained.'})
        for box in [(129, 815, 260, 917), (517, 815, 651, 919)]:
            x0, y0, x1, y1 = box
            region = np.zeros(fg.shape, bool); region[y0:y1, x0:x1] = True
            m = region & interior
            ys, xs = np.where(m)
            t = np.clip((ys - 815) / 32, 0, 1); t = t*t*(3-2*t)
            shade = np.clip((ys - 847) / 70, 0, 1)
            color = np.array([79., 67., 40.])[None, :] - shade[:, None] * np.array([9., 8., 5.])[None, :]
            a[ys, xs] = np.rint(a[ys, xs] * (1-t[:, None]) + color * t[:, None]).astype('uint8')
            operations.append({'box': box, 'pixels': len(xs), 'method': 'Smooth feathered source-colored rear heel fill; internal front toe lines removed, exterior retained, no hard rectangular seam.'})
    else:
        region = np.zeros(fg.shape, bool); region[286:489, 1175:1503] = True
        m = region & interior
        ys, xs = np.where(m)
        t = np.clip((ys - 286) / 44, 0, 1); t = t*t*(3-2*t)
        shade = np.clip((ys - 320) / 170, 0, 1)
        color = np.array([75., 63., 37.])[None, :] - shade[:, None] * np.array([5., 4., 2.])[None, :]
        a[ys, xs] = np.rint(a[ys, xs] * (1-t[:, None]) + color * t[:, None]).astype('uint8')
        operations.append({'region': [1175, 286, 1503, 489], 'pixels': len(xs), 'method': 'Feathered plain canine chest replaces all duplicate muzzle motifs, full outer silhouette and back spikes retained. Lower neck is covered by front head.'})
    a[~fg] = [255, 0, 255]
    Image.fromarray(a).save(out / 'raw.png')
    save(out / 'processing.json', {'observed_at': now(), 'parent': source, 'parent_sha256': sha(src),
        'rejected_prior_local': str(src.parent / 'local_revision_01/raw.png'), 'output_sha256': sha(out / 'raw.png'),
        'new_AI_return': False, 'operations': operations, 'actual_size': list(image.size)})
selection = read(HERE / 'art_selection.json')
selection.update(Up='generation/Up/local_revision_02/raw.png', Down='generation/Down/revision_01/local_revision_02/raw.png')
(HERE / 'art_selection.json').write_text(json.dumps(selection, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
layout = read(HERE / 'layout_adjustments.json')
layout['parts']['Down/Tail'].update(x=.13, y=.86, height=.27, width=.20, angle=-18)
for side, sign in [('L', -1), ('R', 1)]:
    layout['parts'][f'Down/Fore{side}'].update(x=sign*.14, y=.47, height=.35)
    layout['parts'][f'Down/Hind{side}'].update(x=sign*.21, y=.75, height=.32)
(HERE / 'layout_adjustments.json').write_text(json.dumps(layout, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
subprocess.run([sys.executable, str(RUN / 'character_step.py'), 'stage', NAME], check=True)
