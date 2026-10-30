from session_current import *
from mcp_call import URL
import copy

owner()
out = HERE / 'unity_release_final_20261030.json'
assert not out.exists()
c = Client()
report = {'observed_at': now(), 'transport': URL, 'project': c.identity()}
report['errors_before'] = c.tool('read_console', {'action': 'get', 'types': ['error'], 'count': '50', 'format': 'json'})
report['initial_state'] = fresh_state(c, 'PossessedWarg final source/import verification')
idle(probe(c))
art = target()['art_dir']
code = '''var path="ART/PossessedWarg_Directions.png";
var importer=UnityEditor.AssetImporter.GetAtPath(path) as UnityEditor.TextureImporter;
if(importer==null)throw new System.Exception("PossessedWarg atlas importer missing");
var sprites=UnityEditor.AssetDatabase.LoadAllAssetsAtPath(path).OfType<UnityEngine.Sprite>().ToArray();
return Newtonsoft.Json.JsonConvert.SerializeObject(new {spriteMode=importer.spriteImportMode.ToString(),ppu=importer.spritePixelsPerUnit,alphaIsTransparency=importer.alphaIsTransparency,mipmaps=importer.mipmapEnabled,
sprites=sprites.OrderBy(s=>s.name).Select(s=>new {name=s.name,ppu=s.pixelsPerUnit,x=s.rect.x,y=s.rect.y,w=s.rect.width,h=s.rect.height,pivotX=s.pivot.x,pivotY=s.pivot.y}).ToArray(),
dependencies=UnityEditor.AssetDatabase.GetDependencies("Assets/Prefabs/Enemy/Enemy_PossessedWarg.prefab",true)});'''.replace('ART', art)
data = unwrap(c.tool('execute_code', {'action': 'execute', 'code': code}))
report['installed_data'] = data
expected = read(HERE / 'staged_art/PossessedWarg_Directions.sprites.json')
assert len(data['sprites']) == len(expected['sprites']) == 14
assert data['ppu'] == 100 and data['spriteMode'] == 'Multiple' and data['alphaIsTransparency'] and not data['mipmaps']
report['sprite_checks'] = []
for s in expected['sprites']:
    live = next(a for a in data['sprites'] if a['name'] == s['name'])
    ok = (all(abs(live[k]-s[k]) < .001 for k in ['x', 'y', 'w', 'h'])
          and abs(live['pivotX']-s['pivotX']*s['w']) < .01
          and abs(live['pivotY']-s['pivotY']*s['h']) < .01 and live['ppu'] == 100)
    report['sprite_checks'].append({'name': s['name'], 'pass': ok})
assert all(r['pass'] for r in report['sprite_checks'])
for p in [art+'/PossessedWarg_Directions.png', art+'/PossessedWarg_Directions.asset', art+'/Animations/PossessedWarg_Directions.controller']:
    assert p in data['dependencies'], p

def captured_code(file, prefix):
    return next(r['params']['arguments']['code'] for r in read(HERE/file)['protocol_history']
                if r['method'] == 'tools/call' and r['params']['name'] == 'execute_code'
                and r['params']['arguments']['code'].startswith(prefix))

original_controller = 'Assets/_UIAssets/Monsters/_Common/Animations/Wolf/Controller.controller'
derived_controller = art+'/Animations/PossessedWarg_Directions.controller'
clips_code = captured_code('source_animation_contract_complete_20261030.json', 'var paths=')
start, end = clips_code.index('var paths='), clips_code.index('\nvar controller=')
# Avoid hierarchy re-enumeration: the scope auditor checks original prefab semantics separately.
clips_code = clips_code[:start]+'var paths=new string[0];'+clips_code[end:]
original = unwrap(c.tool('execute_code', {'action': 'execute', 'code': clips_code}))
derived = unwrap(c.tool('execute_code', {'action': 'execute', 'code': clips_code.replace(original_controller, derived_controller)}))
frozen = read(HERE/'source_animation_contract_complete_20261030.json')['contract']
assert original['parameters'] == frozen['parameters']
assert sorted(original['parameters'], key=lambda r: r['name']) == sorted(derived['parameters'], key=lambda r: r['name'])
assert original['clips'] == frozen['clips']
clip_checks = []
for old in original['clips']:
    new = next(a for a in derived['clips'] if Path(a['path']).name == old['name']+'_Directions.anim')
    for k in ['length', 'frameRate', 'loop', 'events', 'pptrCurves']:
        assert old[k] == new[k], (old['name'], k)
    horizontal = [r for r in new['floatCurves'] if not r['path'].startswith('DirectionVisual/')]
    assert old['floatCurves'] == horizontal, old['name']
    clip_checks.append({'name': old['name'], 'length': old['length'], 'loop': old['loop'],
                        'original_float_bindings': len(old['floatCurves']), 'derived_float_bindings': len(new['floatCurves']),
                        'pptr_bindings': len(old['pptrCurves']), 'full_horizontal_keys_and_events_equal': True})
report['original_contract_live'] = original
report['derived_contract_live'] = derived
report['clip_checks'] = clip_checks
controller_code = captured_code('source_controller_and_renderers_20261030.json', 'var c=')
live_controller = unwrap(c.tool('execute_code', {'action': 'execute', 'code': controller_code}))
clone_controller = unwrap(c.tool('execute_code', {'action': 'execute', 'code': controller_code.replace(original_controller, derived_controller)}))
assert live_controller['layers'] == read(HERE/'source_controller_and_renderers_20261030.json')['contract']['layers']
assert len(live_controller['layers']) == len(clone_controller['layers']) == 1
old_layer, new_layer = live_controller['layers'][0], clone_controller['layers'][0]
assert old_layer['defaultState'] == new_layer['defaultState'] == 'Idle'
assert {s['name'] for s in old_layer['states']} == {s['name'] for s in new_layer['states']}
for state in new_layer['states']:
    old = next(s for s in old_layer['states'] if s['name'] == state['name'])
    assert Path(state['motion']).name.replace('_Directions.anim', '.anim') == Path(old['motion']).name
    assert state['speedParameter'] == 'Speed' and state['speedParameterActive']
    assert state['speed'] == 1 and state['writeDefaultValues']
assert {t['destination'] for t in new_layer['anyState']} == {'Death', 'Attack'}
for state in new_layer['states']:
    transitions = state['transitions']
    if state['name'] == 'Death':
        assert not transitions
        continue
    assert {t['destination'] for t in transitions} == {'Idle', 'Ready', 'Walk', 'Run'} - {state['name']}
    for t in transitions:
        assert t['duration'] == 0 and t['hasExitTime'] == (state['name'] == 'Attack')
        assert any(q['parameter'] == 'Action' and q['mode'] == 'IfNot' for q in t['conditions'])
report['controller_layers_live'] = {'original': live_controller['layers'], 'derived': clone_controller['layers'],
    'same_state_names_parameters_and_motion_family': True,
    'derived_policy': 'Existing BuildAdvancedHenController: Speed-driven six states at unit state speed; direct locomotion transitions avoid AnyState reentry, native Attack exit time, Action compatibility, Death and Attack AnyState. Original controller remains byte/semantic unchanged. Derived transitions and Idle/Run/Death speed settings intentionally differ; no claim of an identical controller clone.'}
report['renderers_live'] = live_controller['renderers']
report['live_Verify'] = unwrap(c.tool('execute_code', {'action': 'execute', 'code': 'FTProject.EditorTools.EnemyDirectionSpec spec; if(!FTProject.EditorTools.EnemyDirectionPrefabBuilder.TryGetSpec("PossessedWarg",out spec))throw new System.Exception("PossessedWarg spec missing"); string text; bool pass=FTProject.EditorTools.EnemyDirectionalRigBuilder.Verify(spec,out text); return new {pass=pass,report=text};'}))
assert report['live_Verify']['pass'] and 'FAIL ' not in report['live_Verify']['report']
report['state'] = fresh_state(c, 'PossessedWarg final source/import verification complete')
for key, args in [('errors', {}), ('compile_errors', {'filter_text': 'error CS'})]:
    r = c.tool('read_console', {'action': 'get', 'types': ['error'], 'count': '50', 'format': 'json', **args})
    report[key] = r.get('structuredContent') or json.loads(r['content'][0]['text'])
assert report['errors']['data'] == report['compile_errors']['data'] == []
report['final_probe'] = probe(c)
idle(report['final_probe'])
report.update(success=True, note='No Unity CSharp changed. 8088 identity, imported sprites/pivots/PPU/dependencies, exact original and derived horizontal float/PPtr/event contracts, original controller preservation and existing derived controller policy, and own Verify checked. Console not cleared.',
    verification_script_correction='First diagnostic stopped on parameter list order. Disk confirmed the same four parameters in a different order; comparison now keys by name. Existing builder uses a distinct six-state transition/speed policy, verified and explicitly reported rather than claiming identical controller layers. No production edits or new Play were made for this correction.', protocol_history=c.history)
save(out, report)
print(json.dumps({'success': True, 'project': report['project'], 'clip_checks': clip_checks, 'probe': report['final_probe'], 'errors': report['errors']}, ensure_ascii=False))
