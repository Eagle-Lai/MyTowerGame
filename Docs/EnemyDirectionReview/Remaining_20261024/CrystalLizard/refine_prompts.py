from pathlib import Path
p=Path(__file__).parent
for d in ["Up","Down"]:
 f=p/"generation"/d/"prompt.txt"
 text=f.read_text(encoding="utf-8")
 text=text.replace("7. ONE full detached original tail, root at BOTTOM center, rising UP from rump; preserve exact tail type","7. ONE full long pointed original lizard tail, root at TOP center hanging DOWN the page toward a narrow pointed tip, original ochre crystals along its dorsal center. The tail trails the rump along the ground, never an upright scorpion hook")
 text+="\nCrystalLizard specifics: original amber-yellow skin and dark ochre spots, ivory underside and claw tips, angular golden crystals. Two eyes on the TRUE FRONT face, sleepy normal, open jaw with original white teeth for attack, blank round eyes and tongue for death. REAR head plain with no face. Lizard has NO ears, horns or hair. Body axis TOP to BOTTOM with crystal row centered along vertical spine, opaque closed neck root. Legs are short SPLAYED reptiles, bent elbows/knees toward the outer sides, not straight mammal pillars; palms/toes point toward screen UP in rear view so rear of heels is visible, screen DOWN for front view. Each detached left leg has a solid rounded proximal root at TOP RIGHT and the foot slightly OUTWARD to its LEFT bottom. Front and hind foot only one each; mirrored counterparts are made in Unity.\n"
 f.write_text(text,encoding="utf-8")
