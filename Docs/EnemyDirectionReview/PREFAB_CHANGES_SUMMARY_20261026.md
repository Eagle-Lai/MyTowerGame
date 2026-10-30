# Enemy 预制体修改汇总（2026-10-26）

## 统计口径

目标目录：E:/MyTowerGame/Assets/Prefabs/Enemy。以实际文件、Git、现有进度和用户验收记录为依据。

本次仅汇总并新增本文档，没有修改预制体、C# 或配置表，没有操作 Unity 或重新运行测试。文中的运行结果来自已有记录，不代表本次重新验证。


当前 Git HEAD：55cdec16；Unity 版本：2022.3.62f3c1。

续作进度快照：2026-10-26T08:51:00.862569+08:00。

## 总体情况

| 项目 | 数量 / 结论 |
|---|---|
| 目录内 prefab | 119 个 |
| 相对 HEAD 有未提交改动 | 67 个，均为已有 prefab 修改；已暂存 0 个 |
| 相对 HEAD 没有 prefab 改动 | 52 个；不代表历史从未修改 |
| 已绑定方向 Profile | 78 个：AdvancedHen 示例 + 首批 10 个 + 续作 67 个 |
| 续作授权队列 | 108 个 |
| 续作已完成接入，待用户美术验收 | 67 / 108 个，约 62.0% |
| 续作未完成 | 41 个：1 个资源审阅阻断、1 个参考已准备、39 个未开始 |
| 集中 GIF 清单 | 1005 个文件，包含历史和不同 revision，不能等同已验收角色数量 |

## 当前未提交修改的主要内容

1. **补全四方向外观**：66 个原本没有 DirectionVisual 的 prefab 新增 DirectionVisual/Up、DirectionVisual/Down。Monkey 返修既有方向结构。保留侧面表现，新增正面和背面的独立分件。
2. **挂接方向组件**：66 个 prefab 新增 EnemyDirectionalVisual，绑定 Profile、HorizontalRenderers、UpRenderers、DownRenderers、上下头部及身体，AxisHysteresis=1.2。Monkey 更新已有组件的绑定。
3. **切换专用动画**：66 个 prefab 的 Animator 改用角色专用 Directions Controller。Monkey 沿用 Controller GUID，但对应控制器、动画、图集和 Profile 内容均有未提交修改。
4. **重做分件布局和动作**：按角色增加或调整头、身体、前后肢、翅膀、尾巴、钳子、武器和鞍具等节点，调整位置、缩放、旋转、Sprite 引用与遮挡层级；行走、攻击、死亡曲线随结构适配。动作曲线的实际修改位于对应 Directions 资源，不全部序列化在 prefab 内。
5. **统一闪白材质**：将角色 SpriteRenderer 的内置精灵材质切换为现有 AdvancedHenFlash.mat，用于受击、致死闪白。共享路径为 Assets/_UIAssets/Monsters/Birds/AdvancedHen/Directions/AdvancedHenFlash.mat。
6. **移除地面阴影节点**：67 个改动 prefab 均由 1 个名称含 Shadow 的节点变为 0 个。此项是文件统计；本次没有运行游戏重新检查画面。
7. **修复特殊绑定**：MeatBug 修复 MonsterAnimEventReceiver.HeadRenderer 和 HeadSprites；Monkey 由旧六部件方式改为上下独立结构，旧 Wing/Leg 槽位为空由 SeparateViewRigs=1 分支接管。

### 文件差异中的业务边界

- 67 个 prefab 的原 BaseEnemy 组件序列化内容与 HEAD 一致。
- 根 Transform 的位置、旋转、缩放未发现变化；66 个根对象的组件列表变动来自新增方向组件。
- 原有 HpBar、AnchorBody、AnchorWeapon、AnchorStatus 的 GameObject 序列化块未发现变化；不将此项扩大为全部资源和运行逻辑均已重新验证。
- 当前目录没有 prefab 新增、删除或重命名；本次统计的 67 项全部是已有文件修改。

## 续作已完成的 67 个角色

下表均在当前 prefab Git 差异中，进度为 completed_pending_user_art_review，仍待用户美术验收。

| 资源分类 | 数量 | 角色 |
|---|---:|---|
| Apes | 1 | Monkey |
| Bats | 3 | DreadEye, EvilEye, MohawkBat |
| Birds | 9 | BullyRooster, Chick, Chicken, Drake, Duck, ForestTurkey, Gobbler, Goose, Hen |
| Bunnies | 3 | Bunny, DarkBunny, LittleBunny |
| Cattle | 6 | Bull, Burro, Cow, Donkey, Goat, Ox |
| Dogs | 4 | Cerberus, Husky, Nightmare, PossessedBlackBear |
| Felines | 2 | Lion, Panther |
| Giants | 6 | Butcher, Cannibal, Dreadnought, Juggernaut, Maneater, Ogre |
| Horses | 2 | Horse, Pony |
| Inanimate | 2 | Mimic, MimicChest |
| Insects | 7 | BugQueen, Caterpillar, CaveCaterpillar, Crawler, Larva, MeatBug, MossQueen |
| Mounts | 2 | BullMounted, MossQueenMounted |
| Parasites | 6 | FancyParasite, GreenParasite, IceParasite, MechanicalParasiteTypeA, MechanicalParasiteTypeB, MosquitoParasite |
| Pigs | 6 | Hog, MinerBoar, Pig, Piggy, Porky, PossessedBlackBoar |
| Rats | 7 | CaveRat, CrystalLizard, FlyingDemon, Ghost, InfectedRat, Porcupine, PossessedRat |
| Scorpions | 1 | GreenScorpion |

### 重点返修及例外

- **Monkey**：更新正背分件、尾部及控制器/动画；prefab 从 29 个 GameObject / 16 个 SpriteRenderer 调整为 47 / 23。
- **MeatBug**：原运行因侧面头部引用为空失败，角色专属修复后最终记录为 runtime_r02 与 runtime_updeath_r01。
- **Butcher**：经历多轮结构返修，最终进度列出的运行 revision 为 repair_runtime_r03 与 repair_runtime_updeath_r03；旧 repair_note 保留中间状态。
- **PossessedBlackBoar**：保留旧失败证据，最终采用 runtime_visual_r02 与 runtime_updeath_visual_r02。
- **GreenScorpion**：增加上下方向多足、双钳和分节高拱尾结构；首批 BlueScorpion 的批准不能套用到本角色。
- **Mimic / MimicChest**：按宝箱自身结构适配；MimicChest 的头部事件兼容问题有单独修复记录。

## 尚未完成的 41 个角色

| 当前情况 | 数量 | 角色 |
|---|---:|---|
| 资源审阅阻断，未安装 | 1 | PirateBoar |
| 已准备参考 | 1 | PossessedWarg，亦为 progress.current 当前角色 |
| 未开始 | 39 | PossessedWatchdog, PossessedWolf, Pug, Punisher, PurpleScarab, Ram, Rat, RatKing, RedScorpion, Rooster, RoyalBoar, SabretoothTiger, Scarab, ScarabMounted, ShardLizard, Sheep, SlugQueen, Swine, Tiger, TreasureChest, Troll, Turkey, VolcanoParasite, Warg, Wasp, Watchdog, WhiteWolf, WildGoat, WildRooster, WinterBear, WinterBoar, WinterOgre, WinterWarg, WinterWolfTypeA, WinterWolfTypeB, Wolf, WolfHound, WolfMounfed, Zombie |

PirateBoar 在 progress 中为 staged_pending_visual_check；角色 blocked_review.json 则明确标为 blocked。原因是 Down 躯干重复带有帽子、耳环，Up 躯干含耳环、后蹄仍有正面分趾；初稿还把炮管画进头片。原战斗 prefab 保留，未安装、未运行，不能算作完成。

## 已提交修改和既有用户验收

| 日期 | 提交 | 已提交内容 |
|---|---|---|
| 2026-10-17 | 51b8a979 | Monkey 上下方向接入，Controller 增加 WalkUp / WalkDown 与 Dir 参数。 |
| 2026-10-20 | 26929e0a | Monkey 四方向精灵图集改版并同步 prefab 引用。 |
| 2026-10-22 | 19e2a887 | 119 个敌人 prefab 统一渲染排序契约；渲染层调整，SortingGroup order 示例由 200 改为 300。 |
| 2026-10-23 | b576615a | 11 个 prefab 重挂方向视觉组件，包含 AdvancedHen 示例及首批 10 个角色。 |

2026-10-23 的用户批准记录覆盖：Bat, BattlePanther, Bear, BearMounted, BlackBear, BlackBoar, BlackWolf, BlueScorpion, Boar, BoarMounted。

批准范围包含 BlackBear / BlackWolf 动画返修，以及 BlueScorpion 最终背面参考尾巴修订 rear_reference_r02_centered_hook（静态角 20°、尾根固定）。AdvancedHen 是此前示例，不在 108 个续作队列内。

首批 10 个及 AdvancedHen 当前相对 HEAD 没有 prefab 未提交差异，但已经有方向方案；不可将它们计入尚未制作。

## 历史运行记录及资料入口

- 67 个完成项各保存两轮 84 PASS / 0 FAIL，最终 revision 合计 11256 PASS / 0 FAIL。此统计不包含保留的早期失败轮次。
- 这 67 个角色均为 user_approved=false。运行断言通过、内部视觉检查、用户美术批准是不同状态。
- 部分记录对实际查看媒体有明确限制，部分中文视觉备注存在编码损坏；本文没有声称所有 GIF 已在本次逐帧复核。
- 本次没有执行 Unity 编译、Play、完整关卡、长期战斗、发布包回读或设备测试。

| 资料 | 入口 |
|---|---|
| 当前总入口 | [README](README.md) |
| 续作权威进度 | [progress.json](Remaining_20261024/progress.json) |
| 首批用户验收记录 | [user_approval_20261023.json](Batch01_10/user_approval_20261023.json) |
| 集中 GIF 浏览 | [AllGIF/index.html](AllGIF/index.html) |
| GIF 清单 | [AllGIF/manifest.json](AllGIF/manifest.json) |
| PirateBoar 阻断原因 | [blocked_review.json](Remaining_20261024/PirateBoar/blocked_review.json) |

## 119 个预制体逐项状态

角色对应文件名为 Enemy_<角色>.prefab。当前改动列仅说明相对 HEAD 是否有 prefab 未提交差异。

| 序号 | 角色 | 当前阶段 | prefab 未提交改动 |
|---:|---|---|---|
| 示例 | AdvancedHen | 既有方向示例 | 否 |
| 1 | Bat | 用户已批准 | 否 |
| 2 | BattlePanther | 用户已批准 | 否 |
| 3 | Bear | 用户已批准 | 否 |
| 4 | BearMounted | 用户已批准 | 否 |
| 5 | BlackBear | 用户已批准 | 否 |
| 6 | BlackBoar | 用户已批准 | 否 |
| 7 | BlackWolf | 用户已批准 | 否 |
| 8 | BlueScorpion | 用户已批准 | 否 |
| 9 | Boar | 用户已批准 | 否 |
| 10 | BoarMounted | 用户已批准 | 否 |
| 11 | BugQueen | 实现完成，待用户美术验收 | 是 |
| 12 | Bull | 实现完成，待用户美术验收 | 是 |
| 13 | BullMounted | 实现完成，待用户美术验收 | 是 |
| 14 | BullyRooster | 实现完成，待用户美术验收 | 是 |
| 15 | Bunny | 实现完成，待用户美术验收 | 是 |
| 16 | Burro | 实现完成，待用户美术验收 | 是 |
| 17 | Butcher | 实现完成，待用户美术验收 | 是 |
| 18 | Cannibal | 实现完成，待用户美术验收 | 是 |
| 19 | Caterpillar | 实现完成，待用户美术验收 | 是 |
| 20 | CaveCaterpillar | 实现完成，待用户美术验收 | 是 |
| 21 | CaveRat | 实现完成，待用户美术验收 | 是 |
| 22 | Cerberus | 实现完成，待用户美术验收 | 是 |
| 23 | Chick | 实现完成，待用户美术验收 | 是 |
| 24 | Chicken | 实现完成，待用户美术验收 | 是 |
| 25 | Cow | 实现完成，待用户美术验收 | 是 |
| 26 | Crawler | 实现完成，待用户美术验收 | 是 |
| 27 | CrystalLizard | 实现完成，待用户美术验收 | 是 |
| 28 | DarkBunny | 实现完成，待用户美术验收 | 是 |
| 29 | Donkey | 实现完成，待用户美术验收 | 是 |
| 30 | Drake | 实现完成，待用户美术验收 | 是 |
| 31 | DreadEye | 实现完成，待用户美术验收 | 是 |
| 32 | Dreadnought | 实现完成，待用户美术验收 | 是 |
| 33 | Duck | 实现完成，待用户美术验收 | 是 |
| 34 | EvilEye | 实现完成，待用户美术验收 | 是 |
| 35 | FancyParasite | 实现完成，待用户美术验收 | 是 |
| 36 | FlyingDemon | 实现完成，待用户美术验收 | 是 |
| 37 | ForestTurkey | 实现完成，待用户美术验收 | 是 |
| 38 | Ghost | 实现完成，待用户美术验收 | 是 |
| 39 | Goat | 实现完成，待用户美术验收 | 是 |
| 40 | Gobbler | 实现完成，待用户美术验收 | 是 |
| 41 | Goose | 实现完成，待用户美术验收 | 是 |
| 42 | GreenParasite | 实现完成，待用户美术验收 | 是 |
| 43 | GreenScorpion | 实现完成，待用户美术验收 | 是 |
| 44 | Hen | 实现完成，待用户美术验收 | 是 |
| 45 | Hog | 实现完成，待用户美术验收 | 是 |
| 46 | Horse | 实现完成，待用户美术验收 | 是 |
| 47 | Husky | 实现完成，待用户美术验收 | 是 |
| 48 | IceParasite | 实现完成，待用户美术验收 | 是 |
| 49 | InfectedRat | 实现完成，待用户美术验收 | 是 |
| 50 | Juggernaut | 实现完成，待用户美术验收 | 是 |
| 51 | Larva | 实现完成，待用户美术验收 | 是 |
| 52 | Lion | 实现完成，待用户美术验收 | 是 |
| 53 | LittleBunny | 实现完成，待用户美术验收 | 是 |
| 54 | Maneater | 实现完成，待用户美术验收 | 是 |
| 55 | MeatBug | 实现完成，待用户美术验收 | 是 |
| 56 | MechanicalParasiteTypeA | 实现完成，待用户美术验收 | 是 |
| 57 | MechanicalParasiteTypeB | 实现完成，待用户美术验收 | 是 |
| 58 | Mimic | 实现完成，待用户美术验收 | 是 |
| 59 | MimicChest | 实现完成，待用户美术验收 | 是 |
| 60 | MinerBoar | 实现完成，待用户美术验收 | 是 |
| 61 | MohawkBat | 实现完成，待用户美术验收 | 是 |
| 62 | Monkey | 实现完成，待用户美术验收 | 是 |
| 63 | MosquitoParasite | 实现完成，待用户美术验收 | 是 |
| 64 | MossQueen | 实现完成，待用户美术验收 | 是 |
| 65 | MossQueenMounted | 实现完成，待用户美术验收 | 是 |
| 66 | Nightmare | 实现完成，待用户美术验收 | 是 |
| 67 | Ogre | 实现完成，待用户美术验收 | 是 |
| 68 | Ox | 实现完成，待用户美术验收 | 是 |
| 69 | Panther | 实现完成，待用户美术验收 | 是 |
| 70 | Pig | 实现完成，待用户美术验收 | 是 |
| 71 | Piggy | 实现完成，待用户美术验收 | 是 |
| 72 | PirateBoar | 资源审阅阻断，未安装 | 否 |
| 73 | Pony | 实现完成，待用户美术验收 | 是 |
| 74 | Porcupine | 实现完成，待用户美术验收 | 是 |
| 75 | Porky | 实现完成，待用户美术验收 | 是 |
| 76 | PossessedBlackBear | 实现完成，待用户美术验收 | 是 |
| 77 | PossessedBlackBoar | 实现完成，待用户美术验收 | 是 |
| 78 | PossessedRat | 实现完成，待用户美术验收 | 是 |
| 79 | PossessedWarg | 参考已准备 | 否 |
| 80 | PossessedWatchdog | 未开始 | 否 |
| 81 | PossessedWolf | 未开始 | 否 |
| 82 | Pug | 未开始 | 否 |
| 83 | Punisher | 未开始 | 否 |
| 84 | PurpleScarab | 未开始 | 否 |
| 85 | Ram | 未开始 | 否 |
| 86 | Rat | 未开始 | 否 |
| 87 | RatKing | 未开始 | 否 |
| 88 | RedScorpion | 未开始 | 否 |
| 89 | Rooster | 未开始 | 否 |
| 90 | RoyalBoar | 未开始 | 否 |
| 91 | SabretoothTiger | 未开始 | 否 |
| 92 | Scarab | 未开始 | 否 |
| 93 | ScarabMounted | 未开始 | 否 |
| 94 | ShardLizard | 未开始 | 否 |
| 95 | Sheep | 未开始 | 否 |
| 96 | SlugQueen | 未开始 | 否 |
| 97 | Swine | 未开始 | 否 |
| 98 | Tiger | 未开始 | 否 |
| 99 | TreasureChest | 未开始 | 否 |
| 100 | Troll | 未开始 | 否 |
| 101 | Turkey | 未开始 | 否 |
| 102 | VolcanoParasite | 未开始 | 否 |
| 103 | Warg | 未开始 | 否 |
| 104 | Wasp | 未开始 | 否 |
| 105 | Watchdog | 未开始 | 否 |
| 106 | WhiteWolf | 未开始 | 否 |
| 107 | WildGoat | 未开始 | 否 |
| 108 | WildRooster | 未开始 | 否 |
| 109 | WinterBear | 未开始 | 否 |
| 110 | WinterBoar | 未开始 | 否 |
| 111 | WinterOgre | 未开始 | 否 |
| 112 | WinterWarg | 未开始 | 否 |
| 113 | WinterWolfTypeA | 未开始 | 否 |
| 114 | WinterWolfTypeB | 未开始 | 否 |
| 115 | Wolf | 未开始 | 否 |
| 116 | WolfHound | 未开始 | 否 |
| 117 | WolfMounfed | 未开始 | 否 |
| 118 | Zombie | 未开始 | 否 |

本文为 2026-10-26 快照；后续以 progress.json、角色证据及新的用户验收记录为准。
