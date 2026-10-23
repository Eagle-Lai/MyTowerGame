"""Build review media from real Unity frames; never edits Assets or calls Image APIs."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BG = (40, 48, 37)
FONT = 'C:/Windows/Fonts/msyh.ttc'


def font(size=18):
    return ImageFont.truetype(FONT, size)


def tile(path, label, size=320):
    out = Image.new('RGB', (size, size + 44), BG)
    im = Image.open(path).convert('RGBA')
    im.thumbnail((size, size), Image.Resampling.LANCZOS)
    out.paste(im, ((size-im.width)//2, 44+(size-im.height)//2), im)
    ImageDraw.Draw(out).text((12, 10), label, font=font(18), fill='white')
    return out


def row(tiles, path):
    out = Image.new('RGB', (sum(t.width for t in tiles), max(t.height for t in tiles)), BG)
    x = 0
    for t in tiles:
        out.paste(t, (x, 0)); x += t.width
    out.save(path)


def gif(prefix, filename):
    frames = []
    for i, path in enumerate(sorted((HERE/'frames').glob(prefix+'*.png'))):
        if prefix == 'turn_':
            label = '实际行走与连续转弯 · 20 fps'
        else:
            k = i % 64
            stage = '攻击' if k < 24 else '受击闪白' if k < 32 else '死亡 / 自动回收' if k < 47 else '同一实例复用'
            label = ('Up' if i < 64 else 'Down') + ' · ' + stage
        frames.append(tile(path, label))
    palette_source = Image.new('RGB', (320*6, 364*2), BG)
    for j in range(12):
        palette_source.paste(frames[round(j*(len(frames)-1)/11)], ((j%6)*320, (j//6)*364))
    palette = palette_source.quantize(colors=192)
    frames = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]
    frames[0].save(HERE/filename, save_all=True, append_images=frames[1:], duration=50, loop=0, optimize=False, disposal=2)


row([tile(HERE/f'view_{d}.png', label) for d, label in [('Left','Left · 原侧面'),('Right','Right · 原侧面镜像'),('Up','Up · 新增背向'),('Down','Down · 新增正向')]], HERE/'four_directions.png')
row([tile(ROOT/'Assets/_UIAssets/Monsters/Birds/AdvancedHen/AdvancedHen.png', '原始图集 · 960×800'), tile(HERE/'reference_current.png', '当前原预制体 · 实际渲染'), tile(HERE/'view_Up.png', '新增 Up'), tile(HERE/'view_Down.png', '新增 Down')], HERE/'original_vs_new.png')

gif('turn_', 'walk_turn.gif')
gif('action_', 'attack_death_reuse.gif')

loops = []
for i in range(10):
    tiles = [tile(HERE/'frames'/f'loop_{d}_{i:02}.png', f'{d} · Unity 实际行走循环', 384) for d in ['Up','Down']]
    out = Image.new('RGB', (768, 428), BG)
    for j,t in enumerate(tiles): out.paste(t, (384*j, 0))
    loops.append(out)
palette = loops[0].quantize(colors=192)
loops = [f.quantize(palette=palette,dither=Image.Dither.NONE) for f in loops]
loops[0].save(HERE/'up_down_walk.gif',save_all=True,append_images=loops[1:],duration=50,loop=0,optimize=False,disposal=2)

for prefix, indices in [('turn_', [0,7,15,25,40,55,70,85,100,120,145,170]), ('action_', [0,4,8,24,33,38,44,47,64,68,97,111])]:
    out = Image.new('RGB', (320*4, 364*3), BG)
    for j, index in enumerate(indices):
        out.paste(tile(HERE/'frames'/f'{prefix}{index:03}.png', f'{prefix}{index:03}'), ((j%4)*320, (j//4)*364))
    out.save(HERE/f'{prefix}contact.png')
print('Generated four directions, comparison, three real Unity GIFs and two contact sheets.')
