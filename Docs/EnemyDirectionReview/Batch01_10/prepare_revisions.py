from pathlib import Path
HERE=Path(__file__).resolve().parent
for name in ['Bat','BattlePanther']:
    base=HERE/name/'generation/Up';out=base/'revision_02';out.mkdir(exist_ok=True)
    prompt=base.joinpath('prompt.txt').read_text(encoding='utf-8')
    prompt+='''
EDIT TARGET: Image 3 is the existing generated sheet. Preserve its grid, part sizes, outline, palette, anatomy and all other pixels as closely as possible. Only correct the BACK surfaces of both ears on every rear head in the first three cells. Remove the light tan inner-ear triangles, inner-ear ridges, ear canals and frontal ear fold lines. Fill those areas with the same opaque olive-brown outer fur/skin as the back of the head, leaving only the original thick outer ear silhouette and a simple darker outer-fur crease. The viewer is behind the creature; seeing an inner ear is anatomically wrong. No face, no eyes, no nose. Keep all other parts in the sheet, including torso, limbs and tail/wing, unchanged. Clean hard outlines, no soft halo. Do not introduce ground shadows.
'''
    if not out.joinpath('request.json').exists():out.joinpath('prompt.txt').write_text(prompt,encoding='utf-8')
print('Prepared two targeted rear-ear edits. No paid request made by this script.')
