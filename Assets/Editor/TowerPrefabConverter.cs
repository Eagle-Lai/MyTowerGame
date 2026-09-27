using UnityEditor;
using UnityEngine;

namespace FTProject.EditorTools
{
    /// <summary>
    /// 把防御塔预制体从 **UGUI** 转成 **世界空间 SpriteRenderer**（P0-4）。
    ///
    /// 【为什么要转】
    ///   原工程：塔是 UGUI（RectTransform + Image，Layer 5），怪物是 SpriteRenderer。
    ///   两套渲染体系混用会导致三个硬伤：
    ///     ① 塔和怪无法按 Y 坐标互相遮挡（塔防的刚需：怪走到塔下方应盖住塔）
    ///     ② 坐标要维护"UI 局部坐标"与"世界坐标"双轨，任何换算都会成为 bug 温床
    ///     ③ 点击/拖拽交互要写两套实现
    ///   而 119 个怪物 prefab 是分部件骨骼式结构，转 UGUI 成本高且无收益；
    ///   塔只有 1 个 prefab，转 SpriteRenderer 几乎零成本。故统一到 SpriteRenderer。
    ///
    /// 【产物层级】（BaseTower 依赖的名字，不能改）
    ///   Tower_Normal                     根，挂 NormalTower，scale 0.8
    ///   └── barbette                     炮座（SpriteRenderer, sortingOrder 300）
    ///       └── Img_gun                  炮管（SpriteRenderer, sortingOrder 301）
    ///           └── BarrelPoint          出膛点（BaseTower 取它作为子弹出生位置）
    ///
    /// 【原 UGUI 版会先备份】到 Assets/Prefabs/Tower/_UI_Source/，便于回退对照。
    ///
    /// 菜单：Tools ▸ 塔防 ▸ 2. 转换防御塔预制体
    /// </summary>
    public static class TowerPrefabConverter
    {
        public const string TargetPath = "Assets/Prefabs/Tower/Tower_Normal.prefab";
        public const string BackupPath = "Assets/Prefabs/Tower/_UI_Source/Tower_Normal_UI.prefab";

        private const string BaseSpritePath = "Assets/_UIAssets/Tower/Normal/turret_base_128.png";
        private const string BarrelSpritePath = "Assets/_UIAssets/Tower/Normal/turret_barrel_128.png";

        /// <summary>塔根节点缩放：128px 贴图 = 1.28 世界单位，0.8 后约 1.02，正好一格</summary>
        private const float RootScale = 0.8f;

        /// <summary>炮管出膛点相对炮管中心的距离（炮管本地单位）</summary>
        private const float MuzzleOffset = 0.6f;

        [MenuItem("Tools/塔防/2. 转换防御塔预制体", false, 101)]
        public static void Convert()
        {
            EditorUtil.Report report = new EditorUtil.Report();
            bool ok = ConvertInternal(report);
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();

            Debug.Log("[M0] 防御塔转换结果：\n" + report.Text);
            EditorUtility.DisplayDialog("转换防御塔预制体",
                string.Format("{0}\n\n{1}", ok ? "完成" : "有错误，请查看 Console", report.Text), "好");
        }

        /// <summary>供一键向导调用（不弹窗）</summary>
        public static bool ConvertInternal(EditorUtil.Report report)
        {
            report.Head("转换防御塔预制体 → " + TargetPath);

            if (AssetDatabase.LoadAssetAtPath<GameObject>(TargetPath) == null)
            {
                report.Error("找不到源预制体：" + TargetPath);
                return false;
            }

            Sprite baseSprite = AssetDatabase.LoadAssetAtPath<Sprite>(BaseSpritePath);
            Sprite barrelSprite = AssetDatabase.LoadAssetAtPath<Sprite>(BarrelSpritePath);
            if (baseSprite == null || barrelSprite == null)
            {
                report.Error(string.Format(
                    "塔身贴图缺失或未被导入为 Sprite：\n    base={0} ({1})\n    barrel={2} ({3})",
                    BaseSpritePath, baseSprite == null ? "null" : "ok",
                    BarrelSpritePath, barrelSprite == null ? "null" : "ok"));
                return false;
            }

            BackupSource(report);

            // ---- 先删旧资产再重建，避免残留子节点 ----
            AssetDatabase.DeleteAsset(TargetPath);
            EditorUtil.EnsureFolderOfFile(TargetPath);

            GameObject root = new GameObject("Tower_Normal");
            root.transform.localScale = new Vector3(RootScale, RootScale, 1f);

            GameObject barbette = new GameObject("barbette");
            barbette.transform.SetParent(root.transform, false);
            AddSprite(barbette, baseSprite, BoardSorting.Tower);

            // 炮管挂在炮座下：炮座不动，炮管绕自身 pivot 旋转（美术把 pivot 定在炮管旋转中心）
            GameObject gun = new GameObject("Img_gun");
            gun.transform.SetParent(barbette.transform, false);
            AddSprite(gun, barrelSprite, BoardSorting.Tower + 1);

            // 出膛点：必须在炮管贴图**原生指向**的那一端。
            // 【为什么是 +Y 而不是 +X】炮管贴图（turret_barrel_128.png）是**竖着画**的：
            //   上窄下宽、枪口在图像顶部 ⇒ 本地 +Y 方向。之前放在 (+MuzzleOffset, 0)
            //   是按"炮管朝 +X"的假设写的，结果子弹从炮管侧面冒出来，
            //   与炮管指向差了 90°（和 BaseTower.BarrelNativeAngle 是同一件事的两面）。
            // 炮管旋转时 BarrelPoint 作为子节点跟着转，所以这里只要放对本地位置即可。
            GameObject muzzle = new GameObject("BarrelPoint");
            muzzle.transform.SetParent(gun.transform, false);
            muzzle.transform.localPosition = new Vector3(0f, MuzzleOffset, 0f);

            root.AddComponent<NormalTower>();

            GameObject saved = PrefabUtility.SaveAsPrefabAsset(root, TargetPath);
            Object.DestroyImmediate(root);

            if (saved == null)
            {
                report.Error("保存预制体失败：" + TargetPath);
                return false;
            }

            report.Ok("已生成世界空间版（根 scale " + RootScale + "，barbette 300 / Img_gun 301）");
            report.Ok("层级：Tower_Normal → barbette → Img_gun → BarrelPoint");

            Bounds b;
            if (EditorUtil.TryMeasureBounds(saved, out b))
            {
                report.Ok(string.Format("实测显示尺寸：宽 {0:F2} × 高 {1:F2} 世界单位（格子 1.0）",
                    b.size.x, b.size.y));
            }
            return true;
        }

        /// <summary>把原 UGUI 版另存一份，便于回退与对照</summary>
        private static void BackupSource(EditorUtil.Report report)
        {
            if (AssetDatabase.LoadAssetAtPath<GameObject>(BackupPath) != null)
            {
                report.Ok("原 UGUI 版备份已存在，跳过：" + BackupPath);
                return;
            }
            if (!AssetDatabase.CopyAsset(TargetPath, BackupPath))
            {
                report.Warn("原 UGUI 版备份失败（不影响转换）：" + BackupPath);
                return;
            }
            report.Ok("原 UGUI 版已备份到 " + BackupPath);
        }

        private static void AddSprite(GameObject go, Sprite sprite, int sortingOrder)
        {
            SpriteRenderer sr = go.AddComponent<SpriteRenderer>();
            sr.sprite = sprite;
            sr.sortingOrder = sortingOrder;
            sr.color = Color.white;
        }
    }
}
