using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace FTProject
{
    /// <summary>
    /// 关卡选择界面（M3-4）。
    ///
    /// 【为什么不把 8 个关卡按钮摆进 prefab，而是运行时生成】
    ///   摆进 prefab 意味着"改关卡数量就要改 prefab"，而且 8 个按钮的名字/星标/锁态
    ///   都要人工维护 —— 这正是本项目反复踩过的"生成物与代码分叉"。
    ///   改为：prefab 里只放**一个隐藏的模板按钮**，运行时按 TBSceneInfo 克隆。
    ///   加关卡 = 加配置行，界面自动多一个按钮。
    ///
    /// 【为什么用模板克隆而不是代码 new GameObject】
    ///   新建的 TMP 文本需要字体资产引用，而它就在 prefab 里（打包时才会被包含）。
    ///   克隆模板能天然继承字体、颜色、按钮过渡等一切设置。
    ///
    /// 【节点容错】与 TowerInfoView 同一口径：缺节点只警告、不阻断，
    ///   美术重排 prefab 时不会把功能一起弄坏。
    /// </summary>
    public class SelectView : MonoBehaviour
    {
        public const string LogicalName = "SelectView";

        /// <summary>关卡按钮的尺寸与间距（在 Panel/List 的局部坐标里手排，不依赖 LayoutGroup）</summary>
        private const float ButtonW = 240f;
        private const float ButtonH = 96f;
        private const float GapX = 24f;
        private const float GapY = 20f;
        private const int Columns = 4;

        private TMP_Text _title;
        private TMP_Text _summary;
        private RectTransform _list;
        private Button _closeBtn;

        private readonly List<GameObject> _spawned = new List<GameObject>();
        private Button _template;

        private void Awake()
        {
            BindNodes();
        }

        private void OnEnable()
        {
            Build();
        }

        private void BindNodes()
        {
            _title = FindText("Panel/Title");
            _summary = FindText("Panel/Summary");
            _list = FindRect("Panel/List");
            _closeBtn = FindButton("Panel/CloseBtn");

            Transform tpl = transform.Find("Panel/List/LevelButtonTemplate");
            if (tpl != null)
            {
                _template = tpl.GetComponent<Button>();
                tpl.gameObject.SetActive(false);   // 模板本身永远不显示
            }

            if (_closeBtn != null)
            {
                _closeBtn.onClick.AddListener(OnClickClose);
            }
            Button bg = FindButton("Bg");
            if (bg != null)
            {
                bg.onClick.AddListener(OnClickClose);
            }
        }

        // ------------------------------------------------------------------
        // 构建关卡列表
        // ------------------------------------------------------------------

        /// <summary>按 TBSceneInfo 重建关卡按钮。可重复调用（先清旧的）。</summary>
        public void Build()
        {
            for (int i = 0; i < _spawned.Count; i++)
            {
                if (_spawned[i] != null)
                {
                    Destroy(_spawned[i]);
                }
            }
            _spawned.Clear();

            if (_template == null)
            {
                Debug.LogWarning("[Select] prefab 里没有 Panel/List/LevelButtonTemplate，关卡列表无法生成");
                return;
            }
            if (Configs.LevelTable == null || Configs.LevelTable.DataList == null)
            {
                Debug.LogWarning("[Select] 配置表尚未加载，关卡列表为空");
                return;
            }

            List<cfg.SceneInfo> levels = Configs.LevelTable.DataList;
            for (int i = 0; i < levels.Count; i++)
            {
                cfg.SceneInfo raw = levels[i];
                if (raw == null)
                {
                    continue;
                }
                CreateLevelButton(raw, i);
            }

            RefreshHeader(levels.Count);
        }

        private void CreateLevelButton(cfg.SceneInfo raw, int index)
        {
            GameObject go = Instantiate(_template.gameObject, _template.transform.parent);
            go.name = "LevelButton_" + raw.Id;
            go.SetActive(true);
            _spawned.Add(go);

            RectTransform rt = go.GetComponent<RectTransform>();
            if (rt != null)
            {
                int col = index % Columns;
                int row = index / Columns;
                rt.anchorMin = new Vector2(0f, 1f);
                rt.anchorMax = new Vector2(0f, 1f);
                rt.pivot = new Vector2(0f, 1f);
                rt.sizeDelta = new Vector2(ButtonW, ButtonH);
                rt.anchoredPosition = new Vector2(col * (ButtonW + GapX), -row * (ButtonH + GapY));
            }

            int levelId = raw.Id;
            bool unlocked = SaveManager.Instance.IsUnlocked(levelId);
            int stars = SaveManager.Instance.GetStars(levelId);
            int diff = raw.Difficulty;

            TMP_Text label = go.GetComponentInChildren<TMP_Text>(true);
            if (label != null)
            {
                // 【字号必须比普通按钮小】关卡按钮只有 240×96，却要塞三行文案；
                //   沿用生成器的 32 号会让 3 行溢出到按钮外（表现为文字压在框上/框外）。
                //   富文本逐行给号，与效果图 01（26 / 26 / 22）对齐；
                //   基础字号也一并调小 —— 即便富文本标签失效，3 行（≈80px）仍落在 96px 内。
                // 【为什么要着色】效果图里实心星是金色、空心星与难度是暗蓝灰，
                //   全靠富文本在**一段文本内**分色，否则得拆成三个 TMP 节点。
                label.fontSize = 22f;
                label.text = string.Format(
                    "<size=26><color=#E8F0FA>{0}</color></size>\n" +
                    "<size=26>{1}</size>\n" +
                    "<size=20>{2}</size>",
                    raw.Name,
                    StarRichText(stars),
                    unlocked
                        ? "<color=#7A8CA6>" + Difficulty(diff) + "</color>"
                        : "<color=#5A6B80>未解锁</color>");
            }

            Button btn = go.GetComponent<Button>();
            if (btn != null)
            {
                // 未解锁也保持可点：点了给明确提示，比"灰着不响应"更容易让人理解为什么进不去
                btn.interactable = true;
                btn.onClick.AddListener(delegate { OnClickLevel(levelId, unlocked); });
            }
        }

        private void RefreshHeader(int levelCount)
        {
            int cleared = SaveManager.Instance.ClearedCount;
            int stars = SaveManager.Instance.TotalStars;
            // 数字提亮、星级用金色（效果图 01 的 Summary 配色）
            SetText(_summary, string.Format(
                "已通关 <color=#E8F0FA>{0}/{1}</color>　<color=#FFC94D>★ {2}/{3}</color>",
                cleared, levelCount, stars, levelCount * 3));
            SetText(_title, "选择关卡");
        }

        /// <summary>星级字符串。用实心/空心星而不是数字，一眼能扫完 8 关。</summary>
        public static string Stars(int n)
        {
            n = Mathf.Clamp(n, 0, 3);
            return new string('★', n) + new string('☆', 3 - n);
        }

        /// <summary>星级富文本：已得星金色、未得星暗蓝灰（效果图 01）。**公开**给结算界面复用，
        /// 否则"同一个星级在两处长得不一样"（与 Stars() 同样的理由）。</summary>
        public static string StarRichText(int n)
        {
            n = Mathf.Clamp(n, 0, 3);
            return "<color=#FFC94D>" + new string('★', n) + "</color>" +
                   "<color=#3F4E63>" + new string('☆', 3 - n) + "</color>";
        }

        public static string Difficulty(int d)
        {
            if (d <= 1) return "难度 Ⅰ";
            if (d == 2) return "难度 Ⅱ";
            return "难度 Ⅲ";
        }

        private void OnClickLevel(int levelId, bool unlocked)
        {
            if (!unlocked)
            {
                EventDispatcher.TriggerEvent<string>(EventName.ShowTipEvent, "先通关上一关才能解锁");
                return;
            }
            EventDispatcher.TriggerEvent<int>(EventName.SelectLevelRequestEvent, levelId);
        }

        private void OnClickClose()
        {
            EventDispatcher.TriggerEvent(EventName.CloseSelectRequestEvent);
        }

        // ------------------------------------------------------------------
        // 节点查找（容错）
        // ------------------------------------------------------------------

        private TMP_Text FindText(string path)
        {
            Transform tr = transform.Find(path);
            if (tr == null)
            {
                Debug.LogWarning("[Select] 缺少文本节点「" + path + "」");
                return null;
            }
            return tr.GetComponent<TMP_Text>();
        }

        private Button FindButton(string path)
        {
            Transform tr = transform.Find(path);
            if (tr == null)
            {
                Debug.LogWarning("[Select] 缺少按钮节点「" + path + "」");
                return null;
            }
            return tr.GetComponent<Button>();
        }

        private RectTransform FindRect(string path)
        {
            Transform tr = transform.Find(path);
            if (tr == null)
            {
                Debug.LogWarning("[Select] 缺少容器节点「" + path + "」");
                return null;
            }
            return tr as RectTransform;
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
