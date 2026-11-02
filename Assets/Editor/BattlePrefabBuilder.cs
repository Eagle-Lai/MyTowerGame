using UnityEditor;
using UnityEngine;

namespace FTProject.EditorTools
{
    /// <summary>
    /// 生成战斗用预制体：全部怪物（P0-4）。
    ///
    /// 委托给 <see cref="MonsterPrefabBuilder"/>：它会把
    /// `Assets/_UIAssets/Monsters/**` 下的每个怪物转成战斗预制体
    /// （去物理 / 挂 BaseEnemy / 自适应血条）。
    ///
    /// 【2026-10-31 移除子弹预制体】这里原先还生成 Bullet_Normal.prefab。
    /// 真实子弹系统已于 2026-10-17 废止（塔改成即时命中，伤害在落点直接结算），
    /// 该预制体、BaseBullet、BulletManager 与 bullet_normal 包一并删除，
    /// 本工具只剩怪物这一件事。
    ///
    /// 菜单：Tools ▸ 塔防 ▸ 高级（单步重建）▸ 生成战斗预制体
    /// </summary>
    public static class BattlePrefabBuilder
    {
        [MenuItem("Tools/塔防/高级（单步重建）/生成战斗预制体", false, 302)]
        public static void Build()
        {
            EditorUtil.Report report = new EditorUtil.Report();
            BuildInternal(report);
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();

            Debug.Log(report.Errors > 0
                ? "[M0] 战斗预制体生成有错误：\n" + report.Text
                : "[M0] 战斗预制体生成完成：\n" + report.Text);
        }

        /// <summary>供一键向导调用（不弹窗）</summary>
        public static void BuildInternal(EditorUtil.Report report)
        {
            MonsterPrefabBuilder.BuildAllInternal(report);
        }
    }
}
