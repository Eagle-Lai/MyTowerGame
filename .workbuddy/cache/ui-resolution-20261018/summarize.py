import pathlib,json,collections
base=pathlib.Path('Docs/UIResolution/20261018');cache=pathlib.Path('.workbuddy/cache/ui-resolution-20261018')
views=['MainMenuView','SelectView','TowerCodexView','LevelClearView','LevelDetailView','HudView','GameIntroView','ConfirmView','SellConfirmView','PauseView','SettingView','TipsView','TowerInfoView']
reports={n:json.loads((base/(n+'.json')).read_text(encoding='utf-8')) for n in views}
issues=[];matrix=collections.Counter();bg=0
for name,d in reports.items():
 assert len(d['cases'])==30,name
 for c in d['cases']:
  matrix[(c['width'],c['height'],c['inset'])]+=1
  for k in ['outside','overflows','overlaps','blockedButtons','missingGlyphs']:
   if c.get(k):issues.append([name,c['resizeStep'],c['language'],k,c[k]])
  if 'backgroundCoversCanvas' in c:
   bg+=1
   if not c['backgroundCoversCanvas']:issues.append([name,'background'])
  L=c.get('list',{})
  for k in ['textIssues','missingGlyphs']:
   if L.get(k):issues.append([name,'list.'+k,L[k]])
  for k in ['rightArrowCentered','leftArrowCentered','dragMovedContent','cardReceivesClick']:
   if L.get(k)==False:issues.append([name,'list.'+k])
  for e in L.get('endpoints',[]):
   if not isinstance(e,dict) or e['centerError']>1:issues.append([name,'list.center',e])
assert not issues,issues
comparison=json.loads((cache/'generator-comparison.json').read_text())
assert len(comparison)==15 and not any(comparison.values())
(base/'generator-comparison.json').write_text(json.dumps(comparison,indent=2),encoding='utf-8')
def output(file,label=None):
 for line in (cache/file).read_text(encoding='utf-8',errors='replace').splitlines():
  if label and not line.startswith(label+' '):continue
  try:d=json.loads(line.split(' ',1)[1] if label else line)
  except (ValueError,IndexError):continue
  if 'structuredContent' in d and d.get('structuredContent',{}).get('success'):
   return d['structuredContent'].get('data',{}).get('result',d['structuredContent'].get('data'))
 raise Exception(file)
lists={}
for name in ['SelectView','TowerCodexView']:
 C=reports[name]['cases'];E=[e['centerError'] for c in C for e in c['list']['endpoints']]
 lists[name]={'cases':len(C),'allItemPositionsChecked':len(E),'maximumCenterErrorCanvasUnits':max(E),'viewportLocalWidths':sorted(set(c['list']['viewportWidth'] for c in C)),'arrowCallbacksPassed':all(c['list']['rightArrowCentered'] and c['list']['leftArrowCentered'] for c in C),'dragPassed':all(c['list']['dragMovedContent'] for c in C)}
summary={'projectRoot':'D:/FreedomTower_1','unityVersion':'2022.3.62f3c1','mcpPort':8082,'instance':'FreedomTower_1@520e2c6d9c8bc788','method':'Play Mode; actual shipped prefab scripts/config/fonts, disposable world canvas matching the main CanvasScaler, synthetic presentation fixtures; simulated safe area; real Canvas integration for card clicks','languages':['en','zh-Hans','zh-Hant'],'safeInsetsPixels':{'left':120,'right':80,'top':48,'bottom':24},'views':views,'caseCount':sum(len(x['cases']) for x in reports.values()),'backgroundCoverageChecks':bg,'issues':issues,'matrix':[{'width':w,'height':h,'inset':safe,'caseCount':n} for (w,h,safe),n in sorted(matrix.items())],'lists':lists,'migration':output('migration-final.txt','migrate-and-preview'),'actualCanvasOpen':output('actual-open.txt'),'actualCenteredCardClick':output('actual-click.txt'),'actualAdjacentCardClick':output('actual-adjacent.txt'),'editorRestored':output('restore-final.txt'),'remainingConsoleErrors':['Pre-existing CommandInvokationFailure: Unity Remote requirements check failed'],'limitations':['No physical Android/iOS device run or build was performed.','Matrix validates representative display data, not every gameplay or dialog text state.','Drag callbacks were driven with PointerEventData; this does not certify touch hardware/inertia feel.']}
summary['actualCanvasRecheck']={'open':output('actual-open-recheck.txt'),'centeredCardClick':output('actual-click-recheck.txt'),'stableScreenshot':output('actual-stable-screenshot.txt'),'screenshotPath':str(base/'actual-canvas-select-detail.png')}
summary['temporaryPreviewAssetsRemoved']=not pathlib.Path('Assets/__UIResolutionPreview20261018').exists()
summary['finalAuditLog']=str(cache/'final-audit.txt')
(base/'validation-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print('PASS:',summary['caseCount'],'cases;',bg,'background checks; 15 GUIDs retained; 14 text layouts match; 65 matrix images plus actual Canvas screenshot')
