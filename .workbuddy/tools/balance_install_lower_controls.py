"""Install already C#-rated legal lower-star trajectories; never computes star rules."""
import argparse,copy,pathlib,shutil
import balance_pipeline as core


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',default=str(core.JOBS/'lower-star-search'))
    parser.add_argument('--destination',default=str(core.DESIGN/'Simulation'));parser.add_argument('--recipe',required=True)
    args=parser.parse_args();source=pathlib.Path(args.source);destination=pathlib.Path(args.destination)
    indexes=core.read_json(source/'lower_star_index_160.json');recipe=core.read_json(args.recipe)
    expected={(profile['id'],row['id']):row['planHash'] for profile in recipe['profiles']
              for row in core.generate(recipe,profile['id'])['tables']['tblevelrating']}
    if len(indexes)!=160 or len({(r['profileId'],r['levelId']) for r in indexes})!=160:
        raise RuntimeError('Lower-star source must cover each of the 160 profile-level pairs exactly once')
    checked=[]
    for index in indexes:
        path=core.ROOT/index['resultPath'];r=core.read_json(path);m=r['metrics'];decision=r.get('ratingResult',{})
        key=(r['profileId'],r['levelId']);plan_hash=expected.get(key)
        if not (decision.get('valid') is True and decision.get('victory') is True and
          decision.get('stars') in [1,2,3,4] and m.get('victory') is True and m.get('completedWaveCount')==20 and
          m.get('hp',0)>0 and m.get('successfulSpawned')==m.get('expectedEnemyCount') and
          m.get('killed',0)+m.get('leaked',0)==m.get('expectedEnemyCount') and
          r.get('planHash')==m.get('planHash')==plan_hash and
          decision.get('versionKey','').endswith('|'+plan_hash) and r.get('operations') and
          all(op.get('balanceAfter',-1)>=0 for op in r['operations'])):
            raise RuntimeError('Not a complete C#-rated legal lower-star clear: '+str(path))
        checked.append((index,path,r))
    installed=[]
    for index,path,r in checked:
        target=destination/'lower-star'/r['profileId']/f'L{r["levelId"]:02}-lower-control'/'result.json'
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,target);shutil.copy2(path.with_name('operations.json'),target.with_name('operations.json'))
        core.write_json(target.with_name('source.json'),{'sourcePath':str(path),'originalSearchSource':r.get('selectionSource'),
          'kind':'offline_prediction_only','planHash':r['planHash'],'controlDescription':r.get('controlDescription'),
          'ratingSource':'FTProject.LevelRatingEvaluator; existing C# result preserved verbatim'})
        row=copy.deepcopy(index);row['resultPath']=str(target.relative_to(core.ROOT)).replace('\\','/')
        row['operationsPath']=str(target.with_name('operations.json').relative_to(core.ROOT)).replace('\\','/')
        installed.append(row)
    core.write_json(destination/'lower_star_index_160.json',installed)
    summary=core.read_json(source/'lower_star_summary.json')
    summary['sourceSearchFormalWrites']=summary.pop('formalWrites',False)
    summary['installedInTrackedEvidence']=True;summary['productionAssetsWritten']=False
    core.write_json(destination/'lower_star_summary.json',summary)
    shutil.copy2(source/'selected_economy_audit.json',destination/'lower_star_economy_audit.json')
    print(core.canonical({'installed':len(installed),'destination':str(destination),'allUniqueCSharpValidStarsOneToFour':True}))


if __name__=='__main__':main()
