from pathlib import Path
p=Path(__file__).parent
for d in ["Up","Down"]:
 f=p/"generation"/d/"prompt.txt"
 t=f.read_text(encoding="utf-8")
 t+="\nDarkBunny identity details: GRAY-OLIVE fur with sparse OCHRE GOLD patches, gray cream rim of long ears, dark brown outline, pale gold nose, two white buck teeth. This is NOT a golden rabbit or white rabbit. Preserve original upright long ears and fluffy cheek shape. All three heads same dimensions, front head has TWO eyes. Normal surprised, angry narrow eyes/tongue, dead blank round eyes with tears and tongue matching original atlas. Rear heads have plain OUTER ears, no inner-ear outlines, no face or muzzle. This is a FOUR-FOOTED rabbit, not biped human torso. Rear feet show plain rounded HEELS and sole edge, NO toe marks or frontal claws pointing at viewer. Front feet show source paw toes. Torso has no attached feet and no tail: ONE small gray and ochre fluffy cotton tail supplied separately in cell 7, no second tail painted into body. Body connection surfaces solid opaque, no open cylinders. Keep large rabbit head compared with small crouched body, short forelegs and larger folded hindlegs.\n"
 f.write_text(t,encoding="utf-8")
