using System;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace FTProject
{
    /// <summary>确认弹窗的性质（决定顶部色条与确定按钮的颜色）。</summary>
    public enum ConfirmType
    {
        Info,
        Success,
        Danger,
        Warning
    }

    /// <summary>
    /// 通用二次确认弹窗（UI 补全 C2 / 效果图 22_ConfirmView.svg 右）。
    ///
    /// 【它解决什么问题】改造前"重置存档"是**点一下就真的清了**（`SettingView.OnClickReset` 直接
    /// `ResetAll()`），退出游戏也没有确认。这类不可撤销的操作必须拦一道。
    ///
    /// 【为什么做成静态 Show 而不是让调用方自己 Open + Show】
    ///   调用点关心的是"我要确认一件事"，不是"我要打开某个界面"。
    ///   静态入口把 Open→Show 的样板收在一处，接新调用点只要一行。
    ///
    /// 【高度为什么不做自适应】策划案 §3 C2 写了"高随正文行数自适应（480~700）"，
    ///   但**固定 760×560** 才是效果图 22 的实测几何，而且自适应高度会破坏
    ///   UIPrefabBuilder 的静态布局（生成器产出的节点坐标是写死的，运行期改面板高
    ///   就得同时重排 6 个子节点，很容易出错）。
    ///   按"以 SVG 为准"的裁定：**固定 760×560**，正文限 3 行内，超出自动缩字号。
    /// </summary>
    public class ConfirmView : MonoBehaviour
    {
        public const string LogicalName = "ConfirmView";

        /// <summary>正文最长行数（超过就缩字号，而不是撑破面板）。</summary>
        private const int MaxBodyLines = 3;

        private static readonly Color Cyan = new Color(0.208f, 0.878f, 1f, 1f);          // #35E0FF
        private static readonly Color Gold = new Color(1f, 0.788f, 0.302f, 1f);          // #FFC94D
        private static readonly Color DangerRed = new Color(1f, 0.302f, 0.369f, 1f);     // #FF4D5E
        private static readonly Color Fire = new Color(1f, 0.478f, 0.161f, 1f);          // #FF7A29
        private static readonly Color TextPrimary = new Color(0.910f, 0.941f, 0.980f, 1f);
        private static readonly Color TextSecondary = new Color(0.624f, 0.702f, 0.784f, 1f);

        private TMP_Text _title;
        private TMP_Text _body;
        private Image _topBar;
        private Image _dangerIcon;
        private Button _confirmBtn;
        private Button _cancelBtn;
        private TMP_Text _confirmLabel;
        private TMP_Text _cancelLabel;

        private Action _onConfirm;

        /// <summary>
        /// 弹一个确认框。<paramref name="onConfirm"/> 在点"确定"后**只执行一次**。
        /// 【prefab 缺失时的行为】记一条明确错误并**不执行** onConfirm ——
        /// 不可撤销的操作宁可"什么都没发生"，也不能在玩家没确认的情况下执行。
        /// </summary>
        public static void Show(string title, string body, ConfirmType type, Action onConfirm,
            string confirmLabel = "确定", string cancelLabel = "取消")
        {
            ConfirmView view = UIManager.Instance.Open<ConfirmView>(LogicalName, UILayout.NormalPanel);
            if (view == null)
            {
                Debug.LogError("[Confirm] ConfirmView 打开失败（prefab 可能还没生成），已取消本次操作：" + title);
                return;
            }
            view.Setup(title, body, type, onConfirm, confirmLabel, cancelLabel);
        }

        private void Awake()
        {
            _title = FindText("Panel/BodyTitle");
            _body = FindText("Panel/BodyText");
            _confirmBtn = FindButton("Panel/ConfirmBtn");
            _cancelBtn = FindButton("Panel/CancelBtn");
            _confirmLabel = FindText("Panel/ConfirmBtn/Label");
            _cancelLabel = FindText("Panel/CancelBtn/Label");
            Transform bar = transform.Find("Panel/TopBar");
            _topBar = bar != null ? bar.GetComponent<Image>() : null;
            Transform icon = transform.Find("Panel/DangerIcon");
            _dangerIcon = icon != null ? icon.GetComponent<Image>() : null;

            if (_confirmBtn != null) _confirmBtn.onClick.AddListener(OnClickConfirm);
            if (_cancelBtn != null) _cancelBtn.onClick.AddListener(OnClickCancel);
            // 点背景 = 取消（与"点右上角关闭"同义；不做成"确定"，避免误触致不可撤销）
            Button bg = FindButton("Bg");
            if (bg != null) bg.onClick.AddListener(OnClickCancel);
        }

        private void Setup(string title, string body, ConfirmType type, Action onConfirm,
            string confirmLabel, string cancelLabel)
        {
            _onConfirm = onConfirm;

            SetText(_title, title);
            SetText(_body, body);
            SetText(_confirmLabel, string.IsNullOrEmpty(confirmLabel) ? "确定" : confirmLabel);
            SetText(_cancelLabel, string.IsNullOrEmpty(cancelLabel) ? "取消" : cancelLabel);

            if (_title != null) _title.color = TextPrimary;
            if (_body != null) _body.color = TextSecondary;

            Color accent = ColorFor(type);
            if (_topBar != null) _topBar.color = accent;
            if (_dangerIcon != null) _dangerIcon.color = accent;

            // 正文超长就缩字号（固定高度面板下的兜底，总比文字溢出到面板外好）
            if (_body != null)
            {
                int lines = 1 + Mathf.Max(0, body != null ? body.Length / 22 : 0);
                int size = lines <= MaxBodyLines ? 28 : Mathf.Max(20, 28 - (lines - MaxBodyLines) * 2);
                _body.fontSize = size;
            }
        }

        private static Color ColorFor(ConfirmType type)
        {
            switch (type)
            {
                case ConfirmType.Success: return Gold;
                case ConfirmType.Danger: return DangerRed;
                case ConfirmType.Warning: return Fire;
                default: return Cyan;
            }
        }

        private void OnClickConfirm()
        {
            // 【为什么要先取出再清空】onConfirm 里可能又打开别的界面/再次弹确认，
            // 不清空的话"连点两次确定"会把回调执行两遍（不可撤销操作执行两次是灾难）。
            Action cb = _onConfirm;
            _onConfirm = null;
            UIManager.Instance.Close(LogicalName);
            if (cb != null)
            {
                cb();
            }
        }

        private void OnClickCancel()
        {
            _onConfirm = null;
            UIManager.Instance.Close(LogicalName);
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
                Debug.LogWarning("[Confirm] 缺少文本节点「" + path + "」");
                return null;
            }
            return tr.GetComponent<TMP_Text>();
        }

        private Button FindButton(string path)
        {
            Transform tr = transform.Find(path);
            if (tr == null)
            {
                Debug.LogWarning("[Confirm] 缺少按钮节点「" + path + "」");
                return null;
            }
            return tr.GetComponent<Button>();
        }
    }
}
