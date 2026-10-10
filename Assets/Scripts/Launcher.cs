using System.Collections.Generic;
using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 全局启动器（v2.1 重写）。
    ///
    /// 启动顺序（严格串行，任一步失败都会给出明确报错并中止）：
    ///   ① 注册并初始化各管理器（纯 C# 单例，无 MonoBehaviour 依赖）
    ///   ② 初始化资源加载器（编辑器直读 / 真机 AssetBundle）
    ///   ③ 加载 8 张配置表
    ///   ④ 广播 ConfigLoadedEvent → GameFlowManager 开始建关
    ///
    /// 相对 v1.0 的改动：
    ///   - 去掉 `DataTables`（它把配置表挂在 GameObject 上用 Unity 序列化读，
    ///     而 Luban 的 json 需要显式解析，两套机制混在一起）
    ///   - 去掉 `JsonDataManager`（顶层 `using UnityEditor` → 打包必炸）
    ///   - 去掉 `GameSceneManager` / `RoundCountManager`（职责已并入 GameFlowManager）
    ///   - 管理器不再依赖 `Launcher.Instance.Tables`
    ///   - `TimerManager` 改用自己的 deltaTime 驱动，不再复用 fixedDeltaTime
    ///     （原实现传 `Time.fixedDeltaTime`，改帧率后定时器节奏会漂）
    /// </summary>
    public class Launcher : MonoBehaviour
    {
        /// <summary>
        /// 启动阶段（UI 补全 §5.1）。顺序**不可颠倒**：
        ///   ① Splash 品牌过场（纯定时，不阻塞任何加载）
        ///   ② Loading 里做 ResLoader.Init（只有资源系统就绪后才有"版本"这个概念）
        ///   ③ HotUpdate 版本比对 + 差异下载（必须在 Init **之后**）
        ///   ④ 回到 Loading 加载配置表（必须在热更新**之后** —— 否则玩家会先看到旧配置构建的界面）
        ///   ⑤ Ready：广播 ConfigLoadedEvent，GameFlowManager 开始进主菜单
        /// </summary>
        public enum BootPhase
        {
            Splash,
            Loading,
            HotUpdate,
            Ready
        }

        /// <summary>当前启动阶段（只读，供日志与调试查看）</summary>
        public BootPhase Phase { get; private set; }

        public static Launcher Instance { get; private set; }

        /// <summary>LoadingView 的进度权重（A2 表）：资源系统占 [0, 0.3]，配置表占 [0.3, 0.9]，收尾 [0.9, 1]。</summary>
        private const float LoadingResWeight = 0.3f;
        private const float LoadingConfigEnd = 0.9f;

        /// <summary>热更新完成后的停留时长（让"更新完成"至少被看见，而不是一闪而过）。</summary>
        private const float HotUpdateDoneHoldSec = 0.5f;

        /// <summary>
        /// 管理器注册表。**顺序有意义**：
        ///   AStarManager 先建（棋盘数据层），CombatSystem 后建（它要读配置算网格尺寸）
        ///
        /// 【必须用 .Instance，不能用 new】这是一个真实踩过的严重坑：
        ///   `BaseManager&lt;T&gt;.Instance` 是**懒创建**的，如果这里 `new` 一个，
        ///   而其它代码用 `.Instance` 访问，就会同时存在**两个对象**。
        ///   症状极具迷惑性：Launcher 创建的那个被寄存器接受、每帧 tick，
        ///   而 `.Instance` 那个才是各处写入数据的目标 —— 于是
        ///   "怪物生成了但不移动、不计入存活、回合空转完成"，
        ///   而且**没有任何报错**。所以统一走 `.Instance`。
        /// </summary>
        private readonly List<IManagerInterface> _managers = new List<IManagerInterface>
        {
            AStarManager.Instance,
            // 存档最早初始化：它的设置要在 AudioManager 起来后立刻生效（见 Awake 末尾）
            SaveManager.Instance,
            PlayerDataManager.Instance,
            EnemyManager.Instance,
            BulletManager.Instance,
            TowerManager.Instance,
            CombatSystem.Instance,
            UIManager.Instance,
            // 音效放最后：它依赖 Configs（TBAudio 表）与 ResLoader，
            // 但两项都是"用到时才查"，早注册晚注册都不影响正确性，放在末尾更符合阅读顺序。
            AudioManager.Instance,
        };

        private bool _booted;

        private void Awake()
        {
            if (Instance != null && Instance != this)
            {
                Debug.LogWarning("[Launcher] 场景中存在多个 Launcher，已销毁后出现的那个");
                Destroy(gameObject);
                return;
            }
            Instance = this;
            DontDestroyOnLoad(gameObject);

            Screen.orientation = ScreenOrientation.AutoRotation;
            Screen.autorotateToPortrait = false;
            Screen.autorotateToPortraitUpsideDown = false;
            Screen.autorotateToLandscapeLeft = true;
            Screen.autorotateToLandscapeRight = true;

            for (int i = 0; i < _managers.Count; i++)
            {
                _managers[i].OnInit();
            }

            // M5-3：性能探针常驻（只在按 F3 / 到达自动打印间隔时才输出，平时零日志）
            PerfProbe.Ensure();

            // 所有管理器就绪后，把存档里的设置推给音频系统。
            // 【为什么放在循环之后】SaveManager 读档时 AudioManager 可能还没 OnInit，
            // 那时 ApplyToAudio 会因为 Instance 还没准备好而空转。
            SaveManager.Instance.ApplyToAudio();
        }

        private void Start()
        {
            if (_booted)
            {
                return;
            }
            _booted = true;
            BootResAndConfig();
        }

        /// <summary>
        /// 启动链（UI 补全 §5.1 重写）。
        ///
        /// 【旧实现的两个问题】
        ///   ① 全程黑屏静默：ResLoader.Init → Configs.LoadAsync 是纯嵌套回调，没有任何界面；
        ///   ② 没有热更新：发版后无法更新资源，只能整包重发。
        ///
        /// 【进度口径】LoadingView 只显示 [0,1] 的**总进度**，各阶段权重见常量：
        ///   资源系统 → 0.30；配置表 → 0.90；收尾 → 1.00；热更新有自己的界面与进度条，不占本进度。
        /// </summary>
        private void BootResAndConfig()
        {
            Phase = BootPhase.Splash;

            SplashView splash = UIManager.Instance.Open<SplashView>("SplashView", UILayout.NormalPanel);
            if (splash == null)
            {
                // 【降级】SplashView.prefab 还没生成时不阻塞启动 —— 直接进资源初始化。
                // 这条路径在"先写代码后跑生成器"的中间态下一定会走到，必须能跑通。
                Debug.LogWarning("[Launcher] SplashView 打开失败（prefab 可能还没生成），跳过开屏页");
                BeginLoadingRes();
                return;
            }

            EventDispatcher.AddEventListener(EventName.SplashFinishedEvent, OnSplashFinished);
        }

        private void OnSplashFinished()
        {
            EventDispatcher.RemoveEventListener(EventName.SplashFinishedEvent, OnSplashFinished);
            UIManager.Instance.Close("SplashView");
            BeginLoadingRes();
        }

        /// <summary>阶段②：资源系统初始化（LoadingView 0 → 0.3）。</summary>
        private void BeginLoadingRes()
        {
            Phase = BootPhase.Loading;
            LoadingView loading = UIManager.Instance.Open<LoadingView>("LoadingView", UILayout.NormalPanel);
            if (loading == null)
            {
                Debug.LogWarning("[Launcher] LoadingView 打开失败（prefab 可能还没生成），加载界面不可见");
            }
            PublishLoading("正在初始化资源系统...", 0f);

            ResLoader.Instance.Init(
                progress => PublishLoading("正在初始化资源系统...", progress * LoadingResWeight),
                () =>
                {
                    if (!ResLoader.Instance.IsReady)
                    {
                        Debug.LogError("[Launcher] 资源加载器初始化失败，启动中止。");
                        PublishLoadingFailed("资源系统初始化失败，请查看 Console");
                        EventDispatcher.TriggerEvent<bool>(EventName.ConfigLoadedEvent, false);
                        return;
                    }

                    PublishLoading("正在加载配置表...", LoadingResWeight);
                    BeginHotUpdate();
                });
        }

        /// <summary>统一发布加载进度（LoadingView 监听此事件，Launcher 不直接持有界面引用）。</summary>
        private static void PublishLoading(string phase, float progress)
        {
            EventDispatcher.TriggerEvent<string, float>(EventName.LoadingProgressEvent, phase, progress);
        }

        /// <summary>发布"加载失败"（LoadingView 会把状态文字转红，并把原因显示出来）。</summary>
        private static void PublishLoadingFailed(string reason)
        {
            EventDispatcher.TriggerEvent<string, float>(EventName.LoadingProgressEvent, reason, -1f);
        }

        /// <summary>阶段③：热更新（独立界面与进度条）。无需更新时立刻回到 Loading。</summary>
        private void BeginHotUpdate()
        {
            IHotUpdateLoader hot = ResLoader.HotUpdate;
            if (hot == null)
            {
                // 兜底：实现没接 IHotUpdateLoader 时视为"无需更新"
                BeginLoadingConfig();
                return;
            }

            Phase = BootPhase.HotUpdate;
            HotUpdateView hu = UIManager.Instance.Open<HotUpdateView>("HotUpdateView", UILayout.NormalPanel);
            if (hu == null)
            {
                // 【降级】没有热更新界面时不能把玩家卡在加载页：
                // 照常跑热更新逻辑（日志可查），只是没有可视化。
                Debug.LogWarning("[Launcher] HotUpdateView 打开失败（prefab 可能还没生成），热更新将无界面执行");
            }

            // 主加载界面让位给热更新界面（热更新有自己的进度条）
            UIManager.Instance.Close("LoadingView");

            hot.StartCheckUpdate(
                PublishHotUpdatePhase,
                (cur, total) => EventDispatcher.TriggerEvent<int, int, long, long>(
                    EventName.HotUpdateProgressEvent, cur, total, 0L, 0L),
                (bytes, totalBytes) => EventDispatcher.TriggerEvent<int, int, long, long>(
                    EventName.HotUpdateProgressEvent, -1, -1, bytes, totalBytes),
                OnHotUpdateError,
                OnHotUpdateDone);
        }

        /// <summary>发布热更新阶段文案（与进度分开：EventDispatcher 最多 4 个泛型参数）。</summary>
        private static void PublishHotUpdatePhase(string phase)
        {
            EventDispatcher.TriggerEvent<string>(EventName.HotUpdatePhaseEvent, phase);
        }

        private void OnHotUpdateError(string reason)
        {
            Debug.LogError("[Launcher] 热更新失败：" + reason);
            EventDispatcher.TriggerEvent<string>(EventName.HotUpdateFailedEvent, reason);

            // 【降级】没有热更新界面（prefab 还没生成）时没人接这个失败事件，
            // 玩家会永远停在"检查更新"——先按"无更新"继续，让人能玩到旧版本。
            if (!UIManager.Instance.IsOpen("HotUpdateView"))
            {
                Debug.LogWarning("[Launcher] 热更新界面不存在，按旧版本继续启动");
                BeginLoadingConfig();
            }
        }

        private void OnHotUpdateDone(bool updated)
        {
            EventDispatcher.TriggerEvent(EventName.HotUpdateFinishedEvent);
            StartCoroutine(FinishHotUpdate());
        }

        private System.Collections.IEnumerator FinishHotUpdate()
        {
            // 让"更新完成"至少显示一小会儿，否则玩家只看到进度条一闪就换了界面
            yield return new WaitForSecondsRealtime(HotUpdateDoneHoldSec);
            BeginLoadingConfig();
        }

        /// <summary>
        /// 「重试」入口（HotUpdateView 的 RetryBtn 调它）。
        /// 重新跑一遍热更新，而不是重启整个启动链 —— 资源系统已经初始化过了，
        /// 重跑 Init 反而会踩"重复初始化"的坑。
        /// </summary>
        public void RetryHotUpdate()
        {
            if (Phase != BootPhase.HotUpdate)
            {
                return;
            }
            BeginHotUpdate();
        }

        /// <summary>阶段④：配置表加载（LoadingView 0.3 → 0.9），随后收尾到 1.0。</summary>
        private void BeginLoadingConfig()
        {
            Phase = BootPhase.Loading;
            UIManager.Instance.Close("HotUpdateView");

            LoadingView loading = UIManager.Instance.Open<LoadingView>("LoadingView", UILayout.NormalPanel);
            if (loading == null)
            {
                Debug.LogWarning("[Launcher] LoadingView 打开失败（prefab 可能还没生成），配置加载将无界面执行");
            }
            PublishLoading("正在加载配置表...", LoadingResWeight);

            Configs.LoadAsync(
                (done, total) =>
                {
                    if (total <= 0)
                    {
                        return;
                    }
                    float ratio = done / (float)total;
                    PublishLoading("正在加载配置表...",
                        LoadingResWeight + (LoadingConfigEnd - LoadingResWeight) * ratio);
                },
                ok =>
                {
                    PublishLoading("正在准备关卡数据...", LoadingConfigEnd);

                    // 配置就绪后，CombatSystem 要按最终 cellSize 重建空间哈希
                    if (ok && CombatSystem.Instance != null)
                    {
                        CombatSystem.Instance.RebuildGridFromConfig();
                    }

                    if (!ok)
                    {
                        PublishLoadingFailed("配置表加载失败，请查看 Console");
                    }
                    else
                    {
                        PublishLoading("准备完成", 1f);
                    }

                    Phase = BootPhase.Ready;
                    StartCoroutine(FinishBoot(ok));
                });
        }

        private System.Collections.IEnumerator FinishBoot(bool ok)
        {
            // 让"准备完成"至少显示一帧，否则 100% 会一闪而过
            yield return new WaitForSecondsRealtime(0.25f);
            UIManager.Instance.Close("LoadingView");
            // GameFlowManager 收到后进主菜单（见 OnConfigLoaded）
            EventDispatcher.TriggerEvent<bool>(EventName.ConfigLoadedEvent, ok);
        }

        private void Update()
        {
            TimerManager.Instance.Update(Time.deltaTime);
            // CombatSystem 是唯一的 UpdateEvent 订阅者（见 CombatSystem.OnInit）
            EventDispatcher.TriggerEvent(EventName.UpdateEvent);
        }

        private void OnDestroy()
        {
            if (Instance != this)
            {
                return;
            }
            for (int i = 0; i < _managers.Count; i++)
            {
                _managers[i].OnDestroy();
            }
            Instance = null;
        }
    }
}
