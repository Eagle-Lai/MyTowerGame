from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageSequence

D = Path(__file__).resolve().parent
OUT = D / 'visual_review_final_20261028'
OUT.mkdir(exist_ok=True)
revisions = ['runtime_r01', 'runtime_updeath_r01']
gif_names = [
    'UpWalk.gif', 'DownWalk.gif', 'up_down_walk.gif',
    'walk_turn.gif', 'attack_death_reuse.gif', 'pause_speed.gif',
]
columns = 5
cell_w, cell_h = 220, 245
canvas = Image.new('RGB', (columns * cell_w, len(revisions) * len(gif_names) * cell_h), (40, 48, 37))
draw = ImageDraw.Draw(canvas)
samples = []
row = 0

for revision in revisions:
    for gif_name in gif_names:
        path = D / revision / gif_name
        with Image.open(path) as gif:
            frame_count = getattr(gif, 'n_frames', 1)
            indices = sorted({round((frame_count - 1) * i / (columns - 1)) for i in range(columns)})
            for column, frame_index in enumerate(indices):
                gif.seek(frame_index)
                frame = gif.convert('RGBA')
                frame.thumbnail((cell_w - 10, cell_h - 42), Image.Resampling.LANCZOS)
                x = column * cell_w + (cell_w - frame.width) // 2
                y = row * cell_h + 30 + (cell_h - 42 - frame.height) // 2
                canvas.paste(frame, (x, y), frame)
                samples.append({
                    'revision': revision,
                    'gif': gif_name,
                    'sha256': __import__('hashlib').sha256(path.read_bytes()).hexdigest().upper(),
                    'gif_frame_count': frame_count,
                    'sample_frame_index': frame_index,
                })
        draw.text((row * 0 + 5, row * cell_h + 7), revision + ' / ' + gif_name, fill='white')
        row += 1

image_path = OUT / 'gif_review_sample_board.png'
canvas.save(image_path)
report = {
    'sampled_at': __import__('datetime').datetime.now().astimezone().isoformat(),
    'method': 'Five evenly spaced frames from each emitted GIF; this samples the actual exported animations and is not exhaustive playback.',
    'runs': revisions,
    'gif_count': len(revisions) * len(gif_names),
    'sample_count': len(samples),
    'board': image_path.name,
    'samples': samples,
}
(OUT / 'gif_review_samples.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'board': str(image_path), 'gifs': report['gif_count'], 'sampled_frames': report['sample_count']}))
