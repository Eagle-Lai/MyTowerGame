namespace FTProject
{
    /// <summary>
    /// 强力防御塔（type=2）。
    ///
    /// 与 NormalTower 一样，差异化行为由 TBTowerInfo / TBBulletData 配置驱动，
    /// 本身保持为空 —— 只有需要"该类塔独有的运行时逻辑"时才在这里加代码。
    ///
    /// 【为什么单独成文件】Unity 要求 MonoBehaviour 的类名与文件名一致，
    /// 否则该组件拿不到 MonoScript、无法被 AddComponent 出来、也无法序列化进 prefab。
    /// </summary>
    public class PowerTower : BaseTower
    {
    }
}
