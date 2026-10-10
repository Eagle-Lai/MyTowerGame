using System;
using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 统一资源加载接口。
    /// 业务代码**只依赖本接口**，不感知底层是 AssetDatabase 还是 AssetBundle。
    ///
    /// 两个实现：
    ///   - EditorResLoader：编辑器下用 AssetDatabase 直读，改完资源即时生效，无需打 AB
    ///   - BundleResLoader：真机/发布用 AssetBundle，含依赖与引用计数
    /// 由 ResLoader.Instance 按编译宏自动选择。
    /// </summary>
    public interface IResLoader
    {
        /// <summary>是否已初始化完成</summary>
        bool IsReady { get; }

        /// <summary>
        /// 初始化（真机实现会加载 AB 总清单；编辑器实现为空操作）。
        /// 完成后回调，之后才能调用其它接口。
        /// </summary>
        void Init(Action onDone);

        /// <summary>
        /// 带进度的初始化（UI 补全 A2：LoadingView 的进度条数据源）。
        /// <paramref name="onProgress"/> 收 0~1 的**归一化**进度，实现方保证**单调不减**；
        /// 允许实现方只在少数几个离散点回报（例如每个包裹一次），界面侧负责补间。
        /// 【为什么不改旧签名】三套实现 + 既有调用方都在用 <see cref="Init(Action)"/>，
        /// 改签名会一次性波及全部；加重载则旧路径零成本保留。
        /// </summary>
        void Init(Action<float> onProgress, Action onDone);

        /// <summary>同步加载单个资源（返回 null 表示加载失败，已打印错误）</summary>
        T Load<T>(string logicalName) where T : UnityEngine.Object;

        /// <summary>
        /// 异步加载单个资源。
        /// 【注意】即使编辑器实现也要保证"至少延迟一帧回调"，
        /// 以免业务代码写出"依赖同步返回"的写法，在真机上才暴露问题。
        /// </summary>
        void LoadAsync<T>(string logicalName, Action<T> onDone) where T : UnityEngine.Object;

        /// <summary>
        /// 实例化预制体（从已加载的 bundle 取资产并实例化）。
        /// 【引用计数约定】本方法**不改变** bundle 引用计数 —— bundle 的生命周期
        /// 由 <see cref="Preload"/> 与 <see cref="ReleaseBundle"/> 按"关卡"粒度管理。
        /// 对象自身的复用请交给游戏侧的对象池，不要与 AB 生命周期混在一起。
        /// 失败返回 null。
        /// </summary>
        GameObject Instantiate(string logicalName, Transform parent = null);

        /// <summary>异步实例化预制体</summary>
        void InstantiateAsync(string logicalName, Transform parent, Action<GameObject> onDone);

        /// <summary>
        /// 销毁一个由 Instantiate 创建、且不参与对象池的实例。
        /// 池化对象请由对象池管理，不要调用本方法。
        /// 【引用计数约定】本方法**不改变** bundle 引用计数。
        /// </summary>
        void ReleaseInstance(string logicalName, GameObject instance);

        /// <summary>
        /// 释放某个逻辑资源在加载器内部的缓存引用。
        /// 一般不需要手动调用（关卡结束用 <see cref="ReleaseBundle"/> 整包释放即可）。
        /// </summary>
        void Release(string logicalName);

        /// <summary>
        /// 整包释放：bundle 引用计数 -1，归零时 Unload(false) + UnloadUnusedAssets。
        /// 切关卡时对不再需要的包调用。**常驻包（ResBundle.Persistent）不会被真正卸载。**
        /// </summary>
        void ReleaseBundle(string bundleName);

        /// <summary>
        /// 预加载一批逻辑资源（进关卡前预热）。
        /// 内部会对涉及的每个 bundle 获取一次"关卡引用"（引用计数 +1），
        /// 与 ReleaseBundle 配对使用。
        /// </summary>
        void Preload(string[] logicalNames, Action onDone);

        /// <summary>
        /// 带进度的预加载（按"已处理逻辑名个数 / 总数"回报 0~1）。
        /// 与 <see cref="Init(Action, Action)"/> 同理：只加重载，不动旧签名。
        /// </summary>
        void Preload(string[] logicalNames, Action<float> onProgress, Action onDone);

        /// <summary>诊断信息（打印当前已加载的包与引用计数）</summary>
        string DumpDebugInfo();
    }
}
