"""Keep board area/buildable cells while replacing short vertical combat corridors."""
import copy,pathlib
import balance_pipeline as core
from balance_campaign import capacity

def main():
    recipe=core.read_json(core.DEFAULT_RECIPE);plan=core.generate(recipe,'D04');changes=[]
    for board in plan['tables']['tblevelmap']:
        if board['id']>20:continue
        cells=board['cells'];start=next((x,y) for y,row in enumerate(cells) for x,c in enumerate(row) if c=='S')
        end=next((x,y) for y,row in enumerate(cells) for x,c in enumerate(row) if c=='E')
        if abs(end[0]-start[0])>=len(cells[0])*.6:continue
        new=[list(row.replace('S','.').replace('E','.')) for row in cells]
        if start[1] <= end[1]:new[0][0]='S';new[-1][-1]='E'
        else:new[-1][-1]='S';new[0][0]='E'
        new=[''.join(row) for row in new]
        before=capacity(cells);after=capacity(new)
        if before['buildableCells']!=after['buildableCells']:raise ValueError('Do not reduce buildable cells')
        recipe['mapDefinitions'].append({'id':board['id'],'levelId':board['id'],'cells':new})
        changes.append({'levelId':board['id'],'oldCells':cells,'newCells':new,'oldCapacity':before,'newCapacity':after,
            'reason':'Preserve dimensions, obstacles and buildable area; extend short eight-step ground/air traversal to permit multiple firing zones'})
    destination=core.JOBS/'30x25-corridors';core.write_json(destination/'recipe.json',recipe)
    core.write_json(destination/'map-changes.json',changes)
    print([r['levelId'] for r in changes])

if __name__=='__main__':main()
