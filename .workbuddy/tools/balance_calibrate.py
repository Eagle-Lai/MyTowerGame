"""Create an explicit, reviewable draft calibration; never applies it automatically.

Consumes resolved baseline budgets from the shared compiler. Preserves all opening
benchmarks, counts, rewards and resources. Every changed later budget is an explicit
recipe override and remains subject to the compiler's strict growth constraints.
"""
import argparse,copy,math,pathlib
from balance_pipeline import ROOT,DEFAULT_RECIPE,read_json,generate,write_json,validate

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',default=str(ROOT/'Library/BalanceWorkbench/calibration-draft'))
    ap.add_argument('--ratios',default='D05:0.92,D06:0.80,D07:0.70,D08:0.60');args=ap.parse_args()
    recipe=read_json(DEFAULT_RECIPE);base=copy.deepcopy(recipe);recipe['overrides']=[o for o in recipe.get('overrides',[]) if not o.get('id','').startswith('calibration-budget-')]
    changes=[]
    for part in args.ratios.split(','):
        profile,ratio=part.split(':');ratio=float(ratio);plan=generate(base,profile);budgets={}
        for wave in plan['waves']:
            L,w=wave['levelId'],wave['waveOrdinal'];value=wave['targetEhp'] if w==1 else wave['targetEhp']*ratio
            # Envelope is materialized as explicit final values, never an invisible user-input correction.
            if w>1:value=max(value,math.ceil(budgets[L,w-1]*1.04))
            if L>1:value=max(value,math.ceil(budgets[L-1,w]*1.04))
            budgets[L,w]=value
            if abs(value-wave['targetEhp'])>1e-9:
                recipe['overrides'].append({'id':f'calibration-budget-{profile}-{L}-{w}','profileId':profile,'target':'wave','scope':'wave',
                    'levelId':L,'waveOrdinal':w,'field':'targetEhp','mode':'replace','value':value,
                    'reason':'Spatial strategies fail with initial EHP ladder; opening benchmark preserved, later budgets reduced to match fixed kill income; pending Unity verification'})
                changes.append({'profileId':profile,'levelId':L,'waveOrdinal':w,'before':wave['targetEhp'],'after':value})
    out=pathlib.Path(args.out);write_json(out/'recipe.json',recipe);write_json(out/'budget_changes.json',changes)
    results={}
    for profile in [part.split(':')[0] for part in args.ratios.split(',')]:
        plan=generate(recipe,profile);results[profile]=validate(plan)
    write_json(out/'validation.json',results)
    print(str(out/'recipe.json'))

if __name__=='__main__':main()
