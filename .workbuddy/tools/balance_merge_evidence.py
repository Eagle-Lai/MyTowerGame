"""Merge hash-matching predictions and real Unity results into generated wave reports.

Explicit output only; this command never applies Excel/runtime data. Historical
results with another plan hash are counted as unmatched and never certify a plan.
"""
import argparse,collections,copy,os,pathlib,re
from balance_pipeline import ROOT,DEFAULT_RECIPE,read_json,write_json,generate,dimensions,export_reports,seconds_to_ms,unity_trajectory_finished


def relative(path):
    path=pathlib.Path(path).resolve()
    try:return str(path.relative_to(ROOT)).replace('\\','/')
    except ValueError:return str(path)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--recipe',default=str(DEFAULT_RECIPE));ap.add_argument('--runtime',action='append',default=[])
    ap.add_argument('--offline-root',action='append',default=[]);ap.add_argument('--out',required=True);ap.add_argument('--recipe-draft')
    args=ap.parse_args();recipe=copy.deepcopy(read_json(args.recipe));out=pathlib.Path(args.out)
    if args.runtime:recipe['calibrationEvidence']=list(dict.fromkeys(relative(p) for p in args.runtime))
    if args.recipe_draft:write_json(args.recipe_draft,recipe)
    runs=collections.defaultdict(list);runtime_count=0;offline_count=0
    for path in args.runtime:
        payload=read_json(path);records=payload if isinstance(payload,list) else payload.get('results',[])
        for i,r in enumerate(records):
            key=(r.get('profileId'),r.get('levelId'),r.get('profile',{}).get('planHash',r.get('metrics',{}).get('planHash')))
            runs[key].append({'kind':'unity','path':relative(path),'recordIndex':i,'record':r});runtime_count+=1
    for root in args.offline_root or [ROOT/'Luban/BalanceDesign/Simulation']:
        for path in pathlib.Path(root).glob('**/result.json'):
            r=read_json(path)
            if not isinstance(r,dict) or not r.get('metrics') or not r.get('planHash'):continue
            key=(r.get('profileId'),r.get('levelId'),r['planHash'])
            runs[key].append({'kind':'offline','path':relative(path),'record':r});offline_count+=1
    level_count=dimensions(recipe)[0];total_levels=level_count*len(recipe['profiles'])
    combined=[];coverage=[];reference_index=[];matched_runtime=0;matched_offline=0
    for profile in recipe['profiles']:
        plan=generate(recipe,profile['id'])
        for level in plan['levels']:
            matches=runs.get((profile['id'],level['levelId'],level['planHash']),[])
            level_runs=[]
            for item in matches:
                r=item['record'];metrics=r['metrics'];kind=item['kind']
                evidence={'kind':kind,'path':item['path'],'runId':metrics.get('runId'),'strategy':r.get('strategy',r.get('strategyId')),
                  'victory':metrics.get('victory'),'leaked':metrics.get('leaked'),'completedWaveCount':metrics.get('completedWaveCount'),
                  'combatElapsedMs':seconds_to_ms(metrics.get('combatElapsedSeconds',metrics.get('combatElapsedMs',0)/1000)),
                  'levelElapsedMs':seconds_to_ms(metrics.get('levelElapsedSeconds',metrics.get('levelElapsedMs',0)/1000)),
                  'stars':r.get('stars') if kind=='unity' else r.get('predictionStars'),
                  'valid':r.get('valid') if kind=='unity' else r.get('ratingResult',{}).get('valid'),
                  'operationsPath':item['path'] if kind=='unity' else relative(pathlib.Path(ROOT/item['path']).with_name('operations.json'))}
                if kind=='offline':evidence['selectedAs']=r.get('selectedAs')
                if kind=='unity':
                    evidence['recordIndex']=item['recordIndex'];matched_runtime+=1
                    evidence.update(state=r.get('state'),trajectoryFinished=unity_trajectory_finished(r),fundingPolicy=r.get('fundingPolicy'),
                      pendingOperationCount=len(r.get('pendingOperations') or []),operationError=r.get('operationError'))
                    name=re.sub(r'[^A-Za-z0-9_-]','_',str(evidence['strategy'])+'-'+str(evidence['runId'] or item['recordIndex']))
                    operations=out/'References'/profile['id']/f'L{level["levelId"]:02}-{level["planHash"]}'/(name+'-operations.json')
                    write_json(operations,r.get('operations',[]));evidence['operationsPath']=relative(operations)
                    write_json(operations.with_name(name+'-source.json'),{'profileId':profile['id'],'levelId':level['levelId'],
                      'planHash':level['planHash'],'runId':evidence['runId'],'sourcePath':item['path'],
                      'sourceRecordIndex':item['recordIndex'],'operationsPath':evidence['operationsPath'],
                      'coverage':r.get('coverage'),'stars':r.get('stars'),'valid':r.get('valid'),'state':r.get('state'),
                      'fundingPolicy':r.get('fundingPolicy'),'pendingOperationCount':len(r.get('pendingOperations') or []),'operationError':r.get('operationError')})
                else:matched_offline+=1
                evidence['combatToParRatio']=evidence['combatElapsedMs']/next(x for x in plan['tables']['tblevelrating'] if x['id']==level['levelId'])['parCombatTimeMs']
                level_runs.append(evidence)
                actual_by={w['ordinal']:w for w in metrics.get('waves',[])}
                for wave in [w for w in plan['waves'] if w['levelId']==level['levelId']]:
                    actual=actual_by.get(wave['waveOrdinal'])
                    if not actual:continue
                    trace={'path':item['path'],'strategy':evidence['strategy'],'runId':evidence['runId'],'runStars':evidence['stars'],
                      'runValid':evidence['valid'],'successfulSpawned':actual.get('successfulSpawned'),'killed':actual.get('killed'),
                      'leaked':actual.get('leaked'),'bossLeaked':actual.get('bossLeaked'),'criticalLeaked':actual.get('criticalLeaked'),
                      'balance':actual.get('gold'),'hp':actual.get('hp'),'peakAlive':actual.get('peakAlive'),
                      'combatElapsedMs':seconds_to_ms(actual.get('combatEndSeconds',0)-actual.get('combatStartSeconds',0)),
                      'levelEndMs':seconds_to_ms(actual.get('levelEndSeconds',0))}
                    if kind=='unity':trace.update(recordIndex=item['recordIndex'],state=r.get('state'),trajectoryFinished=evidence['trajectoryFinished'])
                    wave.setdefault('unityRuns' if kind=='unity' else 'offlineRuns',[]).append(trace)
            level['evidenceRuns']=level_runs
            unity=[r for r in level_runs if r['kind']=='unity'];witness=level.get('unityReference',{})
            five=[r for r in unity if r['path']==relative(witness.get('path','')) and r['recordIndex']==witness.get('recordIndex')]
            lower=[r for r in unity if r['trajectoryFinished'] and r['valid'] and r['victory'] and 0<r['stars']<5]
            failed=[r for r in unity if not r['victory']]
            offline_five=[r for r in level_runs if r['kind']=='offline' and r['valid'] and r['stars']==5]
            offline_lower=[r for r in level_runs if r['kind']=='offline' and r['valid'] and r['victory'] and 0<r['stars']<5]
            preferred=min(five,key=lambda r:r['combatElapsedMs']) if five else min(offline_five,key=lambda r:r['combatElapsedMs']) if offline_five else None
            reference_index.append({'profileId':profile['id'],'levelId':level['levelId'],'planHash':level['planHash'],
              'calibrationStatus':level['calibrationStatus'],
              'preferredFiveStarReference':preferred,
              'preferredReferenceCoverage':'Unity PlayMode' if five else 'offline_prediction_only',
              'unityFiveStarReference':min(five,key=lambda r:r['combatElapsedMs']) if five else None,
              'unityLowerStarControl':min(lower,key=lambda r:(r['stars'],-r['leaked'])) if lower else None,
              'unityFailureControl':failed[0] if failed else None,
              'offlinePredictionReferences':offline_five,
              'offlineLowerStarControl':min(offline_lower,key=lambda r:(r.get('selectedAs')!='legal_clear_lower_star_control',r['stars'])) if offline_lower else None})
            coverage.append({'profileId':profile['id'],'levelId':level['levelId'],'planHash':level['planHash'],
              'calibrationStatus':level['calibrationStatus'],'unityRuns':sum(x['kind']=='unity' for x in matches),
              'offlineRuns':sum(x['kind']=='offline' for x in matches),
              'unityFiveStar':level['calibrationStatus']=='verified_unity_reference',
              'unityLowerStarClear':bool(lower),'offlineLowerStarClear':bool(offline_lower),
              'offlineFiveStarPrediction':any(x['kind']=='offline' and x['valid'] and x['stars']==5 for x in level_runs)})
        export_reports(plan,out/profile['id']);combined.extend(plan['waves'])
    write_json(out/f'all_waves_{len(combined)}.json',combined);write_json(out/'coverage.json',coverage)
    write_json(out/'reference_index.json',reference_index)
    write_json(out/'evidence_index.json',{'runtimeRecords':runtime_count,'matchedRuntimeRecords':matched_runtime,
      'unmatchedRuntimeRecords':runtime_count-matched_runtime,'offlineRecords':offline_count,'matchedOfflineRecords':matched_offline,
      'unmatchedOfflineRecords':offline_count-matched_offline,'verifiedUnityLevels':sum(r['unityFiveStar'] for r in coverage),
      'totalProfileLevels':total_levels,'waveCount':len(combined),'productionApplied':False})
    lines=['# 数值与参考证据入口','',
      f'八档共 {total_levels} 关、{len(combined)} 波；匹配真实运行 {matched_runtime}/{runtime_count} 条、离线运行 {matched_offline}/{offline_count} 条。',
      f'真实五星严格认证 {sum(r["unityFiveStar"] for r in coverage)}/{total_levels} 关；其余关卡保留离线参考和待验证标记。',
      '', '`reference_index.json` 的 `preferredFiveStarReference` 优先指向同版本、完整操作的真实五星；否则明确使用离线预测。',
      '`coverage.json` 分别记录静态计划、离线与真实覆盖；all_waves 文件为逐波完整数据，各档另有 JSON、CSV、地图、资源清单与可读 Markdown。',
      '', '|预设|真实五星关卡|真实有效低星关卡|离线有效低星关卡|', '|---|---:|---:|---:|']
    for profile in recipe['profiles']:
        subset=[r for r in coverage if r['profileId']==profile['id']]
        lines.append(f'|{profile["id"]} {profile["name"]}|{sum(r["unityFiveStar"] for r in subset)}/{level_count}|{sum(r["unityLowerStarClear"] for r in subset)}/{level_count}|{sum(r["offlineLowerStarClear"] for r in subset)}/{level_count}|')
    lines+=['','## D04 正式预设逐关参考','', '|关卡|参考覆盖|星|战斗/Par|操作|', '|---:|---|---:|---:|---|']
    for row in [r for r in reference_index if r['profileId']=='D04']:
        ref=row['preferredFiveStarReference']
        if not ref:continue
        operation_link=os.path.relpath(ROOT/ref['operationsPath'],out).replace('\\','/')
        lines.append(f'|{row["levelId"]}|{row["preferredReferenceCoverage"]}|{ref["stars"]}|{ref["combatToParRatio"]:.3f}|[operations]({operation_link})|')
    lines+=['','真实操作的来源 sidecar 保留原始结果文件、记录索引、runId、完整 hash、完成状态与资金等待策略。',
      '未完成或被拒绝的操作轨迹仍留在原始证据中，但不能成为五星参考。离线完整结果和 1—4 星/失败对照位于 `../Simulation/`。','']
    (out/'README.md').write_text('\n'.join(lines),encoding='utf-8')
    print(str(out/'evidence_index.json'))


if __name__=='__main__':main()
