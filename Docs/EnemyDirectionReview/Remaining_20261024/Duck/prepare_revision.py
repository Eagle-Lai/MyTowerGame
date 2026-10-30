from pathlib import Path
import json
root=Path(__file__).resolve().parent
for direction in ['Up','Down']:
    folder=root/'generation'/direction/'revision_01'
    folder.mkdir(exist_ok=True)
    if (folder/'request.json').exists():raise ValueError('Existing paid revision')
    instruction='Use Image 3 as the edit target. Preserve its exact cell positions, all original part sizes, cream-white palette, outline and clear magenta background. Change ONLY cell 4 torso: REMOVE the extra tail/feather patch painted on the bottom center. Fill that area with uninterrupted smooth cream torso and pale lower body cel shading, following the surrounding contour. The torso must be a plain pear-shaped rear/front body with narrow solid neck, existing two ochre flank patches, NO tail, NO feather rosette, NO wings, NO feet. Preserve the ONE detached tail in cell 7 without alteration. Do not add extra parts. All three top heads stay identically aligned. '
    if direction=='Down':instruction+='Also match cell 3 dead head to ORIGINAL Image 1: eyes are big plain ivory CIRCLES with tiny rolled/absent pupils and the original small tear at the eye corner; NO X-shaped eyes. Keep exact bill and head silhouette.'
    else:instruction+='Back heads remain entirely faceless. Keep the plain rear heel in cell 6; no front toes.'
    (folder/'prompt.txt').write_text(instruction,encoding='utf-8')
(root/'art_review_rejected.json').write_text(json.dumps({'Up':'generation/Up/raw.png','Down':'generation/Down/raw.png','reason':'Both first sheets duplicate detached tail inside torso; front death expression does not match original.', 'status':'rejected_history_not_for_install'},indent=2),encoding='utf-8')
