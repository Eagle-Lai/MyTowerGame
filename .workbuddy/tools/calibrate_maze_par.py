"""Bind Par to actual 25-wave spawn spans and clear tails; preserve raw witnesses."""
import argparse,math,pathlib,statistics
import balance_pipeline as core

def elapsed_ms(metrics):
    # Unity JsonUtility serializes the seconds field, not computed properties.
    return core.seconds_to_ms(metrics['combatElapsedSeconds'])

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--inputs',nargs='+',required=True);ap.add_argument('--out',required=True);a=ap.parse_args()
    recipe=core.read_json(core.DEFAULT_RECIPE);plans={p['id']:core.generate(recipe,p['id']) for p in recipe['profiles']}
    witnesses={};rejected=[]
    for name in a.inputs:
        path=pathlib.Path(name)
        for i,r in enumerate(core.read_json(path,[])):
            key=(r.get('profileId'),r.get('levelId'));p=plans.get(key[0]);m=r.get('metrics',{})
            if not p:continue
            rating=next(t for t in p['tables']['tblevelrating'] if t['id']==key[1])
            if r.get('state')!='finished' or r.get('pendingOperations') or not r.get('valid') or m.get('leaked') or not m.get('victory') or m.get('completedWaveCount')!=p['wavesPerLevel'] or r.get('profile',{}).get('planHash')!=rating['planHash']:
                rejected.append({'source':str(path),'index':i,'profileId':key[0],'levelId':key[1],'reason':'unfinished, leaks, stale identity or incomplete operations'});continue
            if key not in witnesses or elapsed_ms(m)<elapsed_ms(witnesses[key]['run']['metrics']):
                witnesses[key]={'source':str(path),'index':i,'run':r}
    missing=[L for L in range(1,31) if ('D04',L) not in witnesses]
    if missing:raise ValueError('D04 actual no-leak 25-wave witnesses missing: '+str(missing))
    out=pathlib.Path(a.out);core.write_json(out/'recipe-before-par.json',recipe);rows=[];calibration={};index=[]
    for profile,p in plans.items():
        scales=[]
        for L in [1,10,20,30]:
            if (profile,L) in witnesses:
                span=sum(w['plannedSpawnSpanMs'] for w in p['waves'] if w['levelId']==L)
                d04span=sum(w['plannedSpawnSpanMs'] for w in plans['D04']['waves'] if w['levelId']==L)
                baseline=elapsed_ms(witnesses['D04',L]['run']['metrics'])-d04span
                scales.append((elapsed_ms(witnesses[profile,L]['run']['metrics'])-span)/max(1,baseline))
        factor=statistics.median(scales) if scales else math.sqrt(next(x['ehpMultiplier'] for x in recipe['profiles'] if x['id']==profile))
        calibration[profile]={}
        for level in p['levels']:
            L=level['levelId'];span=sum(w['plannedSpawnSpanMs'] for w in p['waves'] if w['levelId']==L);witness=witnesses.get((profile,L))
            if witness:
                elapsed=elapsed_ms(witness['run']['metrics']);tail=elapsed-span;method='measured 25-wave spawn span + actual legal maze clear tails, 6% scheduling margin, rounded up to 5s'
                source={'sourceFile':witness['source'],'sourceIndex':witness['index'],'sourcePlanHash':witness['run']['profile']['planHash']}
                ops=[{k:op[k] for k in ['waveOrdinal','timeMs','action','row','col','towerId','cost','balanceAfter']} for op in witness['run']['operations']]
                dest=out/'ReferenceOperations'/profile/f'L{L:02}.json';core.write_json(dest,ops)
                index.append({'profileId':profile,'levelId':L,**source,'operationsPath':str(dest.resolve()),'capacity':witness['run']['waveBoundaries'][0]['capacity']})
            else:
                d04span=sum(w['plannedSpawnSpanMs'] for w in plans['D04']['waves'] if w['levelId']==L)
                tail=(elapsed_ms(witnesses['D04',L]['run']['metrics'])-d04span)*factor;elapsed=span+tail
                method='estimate: this level D04 measured tail times median representative profile tail ratio; pending full-level Unity timing'
                source={'referenceProfile':'D04','tailScale':factor}
            par=5000*math.ceil(elapsed*1.06/5000)
            entry={'combatBasisHash':level['combatBasisHash'],'parCombatTimeMs':par,'method':method,
                'spawnSpanMs':span,'clearTailMs':tail,'observedCombatMs':elapsed,'measured':bool(witness),**source}
            calibration[profile][str(L)]=entry;rows.append({'profileId':profile,'levelId':L,**entry})
    recipe['parCalibration']=calibration;core.write_json(core.DEFAULT_RECIPE,recipe)
    core.write_json(out/'par-calibration.json',{'method':'6% bounded scheduling margin; source clocks exclude pauses and automatic waits','rows':rows,'rejectedRecords':rejected})
    core.write_json(out/'reference-index.json',index);print('calibrated',len(rows),'measured',len(index))
if __name__=='__main__':main()
