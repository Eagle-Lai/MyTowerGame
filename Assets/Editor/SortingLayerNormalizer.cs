using System.Text;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;

namespace FTProject.EditorTools
{
    /// <summary>
    /// 渲染层级标准化 / 体检（2026-10-21）。
    ///
    /// 【为什么需要这个工具】
    ///   层级约定写在 <see cref="BoardSorting"/> 里，但**资产是另一套事实**：
    ///   敌人预制体是从美术包 Instantiate 来的，源包自带的 SortingGroup 序并不统一
    ///   （实测 119 个里 88 个是 200，其余 31 个是 0/1/2/3/4、100–104、201–204），
    ///   塔预制体则根本没有 SortingGroup。只看代码会以为层级是对的。
    ///   所以约定必须能被"跑一次菜单"落到资产上，并且能被独立校验。
    ///
    /// 【约定（与 BoardSorting 一一对应）】
    ///   排序层：Bg < Main < Pop（层优先级高于层内 sortingOrder）
    ///   Main 层：Cell 0 → PathArrow 10 → RangeIndicator 100 → Tower 200 → Enemy 300 → FireFx 400
    ///   （400 槽位沿用 BoardSorting.Bullet，现由枪口焰/爆炸使用；真实子弹已于 2026-10-31 删除）
    ///   塔：根 SortingGroup = 200；组内 barbette 0 / Img_gun 1 / 枪口焰 2
    ///   怪：根 SortingGroup = 300；组内血条 Bg 500 / Fill 501（必须压过美术部件，最大 99）
    ///   背景：Bg 层，序 0
    ///
    /// 【为什么怪必须大于塔】
    ///   塔防刚需：怪走到塔下方（更靠近镜头）时必须盖住塔。
    ///   塔在上会表现为"怪的头被塔底座吃掉"——2026-10-21 定案：永远怪压塔。
    /// </summary>
    public static class SortingLayerNormalizer
    {
        private const string EnemyDir = "Assets/Prefabs/Enemy";
        private const string TowerDir = "Assets/Prefabs/Tower";
        private const string TowerBackupDir = "Assets/Prefabs/Tower/_UI_Source";
        private const string MainScenePath = "Assets/Scenes/Main.unity";
        private const string BackgroundName = "Background";

        // ------------------------------------------------------------------
        // 菜单：标准化（会改资产）
        // ------------------------------------------------------------------

        /// <summary>
        /// 菜单入口：把全部敌人/塔/子弹预制体与主场景背景的排序落到约定值上。
        /// **幂等**：已经正确的资产不会被改动（内部仍会重存一次，值不变）。
        /// 不弹窗（工程规范：编辑器脚本走 Debug.Log）。
        /// </summary>
        [MenuItem("Tools/塔防/高级（单步重建）/标准化渲染层级（预置体+场景）", false, 318)]
        public static void Normalize()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode)
            {
                Debug.LogError("[Sorting] 请先退出 Play Mode 再执行：播放态下改预制体会在退出时被丢弃。");
                return;
            }

            var log = new StringBuilder();
            int enemies = NormalizeEnemies(log);
            int towers = NormalizeTowers(log);
            bool scene = NormalizeScene(log);

            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();

            Debug.Log(string.Format(
                "[Sorting] 标准化完成：敌人 {0} 个 / 塔 {1} 个 / 场景背景 {2}\n{3}",
                enemies, towers, scene ? "已改" : "无需改", log));
        }

        private static int NormalizeEnemies(StringBuilder log)
        {
            int count = 0;
            string[] paths = CollectPrefabs(EnemyDir);
            for (int i = 0; i < paths.Length; i++)
            {
                string path = paths[i];
                GameObject root = PrefabUtility.LoadPrefabContents(path);
                try
                {
                    SortingGroup group = root.GetComponent<SortingGroup>();
                    if (group == null)
                    {
                        group = root.AddComponent<SortingGroup>();
                        log.AppendLine("  + 补 SortingGroup：" + path);
                    }
                    if (group.sortingOrder != BoardSorting.Enemy || group.sortingLayerName != BoardSorting.LayerMain)
                    {
                        log.AppendLine(string.Format("  ~ {0} 组序 {1}/{2} → {3}/{4}",
                            System.IO.Path.GetFileName(path), group.sortingLayerName, group.sortingOrder,
                            BoardSorting.LayerMain, BoardSorting.Enemy));
                    }
                    group.sortingLayerName = BoardSorting.LayerMain;
                    group.sortingOrder = BoardSorting.Enemy;

                    // 组内渲染器统一到 Main（组本来就覆盖层，但显式写死便于人看与后续拆组）
                    SpriteRenderer[] renderers = root.GetComponentsInChildren<SpriteRenderer>(true);
                    for (int r = 0; r < renderers.Length; r++)
                    {
                        renderers[r].sortingLayerName = BoardSorting.LayerMain;
                    }

                    Transform bar = root.transform.Find("HpBar");
                    if (bar == null)
                    {
                        log.AppendLine("  ! 找不到 HpBar：" + path);
                    }
                    else
                    {
                        SetSpriteOrder(bar, "Bg", BoardSorting.EnemyHpBarBack);
                        SetSpriteOrder(bar, "Fill", BoardSorting.EnemyHpBarFill);
                    }

                    PrefabUtility.SaveAsPrefabAsset(root, path);
                    count++;
                }
                finally
                {
                    PrefabUtility.UnloadPrefabContents(root);
                }
            }
            return count;
        }

        private static int NormalizeTowers(StringBuilder log)
        {
            int count = 0;
            string[] paths = CollectPrefabs(TowerDir);
            for (int i = 0; i < paths.Length; i++)
            {
                string path = paths[i];
                if (path.Replace('\\', '/').StartsWith(TowerBackupDir)) continue;

                GameObject root = PrefabUtility.LoadPrefabContents(path);
                try
                {
                    SortingGroup group = root.GetComponent<SortingGroup>();
                    if (group == null)
                    {
                        group = root.AddComponent<SortingGroup>();
                        log.AppendLine("  + 补 SortingGroup：" + path);
                    }
                    group.sortingLayerName = BoardSorting.LayerMain;
                    group.sortingOrder = BoardSorting.Tower;

                    SpriteRenderer[] renderers = root.GetComponentsInChildren<SpriteRenderer>(true);
                    for (int r = 0; r < renderers.Length; r++)
                    {
                        renderers[r].sortingLayerName = BoardSorting.LayerMain;
                    }

                    // 组内相对序号：炮座在下、炮管在上（枪口焰运行时挂到 BarrelPoint，序 2）
                    Transform barbette = root.transform.Find("barbette");
                    if (barbette == null)
                    {
                        log.AppendLine("  ! 找不到 barbette：" + path);
                    }
                    else
                    {
                        SetSpriteOrder(barbette, null, BoardSorting.TowerBody);
                        SetSpriteOrder(barbette, "Img_gun", BoardSorting.TowerBarrel);
                    }

                    PrefabUtility.SaveAsPrefabAsset(root, path);
                    count++;
                }
                finally
                {
                    PrefabUtility.UnloadPrefabContents(root);
                }
            }
            return count;
        }

        /// <summary>
        /// 背景改用 Bg 排序层。
        /// **不强制打开场景**：Main.unity 没打开就以 Additive 方式临时打开、改完保存再关掉，
        /// 避免把用户正在编辑的其它场景挤掉。
        /// </summary>
        private static bool NormalizeScene(StringBuilder log)
        {
            Scene scene = SceneManager.GetSceneByPath(MainScenePath);
            bool openedHere = false;
            if (!scene.IsValid() || !scene.isLoaded)
            {
                scene = EditorSceneManager.OpenScene(MainScenePath, OpenSceneMode.Additive);
                openedHere = true;
            }
            if (!scene.IsValid())
            {
                log.AppendLine("  ! 打不开主场景：" + MainScenePath);
                return false;
            }

            bool changed = false;
            try
            {
                GameObject[] roots = scene.GetRootGameObjects();
                for (int i = 0; i < roots.Length; i++)
                {
                    SpriteRenderer[] renderers = roots[i].GetComponentsInChildren<SpriteRenderer>(true);
                    for (int r = 0; r < renderers.Length; r++)
                    {
                        SpriteRenderer sr = renderers[r];
                        if (sr.gameObject.name != BackgroundName) continue;
                        if (sr.sortingLayerName == BoardSorting.LayerBg
                            && sr.sortingOrder == BoardSorting.Background) continue;
                        sr.sortingLayerName = BoardSorting.LayerBg;
                        sr.sortingOrder = BoardSorting.Background;
                        changed = true;
                        log.AppendLine("  ~ 场景背景 → " + BoardSorting.LayerBg + "/" + BoardSorting.Background);
                    }
                }
                if (changed) EditorSceneManager.SaveScene(scene);
            }
            finally
            {
                if (openedHere) EditorSceneManager.CloseScene(scene, true);
            }
            return changed;
        }

        // ------------------------------------------------------------------
        // 菜单：体检（只读）
        // ------------------------------------------------------------------

        /// <summary>
        /// 只读体检：把资产与 <see cref="BoardSorting"/> 的偏差逐条打到 Console。
        /// </summary>
        [MenuItem("Tools/塔防/校验/渲染层级体检（只读）", false, 401)]
        public static void Audit()
        {
            var problems = new StringBuilder();
            int issue = AuditFindings(problems);
            if (issue == 0) Debug.Log("[Sorting] 体检通过，无层级偏差。\n" + problems);
            else Debug.LogWarning(string.Format("[Sorting] 体检发现 {0} 处偏差：\n{1}", issue, problems));
        }

        /// <summary>
        /// 体检的核心：偏差写进 <paramref name="sb"/>，返回问题数。
        /// 同时供「校验 ▸ 渲染层级体检」与「0. 自检」调用 —— 任何重建脚本把层级冲掉，
        /// 标准自检都会报出来。只在内存里读预制体，不实例化、不保存。
        /// </summary>
        public static int AuditFindings(StringBuilder sb)
        {
            int issue = 0;

            SortingLayer[] layers = SortingLayer.layers;
            var names = new StringBuilder();
            for (int i = 0; i < layers.Length; i++)
            {
                if (i > 0) names.Append(" < ");
                names.Append(layers[i].name);
            }
            sb.AppendLine("  排序层（低 → 高）：" + names);

            if (layers.Length != 4)
            {
                sb.AppendLine(string.Format("  ! 排序层应为 4 个（Default/Bg/Main/Pop），实际 {0} 个", layers.Length));
                issue++;
            }

            // 敌人
            string[] enemies = CollectPrefabs(EnemyDir);
            int badGroup = 0, badBar = 0;
            for (int i = 0; i < enemies.Length; i++)
            {
                GameObject prefab = AssetDatabase.LoadAssetAtPath<GameObject>(enemies[i]);
                if (prefab == null) continue;
                SortingGroup group = prefab.GetComponent<SortingGroup>();
                if (group == null || group.sortingOrder != BoardSorting.Enemy
                    || group.sortingLayerName != BoardSorting.LayerMain)
                {
                    badGroup++;
                    if (badGroup <= 12) sb.AppendLine("  ! 组序不对：" + enemies[i] + " = " + Describe(group));
                }
                Transform bar = prefab.transform.Find("HpBar");
                if (bar == null) { badBar++; continue; }
                if (!OrderIs(bar, "Bg", BoardSorting.EnemyHpBarBack)
                    || !OrderIs(bar, "Fill", BoardSorting.EnemyHpBarFill)) badBar++;
            }
            if (badGroup > 0) issue += badGroup;
            if (badBar > 0) issue += badBar;
            sb.AppendLine(string.Format("  敌人：{0} 个，组序错 {1}，血条序错 {2}", enemies.Length, badGroup, badBar));

            // 塔
            string[] towers = CollectPrefabs(TowerDir);
            int badTower = 0, towerCount = 0;
            for (int i = 0; i < towers.Length; i++)
            {
                if (towers[i].Replace('\\', '/').StartsWith(TowerBackupDir)) continue;
                towerCount++;
                GameObject prefab = AssetDatabase.LoadAssetAtPath<GameObject>(towers[i]);
                if (prefab == null) continue;
                SortingGroup group = prefab.GetComponent<SortingGroup>();
                if (group == null || group.sortingOrder != BoardSorting.Tower
                    || group.sortingLayerName != BoardSorting.LayerMain)
                {
                    badTower++;
                    if (badTower <= 12) sb.AppendLine("  ! 塔组序不对：" + towers[i] + " = " + Describe(group));
                    continue;
                }
                Transform barbette = prefab.transform.Find("barbette");
                if (barbette == null || !OrderIs(barbette, null, BoardSorting.TowerBody)
                    || !OrderIs(barbette, "Img_gun", BoardSorting.TowerBarrel))
                {
                    badTower++;
                    if (badTower <= 12) sb.AppendLine("  ! 塔内序不对：" + towers[i]);
                }
            }
            if (badTower > 0) issue += badTower;
            sb.AppendLine(string.Format("  塔：{0} 个，有问题 {1}", towerCount, badTower));

            // 场景背景（仅当 Main 已加载）
            Scene scene = SceneManager.GetSceneByPath(MainScenePath);
            if (scene.IsValid() && scene.isLoaded)
            {
                GameObject[] roots = scene.GetRootGameObjects();
                bool found = false;
                for (int i = 0; i < roots.Length; i++)
                {
                    SpriteRenderer[] rs = roots[i].GetComponentsInChildren<SpriteRenderer>(true);
                    for (int r = 0; r < rs.Length; r++)
                    {
                        if (rs[r].gameObject.name != BackgroundName) continue;
                        found = true;
                        if (rs[r].sortingLayerName != BoardSorting.LayerBg
                            || rs[r].sortingOrder != BoardSorting.Background)
                        {
                            issue++;
                            sb.AppendLine("  ! 场景背景层级不对：" + Describe(rs[r]));
                        }
                    }
                }
                if (!found) sb.AppendLine("  · 场景里没找到 Background（可能重建过场景）");
            }
            else
            {
                sb.AppendLine("  · Main.unity 未打开，跳过场景背景检查");
            }

            return issue;
        }

        // ------------------------------------------------------------------
        // 工具方法
        // ------------------------------------------------------------------

        private static string[] CollectPrefabs(string dir)
        {
            string[] guids = AssetDatabase.FindAssets("t:Prefab", new[] { dir });
            var paths = new string[guids.Length];
            for (int i = 0; i < guids.Length; i++)
            {
                paths[i] = AssetDatabase.GUIDToAssetPath(guids[i]);
            }
            return paths;
        }

        /// <summary>childName 传 null 表示 parent 自身。</summary>
        private static void SetSpriteOrder(Transform parent, string childName, int order)
        {
            Transform t = childName == null ? parent : parent.Find(childName);
            if (t == null)
            {
                Debug.LogWarning("[Sorting] 缺少节点：" + parent.name + "/" + childName);
                return;
            }
            SpriteRenderer sr = t.GetComponent<SpriteRenderer>();
            if (sr == null) return;
            sr.sortingLayerName = BoardSorting.LayerMain;
            sr.sortingOrder = order;
        }

        private static bool OrderIs(Transform parent, string childName, int order)
        {
            Transform t = childName == null ? parent : parent.Find(childName);
            if (t == null) return false;
            SpriteRenderer sr = t.GetComponent<SpriteRenderer>();
            return sr != null && sr.sortingOrder == order;
        }

        private static string Describe(SortingGroup g)
        {
            return g == null ? "无 SortingGroup" : g.sortingLayerName + "/" + g.sortingOrder;
        }

        private static string Describe(SpriteRenderer sr)
        {
            return sr == null ? "无 SpriteRenderer" : sr.sortingLayerName + "/" + sr.sortingOrder;
        }
    }
}
