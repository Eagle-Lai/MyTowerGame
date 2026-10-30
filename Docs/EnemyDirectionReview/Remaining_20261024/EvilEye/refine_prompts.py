from pathlib import Path
import json
root=Path(__file__).resolve().parent
plan=json.loads((root/'anatomy_plan.json').read_text(encoding='utf-8'))
plan['individual_constraints']=['One bright ochre gold spherical shell with ONE large ivory eye at front only; no mouth, teeth, legs or tail','Exactly two simple ochre triangular leathery wings with two inner membrane regions','Rear shell has no eye or face, original small dark gold spots retained','Head cells contain the entire spherical shell only, NO wings. Body cell is a small plain gold opaque connector hidden within shell']
(root/'anatomy_plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+chr(10),encoding='utf-8')
for direction in ['Up','Down']:
    path=root/'generation'/direction/'prompt.txt'
    if (path.parent/'request.json').exists():raise ValueError('Existing request')
    rear=direction=='Up'
    text=path.read_text(encoding='utf-8')
    text+=chr(10)+'EvilEye exact structure overrides generic descriptions: this is ONE bright gold spherical eye shell and exactly TWO bat wings, NOT an animal with a separate head and torso. Cells 1,2,3 must each contain the ENTIRE ROUND SPHERE ONLY, NO WINGS OR BODY below it. '+('All three rear sphere cells show identical plain ochre-gold shell with original small dark golden spots; NO eye, eyelid, mouth, facial slit or teeth.' if rear else 'Front normal has one enormous ivory circular eye with black pupil and gold rim; angry is same eye squinting; dead is one closed horizontal eyelid as in original. There is NO mouth or teeth.')+' Cell 4 is a tiny simple gold solid connector patch ONLY, no eye, face or appendages; hidden inside shell in assembled rig. Cell 5 ONE LEFT wing with its hinge at LOWER RIGHT edge, sharp wingtip rising to upper LEFT, simple triangular ochre membrane and dark outline, NO shell attached. Cell 6 SAME LEFT wing extended more horizontally leftward, hinge still at LOWER RIGHT; same size and anatomy, no shell. Exactly two membrane regions per wing as original, not extra fingers or spikes. Empty cells 7 and 8. Keep every piece within its cell, no crossing between head row and wing row, 15 percent clear magenta padding. Bright original gold not olive DreadEye palette. No glow, no shadow.'+chr(10)
    path.write_text(text,encoding='utf-8')
