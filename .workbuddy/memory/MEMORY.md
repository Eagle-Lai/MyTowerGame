# FreedomTower 项目长期记忆

> 本文件存放**跨会话必须遵守**的项目约定与关键事实。日常流水账写 `YYYY-MM-DD.md`。

## 技术栈与工程约定

- **引擎**：Unity 2022.3.62f3c1，2D 塔防（"FreeTower"），工程根 `D:\FreedomTower_1`。
- **配置表**：Luban。源表 `Luban/Config/Datas/*.xlsx` → 导出 `Assets/Gen/*.cs` + `Assets/ConfigJson/*.json`。
  改表后必须重导：`Luban/gen_code_json.bat`（或直接调 `Luban.ClientServer.exe`，需 `DOTNET_ROLL_FORWARD=LatestMajor`）。
  **新表必须先在 `__tables__.xlsx` 登记**，否则不导出。
- **资源寻址**：`ResTable.cs` 是唯一寻址源（逻辑名 → ResAddress(bundle, assetName, editorPath)）。
  **任何新资源必须在此登记**，否则运行时"找不到资源地址"。
  盲区提醒：`check_code.py` 的逻辑名检查只扫 `ResTable.Get("字面量")`，不扫 `Configs.ConfigKeys` 字符串数组 —— 给 ConfigKeys 加表时必须同步 ResTable。
- **AssetBundle 分包**：包名常量在 `ResBundle.cs`（全小写下划线）。`Fixed` 数组决定打包范围，`Persistent` 决定开机常驻。
  新增共享资源（字体等）应单独分包，避免被隐式复制进多个包。
- **战斗架构**：无物理（无 Rigidbody/OnTriggerEnter）。`EnemyGrid` 空间哈希 + `CombatSystem` 集中 tick。
- **对象池**：`BaseBullet`/`BulletManager` 按资源名分池；`BaseManager<T>` 单例模式。
- **UI 事件**：`EventDispatcher`。`CombatSystem` 是 `UpdateEvent` 的唯一订阅者。
- **不变量**：塔"无目标绝不开火"。

## 字体与 UI（★ 重要约定）

- **全工程字体组件统一使用 TextMeshPro（TMP），禁止再新增 UGUI `UnityEngine.UI.Text`。**
- **中文字体资产**：`Assets/Font/SiYuanSongTi SDF.asset`（源思源宋体，含中文字形）。
  TMP Settings 的 `m_defaultFontAsset` 已指向它 —— 新建 TMP 文本**默认即中文可用**。
- **字体解析（编辑器）**：`EditorUtil.GetDefaultTmpFont()`（不要再加回 `GetDefaultFont`/LegacyRuntime）。
- **运行时 UI 脚本**：文本字段用 `TMP_Text`（基类即可）；节点查找用 `GetComponent<TMP_Text>()`。
  注意：`Button`/`Image`/`CanvasScaler` 仍是 `UnityEngine.UI`，对应文件仍需 `using UnityEngine.UI;`。
- **UI 预制体生成器**：`Assets/Editor/UIPrefabBuilder.cs` 的 `CreateText` 产 `TextMeshProUGUI`。
  它只管理"自己产出的节点"，跑全量重建（DeleteAsset+重建）会抹掉手工改动 ——
  日常用「补缺」，确要重建用「高级（单步重建）」。
- **Text→TMP 就地迁移工具**：`Assets/Editor/UiTmpMigrator.cs`
  （菜单：Tools ▸ 塔防 ▸ 高级（单步重建）▸ 把 UI 预制体的 Text 迁移为 TextMeshPro）。
  幂等；不动节点树，保住手工摆位。M0 一键向导步骤 8.5 会自动跑。
- **描边**：TMP 不支持 UGUI `Outline` 组件；描边走字体材质 `_OutlineWidth`/`_OutlineColor`
  （共享材质 `Assets/Font/SiYuanSongTi SDF - Outline.mat`）。
- **字体分包**：字体资产在独立 AB 包 `font`（`ResBundle.Font`），常驻加载。

## 环境限制（沙箱内做不到的事）

- **无法编译**：`MSBuild.exe` / `dotnet msbuild` / `csc.exe` 被沙箱拦截（Windows LOLBin）。
  代码正确性靠静态脚本 + 人工核对，**最终编译必须在 Unity 里做**。
- **Unity 编辑器不可直接驱动**（`Unity.exe` 路径在沙箱内不可访问）→ prefab 重建/迁移等编辑器操作
  要产出菜单工具或脚本，由用户在 Unity 里执行。
- **静态校验工具**（`.workbuddy/tools/`）：`check_code.py`（括号/重名/文件名/事件名/逻辑名）、
  `check_usings.py`（using→CS0246，含 TMPro 映射）、`check_members.py`、`check_unity_api.py`、`check_events.py`。
  改动后应全跑一遍。

## 命名口径易错点

- 塔型：`TowerType` 枚举 `Normal=1, Aoe=2, Slow=3, Pierce=4, Laser=5`。
  美术/节点/资源目录里 "**Power**"=Aoe 塔、"**Retard**"=Slow 塔 —— 这处不一致只在少数几处映射，别处不要各写一份。
- `EffectType`（塔表与子弹表共用）：`None=0, Slow=1, Dot=2, Aoe=3, Laser=4`。
- **塔分等级 prefab（三种塔统一口径）**：每种塔 3 个独立 prefab `Tower_<Type>0|1|2`（level0/1/2），
  放 `Assets/Prefabs/Tower/<Type>/`（目录名 `Normal`/`Power`/`Retard`）。
  `TowerInfo.xlsx` 的 `resName` **逐级**指向它们（不是三级同名）；`BaseTower` 升级时换实例并逐级预载。
  `TowerPrefabConverter.TowerResNames` 是自检清单（9 项），与配置 resName 必须逐行一致。
  ⚠️ 新增/替换塔美术时，这条链要**四层同步**：配置 resName → `ResTable` → 代码兜底/预载 → prefab+meta(AB 名)。
  Pierce(4)/Laser(5) 暂无独立美术，resName 占位指向 `Tower_Normal0`（详见设计文档 §Z.7.1 D-B、§Z.12）。
