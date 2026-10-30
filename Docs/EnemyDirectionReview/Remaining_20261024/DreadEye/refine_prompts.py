from pathlib import Path
root=Path(__file__).resolve().parent
for direction in ['Up','Down']:
    p=root/'generation'/direction/'prompt.txt'
    if (p.parent/'request.json').exists():raise ValueError('Preserve paid request')
    text=p.read_text(encoding='utf-8')
    text+='''
DreadEye-specific structure: The entire creature is ONE spherical olive/ochre shell containing ONE large ivory eyeball in front, with exactly TWO original leathery bat wings. Original image 1 determines the muted olive brown gold palette, not bright yellow. No torso beneath sphere, no lower jaw, no ears, horns, teeth, legs or tail. Cells 1-3 are the COMPLETE spherical orb, not just an isolated eyeball. Cell 4 is a small plain color-matched lower-shell connector patch only, not a second complete sphere. Cell 5 and Cell 6 are ONE LEFT bat wing in raised and lowered poses, original three membrane panels, thick tan spars, tiny ivory claw on elbow, root at RIGHT center edge. The wing extends LEFT, with an intact solid rounded attachment at right; never detach claw or create an extra arm. Both wing poses same overall canvas/size and same right-edge pivot region so switching does not teleport root. Bat wing silhouette must match original long vertical spars and scalloped outer membrane. Sheet precisely FOUR columns by TWO rows: row1 all THREE sphere head states and connector patch; row2 wing raised, wing lowered, EMPTY, EMPTY. All pieces wholly inside own cell with 14 percent margin.
'''
    if direction=='Up':
        text+='''Rear orb has a closed plain opaque olive/gold back surface, matching original shell shadow and highlight: NO eye, pupil, sclera, eyelids, slit eye, mouth or face marks. All three rear head cells are the SAME rear spherical shell. Show backs of wing membranes and spar connections, no invented symbol.
'''
    else:
        text+='''Front sphere centered axial: one HUGE circular ivory eye with one dark pupil and tiny white highlight. Normal eye wide open. Angry front eye half-lidded/narrowed. Dead eye fully CLOSED with horizontal original eyelid strokes, not blank white eye. Do not invent a second eye or mouth.
'''
    p.write_text(text,encoding='utf-8')
print('DreadEye prompts refined')
