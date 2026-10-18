import json,sys,pathlib,re
sys.path.insert(0,'.workbuddy/tools')
import gen_ui_prefab_cache as g
base=pathlib.Path('.workbuddy/cache/ui-resolution-20261018')
result={}
keys=['anchorMin','anchorMax','anchoredPosition','sizeDelta','pivot','active']
def flat(tree):
 out={}
 def walk(n):
  out[n['path']]={k:n[k] for k in keys if k in n}
  for c in n['children']:walk(c)
 for r in tree['roots']:walk(r)
 return out
for p in pathlib.Path('Assets/Prefabs/UI').glob('*.prefab'):
 a=flat(g.dump_prefab(str(p)));b=flat(g.dump_prefab('Assets/__UIResolutionPreview20261018/'+p.name))
 diff={k:{'production':a.get(k),'generated':b.get(k)} for k in a.keys()|b.keys() if a.get(k)!=b.get(k)}
 result[p.stem]=diff
 print(p.stem,len(diff),'layout differences')
 for k,v in diff.items():print(k,v)
 assert (base/'prefabs-before'/p.with_suffix('.prefab.meta').name).read_bytes()==p.with_suffix('.prefab.meta').read_bytes(),p
(base/'generator-comparison.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('All 15 prefab GUID/meta files retained')