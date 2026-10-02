using System.Collections.Generic;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

namespace FTProject.EditorTools
{
    /// <summary>
    /// 在 main.unity 里搭出完整可运行的战斗场景（P0-2 / 需求 6）。
    ///
    /// 【为什么用脚本搭场景而不是让人手工拖】
    ///   手工搭场景的问题不是"慢"，而是**不可复现**：漏连一个引用、名字打错一个字符，
    ///   都要到运行时以 NullReference 的形式暴露，排查成本极高。
    ///   脚本搭场景 + GameSceneLauncher 启动时校验，能把这类问题在点下 Play 之前就报出来。
    ///
    /// 【本脚本会重建整个场景】执行前会把原 main.unity 备份到 Assets/Scenes/_Backup/。
    ///
    /// 目标层级：
    ///   Camera(+CameraController)      正交相机，半径由 CameraController.FitBoard 按棋盘算
    ///   EventSystem                    UGUI 事件系统（按钮点击必需）
    ///   Launcher                       全局启动器（注册并初始化各管理器）
    ///   UICanvas  [tag=UICanvas]       Canvas(ScreenSpaceOverlay) + CanvasScaler(1920×1080)
    ///     ├── BgPanel                  背景层
    ///     ├── NormalPanel              常规面板层（HudView 挂这里）
    ///     └── TipsPanel                浮层提示层（TipsView 挂这里）
    ///   BattleRoot                     战斗棋盘根
    ///     ├── Background               Paper.png 世界空间背景
    ///     ├── BoardRoot    (BoardView)      格子
    ///     ├── PathRoot     (PathArrowView)  路径箭头
    ///     ├── TowerRoot    (TowerPlacement) 塔 + 放置预览
    ///     ├── EnemyRoot                     怪物
    ///     └── BulletRoot                    子弹
    ///   GameFlow          (GameFlowManager)     关卡流程总控
    ///   GameSceneLauncher (GameSceneLauncher)   组合根：校验并注入引用
    ///
    /// 菜单：Tools ▸ 塔防 ▸ 高级（单步重建）▸ 重建 main 场景
    /// </summary>
    public static class SceneMainBuilder
    {
        public const string MainScenePath = ProjectSettingsConfigurator.MainScenePath;
        private const string BackupPath = "Assets/Scenes/_Backup/main_before_builder.unity";
        private const string BackgroundSpritePath = "Assets/_UIAssets/Backgrounds/Paper.png";

        /// <summary>背景缩放：Paper.png 是 19.5×13 世界单位，放大后足以覆盖视野</summary>
        private const float BackgroundScale = 1.6f;

        /// <summary>
        /// 菜单入口：**危险**，会重建整个 main.unity（原文件先备份）。
        /// 为了不被误点，收进「高级（单步重建）」子菜单。
        /// </summary>
        [MenuItem("Tools/塔防/高级（单步重建）/重建 main 场景（危险：会清空重建）", false, 307)]
        public static void Build()
        {
            if (!EditorUtility.DisplayDialog("重建 main 场景",
                    "此操作会**清空并重建** main.unity 的全部根对象，" +
                    "你在场景里的手工接线会丢失（原文件会先备份到\n" +
                    BackupPath + "）。\n\n确认继续？",
                    "重建", "取消"))
            {
                return;
            }
            EditorUtil.Report report = new EditorUtil.Report();
            bool ok = BuildInternal(report);
            Debug.Log("[M0] 场景搭建结果：\n" + report.Text);
            EditorUtility.DisplayDialog("重建 main 场景",
                string.Format("{0}\n\n{1}",
                    ok ? "完成，已打开 main.unity" : "有错误，请查看 Console", report.Text), "好");
        }

        /// <summary>
        /// 安全入口（供一键补齐向导调用）：场景已存在则**跳过**，只在缺失时搭建。
        /// 这样"跑一次向导"不会抹掉手工接线。
        /// </summary>
        public static bool EnsureOrBuildInternal(EditorUtil.Report report)
        {
            report.Head("main 场景（安全模式：缺失才搭建）");
            if (AssetDatabase.LoadAssetAtPath<Object>(MainScenePath) != null)
            {
                report.Ok("main.unity 已存在，跳过重建（保住手工接线）。需要重建请走「高级（单步重建）」");
                return true;
            }
            return BuildInternal(report);
        }

        /// <summary>供一键向导调用（不弹窗，会重建）</summary>
        public static bool BuildInternal(EditorUtil.Report report)
        {
            report.Head("搭建 main 场景 → " + MainScenePath);

            // ① 保存用户当前改动（否则切场景会丢）
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo())
            {
                report.Warn("用户取消了「保存当前场景」，搭建中止");
                return false;
            }

            bool existed = AssetDatabase.LoadAssetAtPath<Object>(MainScenePath) != null;
            if (existed)
            {
                BackupScene(report);
            }

            // ② 打开（或新建）主场景
            Scene scene;
            if (existed)
            {
                scene = EditorSceneManager.OpenScene(MainScenePath, OpenSceneMode.Single);
                // 清空所有根对象，保证结果可复现
                GameObject[] roots = scene.GetRootGameObjects();
                for (int i = 0; i < roots.Length; i++)
                {
                    Object.DestroyImmediate(roots[i]);
                }
                report.Ok(string.Format("已清空原场景的 {0} 个根对象", roots.Length));
            }
            else
            {
                EditorUtil.EnsureFolderOfFile(MainScenePath);
                scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
                report.Ok("主场景不存在，已新建空场景");
            }

            // ③ 逐步搭建
            CameraController camera = BuildCamera(report);
            BuildEventSystem(report);
            BuildLauncher(report);
            BuildUiCanvas(report);
            Transform battleRoot = BuildBattleRoot(report, out BoardView boardView,
                out PathArrowView arrowView, out TowerPlacement placement);
            GameFlowManager flow = BuildGameFlow(report);

            // ④ 组合根接线
            BuildSceneLauncher(report, flow, boardView, arrowView, placement, battleRoot);

            EditorSceneManager.MarkSceneDirty(scene);
            bool saved = EditorSceneManager.SaveScene(scene, MainScenePath);
            if (!saved)
            {
                report.Error("保存场景失败：" + MainScenePath);
                return false;
            }
            report.Ok("场景已保存");
            if (camera == null)
            {
                report.Warn("相机未创建，运行时将无法取景");
            }
            return true;
        }

        private static void BackupScene(EditorUtil.Report report)
        {
            EditorUtil.EnsureFolderOfFile(BackupPath);
            AssetDatabase.DeleteAsset(BackupPath);
            if (AssetDatabase.CopyAsset(MainScenePath, BackupPath))
            {
                report.Ok("原场景已备份到 " + BackupPath);
            }
            else
            {
                report.Warn("原场景备份失败（不影响搭建）：" + BackupPath);
            }
        }

        // ------------------------------------------------------------------
        // 相机
        // ------------------------------------------------------------------

        private static CameraController BuildCamera(EditorUtil.Report report)
        {
            GameObject go = new GameObject("Camera");
            Camera cam = go.AddComponent<Camera>();
            cam.tag = "MainCamera";                 // Camera.main 依赖这个 Tag
            cam.orthographic = true;
            cam.orthographicSize = 5.5f;            // 运行时由 CameraController.FitBoard 覆盖
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = new Color(0.09f, 0.10f, 0.13f, 1f);
            cam.nearClipPlane = 0.1f;
            cam.farClipPlane = 100f;
            go.transform.position = new Vector3(0f, 0f, CameraController.DefaultZ);
            go.transform.rotation = Quaternion.identity;

            CameraController ctrl = go.AddComponent<CameraController>();
            report.Ok("相机：正交、Tag=MainCamera、位置 (0,0,-10)，半径运行时按棋盘自适应");
            return ctrl;
        }

        // ------------------------------------------------------------------
        // 事件系统 / 启动器
        // ------------------------------------------------------------------

        private static void BuildEventSystem(EditorUtil.Report report)
        {
            GameObject go = new GameObject("EventSystem");
            go.AddComponent<EventSystem>();
            go.AddComponent<StandaloneInputModule>();
            report.Ok("EventSystem（UGUI 按钮点击必需；注意 TowerPlacement 用 " +
                      "EventSystem.IsPointerOverGameObject() 避免点 UI 时误放塔）");
        }

        private static void BuildLauncher(EditorUtil.Report report)
        {
            GameObject go = new GameObject("Launcher");
            go.AddComponent<Launcher>();
            report.Ok("Launcher（注册各管理器 → 初始化资源加载 → 加载 8 张配置表）");
        }

        // ------------------------------------------------------------------
        // UI
        // ------------------------------------------------------------------

        private static void BuildUiCanvas(EditorUtil.Report report)
        {
            GameObject go = new GameObject("UICanvas");
            Canvas canvas = go.AddComponent<Canvas>();
            // Overlay 而不是 ScreenSpaceCamera：HUD 不受相机缩放/平移影响
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            canvas.sortingOrder = 100;

            CanvasScaler scaler = go.AddComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1920f, 1080f);
            // 0.5 = 宽高各占一半权重，横竖屏切换时不会一边被拉爆
            scaler.screenMatchMode = CanvasScaler.ScreenMatchMode.MatchWidthOrHeight;
            scaler.matchWidthOrHeight = 0.5f;

            go.AddComponent<GraphicRaycaster>();
            // 先确保 Tag 已存在：给未定义的 Tag 赋值会抛 UnityException
            ProjectSettingsConfigurator.EnsureUiCanvasTag();
            go.tag = ProjectSettingsConfigurator.UiCanvasTag;

            CreatePanel(go.transform, "BgPanel");
            CreatePanel(go.transform, "NormalPanel");
            CreatePanel(go.transform, "TipsPanel");

            report.Ok("UICanvas（ScreenSpaceOverlay，1920×1080，Match 0.5）+ 三层 Panel");
        }

        private static void CreatePanel(Transform parent, string name)
        {
            GameObject go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(parent, false);
            RectTransform rt = (RectTransform)go.transform;
            rt.anchorMin = Vector2.zero;
            rt.anchorMax = Vector2.one;
            rt.pivot = new Vector2(0.5f, 0.5f);
            rt.anchoredPosition = Vector2.zero;
            rt.sizeDelta = Vector2.zero;
            rt.localScale = Vector3.one;
        }

        // ------------------------------------------------------------------
        // 战斗根节点
        // ------------------------------------------------------------------

        private static Transform BuildBattleRoot(EditorUtil.Report report,
            out BoardView boardView, out PathArrowView arrowView, out TowerPlacement placement)
        {
            GameObject root = new GameObject("BattleRoot");

            // 背景
            Sprite bg = AssetDatabase.LoadAssetAtPath<Sprite>(BackgroundSpritePath);
            GameObject bgGo = new GameObject("Background");
            bgGo.transform.SetParent(root.transform, false);
            bgGo.transform.localPosition = Vector3.zero;
            bgGo.transform.localScale = new Vector3(BackgroundScale, BackgroundScale, 1f);
            SpriteRenderer bgSr = bgGo.AddComponent<SpriteRenderer>();
            bgSr.sprite = bg;
            bgSr.sortingOrder = BoardSorting.Background;
            bgSr.color = new Color(1f, 1f, 1f, 0.55f);
            // M4-4：背景视差。Init 必须在设完缩放与颜色之后调用 —— 它要记住这两者的基准值。
            BackgroundParallax parallax = bgGo.AddComponent<BackgroundParallax>();
            parallax.Init();
            if (bg == null)
            {
                report.Warn("背景贴图未找到或未导入为 Sprite：" + BackgroundSpritePath);
            }

            // 格子
            GameObject boardGo = new GameObject("BoardRoot");
            boardGo.transform.SetParent(root.transform, false);
            boardView = boardGo.AddComponent<BoardView>();

            // 路径箭头
            GameObject pathGo = new GameObject("PathRoot");
            pathGo.transform.SetParent(root.transform, false);
            arrowView = pathGo.AddComponent<PathArrowView>();

            // 塔（放置控制器与塔的父节点同一个对象，预览体也挂在它下面）
            GameObject towerGo = new GameObject("TowerRoot");
            towerGo.transform.SetParent(root.transform, false);
            placement = towerGo.AddComponent<TowerPlacement>();

            // 怪物 / 子弹（纯容器，实例由对象池创建并挂进来）
            GameObject enemyGo = new GameObject("EnemyRoot");
            enemyGo.transform.SetParent(root.transform, false);
            GameObject bulletGo = new GameObject("BulletRoot");
            bulletGo.transform.SetParent(root.transform, false);

            report.Ok("BattleRoot → Background / BoardRoot(BoardView) / PathRoot(PathArrowView) " +
                      "/ TowerRoot(TowerPlacement) / EnemyRoot / BulletRoot");
            return root.transform;
        }

        private static GameFlowManager BuildGameFlow(EditorUtil.Report report)
        {
            GameObject go = new GameObject("GameFlow");
            GameFlowManager flow = go.AddComponent<GameFlowManager>();
            flow.startLevelId = 0;   // 0 = 用配置表里第一个关卡
            report.Ok("GameFlow（GameFlowManager，startLevelId=0 → 取 TBSceneInfo 第一行）");
            return flow;
        }

        // ------------------------------------------------------------------
        // 组合根
        // ------------------------------------------------------------------

        private static void BuildSceneLauncher(EditorUtil.Report report,
            GameFlowManager flow, BoardView boardView, PathArrowView arrowView,
            TowerPlacement placement, Transform battleRoot)
        {
            GameObject go = new GameObject("GameSceneLauncher");
            GameSceneLauncher launcher = go.AddComponent<GameSceneLauncher>();

            launcher.flowManager = flow;
            launcher.boardView = boardView;
            launcher.pathArrowView = arrowView;
            launcher.boardRoot = battleRoot.Find("BoardRoot");
            launcher.pathRoot = battleRoot.Find("PathRoot");
            launcher.towerRoot = battleRoot.Find("TowerRoot");
            launcher.enemyRoot = battleRoot.Find("EnemyRoot");
            launcher.bulletRoot = battleRoot.Find("BulletRoot");

            // placement 与 towerRoot 是同一个对象，GameSceneLauncher 不持有它的引用：
            // TowerPlacement 自己从 Inspector 取父节点即可，少一处可漏连的引用
            if (placement == null)
            {
                report.Warn("TowerPlacement 未创建，将无法建塔");
            }

            report.Ok("GameSceneLauncher（组合根：启动时校验并注入全部场景引用）");
        }
    }
}
