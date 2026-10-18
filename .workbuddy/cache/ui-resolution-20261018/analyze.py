import pathlib,json,collections
base=pathlib.Path('Docs/UIResolution/20261018')
for p in base.glob('*.json'):
 d=json.loads(p.read_text(encoding='utf-8-sig'))
 if 'cases' not in d:continue
 issues=collections.defaultdict(set)
 for c in d['cases']:
  for k in ['outside','overflows','overlaps','blockedButtons','missingGlyphs']:
   issues[k].update(c.get(k,[]))
  if c.get('backgroundCoversCanvas')==False:issues['background'].add(str(c['resizeStep']))
  L=c.get('list',{})
  for k in ['textIssues','missingGlyphs']:issues['list.'+k].update(L.get(k,[]))
  for k in ['rightArrowCentered','leftArrowCentered','dragMovedContent','cardReceivesClick']:
   if L.get(k)==False:issues['list.'+k].add(str(c['resizeStep']))
  for e in L.get('endpoints',[]):
   if not isinstance(e,dict) or e['centerError']>1:issues['list.center'].add(str(e))
 print(p.stem,dict((k,sorted(v)) for k,v in issues.items() if v))
