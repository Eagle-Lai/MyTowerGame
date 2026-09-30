namespace FTProject
{
    /// <summary>
    /// 怪物类型。
    ///
    /// 【v2.1 说明】类型标签只用于分类展示与筛选（例如后续做"只攻击地面单位"的塔），
    /// **不再驱动资源选择** —— 资源一律由 TBEnemyData.resName 决定，
    /// 这样新增一种怪只需加一行配置，不用改代码、不用加枚举。
    ///
    /// 原来的 PointType / BulletType / EnemyState / TowerBuildState / BulletState 已移除：
    ///   - PointType/TowerBuildState 属于已废弃的 Node/Obstacle 3D 节点体系
    ///   - BulletState 定义在 BaseBullet.cs（与使用处相邻，便于维护）
    ///   - EnemyState 与新的 EnemyAnimState（Animator 的 int 参数 State）语义重复
    /// </summary>
    public enum EnemyType
    {
        NONE = 0,
        /// <summary>普通地面单位</summary>
        Normal = 1,
        /// <summary>快速单位</summary>
        Quick = 2,
        /// <summary>重甲单位</summary>
        Armored = 3,
        /// <summary>飞行单位（M0 未启用）</summary>
        Flying = 4,
        /// <summary>Boss</summary>
        Boss = 5,
    }

    /// <summary>
    /// 特殊效果类型。**塔表与子弹表共用这一套编号**（图例写在两张 xlsx 的第 3 行注释里）。
    ///
    /// 【为什么塔和子弹共用一个枚举】两处各写一套编号，迟早会出现
    /// "表里填 2 以为在说 AOE、代码里 2 却当成持续伤害"这类只有运行时才暴露的错。
    /// 共用一个枚举 + 一份图例，是这个项目里成本最低的一致性保障。
    ///
    /// 【谁说了算】真正的**命中效果**以子弹的 effectType 为准；
    /// 塔的 effectType 用于①分类展示 ②判定激光（Laser 走 hitscan，不发射弹体）。
    /// 效果**强度**：塔的 effectValue > 0 时覆盖子弹的 effectValue，否则用子弹自己的 ——
    /// 这样减速塔三级（0.5/0.6/0.7）能各自不同，而 AOE/穿透塔不必重复填。
    /// </summary>
    public enum EffectType
    {
        /// <summary>无特殊效果</summary>
        None = 0,
        /// <summary>减速：effectValue = 减速比例 0~1（实际速度 = 原速 × (1 - effectValue)）</summary>
        Slow = 1,
        /// <summary>持续伤害：effectValue = 每秒伤害</summary>
        Dot = 2,
        /// <summary>范围伤害：半径由子弹的 aoeRadius 决定</summary>
        Aoe = 3,
        /// <summary>激光：瞬发命中，不生成弹体</summary>
        Laser = 4,
    }
}
