using cfg;
using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 全局参数配置（TBGlobal 单行表）。
    /// 把原先散落在 GlobalConst / TowerCofig 里的硬编码集中到配置表。
    /// </summary>
    public class GlobalConfig
    {
        private readonly Global _g;

        public GlobalConfig(Global g)
        {
            _g = g;
        }

        /// <summary>棋盘格子边长（世界单位）。与美术 PPU 对齐：PPU=100 时取 1.0</summary>
        public float CellSize { get { return _g.CellSize > 0f ? _g.CellSize : 1f; } }

        /// <summary>棋盘相对相机中心的留白（世界单位）</summary>
        public float BoardOriginPadding { get { return _g.BoardOriginPadding; } }

        public int EnemyPoolSize { get { return _g.EnemyPoolSize > 0 ? _g.EnemyPoolSize : 64; } }
        public int BulletPoolSize { get { return _g.BulletPoolSize > 0 ? _g.BulletPoolSize : 128; } }

        /// <summary>同屏怪物上限（性能保护）</summary>
        public int MaxEnemyAlive { get { return _g.MaxEnemyAlive > 0 ? _g.MaxEnemyAlive : 200; } }

        /// <summary>未配 reward 时的默认击杀奖励</summary>
        public int DefaultReward { get { return _g.DefaultReward > 0 ? _g.DefaultReward : 5; } }

        /// <summary>未配 damageToPlayer 时的默认漏怪伤害</summary>
        public int DefaultDamageToPlayer
        {
            get { return _g.DefaultDamageToPlayer > 0 ? _g.DefaultDamageToPlayer : 1; }
        }

        /// <summary>未配 bodyRadius 时的默认受击半径（格）</summary>
        public float DefaultBodyRadius
        {
            get { return _g.DefaultBodyRadius > 0f ? _g.DefaultBodyRadius : 0.4f; }
        }

        /// <summary>未配 searchIntervalMs 时的默认索敌间隔（毫秒）</summary>
        public int DefaultSearchIntervalMs
        {
            get { return _g.DefaultSearchIntervalMs > 0 ? _g.DefaultSearchIntervalMs : 100; }
        }

        public int TargetFrameRate { get { return _g.TargetFrameRate > 0 ? _g.TargetFrameRate : 60; } }

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
        // 玩法常数
        // （本表是全工程唯一的常数配置表，新增常数都加在这里，见 Global.xlsx 的注释行）
        // ==================================================================

        /// <summary>
        /// 回合完成后自动开始下一回合的延迟（秒）。0 = 不自动，需手动点「下一回合」。
        /// 之所以留出间隔：玩家需要在两波之间布防/卖塔，直接连打会没有操作窗口。
        /// </summary>
        public float AutoNextRoundDelaySec
        {
            get { return Mathf.Max(0f, _g.AutoNextRoundDelayMs / 1000f); }
        }

        /// <summary>
        /// 关卡就绪后自动开始第一回合的延迟（秒）。0 = 等玩家点「开始」。
        /// 默认留 0：第一回合通常要留给玩家看地图 + 布防。
        /// </summary>
        public float AutoStartRoundDelaySec
        {
            get { return Mathf.Max(0f, _g.AutoStartRoundDelayMs / 1000f); }
        }

        /// <summary>
        /// 售卖返还比例（乘在 TBTowerInfo.sellPrice 上）。
        /// 1.0 = 按配置值全额返还；<1 可以做出"卖塔有折损"的经济压力。
        /// </summary>
        public float SellRefundRate
        {
            get { return _g.SellRefundRate > 0f ? _g.SellRefundRate : 1f; }
        }

        /// <summary>
        /// 怪物美术的默认朝向是否朝左。
        /// 本美术包的怪物都是朝左的（Head 在 -X、Tail 在 +X），所以向右移动时需要水平翻转。
        /// 做成常数是为了以后换美术包时不用改代码。
        /// </summary>
        public bool ArtFaceLeft { get { return _g.ArtFaceLeft != 0; } }

        // ==================================================================
        // 表现层常数（M2 打击感）
        // ==================================================================

        /// <summary>是否显示伤害飘字（关掉即整条链路短路，用于压测与低端机降级）</summary>
        public bool ShowDamageText { get { return _g.ShowDamageText != 0; } }

        /// <summary>同一怪物两次伤害飘字的最小间隔（秒），防止高频攻击把屏幕刷满</summary>
        public float DamageTextThrottleSec
        {
            get { return Mathf.Max(0f, _g.DamageTextThrottleMs / 1000f); }
        }

        /// <summary>屏幕震动幅度（世界单位）。0 = 不震。</summary>
        public float ShakeAmplitude { get { return Mathf.Max(0f, _g.ShakeAmplitude); } }

        /// <summary>屏幕震动持续时间（秒），0 = 不震。</summary>
        public float ShakeDurationSec { get { return Mathf.Max(0f, _g.ShakeDurationMs / 1000f); } }

        public Global Raw { get { return _g; } }
    }
}
