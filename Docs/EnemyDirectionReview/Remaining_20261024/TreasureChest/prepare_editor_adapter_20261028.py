from session_treasurechest import *
owner()
source=R/'Assets/Editor/EnemyDirectionBatchReview.cs'
s=source.read_text(encoding='utf-8')
s=s.replace('EnemyDirectionBatchReview','TreasureChestDirectionReview').replace('MimicChest','TreasureChest')
old='if (!EnemyDirectionPrefabBuilder.TryGetSpec(name, out spec) || (name != "AdvancedHen" && !spec.UseSeparateViewRigs))'
assert s.count(old)==1
s=s.replace(old,'if (name != "TreasureChest" || !EnemyDirectionPrefabBuilder.TryGetSpec(name, out spec) || !spec.UseSeparateViewRigs)')
s=s.replace('if (Running || BalancePlayModeVerifier.Running','if (Running || EnemyDirectionBatchReview.Running || BalanceVideoRecorder.Running || BalancePlayModeVerifier.Running')
s=s.replace('"Assets/Prefabs/Enemy/Enemy_TreasureChest.prefab") : null','"Assets/_UIAssets/Monsters/Inanimate/TreasureChest/TreasureChest.prefab") : null')
old='''var sourceReceiver = sourcePrefab ? sourcePrefab.GetComponent<MonsterAnimEventReceiver>() : null;'''
assert s.count(old)==1;s=s.replace(old,'// Source art prefab has no gameplay receiver; original battle receiver is intentionally null-head/empty-array.')
s=s.replace('headlessContainer && receiver && sourceReceiver','headlessContainer && receiver && sourcePrefab')
s=s.replace('&& !sourceReceiver.HeadRenderer && sourceReceiver.HeadSprites != null && sourceReceiver.HeadSprites.Length == 0','&& sourcePrefab.transform.Find("Body/Normal") && sourcePrefab.transform.Find("Body/Broken")')
s=s.replace('Native attack event selects angry','Compatibility attack event selects closed attack state').replace('Native attack returns normal expression','Compatibility attack returns closed state').replace('Native death event selects directional dead head','Directional death event selects opened chest state')
s=s.replace('public int frame, expression;','public int frame, expression;\n            public bool originalNormalActive, originalBrokenActive;\n            public string shownSprite;\n            public Vector3 originalBodyPosition, originalBodyEuler;')
old='alive=_enemy.IsAlive,recycled=_enemy.IsFullyRecycled,paused=GameClock.IsPaused,headAngry=_visual.HeadIndex==1,shadow=!NoShadow(_enemy)};'
assert s.count(old)==1
s=s.replace(old,'alive=_enemy.IsAlive,recycled=_enemy.IsFullyRecycled,paused=GameClock.IsPaused,headAngry=_visual.HeadIndex==1,shadow=!NoShadow(_enemy), originalNormalActive=_enemy.transform.Find("Body/Normal").gameObject.activeSelf,originalBrokenActive=_enemy.transform.Find("Body/Broken").gameObject.activeSelf,shownSprite=_visual.Head.sprite.name,originalBodyPosition=_enemy.transform.Find("Body").localPosition,originalBodyEuler=_enemy.transform.Find("Body").localEulerAngles};')
s='// TreasureChest-only adaptation of existing real Play harness; all checks and timing retained.\n'+s
(D/'TreasureChestDirectionReview.cs.txt').write_text(s,encoding='utf-8')
write(D/'editor_adapter_derivation_20261028.json',dict(observed_at=now(),parent=source.relative_to(R).as_posix(),parent_sha256=sha(source),output='TreasureChestDirectionReview.cs.txt',output_sha256=sha(D/'TreasureChestDirectionReview.cs.txt'),changes=['Unique class/session keys and TreasureChest-only start guard','Same84 checks; source sprite comparison uses original art prefab Normal/Broken and exact null-head receiver contract','Original generic review and recorder occupancy excluded','State activation/body transforms and current sprite captured in every actual frame','No manual Animator.Update; same real Play lifecycle, timing and scene restore','Compatibility event labels explicitly distinguish added events from original Container clips'],builder='TreasureChestDirectionAdapter.cs.txt',builder_sha256=sha(D/'TreasureChestDirectionAdapter.cs.txt'),shared_CSharp_modified=False))
print(json.dumps(dict(prepared='target-only Editor source',review_sha=sha(D/'TreasureChestDirectionReview.cs.txt'))))
