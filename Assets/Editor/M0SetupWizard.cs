using System.IO;
using System.Text;
using SimpleJSON;
using UnityEditor;
using UnityEngine;

namespace FTProject.EditorTools
{
    /// <summary>
    /// M0 一键资源准备向导 + 交付自检。
    ///
    /// 【为什么要做成向导】
    ///   M0 的资源就绪化涉及 7 个步骤，且**顺序有依赖**（先有占位美术才能生成怪物血条；
    ///   先有 Tag 才能给 Canvas 打 Tag；先有预制体才能搭场景引用）。
    ///   让人按文档一步步点，漏一步就要花很久排查。向导把顺序固化下来，且每步都会
    ///   把结果汇总成一份报告，成功失败一目了然。
    ///
    /// 【为什么还要自检】
    ///   "工具跑完了"不等于"产物可用"。自检会把启用游戏前的所有前提条件过一遍
    ///   （配置表有没有导出、资源路径对不对、场景引用全不全、AB 有没有打），
    ///   把问题在按 Play 之前暴露出来。
    ///
    /// 菜单：
    ///   Tools ▸ 塔防 ▸ 0. 自检（先跑这个）
    ///   Tools ▸ 塔防 ▸ 一键完成 M0 资源准备
    /// </summary>
    public static class M0SetupWizard
    {
        [MenuItem("Tools/塔防/一键完成 M0 资源准备", false, 10)]
        public static void RunAll()
        {
            if (!EditorUtility.DisplayDialog("M0 一键资源准备",
                    "将依次执行：\n" +
                    "  1. 导出配置表（Luban，改完 Excel 后可整体重跑）\n" +
                    "  2. 配置工程设置（Tag / 渲染排序 / Build Settings / 物理）\n" +
                    "  3. 生成占位美术（格子 / 箭头 / 血条 / 子弹）\n" +
                    "  4. 转换防御塔预制体（UGUI → 世界空间 SpriteRenderer）\n" +
                    "  5. 生成战斗预制体（子弹 / 全部 119 个怪物）\n" +
                    "  6. 清理物理组件\n" +
                    "  7. 生成 UI 预制体（HUD / 提示）\n" +
                    "  8. 搭建 main 场景并接线\n" +
                    "  9. 按 ResTable 打 AssetBundle 标记\n\n" +
                    "注意：第 8 步会重建 main.unity（原文件会先备份到\n" +
                    "Assets/Scenes/_Backup/main_before_builder.unity）。\n\n是否继续？",
                    "开始执行", "取消"))
            {
                return;
            }

            EditorUtil.Report report = new EditorUtil.Report();
            report.Head("M0 一键资源准备（顺序执行，某步失败会继续后续步骤）");

            // 1. 导出配置表（Luban）—— 必须最先做：后面所有步骤都依赖表已就绪
            if (!LubanExporter.ExportInternal(report))
            {
                Debug.LogError("[M0] 导出配置表失败，已中止一键流程。\n" + report.Text);
                EditorUtility.DisplayDialog("M0 一键资源准备",
                    "中止：配置表导出失败。\n\n" + report.Text +
                    "\n\n（常见原因：Excel 被占用没保存 / 表结构改错）", "好");
                return;
            }

            // 2. 工程设置（必须在搭场景之前：Canvas 要打 UICanvas Tag）
            ProjectSettingsConfigurator.ConfigureInternal(report);

            // 2. 占位美术（必须在战斗预制体之前：怪物要挂血条）
            PlaceholderArtGenerator.GenerateInternal(report);

            // 3. 塔预制体
            TowerPrefabConverter.ConvertInternal(report);

            // 4. 战斗预制体
            BattlePrefabBuilder.BuildInternal(report);

            // 5. 物理清理（兜住前两步可能漏掉的）
            PhysicsComponentCleaner.CleanAllInternal(report);

            // 6. UI 预制体
            UIPrefabBuilder.BuildInternal(report);

            // 7. 场景
            SceneMainBuilder.BuildInternal(report);

            // 8. AB 打标（只打标不打包；真正的打包耗时较长，单独一个菜单）
            ABNameSetter.Apply(report);

            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();

            Debug.Log("[M0] 一键资源准备完成：\n" + report.Text);

            bool hasError = report.Errors > 0;
            bool buildAb = EditorUtility.DisplayDialog("M0 一键资源准备",
                string.Format("{0}\n错误 {1} · 警告 {2}\n\n完整报告已打印到 Console。\n\n" +
                              "{3}",
                    hasError ? "有错误，请先按报告修复" : "全部完成",
                    report.Errors, report.Warnings,
                    hasError
                        ? "请查看 Console 的 [M0] 开头日志。"
                        : "下一步建议：\n① 运行「Tools ▸ 塔防 ▸ 0. 自检」确认产物可用\n" +
                          "② 打开 Assets/Scenes/main.unity 按 Play 试跑（编辑器走直读模式，不需要打 AB）\n" +
                          "③ 需要验证真 AB 链路时，先点「8b. 打包 AssetBundle」，再加 FORCE_AB 宏"),
                "好", "顺便打包 AB");

            if (!buildAb)
            {
                BuildAssetBundles.Build();
            }
        }

        // ==================================================================
        // 自检
        // ==================================================================

        [MenuItem("Tools/塔防/0. 自检（先跑这个）", false, 9)]
        public static void SelfCheck()
        {
            EditorUtil.Report report = new EditorUtil.Report();
            report.Head("M0 交付自检（" + System.DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss") + "）");

            CheckConfigJson(report);
            CheckResources(report);
            CheckPrefabs(report);
            CheckScene(report);
            CheckProjectSettings(report);
            CheckBundles(report);

            report.Head("结论");
            if (report.Errors == 0 && report.Warnings == 0)
            {
                report.Ok("全部检查通过，可以直接 Play 试跑。");
            }
            else if (report.Errors == 0)
            {
                report.Ok(string.Format("无阻塞项，但有 {0} 条提醒（多数不影响运行）。", report.Warnings));
            }
            else
            {
                report.Error(string.Format("发现 {0} 个阻塞项，请按上面的 ✘ 逐条修复。", report.Errors));
            }

            Debug.Log("[M0] 自检报告：\n" + report.Text);
            EditorUtility.DisplayDialog("M0 自检",
                string.Format("错误 {0} · 警告 {1}\n\n详见 Console 的 [M0] 日志。",
                    report.Errors, report.Warnings), "好");
        }

        // ------------------------------------------------------------------
        // 各项检查
        // ------------------------------------------------------------------

        private static void CheckConfigJson(EditorUtil.Report report)
        {
            report.Head("① 配置表");
            string dir = BuildAssetBundles.ConfigDir;
            string[] expected =
            {
                "tbenemydata", "tbtowerinfo", "tbbulletdata", "tbenemylist",
                "tbrounddata", "tbsceneinfo", "tblevelmap", "tbglobal"
            };

            for (int i = 0; i < expected.Length; i++)
            {
                string path = dir + "/" + expected[i] + ".json";
                string full = Path.Combine(Directory.GetCurrentDirectory(), path);
                if (!File.Exists(full))
                {
                    report.Error(string.Format(
                        "{0}.json 缺失 —— 请执行 Luban/gen_code_json.bat 导出配置表", expected[i]));
                    continue;
                }
                try
                {
                    JSONNode node = JSONNode.Parse(File.ReadAllText(full, Encoding.UTF8));
                    int count = node != null && node.IsArray ? node.Count : (node != null && node.Count > 0 ? 1 : 0);
                    if (count == 0)
                    {
                        report.Warn(string.Format("{0}.json 没有任何记录", expected[i]));
                    }
                    else
                    {
                        report.Ok(string.Format("{0,-14} {1,3} 条", expected[i], count));
                    }
                }
                catch (System.Exception ex)
                {
                    report.Error(string.Format("{0}.json 解析失败：{1}", expected[i], ex.Message));
                }
            }
        }

        private static void CheckResources(EditorUtil.Report report)
        {
            report.Head("② 资源地址表（ResTable）");
            int total = 0;
            int missing = 0;

            foreach (System.Collections.Generic.KeyValuePair<string, ResAddress> kv in ResTable.All)
            {
                total++;
                ResAddress addr = kv.Value;

                // 配置表用 TextAsset 类型查：只有这样才真实反映"运行时能否读到内容"。
                // （踩过的坑：StreamingAssets 下的 .json 用 Object 查得到、用 TextAsset 查不到）
                bool exists = addr.Bundle == ResBundle.Config
                    ? AssetDatabase.LoadAssetAtPath<TextAsset>(addr.EditorPath) != null
                    : AssetDatabase.LoadAssetAtPath<Object>(addr.EditorPath) != null;

                if (!exists)
                {
                    missing++;
                    report.Error(string.Format("「{0}」指向的文件不存在或类型不对：{1}",
                        kv.Key, addr.EditorPath));
                }
            }

            if (missing == 0)
            {
                report.Ok(string.Format("登记 {0} 条资源全部就绪", total));
            }
        }

        private static void CheckPrefabs(EditorUtil.Report report)
        {
            report.Head("③ 关键预制体与组件");

            // 塔：必须世界空间 + 有炮管 + 有出膛点
            GameObject tower = AssetDatabase.LoadAssetAtPath<GameObject>(TowerPrefabConverter.TargetPath);
            if (tower == null)
            {
                report.Error("塔预制体不存在：" + TowerPrefabConverter.TargetPath +
                             "（请执行「2. 转换防御塔预制体」）");
            }
            else if (tower.GetComponent<RectTransform>() != null)
            {
                report.Error("Tower_Normal.prefab 仍是 UGUI（带 RectTransform），" +
                             "请执行「2. 转换防御塔预制体」");
            }
            else if (tower.GetComponentInChildren<SpriteRenderer>(true) == null)
            {
                report.Error("Tower_Normal.prefab 里没有 SpriteRenderer，无法显示");
            }
            else if (tower.transform.Find("barbette/Img_gun") == null)
            {
                report.Error("Tower_Normal.prefab 缺少 barbette/Img_gun 节点，" +
                             "BaseTower 找不到炮管，塔不会转向");
            }
            else if (tower.transform.Find("barbette/Img_gun/BarrelPoint") == null)
            {
                report.Warn("炮管下没有 BarrelPoint，子弹会从塔中心而不是枪口发出（不影响玩法）");
            }
            else
            {
                report.Ok("Tower_Normal.prefab：世界空间 SpriteRenderer + 炮管 + 出膛点");
            }
            if (tower != null && !HasScript(tower, "NormalTower"))
            {
                report.Error("Tower_Normal.prefab 上没有挂 NormalTower 脚本");
            }

            // 子弹
            GameObject bullet = AssetDatabase.LoadAssetAtPath<GameObject>(BattlePrefabBuilder.BulletPath);
            if (bullet == null)
            {
                report.Error("子弹预制体不存在：" + BattlePrefabBuilder.BulletPath);
            }
            else if (bullet.GetComponentInChildren<SpriteRenderer>(true) == null)
            {
                report.Error("Bullet_Normal.prefab 没有 SpriteRenderer");
            }
            else if (!HasScript(bullet, "BaseBullet"))
            {
                report.Error("Bullet_Normal.prefab 上没有挂 BaseBullet 脚本");
            }
            else
            {
                report.Ok("Bullet_Normal.prefab：SpriteRenderer + BaseBullet");
            }

            // 怪物：119 个逐个报太啰嗦 → 全量存在性检查 + 抽样结构检查
            int monsterTotal = MonsterCatalog.Count;
            int monsterMissing = 0;
            string firstMissing = null;
            for (int i = 0; i < monsterTotal; i++)
            {
                if (AssetDatabase.LoadAssetAtPath<GameObject>(MonsterCatalog.PrefabPath(i)) == null)
                {
                    monsterMissing++;
                    if (firstMissing == null)
                    {
                        firstMissing = MonsterCatalog.PrefabPath(i);
                    }
                }
            }
            if (monsterMissing > 0)
            {
                report.Error(string.Format(
                    "{0}/{1} 个怪物战斗预制体不存在（例：{2}）\n" +
                    "      修复：执行「Tools ▸ 塔防 ▸ 9. 导入全部怪物」",
                    monsterMissing, monsterTotal, firstMissing));
            }
            else
            {
                report.Ok(string.Format("{0} 个怪物战斗预制体全部存在", monsterTotal));
            }

            // 抽样检查结构（第 1 个 + 随机一个，避免只对第一个成立）
            if (monsterMissing == 0 && monsterTotal > 0)
            {
                CheckMonsterSample(report, 0);
                CheckMonsterSample(report, monsterTotal / 2);
                CheckMonsterSample(report, monsterTotal - 1);
            }
            // UI
            CheckUiPrefab(report, UIPrefabBuilder.HudPath, "HudView",
                new[] { "GoldText", "HpText", "RoundText", "StartButton", "TowerButton" });
            CheckUiPrefab(report, UIPrefabBuilder.TipsPath, "TipsView", new[] { "TipText" });
        }

        /// <summary>抽样检查某个怪物的战斗预制体结构</summary>
        private static void CheckMonsterSample(EditorUtil.Report report, int index)
        {
            string path = MonsterCatalog.PrefabPath(index);
            GameObject go = AssetDatabase.LoadAssetAtPath<GameObject>(path);
            if (go == null)
            {
                return;
            }
            string tag = System.IO.Path.GetFileName(path);

            if (!HasScript(go, "BaseEnemy"))
            {
                report.Error(tag + " 上没有挂 BaseEnemy 脚本");
            }
            if (go.GetComponentInChildren<Collider2D>(true) != null ||
                go.GetComponentInChildren<Collider>(true) != null ||
                go.GetComponentInChildren<Rigidbody2D>(true) != null ||
                go.GetComponentInChildren<Rigidbody>(true) != null)
            {
                report.Error(tag + " 上仍有物理组件（Collider/Rigidbody），" +
                             "请执行「9. 导入全部怪物」或「4b. 清理全部战斗预制体的物理组件」");
            }
            else if (go.transform.Find("HpBar/Fill") == null)
            {
                report.Error(tag + " 缺少 HpBar/Fill 节点，血条不会显示");
            }
            else
            {
                report.Ok(tag + "：BaseEnemy / 无物理组件 / HpBar 均就绪（抽样）");
            }
        }

        /// <summary>按类型名判断预制体上是否挂了某个脚本（不直接依赖运行时代码的类型，避免编辑器程序集耦合）</summary>
        private static bool HasScript(GameObject prefab, string typeName)
        {
            MonoBehaviour[] comps = prefab.GetComponentsInChildren<MonoBehaviour>(true);
            for (int i = 0; i < comps.Length; i++)
            {
                if (comps[i] != null && comps[i].GetType().Name == typeName)
                {
                    return true;
                }
            }
            return false;
        }

        private static void CheckUiPrefab(EditorUtil.Report report, string path, string rootName, string[] childNames)
        {
            GameObject go = AssetDatabase.LoadAssetAtPath<GameObject>(path);
            if (go == null)
            {
                report.Error("UI 预制体不存在：" + path + "（请执行「5. 生成 UI 预制体」）");
                return;
            }
            if (!HasScript(go, rootName))
            {
                report.Error(path + " 上没有挂 " + rootName + " 脚本");
            }
            int missing = 0;
            for (int i = 0; i < childNames.Length; i++)
            {
                if (go.transform.Find(childNames[i]) == null)
                {
                    missing++;
                    report.Error(string.Format(
                        "{0} 缺少子节点「{1}」—— {2}.cs 用 transform.Find 查找它，名字必须一致",
                        path, childNames[i], rootName));
                }
            }
            if (missing == 0)
            {
                report.Ok(Path.GetFileName(path) + "：节点齐备（" + string.Join(" / ", childNames) + "）");
            }
        }

        private static void CheckScene(EditorUtil.Report report)
        {
            report.Head("④ 主场景");
            string path = SceneMainBuilder.MainScenePath;
            string full = Path.Combine(Directory.GetCurrentDirectory(), path);
            if (!File.Exists(full))
            {
                report.Error("主场景不存在：" + path + "（请执行「7. 搭建 main 场景」）");
                return;
            }

            // 【注意】场景 YAML 里脚本引用是 GUID，不出现类名；能匹配的只有 GameObject 的
            // m_Name 与 m_TagString。所以这里只检查**对象名**，并用 "m_Name: X" 精确匹配，
            // 避免"Camera"这种词在别处偶然命中造成假通过。
            string text = File.ReadAllText(full, Encoding.UTF8);
            string[] requiredObjects =
            {
                "Camera", "EventSystem", "Launcher", "UICanvas",
                "BgPanel", "NormalPanel", "TipsPanel",
                "BattleRoot", "Background", "BoardRoot", "PathRoot",
                "TowerRoot", "EnemyRoot", "BulletRoot",
                "GameFlow", "GameSceneLauncher"
            };
            int missing = 0;
            for (int i = 0; i < requiredObjects.Length; i++)
            {
                if (!text.Contains("m_Name: " + requiredObjects[i]))
                {
                    missing++;
                    report.Error(path + " 中缺少对象「" + requiredObjects[i] + "」");
                }
            }
            if (missing == 0)
            {
                report.Ok(string.Format("场景包含全部 {0} 个必需对象", requiredObjects.Length));
            }

            // Canvas 的 Tag 必须真的写进了场景（UIManager 靠它查找）
            if (text.Contains("m_TagString: " + ProjectSettingsConfigurator.UiCanvasTag))
            {
                report.Ok("UICanvas 的 Tag 已正确写入场景");
            }
            else
            {
                report.Error("场景里没有任何对象带 Tag「" + ProjectSettingsConfigurator.UiCanvasTag +
                             "」，UIManager 找不到根 Canvas，UI 打不开");
            }
        }

        private static void CheckProjectSettings(EditorUtil.Report report)
        {
            report.Head("⑤ 工程设置");

            // Tag
            Object[] tagAssets = AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/TagManager.asset");
            bool hasTag = false;
            if (tagAssets != null && tagAssets.Length > 0)
            {
                SerializedObject so = new SerializedObject(tagAssets[0]);
                SerializedProperty tags = so.FindProperty("tags");
                if (tags != null)
                {
                    for (int i = 0; i < tags.arraySize; i++)
                    {
                        if (tags.GetArrayElementAtIndex(i).stringValue == ProjectSettingsConfigurator.UiCanvasTag)
                        {
                            hasTag = true;
                            break;
                        }
                    }
                }
            }
            if (hasTag)
            {
                report.Ok("Tag「UICanvas」已存在（UIManager 靠它找根 Canvas）");
            }
            else
            {
                report.Error("Tag「UICanvas」缺失，UI 打不开。请执行「6. 配置工程设置」");
            }

            // 渲染排序
            Object[] gsAssets = AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/GraphicsSettings.asset");
            bool sortOk = false;
            if (gsAssets != null && gsAssets.Length > 0)
            {
                SerializedObject so = new SerializedObject(gsAssets[0]);
                SerializedProperty mode = so.FindProperty("m_TransparencySortMode");
                SerializedProperty axis = so.FindProperty("m_TransparencySortAxis");
                if (mode != null && axis != null && mode.intValue == 3 &&
                    Mathf.Approximately(axis.vector3Value.y, -1f))
                {
                    sortOk = true;
                }
            }
            if (sortOk)
            {
                report.Ok("Transparency Sort Mode = Custom Axis (0,-1,0)（塔怪能按 Y 正确遮挡）");
            }
            else
            {
                report.Warn("Transparency Sort Mode 未设为 Custom Axis (0,-1,0)，" +
                            "塔与怪的前后遮挡关系会不可控。请执行「6. 配置工程设置」");
            }

            // Build Settings
            EditorBuildSettingsScene[] scenes = EditorBuildSettings.scenes;
            if (scenes == null || scenes.Length == 0)
            {
                report.Error("Build Settings 里没有任何场景，打包会失败");
            }
            else if (scenes.Length > 1)
            {
                report.Warn(string.Format("Build Settings 里有 {0} 个场景，M0 只需要 main.unity", scenes.Length));
            }
            else if (scenes[0].path != SceneMainBuilder.MainScenePath)
            {
                report.Warn("Build Settings 的首个场景不是 main.unity：" + scenes[0].path);
            }
            else
            {
                report.Ok("Build Settings：仅 main.unity");
            }
        }

        private static void CheckBundles(EditorUtil.Report report)
        {
            report.Head("⑥ AssetBundle（编辑器试跑不需要，出包/验证 AB 时才需要）");
            string dir = ResPathUtil.BuildOutputRoot;
            if (!Directory.Exists(dir))
            {
                report.Warn("尚未打包过 AB（" + dir + "）。编辑器下走直读模式可以正常试跑，" +
                            "但出真机包之前必须执行「8b. 打包 AssetBundle」");
                return;
            }

            for (int i = 0; i < ResBundle.All.Length; i++)
            {
                string file = Path.Combine(dir, ResBundle.All[i]);
                if (File.Exists(file))
                {
                    report.Ok(string.Format("{0,-16} {1,8:F1} KB", ResBundle.All[i],
                        new FileInfo(file).Length / 1024f));
                }
                else
                {
                    // 降级为提示：编辑器试跑走直读模式，不需要 AB；
                    // 而且新增了 16 个怪物家族包后，旧的一次打包结果必然"缺"它们。
                    report.Warn("包缺失：" + ResBundle.All[i] +
                                "（出真机包前重新执行「8b. 打包 AssetBundle」即可全部产出）");
                }
            }
            string manifest = Path.Combine(dir, ResPathUtil.ManifestBundleName);
            if (!File.Exists(manifest))
            {
                report.Error("主清单缺失：" + ResPathUtil.ManifestBundleName);
            }
        }
    }
}
