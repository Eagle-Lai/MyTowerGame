# Zombie118 完成；队列仅余 PossessedWarg79 阻断

封存时间：2026-10-29T23:46:26.681643+08:00。本聊天/最终审计owner：01a18832-7895-7a23-ba81-c2c410a5a454；本轮dispatch_token：wolfmounfed-to-zombie-20261029_230534-9abf79b2-282d-4c43-bc85-2b10f14a62f1。Zombie已record为completed_pending_user_art_review，user_approved=false；实时107/108。唯一未完成项PossessedWarg79保持blocked。没有后继候选，不创建新聊天、fork、子代理或自动化。

## 最终资源与原生合同

最终版本：Up_AIrevision01_Down_AIinitial_alpha01_layout02_nativeattack01。仅改Assets/Prefabs/Enemy/Enemy_Zombie.prefab及Assets/_UIAssets/Monsters/Giants/Zombie/Directions；battle SHA256为BC5F3E9009CB22C03F38075CA358A4AEA29F362EF53019315941DD9953AF91E0。22个生产绑定、全部暂存、installed_manifest/Verify与角色专属native_attack_timing01 manifest/Verify均匹配preplay_version_binding_20261029.json，最终绑定见Docs/EnemyDirectionReview/Remaining_20261024/Zombie/final_version_binding_20261029.json。

源为灰褐/橄榄色缝合双足巨人，赭斑、浅米大块高光、刺状缝线与小环、头顶小块浅褐脑瓣、淡黄圆眼小黑瞳、愤怒张嘴/死亡空白眼闭嘴、深色宽护腕、米白破腰裙。解剖右手唯一象牙刺金褐木棒，左手空拳；没有骷髅项链、腰扣、尾巴或靴子。Up初图三个头误为正脸，否决原图完整保留；Up revision_01成功得到无脸后脑/耳背，Down用初图。Up三表情用选定Normal后脑复用，明确记录在art_selection。14透明分件、2048atlas、PPU100，alpha01填354个小孔像素且保原件/区域方法，最终0孔洞/0品红；layout02将肩髋根埋入躯干、双腿错相短步、后臂在body后。没有重新pack覆盖这些修订。

自身Giant Ready0.5s/Walk0.666666687s/Attack1s/Death0.5s，float绑定18/30/27/24、PPtr均0。Attack原事件SetHead0@0、SetHead1@0.25、Attack@0.766666651、SetHead0@0.783333361，Death SetHead2@0；完整曲线key/tangent/weight/wrap、事件、controller参数/过渡及原件字节存档。仅本角色Attack_Directions的92条DirectionVisual曲线，将蓄力结束定为2/3秒、发力峰值对齐原Attack事件，Down双臂相对Up镜像且空臂幅度30%。原左右绑定、事件、时长、loop和原源动画保持；没有修改共享C#。Zombie原battle表情接收器完整，无HeadSprites修复。generic原组件语义直接PASS，无例外门。

## 真实运行与视觉审阅

runtime_r01：84PASS0FAIL，322张PNG，JSONL SHA256 1D1E49FE4B0B4CC5210DDD24E4490CF10A365080C1575696F2D718A18136D177。runtime_updeath_r01：84PASS0FAIL，317张PNG，JSONL SHA256 2794C0C441C583767926245F92D9462FA4FF32629FB7C810BFB279ACCFA087A4。总168PASS0FAIL、639张真实Unity Play帧；两轮自动返回clean Boot。保存actual_frames.jsonl、checks、全部PNG的frame/realtime/normalizedTime/SHA及媒体。覆盖四向、斜向滞回/近零、原生状态/表情/攻击事件、连续转向保相位、受击和致死白闪结束、死亡旋转收缩淡出、自动回收同实例复用、暂停恢复与1x/2x/3x、测试器Flying探针。无Animator.Update或合成姿态冒充实机帧。

实际审完整源/离线四向与两轮four_directions、runtime strip、14张时序/原生循环/GIF解码板，319采样位/303张不同真实PNG；12个最终GIF各5编码帧，共60。另看未裁Up、Down愤怒攻击、Up死亡、复用、双向GIF整帧，以及两轮Up/Down距0.766666651秒最近的发力峰值原PNG。所审样本肩髋根连接、短步及单手木棒横扫正常，发力时手和棒柄在躯干后自然遮挡；无五官后脑、重复器官、地面影或头手脚武器裁边。白闪结束、死亡和复用复位正常。死亡为分renderer淡出，重叠分件可见。采用逐序抽样，未实时播放GIF、未逐张审完全部639帧；不声称一体alpha。仍须用户美术验收。

Zombie原生Walk约666.6667ms，GIF只能编码10ms单位，6个行走循环分别从430/440/500/450/430/500ms修为最近合法670ms，量化差+3.3333ms。只在Docs按真实normalized phase及原有10组实际PNG配对重编码，无合成姿态，原6份GIF和两manifest保留。AllGIF1726→1744，本角色18来源=12当前审核版本+6历史时长版；本角色全部源/集中副本SHA一致，1726个旧来源及副本逐个SHA校验一致，分类保留。

## 范围与交还Unity

Assets/Packages/ProjectSettings/Luban全路径SHA并集5685→5705，共22变化=20新增Directions文件含根meta+当前battle修改+Reporter build_info自动时间戳，0删除、0unexpected。ReporterEditor代码未改，build_info严格匹配本机名/本地格式及两轮Play时间窗。源prefab/atlas及meta、原动画/controller字节、共享C#、其他角色/配置与首批批准/BlueScorpion历史保护保持。历史global scope不改写PASS。最终现场8088检查14个sprite rect/pivot/PPU100、Multiple/alphaTransparency/mipmap、依赖和live Verify通过；error/errorCS均0、scriptCompilationFailed=false；单一Assets/Scenes/Boot.unity干净，非Play、compile/update/reload/test/balance/recording/review/manual均空闲。无C#修改，不为形式额外编译。最终交还见Docs/EnemyDirectionReview/Remaining_20261024/Zombie/handoff_release_final_20261029.json，未构建或部署。

## 网络与唯一未完成项

Zombie正式图像请求3次，全HTTP200：Up初图1532858bytes、Up定向美术revision_01为1481775bytes、Down初图1547009bytes，实际均PNG RGBA1536×1024。0unknown、0网络恢复、1次必要付费美术修正；费用未独立核实，响应usage为本地估计。保现有generate入口和Curl固定域名边缘，凭据仅运行时使用，无系统代理/hosts/TLS改动。其他历史unknown/计数完整保留，无借其他角色付费探测。

重新递归核所有未完成材料，仅PossessedWarg79，21个文件；Up已成功、Down只有prompt.txt和request.json，原请求SHA256 B2B3C9FB4B78E2FFB5E606FCE95BB2843575982CADBE6C6E97D352346D27BA4A，无raw/result/uncertain result、服务响应或查询ID，无stage/install/runtime；六源指纹仍与原阻断记录一致。本机没有既有入口的在途图像生成进程。原请求结果和可能费用unknown，不能推断未发送/未收费；本轮未重新发送或修改其原材料。队列因此blocked，不是108/108完成，也不因待用户美术审核而阻断。

恢复条件：

1. 恢复原Down请求对应的完整图片/服务响应，并用request.json SHA256、输入/提示词和原时间核对身份；若取得服务端请求/任务ID，先查询原结果，不能把查询当作新生成。
2. 如果无法取回原结果，需要用户针对PossessedWarg Down明确授权一个新的有费用请求，并知悉旧请求结果/费用仍unknown及可能重复计费；一般API授权和其他角色的恢复额度不能替代这一针对性授权。
3. 合法恢复条件满足后先重读progress/chain与磁盘，显式登记唯一active所有权和适用于PossessedWarg的新token，再从已有Up和Down原始请求阶段恢复。不得清除旧unknown、重置计数或把Zombie再次执行。

真实队列、全部原失败/否决/未知请求及历史已保留；没有Git提交/同步/清理、配置表写入、声音恢复、桌面控制或memory修改。
