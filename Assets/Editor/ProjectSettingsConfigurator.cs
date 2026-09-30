using System.Collections.Generic;
using UnityEditor;
using UnityEngine;

namespace FTProject.EditorTools
{
    /// <summary>
    /// 一次性配好工程级设置（P0-4）。
    ///
    /// 这些设置**必须**在跑游戏之前配好，否则会以很隐晦的方式出错：
    ///
    ///  ① Transparency Sort Mode = Custom Axis (0,-1,0)
    ///     这是 2D 游戏"靠下的物体盖住靠上的"的实现方式。
    ///     不设的话，怪物和塔之间谁盖谁完全看渲染顺序（不可控），
    ///     典型症状是"怪走到塔前面却被塔挡住了"。
    ///
    ///  ② Tag: UICanvas
    ///     UIManager 通过 GameObject.FindGameObjectWithTag("UICanvas") 找根 Canvas。
    ///     没有这个 Tag 会直接报错、整个 UI 打不开。
    ///
    ///  ③ Build Settings 只保留 main.unity
    ///     原工程指向已删除的 Launcher/Start/Main 三个场景，打包会失败。
    ///
    ///  ④ 关闭物理自动模拟（Physics / Physics2D）
    ///     我们已经完全不用物理，关掉可以让 Profiler 的 Physics 分区稳定为 0，
    ///     这就是需求 8 的量化验收标准。
    ///
    /// 菜单：Tools ▸ 塔防 ▸ 2. 配置工程设置
    /// </summary>
    public static class ProjectSettingsConfigurator
    {
        public const string MainScenePath = "Assets/Scenes/main.unity";
        public const string UiCanvasTag = "UICanvas";

        [MenuItem("Tools/塔防/2. 配置工程设置", false, 102)]
        public static void Configure()
        {
            EditorUtil.Report report = new EditorUtil.Report();
            ConfigureInternal(report);
            AssetDatabase.SaveAssets();

            Debug.Log("[M0] 工程设置配置结果：\n" + report.Text);
            EditorUtility.DisplayDialog("配置工程设置",
                string.Format("{0}\n\n{1}",
                    report.Errors > 0 ? "有错误，请查看 Console" : "完成", report.Text), "好");
        }

        /// <summary>供一键向导调用（不弹窗）</summary>
        public static void ConfigureInternal(EditorUtil.Report report)
        {
            report.Head("配置工程设置");

            EnsureTag(UiCanvasTag, report);
            ConfigureTransparencySort(report);
            ConfigureBuildSettings(report);
            ConfigurePhysics(report);
            ConfigurePlayerSettings(report);
        }

        /// <summary>
        /// 确保 UICanvas Tag 存在。
        /// 单独暴露出来是因为 SceneMainBuilder 要给 Canvas 赋这个 Tag，
        /// 而**给未定义的 Tag 赋值会直接抛 UnityException**，
        /// 所以搭场景之前必须先过这一关（哪怕用户没单独点过「6. 配置工程设置」）。
        /// </summary>
        public static void EnsureUiCanvasTag()
        {
            EditorUtil.Report tmp = new EditorUtil.Report();
            EnsureTag(UiCanvasTag, tmp);
        }

        // ------------------------------------------------------------------
        // Tag
        // ------------------------------------------------------------------

        private static void EnsureTag(string tag, EditorUtil.Report report)
        {
            Object[] assets = AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/TagManager.asset");
            if (assets == null || assets.Length == 0)
            {
                report.Error("读不到 ProjectSettings/TagManager.asset，无法添加 Tag");
                return;
            }
            SerializedObject so = new SerializedObject(assets[0]);
            SerializedProperty tags = so.FindProperty("tags");
            if (tags == null)
            {
                report.Error("TagManager 里找不到 tags 数组");
                return;
            }

            for (int i = 0; i < tags.arraySize; i++)
            {
                if (tags.GetArrayElementAtIndex(i).stringValue == tag)
                {
                    report.Ok("Tag「" + tag + "」已存在，跳过");
                    return;
                }
            }

            tags.InsertArrayElementAtIndex(tags.arraySize);
            tags.GetArrayElementAtIndex(tags.arraySize - 1).stringValue = tag;
            so.ApplyModifiedProperties();
            report.Ok("已添加 Tag「" + tag + "」");
        }

        // ------------------------------------------------------------------
        // 渲染排序
        // ------------------------------------------------------------------

        private static void ConfigureTransparencySort(EditorUtil.Report report)
        {
            Object[] assets = AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/GraphicsSettings.asset");
            if (assets == null || assets.Length == 0)
            {
                report.Error("读不到 ProjectSettings/GraphicsSettings.asset");
                return;
            }
            SerializedObject so = new SerializedObject(assets[0]);
            SerializedProperty mode = so.FindProperty("m_TransparencySortMode");
            SerializedProperty axis = so.FindProperty("m_TransparencySortAxis");

            if (mode == null || axis == null)
            {
                report.Warn("找不到 m_TransparencySortMode/m_TransparencySortAxis，" +
                            "请手动设置：Project Settings ▸ Graphics ▸ Transparency Sort Mode = Custom Axis (0,-1,0)");
                return;
            }

            mode.intValue = 3;   // TransparencySortMode.CustomAxis
            axis.vector3Value = new Vector3(0f, -1f, 0f);
            so.ApplyModifiedProperties();
            report.Ok("Transparency Sort Mode = Custom Axis (0,-1,0)（Y 越小越靠前，实现前后遮挡）");
        }

        // ------------------------------------------------------------------
        // 构建场景
        // ------------------------------------------------------------------

        private static void ConfigureBuildSettings(EditorUtil.Report report)
        {
            if (AssetDatabase.LoadAssetAtPath<Object>(MainScenePath) == null)
            {
                report.Warn("主场景不存在（稍后由「搭建 main 场景」生成）：" + MainScenePath);
                return;
            }

            List<EditorBuildSettingsScene> scenes = new List<EditorBuildSettingsScene>();
            // 只保留 main.unity —— 其余场景文件已被删除，留着会让打包直接失败
            scenes.Add(new EditorBuildSettingsScene(MainScenePath, true));
            EditorBuildSettings.scenes = scenes.ToArray();
            report.Ok("Build Settings 已设为仅 " + MainScenePath);
        }

        // ------------------------------------------------------------------
        // 物理
        // ------------------------------------------------------------------

        private static void ConfigurePhysics(EditorUtil.Report report)
        {
            // 2D：属性名 m_AutoSimulation
            bool ok2d = TrySetBool("ProjectSettings/Physics2DSettings.asset", "m_AutoSimulation", false);
            if (ok2d)
            {
                report.Ok("已关闭 Physics2D 自动模拟（战斗判定不依赖物理，Profiler 的 Physics2D 分区将为 0）");
            }
            else
            {
                report.Warn("未能自动关闭 Physics2D 自动模拟，可手动设置：" +
                            "Project Settings ▸ Physics 2D ▸ 取消勾选 Simulate（或用 Simulation Mode = Script）");
            }

            // 3D：属性名同样是 m_AutoSimulation
            bool ok3d = TrySetBool("ProjectSettings/DynamicsManager.asset", "m_AutoSimulation", false);
            if (ok3d)
            {
                report.Ok("已关闭 Physics(3D) 自动模拟");
            }
            else
            {
                report.Warn("未能自动关闭 3D 物理自动模拟（项目里已无任何 3D 碰撞体，可忽略）");
            }
        }

        private static bool TrySetBool(string settingsAssetPath, string propertyName, bool value)
        {
            Object[] assets = AssetDatabase.LoadAllAssetsAtPath(settingsAssetPath);
            if (assets == null || assets.Length == 0)
            {
                return false;
            }
            SerializedObject so = new SerializedObject(assets[0]);
            SerializedProperty prop = so.FindProperty(propertyName);
            if (prop == null || prop.propertyType != SerializedPropertyType.Boolean)
            {
                return false;
            }
            prop.boolValue = value;
            so.ApplyModifiedProperties();
            return true;
        }

        // ------------------------------------------------------------------
        // Player Settings
        // ------------------------------------------------------------------

        private static void ConfigurePlayerSettings(EditorUtil.Report report)
        {
            PlayerSettings.defaultScreenWidth = 1920;
            PlayerSettings.defaultScreenHeight = 1080;
            PlayerSettings.resizableWindow = true;
            PlayerSettings.runInBackground = true;
            // 横屏（2D 塔防的棋盘是宽大于高的）
            PlayerSettings.defaultInterfaceOrientation = UIOrientation.LandscapeLeft;
            report.Ok("Player Settings：默认窗口 1920×1080、可调整大小、允许后台运行、横屏");
        }
    }
}
