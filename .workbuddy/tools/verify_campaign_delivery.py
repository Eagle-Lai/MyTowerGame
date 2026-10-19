"""Summarize existing acceptance artifacts; never invent gameplay certification."""
import collections,pathlib,re
import balance_pipeline as core

def main():
    root=core.ROOT;out=root/'Docs/BalanceEvidence/30x25';e=root/'Luban/BalanceDesign/Evidence30x25'
    recipe=core.read_json(core.DEFAULT_RECIPE);plan=core.generate(recipe,'D04');checks=[]
    def check(name,passed,source,details=None):checks.append({'name':name,'passed':bool(passed),'source':source,'details':details})
    validation=core.validate(plan,root/'Assets/ConfigJson');core.write_json(out/'formal-readback.json',validation)
    check('formal D04 30 levels / 750 waves / runtime float32 and hash readback',validation['passed'] and len(plan['levels'])==30 and len(plan['waves'])==750,'formal-readback.json')
    static=core.read_json(e/'Reports/validation.json',{});check('eight profiles static 6000 waves',static.get('passed') and static.get('waves')==6000,'Reports/validation.json')
    reference=core.read_json(out/'final-reference/unity-results.json',[])
    check('58 final-hash real five-star references',len(reference)==58 and all(r['state']=='finished' and r['valid'] and r['stars']==5 and not r['pendingOperations'] and r['metrics']['leaked']==0 and r['metrics']['completedWaveCount']==25 for r in reference),'final-reference/unity-results.json')
    ablations=core.read_json(out/'final-ablations/unity-results.json',[]);pruned=[r for r in ablations if r['strategy']=='maze-pruned-upgrades']
    check('30 real successful upgrade ablations',len(pruned)==30 and all(r['state']=='finished' and r['stars']==5 and r['valid'] and not r['metrics']['leaked'] for r in pruned),'final-ablations/unity-results.json')
    matrix=core.read_json(out/'strategy-matrix.json',[]);check('720 scored three-strategy predictions',sum(r['mode']=='baseline' and r['stars'] is not None for r in matrix)==720,'strategy-matrix.json')
    economy=core.read_json(out/'route-economy.json',{});check('all 30 before-wave-25 cash ledgers',len(economy.get('rows',[]))==30 and not economy.get('issues') and all(r['cashReconciled'] and r['minOperationBalance']>=0 for r in economy['rows']),'route-economy.json')
    speed=core.read_json(out/'final-checkpoints/speed-comparison.json',{});check('24->25 / half wave25 / terminal duplicate / 1x 2x 3x exact comparison',speed.get('passed'),'final-checkpoints/speed-comparison.json')
    checkpoint=core.read_json(out/'final-checkpoints/unity-results.json',[])
    high=[r for r in checkpoint if r['strategy']=='high-occupancy-control'];check('real high occupancy controls L1/10/20/30',sorted(r['levelId'] for r in high)==[1,10,20,30],'final-checkpoints/unity-results.json',[(r['levelId'],r['stars'],r['state']) for r in high])
    low=[]
    for r in core.read_json(e/'Controls/lower-index.json',[]):
        result=core.read_json(r['source']) if r.get('source') else {}
        low.append({**r,'predictionStars':result.get('predictionStars'),'valid':result.get('ratingResult',{}).get('valid'),'victory':result.get('metrics',{}).get('victory')})
    core.write_json(out/'lower-star-index.json',low);check('D04 each level legal lower-star offline control',len(low)==30 and all(r['valid'] and r['victory'] and 0<r['predictionStars']<5 for r in low),'lower-star-index.json')
    perf=core.read_json(out/'final-performance/unity-results.json',[])
    check('real rendered-frame high-board performance',len(perf)>=2 and all(r.get('renderedPerformance',{}).get('completed') and r['renderedPerformance']['samples']==180 for r in perf),'final-performance/unity-results.json')
    gameplay=[core.read_json(p) for p in (out/'final-performance').glob('Gameplay-*/gameplay-capture.json')]
    check('actual battle 3 languages x 2 resolutions',len(gameplay)>=2 and all(r.get('passed') and len(r['results'])==6 for r in gameplay),'final-performance/Gameplay-*/gameplay-capture.json')
    ui=core.read_json(out/'UI/ui-visual-results.json',{});check('36 shipped prefab UI captures',ui.get('images')==36,'UI/ui-visual-results.json')
    check('visible UI overflow/glyph checks',bool(ui) and all(r['issueCount']==0 for r in ui.get('results',[])),'UI/ui-visual-results.json',[(r['scenario'],r['language'],r['width'],r['issueCount']) for r in ui.get('results',[]) if r['issueCount']])
    safety=core.read_json(out/'runtime-safety.json',{});check('pause / capacity / migration / once-only rewards / JSON and SQLite retry',safety.get('passed'),'runtime-safety.json')
    bundle=core.read_json(out/'config-bundle.json',{});check('real Android-target config bundle build and every TextAsset readback',bundle.get('passed') and bundle.get('ratingRows')==30,'config-bundle.json')
    driver=core.read_json(root/'Library/BalanceWorkbench/acceptance-driver-state.json',{});check('Workbench stage/apply/new hash/report/rollback and official save isolation',driver.get('passed') and driver.get('formalHashesRestored') and driver.get('officialSaveHashesUnchanged') and driver.get('keyShardUnchanged'),'workbench-acceptance.json')
    if driver:core.write_json(out/'workbench-acceptance.json',{'resultPath':str(pathlib.Path(driver.get('output',''))/'result.json'),'passed':driver.get('passed'),'formalHashesRestored':driver.get('formalHashesRestored'),'officialSaveHashesUnchanged':driver.get('officialSaveHashesUnchanged'),'keyShardUnchanged':driver.get('keyShardUnchanged'),'elapsedSeconds':driver.get('elapsedSeconds')})
    log=(root/'Library/BalanceWorkbench/30x25-python-final-tests.log').read_text(encoding='utf-8-sig',errors='replace');check('51 Python compiler/calibration/IO tests',bool(re.search(r'Ran 51 tests',log)) and re.search(r'\nOK\s*$',log),'python-tests.log');(out/'python-tests.log').write_text(log,encoding='utf-8')
    unity=core.read_json(out/'unity-tests.json',{});check('Unity EditMode tests',unity.get('passed'),'unity-tests.json')
    compile=core.read_json(out/'unity-final-validation.json',{});check('correct Unity instance / ready / compilationFailed false / classified console',compile.get('passed'),'unity-final-validation.json')
    numerical_gaps=[{'objective':'Klow sparse references should not remain widespread five-star','observedDefaultD04FiveStars':sum(r['mode']=='low' and r['profileId']=='D04' and r['stars']==5 for r in matrix),'actualRepresentativeFiveStars':sum(r['strategy']=='low-finite-best' and r['stars']==5 and r['state']=='finished' for r in ablations),'status':'not fully achieved; counterexamples retained'},
        {'objective':'all profile-level Unity calibration','verified':58,'total':240,'pending':182,'status':'required representative minimum met; remaining combinations not certified'},
        {'objective':'globally longest legal path and minimal upgrade cost','status':'finite search and verified feasible cost only; no proof of global optimum'},
        {'objective':'Android device performance','status':'Editor rendered frames sampled; no device FPS certification'}]
    result={'implementationAcceptancePassed':all(r['passed'] for r in checks),'allBalanceObjectivesAchieved':False,'balanceRevision':recipe['balanceRevision'],'profileId':'D04','checks':checks,'numericalGaps':numerical_gaps}
    core.write_json(out/'final-verification.json',result);print(core.canonical({'checks':len(checks),'failed':[r['name'] for r in checks if not r['passed']],'allBalanceObjectivesAchieved':False}))
if __name__=='__main__':main()
