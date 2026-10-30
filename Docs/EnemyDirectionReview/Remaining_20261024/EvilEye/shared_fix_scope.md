# Builder serialization repair

The initial installation passed actual runtime checks but the independent component audit found that HeadRenderer changed from null to the original Body SpriteRenderer. The initial audit and runtime evidence remain preserved.

EnemyDirectionalRigBuilder.Apply calls ResetForSpawn for initial view selection. That call can resolve a missing head reference through MonsterAnimEventReceiver.SetHead. The builder now saves and restores the receiver reference around that preview initialization, including exceptional exits. Runtime lazy resolution remains unchanged. Only EvilEye is rebuilt in this revision; other production prefabs are not rebuilt.

repair_01 restores EvilEye's original null reference, then rebuilds with the fixed builder. The original HeadSprites, object identity, horizontal art, event contract, HP and gameplay parameters remain protected by the component audit. The initial manifests, backups and media are retained. Final runtime evidence uses runtime_r02 and runtime_updeath_r02.
