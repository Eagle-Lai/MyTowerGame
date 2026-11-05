# Localization Repair Follow-up

Date: 2026-11-05  
Project: `E:/MyTowerGame`  
Unity: `2022.3.62f3c1`  
MCP: `unityMCP`, instance `MyTowerGame@9e28c50b510eeb91`

## Changes

Added the six missing keys from the audit to `Luban/Config/Datas/Localization.xlsx`, rows 386-391. The 377 original records and the five pre-existing blank-key rows (24-26 and 159-160) were preserved. The resulting localization table has 383 unique keys.

| Key | English | Simplified Chinese | Traditional Chinese |
|---|---|---|---|
| `Combat {0} · Level {1}` | `Combat {0} · Level {1}` | `战斗 {0} · 整局 {1}` | `戰鬥 {0} · 整局 {1}` |
| `Boss leaks {0}` | `Boss leaks {0}` | `首领漏怪 {0}` | `首領漏怪 {0}` |
| `Best stars: {0}/5` | `Best stars: {0}/5` | `历史最佳：{0}/5` | `歷史最佳：{0}/5` |
| `Not cleared` | `Not cleared` | `未通关` | `未通關` |
| `Best clear: {0}` | `Best clear: {0}` | `最佳整关用时：{0}` | `最佳整關用時：{0}` |
| `Clearing a level awards five stars until the rating rules are rebuilt` | `Clearing a level awards five stars until the rating rules are rebuilt` | `评分规则重建前，通关即记 5 星` | `評分規則重建前，通關即記 5 星` |

Luban export completed with exit code 0 (`== succ ==`) and regenerated `Assets/ConfigJson/tblocalization.json`. The export emitted an unrelated unknown-tag notice for `Global.xlsx`; Unity subsequently loaded all configuration tables successfully. The exporter also removed the existing `Assets/Gen/FTProject.Gen.asmdef`; Unity MCP exposed the resulting missing `FTProject.Gen.dll` compile error. The original tracked assembly definition content was restored before the final refresh. Final compilation succeeded.

## Runtime Localization

Unity MCP loaded `tblocalization.json` as a `TextAsset`, constructed `cfg.TBLocalization` and the project `LocalizationLookup`, then called `Localization.Get` for every repaired key in all three languages. Formatted calls used sample values `00:15`, `01:23`, `2`, `3`, and `04:56`. All 18 key-language results matched the expected text and retained the correct placeholders. The full per-check output is in [repair-runtime-checks.csv](evidence/repair-runtime-checks.csv).

The follow-up TMP test loaded the actual `LevelClearView`, `LevelDetailView`, and `SelectLevelItem` prefab contents in Unity. It assigned the corresponding `Localization.Get` output, applied each configured language font through `LanguageManager.ApplyFont`, called `ForceMeshUpdate`, checked font identity, atlas dimensions, glyph coverage, and `TMP_Text.isTextOverflowing`. Across 21 rendered prefab-node checks, all configured fonts matched, missing glyphs were 0, and overflow was 0. Per-language text and node measurements are in [repair-tmp-layout-checks.csv](evidence/repair-tmp-layout-checks.csv).

## TMP Font Repair

The first post-translation TMP render check found three missing Traditional Chinese glyphs in the combined `LevelDetailView/Panel/RatingTarget` text: `規`, `則`, and `記`. Unity MCP confirmed that `TacticalSans` is a dynamic TMP font asset using `NotoSansCJKsc-Regular.otf`, and that the source font contains all three characters. `TMP_FontAsset.TryAddCharacters("規則記", out missing, false)` succeeded with no remaining missing characters; the font asset was saved through the Unity Editor.

After refresh and reload, Unity MCP confirmed all three characters are present. `TacticalSans` remains a single 2048x2048 atlas; its character table increased from 838 to 841 entries and its glyph table from 837 to 840. English, Simplified Chinese, and Traditional Chinese still reference the same valid `TacticalSans` asset. The final 21 TMP checks reported no missing glyphs or overflowing text.

## Unity Verification

| Check | Verification | Result |
|---|---|---|
| Project identity | Re-read `custom-tools`, `instances`, selected the full instance ID, then read `project/info` | Root `E:/MyTowerGame`, Unity `2022.3.62f3c1`, Android target |
| Luban configuration load | Entered Play Mode and read `[Config]` from Unity Console | `配置加载完成`; `TBLocalization: 383` and all other configured tables had nonzero expected row counts; no failed-table list |
| Compilation | Read editor state and executed `EditorUtility.scriptCompilationFailed` after final forced refresh | `is_compiling=false`, `is_domain_reload_pending=false`, `scriptCompilationFailed=false` |
| Console | Unity MCP `read_console(action="get", types=["error"])` after final refresh and Play Mode exit | 0 Error entries |
| Editor state | Read `mcpforunity://editor/state` after final refresh | Play Mode false; active scene `Assets/Scenes/Boot.unity`; scene not dirty; resources ready |
| Localization runtime | Runtime query results in `repair-runtime-checks.csv` | 18/18 exact matches; 383 unique lookup entries |
| TMP rendering | Actual prefab TMP checks in `repair-tmp-layout-checks.csv` | 21 checks; font mismatch 0; missing glyphs 0; overflow 0 |

The original full audit remains at [report.md](report.md). This follow-up records the repair, the initial font finding, and the post-repair Unity evidence without overwriting the original audit results.
