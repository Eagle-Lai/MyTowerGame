using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace FTProject
{
    /// <summary>
    /// 塔图鉴的一张卡片（UI 补全 B2）。
    ///
    /// 【为什么卡片必须有脚本】图鉴是**同一个 prefab 被池化复用 3 次**（LoopListView2 的机制，
    /// 2026-10-14 起塔型收敛为三类），一次显示、一次回收再填别的塔 ——
    /// 所以内容只能在运行时灌进去，不能烘死在 prefab 里。
    ///
    /// 【缩放/淡化挂在 Body 而不是根节点】LoopListView2 的条目根节点 pivot 固定 (0,0.5)，
    /// 缩放根节点会让卡片围绕左缘缩放 → 视觉上"居中卡左右空隙一宽一窄"。
    /// </summary>
    public class TowerCodexItem : MonoBehaviour
    {
        [SerializeField] private Sprite[] portraits = new Sprite[3];

        public void ConfigurePortraits(Sprite[] sprites) { portraits = sprites; }

        /// <summary>The codex owns large portraits; battle HUD icons stay lightweight.</summary>
        public bool ApplyPortrait(int type)
        {
            int index = type - 1;
            if (portraits == null || index < 0 || index >= portraits.Length || portraits[index] == null) return false;
            if (_icon == null) _icon = FindImage("Body/Icon");
            if (_icon == null) return false;
            _icon.sprite = portraits[index]; _icon.color = Color.white; _icon.preserveAspect = true;
            return true;
        }
        private static readonly Color Cyan = new Color(0.208f, 0.878f, 1f, 1f);
        private static readonly Color Gold = new Color(1f, 0.788f, 0.302f, 1f);
        private static readonly Color TextPrimary = new Color(0.910f, 0.941f, 0.980f, 1f);
        private static readonly Color TextSecondary = new Color(0.624f, 0.702f, 0.784f, 1f);

        private RectTransform _body;
        private Image _cardBg;
        private Image _topBar;
        private Image _icon;
        private TMP_Text _typeName;
        private TMP_Text _role;
        private TMP_Text _dpsRow;
        private TMP_Text _rangeRow;
        private TMP_Text _speedRow;
        private TMP_Text _priceRow;
        private TMP_Text _desc;
        private TowerConfig _config;
        private bool _comparison;

        private void OnRectTransformDimensionsChange()
        {
            if(_body!=null)TacticalForgeLayout.ArrangeTowerCard(transform,_comparison);
        }

        /// <summary>供 LoopListView2 做缩放/淡化（挂在 Body 上，不缩根节点）。</summary>
        public RectTransform Body { get { return _body; } }

        private void Awake()
        {
            Transform bodyTr = transform.Find("Body");
            _body = bodyTr as RectTransform;
            _cardBg = FindImage("Body/CardBg");
            _topBar = FindImage("Body/TopBar");
            _icon = FindImage("Body/Icon");
            _typeName = FindText("Body/TypeName");
            _role = FindText("Body/Role");
            _dpsRow = FindText("Body/DpsRow");
            _rangeRow = FindText("Body/RangeRow");
            _speedRow = FindText("Body/SpeedRow");
            _priceRow = FindText("Body/PriceRow");
            _desc = FindText("Body/DescText");

            if (_typeName != null) _typeName.color = Cyan;
            if (_role != null) _role.color = TextSecondary;
            if (_dpsRow != null) _dpsRow.color = TextPrimary;
            if (_rangeRow != null) _rangeRow.color = TextPrimary;
            if (_speedRow != null) _speedRow.color = TextPrimary;
            if (_priceRow != null) _priceRow.color = Gold;
            if (_desc != null) _desc.color = TextSecondary;
        }

        /// <summary>回填一座塔的数据。全部取自配置，**没有任何硬编码数值**。</summary>
        public void SetData(TowerConfig cfg, string roleText)
        {
            if (cfg == null)
            {
                return;
            }

            _config = cfg;
            Color theme = ThemeColor(cfg.Type);
            if (_topBar != null) _topBar.color = theme;
            if (_typeName != null)
            {
                // DisplayName：过多语言表（"普通塔"），缺条目回退英文原文（"Normal Tower"）
                _typeName.text = cfg.DisplayName;
                _typeName.color = theme;
            }
            if (_role != null) _role.text = roleText;
            if (_dpsRow != null) _dpsRow.text = cfg.IsSlowAura
                ? (Localization.Get("Slow {0:P0} · DPS 0", cfg.EffectValue) ?? string.Format("减速 {0:P0} · DPS 0", cfg.EffectValue))
                : (Localization.Get("Damage   {0}", cfg.Power) ?? string.Format("伤害　{0}", cfg.Power));
            if (_rangeRow != null) _rangeRow.text = Localization.Get("Range    {0:F1}", cfg.RadiusGrid) ?? string.Format("射程　{0:F1} 格", cfg.RadiusGrid);
            if (_speedRow != null) _speedRow.text = cfg.IsSlowAura
                ? (Localization.Get("Aura refresh {0:0.00}s", cfg.CooldownSec) ?? string.Format("光环刷新　{0:0.00} 秒", cfg.CooldownSec))
                : (Localization.Get("Speed    {0:F2}", cfg.CooldownSec) ?? string.Format("攻速　{0:F2} 秒", cfg.CooldownSec));
            if (_priceRow != null) _priceRow.text = Localization.Get("Cost     {0}", cfg.Prices) ?? string.Format("造价　{0} 金币", cfg.Prices);
            if (_desc != null)
            {
                _desc.text = TowerPresentation.Description(cfg);
            }

            if (_icon != null && !ApplyPortrait(cfg.Type))
            {
                Sprite sprite = ResLoader.Instance.IsReady
                    ? ResLoader.Instance.Load<Sprite>("UI_TowerIcon_" + IconSuffix(cfg.Type))
                    : null;
                if (sprite != null)
                {
                    _icon.sprite = sprite;
                    _icon.color = Color.white;
                }
            }
            if (_cardBg != null)
            {
                _cardBg.color = new Color(0.118f, 0.161f, 0.224f, 0.96f);   // L3 面板色
            }
            foreach (TMP_Text text in GetComponentsInChildren<TMP_Text>(true)) LanguageManager.ApplyFont(text);
        }

        public void ShowComparison(bool show)
        {
            if (_config == null) return;
            _comparison=show;
            _icon.gameObject.SetActive(!show);
            _dpsRow.gameObject.SetActive(!show);
            _rangeRow.gameObject.SetActive(!show);
            _speedRow.gameObject.SetActive(!show);
            _priceRow.gameObject.SetActive(!show);
            transform.Find("Body/Divider").gameObject.SetActive(!show);
            Position(_typeName, show ? 24 : 275, 60);
            Position(_role, show ? 92 : 340, 56);
            Position(_desc, show ? 168 : 565, show ? 440 : 65);
            _desc.alignment = show ? TextAlignmentOptions.TopLeft : TextAlignmentOptions.Center;
            TacticalForgeLayout.ArrangeTowerCard(transform,show);
            if (!show) return;
            var levels = new System.Collections.Generic.List<TowerConfig>();
            if (Configs.TowerTable != null)
                foreach (var row in Configs.TowerTable.DataList)
                    // 塔表已按关卡拆分（2026-10-30）：图鉴只列当前关卡的那 9 行
                    if (row.Type == _config.Type && row.LevelId == Configs.ActiveLevelId) levels.Add(new TowerConfig(row));
            levels.Sort((a, b) => a.Level.CompareTo(b.Level));
            var text = new System.Text.StringBuilder();
            foreach (TowerConfig level in levels)
            {
                text.Append("<color=#35E0FF>Lv.").Append(level.Level).Append("</color>\n");
                text.AppendLine(level.IsSlowAura
                    ? (Localization.Get("Slow {0:P0} · DPS 0", level.EffectValue) ?? string.Format("Slow {0:P0} · DPS 0", level.EffectValue))
                    : (Localization.Get("Damage   {0}", level.Power) ?? string.Format("Damage {0}", level.Power)));
                text.Append(Localization.Get("Range    {0:F1}", level.RadiusGrid) ?? string.Format("Range {0:F1}", level.RadiusGrid));
                text.Append(" · ").Append(level.CooldownSec.ToString("0.00")).Append("s\n");
                text.AppendLine(Localization.Get("Cost     {0}", level.Prices) ?? string.Format("Cost {0}", level.Prices));
                text.AppendLine();
            }
            _desc.text = text.ToString();
            LanguageManager.ApplyFont(_desc);
        }

        private static void Position(TMP_Text text, float y, float height)
        {
            RectTransform rect = text.rectTransform;
            rect.anchorMin = new Vector2(0, 1); rect.anchorMax = new Vector2(1, 1); rect.pivot = new Vector2(.5f, 1);
            rect.anchoredPosition = new Vector2(0, -y); rect.sizeDelta = new Vector2(-48, height);
        }

        /// <summary>塔型主题色（2026-10-14 三塔型收敛后的三色映射）。</summary>
        public static Color ThemeColor(int type)
        {
            switch (type)
            {
                case 2: return new Color(1f, 0.478f, 0.161f, 1f);      // Power 火 #FF7A29
                case 3: return new Color(0.490f, 0.910f, 1f, 1f);      // Retard 冰 #7DE8FF
                default: return new Color(0.208f, 0.878f, 1f, 1f);     // Normal 青 #35E0FF
            }
        }

        /// <summary>塔型 → 图标名后缀（与 ResTable 登记的逻辑名一致）。</summary>
        public static string IconSuffix(int type)
        {
            switch (type)
            {
                case 2: return "Power";
                case 3: return "Retard";
                default: return "Normal";
            }
        }

        /// <summary>塔型 → 一句话定位（三塔型的定位文案）。</summary>
        public static string RoleText(int type)
        {
            switch (type)
            {
                case 2: return Localization.Get("Area blast · swarm clearer") ?? "范围爆炸 · 清群核心";
                case 3: return Localization.Get("Slows enemies · control") ?? "减速光环 · 增益全队";
                default: return Localization.Get("Single-target rapid fire") ?? "单体速射 · 性价比基准";
            }
        }

        private TMP_Text FindText(string path)
        {
            Transform tr = transform.Find(path);
            if (tr == null)
            {
                Debug.LogWarning("[TowerCodexItem] 缺少文本节点「" + path + "」");
                return null;
            }
            return tr.GetComponent<TMP_Text>();
        }

        private Image FindImage(string path)
        {
            Transform tr = transform.Find(path);
            if (tr == null)
            {
                Debug.LogWarning("[TowerCodexItem] 缺少图片节点「" + path + "」");
                return null;
            }
            return tr.GetComponent<Image>();
        }
    }
}
