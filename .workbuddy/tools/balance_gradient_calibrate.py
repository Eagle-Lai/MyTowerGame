"""Stage an explicit high-profile growth calibration with intact opening benchmarks.

Never applies production data. Final budgets preserve the adjacent-wave/level
envelope and the eight-profile EHP ordering; timing/economy are unchanged.
"""
import argparse,copy,math,pathlib
from balance_pipeline import ROOT,DEFAULT_RECIPE,read_json,generate,write_json,validate


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',default=str(ROOT/'Library/BalanceWorkbench/gradient-calibration'))
    ap.add_argument('--late-multipliers',default='D05:1.04,D06:1.08,D07:1.12,D08:1.16')
    args=ap.parse_args();base=read_json(DEFAULT_RECIPE);recipe=copy.deepcopy(base)
    recipe['overrides']=[o for o in recipe.get('overrides',[]) if not o.get('id','').startswith('gradient-calibration-')]
    ref=generate(base,'D04');ref_b={(w['levelId'],w['waveOrdinal']):w['targetEhp'] for w in ref['waves']}
    previous=dict(ref_b);changes=[];plans={};summaries={}
    for part in args.late_multipliers.split(','):
        profile,mul=part.split(':');mul=float(mul);original=generate(base,profile);budgets={}
        for wave in original['waves']:
            L,w=wave['levelId'],wave['waveOrdinal']
            value=wave['targetEhp'] if w==1 else max(ref_b[L,w]*mul,previous[L,w])
            if w>1:value=max(value,math.ceil(budgets[L,w-1]*1.04))
            if L>1:value=max(value,math.ceil(budgets[L-1,w]*1.04))
            budgets[L,w]=value
            if abs(value-wave['targetEhp'])>1e-9:
                recipe['overrides'].append({'id':f'gradient-calibration-{profile}-{L}-{w}','profileId':profile,'target':'wave','scope':'wave',
                    'levelId':L,'waveOrdinal':w,'field':'targetEhp','mode':'replace','value':value,
                    'reason':'Real Unity high-profile failures: retain opening benchmark and all other profile multipliers, reduce later HP growth while preserving cross-profile ordering; candidate awaiting Unity reference'})
                changes.append({'profileId':profile,'levelId':L,'waveOrdinal':w,'before':wave['targetEhp'],'after':value,'ratioToD04':value/ref_b[L,w]})
        previous=budgets
    out=pathlib.Path(args.out);write_json(out/'recipe.json',recipe);write_json(out/'budget_changes.json',changes)
    for profile in ['D04','D05','D06','D07','D08']:
        plan=generate(recipe,profile);plans[profile]=plan;summaries[profile]=validate(plan)
        write_json(out/profile/'resolved-plan.json',plan)
    for a,b in zip(list(plans),list(plans)[1:]):
        assert all(x['targetEhp']<=y['targetEhp'] for x,y in zip(plans[a]['waves'],plans[b]['waves'])),(a,b)
    write_json(out/'validation.json',{'profiles':summaries,'crossProfileEhpGradient':True,'openingBenchmarksPreserved':True,'productionApplied':False})
    print(str(out/'recipe.json'))


if __name__=='__main__':main()
