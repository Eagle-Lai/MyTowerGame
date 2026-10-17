using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace FTProject
{
    /// <summary>
    /// 主菜单（UI 补全 B1 / 效果图 18_MainMenuView.svg）。
    ///
    /// 【它解决什么问题】改造前开机直接进关卡选择，没有"开始游戏 / 图鉴 / 设置 / 退出"的入口页，
    /// 玩家第一次进来会莫名其妙地站在选关页上。
    ///
    /// 【为什么所有按钮都发事件、不直接操作】
    ///   主菜单是"门面"，不该知道 SelectView 怎么开、设置界面挂在哪一层。
    ///   统一由 GameFlowManager 收事件再决定，改跳转逻辑时不用动本类。
    /// </summary>
    public class MainMenuView : MonoBehaviour
    {
        public const string LogicalName = "MainMenuView";

        private static readonly Color Cyan = new Color(0.208f, 0.878f, 1f, 1f);           // #35E0FF
        private static readonly Color Gold = new Color(1f, 0.788f, 0.302f, 1f);           // #FFC94D
        private static readonly Color TextSecondary = new Color(0.624f, 0.702f, 0.784f, 1f);
        private static readonly Color TextTertiary = new Color(0.369f, 0.451f, 0.588f, 1f);

        private TMP_Text _title;
        private TMP_Text _subtitle;
        private TMP_Text _starText;
        private TMP_Text _clearText;
        private TMP_Text _version;
        private Button _startBtn;
        private Button _codexBtn;
        private Button _settingBtn;
        private Button _quitBtn;

        private void Awake()
        {
            _title = FindText("Panel/GameTitle");
            _subtitle = FindText("Panel/Subtitle");
            _starText = FindText("Panel/StatBg/StarText");
            _clearText = FindText("Panel/StatBg/ClearText");
            _version = FindText("Panel/Version");
            _startBtn = FindButton("Panel/StartBtn");
            _codexBtn = FindButton("Panel/CodexBtn");
            _settingBtn = FindButton("Panel/SettingBtn");
            _quitBtn = FindButton("Panel/QuitBtn");

            if (_startBtn != null) _startBtn.onClick.AddListener(OnClickStart);
            if (_codexBtn != null) _codexBtn.onClick.AddListener(OnClickCodex);
            if (_settingBtn != null) _settingBtn.onClick.AddListener(OnClickSetting);
            if (_quitBtn != null) _quitBtn.onClick.AddListener(OnClickQuit);

            if (_title != null) _title.color = Cyan;
            if (_subtitle != null) _subtitle.color = TextSecondary;
            if (_starText != null) _starText.color = Gold;
            if (_clearText != null) _clearText.color = TextSecondary;
            if (_version != null)
            {
                _version.color = TextTertiary;
                // 底部中间版本行（P：版本号显示与日志）：显示"应用版本 · 资源版本"。
                // 资源版本来自 YooAsset 激活清单 —— 热更完成后进主菜单，这里自动变成新版本；
                // 编辑器直读 / 纯 AB 模式下资源版本拿不到，只显示应用版本。
                // 打开主菜单时资源系统必然已 Init（配置表都加载完了），此时取值即最终版本。
                _version.text = VersionInfo.BuildDisplayVersion();
            }
        }

        private void OnEnable()
        {
            RefreshStats();
            Subscribe();
        }

        private void OnDisable()
        {
            Unsubscribe();
        }

        // ------------------------------------------------------------------
        // 语言切换（2026-10-16）
        // 【为什么主菜单要听这个】设置界面就从主菜单的「SettingsBtn」进 —— 打开设置时
        //   主菜单在全屏遮罩背后；切完语言关闭设置，立刻会看到它。静态文案由 TextLocalizer
        //   自动刷新，这里补的是"代码手动拼出来的动态文本"（通关进度行）。
        // ------------------------------------------------------------------

        private bool _subscribed;

        private void Subscribe()
        {
            if (_subscribed)
            {
                return;
            }
            EventDispatcher.AddEventListener<int>(EventName.LanguageChangedEvent, OnLanguageChanged);
            _subscribed = true;
        }

        private void Unsubscribe()
        {
            if (!_subscribed)
            {
                return;
            }
            EventDispatcher.RemoveEventListener<int>(EventName.LanguageChangedEvent, OnLanguageChanged);
            _subscribed = false;
        }

        private void OnLanguageChanged(int lang)
        {
            RefreshStats();
        }

        /// <summary>
        /// 刷新玩家总览。**全部实时读存档，绝不硬编码** ——
        /// 硬编码的"12/24"在加了新关卡之后必然与实际不符，而且没人会想起来改。
        /// </summary>
        private void RefreshStats()
        {
            int totalLevels = Configs.LevelTable != null && Configs.LevelTable.DataList != null
                ? Configs.LevelTable.DataList.Count
                : 0;
            SaveManager sm = SaveManager.Instance;
            if (sm != null)
            {
                SetText(_starText, string.Format("{0}/{1}", sm.TotalStars, totalLevels * LevelRatingEvaluator.MaxStars));
                SetText(_clearText, Localization.Get("Cleared {0}/{1}", sm.ClearedCount, totalLevels)
                    ?? string.Format("已通关 {0}/{1}", sm.ClearedCount, totalLevels));
            }
            else
            {
                SetText(_starText, string.Format("0/{0}", totalLevels * LevelRatingEvaluator.MaxStars));
                SetText(_clearText, Localization.Get("Cleared {0}/{1}", 0, totalLevels)
                    ?? string.Format("已通关 0/{0}", totalLevels));
            }

            // 字体跟随语言（这两行是手动拼写的文本，不在 TextLocalizer 管辖内）
            LanguageManager.ApplyFont(_starText);
            LanguageManager.ApplyFont(_clearText);
        }

        // ------------------------------------------------------------------
        // 操作 → 事件
        // ------------------------------------------------------------------

        private void OnClickStart()
        {
            EventDispatcher.TriggerEvent(EventName.StartGameRequestEvent);
        }

        private void OnClickCodex()
        {
            // 参数 true = 塔图鉴；怪物图鉴用 false（同一事件，少一个事件名）
            EventDispatcher.TriggerEvent<bool>(EventName.OpenCodexRequestEvent, true);
        }

        private void OnClickSetting()
        {
            EventDispatcher.TriggerEvent(EventName.OpenSettingsRequestEvent);
        }

        private void OnClickQuit()
        {
            // 退出是"不可撤销"的（对玩家来说等于关掉游戏），必须先确认
            ConfirmView.Show(
                Localization.Get("Quit Game") ?? "退出游戏",
                Localization.Get("Are you sure you want to quit?") ?? "确定要退出游戏吗？",
                ConfirmType.Warning, DoQuit,
                Localization.Get("Quit") ?? "退出",
                Localization.Get("Cancel") ?? "取消");
        }

        private static void DoQuit()
        {
#if UNITY_EDITOR
            // 编辑器里 Application.Quit() 没有任何效果，会让人以为按钮坏了
            UnityEditor.EditorApplication.isPlaying = false;
#else
            Application.Quit();
#endif
        }

        private static void SetText(TMP_Text t, string v)
        {
            if (t != null && t.text != v)
            {
                t.text = v;
            }
        }

        private TMP_Text FindText(string path)
        {
            Transform tr = transform.Find(path);
            if (tr == null)
            {
                Debug.LogWarning("[MainMenu] 缺少文本节点「" + path + "」");
                return null;
            }
            return tr.GetComponent<TMP_Text>();
        }

        private Button FindButton(string path)
        {
            Transform tr = transform.Find(path);
            if (tr == null)
            {
                Debug.LogWarning("[MainMenu] 缺少按钮节点「" + path + "」");
                return null;
            }
            return tr.GetComponent<Button>();
        }
    }
}
