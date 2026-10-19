"""Repair old prediction schema and assemble evidence without implementing star rules."""
import argparse,json,pathlib
from balance_pipeline import ROOT,read_json,write_json

def normalize(result):
    m=result['metrics'];m['victory']=m.pop('isVictory',m.get('victory',False))
    if not m.get('waves'):
        m['waves']=[];elapsed=0.0
        for w in result['waves']:
            start=elapsed;elapsed+=w['combatElapsedMs']/1000
            m['waves'].append({'ordinal':w['waveOrdinal'],'expected':w['planned'],'successfulSpawned':w['successfulSpawned'],
              'killed':w['killed'],'leaked':w['leaked'],'bossLeaked':w['bossLeaked'],'criticalLeaked':w['criticalLeaked'],
              'gold':w['balance'],'hp':w['hp'],'killGold':w['killGold'],'clearGold':w['clearReward'],'peakAlive':w['alivePeak'],
              'combatStartSeconds':start,'combatEndSeconds':elapsed,'levelEndSeconds':w['levelElapsedMs']/1000})
    return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',default=str(ROOT/'Luban/BalanceDesign/Simulation'));args=parser.parse_args()
    base=pathlib.Path(args.root);rows=[]
    for p in base.glob('*/*/L*/result.json'):
        r=normalize(read_json(p));write_json(p,r)
        row={k:v for k,v in r.items() if k not in ['waves','operations','ratingProfile']}
        # Per-wave evidence remains in linked result.json; avoid duplicating it in
        # both aggregate matrices. Aggregates are indexes, never evaluator input.
        row['metrics']={k:v for k,v in r['metrics'].items() if k!='waves'}
        if 'ratingResult' in row:
            row['ratingResult']={k:v for k,v in row['ratingResult'].items() if k not in ['metrics','profile']}
        row['artifactPath']=str(p.relative_to(ROOT)).replace('\\','/');row['matrixGroup']=p.relative_to(base).parts[0]
        rows.append(row)
    baselines=[r for r in rows if r['matrixGroup'] in ['normal','power','mixed']]
    lower=[r for r in rows if r['matrixGroup']=='lower-star']
    write_json(base/f'matrix_{len(baselines)}.json',baselines)
    write_json(base/'matrix_references.json',[r for r in rows if r['matrixGroup']!='lower-star'])
    if lower:
        write_json(base/'matrix_lower.json',lower);write_json(base/'matrix_all.json',rows)
    summary={}
    for profile in ['D%02d'%i for i in range(1,9)]:
        subset=[r for r in baselines if r['profileId']==profile]
        summary[profile]={'runs':len(subset),'predictedClears':sum(r['result']=='predicted_clear' for r in subset),
          'noLeakUnderPar':sum(r['metrics']['victory'] and r['leaked']==0 and r['combatToParRatio']<=1 for r in subset),
          'uniqueLevelsWithNoLeakUnderPar':sorted(set(r['levelId'] for r in subset if r['metrics']['victory'] and r['leaked']==0 and r['combatToParRatio']<=1)),
          'ratingSource':'FTProject.LevelRatingEvaluator; values copied from result.json, never calculated in Python',
          'ratedRuns':sum(r.get('predictionStars') is not None for r in subset),
          'predictionStarsDistribution':{str(star):sum(r.get('predictionStars')==star for r in subset) for star in range(6)}}
    write_json(base/'summary.json',summary)
    # These are candidates for the C# unique evaluator, not independent star awards.
    references=[]
    for level in sorted(set(r['levelId'] for r in rows if r['profileId']=='D04')):
        options=[r for r in rows if r['profileId']=='D04' and r['levelId']==level]
        best=min(options,key=lambda r:(not r['metrics']['victory'],r['leaked'],max(0,r['combatToParRatio']-1),r['combatToParRatio']))
        strategy=best['strategyId'];p=(ROOT/best['artifactPath']).parent
        references.append({'levelId':level,'profileId':'D04','strategyId':strategy,'planHash':best['planHash'],
          'metrics':best['metrics'],'combatToParRatio':best['combatToParRatio'],'leaked':best['leaked'],
          'operationsPath':str((p/'operations.json').relative_to(ROOT)).replace('\\','/'),
          'resultPath':str((p/'result.json').relative_to(ROOT)).replace('\\','/'),
          'status':'offline reference candidate; requires Unity replay and C# unique evaluator'})
    write_json(base/'D04_reference_index.json',references)
    index=read_json(base/'reference_index_160.json',[])
    lower_by={(r['profileId'],r['levelId']):r for r in read_json(base/'lower_star_index_160.json',[])}
    for row in index:
        reference=read_json(ROOT/row['referenceResult']);control=read_json(ROOT/row['mistakeResult'])
        row.update(referencePredictionStars=reference.get('predictionStars'),referenceRatingValid=reference.get('ratingResult',{}).get('valid'),
          mistakePredictionStars=control.get('predictionStars'),mistakeRatingValid=control.get('ratingResult',{}).get('valid'),
          ratingSource=reference.get('ratingStatus'))
        lower_entry=lower_by.get((row['profileId'],row['levelId']))
        if lower_entry:
            row.update(lowerStarResult=lower_entry['resultPath'],lowerStarOperations=lower_entry['operationsPath'],
              lowerStarPredictionStars=lower_entry['predictionStars'],lowerStarRatingValid=lower_entry['ratingValid'],
              lowerStarVictory=lower_entry['victory'],lowerStarHp=lower_entry['hp'],lowerStarLeaked=lower_entry['leaked'])
    if index:
        write_json(base/'reference_index_160.json',index)
        coverage=read_json(base/'final_matrix_coverage.json',{})
        coverage.update(referenceValidCSharpFiveStars=sum(r['referencePredictionStars']==5 and r['referenceRatingValid'] for r in index),
          mistakeCSharpBelowFive=sum(r['mistakePredictionStars'] is not None and r['mistakePredictionStars']<5 for r in index),
          totalRuns=len(rows),baselineRuns=len(baselines),referenceRuns=sum(r['matrixGroup']=='reference' for r in rows),
          mistakeRuns=sum(r['matrixGroup']=='mistake' for r in rows),lowerStarRuns=len(lower),
          lowerStarValidCSharpClears=sum(r.get('lowerStarRatingValid') and r.get('lowerStarVictory') and 0<r.get('lowerStarPredictionStars',0)<5 for r in index),
          starDecision='Copied from each result.json after FTProject.LevelRatingEvaluator; no independent Python score')
        write_json(base/'final_matrix_coverage.json',coverage)
    print(json.dumps(summary,ensure_ascii=False))

if __name__=='__main__':main()
