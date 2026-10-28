# 设计验收记录

成果目录：D:/FishTestGame/Docs/UI_Redesign/2026-10-26

本表区分设计文件覆盖与产品/真机验收。**设计文件已交付；真实状态和设备验收仍待确认，不宣称整项产品验收通过。** 条件示意并非实际成绩，规划页在清单和图册中标记。

## 24项范围对应

| Prompt项 | 内容 | 画面ID | 结果 |
|---|---|---|---|
| 1 | SplashView | 01_splash | 通过：独立画面与线框覆盖；真实状态待复核 |
| 2 | LoadingView | 02_loading_reading、02_loading_failed | 通过：独立画面与线框覆盖；真实状态待复核 |
| 3 | HotUpdateView | 03_update_checking、03_update_download、03_update_validating、03_update_complete、03_update_paused、03_update_resuming、03_update_retry、03_update_failed | 通过：独立画面与线框覆盖；真实状态待复核 |
| 4 | MainMenuView | 04_menu_new、04_menu_continue | 通过：独立画面与线框覆盖；真实状态待复核 |
| 5 | SelectView | 05_select_all | 通过：独立画面与线框覆盖；真实状态待复核 |
| 6 | SelectLevelItem | 06_item_normal、06_item_selected、06_item_complete、06_item_locked、06_item_continue、06_item_history、06_item_record | 通过：独立画面与线框覆盖；真实状态待复核 |
| 7 | LevelDetailView | 07_detail_challenge、07_detail_continue、07_detail_restart | 通过：独立画面与线框覆盖；真实状态待复核 |
| 8 | GameIntroView | 08_intro | 通过：独立画面与线框覆盖；真实状态待复核 |
| 9 | HudView备战 | 09_hud_prepare | 通过：独立画面与线框覆盖；真实状态待复核 |
| 10 | HudView战斗 | 09_hud_combat | 通过：独立画面与线框覆盖；真实状态待复核 |
| 11 | HudView建造 | 09_hud_build、09_hud_drag、09_hud_invalidpath、09_hud_occupied、09_hud_entry、09_hud_poor、09_hud_built、09_hud_cancel | 通过：独立画面与线框覆盖；真实状态待复核 |
| 12 | HudView选中塔 | 09_hud_selected、09_hud_hide_range | 通过：独立画面与线框覆盖；真实状态待复核 |
| 13 | TowerInfoView | 10_tower_normal_l1、10_tower_normal_l2、10_tower_normal_l3、10_tower_power_l1、10_tower_power_l2、10_tower_power_l3、10_tower_retard_l1、10_tower_retard_l2、10_tower_retard_l3、10_tower_normal_poor、10_tower_power_poor、10_tower_retard_poor | 通过：独立画面与线框覆盖；真实状态待复核 |
| 14 | PauseView | 11_pause | 通过：独立画面与线框覆盖；真实状态待复核 |
| 15 | TipsView | 12_tip_success、12_tip_warning、12_tip_failure | 通过：独立画面与线框覆盖；真实状态待复核 |
| 16 | TowerCodex | 13_codex_normal、13_codex_power、13_codex_retard、13_codex_compare | 通过：独立画面与线框覆盖；真实状态待复核 |
| 17 | MonsterCodex | 14_monster_grid、14_monster_detail、14_monster_empty | 通过：独立画面与线框覆盖；真实状态待复核 |
| 18 | SellConfirm | 15_sell、15_sell_pending | 通过：独立画面与线框覆盖；真实状态待复核 |
| 19 | ConfirmView | 16_confirm_reset、16_confirm_resetpending、16_confirm_resetfailed、16_confirm_leave、16_confirm_restart、16_confirm_quit、16_confirm_unsaved、17_settings_zh-Hans、17_settings_zh-Hant、17_settings_en | 通过：独立画面与线框覆盖；真实状态待复核 |
| 20 | 胜利结算 | 18_result_win、18_result_record、18_result_low、18_result_saved | 通过：独立画面与线框覆盖；真实状态待复核 |
| 21 | 失败结算 | 18_result_lose | 通过：独立画面与线框覆盖；真实状态待复核 |
| 22 | 保存中与失败 | 16_confirm_unsaved、18_result_saving、18_result_savefailed、18_result_retry | 通过：独立画面与线框覆盖；真实状态待复核 |
| 23 | 末关完成 | 18_result_final | 通过：独立画面与线框覆盖；真实状态待复核 |
| 24 | 通用状态 | 03_update_failed、06_item_locked、09_hud_poor、16_confirm_resetpending、19_common_empty、19_common_unavailable、19_common_confirming | 通过：独立画面与线框覆盖；真实状态待复核 |

## 分项检查

| 检查项 | 结果 | 证据及实际问题 |
|---|---|---|
| 独立页面与关键状态 | 通过（文件覆盖） | 85项基础稿和85项线框，详见page-inventory.md |
| 方向探索与统一系统 | 通过（设计稿） | system/03_directions和01_design-system：一致的颜色角色、切角及主次按钮 |
| 逐页目标与动作 | 通过（规格） | page-ux.md逐项列目标、信息、主次动作、返回与状态变化 |
| 三语言文件 | 通过（覆盖） | 85简中、85繁中、85英文；翻译映射无缺失 |
| 已检查文字几何 | 通过（有限检查） | language-layout-report.json：170稿、0项已检查画布/居中按钮越界；11个英文按钮保持字号换行 |
| 所有相邻控件碰撞 | 需要继续确认 | 边界报告不能推出全局零重叠。已修正窄屏标签、操作条缺项、结算星级冲突；仍需真实数据全状态巡检 |
| 四类页面四种比例 | 通过（文件） | 4类×4比例=16稿，另4张安全区压力稿；重排而非全屏等比缩放 |
| 窄屏关键操作 | 通过（已查看稿） | 1024 HUD含升级、出售、范围、速度、下一波、暂停；关卡导航完整 |
| 保存中/失败/已保存 | 通过（设计语义） | 保存中移除直接返回；失败明确尚未保存，只留安全重试；下一关在保存后 |
| 末关与失败去向 | 通过（设计稿） | 末关只有有效返回/重玩；失败用标题和危险形状表达 |
| 无声及三塔定位 | 通过（内容） | 无音量/音乐/音效项；速射单体、火力范围、减速控制 |
| 颜色对比 | 通过（令牌数值）/设备待确认 | contrast-report.json；重要文字不用结构线色。纹理背景、眩光和低亮度仍需设备检查 |
| 触控尺寸和间距 | 需要真机确认 | 设计px不证明48dp；缺目标机密度、安全区和实际热区映射 |
| 较大文字 | 需要确认 | 有代表板；没有全页面大字变体，也不证明运行版具备字号设置 |
| 繁中/英文正式文案 | 需要本地化确认 | 几何已检查；地区用语、动态插值最大长度尚未以真实配置审校 |
| 实际数值/星数/纪录 | 需要真实数据 | 未读存档/数值表，用—占位；实际星级填充、新纪录、具体低星原因未认证 |
| 真实地图/敌人威胁 | 需要真实数据 | 地图为构图示意；未假称某形象属于01关编组，没有虚构抗性或故事 |
| 双输入建造/倍速 | 需要运行确认 | 点选和拖动有文档依据，实际支持程度及非×1档位待产品核对 |
| Android安全区/低亮度/密集战斗 | 需要真机确认 | 无APK或设备实测；96/96/24/36是设计压力值 |
| 品牌提案 | 需要产品确认 | 六边盾塔标记及Freedom Tower译名未视作已采纳 |
| 游戏工程边界 | 通过（本轮操作） | 仅写设计目录和外部制图目录；未修改游戏代码、场景、Prefab、配置、源资产 |
| 全局导航与风险 | 通过（规格） | navigation-detail.md补齐返回、确认来源、错误重试和末关去向 |

## 本次具体修正

1. 窄屏选关编号和状态改为左右对齐，全部有效关卡完整可见。
2. 1024/1280 HUD补回出售及速度，属性和底部塔栏独立。
3. 结算星级与标题分离，末关、失败和未保存独立表达。
4. 保存处理中移除绕过返回；未保存只留结算/重试，不假设可丢弃成绩。
5. 玩家文案移除“完成前不发布新纪录”等内部措辞。
6. 英文长按钮保持字号拆行，不统一缩小。

## 交接判定

可进入内部视觉与UX评审，不能作为运行功能、数值或Android真机验收证明。待确认项集中于真实数据、现有能力、地区文案及设备；后续补入真实信息复核，不补造测试值。
