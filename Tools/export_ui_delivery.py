"""Read-only inventory of UI implementation. Writes documentation only, never configuration or saves."""
import csv
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Docs/UI_Redesign/Implementation/2026-10-26'
OUT.mkdir(parents=True, exist_ok=True)

def read(path):
    return (ROOT / path).read_text(encoding='utf-8-sig')

def csv_write(name, fields, rows):
    with (OUT / name).open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

def git_paths(*args):
    return subprocess.check_output(['git', '-c', 'core.quotepath=false', 'diff', '--name-only', '--', *args], cwd=ROOT, text=True, encoding='utf-8', stderr=subprocess.DEVNULL).splitlines()

manifest = json.loads(read('Docs/UI_Redesign/2026-10-26/specs/page-manifest.json'))
pages = {
    'splash': ('SplashView', 'SplashView', 'Launcher.FinishLoading → SplashFinishedEvent', '启动链状态；版本信息；Boot 后已就绪字体'),
    'loading': ('LoadingView', 'LoadingView; Launcher', 'Launcher.BeginLoadingConfig / HandleConfigLoadFailed', 'LoadingProgressEvent；Configs.FailedTables；真实重试回调'),
    'update': ('HotUpdateView', 'Assets/AOTAssembly/HotUpdateView.cs; Assets/AOTAssembly/BootUpdateSession.cs', 'BootLoader / HotUpdateEntry / Launcher', 'BootUpdateSession 阶段、字节、文件、Pause/Resume/Retry 回调；BootLocalization'),
    'menu': ('MainMenuView', 'MainMenuView; GameFlowManager', '启动完成 → MainMenuView', 'Configs.LevelTable；SaveManager 总成绩；TryGetResumableCheckpoint'),
    'select': ('SelectView', 'SelectView; LevelMapPreviewGraphic', '主菜单 StartGameRequestEvent → SelectView', '正式 TBSceneInfo 全量列表；SaveManager；TBLevelMap'),
    'item': ('TacticalLevelItem', 'SelectView', 'SelectView.BuildGrid → SelectGridLevel', '正式关卡 ID；解锁、当前版本星级、旧版星级和兼容检查点'),
    'detail': ('LevelDetailView', 'LevelDetailView; LevelMapPreviewGraphic', 'SelectView.OpenBriefing → LevelDetailView.Show', 'LevelConfig；LevelRatingProfile；Round/Wave/Enemy；SaveManager'),
    'intro': ('GameIntroView', 'GameIntroView; LevelDetailView', '简报 IntroBtn；关闭回到简报', '正式本地化四条玩法说明；来源页面；原有返回事件'),
    'hud': ('HudView; TowerInfoView', 'HudView; TowerActionMenu; TowerInfoView; Assets/Scripts/Tower/TowerPlacement.cs', 'GameFlowManager.StartLevel → HUD；TowerSelectedEvent → HUD 内嵌 TowerActionMenu', 'PlayerDataManager；GameFlowState；GameClock；TowerPlacement 原有合法性和拖动判定；已选塔 Config'),
    'tower': ('HudView; TowerInfoView', 'TowerActionMenu; TowerInfoView', '塔周围环形操作组 More → UIManager.Open<TowerInfoView>', '真实 BaseTower.Config；upgradeTo 链；金币；返还规则；RangeIndicatorView'),
    'pause': ('PauseView', 'PauseView; GameFlowManager', 'HUD 菜单 → PauseRequestEvent → SetPausedState(true)', 'GameClock.IsPaused；原有 Resume/Restart/Settings/QuitToSelect 事件'),
    'tip': ('TipsView', 'TipsView', 'ShowTipEvent → 有限队列；警告/失败抢占', '原有业务消息与正式本地化 key；unscaledDeltaTime'),
    'codex': ('TowerCodexView', 'TowerCodexView; TowerCodexItem', '主菜单塔图鉴；CompareBtn 切换', 'Configs.GetBaseTowers；正式塔表全部等级；Power/Radius/CD/Prices/EffectValue'),
    'compare': ('TowerCodexView', 'TowerCodexView; TowerCodexItem', '塔图鉴 CompareBtn；Back 返回浏览', '正式塔表按真实 Type / Level 排序；逐级属性与价格'),
    'monster': ('MonsterCodexView', 'MonsterCodexView', '主菜单 MonsterCodexBtn → OpenCodexRequestEvent(false)', '正式 EnemyTable 按 ResName 分组；119 张独立 UI 肖像；各配置变体属性范围'),
    'sell': ('SellConfirmView', 'SellConfirmView; GameFlowManager', '选中塔 → SellBtn → 二次确认', '真实塔对象/等级；sellPrice × SellRefundRate；原 TowerManager.Sell'),
    'confirm': ('ConfirmView', 'ConfirmView; SettingView; PauseView; LevelClearView; MainMenuView', '重置、重开、离开、退出及未保存返回', '原操作回调；TryResetAll；RetryPendingClearSave；风险后果说明'),
    'settings': ('SettingView', 'SettingView', '主菜单或暂停菜单 Settings；关闭保留原来源', 'LocalizationSettings.supportedLanguages；LanguageManager；SaveManager.TryResetAll'),
    'result': ('LevelClearView', 'LevelClearView; GameFlowManager', 'GameFlowManager.ShowClearPopup；RetrySave', 'LevelClearInfo；RatingPresentation；progressSaved/savePending；previousBest/newRecord；真实末关'),
    'common': ('LevelDetailView; MonsterCodexView; TowerCodexView; ConfirmView', 'LevelDetailView; MonsterCodexView; TowerCodexView; SettingView; LevelClearView', '空历史、图鉴读表失败、已提交操作的等待状态', '既有数据有效性、读表回调、保存/重置/出售处理标记'),
}
triggers = {
    '01_splash': '资源与配置完成后 Launcher 打开 Splash；结束事件进入主菜单',
    '02_loading_reading': 'Configs.LoadAsync 的已完成表数/总数改变',
    '02_loading_failed': '限定自动重试耗尽后显示原因、重试和退出',
    '03_update_checking': 'BootUpdateSession.Phase=Checking / Preparing',
    '03_update_download': 'Phase=Resources / DLL 且收到真实文件/字节计数',
    '03_update_validating': '资源或 DLL 校验阶段；未提供细分进度时使用不确定等待',
    '03_update_complete': 'Phase=Ready 后进入正式 Loading',
    '03_update_paused': 'Paused=true 且 Resume 回调存在；不支持时不显示虚假按钮',
    '03_update_resuming': '点击真实 Resume 回调后 Paused=false，继续真实进度',
    '03_update_retry': 'Retry 回调存在；点击先摘除回调防止重复提交，再重新检查',
    '03_update_failed': 'Phase=Failed / Restart；保留真实原因和可用重试',
    '04_menu_new': '没有通过版本和内容校验的可继续检查点；主按钮进入选关',
    '04_menu_continue': 'TryGetResumableCheckpoint 成功；按钮显示对应关卡',
    '05_select_all': '按正式 TBSceneInfo 的全部记录构建可滚动网格；点选只更新预览，简报按钮明确前进',
    '06_item_normal': '当前版本未评级且未选中',
    '06_item_selected': 'levelId == _selectedLevelId；青色描边与勾选',
    '06_item_complete': 'SaveManager.GetStars(levelId)>0；显示五星槽',
    '06_item_locked': '!SaveManager.IsUnlocked；仍可预览，简报明确解释锁定',
    '06_item_continue': '有效检查点关卡与条目相同；显示 Continue',
    '06_item_history': '当前版无星、GetLegacyStars>0；明确旧版未评级',
    '06_item_record': '预览显示当前正式最佳成绩；不把永久最佳记录误标为刚产生的新纪录',
    '07_detail_challenge': '已解锁；无该关有效检查点；显示挑战',
    '07_detail_continue': '该关有通过校验的兼容检查点；使用原 StartLevel 续玩路径',
    '07_detail_restart': 'ReplayBtn → 风险确认 → 成功清除兼容检查点后从头挑战；清除失败保留原数据',
    '08_intro': '简报 IntroBtn 打开；来源标记隐藏退出战斗按钮，Close 只关自身',
    '09_hud_prepare': 'GameFlowState.Preparing；开始按钮与金币/生命来自当前关卡',
    '09_hud_combat': 'GameFlowState.RoundRunning；波次、速度和暂停实时同步',
    '09_hud_between': 'RoundComplete；原有下一波倒计时和提前开始',
    '09_hud_build': '原塔型按钮发送 BuildTowerRequestEvent；选中态使用现有交互状态',
    '09_hud_drag': '原 TowerDragButton 长按/拖动/释放链；不另设第二次扣款',
    '09_hud_invalidpath': '原合法性判定会完全堵路；提示明确原因，失败不扣款',
    '09_hud_occupied': '目标格已有塔；原判定拒绝并提示',
    '09_hud_entry': '入口/基地/洞等非可建格；原判定拒绝',
    '09_hud_poor': '金币不足；建造按钮保持现有可用性规则，提示实际所需金额',
    '09_hud_built': '原 TryBuild 成功后原有表现与资源变化；无新经济规则',
    '09_hud_cancel': '原有取消建造/右键/ESC 路径；清除预览与选中',
    '09_hud_selected': '选中真实塔后 SortingGroup 临时提高；HUD 跟随塔显示升级/出售/更多环形动作；More 才打开 TowerInfoView 弹窗；关闭返回环形动作',
    '09_hud_hide_range': 'More 弹窗内 RangeBtn 切换范围显隐，勾选/空心标记同步',
    '11_pause': '打开菜单先由流程层暂停；设置关闭仍暂停；Continue 统一恢复',
    '12_tip_success': '原成功/普通消息；青色反馈；2.8 秒显示，不吞触摸',
    '12_tip_warning': '完全堵路消息；金色文字与具体原因；优先替换旧提示',
    '12_tip_failure': '占用/不可建/不足/加载或保存失败；红色原因，不只依赖颜色',
    '13_codex_normal': 'GetBaseTowers 返回普通塔；图鉴卡显示正式数值与定位',
    '13_codex_power': 'GetBaseTowers 返回火力塔；图鉴卡显示正式数值与定位',
    '13_codex_retard': 'GetBaseTowers 返回减速塔；图鉴卡显示正式数值与定位',
    '13_codex_compare': 'CompareBtn 切换，按真实塔表等级排序显示属性比较；Back 返回浏览',
    '14_monster_grid': 'EnemyTable 就绪；按真实 ResName 分组，滚动浏览 119 种形象',
    '14_monster_detail': '点卡片选择；显示原 UI 肖像与该形象全部配置变体属性范围',
    '14_monster_empty': 'EnemyTable 为空/失败；隐藏旧列表和旧肖像，显示重试与返回；关闭后过期回调失效',
    '15_sell': 'SellConfirmView.Setup 绑定当前真实塔，显示真实等级和返还',
    '15_sell_pending': '确认后 _pending，禁止重复/取消；下一帧调用原出售流程，失败不修改塔或金币',
    '16_confirm_reset': '设置 ResetBtn → 后果与清除范围确认；不在预览中执行',
    '16_confirm_resetpending': '确认关闭后设置页 _resetting；重置/关闭按钮防重复，提交原 TryResetAll',
    '16_confirm_resetfailed': 'TryResetAll=false；错误确认提供重试和取消',
    '16_confirm_leave': '暂停菜单选关按钮 → 保留最后已保存检查点的风险说明与确认',
    '16_confirm_restart': '暂停菜单或简报重开 → 重开风险确认',
    '16_confirm_quit': '主菜单退出 → 应用退出确认',
    '16_confirm_unsaved': '结算 savePending 时请求返回；只允许留在结算/重试保存，不丢弃成绩',
    '17_settings_zh-Hans': '正式设置下拉框选择简体中文，LanguageManager 即时刷新并持久化',
    '17_settings_zh-Hant': '正式设置下拉框选择繁體中文，LanguageManager 即时刷新并持久化',
    '17_settings_en': '正式设置下拉框选择 English，LanguageManager 即时刷新并持久化',
    '18_result_win': 'info.victory=true；显示唯一一组本次星级、真实统计和历史比较',
    '18_result_record': 'victory && progressSaved && !savePending && newRecord；未保存不显示新纪录',
    '18_result_low': 'RatingPresentation.Reasons(result) 提供实际扣星原因',
    '18_result_lose': 'victory=false；无下一关，只提供重试/选关',
    '18_result_saving': '_saving=true；真实重试提交期间禁用操作；初次同步保存不造假等待时长',
    '18_result_savefailed': 'savePending=true；明确原因，重试保存；返回进入安全说明',
    '18_result_retry': 'RetrySave 协程先禁用，调用 GameFlowManager.RetryPendingClearSave，再重绘同一 info',
    '18_result_saved': 'progressSaved=true && !savePending；合法路径恢复，无额外伪造成功状态',
    '18_result_final': '!hasNext || nextLevelId<=0；隐藏下一关，仅重玩/选关',
    '19_common_empty': '无当前版本历史成绩；显示未评级，不虚构 0 秒或新纪录，仍可挑战',
    '19_common_unavailable': '图鉴或启动读表失败；重试走 Configs.LoadAsync，保留返回/退出',
    '19_common_confirming': '保存、重置、出售处理标记；按钮禁止重复，完成/失败后恢复有效去向',
}

rows=[]
for entry in manifest:
    ident=entry['id']; family=entry['family']; prefab,script,entrance,data=pages[family]
    if family=='tower':
        tower_type={'normal':1,'power':2,'retard':3}[ident.split('_')[2]]
        level=ident.split('_')[-1]
        trigger=(f'真实选中塔 type={tower_type}；' + (f'等级={level[1:]}；按 upgradeTo 决定是否满级' if level.startswith('l') else '金币小于下一等级增量价格；显示缺额；范围/出售/关闭仍有效'))
    else: trigger=triggers[ident]
    if not script.startswith('Assets/'): script='; '.join('Assets/Scripts/UI/'+s+'.cs' if '/' not in s and s not in ['Launcher','GameFlowManager'] else ('Assets/Scripts/Launcher.cs' if s=='Launcher' else 'Assets/Scripts/Game/GameFlowManager.cs' if s=='GameFlowManager' else s) for s in script.split('; '))
    paths=[]
    for page in prefab.split('; '):
        paths.append(('Assets/Resources/BootUI/' if page=='HotUpdateView' else 'Assets/HotUpdateUI/' if page in ['LoadingView','SplashView'] else 'Assets/Prefabs/UI/')+page+'.prefab')
    partial = family in ['menu','monster','codex','compare','select','item','tower'] or ident in ['02_loading_failed','16_confirm_resetfailed','16_confirm_restart','16_confirm_leave','18_result_saving','18_result_retry','09_hud_selected','09_hud_hide_range','15_sell','15_sell_pending']
    note='已接入正式页面/数据或复用状态控制；未进入 Play Mode，未认证运行交互。'
    if partial: note+=' 新文案有源表缺项，详见 localization-required.csv；保留英文/原文回退。'
    if ident=='06_item_record': note+=' 条目只显示真实最佳；瞬时新纪录仅在已保存结算中表达，未增加虚构永久新纪录徽标。'
    if family=='monster': note+=' 12705 行配置按 119 种资源分组，范围为真实配置范围，不是当前关卡敌人的单一数值；大卡片列表与详情复用当前页面，返回详情列表保留滚动位置。'
    if family in ['codex','compare']: note+=' 塔型标签页展示单塔；比较显示正式全等级；窄屏比较可滚动。'
    if family=='update': note+=' 原 AOT 会话能力复用；暂停/恢复只在真实回调可用时出现。'
    if family=='settings': note+=' 三语切换机制保持；重置失败新文案仍待源表补齐。'
    if family=='detail': note+=' 敌人横向肖像条按正式波次引用去重；缺少图片时保留真实名称。'
    rows.append(dict(id=ident,title=entry['title'],prefab='; '.join(paths),script=script,data_source=data,entry=entrance,trigger=trigger,status='部分实现：本地化源表待补；运行未验证' if partial else '实现已接入；运行未验证',notes=note))
known={x['id'] for x in json.loads(read('Assets/ConfigJson/tblocalization.json'))}
missing={}
source_files=set(git_paths('Assets'))
source_files.update(str(p.relative_to(ROOT)).replace('\\','/') for p in (ROOT/'Assets/Scripts/UI').glob('*.cs') if p.name in ['MonsterCodexView.cs','LevelMapPreviewGraphic.cs','TowerActionMenu.cs','TowerPresentation.cs'])
for file in source_files:
    if not file.endswith('.cs') or not (ROOT/file).exists(): continue
    source=read(file)
    literals=re.findall(r'Localization\.Get\("((?:\\.|[^"\\])*)"',source)
    literals.extend(re.findall(r'(?:Text|Format)\(translate,\s*"((?:\\.|[^"\\])*)"',source))
    for literal in literals:
        key=json.loads('"'+literal+'"')
        if key not in known: missing.setdefault(key,set()).add(file)
for key in ['Compare','Monster Codex','Range','View Briefing','Configured variants: {0}','View Details']:
    if key not in known: missing.setdefault(key,set()).add('Assets/Editor/TacticalForgePrefabBuilder.cs / UI state labels')
proposals={
 'Save reset failed':('存档重置失败，请重试。','存檔重設失敗，請重試。'),
 'Restart this level?':('从头重新挑战本关？当前战斗将重新开始。','從頭重新挑戰本關？目前戰鬥將重新開始。'),
 'Range':('射程范围','射程範圍'), 'Saving...':('正在保存…','正在儲存…'),
 'Monster Codex':('怪物图鉴','怪物圖鑑'), 'Configured variants: {0}':('配置变体：{0}','設定變體：{0}'),
 'Speed':('移动速度','移動速度'), 'Armor':('护甲减伤','護甲減傷'), 'Gold':('金币奖励','金幣獎勵'),
 'Unavailable':('内容暂不可用','內容暫時無法使用'),
 'Config load failed, retrying...':('配置读取失败，正在重试…','設定讀取失敗，正在重試…'),
 'Leave this battle?':('返回选关？只保留最后成功保存的波次检查点。','返回選關？只保留最後成功儲存的波次檢查點。'),
 'Compare':('属性比较','屬性比較'), 'View Briefing':('查看战前简报','查看戰前簡報'),
 'View Details':('查看详情','查看詳情'), 'More':('更多','更多'),
}
locale_rows=[]
for key,files in sorted(missing.items()):
    if key not in proposals: raise RuntimeError('Provide manual translation proposal for '+repr(key))
    hans,hant=proposals[key]
    locale_rows.append(dict(id=key,en=key,zhHans=hans,zhHant=hant,source='; '.join(sorted(files)),status='待人工维护 Localization.xlsx 并标准 Luban 导出；本 CSV 不参与运行'))
csv_write('localization-required.csv',['id','en','zhHans','zhHant','source','status'],locale_rows)
if not locale_rows:
    for row in rows:
        row['status']='实现已接入；运行未验证'
        row['notes']=row['notes'].replace(' 新文案有源表缺项，详见 localization-required.csv；保留英文/原文回退。',' 新增文案已由 Localization.xlsx 经标准 Luban 导出。')
        row['notes']=row['notes'].replace('三语切换机制保持；重置失败新文案仍待源表补齐。','三语切换机制保持；重置失败新文案已由源表导出。')
csv_write('ui-state-implementation.csv',list(rows[0]),rows)

catalog=read('Assets/Scripts/Data/MonsterCatalog.cs')
def array(name):
    match=re.search(r'string\[\]\s+'+name+r'\s*=\s*\{(.*?)\};',catalog,re.S)
    return re.findall(r'"([^"]+)"',match.group(1))
catalog_sources=dict(zip(array('Names'),array('SourcePaths')))
assets=[]
for file in sorted((ROOT/'Assets/_UIAssets/UI/TacticalForge').rglob('*')):
    if not file.is_file() or file.suffix in ['.meta','.txt']:continue
    path=file.relative_to(ROOT).as_posix(); width=height=''; source='TacticalForgePrefabBuilder.GenerateArt'; usage='生产 UI prefab 直接序列化引用；现有 _UIAssets 收集器覆盖'
    meta=file.with_suffix(file.suffix+'.meta').read_text(encoding='utf-8-sig') if file.with_suffix(file.suffix+'.meta').exists() else ''
    if file.suffix=='.png':
        with file.open('rb') as f: header=f.read(24)
        width,height=struct.unpack('>II',header[16:24]); kind='Sprite (single)'
    elif file.suffix=='.otf':
        kind='OpenType source font';source='Noto CJK / NotoSansCJKsc-Regular; SIL Open Font License 1.1';usage='TacticalSans 动态 SDF 源字体；APK Resources 启动壳的直接依赖'
    else:
        kind='TMP dynamic SDF font; atlas/material subassets';width=height=2048;source='NotoSansCJKsc-Regular.otf；正式本地化字符预热';usage='LocalizationSettings 三语映射；页面 TMP 直接引用；AOT Resources 依赖嵌入 APK'
    if '/Portraits/' in path:
        name=file.stem.removeprefix('Enemy_');original=catalog_sources[name];directory=Path(original).parent
        directions=(directory/'Directions'/(name+'_Directions.png')).as_posix()
        source=original+' read-only SpriteRenderer hierarchy composition; no enemy component instantiated'
        usage='MonsterCodexView.portraits 序列化 Sprite；独立 UI 展示副本'
    if file.name=='keyart.png':source='Docs/UI_Redesign/2026-10-26/assets/tactical-forge-keyart.png；原设计包主视觉复用，本轮未调用 Image API'
    guid_match=re.search(r'^guid: (\w+)',meta,re.M)
    assets.append(dict(path=path,source=source,width=width,height=height,import_type=kind,guid=guid_match.group(1) if guid_match else '',sha256=hashlib.sha256(file.read_bytes()).hexdigest(),usage=usage,notes='Android：肖像/主视觉 ETC2_RGBA8，其余小图 RGBA32；无 mipmap；实际内存需设备验收' if kind.startswith('Sprite') else '许可：Assets/_UIAssets/UI/TacticalForge/Fonts/OFL.txt'))
reused = {
    'Assets/_UIAssets/UI/UI_TowerIcon_Normal.png': 'HUD 普通塔入口、普通塔图鉴、选中塔面板',
    'Assets/_UIAssets/UI/UI_TowerIcon_Power.png': 'HUD 火力塔入口、火力塔图鉴、选中塔面板',
    'Assets/_UIAssets/UI/UI_TowerIcon_Retard.png': 'HUD 减速塔入口、减速塔图鉴、选中塔面板',
    'Assets/Art/Generated/Range_Ring.png': '原 RangeIndicatorView 按正式射程绘制；显隐按钮复用该显示对象',
    'Assets/Art/Generated/Path_Arrow.png': '原战场实时路径显示；预览地图使用独立 UGUI 网格',
}
for path,usage in reused.items():
    file=ROOT/path
    if not file.exists(): raise FileNotFoundError(path)
    with file.open('rb') as stream: width,height=struct.unpack('>II',stream.read(24)[16:24])
    meta=read(path+'.meta');guid=re.search(r'^guid: (\w+)',meta,re.M).group(1)
    assets.append(dict(path=path,source='工程既有资源；本轮只读复用',width=width,height=height,import_type='Existing Sprite',guid=guid,sha256=hashlib.sha256(file.read_bytes()).hexdigest(),usage=usage+'；ResTable 原逻辑名 / 已有收集器',notes='没有改写原文件、导入设置或 meta'))
prefab_files=list((ROOT/'Assets/Prefabs/UI').glob('*.prefab'))+list((ROOT/'Assets/HotUpdateUI').glob('*.prefab'))+[ROOT/'Assets/Resources/BootUI/HotUpdateView.prefab']
prefab_guids=set()
for prefab_file in prefab_files:
    prefab_guids.update(re.findall(r'guid: ([0-9a-f]{32})',prefab_file.read_text(encoding='utf-8-sig')))
already_listed={x['path'] for x in assets}
for directory in ['Assets/_UIAssets/UI','Assets/Art/Generated','Assets/Art/Logo']:
    for meta_file in sorted((ROOT/directory).rglob('*.png.meta')):
        path=meta_file.relative_to(ROOT).as_posix().removesuffix('.meta')
        if path in already_listed: continue
        guid=re.search(r'^guid: (\w+)',meta_file.read_text(encoding='utf-8-sig'),re.M).group(1)
        if guid not in prefab_guids: continue
        file=ROOT/path
        with file.open('rb') as stream: width,height=struct.unpack('>II',stream.read(24)[16:24])
        assets.append(dict(path=path,source='工程既有 UI 图片；生产预制体直接引用',width=width,height=height,import_type='Existing Sprite',guid=guid,sha256=hashlib.sha256(file.read_bytes()).hexdigest(),usage='正式 UI prefab 序列化 Sprite；沿用当前收集器及依赖',notes='本轮保留的装饰、卡片或状态图片；没有改写原 PNG/meta'))
        already_listed.add(path)
assets.append(dict(path='Assets/Scripts/UI/LevelMapPreviewGraphic.cs',source='正式 TBLevelMap + BoardGeometry.IsWalkable',width='dynamic',height='dynamic',import_type='UGUI mesh',guid='',sha256=hashlib.sha256((ROOT/'Assets/Scripts/UI/LevelMapPreviewGraphic.cs').read_bytes()).hexdigest(),usage='选关/简报实际地图展示；不修改战场寻路或地图',notes='静态空地图通路；战场实时路线沿用现有 AStar 表现'))
csv_write('asset-manifest.csv',list(assets[0]),assets)

protected=git_paths('Assets/Prefabs/Enemy','Assets/_UIAssets/Monsters','Assets/Scripts/Data/MonsterCatalog.cs','Luban/Config/Datas','Assets/ConfigJson','Assets/Gen')
authorized_localization=[p for p in protected if p in {'Luban/Config/Datas/Localization.xlsx','Assets/ConfigJson/tblocalization.json'}]
protected=[p for p in protected if p not in authorized_localization]
portrait_files=list((ROOT/'Assets/_UIAssets/UI/TacticalForge/Portraits').glob('*.png'))
blank_portraits=[]
for file in portrait_files:
    with Image.open(file) as portrait:
        if not portrait.convert('RGBA').getchannel('A').getbbox(): blank_portraits.append(file.name)
if len(rows)!=85 or len({x['id'] for x in rows})!=85: raise RuntimeError('State inventory must contain all 85 unique IDs')
summary={'designStates':len(rows),'formalLevels':len(json.loads(read('Assets/ConfigJson/tbsceneinfo.json'))),'enemyRows':len(json.loads(read('Assets/ConfigJson/tbenemydata.json'))),'portraitCount':len(portrait_files),'blankPortraits':blank_portraits,'assetRows':len(assets),'missingLocalizationKeys':len(locale_rows),'protectedTrackedDiffs':protected,'screenshotCount':len(list((OUT/'evidence').glob('*.png'))),'project':'D:/FishTestGame','mcp':'http://127.0.0.1:8084/mcp','runtimeAcceptance':'not executed','visualFidelity':'implemented; open differences documented in changes.md; not accepted on device'}
summary['authorizedLocalizationTrackedDiffs']=authorized_localization
(OUT/'delivery-inventory.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False))
