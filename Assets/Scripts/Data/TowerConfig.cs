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

        /// <summary>
        /// 塔的招牌效果（与子弹共用 EffectType 编号，见该枚举注释）。
        /// 【为什么这里没有 int EffectType 属性】同名属性会**遮蔽枚举类型名**，
        /// 于是在本类内部写 EffectType.Laser 会被解析成"int 的成员"，报 CS1061。
        /// 与其到处写全限定名，不如只留一个语义明确的枚举属性。
        /// </summary>
        public EffectType Effect { get { return (EffectType)_t.EffectType; } }

        public float EffectValue { get { return _t.EffectValue; } }

        /// <summary>激光塔：瞬发命中（hitscan），不发射弹体</summary>
        public bool IsLaser { get { return Effect == EffectType.Laser; } }

        /// <summary>
        /// 范围攻击塔（强力塔，TowerType.Aoe）：弹体飞向"发射瞬间锁定的落点"，
        /// 到达即引爆，对落点半径内的**全部**敌人造成伤害 —— 不是单体攻击。
        ///
        /// 【判定依据】用 TowerType.Aoe，与 IsSlowAura 同一口径：这是**塔型级别**
        /// 的行为差异（发射的是"落点弹"而非"追踪弹"），不是命中效果差异。
        /// 底层仍靠子弹的 aoeRadius&gt;0 生效，此处属性供分类/自检/未来分支使用。
        /// </summary>
        public bool IsAoe { get { return Type == (int)TowerType.Aoe; } }

        /// <summary>
        /// 减速光环塔：**不发射子弹**，而是持续把射程内的所有敌人减速。
        ///
        /// 【为什么用 Type 而不是 Effect 判定】Effect 描述的是"命中后对单个目标做什么"，
        /// 减速塔改造后根本没有"命中"这个动作 —— 它的行为差异是**塔型级别**的
        /// （有无索敌/开火/转向），所以判定依据必须是 TowerType.Slow，
        /// 而不是 effectType=1（那个编号现在只用于 UI 分类展示与图例一致性）。
        /// </summary>
        public bool IsSlowAura { get { return Type == (int)TowerType.Slow; } }

        /// <summary>
        /// 本塔是否会生成弹体。激光塔与减速光环塔都不会。
        /// </summary>
        public bool FiresBullet { get { return !IsLaser && !IsSlowAura && _t.BulletId > 0; } }

        /// <summary>
        /// 是否可攻击飞行单位（TBTowerInfo.canAttackAir，1=可 / 0=不可）。
        ///
        /// 【为什么不是"缺省即可攻空"】这一列在表里是**每行都必须填**的：
        /// Luban 对空单元格给的是 0，与"显式填 0"无法区分。
        /// 与其在代码里猜，不如把它定义清楚 —— 表里的说明行已同步写明"留空视为 0"。
        /// 当前 15 行全部填 1；将来若要设计"对空专用塔"，把对应行改成 0 即可。
        /// </summary>
        public bool CanAttackAir { get { return _t.CanAttackAir != 0; } }

        public string Desc { get { return _t.Desc; } }

        public override string ToString()
        {
            return string.Format("TowerConfig(id={0}, name={1}, lv={2}, power={3}, radius={4}格)",
                Id, Name, Level, Power, RadiusGrid);
        }
    }
}
