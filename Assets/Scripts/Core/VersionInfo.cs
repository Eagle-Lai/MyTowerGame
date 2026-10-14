using System.Text;
using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 版本信息统一出口（P：版本号显示与日志）。
    ///
    /// 【它把两件事合在一处】
    ///   ① 应用版本 —— Player Settings → Version（打包时写进 APK 的 versionName），
    ///      读 <see cref="Application.version"/>，与 SplashView 既有逻辑同一口径。
    ///   ② 资源版本 —— YooAsset 激活清单的版本号（热更后自动变化），
    ///      经 <see cref="IHotUpdateLoader.CurrentResourceVersion"/> 读取；
    ///      编辑器直读 / 纯 AB 链路没有远端概念，返回 null（显示时自动省略）。
    ///
    /// 【谁用它】
    ///   · Launcher：启动时打印当前版本号日志（BuildLogSummary）。
    ///   · MainMenuView：主菜单底部中间版本行（BuildDisplayVersion）。
    ///   · YooAssetResLoader：检查更新 / 更新完成的前后版本日志。
    ///
    /// 【为什么显示格式用 "r" 而不是中文"资源"】版本行是技术信息，
    /// 走多语言要处理取词时序（主菜单打开前 LanguageManager 才初始化），
    /// 而 "v1.0.0 · r2026101501" 这种格式对任何语言玩家都无歧义，刻意保持中立。
    /// </summary>
    public static class VersionInfo
    {
        /// <summary>
        /// 应用版本（Player Settings → Version）。可能为空（工程没填），
        /// 调用方必须容忍空串 —— 显示层直接省略，日志层写 "(未设置)"。
        /// </summary>
        public static string AppVersion
        {
            get { return Application.version ?? string.Empty; }
        }

        /// <summary>
        /// 当前**已激活**的资源清单版本（YooAsset Init 成功后才有值；
        /// 热更完成后会变成远端最新版本）。拿不到时返回 null。
        ///
        /// 【为什么不直接引用 YooAssetResLoader】ResLoader.HotUpdate 按编译宏
        /// 自动选实现，本类与 UI 一样只认接口，不感知具体资源系统。
        /// </summary>
        public static string ResourceVersion
        {
            get
            {
                IHotUpdateLoader hot = ResLoader.HotUpdate;
                if (hot == null)
                {
                    return null;
                }
                try
                {
                    return hot.CurrentResourceVersion;
                }
                catch (System.Exception)
                {
                    // GetPackageVersion 在清单未激活等状态下可能抛异常 ——
                    // 版本号属于"锦上添花"的信息，绝不因为取版本把启动/界面搞挂。
                    return null;
                }
            }
        }

        /// <summary>
        /// 主菜单底部版本行的显示文案：
        ///   有应用版本且有资源版本 → <c>v1.0.0 · r2026101501</c>
        ///   只有应用版本           → <c>v1.0.0</c>
        ///   两者都没有             → 空串（节点隐藏文字，不占视觉）
        /// </summary>
        public static string BuildDisplayVersion()
        {
            string app = AppVersion;
            string res = ResourceVersion;

            StringBuilder sb = new StringBuilder(64);
            if (!string.IsNullOrEmpty(app))
            {
                sb.Append('v').Append(app);
            }
            if (!string.IsNullOrEmpty(res))
            {
                if (sb.Length > 0)
                {
                    sb.Append(" · ");
                }
                sb.Append('r').Append(res);
            }
            return sb.ToString();
        }

        /// <summary>
        /// 启动日志用的完整版本摘要（一行，方便adb logcat / Editor Console 过滤）。
        /// 示例：<c>[Version] 应用版本=1.0.0 | 资源版本=2026101501 | 资源实现=YooAssetResLoader</c>
        /// </summary>
        public static string BuildLogSummary()
        {
            string app = AppVersion;
            string res = ResourceVersion;
            return string.Format(
                "[Version] 应用版本={0} | 资源版本={1} | 资源实现={2}",
                string.IsNullOrEmpty(app) ? "(未设置)" : app,
                string.IsNullOrEmpty(res) ? "(未激活)" : res,
                ResLoader.ImplName);
        }
    }
}
