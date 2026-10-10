namespace FTProject
{
    /// <summary>
    /// 全局事件名常量。
    /// v2.1 在原有基础上补齐了「波次 / 经济 / 生命 / 战斗」相关事件。
    /// </summary>
    public class EventName
    {
        // ------------------------------------------------------------------
        // 基础
        // ------------------------------------------------------------------

        /// <summary>每帧驱动（v2.1 起只有 CombatSystem 一个订阅者，见 CombatSystem.OnInit）</summary>
        public const string UpdateEvent = "UpdateEvent";

        /// <summary>配置表加载完成，参数：bool 是否全部成功（GameFlowManager 据此开始建关）</summary>
        public const string ConfigLoadedEvent = "ConfigLoadedEvent";

        // ------------------------------------------------------------------
        // 地图与寻路
        // ------------------------------------------------------------------

        /// <summary>棋盘初始化完成</summary>
        public const string MapInitFinish = "MapInitFinish";

        /// <summary>请求刷新敌人路径（建塔/拆塔后触发）</summary>
        public const string RefreshPathEvent = "RefreshPathEvent";

        /// <summary>地图显隐（调试用）</summary>
        public const string SetMapActiveState = "SetMapActiveState";

        // ------------------------------------------------------------------
        // 建造 / 拆除
        // ------------------------------------------------------------------

        /// <summary>进入建造态（塔跟随鼠标）</summary>
        public const string BuildingTower = "BuildingTower";

        /// <summary>建造成功，参数：BaseTower</summary>
        public const string BuildTowerSuccess = "BuildTowerSuccess";

        /// <summary>建造失败（参数：string 原因，供 UI 直接展示）</summary>
        public const string BuildTowerFail = "BuildTowerFail";

        /// <summary>塔被销毁，参数：BaseTower</summary>
        public const string DestroyTower = "DestroyTower";

        /// <summary>选中一座已建造的塔（用于打开塔信息面板），参数：BaseTower</summary>
        public const string TowerSelectedEvent = "TowerSelectedEvent";

        /// <summary>取消选中塔</summary>
        public const string TowerDeselectedEvent = "TowerDeselectedEvent";

        /// <summary>请求升级选中的塔，参数：BaseTower</summary>
        public const string TowerUpgradeRequestEvent = "TowerUpgradeRequestEvent";

        /// <summary>升级成功，参数：BaseTower（升级后的**新实例**）。
        /// 【为什么必须带参】升级采用"换实例"，旧的 BaseTower 已被销毁并归还对象池。
        /// UI 必须拿新实例刷新，任何缓存的旧引用都是失效对象。
        /// 【不要用 BuildTowerSuccess 代替】那个事件的语义是"新建了一座塔"，
        /// HudView 收到会退出放置态并复位按钮，升级时发它会把 HUD 状态搅乱。</summary>
        public const string TowerUpgradeSuccess = "TowerUpgradeSuccess";

        /// <summary>请求出售选中的塔，参数：BaseTower</summary>
        public const string TowerSellRequestEvent = "TowerSellRequestEvent";

        // ------------------------------------------------------------------
        // 怪物
        // ------------------------------------------------------------------

        /// <summary>怪物被击杀，参数：(BaseEnemy, int reward)</summary>
        public const string EnemyKilledEvent = "EnemyKilledEvent";

        /// <summary>怪物走到终点（漏怪），参数：(BaseEnemy, int damage)</summary>
        public const string EnemyReachedEndEvent = "EnemyReachedEndEvent";

        /// <summary>怪物被回收，参数：BaseEnemy</summary>
        public const string EnemyResetEvent = "EnemyResetEvent";

        /// <summary>请求生成本波敌人（保留兼容）</summary>
        public const string GenerateEnemyEvent = "GenerateEnemyEvent";

        /// <summary>玩家点击「开始」请求开打本回合</summary>
        public const string StartRoundRequestEvent = "StartRoundRequestEvent";

        // ------------------------------------------------------------------
        // 关卡选择 / 暂停 / 设置（M3 元进度）
        // ------------------------------------------------------------------

        /// <summary>请求开始某一关，参数：int 关卡 id</summary>
        public const string SelectLevelRequestEvent = "SelectLevelRequestEvent";

        /// <summary>请求关闭关卡选择界面（回到当前对局 / 退出）</summary>
        public const string CloseSelectRequestEvent = "CloseSelectRequestEvent";

        /// <summary>请求暂停</summary>
        public const string PauseRequestEvent = "PauseRequestEvent";

        /// <summary>请求继续（取消暂停）</summary>
        public const string ResumeRequestEvent = "ResumeRequestEvent";

        /// <summary>请求重开当前关卡</summary>
        public const string RestartLevelRequestEvent = "RestartLevelRequestEvent";

        /// <summary>请求退出当前对局、回到关卡选择</summary>
        public const string QuitToSelectRequestEvent = "QuitToSelectRequestEvent";

        /// <summary>请求打开设置界面</summary>
        public const string OpenSettingsRequestEvent = "OpenSettingsRequestEvent";

        /// <summary>请求关闭设置界面</summary>
        public const string CloseSettingsRequestEvent = "CloseSettingsRequestEvent";

        /// <summary>关卡通关结算，参数：(int 关卡 id, int 星级, int 剩余生命)</summary>
        public const string LevelClearEvent = "LevelClearEvent";

        /// <summary>玩家点击塔按钮，请求进入放置模式。参数：(int type, int level)</summary>
        public const string BuildTowerRequestEvent = "BuildTowerRequestEvent";

        /// <summary>退出放置模式（右键 / ESC）</summary>
        public const string CancelBuildRequestEvent = "CancelBuildRequestEvent";

        // ------------------------------------------------------------------
        // 波次与流程
        // ------------------------------------------------------------------

        /// <summary>一波开始，参数：int 波次序号</summary>
        public const string WaveStartEvent = "WaveStartEvent";

        /// <summary>一波清空，参数：int 波次序号</summary>
        public const string WaveClearEvent = "WaveClearEvent";

        /// <summary>回合开始，参数：int 回合序号（从 1 计）</summary>
        public const string RoundStartEvent = "RoundStartEvent";

        /// <summary>回合清空，参数：int 回合序号</summary>
        public const string RoundClearEvent = "RoundClearEvent";

        /// <summary>全部回合完成（胜利）</summary>
        public const string AllRoundClearEvent = "AllRoundClearEvent";

        /// <summary>结算，参数：(bool isVictory)</summary>
        public const string GameOverEvent = "GameOverEvent";

        // ------------------------------------------------------------------
        // 经济与生命
        // ------------------------------------------------------------------

        /// <summary>金币变化，参数：(int current, int delta)</summary>
        public const string GoldChangeEvent = "GoldChangeEvent";

        /// <summary>玩家生命变化，参数：(int current, int delta)</summary>
        public const string PlayerHpChangeEvent = "PlayerHpChangeEvent";

        /// <summary>玩家状态初始化完成（进关卡时触发一次）</summary>
        public const string PlayerStateInitEvent = "PlayerStateInitEvent";

        // ------------------------------------------------------------------
        // UI 提示
        // ------------------------------------------------------------------

        /// <summary>弹出提示，参数：string</summary>
        public const string ShowTipEvent = "ShowTipEvent";

        // ------------------------------------------------------------------
        // 倍速（P2b）
        // ------------------------------------------------------------------

        /// <summary>
        /// 请求切换倍速，参数：float 目标倍率（1 / 2 / 3，允许 2.5 这类降档值）。
        /// 【为什么是 float 而不是 int】策划案 §7.3 硬性约束⑤要求"降档扩展只需改 Speed 值"：
        /// 若这里收窄成 int，把 ×3 降成 ×2.5 就必须改事件签名与全部订阅方。
        /// 由 HudView 发请求、GameFlowManager 校验后写入 GameClock。
        /// </summary>
        public const string GameSpeedChangeRequestEvent = "GameSpeedChangeRequestEvent";

        /// <summary>倍速已变更，参数：float 新的倍率（订阅方：HudView 同步按钮文案、BaseEnemy 同步 Animator）。</summary>
        public const string GameSpeedChangedEvent = "GameSpeedChangedEvent";

        // ------------------------------------------------------------------
        // 启动链（UI 补全 A1/A2/A3）—— Splash → Loading → HotUpdate → 主菜单
        // ------------------------------------------------------------------

        /// <summary>开屏页动画播完（Launcher 据此切到 LoadingView）</summary>
        public const string SplashFinishedEvent = "SplashFinishedEvent";

        /// <summary>启动加载进度，参数：(string 阶段文案, float 0~1 进度)。
        /// 【为什么带阶段文案】LoadingView 的 StatusText 要随阶段变（"正在初始化资源系统..." → "正在加载配置表..."），
        /// 只给一个 0~1 数字无法表达"当前在做什么"，玩家会觉得进度条在空转。</summary>
        public const string LoadingProgressEvent = "LoadingProgressEvent";

        /// <summary>热更新阶段文案，参数：string（"正在检查更新..." / "正在下载资源..." / "已暂停" ...）。
        /// 【为什么与进度分成两个事件】EventDispatcher 的泛型重载最多 4 个类型参数，
        /// 而本界面需要"文案 + 文件数 + 字节数"共 5 项信息。
        /// 拆成"文案"与"数值"两个事件，既绕开上限，也让语义更清楚（文案变化远比进度稀疏）。</summary>
        public const string HotUpdatePhaseEvent = "HotUpdatePhaseEvent";

        /// <summary>热更新进度，参数：(int 已下载文件数, int 总文件数, long 已下载字节, long 总字节)</summary>
        public const string HotUpdateProgressEvent = "HotUpdateProgressEvent";

        /// <summary>热更新失败，参数：string 失败原因（HotUpdateView 显示红字并给"重试"）</summary>
        public const string HotUpdateFailedEvent = "HotUpdateFailedEvent";

        /// <summary>热更新完成（无论是否真的更新过内容），Launcher 据此继续走配置表加载</summary>
        public const string HotUpdateFinishedEvent = "HotUpdateFinishedEvent";

        // ------------------------------------------------------------------
        // 主菜单与图鉴（UI 补全 B1/B2/B3/B4）
        // ------------------------------------------------------------------

        /// <summary>请求打开主菜单</summary>
        public const string OpenMainMenuRequestEvent = "OpenMainMenuRequestEvent";

        /// <summary>主菜单点「开始游戏」请求进入选关</summary>
        public const string StartGameRequestEvent = "StartGameRequestEvent";

        /// <summary>请求打开图鉴，参数：bool（true=塔图鉴，false=怪物图鉴）</summary>
        public const string OpenCodexRequestEvent = "OpenCodexRequestEvent";

        /// <summary>请求打开关卡详情弹窗，参数：int 关卡 id</summary>
        public const string OpenLevelDetailRequestEvent = "OpenLevelDetailRequestEvent";

        // ------------------------------------------------------------------
        // 出售二次确认（UI 补全 C1）
        // ------------------------------------------------------------------

        /// <summary>出售已在 SellConfirmView 里被确认，参数：BaseTower。
        /// 【与 TowerSellRequestEvent 的区别】后者是"玩家点了出售按钮"（意图），
        /// 本事件是"玩家在确认弹窗里点了确认"（决定）。GameFlowManager 只监听本事件真正执行出售，
        /// 这样"取消"永远不可能误卖。</summary>
        public const string TowerSellConfirmEvent = "TowerSellConfirmEvent";
    }
}
