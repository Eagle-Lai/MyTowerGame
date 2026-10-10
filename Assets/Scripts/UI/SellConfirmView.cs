using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace FTProject
{
    /// <summary>
    /// 出售塔二次确认（UI 补全 C1 / 效果图 22_ConfirmView.svg 左）。
    ///
    /// 【为什么从"原地两段式"升级成独立弹窗】
    ///   原实现（`TowerInfoView.OnClickSell` 的原地改文案）确实能拦误触，但有三个问题：
    ///     ① 玩家看不到"这一卖要亏多少"——退回金额只在按钮文案里一闪而过；
    ///     ② 因为要"记住上次点的是哪个按钮"，面板一刷新就得小心别把确认态刷掉；
    ///     ③ 文案"确认出售？"顶掉"出售 (+46)"之后，玩家不知道自己点的是哪座塔。
    ///   独立弹窗能一次讲清：塔名 + 退回多少 + 不可撤销。
    ///
    /// 【退回额怎么算】与 `TowerInfoView` 用同一口径（`Configs.Global.SellRefundRate × cfg.SellPrice`），
    ///   不在这里另算一套 —— 两处算法分叉是"按钮写退 46、实际退 30"这类 bug 的根源。
    /// </summary>
    public class SellConfirmView : MonoBehaviour
    {
        public const string LogicalName = "SellConfirmView";

        private static readonly Color TextPrimary = new Color(0.910f, 0.941f, 0.980f, 1f);
        private static readonly Color TextSecondary = new Color(0.624f, 0.702f, 0.784f, 1f);
        private static readonly Color Fire = new Color(1f, 0.478f, 0.161f, 1f);      // #FF7A29
        private static readonly Color Gold = new Color(1f, 0.788f, 0.302f, 1f);      // #FFC94D

        private TMP_Text _title;
        private TMP_Text _towerName;
        private TMP_Text _warnText;
        private TMP_Text _refundValue;
        private TMP_Text _refundLabel;
        private Image _topBar;
        private Image _towerIcon;
        private Button _confirmBtn;
        private Button _cancelBtn;

        private BaseTower _tower;

        /// <summary>弹出出售确认。<paramref name="tower"/> 为 null 时不弹（避免出现"确认卖掉空气"）。</summary>
        public static void Show(BaseTower tower)
        {
            if (tower == null)
            {
                return;
            }
            SellConfirmView view = UIManager.Instance.Open<SellConfirmView>(LogicalName, UILayout.NormalPanel);
            if (view == null)
            {
                // 【降级】弹窗缺失时不静默卖掉，而是提示"暂不可用"——
                // 不可撤销的操作绝不能因为 UI 缺失就自动执行。
                Debug.LogError("[Sell] SellConfirmView 打开失败（prefab 可能还没生成），已取消本次出售");
                EventDispatcher.TriggerEvent<string>(EventName.ShowTipEvent, "出售确认界面不可用");
                return;
            }
            view.Setup(tower);
        }

        private void Awake()
        {
            _title = FindText("Panel/SellTitle");
            _towerName = FindText("Panel/TowerName");
            _warnText = FindText("Panel/WarnText");
            _refundValue = FindText("Panel/RefundValue");
            _refundLabel = FindText("Panel/RefundLabel");
            _confirmBtn = FindButton("Panel/ConfirmBtn");
            _cancelBtn = FindButton("Panel/CancelBtn");
            Transform bar = transform.Find("Panel/TopBar");
            _topBar = bar != null ? bar.GetComponent<Image>() : null;
            Transform icon = transform.Find("Panel/TowerIcon");
            _towerIcon = icon != null ? icon.GetComponent<Image>() : null;

            if (_confirmBtn != null) _confirmBtn.onClick.AddListener(OnClickConfirm);
            if (_cancelBtn != null) _cancelBtn.onClick.AddListener(OnClickCancel);
            Button bg = FindButton("Bg");
            if (bg != null) bg.onClick.AddListener(OnClickCancel);

            if (_title != null) _title.color = TextPrimary;
            if (_towerName != null) _towerName.color = TextPrimary;
            if (_warnText != null) _warnText.color = Fire;
            if (_refundLabel != null) _refundLabel.color = TextSecondary;
            if (_refundValue != null) _refundValue.color = Gold;
            if (_topBar != null) _topBar.color = Fire;

            // 警告文案里的比例**跟随配置**，不写死 70%：数值一改文案就跟着对
            float rate = Configs.Global != null ? Configs.Global.SellRefundRate : 1f;
            if (_warnText != null)
            {
                _warnText.text = string.Format(
                    "出售后将退回 {0}% 的累计投入\n且无法撤销", Mathf.RoundToInt(rate * 100f));
            }
        }

        private void Setup(BaseTower tower)
        {
            _tower = tower;
            TowerConfig cfg = tower.Config;
            if (cfg == null)
            {
                return;
            }

            if (_towerName != null)
            {
                _towerName.text = string.IsNullOrEmpty(cfg.Name) ? "塔" : cfg.Name;
            }

            float rate = Configs.Global != null ? Configs.Global.SellRefundRate : 1f;
            int refund = Mathf.Max(0, Mathf.RoundToInt(cfg.SellPrice * rate));
            if (_refundValue != null)
            {
                _refundValue.text = refund.ToString();
            }
            if (_towerIcon != null)
            {
                // 图标缺失只是不好看，不影响功能：取不到就留一个暗色块
                Sprite icon = ResLoader.Instance.IsReady
                    ? ResLoader.Instance.Load<Sprite>("UI_TowerIcon_" + TypeSuffix(cfg.Type))
                    : null;
                if (icon != null)
                {
                    _towerIcon.sprite = icon;
                    _towerIcon.color = Color.white;
                }
            }
        }

        /// <summary>TowerType → 图标名后缀（与 UIPrefabBuilder.TowerIconSpriteName 同一口径）。</summary>
        private static string TypeSuffix(int type)
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

        private void OnClickConfirm()
        {
            BaseTower t = _tower;
            _tower = null;
            UIManager.Instance.Close(LogicalName);
            if (t != null)
            {
                // 只有这里才真正出售：TowerSellRequestEvent 是"玩家想卖"（意图），
                // 本事件是"玩家确认了"（决定）。GameFlowManager 只监听本事件。
                EventDispatcher.TriggerEvent<BaseTower>(EventName.TowerSellConfirmEvent, t);
            }
        }

        private void OnClickCancel()
        {
            _tower = null;
            UIManager.Instance.Close(LogicalName);
        }

        private TMP_Text FindText(string path)
        {
            Transform tr = transform.Find(path);
            if (tr == null)
            {
                Debug.LogWarning("[Sell] 缺少文本节点「" + path + "」");
                return null;
            }
            return tr.GetComponent<TMP_Text>();
        }

        private Button FindButton(string path)
        {
            Transform tr = transform.Find(path);
            if (tr == null)
            {
                Debug.LogWarning("[Sell] 缺少按钮节点「" + path + "」");
                return null;
            }
            return tr.GetComponent<Button>();
        }
    }
}
