import pathlib,sys,json
sys.path.insert(0,'.workbuddy/tools')
from _prefab_tree import parse,build,get_scalar
names=['GameIntroView','TowerInfoView','TowerCodexItem','SellConfirmView']
fields=['m_enableAutoSizing','m_fontSizeMin','m_fontSizeMax','m_enableWordWrapping','m_overflowMode']
paths={'GameIntroView':['Panel/Info'+str(i) for i in range(1,5)],'TowerInfoView':['Panel/Title'],'TowerCodexItem':['Body/'+n for n in ['TypeName','Role','DescText','DpsRow','RangeRow','SpeedRow','PriceRow']],'SellConfirmView':['Panel/TowerName','Panel/WarnText']}
def read(p):
 b=parse(str(p));gs,ts=build(b);out={}
 def walk(g,path):
  if path in paths[p.stem]:
   for fid in gs[g]['comps']:
    body=b[fid][1]
    if get_scalar(body,'m_enableAutoSizing') is not None:out[path]={f:get_scalar(body,f) for f in fields}
  for ch in ts[g]['children_go']:walk(ch,(path+'/' if path else '')+gs[ch]['name'])
 for g,t in ts.items():
  if t['parent_go'] is None:walk(g,'')
 return out
result={}
for n in names:
 a=read(pathlib.Path('Assets/Prefabs/UI')/(n+'.prefab'));b=read(pathlib.Path('Assets/__UIResolutionPreview20261018')/(n+'.prefab'))
 assert a==b,(n,a,b)
 assert a and all(row['m_enableAutoSizing']=='1' for row in a.values())
 result[n]=a
pathlib.Path('Docs/UIResolution/20261018/text-layout-comparison.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('All',sum(len(x) for x in result.values()),'changed text layouts match generated prefabs')
