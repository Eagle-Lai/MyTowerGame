using UnityEngine;
using cfg;

namespace FTProject
{
    /// <summary>
    /// 子弹配置视图。
    /// 2D 塔防下子弹行为完全配置化（速度/命中半径/存活时间/穿透/爆炸）。
    /// </summary>
    public class BulletConfig
    {
        private readonly BulletData _b;

        public BulletConfig(BulletData b)
        {
            _b = b;
        }

        public BulletData Raw { get { return _b; } }

        public int Id { get { return _b.Id; } }
        public string Name { get { return _b.Name; } }
        public string ResName { get { return _b.ResName; } }

        /// <summary>飞行速度（格/秒）</summary>
        public float Speed { get { return _b.Speed; } }

        /// <summary>命中判定半径（格）。命中条件：子弹与目标距离 &lt;= HitRadius</summary>
        public float HitRadius { get { return _b.HitRadius > 0f ? _b.HitRadius : 0.2f; } }

        /// <summary>最大存活时间（秒），超时回收，防止"追不上的子弹"永久存在</summary>
        public float LifeTimeSec
        {
            get { return (_b.LifeTimeMs > 0 ? _b.LifeTimeMs : 3000) / 1000f; }
        }

        /// <summary>穿透数量，0 = 命中即消失</summary>
        public int Pierce { get { return _b.Pierce; } }

        /// <summary>爆炸半径（格），0 = 单体伤害</summary>
        public float AoeRadius { get { return _b.AoeRadius; } }

        /// <summary>
        /// 命中时施加的效果（与塔表共用一套编号，见 EffectType 枚举注释）。
        /// **子弹的 effectType 是命中效果的权威来源**；塔的 effectType 只用于分类与激光判定。
        /// </summary>
        public EffectType Effect { get { return (EffectType)_b.EffectType; } }

        /// <summary>
        /// 效果参数。语义随 Effect 变化：
        ///   减速 → 减速比例 0~1；持续伤害 → 每秒伤害；范围伤害 → 不使用（半径看 AoeRadius）。
        /// 塔自身 effectValue > 0 时会**覆盖**本值（减速塔三级因此可以各不相同）。
        /// </summary>
        public float EffectValue { get { return _b.EffectValue; } }

        public float Scale { get { return _b.Scale > 0f ? _b.Scale : 1f; } }

        public string Desc { get { return _b.Desc; } }

        /// <summary>
        /// 高速穿透自检：若单帧位移超过命中直径，可能"穿过"目标而漏判。
        /// 调用方可据此告警或降低子弹速度。
        /// </summary>
        public bool IsSpeedSafeAtFps(float fps)
        {
            if (fps <= 0f)
            {
                return true;
            }
            return Speed / fps < HitRadius * 2f;
        }

        public override string ToString()
        {
            return string.Format("BulletConfig(id={0}, name={1}, speed={2}, hitR={3})",
                Id, Name, Speed, HitRadius);
        }
    }
}
