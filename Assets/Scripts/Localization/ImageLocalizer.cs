using UnityEngine;
using UnityEngine.UI;

namespace FTProject
{
    /// <summary>
    /// Image 多语言组件 —— 挂在带 `Image` 的节点上，按当前语言切换 Sprite。
    ///
    /// 【用法 · 两套并行机制（显式引用优先）】
    ///   ① **每语言直填引用**（enSprite / zhHansSprite / zhHantSprite）—— 传统用法，
    ///      填了就走它，与旧行为完全一致；
    ///   ② **key 驱动**（`key` 字段）—— 填了 key（或留空走"原值当 key"，见下）后，
    ///      用 key 去多语言表查**图片资源名**，再按资源名加载 Sprite。
    ///
    /// 【key 为空时"原值当 key"指什么】
    ///   Image 没有文本，所以"原值"取 **Image.sprite 的资源名**（如 `UI_Btn_Primary`）；
    ///   若 sprite 也为空，再退到**节点名**（`gameObject.name`）。
    ///   这和多语言表"英文原文即 key"的约定同构：资源名即 key。
    ///
    /// 【回退】key 查不到 / 该语言留空 → 回退英文 → 再回退 prefab 原 Sprite。
    ///
    /// 【为什么保留"每语言直填引用"】工程里 Sprite 是 prefab 的直接依赖
    ///   （UIPrefabBuilder 生成时烘 sprite 的写法），直填引用符合现有惯例，
    ///   且免去再维护一张图片映射表的成本。key 驱动是给"想统一走表"的场景用的补充。
    /// </summary>
    [RequireComponent(typeof(Image))]
    [DisallowMultipleComponent]
    public class ImageLocalizer : MonoBehaviour
    {
        [Tooltip("多语言表的 key（英文原文）。留空则自动用 Image.sprite 资源名，再回退节点名。")]
        public string key;

        [Tooltip("英文（默认语言）用图。也作为其它语言的回退图。")]
        [SerializeField] private Sprite enSprite;

        [Tooltip("简体中文用图。留空则回退英文。")]
        [SerializeField] private Sprite zhHansSprite;

        [Tooltip("繁体中文用图。留空则回退英文。")]
        [SerializeField] private Sprite zhHantSprite;

        private Image _image;
        private Sprite _originalSprite;
        private bool _subscribed;

        private void Awake()
        {
            _image = GetComponent<Image>();
            if (_image != null)
            {
                _originalSprite = _image.sprite;
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
        ///   ② 否则用 Image.sprite 的资源名（`UI_Btn_Primary`）；
        ///   ③ sprite 也为空 → 用节点名（`gameObject.name`）。
        /// ⚠️ 取 sprite 名用 **_originalSprite**（Awake 缓存的原图），
        ///   不用 `_image.sprite`：刷新过之后它已是本语言的图，
        ///   再拿它当 key 会"查一次译文再查表"层层套娃。
        /// </summary>
        public string ResolveKey()
        {
            if (!string.IsNullOrEmpty(key))
            {
                return key;
            }
            if (_originalSprite != null && !string.IsNullOrEmpty(_originalSprite.name))
            {
                return _originalSprite.name;
            }
            return gameObject.name;
        }

        /// <summary>按当前语言刷新 Sprite（幂等，可外部调用）。</summary>
        public void Refresh()
        {
            if (_image == null)
            {
                return;
            }

            Sprite s = Pick(LanguageManager.Current);
            if (s == null)
            {
                s = enSprite;   // 回退英文
            }
            if (s == null)
            {
                // 显式引用全空 → 走 key 驱动：key → 资源名 → ResLoader 加载
                s = LoadByKey(ResolveKey(), LanguageManager.Current);
            }
            if (s != null)
            {
                _image.sprite = s;
            }
            else if (_originalSprite != null)
            {
                _image.sprite = _originalSprite;
            }
        }

        private Sprite Pick(Language lang)
        {
            switch (lang)
            {
                case Language.ChineseSimplified:  return zhHansSprite;
                case Language.ChineseTraditional: return zhHantSprite;
                default:                          return enSprite;
            }
        }

        /// <summary>
        /// key → 资源名 → Sprite。
        ///
        /// 【查表口径】与文本同构：key 先去多语言表取"该语言下的资源名"；
        ///   取不到就用 key 本身当资源名（因为表的 id 就是英文资源名/原文）。
        /// 【资源名 → Sprite】走 ResTable 的逻辑名（唯一寻址源），例如
        ///   `UI_TowerIcon_Normal` → Assets/_UIAssets/UI/UI_TowerIcon_Normal.png。
        ///   取不到就返回 null，由调用方回退到 prefab 原图（"零破坏"）。
        /// </summary>
        private Sprite LoadByKey(string k, Language lang)
        {
            if (string.IsNullOrEmpty(k))
            {
                return null;
            }
            if (!ResLoader.Instance.IsReady)
            {
                return null;    // 引导期资源系统未就绪 → 回退原图
            }

            string resName = LanguageManager.GetText(k);
            if (string.IsNullOrEmpty(resName))
            {
                resName = k;    // 表里没有这条 → key 本身即资源名
            }

            return ResLoader.Instance.Load<Sprite>(resName);
        }
    }
}
