using UnityEngine;
using cfg;

namespace FTProject
{
    /// <summary>
    /// 怪物配置视图。
    /// 作用：把 Luban 生成的 EnemyData 包装成业务友好的形式，
    /// 并统一处理「字段缺失 → 取 TBGlobal 默认值」的兜底逻辑（需求 5：功能缺失不应阻塞）。
    ///
    /// 【2026-11-02 波型调节】新增一层「关卡 × 波型」缩放：
    ///   - 战斗用 -> `new EnemyConfig(d, WaveTuning)`，按当前关当前波型套倍率/加成；
    ///   - 看表用（图鉴、关卡详情预览）-> `new EnemyConfig(d)`，**不缩放**，
    ///     否则图鉴里的血量会随"上次进过哪一关"漂移。
    /// 【为什么不把 WaveTuning 存成字段】构造里已把 5 个值摊平成倍率/加成，
    ///   留着字段只会触发"未使用私有字段"告警，也会让人误以为可以中途换表。
    /// </summary>
    public class EnemyConfig
    {
        private readonly EnemyData _d;
        private readonly float _hpScale;
        private readonly float _speedScale;
        private readonly float _armorBonus;
        private readonly float _rewardScale;
        private readonly int _leakBonus;

        /// <summary>看表值（图鉴等）：不缩放</summary>
        public EnemyConfig(EnemyData d) : this(d, null) { }

        /// <summary>战斗用：按当前关 + 当前波型缩放</summary>
        public EnemyConfig(EnemyData d, WaveTuning t)
        {
            _d = d;
            bool air = d.IsFlying != 0;
            _hpScale = Positive(air ? t?.AirHpScale : t?.GroundHpScale);
            _speedScale = Positive(air ? t?.AirSpeedScale : t?.GroundSpeedScale);
            _armorBonus = air ? (t != null ? t.AirArmorBonus : 0f)
                              : (t != null ? t.GroundArmorBonus : 0f);
            _rewardScale = Positive(t?.KillGoldScale);
            _leakBonus = t != null ? t.LeakDamageBonus : 0;
        }

        /// <summary>
        /// 倍率兜底：null / ≤0 一律按 1。
        /// 【为什么不是 0】0 倍速的怪永远走不到终点、0 血的怪一碰就死，
        /// 这两种都只会表现为"关卡卡死"或"莫名其妙秒杀"，不是配置意图。
        /// </summary>
        private static float Positive(float? v) { return v.HasValue && v.Value > 0f ? v.Value : 1f; }

        public EnemyData Raw { get { return _d; } }

        public int Id { get { return _d.Id; } }
        public string Name { get { return _d.Name; } }

        /// <summary>战斗预制体资源名（对应 ResTable 逻辑名）</summary>
        public string ResName { get { return _d.ResName; } }

        public EnemyType Type { get { return (EnemyType)_d.Type; } }

        /// <summary>移动速度（格/秒）</summary>
        public float Speed { get { return _d.Speed * _speedScale; } }

        public float Hp { get { return _d.Hp * _hpScale; } }

        /// <summary>
        /// 护甲减伤 0~1（最终伤害 = 伤害 × (1 - Armor)）。
        /// 【必须 clamp】护甲是"加法加成"，配到 &gt;1 会让伤害变负数 —— 表现是塔打怪给怪回血。
        /// </summary>
        public float Armor { get { return Mathf.Clamp01(_d.Armor + _armorBonus); } }

        /// <summary>击杀奖励金币（小数）。【2026-10-29 flatdrop】改为 float：
        /// 每个变体给 0.16~1.40 的小数单价，由 PlayerDataManager 累加，满 1 才真正入账；
        /// 0 表示该变体确实不给金（当前 L01 已无 0 值变体）。不再回退 Global.DefaultReward。</summary>
        public float Reward
        {
            get { return _d.Reward * _rewardScale; }
        }

        /// <summary>
        /// 不含波型加成的漏怪伤害。
        /// 【为什么要单独暴露】漏怪震屏的幅度按"这一只有多疼"分级；若直接读加成后的值，
        /// 只要有人调 `leakDamageBonus`（经济/难度旋钮），屏幕抖动强度就会跟着变——
        /// 那不是调数值的人的意图，也违背"震幅口径不变"的约定。
        /// </summary>
        public int BaseDamageToPlayer
        {
            get { return _d.DamageToPlayer > 0 ? _d.DamageToPlayer : Configs.Global.DefaultDamageToPlayer; }
        }

        /// <summary>实际扣除的玩家生命（未配则取全局默认，再加波型加成）</summary>
        public int DamageToPlayer { get { return BaseDamageToPlayer + _leakBonus; } }

        /// <summary>显示缩放</summary>
        public float Scale { get { return _d.Scale > 0f ? _d.Scale : 1f; } }

        /// <summary>受击半径（格），索敌与命中判定用</summary>
        public float BodyRadius
        {
            get { return _d.BodyRadius > 0f ? _d.BodyRadius : Configs.Global.DefaultBodyRadius; }
        }

        /// <summary>是否飞行单位（地空倍率选择依据）</summary>
        public bool IsFlying { get { return _d.IsFlying != 0; } }

        /// <summary>AnimatorController 家族名（对应 _Common/Animations/&lt;名&gt;/Controller）</summary>
        public string AnimController { get { return _d.AnimController; } }

        public string Desc { get { return _d.Desc; } }

        public override string ToString()
        {
            return string.Format("EnemyConfig(id={0}, name={1}, hp={2}, spd={3})", Id, Name, Hp, Speed);
        }
    }
}
