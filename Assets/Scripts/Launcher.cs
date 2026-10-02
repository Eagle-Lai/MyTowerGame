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
        public static Launcher Instance { get; private set; }

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

        private void BootResAndConfig()
        {
            // ① 资源加载器
            ResLoader.Instance.Init(() =>
            {
                if (!ResLoader.Instance.IsReady)
                {
                    Debug.LogError("[Launcher] 资源加载器初始化失败，启动中止。");
                    EventDispatcher.TriggerEvent<bool>(EventName.ConfigLoadedEvent, false);
                    return;
                }

                // ② 配置表
                Configs.LoadAsync(ok =>
                {
                    // ③ 配置就绪后，CombatSystem 要按最终 cellSize 重建空间哈希
                    if (ok && CombatSystem.Instance != null)
                    {
                        CombatSystem.Instance.RebuildGridFromConfig();
                    }
                    EventDispatcher.TriggerEvent<bool>(EventName.ConfigLoadedEvent, ok);
                });
            });
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
