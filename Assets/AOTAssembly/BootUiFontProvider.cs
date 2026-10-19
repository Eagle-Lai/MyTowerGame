using UnityEngine;

namespace FTProject.AOT
{
    /// <summary>Legacy UGUI font bridge retained for compatible runtime callers.
    /// The scene-configured HotUpdateView uses APK-owned TMP fonts and does not depend on it.
    /// </summary>
    public static class BootUiFontProvider
    {
        /// <summary>Boot 更新界面用字体（系统字体优先，失败退内置；皆失败为 null）。</summary>
        public static Font UiFont { get; private set; }

        /// <summary>UiFont 是否为含 CJK 的系统字体（决定热更侧文案用中文还是英文）。</summary>
        public static bool UiFontHasCjk { get; private set; }

        private static bool s_tried;

        /// <summary>启动早期调用一次（幂等）。</summary>
        public static void Ensure()
        {
            if (s_tried)
            {
                return;
            }
            s_tried = true;

            try
            {
                UiFont = Font.CreateDynamicFontFromOSFont(
                    new string[] { "sans-serif", "Roboto", "Noto Sans CJK SC", "Arial" }, 26);
            }
            catch (System.Exception e)
            {
                Debug.LogWarning("[Boot] 系统字体创建失败（退内置字体）：" + e.Message);
                UiFont = null;
            }

            UiFontHasCjk = UiFont != null;

            if (UiFont == null)
            {
                try
                {
                    UiFont = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
                }
                catch (System.Exception e)
                {
                    Debug.LogWarning("[Boot] 内置字体读取失败（更新界面将无文字，仅图形）：" + e.Message);
                    UiFont = null;
                }
            }

            Debug.Log("[Boot] 更新界面字体：" + (UiFont == null
                ? "(不可用)"
                : UiFont.name + (UiFontHasCjk ? "（系统字体，支持中文）" : "（内置字体，文案退英文）")));
        }
    }
}
