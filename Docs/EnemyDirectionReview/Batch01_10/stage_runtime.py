"""Prepare minimal additive extensions; do not apply while the project is frozen."""
from pathlib import Path
import json,difflib
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OUT=HERE/'staged_code';OUT.mkdir(exist_ok=True)
snapshot={entry['path']:entry['content'] for entry in json.loads((HERE/'source_snapshot.json').read_text(encoding='utf-8'))}

profile=snapshot['Assets/Scripts/Enemy/EnemyDirectionalProfile.cs']
profile=profile.replace('public bool IsComplete\n            {','public bool HasHeadAndBody { get { return NormalHead && AngryHead && DeadHead && Body; } }\n\n            public bool IsComplete\n            {',1)
profile=profile.replace('public Parts Up = new Parts();','// Optional complete per-view rigs for wings, quadrupeds and multi-legged enemies.\n        // Existing six-part profiles retain their serialized behavior.\n        public bool SeparateViewRigs;\n\n        public Parts Up = new Parts();')
profile=profile.replace('return Up != null && Down != null && Up.IsComplete && Down.IsComplete && Controller;',
 '''return Up != null && Down != null && Controller && (SeparateViewRigs
                    ? Up.HasHeadAndBody && Down.HasHeadAndBody
                    : Up.IsComplete && Down.IsComplete);''')

visual=snapshot['Assets/Scripts/Enemy/EnemyDirectionalVisual.cs']
visual=visual.replace('public SpriteRenderer LegR;', '''public SpriteRenderer LegR;

        // Only profiles opting into separate anatomical rigs use these arrays.
        public SpriteRenderer[] UpRenderers;
        public SpriteRenderer[] DownRenderers;
        public SpriteRenderer UpHead, DownHead;
        public SpriteRenderer UpBody, DownBody;''')
visual=visual.replace('return Profile && Profile.IsComplete && Head && Body && WingL && WingR && LegL && LegR\n                    && HorizontalRenderers != null && HorizontalRenderers.Length > 0;',
'''if (!Profile || !Profile.IsComplete || HorizontalRenderers == null || HorizontalRenderers.Length == 0)
                    return false;
                if (Profile.SeparateViewRigs)
                    return UpHead && DownHead && UpBody && DownBody && UpRenderers != null && UpRenderers.Length > 0
                        && DownRenderers != null && DownRenderers.Length > 0;
                return Head && Body && WingL && WingR && LegL && LegR;''')
visual=visual.replace('foreach (var sr in HorizontalRenderers) Flash(sr, amount);', '''foreach (var sr in HorizontalRenderers) Flash(sr, amount);
            if (Profile && Profile.SeparateViewRigs)
            {
                foreach (var sr in UpRenderers) Flash(sr, amount);
                foreach (var sr in DownRenderers) Flash(sr, amount);
                return;
            }''')
visual=visual.replace('bool vertical = Facing == EnemyFacing.Up || Facing == EnemyFacing.Down;\n            foreach (var sr in HorizontalRenderers)',
'''bool vertical = Facing == EnemyFacing.Up || Facing == EnemyFacing.Down;
            if (Profile.SeparateViewRigs)
            {
                // Original Bat clips animate SpriteRenderer.enabled on alternating wing poses.
                // A renderer-level draw gate preserves those curves while hiding the entire side view.
                foreach (var sr in HorizontalRenderers) if (sr) sr.forceRenderingOff = vertical;
                bool up = Facing == EnemyFacing.Up;
                foreach (var sr in UpRenderers) if (sr) sr.forceRenderingOff = !vertical || !up;
                foreach (var sr in DownRenderers) if (sr) sr.forceRenderingOff = !vertical || up;
                Head = up ? UpHead : DownHead;
                Body = up ? UpBody : DownBody;
                if (vertical) Head.sprite = CurrentParts().HeadAt(HeadIndex);
                return;
            }
            foreach (var sr in HorizontalRenderers)''')

builder=snapshot['Assets/Editor/EnemyDirectionPrefabBuilder.cs']
builder=builder.replace('public bool UseRealController;', 'public bool UseSeparateViewRigs;\n        public bool UseRealController;',1)
builder=builder.replace('foreach (var s in Specs)\n            {','if (EnemyDirectionalRigBuilder.TryGetSpec(monsterName, out spec)) return true;\n            foreach (var s in Specs)\n            {',1)
builder=builder.replace('public static void Build(EnemyDirectionSpec spec)\n        {','public static void Build(EnemyDirectionSpec spec)\n        {\n            if (spec.UseSeparateViewRigs) { EnemyDirectionalRigBuilder.Build(spec); return; }',1)
builder=builder.replace('Apply(root, profile, spec);\n            return true;','if (spec.UseSeparateViewRigs) EnemyDirectionalRigBuilder.Apply(root, profile, spec);\n            else Apply(root, profile, spec);\n            return true;',1)
builder=builder.replace('private static RuntimeAnimatorController BuildAdvancedHenController(', 'internal static RuntimeAnimatorController BuildAdvancedHenController(',1)
builder=builder.replace('public static bool Verify(EnemyDirectionSpec s, out string report)\n        {', 'public static bool Verify(EnemyDirectionSpec s, out string report)\n        {\n            if (s.UseSeparateViewRigs) return EnemyDirectionalRigBuilder.Verify(s, out report);',1)
builder=builder.replace('string path = spec.AnimDir + "/AdvancedHen_Directions.controller";', 'string path = spec.AnimDir + "/" + spec.Name + "_Directions.controller";',1)

patch=[]
for path,content in [('Assets/Scripts/Enemy/EnemyDirectionalProfile.cs',profile),('Assets/Scripts/Enemy/EnemyDirectionalVisual.cs',visual),('Assets/Editor/EnemyDirectionPrefabBuilder.cs',builder)]:
    (OUT/(Path(path).name+'.txt')).write_text(content,encoding='utf-8')
    patch.extend(difflib.unified_diff(snapshot[path].splitlines(True),content.splitlines(True),fromfile='before/'+path,tofile='after/'+path))
(HERE/'planned_shared_changes.patch').write_text(''.join(patch),encoding='utf-8')
print('Staged additive runtime/editor extensions under Docs. BaseEnemy stays untouched.')
