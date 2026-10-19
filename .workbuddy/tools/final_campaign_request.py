"""Rebind actual legal maze operations to the final Par/config identity, then replay."""
import argparse, pathlib
import balance_pipeline as core

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--kind',choices=['reference','checkpoints','performance'],default='reference');a=ap.parse_args()
    recipe=core.read_json(core.DEFAULT_RECIPE);out=pathlib.Path(a.out).resolve()
    index=core.read_json(core.ROOT/'Luban/BalanceDesign/Evidence30x25/Par/reference-index.json')
    candidates={p['id']:core.write_candidate(core.generate(recipe,p['id']),core.JOBS/('final-maze-'+p['id'])) for p in recipe['profiles']}
    runs=[]
    for row in index:
        p,L=row['profileId'],row['levelId']
        if a.kind!='reference' and (p!='D04' or L!=30):continue
        base={'profileId':p,'levelId':L,'strategy':'maze','speed':1,'candidateDirectory':str(candidates[p]),'operationsPath':row['operationsPath'],'capacity':row['capacity'],'screenshots':a.kind=='reference' and p=='D04' and L in [1,10,20,30]}
        if a.kind=='checkpoints':
            for scenario,wave,speed in [('boundary_resume',24,1),('half_wave_rollback',25,1),('terminal_duplicate',25,1),('speed_baseline',25,1),('speed_baseline',25,2),('speed_baseline',25,3)]:
                runs.append(dict(base,checkpointScenario=scenario,checkpointWave=wave,speed=speed,speedComparisonGroup='L30-final-operations' if scenario=='speed_baseline' else ''))
        else:
            if a.kind=='performance':
                base.pop('candidateDirectory',None)
                base['operationsPath']=str(core.ROOT/'Docs/BalanceEvidence/30x25/final-ablations/Operations/L30-pruned.json')
                high=dict(base,strategy='high-occupancy-performance',operationsPath=str(core.ROOT/'Luban/BalanceDesign/Evidence30x25/Simulation/high/D04/mixed/L30-mixed/operations.json'),waitForFunds=True)
                runs.append(high)
            runs.append(base)
    if a.kind=='checkpoints':
        plan=core.generate(recipe,'D04')
        for L in [1,10,20,30]:
            path=core.ROOT/'Luban/BalanceDesign/Evidence30x25/Simulation/high/D04/mixed'/f'L{L:02}-mixed/operations.json'
            runs.append({'profileId':'D04','levelId':L,'strategy':'high-occupancy-control','speed':1,'candidateDirectory':str(candidates['D04']),'operationsPath':str(path),'capacity':next(x['capacity'] for x in plan['capacityEconomy'] if x['levelId']==L),'waitForFunds':True})
        lower=core.read_json(core.ROOT/'Luban/BalanceDesign/Evidence30x25/Controls/lower-index.json')
        for L in [1,10,20,30]:
            source=next(x['source'] for x in lower if x['levelId']==L);path=pathlib.Path(source).resolve().with_name('operations.json')
            runs.append({'profileId':'D04','levelId':L,'strategy':'lower-star-control','speed':1,'candidateDirectory':str(candidates['D04']),'operationsPath':str(path),'capacity':next(x['capacity'] for x in plan['capacityEconomy'] if x['levelId']==L),'waitForFunds':True})
    core.write_json(out/'request.json',{'output':str(out),'stepSeconds':1/60 if a.kind=='performance' else .05,'stepsPerUpdate':240,'runs':runs,'keepPlaying':a.kind=='performance','renderedPerformance':a.kind=='performance'})
    print(str(out/'request.json'),len(runs))
if __name__=='__main__':main()
