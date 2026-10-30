"""Stage additive single-character catalog and anatomical validation changes. Docs only."""
from pathlib import Path
import json,difflib
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
snapshot={x['path']:x['content'] for x in json.loads((HERE/'source_snapshot.json').read_text(encoding='utf-8'))}
targets=json.loads((HERE/'local_baseline.json').read_text(encoding='utf-8'))['targets']
catalog='''using System;
using System.Collections.Generic;
namespace FTProject.EditorTools
{
    // Explicit user-authorized catalog. Merely registering a spec never installs or rebuilds it.
    public static class EnemyDirectionRemainingCatalog
    {
        private static readonly Dictionary<string,EnemyDirectionSpec> Specs = new Dictionary<string,EnemyDirectionSpec>(StringComparer.Ordinal)
        {
'''
for t in targets:
    catalog+='            {"'+t['name']+'", new EnemyDirectionSpec {Name="'+t['name']+'", ArtDir="'+t['art_dir']+'", PrefabPath="'+t['battle']+'", ControllerSource="'+t['controller']+'", OriginalAtlasPath="'+t['atlas']+'", UseSeparateViewRigs=true}},\n'
catalog+='''        };
        public static bool TryGetSpec(string name,out EnemyDirectionSpec spec) { return Specs.TryGetValue(name,out spec); }
        public static bool TryGetSpecByAtlas(string path,out EnemyDirectionSpec spec)
        {
            foreach(var item in Specs.Values) if(string.Equals(item.OriginalAtlasPath,path.Replace('\\\\','/'),StringComparison.OrdinalIgnoreCase)) {spec=item; return true;}
            spec=null;return false;
        }
    }
}
'''
rig=snapshot['Assets/Editor/EnemyDirectionalRigBuilder.cs']
rig=rig.replace('spec = null;\n            return false;','return EnemyDirectionRemainingCatalog.TryGetSpec(name, out spec);',1)
rig=rig.replace('[Serializable] public sealed class Layout { public int schema;', '[Serializable] public sealed class Anatomy { public int legs, wings, claws, tails, arms, feelers; }\n        [Serializable] public sealed class Layout { public Anatomy anatomy; public string motionKind; public int schema;')
rig=rig.replace('view.parts.Length < 3','view.parts.Length < (layout.anatomy == null ? 3 : 2)')
rig=rig.replace('int legs=0,wings=0,claws=0,tails=0;','int legs=0,wings=0,claws=0,tails=0,arms=0,feelers=0;')
rig=rig.replace('if(part.role=="tail")tails++;','if(part.role=="tail")tails++;if(part.role=="arm")arms++;if(part.role=="feeler")feelers++;')
rig=rig.replace('if(!anatomy)throw', 'if(layout.anatomy != null) anatomy=legs==layout.anatomy.legs&&wings==layout.anatomy.wings&&claws==layout.anatomy.claws&&tails==layout.anatomy.tails&&arms==layout.anatomy.arms&&feelers==layout.anatomy.feelers;\n                if(!anatomy)throw')
rig=rig.replace('spec.ArtDir.Substring(0,spec.ArtDir.Length-"/Directions".Length)+"/"+spec.Name+".png"','string.IsNullOrEmpty(spec.OriginalAtlasPath)?spec.ArtDir.Substring(0,spec.ArtDir.Length-"/Directions".Length)+"/"+spec.Name+".png":spec.OriginalAtlasPath')
rig=rig.replace('if (EnemyDirectionalAnimationPolish.TryAdd(clip, action, layout)) return;', 'if (EnemyDirectionalAnimationPolish.TryAdd(clip, action, layout)) return;\n            if (EnemyDirectionRemainingMotion.TryAdd(clip, action, layout, sprites)) return;')
builder=snapshot['Assets/Editor/EnemyDirectionPrefabBuilder.cs']
builder=builder.replace('public string Name;','public string Name;\n        public string OriginalAtlasPath;',1)
builder=builder.replace('if (!TryGetSpec(name, out spec)) return false;\n            var profile = AssetDatabase.LoadAssetAtPath<EnemyDirectionalProfile>(folder + "/Directions/" + name + "_Directions.asset");','if (!TryGetSpec(name, out spec) && !EnemyDirectionRemainingCatalog.TryGetSpecByAtlas(originalAtlasPath, out spec)) return false;\n            var profile = AssetDatabase.LoadAssetAtPath<EnemyDirectionalProfile>(spec.ProfilePath);')
review=snapshot['Assets/Editor/EnemyDirectionBatchReview.cs']
review=review.replace('string output=Root+"/"+name+"/"+revision;', 'string output=(EnemyDirectionRemainingCatalog.TryGetSpec(name,out spec)?"Docs/EnemyDirectionReview/Remaining_20261024":Root)+"/"+name+"/"+revision;')
review=review.replace('_out=Root+"/"+_request.name+"/"+_request.revision;', 'EnemyDirectionSpec outputSpec;\n            _out=(EnemyDirectionRemainingCatalog.TryGetSpec(_request.name,out outputSpec)?"Docs/EnemyDirectionReview/Remaining_20261024":Root)+"/"+_request.name+"/"+_request.revision;')
# A transient opt-out clone remains meaningful after the last battle prefab is adapted.
legacy='var legacy=Object.Instantiate(AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Prefabs/Enemy/Enemy_BugQueen.prefab")).GetComponent<BaseEnemy>();'
review=review.replace(legacy,legacy+'''
            var legacyVisual=legacy.GetComponent<EnemyDirectionalVisual>();if(legacyVisual)Object.DestroyImmediate(legacyVisual);
            var legacyRig=legacy.transform.Find("DirectionVisual");if(legacyRig)Object.DestroyImmediate(legacyRig.gameObject);
            legacy.GetComponent<Animator>().runtimeAnimatorController=AssetDatabase.LoadAssetAtPath<RuntimeAnimatorController>("Assets/_UIAssets/Monsters/_Common/Animations/BugQueen/Controller.controller");
            foreach(var sr in legacy.GetComponentsInChildren<SpriteRenderer>(true))sr.forceRenderingOff=false;''')
review=review.replace('Untouched BugQueen has no directional component','Explicit opt-out legacy clone has no directional component')
out=HERE/'staged_code';out.mkdir(exist_ok=True)
changes={'Assets/Editor/EnemyDirectionRemainingCatalog.cs':catalog,'Assets/Editor/EnemyDirectionalRigBuilder.cs':rig,'Assets/Editor/EnemyDirectionPrefabBuilder.cs':builder,'Assets/Editor/EnemyDirectionBatchReview.cs':review}
patch=[]
for p,content in changes.items():
    (out/Path(p).name).write_text(content,encoding='utf-8')
    patch.extend(difflib.unified_diff(snapshot.get(p,'').splitlines(True),content.splitlines(True),fromfile='before/'+p,tofile='after/'+p))
(HERE/'planned_editor_changes.patch').write_text(''.join(patch),encoding='utf-8')
print('Staged catalog and anatomical validator; production files unchanged.')
