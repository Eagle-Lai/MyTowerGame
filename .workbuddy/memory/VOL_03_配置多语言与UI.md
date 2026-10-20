# VOL_03 配置 / 多语言 / UI

> 本分册由 `MEMORY.md` 拆分而来，**原文一字未删**。覆盖：Luban 表与重导、多语言词条与 TextLocalizer、名字本地化、UI 生成器 UIPrefabBuilder、全量重建副作用、HUD 两按钮职责。

## 配置 / 多语言 / UI
- Luban：改任何 xlsx 必重导（菜单 3）；新表要在 `__tables__.xlsx` 登记；字段从 B 列开始；`ResTable.cs` 是唯一寻址源。
  - ★`gen_code_json.bat` 会删 `FTProject.Gen.asmdef` → CS0246，跑完要还原。
- 多语言：主键 = 英文原文。
  - ★`gen_localization_table.py` 里的 ROWS **已过期**（168 条 vs 表内 352 条），**禁止重跑**（会丢 180+ 词条）。加词条走 `.workbuddy/tools/append_localization_*.py` + 菜单 3。
  - `TextLocalizer` 的 key 留空会自动取文本；回退链：当前语言 → 英文 → 原文。菜单 308 挂载 / 309 清除。
  - 改 SettingView 的文案 → 重建 → 308 → 菜单 4。
  - ★★两态文本（MuteBtn、Btn_Pause 的 Pause⇄Continue）**不能挂 TextLocalizer**（会被刷回原文）；308 时按父节点名跳过，由 View 按状态写入 + 监听语言事件重算。
- ★名字本地化：塔名 = `TowerConfig.DisplayName`｜关卡名 = `Localization.LevelName(id)`｜怪物名 = 123 词条（`Get(name) ?? name`）。★在 `Awake` 里一次性写文案是坑（切语言不刷新）。
- UI 生成器 `UIPrefabBuilder`：改文案/布局 = 改它 + 重编译 + 重生成。
  - ★塔图标 `UI_TowerIcon_{Normal,Power,Retard}` = 96×96 透明底（`ui_hud`），改图跑 `tower_icon_bg_remove.py`。
  - ★logo = `Assets/Art/Logo/app_icon_512x512.png`（ResTable 里登记 `UI_AppLogo`）。
- ★★用 MCP 验证 UI 时严禁 instantiate 预制体的子物体（TMP 的 OnEnable 会把状态写回资产）→ 自搭 Canvas + Image。
- ★refresh/编译会触发 AB 打标 → 改写 UI prefab / .meta 的 `assetBundleName`；提交前用 `diff_ui_prefabs.py --base` 核对。
- ★★全量重建三个副作用：重排 fileID／清空 `assetBundleName`／抹掉 TextLocalizer → 必须「重建 → 308 → 菜单 4」补齐。
  - 关键尺寸：塔按钮 96×96、VolumeSlider 480×65、`TowerCodexItem` / `SelectLevelItem` 根节点 active=false。
  - ResTable 漏登记 = 真机打不开。
- ★HUD 右上两按钮职责：`Btn_Pause` = 只切暂停/继续（不弹窗，两态文本）；`Btn_Intro` = 只打开暂停菜单（不暂停，文案 `Menu`）。暂停的唯一写入口 = `GameClock.SetPaused`，`PauseView` 不写 timeScale；标题按 `IsPaused` 取词。
