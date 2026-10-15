using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// main 场景的**组合根**（Composition Root）。
    ///
    /// 为什么单独要这个类：Unity 的 prefab/场景序列化字段散落在各个组件上，
    /// 一旦某个引用漏连，往往要到运行时某个随机时刻才以 NullReference 的形式暴露。
    /// 把所有场景引用集中在这里、在 Awake 里一次性校验并注入给 GameFlowManager，
    /// 出错时能立刻给出"哪个引用没连"的明确报错。
    ///
    /// 该脚本与全部引用由「Tools ? 塔防 ? 搭建 main 场景」自动生成并连线，
    /// 一般情况下不需要手动改。
    /// </summary>
    public class GameSceneLauncher : MonoBehaviour
    {
        [Header("流程")]
        public GameFlowManager flowManager;

        [Header("视图")]
        public BoardView boardView;
        public PathArrowView pathArrowView;

        [Header("层级容器")]
        public Transform boardRoot;
        public Transform pathRoot;
        public Transform towerRoot;
        public Transform enemyRoot;
        public Transform bulletRoot;

        private void Awake()
        {
            if (!Validate())
            {
                enabled = false;
                return;
            }

            // 注入流程管理器
            flowManager.boardView = boardView;
            flowManager.pathArrowView = pathArrowView;
            flowManager.boardRoot = boardRoot;
            flowManager.pathRoot = pathRoot;
            flowManager.towerRoot = towerRoot;
            flowManager.enemyRoot = enemyRoot;
            flowManager.bulletRoot = bulletRoot;

            EnsureReporter();
        }

        /// <summary>
        /// 挂上 Reporter 调试控制台（真机上**画圈或双击**调出，看日志/内存/FPS）。
        ///
        /// 【为什么动态挂而不是进场景】Reporter 脚本在热更程序集
        /// （FTProject.ThirdParty.Reporter）里 —— 挂进 Build Settings 场景会在打包时
        /// 被烘焙成空壳（HybridCLR 限制，见 BootLoader 注释）；放 prefab 里也没人
        /// 实例化它。动态 AddComponent 时热更 dll 已加载（main 场景加载的前提），
        /// 组件能正常工作。Reporter 的 Awake 会自建 UI（Initialized 默认 false）。
        ///
        /// 【为什么要注入图片加载器】Reporter 的 images 字段原本靠编辑器菜单
        /// 「Reporter/Create」填充并随场景序列化；动态挂载没有这一步，images 为空会
        /// 让 Initialize 抛 NullReferenceException、初始化中断，面板永远打不开
        /// （2026-10-14 模拟器实测定位）。这里把图片接到工程统一资源链路
        /// （ResTable Reporter_* → 编辑器 AssetDatabase / 真机 YooAsset AB，
        /// 收集器 ReporterData 组），加载失败时 Reporter 内部退化为占位图，不崩。
        /// **必须在 AddComponent 之前注入**：AddComponent 会同步触发 Awake。
        /// </summary>
        private void EnsureReporter()
        {
            // Reporter 是全局命名空间的 MonoBehaviour（无命名空间），直接泛型挂载。
            // 【注意】必须用泛型 AddComponent —— 官方已知问题：字符串重载
            // GetComponent/AddComponent 对热更脚本不可靠。
            if (GetComponent<Reporter>() != null)
            {
                return;
            }
            // 跨场景守卫：main 场景若被重载，旧 Reporter 已 DontDestroyOnLoad 常驻，
            // 不要再挂第二个（重复注册日志回调会让每条日志记两遍；且 Reporter 的
            // "第二实例自删"逻辑会连本物体一起 Destroy，必须在这里拦住）。
            if (Reporter.Instance != null)
            {
                return;
            }

            Reporter.ImageLoader = LoadReporterIcon;
            Reporter.ScrollerSkinLoader = LoadReporterScrollerSkin;

            gameObject.AddComponent<Reporter>();
            // 原版 Reporter prefab 同一物体上自带 ReporterMessageReceiver
            // （OnPreStart 按分辨率调面板尺寸 + OnShow/OnHide/OnLog 用户钩子）。
            // 动态挂载时漏掉它，SendMessage("OnPreStart") 等会报 "no receiver" 警告
            // （恢复原版契约；OnLog 一侧的死循环隐患另在 Reporter.cs 用
            // DontRequireReceiver 釜底抽薪）。
            gameObject.AddComponent<ReporterMessageReceiver>();
            Debug.Log("[Scene] Reporter 调试控制台已挂载（画圈或双击调出）");
        }

        /// <summary>Reporter 图标（逻辑名见 ResTable 的 Reporter_* 段；失败返回 null，由 Reporter 兜底占位）</summary>
        private static Texture2D LoadReporterIcon(string name)
        {
            return ResLoader.Instance.Load<Texture2D>("Reporter_" + name);
        }

        /// <summary>Reporter 滚动条皮肤（失败返回 null，由 Reporter 兜底为空 GUISkin）</summary>
        private static GUISkin LoadReporterScrollerSkin()
        {
            return ResLoader.Instance.Load<GUISkin>("Reporter_scrollerSkin");
        }

        private bool Validate()
        {
            bool ok = true;
            ok &= Check(flowManager, "flowManager");
            ok &= Check(boardView, "boardView");
            ok &= Check(pathArrowView, "pathArrowView");
            ok &= Check(boardRoot, "boardRoot");
            ok &= Check(pathRoot, "pathRoot");
            ok &= Check(towerRoot, "towerRoot");
            ok &= Check(enemyRoot, "enemyRoot");
            ok &= Check(bulletRoot, "bulletRoot");

            if (!ok)
            {
                Debug.LogError(
                    "[Scene] GameSceneLauncher 存在未连线的引用，流程已停止。\n" +
                    "  修复：菜单「Tools ? 塔防 ? 搭建 main 场景」重新生成场景，" +
                    "或手工把缺失的引用拖到 Inspector 对应槽位。");
            }
            return ok;
        }

        private static bool Check(Object o, string name)
        {
            if (o == null)
            {
                Debug.LogError("[Scene] 引用未连线：" + name);
                return false;
            }
            return true;
        }
    }
}
