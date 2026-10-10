using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace FTProject
{
    /// <summary>
    /// 塔图鉴的一张卡片（UI 补全 B2）。
    ///
    /// 【为什么卡片必须有脚本】图鉴是**同一个 prefab 被池化复用 5 次**（LoopListView2 的机制），
    /// 一次显示、一次回收再填别的塔 —— 所以内容只能在运行时灌进去，不能烘死在 prefab 里。
    ///
    /// 【缩放/淡化挂在 Body 而不是根节点】LoopListView2 的条目根节点 pivot 固定 (0,0.5)，
    /// 缩放根节点会让卡片围绕左缘缩放 → 视觉上"居中卡左右空隙一宽一窄"。
    /// </summary>
    public class TowerCodexItem : MonoBehaviour
    {
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

            Color theme = ThemeColor(cfg.Type);
            if (_topBar != null) _topBar.color = theme;
            if (_typeName != null)
            {
                _typeName.text = string.IsNullOrEmpty(cfg.Name) ? ("塔 " + cfg.Type) : cfg.Name;
                _typeName.color = theme;
            }
            if (_role != null) _role.text = roleText;
            if (_dpsRow != null) _dpsRow.text = string.Format("伤害　{0}", cfg.Power);
            if (_rangeRow != null) _rangeRow.text = string.Format("射程　{0:F1} 格", cfg.RadiusGrid);
            if (_speedRow != null) _speedRow.text = string.Format("攻速　{0:F2} 秒", cfg.CooldownSec);
            if (_priceRow != null) _priceRow.text = string.Format("造价　{0} 金币", cfg.Prices);
            if (_desc != null)
            {
                _desc.text = string.IsNullOrEmpty(cfg.Desc) ? roleText : cfg.Desc;
            }

            if (_icon != null)
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
        }

        /// <summary>塔型主题色（策划案 §B2 的五色映射）。</summary>
        public static Color ThemeColor(int type)
        {
            switch (type)
            {
                case 2: return new Color(1f, 0.478f, 0.161f, 1f);      // Power 火 #FF7A29
                case 3: return new Color(0.490f, 0.910f, 1f, 1f);      // Retard 冰 #7DE8FF
                case 4: return new Color(0.486f, 0.361f, 1f, 1f);      // Pierce 紫 #7C5CFF
                case 5: return new Color(0.486f, 0.361f, 1f, 1f);      // Laser 紫 #7C5CFF
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
                case 4: return "Pierce";
                case 5: return "Laser";
                default: return "Normal";
            }
        }

        /// <summary>塔型 → 一句话定位（策划案 §B2 的定位文案）。</summary>
        public static string RoleText(int type)
        {
            switch (type)
            {
                case 2: return "范围爆炸 · 清群核心";
                case 3: return "减速光环 · 增益全队";
                case 4: return "直线穿透 · 一列贯穿";
                case 5: return "高单伤 · 专克重甲";
                default: return "单体速射 · 性价比基准";
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
