using UnityEngine;

namespace FTProject.AOT
{
    /// <summary>
    /// Boot 更新界面的字体桥（AOT 侧，2026-10-16）。
    ///
    /// ==================================================================
    /// 【为什么必须在 AOT 侧拿字体】
    ///   HybridCLR 下，热更代码只能调用"AOT 里真实存在（未被 IL2CPP 链接器裁剪）"
    ///   的方法。`Font.CreateDynamicFontFromOSFont` / `Resources.GetBuiltinResource&lt;Font&gt;`
    ///   若在 AOT 中没有任何调用点，会被裁剪 —— 热更侧调用时直接
    ///   `MissingMethodException: MethodNotFind`（2026-10-16 模拟器实测踩坑：
    ///   Boot 更新界面挂在"创建字体"第一步，异常杀死了闸门协程、应用停在黑屏）。
    ///
    ///   本类在 Boot 启动链（BootLoader.BootRoutine 开头）里**真实调用**这两个 API
    ///   并把结果缓存成静态字段；热更侧（BootHotUpdateUI）只做"读静态字段" ——
    ///   访问 AOT 已保留的成员是 HybridCLR 的标准安全路径。
    ///
    /// 【为什么优先系统字体】
    ///   内置字体（LegacyRuntime.ttf）没有 CJK 字形，中文会显示为方块。
    ///   系统字体（Android "sans-serif"）一般含中文；拿不到时由热更侧把文案退成英文
    ///   （见 BootHotUpdateUI.T）。
    /// ==================================================================
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
