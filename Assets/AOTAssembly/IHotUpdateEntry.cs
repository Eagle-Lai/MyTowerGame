namespace FTProject.AOT
{
    using System;

    /// <summary>
    /// 热更启动入口契约（**定义在 AOT 侧，由热更侧实现**）。
    ///
    /// ==================================================================
    /// 【为什么把它放在 AOT 程序集，而不是热更侧】
    ///   HybridCLR 的铁律是「AOT 主包不得引用热更类型」，但**反向引用是允许的**
    ///   （热更集可以引用 AOT 集）。所以把接口定义在 AOT，让热更侧来 `: IHotUpdateEntry`
    ///   实现 —— 这样：
    ///
    ///     ✅ 编译器保证契约（改方法签名两边同时报错），不再是"字符串约定"
    ///     ✅ 非空性是编译期的（实现类必须实现接口全部成员，漏一个直接编译失败）
    ///     ✅ 接口方法可以带**强类型参数**（bool / 枚举 / 自定义结构），
    ///        而不像以前的反射调用只能无参
    ///     ✅ IDE 能跳转、能重命名、能找到所有实现
    ///
    ///   对比旧方案（`BootLoader` 里写 `EntryTypeName = "FTProject.HotUpdateEntry"` +
    ///   `EntryMethodName = "Start"` 反射调用）：改类名/方法名**不会**编译报错，
    ///   只在运行时抛"找不到入口类型"，排查成本高。这是本次改造的核心动机。
    ///
    /// 【仍然需要一次"查找实现类"】
    ///   接口解决了"契约强类型化"，但 AOT 侧**仍然不能 `new` 热更类型**
    ///   （那会形成编译期符号依赖，IL2CPP 打包直接挂）。
    ///   所以激活流程保留一步"在已加载程序集里找实现类" —— 见
    ///   `HotUpdateEntryLocator.CreateEntry()`。
    ///   区别在于：这一步失败时**错误信息是确定的**（"没有任何类型实现 IHotUpdateEntry"），
    ///   而不是以前那种"名字写错了但看起来像别的问题"。
    ///
    /// 【接口该定义什么 / 不该定义什么】
    ///   ✅ 该定义：与场景无关的启动动作（初始化管理器、准备配置等），
    ///     以及必要时的启动结果/进度反馈。
    ///   ❌ 不该定义：访问 main 场景对象的动作 —— 调用它时 main 还没加载。
    ///     那些应该放在 main 场景的 GameSceneLauncher / Launcher 里。
    ///
    /// 【命名由来】
    ///   类名沿用 `IHotUpdateEntry`（"热更入口"）而非更长的名字，是因为
    ///   它描述的就是"热更代码的启动入口"这一件事，与本工程既有叫法一致。
    /// ==================================================================
    /// </summary>
    public interface IHotUpdateEntry
    {
        /// <summary>
        /// 热更程序集加载完成后由 AOT 侧调用（**在 main 场景加载之前**）。
        ///
        /// 【实现要求】
        ///   - 不能访问任何场景对象（此时 main 还没加载，Boot 也即将卸载）
        ///   - 不能假设 Unity 的 MonoBehaviour 生命周期（本方法不在任何 MonoBehaviour 上）
        ///   - 耗时操作要短：它是在启动链的关键路径上同步执行的
        ///
        /// 【关于重复调用】由实现方自行决定是否需要防重入（推荐用静态 bool 标记）。
        ///   约定：重复调用**不应抛异常**，最多打一条 Warning 后返回。
        /// </summary>
        void Start();

        /// <summary>
        /// 加载 main 场景（**异步**；HybridCLR 真机上场景必须由热更侧从 AssetBundle 加载）。
        ///
        /// 【为什么是热更侧的职责】
        ///   真机上"挂了热更脚本的场景"打进 Build Settings 会在打包时被烘焙成空壳
        ///   （热更程序集被 IFilterBuildAssemblies 剔除，组件序列化成 32 字节 stub），
        ///   运行时表现为 missing script + serialization layout 错误。
        ///   HybridCLR 官方工作流：这类场景必须打 AB，且**在热更 dll 加载后**由
        ///   AB 加载（YooAsset SceneHandle / AssetBundle.LoadFromFile 均可）。
        ///   资源系统的模式选择（联机/离线）也只在热更侧可知（依赖 ResServerConfig），
        ///   所以场景加载放在这里，AOT 侧只等结果。
        ///
        /// 【回调约定】
        ///   - onResult(ok, err)：ok=false 时 err 为可读错误信息
        ///   - 成功时场景已以 Single 模式激活（Boot 场景随之卸载，Boot 侧协程自然终止）
        ///   - 回调在主线程；失败时**不会**激活场景，由 AOT 侧决定展示什么
        /// </summary>
        void EnterMainScene(Action<bool, string> onResult);
    }
}
