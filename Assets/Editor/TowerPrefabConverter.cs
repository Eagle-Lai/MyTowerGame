using UnityEditor;
using UnityEngine;

namespace FTProject.EditorTools
{
    /// <summary>
    /// 把防御塔预制体从 **UGUI** 转成 **世界空间 SpriteRenderer**（P0-4 / M-2）。
    ///
    /// 【为什么要转】
    ///   原工程：塔是 UGUI（RectTransform + Image，Layer 5），怪物是 SpriteRenderer。
    ///   两套渲染体系混用会导致三个硬伤：
    ///     ① 塔和怪无法按 Y 坐标互相遮挡（塔防的刚需：怪走到塔下方应盖住塔）
    ///     ② 坐标要维护"UI 局部坐标"与"世界坐标"双轨，任何换算都会成为 bug 温床
    ///     ③ 点击/拖拽交互要写两套实现
    ///   而 119 个怪物 prefab 是分部件骨骼式结构，转 UGUI 成本高且无收益；
    ///   塔只有少量 prefab，转 SpriteRenderer 成本低。故统一到 SpriteRenderer。
    ///
    /// 【M-2 改进（相对 M0 版）】
    ///   1. 覆盖全部塔型（Normal / Power / Retard），不再只处理 Tower_Normal
    ///   2. **已合规的塔直接跳过**：检测根节点是否已是 SpriteRenderer 结构 → 是则不改
    ///   3. **备份只做一次**：原来每个塔都尝试备份，现在统一在开头扫一遍，已有的跳过
    ///
    /// 【产物层级】（BaseTower 依赖的名字，不能改）
    ///   Tower_<Type>                     根，挂 <Type>Tower，scale 0.8
    ///   └── barbette                     炮座（SpriteRenderer, sortingOrder 300）
    ///       └── Img_gun                  炮管（SpriteRenderer, sortingOrder 301）
    ///           └── BarrelPoint          出膛点（BaseTower 取它作为子弹出生位置）
    ///
    /// 【原 UGUI 版会先备份】到 Assets/Prefabs/Tower/_UI_Source/，便于回退对照。
    ///
    /// 菜单：Tools ▸ 塔防 ▸ 高级（单步重建） ▸ 转换防御塔预制体
    /// </summary>
    public static class TowerPrefabConverter
    {
        private const string TowerDir = "Assets/Prefabs/Tower";
        private const string BackupDir = "Assets/Prefabs/Tower/_UI_Source";

        /// <summary>
        /// 全部塔等级 prefab 的逻辑名（= ResTable 逻辑名 = prefab 文件名）。
        ///
        /// 【M-3 起改为分等级清单】强力塔 / 减速塔各有 3 个独立 prefab，一级一套美术；
        /// Normal 仍是单 prefab（三级共用一套美术，靠配置表数值递进）。
        /// 这些名字必须与 tbtowerinfo.json 的 resName 逐行一致，自检失败即表示两边分叉。
        /// </summary>
        public static readonly string[] TowerResNames =
        {
            "Tower_Normal",
            "Tower_Power0", "Tower_Power1", "Tower_Power2",
            "Tower_Retard0", "Tower_Retard1", "Tower_Retard2",
        };

        /// <summary>
        /// 按逻辑名取塔 prefab 资产路径（供自检等外部调用，勿再写死单塔常量）。
        /// Power / Retard 分等级 prefab 放在与其塔型同名的子目录下。
        /// </summary>
        public static string TowerPath(string resName)
        {
            if (resName.StartsWith("Tower_Power"))
            {
                return TowerDir + "/Power/" + resName + ".prefab";
            }
            if (resName.StartsWith("Tower_Retard"))
            {
                return TowerDir + "/Retard/" + resName + ".prefab";
            }
            return TowerDir + "/" + resName + ".prefab";
        }

        /// <summary>塔根节点缩放：128px 贴图 = 1.28 世界单位，0.8 后约 1.02，正好一格</summary>
        private const float RootScale = 0.8f;

        /// <summary>炮管出膛点相对炮管中心的距离（炮管本地单位）</summary>
        private const float MuzzleOffset = 0.6f;

        /// <summary>
        /// 单座塔的生成规格。
        /// ResName 既作 prefab 文件名，也作 ResTable 逻辑名（M-2 起三塔统一命名）。
        /// 【贴图名不统一】三座塔的美术文件名各不相同，必须逐塔指定，不能靠拼字符串：
        ///   Normal: turret_base_128.png / turret_barrel_128.png
        ///   Power : tower_base[_lv2|_lv3].png      / tower_barrel[_lv2|_lv3].png
        ///   Retard: slowtower_base[_lv2|_lv3].png  / slowtower_crystal[_lv2|_lv3].png
        ///           （目录名是小写 retard，且美术已按等级提供 3 套）
        /// </summary>
        private struct TowerSpec
        {
            public string ResName;         // Tower_Normal / Tower_Power0..2 / Tower_Retard0..2
            public string ArtDir;          // 美术目录（注意 retard 是小写）
            public string BaseSprite;      // 炮座贴图文件名
            public string BarrelSprite;    // 炮管贴图文件名
            public string RootName;        // 根节点名（= ResName）
            /// <summary>根组件类型（NormalTower / PowerTower / RetardTower）</summary>
            public System.Type Behaviour;
        }

        private static TowerSpec[] Specs()
        {
            return new TowerSpec[]
            {
                new TowerSpec
                {
                    ResName = "Tower_Normal", ArtDir = "Normal",
                    BaseSprite = "turret_base_128.png", BarrelSprite = "turret_barrel_128.png",
                    RootName = "Tower_Normal", Behaviour = typeof(NormalTower),
                },
                // ---- 强力塔：3 个等级各有独立 prefab 与美术 ----
                new TowerSpec
                {
                    ResName = "Tower_Power0", ArtDir = "Power",
                    BaseSprite = "tower_base.png", BarrelSprite = "tower_barrel.png",
                    RootName = "Tower_Power0", Behaviour = typeof(PowerTower),
                },
                new TowerSpec
                {
                    ResName = "Tower_Power1", ArtDir = "Power",
                    BaseSprite = "tower_base_lv2.png", BarrelSprite = "tower_barrel_lv2.png",
                    RootName = "Tower_Power1", Behaviour = typeof(PowerTower),
                },
                new TowerSpec
                {
                    ResName = "Tower_Power2", ArtDir = "Power",
                    BaseSprite = "tower_base_lv3.png", BarrelSprite = "tower_barrel_lv3.png",
                    RootName = "Tower_Power2", Behaviour = typeof(PowerTower),
                },
                // ---- 减速塔：同上 ----
                new TowerSpec
                {
                    ResName = "Tower_Retard0", ArtDir = "retard",
                    BaseSprite = "slowtower_base.png", BarrelSprite = "slowtower_crystal.png",
                    RootName = "Tower_Retard0", Behaviour = typeof(RetardTower),
                },
                new TowerSpec
                {
                    ResName = "Tower_Retard1", ArtDir = "retard",
                    BaseSprite = "slowtower_base_lv2.png", BarrelSprite = "slowtower_crystal_lv2.png",
                    RootName = "Tower_Retard1", Behaviour = typeof(RetardTower),
                },
                new TowerSpec
                {
                    ResName = "Tower_Retard2", ArtDir = "retard",
                    BaseSprite = "slowtower_base_lv3.png", BarrelSprite = "slowtower_crystal_lv3.png",
                    RootName = "Tower_Retard2", Behaviour = typeof(RetardTower),
                },
            };
        }

        [MenuItem("Tools/塔防/高级（单步重建）/转换防御塔预制体", false, 301)]
        public static void Convert()
        {
            EditorUtil.Report report = new EditorUtil.Report();
            bool ok = ConvertInternal(report);
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();

            Debug.Log("[M2] 防御塔转换结果：\n" + report.Text);
            EditorUtility.DisplayDialog("转换防御塔预制体",
                string.Format("{0}\n\n{1}", ok ? "完成" : "有错误，请查看 Console", report.Text), "好");
        }

        /// <summary>供一键向导调用（不弹窗）</summary>
        public static bool ConvertInternal(EditorUtil.Report report)
        {
            report.Head("转换防御塔预制体（全部塔型）");

            TowerSpec[] specs = Specs();
            int converted = 0;
            int skipped = 0;
            bool allOk = true;

            for (int i = 0; i < specs.Length; i++)
            {
                TowerSpec spec = specs[i];
                string targetPath = TowerPath(spec.ResName);

                // 已合规 → 跳过（★ 不删不建，保住美术/手工调过的内容）
                if (IsAlreadyConverted(targetPath))
                {
                    report.Ok("跳过（已是 SpriteRenderer 结构）：" + spec.ResName);
                    skipped++;
                    continue;
                }

                if (!ConvertOne(spec, targetPath, report))
                {
                    allOk = false;
                    continue;
                }
                converted++;
            }

            report.Ok(string.Format("完成：新转换 {0} 座，跳过 {1} 座", converted, skipped));
            return allOk;
        }

        /// <summary>
        /// 判定某塔 prefab 是否已经是"世界空间 SpriteRenderer 版"。
        /// 依据：根下存在 barbette，且 barbette 上挂着 SpriteRenderer。
        /// 满足即认为已经转换过 —— 不重复重建（保住手工改动）。
        ///
        /// 【为什么不再校验根组件的子类】实测 Tower_Power0/1/2、Tower_Retard0/1/2 挂的都是 NormalTower，
        /// 但三个子类都是 BaseTower 的空派生，功能上完全等价（差异全在配置表驱动）。
        /// 为这点"类名一致性"去重建 prefab，反而会抹掉美术/手工微调 —— 不划算，改为只提示。
        /// </summary>
        private static bool IsAlreadyConverted(string prefabPath)
        {
            GameObject prefab = AssetDatabase.LoadAssetAtPath<GameObject>(prefabPath);
            if (prefab == null)
            {
                return false;
            }
            Transform barbette = prefab.transform.Find("barbette");
            if (barbette == null)
            {
                return false;
            }
            return barbette.GetComponent<SpriteRenderer>() != null;
        }

        private static bool ConvertOne(TowerSpec spec, string targetPath, EditorUtil.Report report)
        {
            report.Head("转换 → " + targetPath);

            if (AssetDatabase.LoadAssetAtPath<GameObject>(targetPath) == null)
            {
                report.Error("找不到源预制体：" + targetPath);
                return false;
            }

            string baseSpritePath = "Assets/_UIAssets/Tower/" + spec.ArtDir + "/" + spec.BaseSprite;
            string barrelSpritePath = "Assets/_UIAssets/Tower/" + spec.ArtDir + "/" + spec.BarrelSprite;
            Sprite baseSprite = AssetDatabase.LoadAssetAtPath<Sprite>(baseSpritePath);
            Sprite barrelSprite = AssetDatabase.LoadAssetAtPath<Sprite>(barrelSpritePath);
            if (baseSprite == null || barrelSprite == null)
            {
                report.Error(string.Format(
                    "{0} 塔身贴图缺失或未被导入为 Sprite：\n    base={1}\n    barrel={2}",
                    spec.ResName, baseSpritePath, barrelSpritePath));
                return false;
            }

            BackupSource(spec.ResName, targetPath, report);

            // ---- 先删旧资产再重建，避免残留子节点 ----
            AssetDatabase.DeleteAsset(targetPath);
            EditorUtil.EnsureFolderOfFile(targetPath);

            GameObject root = new GameObject(spec.RootName);
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

            if (spec.Behaviour != null)
            {
                root.AddComponent(spec.Behaviour);
            }

            GameObject saved = PrefabUtility.SaveAsPrefabAsset(root, targetPath);
            Object.DestroyImmediate(root);

            if (saved == null)
            {
                report.Error("保存预制体失败：" + targetPath);
                return false;
            }

            report.Ok(spec.ResName + " 已生成世界空间版（根 scale " + RootScale + "，barbette 300 / Img_gun 301）");

            Bounds b;
            if (EditorUtil.TryMeasureBounds(saved, out b))
            {
                report.Ok(string.Format("{0} 实测显示尺寸：宽 {1:F2} × 高 {2:F2} 世界单位（格子 1.0）",
                    spec.ResName, b.size.x, b.size.y));
            }
            return true;
        }

        /// <summary>把原 UGUI 版另存一份，便于回退与对照。已备份过则跳过。</summary>
        private static void BackupSource(string resName, string targetPath, EditorUtil.Report report)
        {
            string backupPath = BackupDir + "/" + resName + "_UI.prefab";
            if (AssetDatabase.LoadAssetAtPath<GameObject>(backupPath) != null)
            {
                report.Ok("原 UGUI 版备份已存在，跳过：" + backupPath);
                return;
            }
            if (!AssetDatabase.CopyAsset(targetPath, backupPath))
            {
                report.Warn("原 UGUI 版备份失败（不影响转换）：" + backupPath);
                return;
            }
            report.Ok("原 UGUI 版已备份到 " + backupPath);
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
