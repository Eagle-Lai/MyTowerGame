from pathlib import Path
root=Path(__file__).resolve().parent
for direction in ['Up','Down']:
    source=root/'generation'/direction
    out=source/'revision_01'
    out.mkdir(exist_ok=True)
    if (out/'request.json').exists():raise ValueError('Paid revision already requested')
    text=(source/'prompt.txt').read_text(encoding='utf-8')
    text+='''
REVISION 01: Image 3 is the REJECTED prior parts sheet, only for matching its successful color/line style. Redraw the entire sheet with these mandatory corrections. Cell 4 Body MUST be a clean symmetric AXIAL oval duck torso, short ivory neck ring centered at TOP. Body has absolutely NO wing feather edges, NO pointed tail, NO side-profile rump or appendage. The separate Cell 5 supplies the two wings via mirroring, and separate Cell 7 supplies the one tail. Body must not duplicate them. Keep all three heads and original ochre/white/orange colors. Wings must hang vertically from upper shoulder with feather tips below attachment. Tail attachment root is at BOTTOM center, feathers point UP, a small original duck tail fan.
'''
    if direction=='Up':
        text+='''Cell 6 is a PURE REAR duck leg: back of ankle over a small smooth rounded heel pad, narrower than the leg root. Front webbed toes project away into depth and are hidden from this camera. The foot silhouette must NOT have three lobes, no central toe point, no claw, no toe division or toe crease. Keep plain faceless rear heads. Body rear has plain back feathers only.
'''
    else:
        text+='''Front Body is exact bilateral axial chest view, not a quarter-view. Do not put wing or tail on upper right edge. Keep the centered bill and BOTH front eyes. Front foot retains broad webbing.
'''
    (out/'prompt.txt').write_text(text,encoding='utf-8')
print('Drake revision 01 prompts ready')
