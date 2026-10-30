from pathlib import Path
import sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, str(Path(__file__).resolve().parent))
from session_current import *

owner()
assert not (HERE / 'staged_art').exists() and not (HERE / 'art_selection.json').exists()
paths = {'Up': 'generation/Up/raw.png', 'Down': 'generation/Down/revision_01/raw.png'}
for direction, source in paths.items():
    src = HERE / source
    out = src.parent / 'local_revision_01'
    out.mkdir(exist_ok=False)
    image = Image.open(src).convert('RGBA')
    a = np.array(image)[:, :, :3].copy()
    original = a.copy()
    if direction == 'Up':
        b = a.astype(np.int16)
        fg = (b[:, :, 2] <= b[:, :, 1] + 8) & (b[:, :, 2] <= b[:, :, 0] + 12) & ((b[:, :, 0] - b[:, :, 1]) <= (b[:, :, 1] - b[:, :, 2]) + 26)
    else:
        fg = np.array(image)[:, :, 3] >= 128
    interior = np.asarray(Image.fromarray(fg.astype('uint8') * 255).filter(ImageFilter.MinFilter(9))) > 0
    operations = []
    if direction == 'Up':
        # The selected rear head is copied to the other rear expression slots by the packer.
        for box in [(113, 194, 173, 245), (239, 193, 301, 245)]:
            x0, y0, x1, y1 = box
            region = np.zeros(fg.shape, bool)
            region[y0:y1, x0:x1] = True
            b = a.astype(np.int16)
            mask = region & interior & (b[:, :, 0] > b[:, :, 2] + 22) & (b[:, :, 1] > b[:, :, 2] + 18)
            a[mask] = [76, 66, 40]
            operations.append({'box': box, 'pixels': int(mask.sum()), 'method': 'Remove front inner-ear gold only, replace with existing outer-ear olive-brown; exterior and actual crown spikes retained.'})
        for box in [(144, 835, 251, 904), (525, 835, 639, 905)]:
            x0, y0, x1, y1 = box
            region = np.zeros(fg.shape, bool)
            region[y0:y1, x0:x1] = True
            mask = region & interior
            crop = a[y0:y1, x0:x1].astype(float)
            mm = mask[y0:y1, x0:x1]
            # Smooth away internal front toe divisions while retaining the complete dark exterior.
            for _ in range(1200):
                pad = np.pad(crop, ((1, 1), (1, 1), (0, 0)), mode='edge')
                avg = (pad[:-2, 1:-1] + pad[2:, 1:-1] + pad[1:-1, :-2] + pad[1:-1, 2:]) / 4
                crop[mm] = avg[mm]
            a[y0:y1, x0:x1][mm] = np.rint(crop[mm]).astype('uint8')
            operations.append({'box': box, 'pixels': int(mask.sum()), 'method': 'Local harmonic fill of toe divisions inside original intact rear paw silhouette.'})
    else:
        # Returned torso incorrectly repeats muzzle/ivory fangs. Remove those internal motifs, not the silhouette or dorsal ornaments.
        polygon = [(1249, 307), (1426, 307), (1460, 377), (1418, 471), (1304, 479), (1244, 427)]
        pm = Image.new('L', image.size)
        ImageDraw.Draw(pm).polygon(polygon, fill=255)
        mask = (np.array(pm) > 0) & interior
        ys, xs = np.where(mask)
        blend = np.clip((ys - 307) / 170, 0, 1)
        colors = np.array([72., 59., 34.])[None, :] * (1 - blend[:, None]) + np.array([80., 67., 39.])[None, :] * blend[:, None]
        a[ys, xs] = np.rint(colors).astype('uint8')
        operations.append({'polygon': polygon, 'pixels': int(mask.sum()), 'method': 'Locally replace erroneous duplicate muzzle, nose and fangs on detached torso with source-matched plain dark olive chest; preserve original returned torso exterior and actual dorsal spikes. Not an AI return.'})
    a[~fg] = [255, 0, 255]
    Image.fromarray(a).save(out / 'raw.png')
    save(out / 'processing.json', {'observed_at': now(), 'parent': source, 'parent_sha256': sha(src),
        'output_sha256': sha(out / 'raw.png'), 'actual_parent_format': image.format or 'PNG',
        'actual_parent_mode': Image.open(src).mode, 'actual_parent_size': list(image.size),
        'new_AI_return': False, 'operations': operations,
        'foreground_method': 'Up spectral chroma, Down returned alpha threshold128; flat magenta exterior for established packer.',
        'changed_foreground_pixels': int((np.any(a != original, axis=2) & fg).sum())})

up = {'HeadNormal': [62, 164, 355, 464], 'HeadAngry': [423, 164, 715, 464], 'HeadDead': [783, 164, 1078, 464],
      'Body': [1127, 78, 1495, 558], 'LegFront': [112, 583, 280, 925], 'LegBack': [490, 582, 686, 924], 'Tail': [845, 513, 1040, 964]}
down = {'HeadNormal': [35, 134, 354, 450], 'HeadAngry': [407, 133, 741, 478], 'HeadDead': [785, 132, 1119, 459],
        'Body': [1175, 68, 1503, 489], 'LegFront': [117, 577, 289, 916], 'LegBack': [511, 579, 711, 921], 'Tail': [849, 531, 1035, 954]}
save(HERE / 'art_selection.json', {'Up': 'generation/Up/local_revision_01/raw.png',
    'Down': 'generation/Down/revision_01/local_revision_01/raw.png',
    'rectangles': {**{'Up_' + k: v for k, v in up.items()}, **{'Down_' + k: v for k, v in down.items()}},
    'source_sha256': {v: sha(HERE / paths[v]) for v in paths},
    'note': 'Own atlas/source and both returned images actually reviewed. Rear ears/paws and erroneous duplicate front muzzle on torso locally corrected, raw responses preserved. Up rear head reused across expressions; Down three separate front expressions.'})
parts = {'Up/Body': dict(y=.55, width=.69, height=.74), 'Up/Head': dict(y=.87, width=.53, height=.50, order=30),
         'Up/Tail': dict(x=-.02, y=.38, width=.25, height=.42, order=31, angle=-7),
         'Down/Body': dict(y=.65, width=.66, height=.76), 'Down/Head': dict(y=.54, width=.64, height=.58, order=35),
         'Down/Tail': dict(x=.19, y=.91, width=.25, height=.40, order=5, angle=-15)}
for direction in ['Up', 'Down']:
    for side, sign in [('L', -1), ('R', 1)]:
        parts[f'{direction}/Fore{side}'] = dict(x=sign * .18, y=.66 if direction == 'Up' else .35, width=.18, height=.30, angle=sign * (20 if direction == 'Up' else 5))
        parts[f'{direction}/Hind{side}'] = dict(x=sign * .18, y=.35 if direction == 'Up' else .74, width=.19, height=.31, angle=sign * (5 if direction == 'Up' else 20))
save(HERE / 'layout_adjustments.json', {'reason': 'Own PossessedWarg original Wolf 0.5s gait, four diagonal-phase legs with fixed roots, native 0.5s attack events. Compact quadruped overlaps, real golden dorsal/crown spikes and long tail.',
    'layout': {'motion': {'legAngle': 10, 'legLift': .045, 'bodyBob': .007, 'bodyRoll': 1.2, 'tailSwing': 8}}, 'parts': parts,
    'sprites': {f'{v}_{role}': {'pivotX': .5, 'pivotY': .93} for v in ['Up', 'Down'] for role in ['LegFront', 'LegBack']}})
save(HERE / 'raw_visual_review_20261030.json', {'observed_at': now(), 'reviewed': paths,
    'findings': 'New front sheet has correct amber eyes/ivory fangs and three original expressions, but its torso incorrectly repeats a muzzle and requires the documented local removal. Rear sheet has no face, actual golden crown/back spikes; ear pad and toe orientation corrected locally. Down alpha contains soft low-alpha outside which must be fully excluded. No additional paid request needed.',
    'original_up_http200': True, 'original_down_outcome': 'unknown', 'new_down_revision01_http_status': 200,
    'new_down_raw_sha256': sha(HERE / paths['Down']), 'billing': 'Not independently verified', 'stage_pending': True})
print('Measured PossessedWarg local raster01, selection and layout ready for stage review')
