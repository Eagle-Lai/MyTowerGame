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
        /// 挂上 Reporter 调试控制台（真机上**画圈**手势调出，看日志/内存/FPS）。
        ///
        /// 【为什么动态挂而不是进场景】Reporter 脚本在热更程序集
        /// （FTProject.ThirdParty.Reporter）里 —— 挂进 Build Settings 场景会在打包时
        /// 被烘焙成空壳（HybridCLR 限制，见 BootLoader 注释）；放 prefab 里也没人
        /// 实例化它。动态 AddComponent 时热更 dll 已加载（main 场景加载的前提），
        /// 组件能正常工作。Reporter 的 Awake 会自建 UI（Initialized 默认 false）。
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
            gameObject.AddComponent<Reporter>();
            Debug.Log("[Scene] Reporter 调试控制台已挂载（真机上画圈调出）");
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
