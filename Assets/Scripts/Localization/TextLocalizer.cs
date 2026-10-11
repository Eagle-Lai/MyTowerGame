using TMPro;
using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// TMP 文本本地化组件 —— 直接挂在带 `TMP_Text` 的节点上。
    ///
    /// 【用法 · 两种 key 来源】
    ///   ① 在 Inspector 的 `key` 字段填一个 key；
    ///   ② **留空** —— 此时组件自动拿**本节点上 TMP 已序列化的文本内容当 key**
    ///      （prefab 里的静态英文原文即 key，见下）。
    ///
    /// 【为什么支持"文本内容即 key"】
    ///   多语言表（`Localization.xlsx`）的主键就是**英文原文本身**（id == en）。
    ///   于是"给 TMP 填英文原文"和"给它一个 key"是同一件事 ——
    ///   prefab 里天然写的就是英文原文，组件只要把它当 key 查一下表即可，
    ///   Inspector 里不必再手工抄一遍 key（少一处会写岔的地方）。
    ///
    /// 【回退链】显式 key（若填了）→ 节点文本内容 → 都查不到时保留原文/打警告。
    ///
    /// 【字体】刷新文本的同时，按当前语言设 `TMP_Text.font`（这是"根据语言切字体"的落点）。
    ///
    /// 【什么时候不该用它】运行时才知道参数的动态文本（如"回合 {0}"）——
    ///   这类文本由 View 代码用 `Localization.Get(key, args)` 主动赋值，不要挂本组件。
    /// </summary>
    [RequireComponent(typeof(TMP_Text))]
    [DisallowMultipleComponent]
    public class TextLocalizer : MonoBehaviour
    {
        [Tooltip("多语言表的 key（英文原文，如 Start）。留空则自动用本节点 TMP 的文本内容当 key。")]
        public string key;

        [Tooltip("查不到 key 时，是否保留 prefab 里序列化的原文。")]
        [SerializeField] private bool fallbackToOriginalText = true;

        private TMP_Text _text;
        private string _originalText;
        private bool _subscribed;

        /// <summary>运行时读写 key（改了会立即刷新）。留空即走"文本内容当 key"。</summary>
        public string Key
        {
            get { return key; }
            set
            {
                if (key == value)
                {
                    return;
                }
                key = value;
                Refresh();
            }
        }

        private void Awake()
        {
            _text = GetComponent<TMP_Text>();
            // 缓存 prefab 原文作为回退基线（只记一次；刷新后 text 会被改写，不能靠它再取）
            if (_text != null && _originalText == null)
            {
                _originalText = _text.text;
            }
        }

        private void OnEnable()
        {
            Refresh();
            Subscribe();
        }

        private void OnDisable()
        {
            Unsubscribe();
        }

        private void Subscribe()
        {
            if (_subscribed)
            {
                return;
            }
            EventDispatcher.AddEventListener<int>(EventName.LanguageChangedEvent, OnLanguageChanged);
            _subscribed = true;
        }

        private void Unsubscribe()
        {
            if (!_subscribed)
            {
                return;
            }
            EventDispatcher.RemoveEventListener<int>(EventName.LanguageChangedEvent, OnLanguageChanged);
            _subscribed = false;
        }

        private void OnLanguageChanged(int lang)
        {
            Refresh();
        }

        /// <summary>
        /// 解析本组件该用的 key：
        ///   ① 显式 key 非空 → 用它；
        ///   ② 否则用本节点 TMP 的**序列化原文**（_originalText，即 prefab 里的英文）；
        ///   ③ 都拿不到 → null（调用方走回退）。
        /// ⚠️ 必须用 _originalText 而不是 _text.text：刷新过一次之后
        ///   _text.text 已是译文，再拿它当 key 会"查一次译文再查表"层层套娃。
        /// </summary>
        public string ResolveKey()
        {
            if (!string.IsNullOrEmpty(key))
            {
                return key;
            }
            return string.IsNullOrEmpty(_originalText) ? null : _originalText;
        }

        /// <summary>按当前语言刷新文本与字体（幂等，可外部调用）。</summary>
        public void Refresh()
        {
            if (_text == null)
            {
                return;
            }

            // ① 字体先跟随语言（即使本文本未命中 key，字体也要对）
            TMP_FontAsset font = LanguageManager.GetFont(LanguageManager.Current);
            if (font != null && _text.font != font)
            {
                _text.font = font;
            }

            // ② 文本
            string resolved = ResolveKey();
            if (string.IsNullOrEmpty(resolved))
            {
                return;
            }

            string value = LanguageManager.GetText(resolved);
            if (value != null)
            {
                _text.text = value;
            }
            else if (fallbackToOriginalText && _originalText != null)
            {
                _text.text = _originalText;
            }
            else
            {
                LanguageManager.WarnMissingKeyOnce(resolved);
            }
        }
    }
}
