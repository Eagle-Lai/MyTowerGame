from session_current import *
from PIL import Image, ImageDraw, ImageChops
import math

owner()
out = HERE / 'visual_review_final_20261030' / 'continuous_gifs'
out.mkdir(exist_ok=False)
manifest = []
for run in ['runtime_r01', 'runtime_updeath_r01']:
    for path in sorted((HERE / run).glob('*.gif')):
        frames, durations = [], []
        with Image.open(path) as gif:
            for i in range(gif.n_frames):
                gif.seek(i)
                frames.append(gif.convert('RGB').copy())
                durations.append(gif.info.get('duration', 0))
        # Exclude only the tiny evidence title; preserve actor and HP in one stable union crop.
        boxes = []
        for im in frames:
            diff = ImageChops.difference(im, Image.new('RGB', im.size, im.getpixel((0, 0))))
            mask = diff.convert('L').point(lambda v: 255 if v > 8 else 0)
            ImageDraw.Draw(mask).rectangle((0, 0, im.width, 38), fill=0)
            b = mask.getbbox()
            if b:
                boxes.append(b)
        crop = (max(0, min(b[0] for b in boxes) - 12), max(38, min(b[1] for b in boxes) - 12),
                min(frames[0].width, max(b[2] for b in boxes) + 12), min(frames[0].height, max(b[3] for b in boxes) + 12))
        pages = []
        for start in range(0, len(frames), 30):
            end = min(start + 30, len(frames))
            sheet = Image.new('RGB', (1500, 240 * math.ceil((end - start) / 6)), (40, 48, 37))
            draw = ImageDraw.Draw(sheet)
            for cell, index in enumerate(range(start, end)):
                im = frames[index].crop(crop)
                im.thumbnail((246, 210), Image.Resampling.LANCZOS)
                x, y = cell % 6 * 250, cell // 6 * 240
                sheet.paste(im, (x + (250 - im.width) // 2, y + 30))
                draw.text((x + 3, y + 2), f'{path.stem} #{index}\n{durations[index]}ms', fill='white')
            dest = out / f'{run}_{path.stem}_{start:03}_{end-1:03}.png'
            sheet.save(dest)
            pages.append({'file': dest.name, 'sha256': sha(dest), 'first': start, 'last': end - 1})
        manifest.append({'revision': run, 'gif': path.name, 'gif_sha256': sha(path), 'encoded_frames': len(frames),
                         'duration_ms': sum(durations), 'durations_ms': durations, 'crop': crop, 'pages': pages})
save(out / 'manifest.json', {'observed_at': now(), 'method': 'Every decoded final GIF frame in encoding order, one stable foreground union crop per file; title excluded only. No interpolation, no new poses, no real-time playback.', 'files': manifest})
print(json.dumps({'gifs': len(manifest), 'encoded_frames': sum(r['encoded_frames'] for r in manifest), 'pages': sum(len(r['pages']) for r in manifest), 'files': [p['file'] for r in manifest for p in r['pages']]}))
