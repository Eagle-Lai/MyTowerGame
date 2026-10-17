"""Stage profile-specific map calibration drafts; no formal files are touched."""
import argparse,copy,pathlib
from balance_pipeline import ROOT,DEFAULT_RECIPE,read_json,write_json,generate,path_for

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',default=str(ROOT/'Library/BalanceWorkbench/map-calibration'));p.add_argument('--profiles',default='D05,D06,D07,D08');p.add_argument('--recipe',default=str(DEFAULT_RECIPE));a=p.parse_args()
    recipe=read_json(a.recipe);base=copy.deepcopy(recipe);changes=[]
    for profile in a.profiles.split(','):
        plan=generate(base,profile)
        for m in plan['tables']['tblevelmap']:
            rows=m['rows'];cols=m['cols'];cells=[list(r) for r in m['cells']];points={c:(x,y) for y,r in enumerate(cells) for x,c in enumerate(r) if c in 'SE'}
            horizontal=abs(points['S'][0]-points['E'][0])>=abs(points['S'][1]-points['E'][1])
            for i in range(2):
                if horizontal:
                    x=cols*(i+1)//3
                    for y in range(rows):
                        if y!=(rows-1 if i==0 else 0) and cells[y][x]=='.':cells[y][x]='#'
                else:
                    y=rows*(i+1)//3
                    for x in range(cols):
                        if x!=(cols-1 if i==0 else 0) and cells[y][x]=='.':cells[y][x]='#'
            strings=[''.join(r) for r in cells]
            if not path_for(strings):continue
            recipe['overrides'].append({'id':f'calibration-map-{profile}-{m["levelId"]}','profileId':profile,'target':'map','scope':'level',
                'levelId':m['levelId'],'field':'cells','mode':'replace','value':strings,
                'reason':'Spatial failures: preserve opening economy/EHP and flight line; extend ground fire windows with two staggered walls. Candidate only, pending Unity.'})
            changes.append({'profileId':profile,'levelId':m['levelId'],'beforePath':len(path_for(m['cells']))-1,'afterPath':len(path_for(strings))-1})
    out=pathlib.Path(a.out);write_json(out/'recipe.json',recipe);write_json(out/'map_changes.json',changes)
    print(out/'recipe.json')

if __name__=='__main__':main()
