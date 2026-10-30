from pathlib import Path
p=Path(__file__).parent
for d in ["Up","Down"]:
 f=p/"generation"/d/"prompt.txt"
 t=f.read_text(encoding="utf-8")
 t=t.replace("7. ONE full detached original tail, root at BOTTOM center, rising UP from rump; preserve exact tail type","7. ONE original thin donkey tuft tail: root at TOP CENTER, short gentle curved stalk hanging DOWN to dark gray-brown leaf-shaped tuft; not a ring, not bushy, no extra tail in body")
 t+="\nDonkey-specific requirements: gray-tan body, sparse ochre patches, small pale gray dots and highlights, cream muzzle and belly. Not a golden donkey. Preserve two very long upright ears, broad elongated donkey muzzle, short narrow four hoof legs and thin curved tuft tail. NO mane or spine stripe, hair crest, horns, saddle, rider, new muscles or shoulder knobs. Front view two eyes and centered nostrils; normal wide eyes, attack angry eyes, death blank pale eyes with tongue as original. Rear head faceless plain gray-tan, ears show only OUTER FUR with narrow light edge highlight and no dark inset inner ear panels. Rear legs show BACK OF HEELS, smooth rounded dark hoof backs, absolutely NO front hoof split/toe lines, no frontal claws. Front hooves match original flat dark hoof rim. Torso axial top-to-bottom, opaque rounded neck concealed under head, no hollow neck opening. Every root solid opaque. Tail excluded from body.\n"
 f.write_text(t,encoding="utf-8")
