# 修改文件清单

相对本次修改前重新读取的本地基线整理；不把并行数值任务或更早已存在的方向脚手架计入本次新增。精确代码差异见 [changes_from_local_baseline.patch](changes_from_local_baseline.patch)，最终 SHA256 见 [implementation_fingerprint.json](implementation_fingerprint.json)。

## 本次改动

当前为 R3：相对 R2 仅 5 个 Assets 文件改变，精确前后哈希见 [R3 changed_assets_sha256.json](revision_03/changed_assets_sha256.json)。下表同时保留本任务从最初本地基线起的累计修改；R2 的 14 文件记录只用于追溯，见 [R2 changed_assets_sha256.json](revision_02/changed_assets_sha256.json)。

R2 新增 `EnemyDirectionalProfile.Parts.WingsBehindBody` 可选字段，默认false，并更新身体/腿/翼姿态。R3 只修改编辑器去阴影接入和审核逻辑，以及尾羽美术；3个运行脚本本轮均未改。BaseEnemy下述累计改动属于R1。


| 路径（相对 E:/MyTowerGame） | 用途 |
|---|---|
| `Assets/Scripts/Enemy/BaseEnemy.cs` | 配置完整时保留专用控制器；方向身体缓存原始颜色/阴影 alpha；实际白闪及致死时到期恢复；跳过近零路径点，保留原有寻路/证据代码 |
| `Assets/Scripts/Enemy/EnemyDirectionalProfile.cs` | R2增加默认false的WingsBehindBody，保持其他已有配置排序 |
| `Assets/Scripts/Enemy/EnemyDirectionalVisual.cs` | 检查 Dir 参数后再写入；缓存 MPB 白闪，无材质实例；复用清头/白闪；方向分件遮挡与可见性 |
| `Assets/Editor/EnemyDirectionPrefabBuilder.cs` | AdvancedHen 专用控制器状态机；复制动作并追加上下曲线，固定片段时长；只为本例应用新材质；未运行其他敌人的入口 |
| `Assets/Editor/AdvancedHenDirectionReview.cs`（新增及 meta） | 隔离运行演示、65 项检查与上下循环、实际 Unity 逐帧采集及自动恢复原场景 |
| `Assets/Prefabs/Enemy/Enemy_AdvancedHen.prefab` | 唯一改动的战斗 prefab：新增 DirectionVisual 分件、Profile、专用控制器与白闪材质引用 |
| `Assets/_UIAssets/Monsters/Birds/AdvancedHen/Directions/AdvancedHen_Directions.png`、`.sprites.json`（新增及 meta） | 透明 12 分件图集与可重复切片清单 |
| 同目录 `AdvancedHen_Directions.asset`（新增及 meta） | Up/Down 各六件、专用控制器引用 |
| 同目录 `AdvancedHenFlash.shader`、`.mat`（新增及 meta） | 保持 Sprite 透明混合的白闪材质，仅本例赋值 |
| 同目录 `Animations/AdvancedHen_Directions.controller`（新增及 meta） | State/Speed/Attack/Action 契约；转向不造成行走 AnyState 重入 |
| 同目录 `Animations/Ready_Directions.anim`、`Walk_Directions.anim`、`Attack_Directions.anim`、`Death_Directions.anim` | 本例原独立片段增加/修正上下专用骨骼曲线；保留原水平曲线与头部事件 |
| `Docs/EnemyDirectionReview/AdvancedHen/**` | 生图输入/输出、透明分件、真实静态/GIF/帧、验证/依赖/范围记录、复现脚本、审核进度 |

所有实际使用依赖和 GUID 随 Unity 生成的 `.meta` 一起保留。旧 `AdvancedHen_Directions.overrideController` 未作为本次控制器使用，保留原文件，不删除既有资源。

## 复用但本次未改

- `MonsterAnimEventReceiver.cs`：继续接收原水平 SetHead 事件，方向组件在同一 Animator 节点接收同一事件维护上下头。
- `MonsterPrefabBuilder.cs`：既有 `ApplyIfConfigured` 和已接入 prefab GUID 保留钩子；已通过临时源克隆重应用检查，本次未运行全量生成。
- 原始 `AdvancedHen.png`、切片 meta、源 `AdvancedHen.prefab`、共享 Rooster 控制器和动作，以及 `Enemy_AdvancedHen.prefab.meta` 均未改。
- 其余 118 个战斗 prefab 均与本次本地基线相同。已有 Monkey 方向资源属于更早工作，本次未处理。
- 资源逻辑名、MonsterCatalog/ResTable 路径、YooAsset 收集配置未改；没有改写 Luban 源表、`Assets/ConfigJson` 或 `Assets/Gen`。

## R2 审核材料

新增 revision_02 生图输入/输出、单腿重绘、离线草图（明确非运行证据）、4脚本预备差异及应用前指纹；R1完整归档和实现备份。最终交付新增上下真实循环、R1/R2对照，重新采集全部静态/转弯/动作帧并更新验证报告。

## R3相对R2

- EnemyDirectionPrefabBuilder.cs：在Apply中仅用编辑器遍历删除接入角色的Shadow节点，后续逐个接入沿用；运行期不增加工作。
- AdvancedHenDirectionReview.cs：四方向各增加无Shadow断言，复用检查替换为无阴影，合计69项。
- AdvancedHen_Directions.png：只有Up_Body新增后躯尾羽，另11片不变；切片元数据/PPU/pivot保持。
- Enemy_AdvancedHen.prefab及本例重建资源：去Shadow、更新尾羽依赖；精确实际变化列表/前后SHA256见revision_03/changed_assets_sha256.json。
- 3个Enemy运行脚本本轮均未改，其他118战斗prefab未改；原始图片/源prefab/共享Rooster不变。
- Docs新增无阴影规则、尾羽生成/打包来源、R3范围语义审计和重采审核材料，R2完整归档。
