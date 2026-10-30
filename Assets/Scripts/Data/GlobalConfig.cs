using cfg;
using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 全局参数门面（2026-10-30 拆分后）。
    ///
    /// ==================================================================
    /// 【为什么还叫 Global、还保留这些属性名】
    ///   拆分前它包着 `TBGlobal` 单行表的 22 个常量，全工程 ~30 处引用 `Configs.Global.X`。
    ///   拆分后：**引擎/性能常量**（池大小、同屏上限、死亡回收、离线检查、日志开关）仍来自
    ///   单行 `TBGlobal`；**玩法/表现常量**（格子尺寸、退款率、波次节奏、飘字、震屏…）
    ///   改由每关一份的 `TBLevelRules` 提供。
    ///
    ///   为了让 30 处调用点一行都不用改，这里保持属性名不变，只把**数据来源**换成
    ///   `(Global 引擎行, 本关 LevelRules 行)` 两段 —— 对上层来说仍然是"读一个 Global"。
    ///   代价是类名有点名不副实，但省掉了 30 处机械替换带来的回归风险。
    ///
    /// 【切换关卡】`Configs.SetActiveLevel` 会重建本对象（换绑 LevelRules 行）。
    /// ==================================================================
    /// </summary>
    public class GlobalConfig
    {
        private readonly Global _g;
        private readonly LevelRules _r;

        public GlobalConfig(Global g, LevelRules rules)
        {
            _g = g;
            _r = rules;
        }

        // ==================================================================
        // 引擎 / 性能常量（仍来自 TBGlobal 单行表）
        // ==================================================================

        public int EnemyPoolSize { get { return _g.EnemyPoolSize > 0 ? _g.EnemyPoolSize : 64; } }
        public int BulletPoolSize { get { return _g.BulletPoolSize > 0 ? _g.BulletPoolSize : 128; } }

        /// <summary>同屏怪物上限（性能保护）</summary>
        public int MaxEnemyAlive { get { return _g.MaxEnemyAlive > 0 ? _g.MaxEnemyAlive : 200; } }

        // 帧率由启动层统一固定，旧配置字段不再覆盖运行策略。
        public int TargetFrameRate { get { return FTProject.AOT.FrameRatePolicy.TargetFrameRate; } }

        /// <summary>死亡动画播完后延迟回收的时间（毫秒）</summary>
        public int DeathRecycleDelayMs { get { return _g.DeathRecycleDelayMs > 0 ? _g.DeathRecycleDelayMs : 600; } }

        /// <summary>每帧最多重算路径次数，防止布塔时集中重算导致卡顿</summary>
        public int CheckOfflinePerFrame
        {
            get { return _g.CheckOfflinePerFrame > 0 ? _g.CheckOfflinePerFrame : 1; }
        }

        /// <summary>是否打印战斗自检日志</summary>
        public bool ShowDebugLog { get { return _g.ShowDebugLog != 0; } }

        // ==================================================================
        // 玩法 / 表现常量（来自本关 TBLevelRules；缺表时退回内置默认值，
        // 保证"表没导出来"也不会让游戏跑不起来）
        // ==================================================================

        /// <summary>棋盘格子边长（世界单位）。与美术 PPU 对齐：PPU=100 时取 1.0</summary>
        public float CellSize
        {
            get { return _r != null && _r.CellSize > 0f ? _r.CellSize : 1f; }
        }

        /// <summary>棋盘相对相机中心的留白（世界单位）</summary>
        public float BoardOriginPadding { get { return _r != null ? _r.BoardOriginPadding : 0f; } }

        /// <summary>未配 reward 时的默认击杀奖励（已被"小数掉落"取代，仅保留兼容）</summary>
        public int DefaultReward { get { return _r != null && _r.DefaultReward > 0 ? _r.DefaultReward : 5; } }

        /// <summary>未配 damageToPlayer 时的默认漏怪伤害</summary>
        public int DefaultDamageToPlayer
        {
            get { return _r != null && _r.DefaultDamageToPlayer > 0 ? _r.DefaultDamageToPlayer : 1; }
        }

        /// <summary>未配 bodyRadius 时的默认受击半径（格）</summary>
        public float DefaultBodyRadius
        {
            get { return _r != null && _r.DefaultBodyRadius > 0f ? _r.DefaultBodyRadius : 0.4f; }
        }

        /// <summary>未配 searchIntervalMs 时的默认索敌间隔（毫秒）</summary>
        public int DefaultSearchIntervalMs
        {
            get { return _r != null && _r.DefaultSearchIntervalMs > 0 ? _r.DefaultSearchIntervalMs : 100; }
        }

        /// <summary>
        /// 回合完成后自动开始下一回合的延迟（秒）。0 = 不自动，需手动点「下一回合」。
        /// 之所以留出间隔：玩家需要在两波之间布防/卖塔，直接连打会没有操作窗口。
        /// </summary>
        public float AutoNextRoundDelaySec
        {
            get { return Mathf.Max(0f, (_r != null ? _r.AutoNextRoundDelayMs : 2500) / 1000f); }
        }

        /// <summary>
        /// 关卡就绪后自动开始第一回合的延迟（秒）。0 = 等玩家点「开始」。
        /// 默认留 0：第一回合通常要留给玩家看地图 + 布防。
        /// </summary>
        public float AutoStartRoundDelaySec
        {
            get { return Mathf.Max(0f, (_r != null ? _r.AutoStartRoundDelayMs : 0) / 1000f); }
        }

        /// <summary>
        /// 售卖返还比例（乘在 TBTowerInfo.sellPrice 上）。
        /// 1.0 = 按配置值全额返还；<1 可以做出"卖塔有折损"的经济压力。
        /// </summary>
        public float SellRefundRate
        {
            get { return _r != null && _r.SellRefundRate > 0f ? _r.SellRefundRate : 1f; }
        }

        /// <summary>
        /// 怪物美术的默认朝向是否朝左。
        /// 本美术包的怪物都是朝左的（Head 在 -X、Tail 在 +X），所以向右移动时需要水平翻转。
        /// 做成常数是为了以后换美术包时不用改代码。
        /// </summary>
        public bool ArtFaceLeft { get { return _r == null || _r.ArtFaceLeft != 0; } }

        /// <summary>是否显示伤害飘字（关掉即整条链路短路，用于压测与低端机降级）</summary>
        public bool ShowDamageText { get { return _r == null || _r.ShowDamageText != 0; } }

        /// <summary>同一怪物两次伤害飘字的最小间隔（秒），防止高频攻击把屏幕刷满</summary>
        public float DamageTextThrottleSec
        {
            get { return Mathf.Max(0f, (_r != null ? _r.DamageTextThrottleMs : 120) / 1000f); }
        }

        /// <summary>屏幕震动幅度（世界单位）。0 = 不震。</summary>
        public float ShakeAmplitude { get { return Mathf.Max(0f, _r != null ? _r.ShakeAmplitude : 0.12f); } }

        /// <summary>屏幕震动持续时间（秒），0 = 不震。</summary>
        public float ShakeDurationSec { get { return Mathf.Max(0f, (_r != null ? _r.ShakeDurationMs : 180) / 1000f); } }

        public Global Raw { get { return _g; } }

        /// <summary>本关玩法常量行（可能为 null：表缺失或关卡 id 越界）</summary>
        public LevelRules RawRules { get { return _r; } }
    }
}
