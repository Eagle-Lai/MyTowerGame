using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace FTProject
{
    /// <summary>
    /// 关卡结算弹窗（通关 / 失败）。
    ///
    /// ==================================================================
    /// 【为什么会有这个文件：原来根本没有"通关弹窗"】
    ///   GameFlowManager 在全部回合结束后只做了三件事：写档、触发 LevelClearEvent、
    ///   弹一条 Tips 文字。而 **LevelClearEvent 在全工程没有任何监听者** ——
    ///   事件空放，玩家自然看不到任何"通关完成"的界面。
    ///   本类就是那个缺失的接收端，改由 GameFlowManager 在 OnGameOver 里打开并 Show()。
    ///
    /// 【为什么星级要在这里显示两遍（本次 / 历史最高）】
    ///   "这个成绩好不好"只有跟自己的历史比才有意义。存档里的星级是**只升不降**的合并值，
    ///   所以如果把"本次所得"和"存档里的值"当成一回事：
    ///     · 玩家第二次打出 1 星时，界面会显示 3 星（历史最高）→ 看起来像"这次打得很好"；
    ///     · 再配上"新纪录"提示就会自相矛盾。
    ///   因此 LevelClearInfo 里同时带 stars（本次）与 previousBest（本局之前的最好成绩），
    ///   两行分开展示，谁也不冒充谁。
    ///
    /// 【本类不做的事】不改任何游戏数值、不直接碰存档 —— 统计与落库都在 GameFlowManager
    ///   与 SaveManager 里完成，本类只负责"把已经算好的结果画出来"并发事件。
    ///   这样结算逻辑无论怎么改，都不会因为界面被销毁/复用而算错。
    /// ==================================================================
    /// </summary>
    public class LevelClearView : MonoBehaviour
    {
        public const string LogicalName = "LevelClearView";

        private TMP_Text _title;
        private TMP_Text _levelName;
        private TMP_Text _stars;
        private TMP_Text _starDetail;
        private TMP_Text _recordTip;
        private TMP_Text _stats;
        private Button _nextBtn;
        private TMP_Text _nextLabel;
        private Button _retryBtn;
        private TMP_Text _retryLabel;
        private Button _selectBtn;

        /// <summary>当前展示的结算数据。按钮回调要用到 nextLevelId / hasNext。</summary>
        private LevelClearInfo _info;

        private void Awake()
        {
            BindNodes();
        }

        private void BindNodes()
        {
            _title = FindText("Panel/Title");
            _levelName = FindText("Panel/LevelName");
            _stars = FindText("Panel/Stars");
            _starDetail = FindText("Panel/StarDetail");
            _recordTip = FindText("Panel/RecordTip");
            _stats = FindText("Panel/Stats");

            _nextBtn = FindButton("Panel/NextBtn");
            _nextLabel = FindText("Panel/NextBtn/Label");
            _retryBtn = FindButton("Panel/RetryBtn");
            _retryLabel = FindText("Panel/RetryBtn/Label");
            _selectBtn = FindButton("Panel/SelectBtn");

            if (_nextBtn != null) _nextBtn.onClick.AddListener(OnClickNext);
            if (_retryBtn != null) _retryBtn.onClick.AddListener(OnClickRetry);
            if (_selectBtn != null) _selectBtn.onClick.AddListener(OnClickSelect);

            // 【为什么 Bg 不绑"点击关闭"】其它对话框（设置/暂停/选关）点背景即关闭是合理的，
            //   它们随时能再开；但结算弹窗是一个**终结状态**，随手点掉之后玩家会卡在
            //   "关卡已结束、却没有任何入口推进"的死角里（只剩暂停键可走）。
            //   所以这里刻意留空：Bg 仍然吞掉点击（挡住下面的 HUD），但必须明确点一个按钮。
            //   注意：prefab 里 Bg 自带 Button 组件（CreateDialogShell 统一给的），只是没接回调。
        }

        /// <summary>
        /// 用一局结算数据刷新弹窗。由 GameFlowManager 在打开界面后立刻调用。
        /// 【为什么不是 OnEnable 里自己算】界面不该知道存档与流程的存在 ——
        ///   否则它被复用（对象池）时算出来的可能是上一局的结果。
        /// </summary>
        public void Show(LevelClearInfo info)
        {
            _info = info;
            if (info == null)
            {
                return;
            }

            SetText(_title, info.victory ? "通关完成！" : "防御失败");
            SetText(_levelName, string.IsNullOrEmpty(info.levelName)
                ? string.Format("关卡 {0}", info.levelId)
                : info.levelName);

            // ---- 星级评价 ----
            // 星星字形统一走 SelectView.StarRichText，避免"同一个星级在两处长得不一样"
            // （金色实心 + 暗蓝灰空心，与效果图 05 一致）
            SetText(_stars, SelectView.StarRichText(info.stars));

            if (info.victory)
            {
                SetText(_starDetail, string.Format(
                    "<color=#9FB3C8>本次</color> {0}　　<color=#9FB3C8>历史最高</color> {1}",
                    SelectView.StarRichText(info.stars), SelectView.StarRichText(info.previousBest)));
            }
            else
            {
                // 失败不给星，但历史成绩仍然要显示 —— 这正是"重新进游戏也能看到记录"的体现
                SetText(_starDetail, string.Format(
                    "<color=#9FB3C8>历史最高</color> {0}",
                    SelectView.StarRichText(info.previousBest)));
            }

            // "新纪录"只在真的超过历史最好成绩时出现
            if (_recordTip != null)
            {
                bool show = info.victory && info.newRecord;
                if (_recordTip.gameObject.activeSelf != show)
                {
                    _recordTip.gameObject.SetActive(show);
                }
                if (show)
                {
                    SetText(_recordTip, "★ 新纪录！刷新了本关最高星级");
                }
            }

            // ---- 战绩 ----
            SetText(_stats, string.Format("剩余生命 {0}/{1}　　击杀 {2}　　漏怪 {3}",
                info.hp, info.maxHp, info.killed, info.leaked));

            // ---- 按钮 ----
            // 三种情况分开处理，避免"最后一关却显示一个可点的下一关"或
            // "失败时显示已是最后一关"这类自相矛盾的文案。
            if (_nextBtn != null)
            {
                if (!info.victory)
                {
                    _nextBtn.gameObject.SetActive(false);          // 失败没有下一关可言
                }
                else
                {
                    bool canGo = info.hasNext && info.nextLevelId > 0;
                    _nextBtn.gameObject.SetActive(true);
                    _nextBtn.interactable = canGo;
                    if (!canGo)
                    {
                        SetText(_nextLabel, "已是最后一关");
                    }
                    else if (!string.IsNullOrEmpty(info.nextLevelName))
                    {
                        SetText(_nextLabel, "下一关：" + info.nextLevelName);
                    }
                    else
                    {
                        SetText(_nextLabel, "下一关");
                    }
                }
            }

            SetText(_retryLabel, info.victory ? "重玩本关" : "重新挑战");
        }

        // ------------------------------------------------------------------
        // 交互 → 事件（真正的跳转由 GameFlowManager 执行，见其事件监听）
        // ------------------------------------------------------------------

        private void OnClickNext()
        {
            if (_info == null || !_info.hasNext || _info.nextLevelId <= 0)
            {
                return;
            }
            // 复用「选择关卡」请求，让下一关和玩家手点关卡走**同一条**入口（StartLevel），
            // 否则两套启动路径迟早分叉。
            EventDispatcher.TriggerEvent<int>(EventName.SelectLevelRequestEvent, _info.nextLevelId);
        }

        private void OnClickRetry()
        {
            EventDispatcher.TriggerEvent(EventName.RestartLevelRequestEvent);
        }

        private void OnClickSelect()
        {
            EventDispatcher.TriggerEvent(EventName.QuitToSelectRequestEvent);
        }

        // ------------------------------------------------------------------
        // 节点查找（与 SettingView / PauseView 同口径：缺节点只警告、不阻断）
        // ------------------------------------------------------------------

        private TMP_Text FindText(string path)
        {
            Transform tr = transform.Find(path);
            if (tr == null)
            {
                Debug.LogWarning("[Clear] 缺少文本节点「" + path + "」");
                return null;
            }
            return tr.GetComponent<TMP_Text>();
        }

        private Button FindButton(string path)
        {
            Transform tr = transform.Find(path);
            if (tr == null)
            {
                Debug.LogWarning("[Clear] 缺少按钮节点「" + path + "」");
                return null;
            }
            return tr.GetComponent<Button>();
        }

        private static void SetText(TMP_Text t, string v)
        {
            if (t != null && t.text != v)
            {
                t.text = v;
            }
        }
    }
}
