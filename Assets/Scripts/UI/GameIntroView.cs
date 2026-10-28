using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace FTProject
{
    /// <summary>
    /// 游戏介绍弹窗（2026-10-14 新增，原由 HUD 右上角「游戏介绍」按钮打开）。
    ///
    /// 【2026-10-18 现状：暂无入口】HUD 的 Btn_Intro 已改为打开暂停菜单（PauseView），
    ///   本弹窗的按钮入口随之撤下；界面资产、多语言词条、事件链路
    ///   （OpenGameIntroRequestEvent → GameFlowManager.OnOpenGameIntroRequest）全部保留，
    ///   将来要恢复入口只需加一颗按钮发那个事件，不用改本文件。
    ///
    /// 【需求契约】弹窗中必须包含一个「回到选关」按钮，点击后返回关卡选择界面 ——
    ///   走 QuitToSelectRequestEvent（与暂停界面的退出、结算弹窗的返回完全同源），
    ///   由 GameFlowManager.QuitToSelect 统一拆卸关卡（TeardownLevel）并打开选关。
    ///   本界面不自己拆关卡 —— "UI 只发事件，流程层决定干什么"是本工程的铁律。
    ///
    /// 【为什么不碰 timeScale】本弹窗是"查阅型"界面，打开期间战斗照常进行
    ///   （想暂停请用旁边的暂停按钮）。若在这里也压 timeScale，就要处理
    ///   "暂停界面 → 介绍弹窗"的嵌套恢复顺序，复杂度换不来收益。
    ///   副作用是关闭必须显式：CloseBtn 直接 UIManager.Close 自己（见下）。
    ///
    /// 【正文四行是动态文本】Info1..Info4 在 LocalizationPrefabBinder.DynamicNames
    ///   里被排除（运行时代码赋值的节点不挂 TextLocalizer），所以这里在 Awake
    ///   主动按当前语言查表；按钮标签是静态文案（BackBtn/CloseBtn 的 Label），
    ///   由生成器写入英文原文 + 批量挂 TextLocalizer 自动切语言。
    /// </summary>
    public class GameIntroView : MonoBehaviour
    {
        /// <summary>ResTable / UIManager 用的逻辑名（与 prefab 名逐字相同）。</summary>
        public const string LogicalName = "GameIntroView";

        private Button _backBtn;
        private Button _closeBtn;
        private TMP_Text _title;
        private TMP_Text[] _infos;
        private bool _fromBriefing;
        public void SetBriefingSource(bool value) { _fromBriefing=value; if(_backBtn!=null)_backBtn.gameObject.SetActive(!value); }

        /// <summary>正文四行的多语言 key（key = 英文原文，表的主键口径）。</summary>
        private static readonly string[] InfoKeys =
        {
            "Stop the monsters before they reach your base: build towers on the open tiles beside the path.",
            "Long-press a tower button, drag it onto the board, then release to build.",
            "You may slow the monsters down, but never fully block their path.",
            "Survive every round to win the level.",
        };

        /// <summary>表未就绪/缺 key 时的中文兜底（与 InfoKeys 一一对应，保证零破坏）。</summary>
        private static readonly string[] InfoFallbacks =
        {
            "在怪物途经的路边空地建造防御塔，阻止它们抵达你的基地。",
            "长按建造栏的塔按钮，拖到棋盘格子上松手即可建造（金币在落地成功后扣除）。",
            "你可以拖慢怪物的脚步，但不能把它们的路完全堵死。",
            "撑过全部回合即通关。",
        };

        private void Awake()
        {
            _title = FindText("Panel/Title");
            _infos = new TMP_Text[InfoKeys.Length];
            for (int i = 0; i < InfoKeys.Length; i++)
            {
                _infos[i] = FindText("Panel/Info" + (i + 1));
            }

            _backBtn = FindButton("Panel/BackBtn");
            _closeBtn = FindButton("Panel/CloseBtn");
            if (_backBtn != null)
            {
                _backBtn.onClick.AddListener(OnClickBack);
            }
            if (_closeBtn != null)
            {
                _closeBtn.onClick.AddListener(OnClickClose);
            }
        }

        /// <summary>
        /// 每次打开按当前语言重建标题与正文四行。
        /// 【为什么必须在 OnEnable 重建】UIManager 池化复用实例（Awake 只跑一次），
        /// 而语言可以在暂停界面随时切换 —— 若只在 Awake 赋值，二次打开会显示上一次
        /// 语言的残留（2026-10-16 多语言审计修复）。
        /// </summary>
        private void OnEnable()
        {
            SetBriefingSource(false);
            Refresh();
        }

        private void Refresh()
        {
            if (_title != null)
            {
                _title.text = Localization.Get("Game Intro") ?? "游戏介绍";
                LanguageManager.ApplyFont(_title);
            }
            if (_infos != null)
            {
                for (int i = 0; i < _infos.Length; i++)
                {
                    if (_infos[i] != null)
                    {
                        _infos[i].text = Localization.Get(InfoKeys[i]) ?? InfoFallbacks[i];
                        LanguageManager.ApplyFont(_infos[i]);
                    }
                }
            }
        }

        /// <summary>「回到选关」：发退出对局事件（口径与 PauseView.OnClickQuit 一致）。</summary>
        private void OnClickBack()
        {
            // 【真机诊断埋点】"点回到选关没反应"排查链第一环；
            // 后续链路：QuitToSelectRequestEvent → GameFlowManager.QuitToSelect → TeardownLevel。
            Debug.Log("[Intro] 点击回到选关");
            // 【2026-10-18】不再在这里写 Time.timeScale：暂停的唯一写入口是
            //   GameClock.SetPaused(false)，而退出对局走 TeardownLevel 时已经统一解除暂停。
            //   UI 再写一次会与流程层状态脱钩（例如把别处设好的暂停态冲掉）。
            EventDispatcher.TriggerEvent(EventName.QuitToSelectRequestEvent);
        }

        /// <summary>「关闭」：只关自己，不打断对局。TeardownLevel 也会兜底关本界面。</summary>
        private void OnClickClose()
        {
            Debug.Log("[Intro] 点击关闭");
            UIManager.Instance.Close(LogicalName);
        }

        // （与 PauseView 同口径：缺节点只警告、不阻断 —— 介绍弹窗缺正文不至于卡玩法）
        private TMP_Text FindText(string path)
        {
            Transform tr = transform.Find(path);
            if (tr == null)
            {
                Debug.LogWarning("[Intro] 缺少文本节点「" + path + "」");
                return null;
            }
            return tr.GetComponent<TMP_Text>();
        }

        private Button FindButton(string path)
        {
            Transform tr = transform.Find(path);
            if (tr == null)
            {
                Debug.LogWarning("[Intro] 缺少按钮节点「" + path + "」");
                return null;
            }
            return tr.GetComponent<Button>();
        }
    }
}
