"""Offline Wasp evidence only; never substitute for real Unity Play frames."""
from pathlib import Path
import runpy, sys, json
from PIL import Image, ImageDraw

D = Path(__file__).resolve().parent
sys.argv = [str(D.parent / 'render_staged_rig.py'), 'Wasp']
r = runpy.run_path(sys.argv[0])
layout, render = r['layout'], r['render']
board = Image.new('RGB', (1440, 1480), (40,48,37))
draw = ImageDraw.Draw(board)
for row in range(2):
    for col, view in enumerate(layout['views']):
        pose = render(view, row)
        pose.save(D / ('offline_'+view['direction']+'_flap'+str(row)+'_r02.png'))
        pose.thumbnail((720,700), Image.Resampling.LANCZOS)
        board.paste(pose, (col*720, row*740+35), pose)
        draw.text((col*720+18,row*740+15), 'OFFLINE '+view['direction']+' / '+('RAISED' if row==0 else 'LOWERED')+' / r02', fill='white')
board.save(D / 'offline_wing_joints_r02.png')
gallery = Image.new('RGB', (1440, 660), (50,50,50))
draw = ImageDraw.Draw(gallery)
for i, s in enumerate(json.loads((D/'staged_art/Wasp_Directions.sprites.json').read_text())['sprites']):
    im=Image.open(D/'staged_art'/(s['name']+'.png')).convert('RGBA')
    im.thumbnail((230,280), Image.Resampling.LANCZOS)
    x,y=(i%6)*240,(i//6)*330
    for yy in range(0,330,15):
        for xx in range(0,240,15):
            c=(60,60,60) if (xx//15+yy//15)%2 else (85,85,85)
            draw.rectangle((x+xx,y+yy,x+xx+14,y+yy+14),fill=c)
    gallery.paste(im,(x+(240-im.width)//2,y+35),im)
    draw.text((x+5,y+10),s['name'],fill='white')
gallery.save(D / 'parts_clean_registered_r02.png')
print('Wasp r02 proof and alpha gallery saved.')
