using UnityEngine;
using cfg;

namespace FTProject
{
    /// <summary>
    /// 怪物配置视图。
    /// 作用：把 Luban 生成的 EnemyData 包装成业务友好的形式，
    /// 并统一处理「字段缺失 → 取 TBGlobal 默认值」的兜底逻辑（需求 5：功能缺失不应阻塞）。
    /// </summary>
    public class EnemyConfig
    {
        private readonly EnemyData _d;

        public EnemyConfig(EnemyData d)
        {
            _d = d;
        }

        public EnemyData Raw { get { return _d; } }

        public int Id { get { return _d.Id; } }
        public string Name { get { return _d.Name; } }

        /// <summary>战斗预制体资源名（对应 ResTable 逻辑名）</summary>
        public string ResName { get { return _d.ResName; } }

        public EnemyType Type { get { return (EnemyType)_d.Type; } }

        /// <summary>移动速度（格/秒）</summary>
        public float Speed { get { return _d.Speed; } }

        public float Hp { get { return _d.Hp; } }

        /// <summary>护甲减伤 0~1（最终伤害 = 伤害 × (1 - Armor)）</summary>
        public float Armor { get { return Mathf.Clamp01(_d.Armor); } }

        /// <summary>击杀奖励金币（未配则取全局默认）</summary>
        public int Reward
        {
            get { return _d.Reward > 0 ? _d.Reward : Configs.Global.DefaultReward; }
        }

        /// <summary>漏怪扣除的玩家生命（未配则取全局默认）</summary>
        public int DamageToPlayer
        {
            get { return _d.DamageToPlayer > 0 ? _d.DamageToPlayer : Configs.Global.DefaultDamageToPlayer; }
        }

        /// <summary>显示缩放</summary>
        public float Scale { get { return _d.Scale > 0f ? _d.Scale : 1f; } }

        /// <summary>受击半径（格），索敌与命中判定用</summary>
        public float BodyRadius
        {
            get { return _d.BodyRadius > 0f ? _d.BodyRadius : Configs.Global.DefaultBodyRadius; }
        }

        /// <summary>是否飞行单位（M0 全为 false）</summary>
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
