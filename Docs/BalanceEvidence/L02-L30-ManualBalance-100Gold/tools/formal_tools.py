"""Read formal exports and prepare manifests of literal edits. No value generation."""
import json,pathlib,hashlib,argparse
ROOT=pathlib.Path(__file__).resolve().parents[4]
REPORT=ROOT/'Docs/BalanceEvidence/L02-L30-ManualBalance-100Gold'
KEYS=['tbenemydata','tbenemylist','tbrounddata','tbsceneinfo','tblevelmap','tbtowerinfo','tbbulletdata','tbglobal']
FIELDS=['id','difficultyTier','profileId','profileRevision','expectedWaveCount','expectedEnemyCount','twoStarHpPermille','threeStarHpPermille','fourStarHpPermille','maxFourStarLeaks','fourStarTimePermille','parCombatTimeMs','bossVariantIds','criticalVariantIds','balanceRevision','ratingRevision','planHash']
def tables():
    return {p.stem:json.loads(p.read_text(encoding='utf-8-sig')) for p in (ROOT/'Assets/ConfigJson').glob('*.json')}
def runtime_hash():
    raw=''
    for key in KEYS:raw+=key+'\n'+(ROOT/'Assets/ConfigJson'/f'{key}.json').read_text(encoding='utf-8-sig').replace('\r\n','\n').replace('\r','\n')+'\n'
    for r in sorted(tables()['tblevelrating'],key=lambda r:r['id']):raw+='|'.join(','.join(map(str,r[f])) if isinstance(r[f],list) else str(r[f]) for f in FIELDS)+'\n'
    return hashlib.sha256(raw.encode()).hexdigest()

def level_gameplay_identity(level,t):
    """Full reachable level records and shared combat tables, excluding rating."""
    scene=next(x for x in t['tbsceneinfo']if x['id']==level)
    rounds={x['id']:x for x in t['tbrounddata']};groups={x['id']:x for x in t['tbenemylist']};enemies={x['id']:x for x in t['tbenemydata']}
    rs=[rounds[i]for i in scene['RoundList']];gs=[groups[i]for r in rs for i in r['EnemyIndexs']]
    ids=sorted({i for g in gs for i in g['EnemyIndexs']})
    payload=dict(scene=scene,rounds=rs,groups=gs,enemies=[enemies[i]for i in ids],map=next(x for x in t['tblevelmap']if x['id']==scene['mapId']),tower=t['tbtowerinfo'],bullet=t['tbbulletdata'],globalConfig=t['tbglobal'])
    return hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()

def frozen_input_paths():
    """Enumerate both file contents and set membership for the frozen Unity inputs."""
    code = sorted({p for folder in ['Assets', 'Packages']
                   for source in (ROOT / folder).rglob('*')
                   if source.is_file() and source.suffix in ['.cs', '.asmdef', '.asmref', '.rsp']
                   for p in [source, pathlib.Path(str(source) + '.meta')] if p.is_file()})
    assets = {p for source in (ROOT / 'Assets/Prefabs/Enemy').glob('*.prefab')
              for p in [source, pathlib.Path(str(source) + '.meta')] if p.is_file()}
    for directory in (ROOT / 'Assets/_UIAssets/Monsters').rglob('Directions'):
        if directory.is_dir():
            assets.update(p for p in directory.rglob('*') if p.is_file())
            meta = pathlib.Path(str(directory) + '.meta')
            if meta.is_file(): assets.add(meta)
    assets.update(p for folder, pattern in [('Assets/Scenes', '*.unity'), ('ProjectSettings', '*')]
                  for source in (ROOT / folder).glob(pattern)
                  for p in [source, pathlib.Path(str(source) + '.meta')] if p.is_file())
    assets.update(p for p in [ROOT / 'Packages/manifest.json', ROOT / 'Packages/packages-lock.json']
                  if p.is_file())
    return code, sorted(assets)

def frozen_input_fingerprints():
    code, assets = frozen_input_paths()
    return {kind: {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in paths}
            for kind, paths in [('codeSha256', code), ('combatAssetSha256', assets)]}

_trial_input_current_cache={}
_current_fingerprint_cache=None
def trial_inputs_match_current(resultfile):
    """Data hashes alone do not certify code/art equivalence after coordination."""
    manifest=pathlib.Path(resultfile).parent/'inputs/input-manifest.json'
    if manifest in _trial_input_current_cache:return _trial_input_current_cache[manifest]
    global _current_fingerprint_cache
    match=manifest.exists()
    if match:
        value=json.loads(manifest.read_text(encoding='utf-8'))
        if _current_fingerprint_cache is None:
            _current_fingerprint_cache=frozen_input_fingerprints()
        for kind in ['codeSha256','combatAssetSha256']:
            if value.get(kind)!=( _current_fingerprint_cache[kind] ):
                match=False;break
    _trial_input_current_cache[manifest]=match
    return match
def manifest(path):
    source=json.loads((REPORT/'audit/current-source-records.json').read_text(encoding='utf-8'));waves=json.loads((REPORT/'audit/current-waves.json').read_text(encoding='utf-8'));spec=json.loads(path.read_text(encoding='utf-8'));edits=[]
    def add(record,field,value,reason):
        before=record['data'][field]
        if before==value:return
        if isinstance(before,list):before=','.join(map(str,before))
        if isinstance(value,list):value=','.join(map(str,value))
        edits.append(dict(path=record['path'],sheet=record['sheet'],cell=record['cells'][field],before=before,after=value,reason=reason))
    for key,fields in spec.get('records',{}).items():
        table,pk=key.split(':')
        for field,item in fields.items():add(source[table][pk],field,item['value'],item['reason'])
    for row in spec.get('waves',[]):
        w=next(w for w in waves if w['level']==row['level'] and w['wave']==row['wave'])
        if 'gap' in row:add(w['sourceGroups'][0],'enemyInterval',row['gap'],row['reason'])
        if 'clear' in row:add(w['sourceRound'],'rewardGold',row['clear'],row['reason'])
        for name,fields in row.get('enemies',{}).items():
            targets=[e for e in w['enemyDetails'] if e['data']['name']==name or name=='@air' and e['data']['isFlying'] or name=='@ground' and not e['data']['isFlying']];assert targets,(row,name)
            for e in targets:
                for field,value in fields.items():add(e,field,value,row['reason'])
    out=path.with_suffix('.cells.json');out.write_text(json.dumps(edits,ensure_ascii=False,indent=2),encoding='utf-8');print(str(out),len(edits),'literal cells')
def formal_plan():
    t=tables();enemies={e['id']:e for e in t['tbenemydata']};rounds={r['id']:r for r in t['tbrounddata']};groups={g['id']:g for g in t['tbenemylist']};waves=[]
    for level in t['tbsceneinfo']:
        for ordinal,rid in enumerate(level['RoundList'],1):
            r=rounds[rid];assert len(r['EnemyIndexs'])==1
            g=groups[r['EnemyIndexs'][0]];ids=g['EnemyIndexs'];unique=list(dict.fromkeys(ids));roles={i:'boss' if enemies[i]['type']==5 else 'flying' if enemies[i]['isFlying'] else 'heavy' if enemies[i]['type']==3 else 'normal' for i in unique}
            waves.append(dict(levelId=level['id'],waveOrdinal=ordinal,enemyIds=ids,composition=[dict(variantId=i,role=roles[i]) for i in unique],count=len(ids),actualEhp=sum(enemies[i]['hp']/(1-enemies[i]['armor']) for i in ids),spawnIntervalMs=g['enemyInterval'],rewardGold=r['rewardGold'],flyingCount=sum(enemies[i]['isFlying'] for i in ids),heavyCount=sum(roles[i]=='heavy' for i in ids),eliteCount=0,bossCount=sum(roles[i]=='boss' for i in ids)))
    return dict(profileId=t['tblevelrating'][0]['profileId'],tables=t,waves=waves)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['hash','manifest']);p.add_argument('path',nargs='?',type=pathlib.Path);a=p.parse_args()
    if a.action=='hash':print(runtime_hash())
    else:manifest(a.path)
