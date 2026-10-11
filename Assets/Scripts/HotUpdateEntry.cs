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
            Debug.Log("[HotUpdate] 热更程序集加载完成，HotUpdateEntry.Start() 已执行。"
                + "（经 IHotUpdateEntry 接口调用，非反射）接下来的启动流程由 main 场景的 Launcher 接管。");

            // 预留：在此处做与场景无关的全局初始化。
            // 例如（将来）：
            //   SomeStaticManager.Init();
            //   确保 Luban 配置表已能被解析（注意：真正的表加载在 Launcher 里做）
        }
    }
}
