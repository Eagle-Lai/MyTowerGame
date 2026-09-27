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
}
