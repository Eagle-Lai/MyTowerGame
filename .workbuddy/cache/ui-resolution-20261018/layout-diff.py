import pathlib,sys,json
sys.path.insert(0,'.workbuddy/tools')
import gen_ui_prefab_cache as g
base=pathlib.Path('.workbuddy/cache/ui-resolution-20261018')
def flat(d):
 out={}
 def walk(n):
  out[n['path']]={k:n.get(k) for k in ['anchorMin','anchorMax','pivot','anchoredPosition','sizeDelta','active','components']}
  for c in n['children']:walk(c)
 for r in d['roots']:walk(r)
 return out
res={}
for p in pathlib.Path('Assets/Prefabs/UI').glob('*.prefab'):
 before=flat(g.dump_prefab(str(base/'prefabs-before'/p.name)))
 after=flat(g.dump_prefab(str(p)))
 res[p.stem]={k:{'before':before.get(k),'after':after.get(k)} for k in before.keys()|after.keys() if before.get(k)!=after.get(k)}
pathlib.Path('Docs/UIResolution/20261018/layout-changes.json').write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf-8')
for k,v in res.items():print(k,len(v))
