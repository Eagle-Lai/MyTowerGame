namespace FTProject
{
    /// <summary>
    /// 减速防御塔（type=3）。
    ///
    /// 【命名对齐】枚举 TowerType 里叫 Slow，资源名/节点名用 Retard，两者是同一件事：
    ///   TowerType.Slow(3)  ⇄  "Tower_Retard" / "Btn_Tower_Retard" / 美术目录 "Retard"
    /// 映射集中在 HudView.TowerTypeOfNode / TowerConfig.Type，避免散落各处。
    ///
    /// 差异化行为由 effectType/effectValue 配置驱动，本类保持为空。
    ///
    /// 【为什么单独成文件】Unity 要求 MonoBehaviour 的类名与文件名一致。
    /// </summary>
    public class RetardTower : BaseTower
    {
    }
}
