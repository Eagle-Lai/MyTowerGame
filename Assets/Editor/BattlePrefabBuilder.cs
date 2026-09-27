using UnityEditor;
using UnityEngine;

namespace FTProject.EditorTools
{
    /// <summary>
    /// 生成战斗用预制体：子弹 + 全部怪物（P0-4）。
    ///
    /// 一、Bullet_Normal.prefab（从零创建）
    ///   极简结构：SpriteRenderer(圆点) + BaseBullet，约一格的四分之一
    ///
    /// 二、全部怪物
    ///   委托给 <see cref="MonsterPrefabBuilder"/>：它会把
    ///   `Assets/_UIAssets/Monsters/**` 下的每个怪物转成战斗预制体
    ///   （去物理 / 挂 BaseEnemy / 自适应血条）。
    ///
    /// 菜单：Tools ▸ 塔防 ▸ 3. 生成战斗预制体
    /// </summary>
    public static class BattlePrefabBuilder
    {
        public const string BulletPath = "Assets/Prefabs/Bullet/Bullet_Normal.prefab";

        private const string BulletSpriteKey = "Bullet_Dot";

        [MenuItem("Tools/塔防/3. 生成战斗预制体", false, 102)]
        public static void Build()
        {
            EditorUtil.Report report = new EditorUtil.Report();
            BuildInternal(report);
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();

            Debug.Log("[M0] 战斗预制体生成结果：\n" + report.Text);
            EditorUtility.DisplayDialog("生成战斗预制体",
                string.Format("{0}\n\n错误 {1} · 警告 {2}\n\n详见 Console。",
                    report.Errors > 0 ? "有错误，请查看 Console" : "完成",
                    report.Errors, report.Warnings), "好");
        }

        /// <summary>供一键向导调用（不弹窗）</summary>
        public static void BuildInternal(EditorUtil.Report report)
        {
            BuildBullet(report);
            MonsterPrefabBuilder.BuildAllInternal(report);
        }

        // ------------------------------------------------------------------
        // 子弹
        // ------------------------------------------------------------------

        private static void BuildBullet(EditorUtil.Report report)
        {
            report.Head("生成子弹预制体 → " + BulletPath);

            Sprite dot = AssetDatabase.LoadAssetAtPath<Sprite>(
                EditorUtil.GeneratedArtDir + "/" + BulletSpriteKey + ".png");
            if (dot == null)
            {
                report.Error("找不到子弹贴图，请先执行「1. 生成占位美术」");
                return;
            }

            AssetDatabase.DeleteAsset(BulletPath);
            EditorUtil.EnsureFolderOfFile(BulletPath);

            GameObject go = new GameObject("Bullet_Normal");
            SpriteRenderer sr = go.AddComponent<SpriteRenderer>();
            sr.sprite = dot;
            sr.sortingOrder = BoardSorting.Bullet;
            go.AddComponent<BaseBullet>();

            GameObject saved = PrefabUtility.SaveAsPrefabAsset(go, BulletPath);
            Object.DestroyImmediate(go);

            if (saved == null)
            {
                report.Error("保存失败：" + BulletPath);
                return;
            }
            Bounds b;
            if (EditorUtil.TryMeasureBounds(saved, out b))
            {
                report.Ok(string.Format("Bullet_Normal.prefab（SpriteRenderer + BaseBullet，直径 {0:F2} 世界单位）",
                    b.size.x));
            }
            else
            {
                report.Ok("Bullet_Normal.prefab（SpriteRenderer + BaseBullet）");
            }
        }
    }
}
