using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace FTProject
{
    /// <summary>
    /// 暂停菜单弹窗（M3-6；2026-10-18 起与"暂停"解耦）。
    ///
    /// 【它现在是什么】一个**菜单浮层**：继续 / 重开 / 设置 / 退出选关。
    ///   入口 = HUD 右上角 Btn_Intro（原 Btn_Pause 的弹窗能力迁移过来）。
    ///   标题按状态取词：已暂停 → `Game Paused`；未暂停 → `Menu`（见 Refresh）。
    ///   （Btn_Intro 的按钮文案 2026-10-18 也从 `Game Intro` 改成了 `Menu`，与之对应）
    ///
    /// 【为什么不再碰 timeScale】2026-10-18 的需求把两件事拆开了：
    ///   · 暂停/继续 = Btn_Pause（或热键 P）→ GameFlowManager.TogglePause → GameClock.SetPaused；
    ///   · 打开本菜单 = 只摆 UI，不改变游戏时间（点 Btn_Intro 不该把游戏停住）。
    ///   所以本界面**不再在 OnEnable 压 timeScale、也不在 OnDisable 恢复**——
    ///   那种"界面负责暂停"的写法会在"开着菜单被人从别处解除暂停"时把时间又写回去，
    ///   与流程层的暂停状态互相打架（这正是本次要清理的遗留耦合）。
    ///   时间恢复的唯一入口是 GameClock.SetPaused(false)（GameFlowManager 负责）。
    ///
    /// 【本界面不做的事】不改任何游戏数值，只发事件；真正的重开/退出由 GameFlowManager 执行。
    /// </summary>
    public class PauseView : MonoBehaviour
    {
        public const string LogicalName = "PauseView";

        private Button _resumeBtn;
        private Button _restartBtn;
        private Button _settingsBtn;
        private Button _quitBtn;
        private TMP_Text _title;

        private void Awake()
        {
            _title = FindText("Panel/Title");
            _resumeBtn = FindButton("Panel/ResumeBtn");
            _restartBtn = FindButton("Panel/RestartBtn");
            _settingsBtn = FindButton("Panel/SettingsBtn");
            _quitBtn = FindButton("Panel/QuitBtn");

            if (_resumeBtn != null) _resumeBtn.onClick.AddListener(OnClickResume);
            if (_restartBtn != null) _restartBtn.onClick.AddListener(OnClickRestart);
            if (_settingsBtn != null) _settingsBtn.onClick.AddListener(OnClickSettings);
            if (_quitBtn != null) _quitBtn.onClick.AddListener(OnClickQuit);

            // 标题文案不在这里写死：挪到 Refresh() —— UIManager 池化复用实例（Awake 只跑一次），
            // 且语言随时可能被切，必须在每次打开时按当前语言重建（见 Refresh / OnLanguageChanged）。
        }

        private void OnEnable()
        {
            // 注意：这里**不写 Time.timeScale**（见类注释）。暂停由流程层独占。
            Refresh();
            Subscribe();
        }

        /// <summary>
        /// 关闭时同样不碰 timeScale：本界面可能是在"游戏正常运行"时打开的，
        /// 关掉它不该顺手暂停/恢复任何东西（原先无条件 Time.timeScale = 1f 会把
        /// 别处设好的暂停态冲掉）。
        /// </summary>
        private void OnDisable()
        {
            Unsubscribe();
        }

        // ------------------------------------------------------------------
        // 语言切换（2026-10-16）
        // 【为什么暂停界面要听这个】设置界面也可以从暂停界面的「SettingsBtn」进 ——
        //   切完语言关闭设置，看到的就是暂停界面：标题必须已是新语言。
        //   （标题走手动 Refresh：它在批量挂载工具的动态文本排除名单里，不挂 TextLocalizer。）
        // ------------------------------------------------------------------

        private bool _subscribed;

        private void Refresh()
        {
            if (_title != null)
            {
                // 【标题为什么按状态取词】本菜单可以在"游戏正常运行"时打开（Btn_Intro），
                //   这时写"已暂停"就是假话。所以：
                //     已暂停 → Game Paused（暂停）；未暂停 → Menu（菜单）。
                //   两个 key 都在多语言表里（Menu = 2026-10-18 新增），缺表时才用中文兜底。
                string text = GameClock.IsPaused
                    ? (Localization.Get("Game Paused") ?? "暂停")
                    : (Localization.Get("Menu") ?? "菜单");
                _title.text = text;
                LanguageManager.ApplyFont(_title);
            }
        }

        private void Subscribe()
        {
            if (_subscribed)
            {
                return;
            }
            EventDispatcher.AddEventListener<int>(EventName.LanguageChangedEvent, OnLanguageChanged);
            // 暂停状态可能在菜单开着时变化（热键 P / 别的入口），标题要跟着切
            EventDispatcher.AddEventListener<bool>(EventName.PauseStateChangedEvent, OnPauseStateChanged);
            _subscribed = true;
        }

        private void Unsubscribe()
        {
            if (!_subscribed)
            {
                return;
            }
            EventDispatcher.RemoveEventListener<int>(EventName.LanguageChangedEvent, OnLanguageChanged);
            EventDispatcher.RemoveEventListener<bool>(EventName.PauseStateChangedEvent, OnPauseStateChanged);
            _subscribed = false;
        }

        private void OnLanguageChanged(int lang)
        {
            Refresh();
        }

        private void OnPauseStateChanged(bool paused)
        {
            Refresh();
        }

        private void OnClickResume()
        {
            EventDispatcher.TriggerEvent(EventName.ResumeRequestEvent);
        }

        private void OnClickRestart()
        {
            // 【为什么这里不再写 timeScale】重开走 RestartLevel → StartLevel → TeardownLevel，
            //   而 TeardownLevel 里已经有唯一的解除暂停入口（GameClock.SetPaused(false)）。
            //   在 UI 里再写一次就是双写，容易与流程层状态脱钩。
            EventDispatcher.TriggerEvent(EventName.RestartLevelRequestEvent);
        }

        private void OnClickSettings()
        {
            EventDispatcher.TriggerEvent(EventName.OpenSettingsRequestEvent);
        }

        private void OnClickQuit()
        {
            // 同上：退出对局由 QuitToSelect → TeardownLevel 统一解除暂停
            EventDispatcher.TriggerEvent(EventName.QuitToSelectRequestEvent);
        }

        private TMP_Text FindText(string path)
        {
            Transform tr = transform.Find(path);
            if (tr == null)
            {
                Debug.LogWarning("[Pause] 缺少文本节点「" + path + "」");
                return null;
            }
            return tr.GetComponent<TMP_Text>();
        }

        private Button FindButton(string path)
        {
            Transform tr = transform.Find(path);
            if (tr == null)
            {
                Debug.LogWarning("[Pause] 缺少按钮节点「" + path + "」");
                return null;
            }
            return tr.GetComponent<Button>();
        }
    }
}
