"""Create a strict real-scene replay request from hash-matching legal operation evidence."""
import argparse,pathlib
import balance_pipeline as core

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--recipe',default=str(core.DEFAULT_RECIPE));ap.add_argument('--profile',default='D04')
    ap.add_argument('--levels',required=True);ap.add_argument('--operations-root',required=True);ap.add_argument('--out',required=True)
    ap.add_argument('--mode',default='high');ap.add_argument('--keep-playing',action='store_true')
    args=ap.parse_args();out=pathlib.Path(args.out).resolve();plan=core.generate(core.read_json(args.recipe),args.profile)
    candidate=core.write_candidate(plan,core.JOBS/('candidate-'+args.profile))
    runs=[]
    for level in map(int,args.levels.split(',')):
        resultpath=pathlib.Path(args.operations_root)/args.mode/args.profile/'mixed'/f'L{level:02}-mixed'/'result.json'
        result=core.read_json(resultpath)
        rating=next(r for r in plan['tables']['tblevelrating'] if r['id']==level)
        if not result or result['planHash']!=rating['planHash']:raise ValueError('Missing or stale replay source: '+str(resultpath))
        audit=next(a for a in plan['capacityEconomy'] if a['levelId']==level)
        runs.append({'profileId':args.profile,'levelId':level,'strategy':args.mode,'speed':1,
            'candidateDirectory':str(candidate),'operationsPath':str(resultpath.with_name('operations.json').resolve()),
            'capacity':audit['capacity'],'screenshots':level in [1,10,20,30]})
    path=out/'request.json';core.write_json(path,{'output':str(out),'stepSeconds':.05,'stepsPerUpdate':80,
        'runs':runs,'keepPlaying':args.keep_playing});print(str(path))

if __name__=='__main__':main()
