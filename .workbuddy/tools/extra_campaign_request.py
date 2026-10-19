"""Actual upgrade ablation and finite sparse counterexample replay requests."""
import pathlib
import balance_pipeline as core

def main():
    root=core.ROOT;out=root/'Docs/BalanceEvidence/30x25/final-ablations';recipe=core.read_json(core.DEFAULT_RECIPE);p=core.generate(recipe,'D04')
    candidate=root/'Library/BalanceWorkbench/final-maze-D04/ConfigJson';runs=[];pruned=[]
    for r in core.read_json(root/'Docs/BalanceEvidence/30x25/final-reference/unity-results.json'):
        if r['profileId']!='D04':continue
        L=r['levelId'];inactive={(t['row'],t['col']) for t in r['towerContributions'] if not t['participated']}
        ops=[op for op in r['operations'] if not (op['action']=='upgrade' and (op['row'],op['col']) in inactive)]
        path=out/'Operations'/f'L{L:02}-pruned.json';core.write_json(path,ops)
        cap=next(a['capacity'] for a in p['capacityEconomy'] if a['levelId']==L)
        runs.append({'profileId':'D04','levelId':L,'strategy':'maze-pruned-upgrades','speed':1,'candidateDirectory':str(candidate),'operationsPath':str(path),'capacity':cap})
        pruned.append({'levelId':L,'removedUpgradeCost':sum(op['cost'] for op in r['operations'])-sum(op['cost'] for op in ops),'removedOperations':len(r['operations'])-len(ops),'source':'final-reference/unity-results.json'})
    for L in [1,7,10,20,30]:
        for mode in ['small','low']:
            path=root/'Luban/BalanceDesign/Evidence30x25/Search'/mode/'D04'/f'L{L:02}'/'best/operations.json'
            runs.append({'profileId':'D04','levelId':L,'strategy':mode+'-finite-best','speed':1,'candidateDirectory':str(candidate),'operationsPath':str(path),'capacity':next(a['capacity'] for a in p['capacityEconomy'] if a['levelId']==L),'waitForFunds':True})
    core.write_json(out/'upgrade-ablation-source.json',pruned)
    core.write_json(out/'request.json',{'output':str(out),'stepSeconds':.05,'stepsPerUpdate':240,'runs':runs})
    print(str(out/'request.json'),len(runs))
if __name__=='__main__':main()
