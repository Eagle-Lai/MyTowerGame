"""Curate the final 480 baselines, 160 references and 160 explicit mistake controls.

Simulation artifacts only. Keeps a recoverable Library copy of superseded high-
profile predictions and never changes production Excel, Gen or ConfigJson.
"""
import argparse,collections,copy,pathlib,shutil
import balance_pipeline as core


def good(r):return r['metrics']['victory'] and not r['leaked'] and r['combatToParRatio']<=1


def copy_artifact(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
    ops=src.with_name('operations.json')
    if ops.exists():shutil.copy2(ops,dst.with_name('operations.json'))


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--recipe',required=True);args=ap.parse_args()
    recipe=core.read_json(args.recipe);out=core.DESIGN/'Simulation';archive=core.JOBS/'pre-gradient-simulation'
    original=core.read_json(out/'matrix_480.json',[]);core.write_json(out/'initial_high_profiles_superseded.json',
      {'status':'superseded_by_explicit_later_growth_calibration','records':[r for r in original if r['profileId']>='D05'],
       'reason':'Initial EHP growth outran fixed kill income; real Unity high-profile failures triggered explicit ordered later-wave overrides. Opening benchmarks unchanged.',
       'recoverableOriginalDirectory':str(archive)})
    for strategy in ['normal','power','mixed']:
        for profile in ['D05','D06','D07','D08']:
            old=out/strategy/profile;backup=archive/strategy/profile
            if old.exists() and not backup.exists():shutil.copytree(old,backup)
            src=core.JOBS/('gradient-'+strategy+'-matrix')/profile
            shutil.copytree(src,old,dirs_exist_ok=True)
    roots=[out/'normal',out/'power',out/'mixed',core.JOBS/'gradient-reference-search-D05-D06',
      core.JOBS/'gradient-reference-search-D07-D08',core.JOBS/'D04-extra-references',
      core.JOBS/'gradient-wall-opening-search',core.JOBS/'gradient-D07-wall-opening-search',
      core.JOBS/'gradient-optimize-D08-L20',core.JOBS/'gradient-D08-L10-extra-references']
    by=collections.defaultdict(list)
    for root in roots:
        for path in root.glob('**/result.json'):
            if 'scratch' in path.parts:continue
            result=core.read_json(path)
            if isinstance(result,dict) and result.get('metrics'):
                by[result['profileId'],result['levelId'],result['planHash']].append((result,path))
    index=[]
    for profile in recipe['profiles']:
        plan=core.generate(recipe,profile['id'])
        for L in range(1,21):
            rating=plan['tables']['tblevelrating'][L-1];key=(profile['id'],L,rating['planHash'])
            matches=[item for item in by[key] if good(item[0])]
            if not matches:raise RuntimeError('Missing legal zero-leak under-Par reference '+str(key))
            result,path=min(matches,key=lambda item:item[0]['combatToParRatio'])
            dest=out/'reference'/profile['id']/f'L{L:02}-reference'/'result.json';copy_artifact(path,dest)
            core.write_json(dest.with_name('source.json'),{'originalPath':str(path),'planHash':rating['planHash'],'kind':'offline_prediction_only'})
            control=core.JOBS/'final-mistake-matrix'/profile['id']/f'L{L:02}-mistake'/'result.json'
            bad=core.read_json(control)
            if bad['planHash']!=rating['planHash'] or good(bad):raise RuntimeError('Invalid mistake control '+str(control))
            copy_artifact(control,out/'mistake'/profile['id']/f'L{L:02}-mistake'/'result.json')
            index.append({'profileId':profile['id'],'levelId':L,'planHash':rating['planHash'],'coverage':'offline_prediction_only',
              'referenceResult':str(dest.relative_to(core.ROOT)).replace('\\','/'),'referenceOperations':str(dest.with_name('operations.json').relative_to(core.ROOT)).replace('\\','/'),
              'referenceLeaked':result['leaked'],'referenceCombatToParRatio':result['combatToParRatio'],
              'mistakeResult':str((out/'mistake'/profile['id']/f'L{L:02}-mistake'/'result.json').relative_to(core.ROOT)).replace('\\','/'),
              'mistakeLeaked':bad['leaked'],'mistakeVictory':bad['metrics']['victory']})
    core.write_json(out/'reference_index_160.json',index)
    core.write_json(out/'final_matrix_coverage.json',{'baselineRuns':480,'referenceRuns':160,'mistakeRuns':160,'totalRuns':800,
      'referenceNoLeakUnderPar':len(index),'mistakeFailureControls':sum(not r['mistakeVictory'] for r in index),
      'starDecision':'Await C# LevelRatingEvaluator; no independent Python score','recipeSource':args.recipe,'productionApplied':False})
    (out/'README.md').write_text('# 离线策略与对照证据\n\n`normal`、`power`、`mixed` 为完整 480 条基线矩阵；`reference` 为八档各 20 关的 160 条合法零漏怪且战斗时间不超过 Par 的预测参考；`mistake` 为 160 条明确失误的失败对照。每次操作按实时余额消费，不预支奖励。星数由 Unity 的唯一 C# LevelRatingEvaluator 回填，离线结果不认证真实五星。\n\n`reference_index_160.json` 可直接定位每关的完整操作轨迹。初版高档结果已被显式后期 EHP 梯度校准替代，摘要见 `initial_high_profiles_superseded.json`；真实实测覆盖由 Reports 的 hash 匹配索引另列。\n',encoding='utf-8')
    print(str(out/'final_matrix_coverage.json'))


if __name__=='__main__':main()
