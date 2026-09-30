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
    }
}
