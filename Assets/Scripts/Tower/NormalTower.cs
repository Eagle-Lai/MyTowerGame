namespace FTProject
{
    /// <summary>
    /// 普通防御塔（type=1，可攻击飞行与行走两类怪物）。
    ///
    /// 差异化行为（AOE / 减速光环）由 TBTowerInfo.effectType 与 TBBulletData 驱动，
    /// 也就是说**新增塔型主要靠配置，而不是新增子类**。本类目前是空的，
    /// 留作需要塔特有逻辑时的扩展点。
    ///
    /// 【为什么单独成文件】Unity 要求 MonoBehaviour 的类名与文件名一致，
    /// 否则该组件拿不到 MonoScript、无法被 AddComponent 出来、也无法序列化进 prefab。
    /// Editor 脚本要把本组件挂到 Tower_Normal.prefab 上，因此必须独立成文件。
    /// </summary>
    public class NormalTower : BaseTower
    {
    }
}
