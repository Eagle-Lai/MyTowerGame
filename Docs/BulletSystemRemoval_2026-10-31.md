# 删除真实子弹系统 + 修正命中数双计 —— 2026-10-31

## 起因

复核“火力塔的 AOE 是否漏算对空”时，外部意见依据 `BaseBullet.Explode → EnemyGrid.QueryCircle → BaseEnemy.Hurt`
三段都没有飞行过滤，推断“落点内的飞行怪会被扣血”。逐行核对后确认：**这条链自 2026-10-17 起就没有调用者**，
是废弃代码；真正在跑的是 `BaseTower.Fire → DetonateAt → HurtEnemy`，其中 `DetonateAt` 有对空过滤、
`HurtEnemy` 有对空倍率。两者规则不一致，属于“死代码没跟着新规则改”的隐患，因此整体删除。

## 删除清单

### 运行时

| 位置 | 处理 |
|---|---|
| `Assets/Scripts/Bullet/BaseBullet.cs`（含 `BaseBullet` / `BulletManager` / `BulletState`） | 整文件删除 |
| `CombatSystem`：`_bullets`、`RegisterBullet`、`UnregisterBullet`、`TickBullets`、`CopyBullets`、`BulletCount` | 删除，`OnUpdate` 少一步“子弹推进” |
| `Launcher`：`BulletManager.Instance` 注册 | 删除 |
| `GameFlowManager`：`bulletRoot` 字段、`SetParent`、`RecycleAll`、预热 `keys.Add("Bullet_Normal")` | 删除 |
| `GameSceneLauncher`：`bulletRoot` 字段、注入、`Validate` 检查 | 删除 |
| `TowerConfig.FiresBullet` | 改名 `CanFire`（语义只剩“这座塔会不会开火”） |
| `BaseTower`：`SlowDurationSec = 2f` / `DotDurationSec = 3f` | 从 `BaseBullet` 迁入本类，成为唯一权威 |

### 资源与编辑器

| 位置 | 处理 |
|---|---|
| `ResTable`：`Bullet_Normal`、`Bullet_Dot` 两条登记 | 删除 |
| `ResBundle`：`BulletNormal` 常量 + `Fixed` 数组项（`bullet_normal` 包） | 删除 |
| `Assets/Prefabs/Bullet/Bullet_Normal.prefab`（含目录与 meta） | 删除 |
| `Assets/Art/Generated/Bullet_Dot.png`（含 meta） | 删除，`PlaceholderArtGenerator` 同步去掉生成段 |
| `BattlePrefabBuilder` | 只保留怪物预制体生成，删除 `BuildBullet` 与 `BulletPath` |
| `M0SetupWizard` | 删除子弹预制体校验与 `BulletRoot` 必需节点 |
| `SceneMainBuilder` | 不再创建 `BulletRoot`，不再给 launcher 赋 `bulletRoot` |
| `SortingLayerNormalizer` | 删除 `NormalizeBullet` 与审计块（`BoardSorting.Bullet` 保留给枪口焰/爆炸） |
| `PhysicsComponentCleaner` | 目录清单去掉 `Assets/Prefabs/Bullet` |
| `Assets/Scenes/Main.unity` | 用 Unity API 删除 `BulletRoot` 空节点并保存；diff 仅 34 行删除 |
| `Bundles/Android/FreeTower/OutputCache/freetower_bullet_normal.bundle` | 删除（未入库的构建缓存；历史 1.0.x 产物不动） |

## 明确保留

- `tbbulletdata` 配置表、`TowerInfo.bulletId`、`BulletConfig`、`Configs.GetBullet`：
  火力塔的 **AOE 半径 / 命中效果 / 效果值**仍从这张表取，删的是“子弹实体”，不是“子弹数据”。
- `BoardSorting.Bullet = 400`：`TowerFireFx` 的枪口焰/爆炸用 `Bullet + 1`，槽位继续有效。
- `Global.bulletPoolSize`：配置表不动（改表需手工），代码已无消费者，属于可追溯的空配置。

## 命中数双计修复

`BaseTower.HurtEnemy` 与 `BaseEnemy.Hurt` 各调一次 `CombatSystem.AddHitCount(1)`，`StatHitCount` 常年翻倍。
删除塔侧那一行，保留 `BaseEnemy.Hurt` —— 它是所有扣血的唯一终点（塔即时命中、DOT、将来任何来源都经过它）。
只影响 `PerfProbe` / `[Combat]` 调试输出的“命中”，不影响伤害、金币与评级。

## 验证

| 项 | 结果 |
|---|---|
| 编译 | `scriptCompilationFailed=False`，`isCompiling=False`，`error CS` 0 条 |
| EditMode 测试 | `FTProject.BalanceCombat.EditModeTests`：**29/29 通过**（含三条 AOE 对空用例） |
| 场景 | `Main.unity` 删除节点后重新打开 `Boot.unity`，`dirty=False`；场景 diff 仅删 `BulletRoot` 相关 34 行 |
| 残留检索 | `BulletManager` / `BaseBullet` / `Bullet_Normal` / `bulletRoot` / `BulletRoot` / `Bullet_Dot` 在 `Assets/**/*.cs` 中只剩历史注释 |

## 未做 / 后续

- **Play Mode 未跑**：删除的是不可达路径，但仍建议进一次关卡确认开火、AOE、减速、飘字正常。
- **AB 与热更需要重打**：`bullet_normal` 包从 `ResBundle.Fixed` 消失，包清单变化；按铁律走“重编 dll → 菜单 9 → 菜单 10 部署”。
- 已出 APK 内仍含旧包，属正常；下次出包自动消失。
- `EventController.cs:112` 的 `Debug.LogError("something error here")` 与 140 行 `InvalidCastException`
  是**历史遗留**（旧事件路由在移除类型不同的监听者时触发），与本次改动无关，未清理。
