namespace FTProject
{
    /// <summary>
    /// 减速防御塔（type=3）。
    ///
    /// 【M3 起行为是**范围光环**，不再发射子弹】曾经的实现是"发射减速弹、打中某只怪才减速"，
    /// 现在改为：不索敌、不转向、不发射子弹 —— 持续把**射程内的所有敌人**减速。
    ///   · 结算：BaseTower.TickSlowAura（按 CD 节拍遍历空间哈希，逐个 ApplySlow）
    ///   · 表现：SlowAuraView（常亮射程圈 + 命中脉冲）
    /// 判定依据是 TowerConfig.IsSlowAura（即 Type==3），**不是** effectType ——
    /// 塔表里保留的 effectType=1 只用于 UI 分类与图例口径。
    ///
    /// 【命名对齐】枚举 TowerType 里叫 Slow，资源名/节点名用 Retard，两者是同一件事：
    ///   TowerType.Slow(3)  ⇄  "Tower_Retard0|1|2" / "Btn_Tower_Retard" / 美术目录 "retard"
    /// 映射集中在 HudView.TowerTypeOfNode / TowerConfig.Type，避免散落各处。
    ///
    /// 【为什么单独成文件】Unity 要求 MonoBehaviour 的类名与文件名一致。
    /// </summary>
    public class RetardTower : BaseTower
    {
    }
}
