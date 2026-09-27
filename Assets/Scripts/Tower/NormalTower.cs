namespace FTProject
{
    /// <summary>
    /// 普通防御塔（M0 唯一的塔型）。
    ///
    /// 差异化行为（AOE / 减速 / 激光）由 TBTowerInfo.effectType 与 TBBulletData 驱动，
    /// 也就是说**新增塔型主要靠配置，而不是新增子类**。本类目前是空的，
    /// 留作 M2 需要塔特有逻辑（例如激光的持续伤害）时的扩展点。
    ///
    /// 【为什么单独成文件】Unity 要求 MonoBehaviour 的类名与文件名一致，
    /// 否则该组件拿不到 MonoScript、无法被 AddComponent 出来、也无法序列化进 prefab。
    /// Editor 脚本要把本组件挂到 Tower_Normal.prefab 上，因此必须独立成文件。
    /// </summary>
    public class NormalTower : BaseTower
    {
    }
}
