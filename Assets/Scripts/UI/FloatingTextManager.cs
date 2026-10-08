using TMPro;
using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 伤害飘字（M2-W5）。世界空间 Canvas + 对象池 TMP 文本。
    ///
    /// 【为什么是"管理器 + 懒创建"，而不是挂在场景里的 prefab】
    ///   挂 prefab 就多一个必须在 Unity 里生成的资产；而飘字属于纯表现，
    ///   用代码创建可以零资产交付，也少一处"忘了往场景里拖引用"的失败模式。
    ///
    /// 【为什么需要一个专门的 MonoBehaviour 来 Update】
    ///   工程约定 CombatSystem 是 UpdateEvent 的**唯一**订阅者（性能与顺序都可控）。
    ///   为了不破坏这条不变量，飘字自带一个轻量 Update，
    ///   而不是把自己塞进全局事件总线。
    ///
    /// 【节流】同一只怪在 DamageTextThrottleMs 内只弹一次。
    ///   高频塔（穿透塔 CD=200ms、激光塔更密）每跳都弹的话，屏幕会被数字糊满，
    ///   反而看不出伤害高低 —— 这是"表现"与"信息量"的取舍。
    ///
    /// 【字体从哪来】全工程统一 TMP。TMP 的 SDF 字体资产自带中文字形，
    ///   这里取 TMP Settings 配置的默认字体（工程已指向 SiYuanSongTi SDF），
    ///   不依赖 UGUI 的 Font / Resources.GetBuiltinResource（那套已弃用）。
    /// </summary>
    public class FloatingTextManager : MonoBehaviour
    {
        private const int PoolSize = 24;
        private const float LifeSec = 0.7f;
        private const float RiseSpeed = 1.4f;
        private const int FontSize = 34;

        private static readonly Color NormalColor = new Color(1f, 0.95f, 0.6f, 1f);
        private static readonly Color KillColor = new Color(1f, 0.42f, 0.32f, 1f);

        private static FloatingTextManager _instance;

        private TextMeshProUGUI[] _texts;
        private RectTransform[] _rects;
        private float[] _life;
        private int _next;
        private bool _ready;

        /// <summary>
        /// 弹一个伤害数字。
        /// </summary>
        /// <param name="owner">伤害归属的怪，用于节流（可为 null，则不节流）</param>
        /// <param name="killing">是否是致命一击 —— 用颜色区分，玩家一眼能看出"这只死了"</param>
        public static void Show(BaseEnemy owner, Vector3 worldPos, int amount, bool killing)
        {
            // 关掉时整条链路短路：压测与低端机降级都靠这一个开关
            if (Configs.Global == null || !Configs.Global.ShowDamageText)
            {
                return;
            }
            if (amount <= 0)
            {
                return;
            }

            // 节流：写在怪身上，避免用"怪 → 时间"的字典（对象池复用时字典键会失效并泄漏）
            if (owner != null)
            {
                float now = Time.unscaledTime;
                if (now < owner.NextDamageTextTime)
                {
                    return;
                }
                owner.NextDamageTextTime = now + Configs.Global.DamageTextThrottleSec;
            }

            if (_instance == null)
            {
                _instance = Create();
                if (_instance == null)
                {
                    return;
                }
            }
            _instance.ShowInternal(worldPos, amount, killing);
        }

        /// <summary>
        /// 立刻收起所有正在飘的伤害数字（切关 / 重开用）。
        ///
        /// 【为什么要它】飘字有 0.7 秒寿命，而切关是同一帧完成的 ——
        /// 不清的话，上一关的伤害数字会继续飘进新关卡，看起来像"新关卡凭空掉血"。
        /// 实例还没被创建过时是空操作（那就本来没有东西可清）。
        /// </summary>
        public static void ClearAll()
        {
            if (_instance != null)
            {
                _instance.ClearInternal();
            }
        }

        private void ClearInternal()
        {
            if (!_ready)
            {
                return;
            }
            for (int i = 0; i < _texts.Length; i++)
            {
                _life[i] = 0f;
                TextMeshProUGUI t = _texts[i];
                if (t != null && t.gameObject.activeSelf)
                {
                    t.gameObject.SetActive(false);
                }
            }
        }

        private static FloatingTextManager Create()
        {
            TMP_FontAsset font = ResolveFont();
            if (font == null)
            {
                Debug.LogWarning("[FloatText] 找不到可用 TMP 字体资产，伤害飘字已跳过（不影响战斗）");
                return null;
            }

            GameObject root = new GameObject("FloatingTextRoot");
            Canvas canvas = root.AddComponent<Canvas>();
            canvas.renderMode = RenderMode.WorldSpace;
            canvas.sortingOrder = BoardSorting.Overlay;   // 已预留 500：血条 / 伤害数字

            // 世界空间 Canvas 的常规做法：整体缩小，让 1 canvas 单位 = 0.01 世界单位。
            // 于是 fontSize=34 的字约 0.34 世界单位高，与"1 格 = 1 世界单位"相称。
            root.transform.localScale = Vector3.one * 0.01f;
            RectTransform crt = root.GetComponent<RectTransform>();
            crt.sizeDelta = new Vector2(200f, 200f);

            FloatingTextManager m = root.AddComponent<FloatingTextManager>();
            m.Init(font);
            return m;
        }

        /// <summary>
        /// 取 TMP 字体资产。
        /// 【为什么不再借场景 UI 文本的 Font】那套是 UGUI 的；TMP 用的是**字体资产**。
        ///   直接取 TMP Settings 的默认字体（工程已配置为 SiYuanSongTi SDF，含中文字形），
        ///   该资产已随 TMP 资源配置进包，不需要再从场景里"借"一个引用。
        /// </summary>
        private static TMP_FontAsset ResolveFont()
        {
            TMP_FontAsset font = TMP_Settings.defaultFontAsset;
            if (font == null && TMP_Settings.fallbackFontAssets != null && TMP_Settings.fallbackFontAssets.Count > 0)
            {
                font = TMP_Settings.fallbackFontAssets[0];
            }
            return font;
        }

        private void Init(TMP_FontAsset font)
        {
            _texts = new TextMeshProUGUI[PoolSize];
            _rects = new RectTransform[PoolSize];
            _life = new float[PoolSize];

            for (int i = 0; i < PoolSize; i++)
            {
                GameObject go = new GameObject("Dmg" + i, typeof(RectTransform));
                go.transform.SetParent(transform, false);

                RectTransform rt = (RectTransform)go.transform;
                rt.anchorMin = new Vector2(0.5f, 0.5f);
                rt.anchorMax = new Vector2(0.5f, 0.5f);
                rt.pivot = new Vector2(0.5f, 0.5f);
                rt.sizeDelta = new Vector2(200f, 60f);

                TextMeshProUGUI t = go.AddComponent<TextMeshProUGUI>();
                if (font != null)
                {
                    t.font = font;
                }
                t.fontSize = FontSize;
                t.alignment = TextAlignmentOptions.Center;
                t.raycastTarget = false;      // 飘字绝不能吃掉点击
                t.enableWordWrapping = false;
                t.overflowMode = TextOverflowModes.Overflow;
                t.color = NormalColor;

                _texts[i] = t;
                _rects[i] = rt;
                go.SetActive(false);
            }
            _ready = true;
        }

        private void OnDestroy()
        {
            if (_instance == this)
            {
                _instance = null;
            }
        }

        private void ShowInternal(Vector3 worldPos, int amount, bool killing)
        {
            if (!_ready)
            {
                return;
            }
            int i = _next;
            _next = (_next + 1) % PoolSize;

            // 【为什么要缓存数字字符串】每跳 ToString 都会产生托管分配，
            // 在 200 怪 + 高频塔的场景下足以在 Profiler 里看出来。
            // 伤害值种类有限，用一个小缓存把它变成零分配。
            TextMeshProUGUI t = _texts[i];
            t.text = NumberCache.Get(amount);
            t.color = killing ? KillColor : NormalColor;

            _rects[i].position = worldPos;
            _texts[i].gameObject.SetActive(true);
            _life[i] = LifeSec;
        }

        private void Update()
        {
            if (!_ready)
            {
                return;
            }
            float dt = GameClock.DeltaTime;
            for (int i = 0; i < _texts.Length; i++)
            {
                if (_life[i] <= 0f)
                {
                    continue;
                }
                _life[i] -= dt;
                if (_life[i] <= 0f)
                {
                    _life[i] = 0f;
                    _texts[i].gameObject.SetActive(false);
                    continue;
                }
                // 上浮 + 淡出
                _rects[i].position += Vector3.up * (RiseSpeed * dt);
                Color c = _texts[i].color;
                c.a = Mathf.Clamp01(_life[i] / LifeSec) * (c.r > 0.9f && c.g < 0.5f ? 1f : 0.95f);
                _texts[i].color = c;
            }
        }
    }

    /// <summary>
    /// 伤害数字的字符串缓存。
    /// 整数伤害的取值范围有限（几百以内），缓存后 Show 就完全不产生垃圾。
    /// </summary>
    internal static class NumberCache
    {
        private const int MaxCached = 512;
        private static readonly string[] _cache = new string[MaxCached];

        public static string Get(int value)
        {
            if (value >= 0 && value < MaxCached)
            {
                string s = _cache[value];
                if (s == null)
                {
                    s = value.ToString();
                    _cache[value] = s;
                }
                return s;
            }
            return value.ToString();
        }
    }
}
