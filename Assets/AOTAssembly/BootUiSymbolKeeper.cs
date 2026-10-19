using UnityEngine;
using UnityEngine.UI;

namespace FTProject.AOT
{
    /// <summary>
    /// 热更侧 Boot 更新界面（HotUpdateView / BootHotUpdateGate）的
    /// **AOT 符号保留清单**（2026-10-16）。
    ///
    /// ==================================================================
    /// 【为什么需要这个类】
    ///   HybridCLR 的核心约束：热更 dll 只能调用"AOT 链接后仍然存在"的方法 ——
    ///   未被任何 AOT 代码引用的方法会被 IL2CPP 链接器裁剪，热更侧一调用就
    ///   `MissingMethodException: MethodNotFind`（2026-10-16 实测：字体 API 被裁，
    ///   异常杀死闸门协程、应用停在黑屏）。
    ///
    ///   本类在 Boot 启动链里**真实执行一遍**（创建 → 配置 → 销毁探针对象），
    ///   以真实执行路径保证链接器 100% 保留清单里所有 API；探针全透明、同帧销毁，
    ///   无任何可见效果。
    ///
    ///   ⚠️ 维护约定：热更侧 HotUpdateView / BootHotUpdateGate 每新增一个
    ///   Unity/UGUI API 调用，**必须同步加进下面的 Keep 清单** —— 否则只会在真机
    ///   触发 MissingMethodException（编译期完全无感；这也是为什么探测必须"真实
    ///   执行而不能只写注释"）。
    ///
    ///   ⚠️ 血泪教训（2026-10-16 两次真机验证）：
    ///   ① 本方法自己也可能抛异常 —— 全函数 try-catch，**锚定失败绝不能弄死
    ///      Boot 启动链**（它只是辅助手段）；
    ///   ② UGUI 规则：**一个 GameObject 只能挂一个 Graphic**（Image/Text 互斥）——
    ///      探针里二者必须分对象（曾因塞同一个对象导致 AddComponent 返回 null
    ///      而空引用崩溃）。
    ///
    ///   【关于 AOT 引用 UGUI】工程约定"运行时 UI 统一 TMP"，但 UGUI 在这里只用于
    ///   "保符号"（真正的更新界面在热更侧，且因 TMP 字体在 AB 中而只能用小 UGUI）。
    ///   这是必要引用，不是运行界面。
    /// ==================================================================
    /// </summary>
    public static class BootUiSymbolKeeper
    {
        private static bool s_done;

        /// <summary>启动早期调用一次（幂等；内部全防护，绝不抛出）。</summary>
        public static void Ensure()
        {
            if (s_done)
            {
                return;
            }
            s_done = true;

            try
            {
                Keep();
                Debug.Log("[Boot] Boot 更新界面符号保留完成（热更侧 API 清单已锚定）。");
            }
            catch (System.Exception e)
            {
                // 锚定只是"防裁剪辅助"——失败绝不能弄死启动链（记录后放行）。
                Debug.LogError("[Boot] Boot 更新界面符号保留失败（忽略，不影响启动）：" + e);
            }
        }

        private static void Keep()
        {
            // —— 根（Canvas + CanvasScaler，二者都不是 Graphic，可共存）——
            GameObject root = new GameObject("~BootUiSymbolKeeper", typeof(Canvas), typeof(CanvasScaler));
            root.hideFlags = HideFlags.HideAndDontSave;

            Canvas canvas = root.GetComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            canvas.sortingOrder = -30000;

            CanvasScaler scaler = root.GetComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1920f, 1080f);
            scaler.matchWidthOrHeight = 0.5f;

            // —— Image 探针（独立对象：UGUI 每个 GameObject 只能挂一个 Graphic）——
            GameObject imgGo = new GameObject("~keep_img", typeof(RectTransform), typeof(Image));
            imgGo.transform.SetParent(root.transform, false);
            Image img = imgGo.GetComponent<Image>();
            img.color = new Color(1f, 1f, 1f, 0f);
            img.raycastTarget = false;
            RectTransform imgRt = img.rectTransform;
            imgRt.anchorMin = Vector2.zero;
            imgRt.anchorMax = Vector2.one;
            imgRt.pivot = new Vector2(0.5f, 0.5f);
            imgRt.anchoredPosition = Vector2.zero;
            imgRt.sizeDelta = Vector2.zero;

            // —— Text 探针（单独对象）——
            GameObject textGo = new GameObject("~keep_text", typeof(RectTransform), typeof(Text));
            textGo.transform.SetParent(root.transform, false);
            Text text = textGo.GetComponent<Text>();
            text.font = BootUiFontProvider.UiFont;
            text.text = string.Empty;
            text.fontSize = 12;
            text.fontStyle = FontStyle.Bold;
            text.color = new Color(1f, 1f, 1f, 0f);
            text.alignment = TextAnchor.MiddleCenter;
            text.horizontalOverflow = HorizontalWrapMode.Overflow;
            text.verticalOverflow = VerticalWrapMode.Overflow;
            text.raycastTarget = false;
            RectTransform textRt = text.rectTransform;
            textRt.anchorMin = new Vector2(0.5f, 0.5f);
            textRt.anchorMax = new Vector2(0.5f, 0.5f);
            textRt.pivot = new Vector2(0.5f, 0.5f);
            textRt.anchoredPosition = new Vector2(0f, 0f);
            textRt.sizeDelta = new Vector2(10f, 10f);

            // —— AddComponent<T> 的实例形态（热更侧另有 new GameObject(...) 的形态）——
            GameObject addGo = new GameObject("~keep_add", typeof(RectTransform));
            addGo.transform.SetParent(root.transform, false);
            Image addImg = addGo.AddComponent<Image>();
            addImg.enabled = false;

            // —— 闸门协程用到的等待类型与数值 API ——
            WaitForSecondsRealtime wait = new WaitForSecondsRealtime(0f);
            wait = null;
            float probe = Mathf.Clamp01(0f) + Mathf.Max(0, 1) + Mathf.RoundToInt(0.5f) + Mathf.CeilToInt(0.1f);
            float now = Time.realtimeSinceStartup;
            if (probe < 0f && now < 0f)
            {
                // 不可达分支：仅为消除"变量未使用"的编译警告（真实调用发生在上面）。
                Debug.Log("unreachable");
            }

            // —— 全部回收（同帧销毁，探针无任何可见/持久影响）——
            Object.Destroy(root);
        }
    }
}
