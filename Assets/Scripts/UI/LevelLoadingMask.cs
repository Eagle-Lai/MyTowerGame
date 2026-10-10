using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace FTProject
{
    /// <summary>
    /// 切关加载遮罩（UI 补全 C4）。
    ///
    /// 【它解决什么问题】`StartLevel` → `TeardownLevel` → `InitLevel` 是一条**同步**链路：
    ///   拆棋盘、清实体、按配置重建棋盘与路径全在同一帧里做完。关卡越大这一帧越长，
    ///   玩家看到的是"画面一黑/一闪，然后新关卡已经在了"——没有过渡，像卡了一下。
    ///
    /// 【为什么用代码建而不是走 UIPrefabBuilder】
    ///   ① 它必须在**任何时刻**都能显示，不能受"资源系统是否就绪""prefab 是否已生成"影响；
    ///   ② 它不属于任何 UILayout 层（要压在所有界面之上），硬塞进 NormalPanel 会跟 Tips 抢层级；
    ///   ③ 工程里已有同样的先例：`FloatingTextManager` 也是纯代码懒创建的 Canvas。
    ///   所以这里用独立 Canvas + 高 sortingOrder，不新增 UILayout 枚举。
    ///
    /// 【为什么必须是"延迟一帧"的用法】同步链路里 show 完立刻 hide，本帧根本不会渲染遮罩。
    ///   调用方必须先 `Show`，`yield return null` 一帧，再做重活，最后 `Hide`（见 GameFlowManager）。
    ///
    /// 【时间基准】一律 `unscaledDeltaTime`：切关时 `timeScale` 可能是 0（从暂停界面重开），
    ///   用缩放时间会让遮罩永远淡不出去。
    /// </summary>
    public class LevelLoadingMask : MonoBehaviour
    {
        /// <summary>遮罩最高不透明度（留一点底透出来，避免纯黑像崩溃）。</summary>
        private const float MaxAlpha = 0.9f;

        private const float FadeInSec = 0.12f;
        private const float FadeOutSec = 0.18f;

        /// <summary>sortingOrder 取 500：远高于 UICanvas（背景/常规/提示三层都在 0 附近）。</summary>
        private const int SortingOrder = 500;

        private static LevelLoadingMask _instance;

        private CanvasGroup _cg;
        private TMP_Text _text;
        private float _targetAlpha;
        private bool _visible;

        /// <summary>显示遮罩并设置文案（首次调用会懒创建整块遮罩）。</summary>
        public static void Show(string text)
        {
            Ensure();
            if (_instance == null)
            {
                return;
            }
            if (_instance._text != null)
            {
                _instance._text.text = text;
            }
            _instance.SetVisible(true);
        }

        /// <summary>开始淡出（淡完自动 SetActive(false)，不销毁 —— 下一关还要用）。</summary>
        public static void Hide()
        {
            if (_instance != null)
            {
                _instance.SetVisible(false);
            }
        }

        /// <summary>是否显示中（调试/自检用）。</summary>
        public static bool IsShowing
        {
            get { return _instance != null && _instance._visible; }
        }

        private static void Ensure()
        {
            if (_instance != null)
            {
                return;
            }

            GameObject root = new GameObject("LevelLoadingMask", typeof(RectTransform));
            Object.DontDestroyOnLoad(root);

            Canvas canvas = root.AddComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            canvas.sortingOrder = SortingOrder;

            CanvasScaler scaler = root.AddComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1920f, 1080f);
            scaler.screenMatchMode = CanvasScaler.ScreenMatchMode.MatchWidthOrHeight;
            scaler.matchWidthOrHeight = 0.5f;

            _instance = root.AddComponent<LevelLoadingMask>();

            GameObject bg = new GameObject("Bg", typeof(RectTransform));
            bg.transform.SetParent(root.transform, false);
            RectTransform brt = (RectTransform)bg.transform;
            brt.anchorMin = Vector2.zero;
            brt.anchorMax = Vector2.one;
            brt.offsetMin = Vector2.zero;
            brt.offsetMax = Vector2.zero;
            Image bgImg = bg.AddComponent<Image>();
            bgImg.color = new Color(0.031f, 0.043f, 0.071f, 1f);   // #080B12
            bgImg.raycastTarget = true;   // 挡住底下的误点（加载中不该能操作）

            GameObject textGo = new GameObject("Text", typeof(RectTransform));
            textGo.transform.SetParent(root.transform, false);
            RectTransform trt = (RectTransform)textGo.transform;
            trt.anchorMin = new Vector2(0.5f, 0.5f);
            trt.anchorMax = new Vector2(0.5f, 0.5f);
            trt.pivot = new Vector2(0.5f, 0.5f);
            trt.anchoredPosition = Vector2.zero;
            trt.sizeDelta = new Vector2(1200f, 60f);
            TextMeshProUGUI tmp = textGo.AddComponent<TextMeshProUGUI>();
            // 字体走 ResTable 已登记的逻辑名（与其它界面同一份资产）；取不到再退 TMP 默认。
            // 遮罩只在切关时使用，那时资源系统早已就绪。
            TMP_FontAsset font = null;
            if (ResLoader.Instance.IsReady)
            {
                font = ResLoader.Instance.Load<TMP_FontAsset>("Font_SiYuanSongTi_SDF");
            }
            if (font == null)
            {
                font = TMP_Settings.defaultFontAsset;
            }
            if (font != null)
            {
                tmp.font = font;
            }
            tmp.fontSize = 34f;
            tmp.alignment = TextAlignmentOptions.Center;
            tmp.color = new Color(0.910f, 0.941f, 0.980f, 1f);
            tmp.raycastTarget = false;
            tmp.text = string.Empty;

            _instance._cg = root.AddComponent<CanvasGroup>();
            _instance._cg.alpha = 0f;
            _instance._text = tmp;
            _instance._visible = false;
            root.SetActive(false);
        }

        private void SetVisible(bool visible)
        {
            _visible = visible;
            _targetAlpha = visible ? MaxAlpha : 0f;
            if (visible)
            {
                gameObject.SetActive(true);
            }
        }

        private void Update()
        {
            float dt = Time.unscaledDeltaTime;
            // 速度按"全程跨度 / 该方向的时长"算，淡入淡出各用各的时长
            bool fadingIn = _targetAlpha > _cg.alpha;
            float speed = MaxAlpha / (fadingIn ? FadeInSec : FadeOutSec);
            _cg.alpha = Mathf.MoveTowards(_cg.alpha, _targetAlpha, speed * dt);

            if (!_visible && _cg.alpha <= 0.001f && gameObject.activeSelf)
            {
                gameObject.SetActive(false);
            }
        }
    }
}
