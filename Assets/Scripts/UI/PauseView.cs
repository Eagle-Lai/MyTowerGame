using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace FTProject
{
    /// <summary>
    /// 暂停界面（M3-6）。
    ///
    /// 【暂停是怎么实现的】Time.timeScale = 0 + 一个自绘的半透明遮罩。
    ///   【为什么必须由本界面负责恢复】如果暂停后直接销毁界面而不恢复 timeScale，
    ///   游戏会永久卡住 —— 这是暂停功能最经典的 bug。所以：
    ///     · OnDisable 里无条件恢复 timeScale（覆盖"被别处销毁"的情况）
    ///     · 按钮点击用 unscaled 语义（见各 OnClick 的注释），否则 timeScale=0 时按钮反馈会僵住
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

            if (_title != null)
            {
                _title.text = "暂停";
            }
        }

        private void OnEnable()
        {
            Time.timeScale = 0f;
        }

        /// <summary>
        /// 【关键】无论因为什么原因被关掉/销毁，都必须把时间恢复回来。
        /// 放在 OnDisable 而不是各个按钮里，是为了覆盖"被 UIManager 直接关掉"这类路径。
        /// </summary>
        private void OnDisable()
        {
            Time.timeScale = 1f;
        }

        private void OnClickResume()
        {
            EventDispatcher.TriggerEvent(EventName.ResumeRequestEvent);
        }

        private void OnClickRestart()
        {
            // 先恢复时间再重开：否则新一局会在 timeScale=0 下启动，看起来像卡死
            Time.timeScale = 1f;
            EventDispatcher.TriggerEvent(EventName.RestartLevelRequestEvent);
        }

        private void OnClickSettings()
        {
            EventDispatcher.TriggerEvent(EventName.OpenSettingsRequestEvent);
        }

        private void OnClickQuit()
        {
            Time.timeScale = 1f;
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
