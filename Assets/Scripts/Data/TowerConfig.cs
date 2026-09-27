using UnityEngine;
using cfg;

namespace FTProject
{
    /// <summary>索敌策略（对应 TBTowerInfo.targetMode）</summary>
    public enum TargetMode
    {
        /// <summary>路径进度最靠前（最危险）优先 —— 塔防标准策略，默认</summary>
        FurthestAlongPath = 0,
        /// <summary>距离自身最近优先</summary>
        Nearest = 1,
        /// <summary>当前血量最高优先</summary>
        HighestHp = 2,
    }

    /// <summary>
    /// 防御塔配置视图（TBTowerInfo 的一行 = 某个塔的某个等级）。
    /// </summary>
    public class TowerConfig
    {
        private readonly TowerInfo _t;

        public TowerConfig(TowerInfo t)
        {
            _t = t;
        }

        public TowerInfo Raw { get { return _t; } }

        public int Id { get { return _t.Id; } }

        /// <summary>塔类型（1 单体 / 2 AOE / 3 减速 / 4 穿透 / 5 激光）</summary>
        public int Type { get { return _t.Type; } }

        public string Name { get { return _t.Name; } }

        /// <summary>AB 资源名（对应 ResTable 逻辑名）</summary>
        public string ResName { get { return _t.ResName; } }

        public int Level { get { return _t.Level; } }

        /// <summary>攻击半径（格）</summary>
        public float RadiusGrid { get { return _t.Radius; } }

        /// <summary>攻击半径（世界单位）。塔是圆形判定，用格数 × 格子尺寸。</summary>
        public float RadiusWorld { get { return _t.Radius * Configs.Global.CellSize; } }

        /// <summary>攻击力（每次命中的基础伤害）</summary>
        public float Power { get { return _t.Power; } }

        /// <summary>攻击间隔（秒）。表里单位是毫秒，此处已换算。</summary>
        public float CooldownSec { get { return Mathf.Max(0.01f, _t.CD / 1000f); } }

        /// <summary>本等级的建造/升级价格（增量价：level1 为建造价，level2/3 为升级价）</summary>
        public int Prices { get { return _t.Prices; } }

        /// <summary>出售返还金币</summary>
        public int SellPrice { get { return _t.SellPrice; } }

        public int BulletId { get { return _t.BulletId; } }

        public TargetMode TargetMode { get { return (TargetMode)_t.TargetMode; } }

        /// <summary>索敌间隔（秒），节流用</summary>
        public float SearchIntervalSec
        {
            get
            {
                int ms = _t.SearchIntervalMs > 0 ? _t.SearchIntervalMs : Configs.Global.DefaultSearchIntervalMs;
                return ms / 1000f;
            }
        }

        /// <summary>炮管转向速度（度/秒）</summary>
        public float RotateSpeed { get { return _t.RotateSpeed > 0f ? _t.RotateSpeed : 360f; } }

        /// <summary>下一等级 id，0 表示满级（M2 接升级链用）</summary>
        public int UpgradeTo { get { return _t.UpgradeTo; } }

        public bool IsMaxLevel { get { return _t.UpgradeTo <= 0; } }

        public int EffectType { get { return _t.EffectType; } }

        public float EffectValue { get { return _t.EffectValue; } }

        public string Desc { get { return _t.Desc; } }

        public override string ToString()
        {
            return string.Format("TowerConfig(id={0}, name={1}, lv={2}, power={3}, radius={4}格)",
                Id, Name, Level, Power, RadiusGrid);
        }
    }
}
