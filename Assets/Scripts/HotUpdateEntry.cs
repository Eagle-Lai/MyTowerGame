using System;
using UnityEngine;
using FTProject.AOT;

namespace FTProject
{
    /// <summary>
    /// 热更侧启动入口（**AOT 接口 `IHotUpdateEntry` 的实现**）。
    ///
    /// ==================================================================
    /// 【谁调用它】
    ///   Assets/AOTAssembly/BootLoader.cs 在加载完全部热更 dll 后，
    ///   通过 HotUpdateEntryLocator 拿到本类的 IHotUpdateEntry 引用并调用 Start()。
    ///
    /// 【契约怎么保证（本次改造的核心）】
    ///   以前：AOT 侧写死字符串 `"FTProject.HotUpdateEntry"` + `"Start"` 反射调用，
    ///         改名只在**运行时**炸，且错误来自反射、难定位。
    ///   现在：AOT 侧定义接口 `IHotUpdateEntry`，本类 `: IHotUpdateEntry` 实现它。
    ///         ✅ 接口改名 / 方法签名改动 → 两边**同时编译报错**
    ///         ✅ 漏实现接口成员 → 编译失败（非空性由编译器保证）
    ///         ✅ IDE 可跳转 / 重命名 / 查引用
    ///
    ///   ⚠️ 仍有一处字符串契约：本类的**全名**要出现在
    ///      `HotUpdateEntryLocator.EntryTypeNames` 候选表里（用于快路径查找）。
    ///      改了类名要同步 —— 但即使忘了，兜底扫描也能找到（会打 Warning 提示同步）。
    ///      这是 Hard 限制：AOT 侧不能 `new` 热更类型，只能运行时查。
    ///
    /// 【实例化要求】
    ///   必须能被**无参构造**（AOT 侧用 Activator.CreateInstance 创建）。
    ///   所以本类是普通 class + 无参构造，**不是 static class**
    ///   （static 类无法实例化，也就无法作为接口实现被调起）。
    ///   实例本身无状态价值 —— "是否已启动"用静态标记记录（见 Started）。
    ///
    /// 【它该做什么 / 不该做什么】
    ///   ✅ 该做：不依赖任何场景对象的全局初始化
    ///          （例如：注册管理器、初始化配置、设置全局回调）
    ///   ❌ 不该做：访问 main 场景里的对象（此时 main 还没加载）
    ///          —— 那些应该放在 main 场景的 GameSceneLauncher / Launcher 里。
    ///
    ///   【本工程的取舍】现有启动链（Splash → Loading → 资源热更 → Ready）
    ///   完全由 main 场景里的 Launcher 驱动，且这一步**必须在 main 场景加载后**
    ///   才有意义（要显示 UI、要读场景引用）。所以这里**保持空实现 + 打印一条日志**，
    ///   真正的流程交给 Launcher —— 这样做的好处是：接入 HybridCLR 后，
    ///   现有启动逻辑一行都不用改。
    ///   将来若需要在进 main 之前做纯代码初始化，往这里加即可。
    /// ==================================================================
    /// </summary>
    public class HotUpdateEntry : IHotUpdateEntry
    {
        /// <summary>被调用过一次的标记（防重复调用；也便于自检）。</summary>
        public static bool Started { get; private set; }

        /// <summary>
        /// main 场景在 YooAsset 里的定位地址。
        /// 收集器「可寻址 = 关闭」→ 定位地址 = **资源路径**（SupportExtensionless=true
        /// 时去扩展名变体也可用）。⚠️ 改了场景文件位置要同步这里。
        /// </summary>
        private const string MainSceneAddress = "Assets/Scenes/Main.unity";

        /// <summary>
        /// 热更程序集加载完成后由 AOT 侧调用（接口实现）。
        /// 注意：这是在 main 场景**加载之前**执行的，不能碰场景对象。
        /// </summary>
        public void Start()
        {
            if (Started)
            {
                Debug.LogWarning("[HotUpdate] HotUpdateEntry.Start() 被重复调用，已忽略。");
                return;
            }
            Started = true;

            // 让 Unity 知道"热更代码已经跑起来了" —— 这条日志是排查启动问题的第一现场：
            //   能看到它      → 说明 dll 加载 + 入口实例化 + 接口调用都成功，问题在后续流程
            //   看不到它      → 说明 dll 加载失败，或没有任何实现类（去看 BootLoader 的报错）
            Debug.Log("[HotUpdate] 热更程序集加载完成，HotUpdateEntry.Start() 已执行（热更验证标记 v2）。"
                + "（经 IHotUpdateEntry 接口调用，非反射）接下来的启动流程由 main 场景的 Launcher 接管。");

            // 预留：在此处做与场景无关的全局初始化。
            // 例如（将来）：
            //   SomeStaticManager.Init();
            //   确保 Luban 配置表已能被解析（注意：真正的表加载在 Launcher 里做）
        }

        /// <summary>
        /// 加载 main 场景（IHotUpdateEntry 接口实现，见 AOT 侧接口注释）。
        ///
        /// 【为什么绕 ResLoader】资源系统的模式选择（联机 HostPlayMode / 离线 OfflinePlayMode）
        /// 由 YooAssetResLoader.CreateInitOptions 决定，依赖 ResServerConfig（热更集内）。
        /// 在这里 Init 一次后，main 场景的 Launcher 再做检查更新时 Init 会直接复用
        /// （YooAssetResLoader 有重复初始化防护），不会撞"重复初始化"异常。
        ///
        /// 【真机上的两段式（2026-10-16 起）】Init 成功后先跑
        /// <see cref="BootHotUpdateGate"/>：版本检查 + 全部差异下载完成才继续加载
        /// main；失败留在 Boot 的自动重试界面（绝不带缺失进 main —— 修复"更新
        /// 中断后残缺运行"的结构性问题）。编辑器下跳过闸门，保持原快速路径。
        ///
        /// 【Init 失败怎么算】Init 的失败详情由 ResLoader 打印，这里把 IsReady 状态
        /// 汇总成回调结果 —— Boot 侧拿到 false 会在启动界面上展示错误。
        /// </summary>
        /// <summary>Boot 阶段"初始化失败 → 自动重试"的间隔（秒）。</summary>
        private const float EnterRetryDelaySeconds = 3f;

        public void EnterMainScene(Action<bool, string> onResult)
        {
            if (onResult == null)
            {
                return;
            }

            // 【2026-10-16】包成"带自动重试的进 main 流程"：
            //   此前 Init 失败会直接 onResult(false) —— Boot 侧只有日志没有界面，
            //   真机/模拟器表现为**黑屏卡死**（实测：服务器在跑但 version 文件 404
            //   时，YooAsset 请求包裹版本会硬失败）。现在失败会显示重试界面并自动
            //   重试（先安全重建包裹再重跑 Init），服务器恢复后自动继续 —— 不黑屏、
            //   不静默，保持与"热更完整性闸门"一致的"宁可停在重试页"策略。
            ResLoaderRunner.Start(EnterMainCo(onResult));
        }

        private System.Collections.IEnumerator EnterMainCo(Action<bool, string> onResult)
        {
            int attempt = 0;
            BootHotUpdateUI ui = null;   // 仅"失败过"时才创建；正常路径零界面

            while (true)
            {
                attempt++;

                bool initCalled = false;
                ResLoader.Instance.Init(() => initCalled = true);
                while (initCalled == false)
                {
                    yield return null;
                }

                if (ResLoader.Instance.IsReady)
                {
                    break;   // 初始化成功 → 出循环（过闸门 / 进 main）
                }

                // ---- 初始化失败：显示原因 + 倒计时 + 自动重试（不黑屏卡死）----
                // 接口不含"重建/最近错误"能力 → 用 as 转型（当前配置下恒为 YooAsset
                // 实现）；转型失败时降级为原行为（直接上报失败）。
                YooAssetResLoader yooLoader = ResLoader.Instance as YooAssetResLoader;
                string reason = yooLoader != null ? yooLoader.LastInitError : null;

                if (yooLoader == null)
                {
                    Debug.LogError("[HotUpdate] 资源系统初始化失败（无安全重建能力，直接上报）。");
                    onResult(false, string.IsNullOrEmpty(reason) ? "资源系统初始化失败，无法加载 main 场景" : reason);
                    yield break;
                }

                Debug.LogWarning(string.Format(
                    "[HotUpdate] 资源系统初始化失败（第 {0} 次）：{1} —— {2} 秒后自动重试（含安全重建）。",
                    attempt, reason, EnterRetryDelaySeconds));

                if (ui == null)
                {
                    try
                    {
                        ui = BootHotUpdateUI.Create();
                    }
                    catch (System.Exception e)
                    {
                        ui = null;
                        Debug.LogError("[HotUpdate] 初始化重试界面创建失败（降级为无界面重试）：" + e);
                    }
                }
                if (ui != null)
                {
                    ui.Toast("资源服务器异常，正在自动重试…",
                        string.IsNullOrEmpty(reason) ? "资源系统初始化失败" : reason);
                }

                float waitStart = Time.realtimeSinceStartup;
                while (Time.realtimeSinceStartup - waitStart < EnterRetryDelaySeconds)
                {
                    if (ui != null)
                    {
                        ui.SetRetryCountdown(attempt, EnterRetryDelaySeconds - (Time.realtimeSinceStartup - waitStart));
                    }
                    yield return null;
                }

                // 重试前先销毁遗留包裹（YooAsset 要求先异步销毁、再从全局移除；
                // 两步之间让帧推进。销毁很小（毫秒级），失败容忍：直接在旧包裹上重跑）
                var destroyOp = yooLoader.BeginRetryDestroy();
                while (destroyOp != null && destroyOp.IsDone == false)
                {
                    yield return null;
                }
                yooLoader.CompleteRetryRebuild();
                if (ui != null) ui.ShowRetrying(attempt);
            }

            // ---- 初始化成功：收尾失败界面（如有）→ 过闸门 / 进 main ----
            if (ui != null)
            {
                ui.ShowDone();
                yield return new WaitForSecondsRealtime(0.35f);
                ui.Destroy();
            }

#if UNITY_EDITOR
            // 编辑器：直读 / 模拟清单，没有"下载"语义 —— 保持原行为（快速进 main）。
            // 热更完整性闸门只在真机生效（见 BootHotUpdateGate 类注释）。
            Debug.Log("[HotUpdate] 资源系统就绪（编辑器模式），开始加载 main 场景（地址 " + MainSceneAddress + "）…");
            ResLoader.Instance.LoadSceneAsync(MainSceneAddress, onResult);
#else
            // 真机：先过"热更完整性闸门" —— 版本检查 + 全部差异下载完成才放行；
            // 失败留在 Boot 的重试界面（断点续传），绝不带缺失进 main。
            bool gateDone = false;
            BootHotUpdateGate.Run(() => gateDone = true);
            while (gateDone == false)
            {
                yield return null;
            }
            Debug.Log("[HotUpdate] 资源系统就绪，开始加载 main 场景（地址 " + MainSceneAddress + "）…");
            ResLoader.Instance.LoadSceneAsync(MainSceneAddress, onResult);
#endif
        }
    }
}
