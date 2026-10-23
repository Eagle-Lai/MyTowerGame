# -*- coding: utf-8 -*-
# 一次性脚本：生成 Luban 多语言表 Localization.xlsx。
# 跑完即可删除。生成后必须走 Unity 菜单「3.导出配置表」产出 json + C#。
import zipfile, shutil, os

DATAS = r'D:/FreedomTower_1/Luban/Config/Datas'
NS = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'

# ---------------- 多语言表数据 ----------------
# 列：id(=英文原文), en, zh-Hans, zh-Hant, comment
# ★ 需求 2 起：id 就是英文原文本身（id == en），英文原文即查找键。
ROWS = [
    ('Start', 'Start', '开始', '開始', 'HUD 开始按钮'),
    ('In Progress', 'In Progress', '进行中', '進行中', '回合进行中'),
    ('Next Round', 'Next Round', '下一回合', '下一回合', '进入下一回合'),
    ('Round {0}', 'Round {0}', '回合 {0}', '回合 {0}', '占位符 {0} 保留'),
    ('Wave {0}', 'Wave {0}', '第 {0} 波', '第 {0} 波', '占位符 {0} 保留'),
    ('Round {0} Clear', 'Round {0} Clear', '回合 {0} 完成', '回合 {0} 完成', '占位符 {0} 保留'),
    ('Cleared', 'Cleared', '已通关', '已通關', '关卡胜利状态'),
    ('Failed', 'Failed', '已失败', '已失敗', '关卡失败状态'),
    ('Gold {0}', 'Gold {0}', '金币 {0}', '金幣 {0}', '占位符 {0} 保留'),
    ('HP {0}/{1}', 'HP {0}/{1}', '生命 {0}/{1}', '生命 {0}/{1}', '占位符保留'),
    ('FREEDOM TOWER', 'FREEDOM TOWER', '自由人塔防', '自由人塔防', '主菜单标题'),
    ('Cleared {0}/{1}', 'Cleared {0}/{1}', '已通关 {0}/{1}', '已通關 {0}/{1}', '占位符保留'),
    ('Start Game', 'Start Game', '开始游戏', '開始遊戲', '主菜单开始'),
    ('Quit Game', 'Quit Game', '退出游戏', '結束遊戲', ''),
    ('Are you sure you want to quit?', 'Are you sure you want to quit?', '确定要退出游戏吗？', '確定要結束遊戲嗎？', ''),
    ('Quit', 'Quit', '退出', '結束', ''),
    ('Cancel', 'Cancel', '取消', '取消', ''),
    ('Starting...', 'Starting...', '正在启动...', '正在啟動...', '开屏状态'),
    ('Game Paused', 'Game Paused', '暂停', '暫停', '暂停界面标题'),
    ('Settings', 'Settings', '设置', '設定', '设置界面标题'),
    ('Reset Save', 'Reset Save', '重置存档', '重置存檔', ''),
    ('This will erase all progress. Continue?', 'This will erase all progress. Continue?', '将清空全部进度，确定吗？', '將清空全部進度，確定嗎？', ''),
    ('Save reset', 'Save reset', '存档已重置', '存檔已重置', 'Tips 提示'),
    ('Language', 'Language', '语言', '語言', '语言设置项标签'),
    ('OK', 'OK', '确定', '確定', '通用确认'),
    ('Level Clear!', 'Level Clear!', '通关完成！', '通關完成！', '结算标题'),
    ('Defense Failed', 'Defense Failed', '防御失败', '防禦失敗', '结算标题'),
    ('Level {0}', 'Level {0}', '关卡 {0}', '關卡 {0}', '占位符 {0} 保留'),
    ('This {0}    Best {1}', 'This {0}    Best {1}', '本次 {0}　　历史最高 {1}', '本次 {0}　　歷史最高 {1}', '占位符保留'),
    ('★ New Record! Best stars improved', '★ New Record! Best stars improved', '★ 新纪录！刷新了本关最高星级', '★ 新紀錄！刷新了本關最高星級', ''),
    ('HP {0}/{1}    Kills {2}    Leaks {3}', 'HP {0}/{1}    Kills {2}    Leaks {3}', '剩余生命 {0}/{1}　　击杀 {2}　　漏怪 {3}', '剩餘生命 {0}/{1}　　擊殺 {2}　　漏怪 {3}', '占位符保留'),
    ('Next Level', 'Next Level', '下一关', '下一關', ''),
    ('Next: {0}', 'Next: {0}', '下一关：{0}', '下一關：{0}', '占位符 {0} 保留'),
    ('Final Level', 'Final Level', '已是最后一关', '已是最後一關', ''),
    ('Replay', 'Replay', '重玩本关', '重玩本關', ''),
    ('Try Again', 'Try Again', '重新挑战', '重新挑戰', ''),
    ('Back to Levels', 'Back to Levels', '返回关卡选择', '返回關卡選擇', ''),
    ('Level {0} Detail', 'Level {0} Detail', '第 {0} 关', '第 {0} 關', '占位符 {0} 保留'),
    ('Best {0} Star', 'Best {0} Star', '历史最佳 {0} 星', '歷史最佳 {0} 星', '占位符保留'),
    ('Not cleared yet', 'Not cleared yet', '尚未通关', '尚未通關', ''),
    ('Rounds    {0}', 'Rounds    {0}', '回合数　{0}', '回合數　{0}', '占位符 {0} 保留'),
    ('Waves     {0}', 'Waves     {0}', '波次　　{0}', '波次　　{0}', '占位符 {0} 保留'),
    ('Start Gold {0}', 'Start Gold {0}', '初始金币　{0}', '初始金幣　{0}', '占位符 {0} 保留'),
    ('Start HP   {0}', 'Start HP   {0}', '初始生命　{0}', '初始生命　{0}', '占位符 {0} 保留'),
    ('Difficulty {0}', 'Difficulty {0}', '难度　　{0}', '難度　　{0}', '占位符 {0} 保留'),
    ('Best Time {0}', 'Best Time {0}', '最佳用时　{0}', '最佳用時　{0}', '占位符 {0} 保留'),
    ('Enemies in this level', 'Enemies in this level', '本关出现怪物', '本關出現怪物', ''),
    ('    {0} kinds', '    {0} kinds', '　等 {0} 种', '　等 {0} 種', '占位符 {0} 保留'),
    ('Start Challenge', 'Start Challenge', '开始挑战', '開始挑戰', ''),
    ('Challenge Again', 'Challenge Again', '再次挑战', '再次挑戰', ''),
    ('Back', 'Back', '返回', '返回', ''),
    ('Restart', 'Restart', '从头重打', '從頭重打', ''),
    ('Tower Panel', 'Tower Panel', '防御塔', '防禦塔', '塔信息面板标题'),
    ('ATK {0}  RNG {1}  SPD {2}s  DPS {3}', 'ATK {0}  RNG {1}  SPD {2}s  DPS {3}', '攻击 {0} 射程 {1} 格 攻速 {2}s DPS {3}', '攻擊 {0} 射程 {1} 格 攻速 {2}s DPS {3}', '占位符保留'),
    ('MAX', 'MAX', '已满级', '已滿級', ''),
    ('Upgrade ({0})', 'Upgrade ({0})', '升级 ({0})', '升級 ({0})', '占位符 {0} 保留'),
    ('No Next Level', 'No Next Level', '无下一级', '無下一級', ''),
    ('Sell (+{0})', 'Sell (+{0})', '出售 (+{0})', '出售 (+{0})', '占位符 {0} 保留'),
    ('Tower {0}', 'Tower {0}', '塔 {0}', '塔 {0}', '占位符 {0} 保留'),
    ('Damage   {0}', 'Damage   {0}', '伤害　{0}', '傷害　{0}', '占位符 {0} 保留'),
    ('Range    {0:F1}', 'Range    {0:F1}', '射程　{0:F1} 格', '射程　{0:F1} 格', '占位符保留'),
    ('Speed    {0:F2}', 'Speed    {0:F2}', '攻速　{0:F2} 秒', '攻速　{0:F2} 秒', '占位符保留'),
    ('Cost     {0}', 'Cost     {0}', '造价　{0} 金币', '造價　{0} 金幣', '占位符 {0} 保留'),
    ('Single-target rapid fire', 'Single-target rapid fire', '单体速射 · 性价比基准', '單體速射 · 性價比基準', '普通塔定位'),
    ('Area blast · swarm clearer', 'Area blast · swarm clearer', '范围爆炸 · 清群核心', '範圍爆炸 · 清群核心', '范围塔定位'),
    ('Slows enemies · control', 'Slows enemies · control', '减速控制 · 拖住节奏', '減速控制 · 拖住節奏', '减速塔定位'),
    # 【2026-10-14 三塔型收敛】原 Pierces a line of enemies / Hitscan burst · anti-boss
    # 两条塔型定位文案随穿透塔/激光塔删除。
    ('Normal Tower', 'Normal Tower', '普通塔', '普通塔', ''),
    ('Blast Tower', 'Blast Tower', '范围塔', '範圍塔', ''),
    ('Frost Tower', 'Frost Tower', '减速塔', '減速塔', ''),
    # 【2026-10-14 三塔型收敛】原 Pierce Tower / Laser Tower 词条随塔型删除。
    ('Sell Tower', 'Sell Tower', '出售确认', '出售確認', ''),
    ('Refund {0}% of total investment.\nThis cannot be undone.', 'Refund {0}% of total investment.\nThis cannot be undone.', '出售后将退回 {0}% 的累计投入\n且无法撤销', '出售後將退回 {0}% 的累計投入\n且無法撤銷', '占位符 {0} 保留'),
    ('Tower', 'Tower', '塔', '塔', ''),
    ('You can build on any open ground; paths recompute in real time.', 'You can build on any open ground; paths recompute in real time.', '可以在任意空地建塔，路径会实时重算', '可以在任意空地建塔，路徑會即時重算', ''),
    ('Towers never waste fire when they have no target.', 'Towers never waste fire when they have no target.', '塔没有目标时绝不会浪费火力', '塔沒有目標時絕不會浪費火力', ''),
    ('Selling a tower refunds part of its total investment.', 'Selling a tower refunds part of its total investment.', '出售塔可以退回一部分累计投入', '出售塔可以退回一部分累計投入', ''),
    ('Slow towers greatly boost the damage of all nearby towers.', 'Slow towers greatly boost the damage of all nearby towers.', '减速塔能大幅提升周围所有塔的输出', '減速塔能大幅提升周圍所有塔的輸出', ''),
    ('Flying enemies ignore ground paths; watch your anti-air coverage.', 'Flying enemies ignore ground paths; watch your anti-air coverage.', '飞行怪会无视地面路径，注意覆盖对空', '飛行怪會無視地面路徑，注意覆蓋對空', ''),
    ('There is build time between rounds, but you can start early.', 'There is build time between rounds, but you can start early.', '回合之间有布防时间，也可以立即开始', '回合之間有佈防時間，也可以立即開始', ''),
    # 【2026-10-14 三塔型收敛】原"穿透塔能一次打穿一整列敌人"加载提示随穿透塔删除。
    ('Initializing resources...', 'Initializing resources...', '正在初始化资源系统...', '正在初始化資源系統...', ''),
    ('Resource Update', 'Resource Update', '资源更新', '資源更新', ''),
    ('Checking for updates...', 'Checking for updates...', '正在检查更新...', '正在檢查更新...', ''),
    ('Comparing resource versions...', 'Comparing resource versions...', '正在比对资源版本...', '正在比對資源版本...', ''),
    ('Loading resource manifest...', 'Loading resource manifest...', '正在加载资源清单...', '正在載入資源清單...', ''),
    ('Resources are up to date', 'Resources are up to date', '资源已是最新', '資源已是最新', ''),
    ('Current mode: no resource update needed', 'Current mode: no resource update needed', '当前模式：无需更新资源', '當前模式：無需更新資源', ''),
    ('Editor mode: no resource update needed', 'Editor mode: no resource update needed', '编辑器模式：无需更新资源', '編輯器模式：無需更新資源', ''),
    ('Downloading resources...', 'Downloading resources...', '正在下载资源...', '正在下載資源...', ''),
    ('Downloaded {0:F1} MB / {1:F1} MB', 'Downloaded {0:F1} MB / {1:F1} MB', '已下载 {0:F1} MB / {1:F1} MB', '已下載 {0:F1} MB / {1:F1} MB', '占位符保留'),
    ('Speed {0:F1} MB/s   ETA {1}', 'Speed {0:F1} MB/s   ETA {1}', '速度 {0:F1} MB/s　剩余约 {1}', '速度 {0:F1} MB/s　剩餘約 {1}', '占位符保留'),
    ('Files {0}/{1}   Failed 0', 'Files {0}/{1}   Failed 0', '文件 {0}/{1}　失败 0', '檔案 {0}/{1}　失敗 0', '占位符保留'),
    ('Download failed', 'Download failed', '下载失败', '下載失敗', ''),
    ('Download failed: {0}', 'Download failed: {0}', '下载失败：{0}', '下載失敗：{0}', '占位符 {0} 保留'),
    ('Update complete', 'Update complete', '更新完成', '更新完成', ''),
    ('Paused', 'Paused', '已暂停', '已暫停', ''),
    ('Retry', 'Retry', '重试', '重試', ''),
    ('Continue', 'Continue', '继续', '繼續', ''),
    ('Clear the previous level first', 'Clear the previous level first', '先通关上一关才能解锁', '先通關上一關才能解鎖', ''),
    ('Not enough gold', 'Not enough gold', '金币不足', '金幣不足', ''),
    ('Cannot Build Here', 'Cannot Build Here', '此处无法建塔', '此處無法建塔', ''),
    ('Sell is unavailable here', 'Sell is unavailable here', '出售确认界面不可用', '出售確認介面不可用', ''),
    ('Next Round ({0})', 'Next Round ({0})', '下一回合({0})', '下一回合({0})', '占位符 {0} 保留'),
    ('Select Level', 'Select Level', '选择关卡', '選擇關卡', '选关界面标题'),
    ('Cleared <color=#E8F0FA>{0}/{1}</color>　<color=#FFC94D>★ {2}/{3}</color>', 'Cleared <color=#E8F0FA>{0}/{1}</color>　<color=#FFC94D>★ {2}/{3}</color>', '已通关 <color=#E8F0FA>{0}/{1}</color>　<color=#FFC94D>★ {2}/{3}</color>', '已通關 <color=#E8F0FA>{0}/{1}</color>　<color=#FFC94D>★ {2}/{3}</color>', '富文本模板，占位符保留'),
    ('Locked', 'Locked', '未解锁', '未解鎖', ''),
    ('Difficulty I', 'Difficulty I', '难度 Ⅰ', '難度 Ⅰ', '罗马数字保留'),
    ('Difficulty II', 'Difficulty II', '难度 Ⅱ', '難度 Ⅱ', '罗马数字保留'),
    ('Difficulty III', 'Difficulty III', '难度 Ⅲ', '難度 Ⅲ', '罗马数字保留'),
    ('Not Buildable Here', 'Not Buildable Here', '该位置不可建造', '該位置不可建造', ''),
    ('Tower already there', 'Tower already there', '该位置已有防御塔', '該位置已有防禦塔', ''),
    ('Cannot fully block the path', 'Cannot fully block the path', '不能完全阻断怪物路径', '不能完全阻斷怪物路徑', ''),
    ('Not enough gold, need {0}', 'Not enough gold, need {0}', '金币不足，需要 {0}', '金幣不足，需要 {0}', '占位符 {0} 保留'),
    ('{0}: move to a buildable tile and click to place, right-click/ESC to cancel', '{0}: move to a buildable tile and click to place, right-click/ESC to cancel', '{0}：移动到可建造格上点击放置，右键/ESC 取消', '{0}：移動到可建造格上點擊放置，右鍵/ESC 取消', '占位符 {0} 保留'),
    ('No tower config for type={0} level={1}', 'No tower config for type={0} level={1}', '找不到 type={0} level={1} 的塔配置', '找不到 type={0} level={1} 的塔配置', '占位符保留'),
    ('No Tile Here', 'No Tile Here', '该位置无法建造', '該位置無法建造', ''),
    ('An enemy is on this tile, try another spot', 'An enemy is on this tile, try another spot', '该格上正有怪物，换个位置吧', '該格上正有怪物，換個位置吧', ''),
    ('Failed to load tower asset', 'Failed to load tower asset', '防御塔资源加载失败', '防禦塔資源載入失敗', ''),
    ('Tower is already at max level', 'Tower is already at max level', '该防御塔已满级', '該防禦塔已滿級', ''),
    ('No next-level config available', 'No next-level config available', '该防御塔暂无可升级的下一级配置', '該防禦塔暫無可升級的下一級配置', ''),
    ('Tower is not on a tile, cannot upgrade', 'Tower is not on a tile, cannot upgrade', '该防御塔不在格子上，无法升级', '該防禦塔不在格子上，無法升級', ''),
    ('Not enough gold, upgrade needs {0}', 'Not enough gold, upgrade needs {0}', '金币不足，升级需要 {0}', '金幣不足，升級需要 {0}', '占位符 {0} 保留'),
    ('Upgrade failed: tower asset missing, gold refunded', 'Upgrade failed: tower asset missing, gold refunded', '升级失败：防御塔资源加载失败，已退还金币', '升級失敗：防禦塔資源載入失敗，已退還金幣', ''),
    ('Upgraded to {0} Lv.{1}', 'Upgraded to {0} Lv.{1}', '已升级为 {0} Lv.{1}', '已升級為 {0} Lv.{1}', '占位符保留'),
    ('Tower sold, refunded {0} gold', 'Tower sold, refunded {0} gold', '已出售防御塔，返还 {0} 金币', '已出售防禦塔，返還 {0} 金幣', '占位符 {0} 保留'),
    ('<color=#9FB3C8>Best</color> {0}', '<color=#9FB3C8>Best</color> {0}', '<color=#9FB3C8>历史最高</color> {0}', '<color=#9FB3C8>歷史最高</color> {0}', '富文本模板，占位符保留'),
    ('Config load failed, see Console', 'Config load failed, see Console', '配置表加载失败，请查看 Console', '配置表載入失敗，請查看 Console', ''),
    ('Monster codex: UI not ready yet', 'Monster codex: UI not ready yet', '怪物图鉴：界面生成中', '怪物圖鑑：介面生成中', ''),
    ('Level config incomplete', 'Level config incomplete', '关卡配置不完整', '關卡配置不完整', ''),
    ('Level ready: {0}, click Start to fight', 'Level ready: {0}, click Start to fight', '关卡就绪：{0}，点击「开始」迎战', '關卡就緒：{0}，點擊「開始」迎戰', '占位符 {0} 保留'),
    ('Round in progress, wait for it to finish', 'Round in progress, wait for it to finish', '回合进行中，请等待本回合结束', '回合進行中，請等待本回合結束', ''),
    ('Game already ended', 'Game already ended', '本局已结束', '本局已結束', ''),
    ('Round {0} config missing', 'Round {0} config missing', '回合 {0} 配置缺失', '回合 {0} 配置缺失', '占位符 {0} 保留'),
    ('Round {0}/{1} start', 'Round {0}/{1} start', '回合 {0}/{1} 开始', '回合 {0}/{1} 開始', '占位符保留'),
    ('Round reward +{0} gold', 'Round reward +{0} gold', '回合奖励 +{0} 金币', '回合獎勵 +{0} 金幣', '占位符 {0} 保留'),
    ('Cleared! Earned {0}', 'Cleared! Earned {0}', '通关！获得 {0}', '通關！獲得 {0}', '占位符 {0} 保留'),
    ('Round complete, next round starts in {0}s (or tap Next Round)', 'Round complete, next round starts in {0}s (or tap Next Round)', '回合完成，{0} 秒后自动开始下一回合（也可直接点「下一回合」）', '回合完成，{0} 秒後自動開始下一回合（也可直接點「下一回合」）', '占位符 {0} 保留'),
    ('Congratulations!', 'Congratulations!', '恭喜通关！', '恭喜通關！', ''),
    ('Defense failed...', 'Defense failed...', '防御失败……', '防禦失敗……', ''),
    ('Resumed from last progress (next round: {0})', 'Resumed from last progress (next round: {0})', '已从上次进度继续（下一回合：第 {0} 回合）', '已從上次進度繼續（下一回合：第 {0} 回合）', '占位符 {0} 保留'),
    ('Entering level {0}...', 'Entering level {0}...', '正在进入第 {0} 关...', '正在進入第 {0} 關...', '占位符 {0} 保留'),
    ('Tower panel not ready, cannot upgrade/sell yet', 'Tower panel not ready, cannot upgrade/sell yet', '塔操作面板资源未就绪，暂无法升级/出售（补齐 TowerInfoView 后可用）', '塔操作面板資源未就緒，暫無法升級/出售（補齊 TowerInfoView 後可用）', ''),
    ('Resource init failed, see Console', 'Resource init failed, see Console', '资源系统初始化失败，请查看 Console', '資源系統初始化失敗，請查看 Console', ''),
    ('Loading config...', 'Loading config...', '正在加载配置表...', '正在載入配置表...', ''),
    ('Preparing level data...', 'Preparing level data...', '正在准备关卡数据...', '正在準備關卡資料...', ''),
    ('Ready', 'Ready', '准备完成', '準備完成', ''),

    # ---------------- prefab 静态文案补录（需求 1/3 挂 TextLocalizer 后核出的缺口） ----------------
    # ★ 这些文案出现在 prefab 的静态文本节点上（挂了 TextLocalizer，key=英文原文）。
    #   补齐后切语言才会真正生效；缺失则走"回退原英文"（不崩，但语言不变）。
    ('Confirm', 'Confirm', '确认', '確認', '通用确认标题'),
    ('Confirm Sell', 'Confirm Sell', '确认出售', '確認出售', '出售确认按钮'),
    ('Sell this tower?', 'Sell this tower?', '确认出售？', '確認出售？', '出售确认标题'),
    ('Refund', 'Refund', '退回金币', '退回金幣', '出售确认退回标签'),
    ('Close', 'Close', '关闭', '關閉', '通用关闭按钮'),
    ('Sell', 'Sell', '出售', '出售', '塔面板出售按钮'),
    ('Upgrade', 'Upgrade', '升级', '升級', '塔面板升级按钮'),
    ('Restart Level', 'Restart Level', '重新开始本关', '重新開始本關', '暂停界面重开'),
    ('Tower Codex', 'Tower Codex', '防御塔图鉴', '防禦塔圖鑑', '图鉴页标题'),
    ('Level', 'Level', '关卡', '關卡', '选关卡片/详情页默认标签'),
    # ---- 品牌副标题（语言相关，入表） ----
    ('FREEDOM TOWER · Tower Defense', 'FREEDOM TOWER · Tower Defense',
     '自由人塔防 · 单机塔防', '自由人塔防 · 單機塔防', '主菜单/开屏副标题'),

    # ---------------- 2026-10-14：暂停/介绍按钮 + 拖拽建造 + 介绍弹窗正文 ----------------
    ('Pause', 'Pause', '暂停', '暫停', 'HUD 右上角暂停按钮'),
    ('Game Intro', 'Game Intro', '游戏介绍', '遊戲介紹', 'HUD 右上角介绍按钮/弹窗标题'),
    ('Back to Level Select', 'Back to Level Select', '回到选关', '回到選關', '介绍弹窗「回到选关」按钮'),
    ('{0}: drag onto a buildable tile and release to place',
     '{0}: drag onto a buildable tile and release to place',
     '{0}：拖到可建造格上松手放置，拖回按钮取消', '{0}：拖到可建造格上鬆手放置，拖回按鈕取消',
     '拖拽建造提示（占位符 {0} 保留）'),
    ('Stop the monsters before they reach your base: build towers on the open tiles beside the path.',
     'Stop the monsters before they reach your base: build towers on the open tiles beside the path.',
     '在怪物途经的路边空地建造防御塔，阻止它们抵达你的基地。',
     '在怪物途經的路邊空地建造防禦塔，阻止它們抵達你的基地。', '介绍弹窗正文 1'),
    ('Long-press a tower button, drag it onto the board, then release to build.',
     'Long-press a tower button, drag it onto the board, then release to build.',
     '长按建造栏的塔按钮，拖到棋盘格子上松手即可建造（金币在落地成功后扣除）。',
     '長按建造欄的塔按鈕，拖到棋盤格子上鬆手即可建造（金幣在落地成功後扣除）。', '介绍弹窗正文 2'),
    ('You may slow the monsters down, but never fully block their path.',
     'You may slow the monsters down, but never fully block their path.',
     '你可以拖慢怪物的脚步，但不能把它们的路完全堵死。',
     '你可以拖慢怪物的腳步，但不能把它們的路完全堵死。', '介绍弹窗正文 3'),
    ('Survive every round to win the level.',
     'Survive every round to win the level.',
     '撑过全部回合即通关。', '撐過全部回合即通關。', '介绍弹窗正文 4'),
]

HEAD = ['id', 'en', 'zhHans', 'zhHant', 'comment']
TYPES = ['string', 'string', 'string', 'string', 'string']

def esc(s):
    return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))

def col_letter(i):
    s = ''
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s

def cell(ref, val):
    return '<c r="%s" t="inlineStr"><is><t xml:space="preserve">%s</t></is></c>' % (ref, esc(val))

rows_xml = []
# 列 A 是 Luban 的 tag 列（值以 ## 开头），字段从列 B 开始。
# row1: ## + head
rows_xml.append('<row r="1">' + cell('A1', '##') + ''.join(cell(col_letter(i+1)+'1', h) for i, h in enumerate(HEAD)) + '</row>')
# row2: ##type
rows_xml.append('<row r="2">' + cell('A2', '##type') + ''.join(cell(col_letter(i+1)+'2', t) for i, t in enumerate(TYPES)) + '</row>')
# row3: ## + desc
rows_xml.append('<row r="3">' + cell('A3', '##') + ''.join(cell(col_letter(i+1)+'3', d) for i, d in enumerate(HEAD)) + '</row>')
# data rows（从列 B 开始）
for ri, row in enumerate(ROWS, start=4):
    rows_xml.append('<row r="%d">' % ri + ''.join(cell(col_letter(ci+1)+str(ri), v) for ci, v in enumerate(row)) + '</row>')

sheet = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
         '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
         '<sheetViews><sheetView tabSelected="1" workbookViewId="0"/></sheetViews>'
         '<sheetFormatPr baseColWidth="8" defaultColWidth="9" defaultRowHeight="14.25"/>'
         '<cols>'
         '<col min="1" max="1" width="6" customWidth="1"/>'
         '<col min="2" max="2" width="26.25" customWidth="1"/>'
         '<col min="3" max="3" width="40" customWidth="1"/>'
         '<col min="4" max="4" width="40" customWidth="1"/>'
         '<col min="5" max="5" width="40" customWidth="1"/>'
         '<col min="6" max="6" width="30" customWidth="1"/>'
         '</cols>'
         '<sheetData>' + ''.join(rows_xml) + '</sheetData>'
         '<pageMargins left="0.7" right="0.7" top="0.75" bottom="0.75" header="0.3" footer="0.3"/>'
         '</worksheet>')

CT = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
      '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
      '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
      '<Default Extension="xml" ContentType="application/xml"/>'
      '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
      '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
      '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
      '</Types>')

RELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        '</Relationships>')

WB = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
      '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
      '<workbookPr/><bookViews><workbookView windowWidth="25920" windowHeight="12900"/></bookViews>'
      '<sheets><sheet name="Localization" sheetId="1" r:id="rId1"/></sheets>'
      '</workbook>')

WBRELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
          '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
          '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
          '</Relationships>')

STYLES = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
          '<fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>'
          '<fills count="1"><fill><patternFill patternType="none"/></fill></fills>'
          '<borders count="1"><border/></borders>'
          '<cellStyleXfs count="1"><xf/></cellStyleXfs>'
          '<cellXfs count="1"><xf/></cellXfs>'
          '</styleSheet>')

out = os.path.join(DATAS, 'Localization.xlsx')
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    z.writestr('[Content_Types].xml', CT)
    z.writestr('_rels/.rels', RELS)
    z.writestr('xl/workbook.xml', WB)
    z.writestr('xl/_rels/workbook.xml.rels', WBRELS)
    z.writestr('xl/styles.xml', STYLES)
    z.writestr('xl/worksheets/sheet1.xml', sheet)
print('written', out, 'rows:', len(ROWS))
