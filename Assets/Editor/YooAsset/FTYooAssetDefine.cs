using System;
using System.Collections.Generic;
using UnityEditor;
using UnityEditor.Build;
using UnityEngine;

namespace FTProject.EditorTools
{
    /// <summary>
    /// YooAsset 编译宏 <c>USE_YOOASSET</c> 的开关。
    ///
    /// 【为什么单独一个文件、且刻意不套宏 —— 这是一个"鸡生蛋"问题】
    ///   工程约定"新依赖一律加宏"，于是 <c>YooAssetResLoader</c>、YooAsset 打包规则、
    ///   接入向导全部包在 <c>#if USE_YOOASSET</c> 里。但那样一来，宏本身就没法靠这些
    ///   代码去打开。所以宏开关单独放这里，**不引用任何 YooAsset 类型**，
    ///   保证在宏关闭（= 包没拉下来 / 想回退旧链路）时本文件依然能编译、能执行。
    ///
    /// 【为什么一次写多个平台】编译宏是**按平台组**存的，不是全局的。
    ///   只给当前平台加，换平台出包时会静默失效，运行时才发现"换回了旧加载器"。
    ///
    /// 【与既有 FORCE_AB 的关系】两者是独立的开关，叠在一起的含义见 ResLoader.cs：
    ///   USE_YOOASSET 决定"用不用 YooAsset"；FORCE_AB 决定 YooAsset 内部走
    ///   "编辑器模拟模式"还是"真资源包（离线模式）"。
    /// </summary>
    public static class FTYooAssetDefine
    {
        /// <summary>编译宏名。运行时适配器与编辑器工具都以此为准。</summary>
        public const string Symbol = "USE_YOOASSET";

        /// <summary>
        /// 热更编译宏名。打开后 YooAsset 走 HostPlayMode（联机模式），
        /// 启动时去 <c>ResServerConfig.ServerUrl</c> 比对版本并下载差异。
        ///
        /// 【为什么与 USE_YOOASSET 分开两个宏】
        ///   两者正交：
        ///     USE_YOOASSET → "用不用 YooAsset 这套资源系统"
        ///     FT_HOTUPDATE → "用 YooAsset 时，从本地包读还是从远端下载"
        ///   合并成一个宏的话，"想在编辑器里验证离线包"与"真机走热更"就无法共存了。
        /// </summary>
        public const string HotUpdateSymbol = "FT_HOTUPDATE";

        /// <summary>
        /// 一并处理的平台组。工程实际出包是 Standalone + Android，iOS/WebGL 顺带写上，
        /// 避免将来新增平台时漏配。
        /// </summary>
        private static readonly NamedBuildTarget[] Targets =
        {
            NamedBuildTarget.Standalone,
            NamedBuildTarget.Android,
            NamedBuildTarget.iOS,
            NamedBuildTarget.WebGL,
        };

        // ==================================================================
        // 菜单
        // ==================================================================

        [MenuItem("Tools/塔防/YooAsset 接入/1. 启用 USE_YOOASSET 宏", false, 210)]
        public static void Enable()
        {
            Apply(true);
        }

        [MenuItem("Tools/塔防/YooAsset 接入/2. 停用 USE_YOOASSET 宏（回退原链路）", false, 211)]
        public static void Disable()
        {
            Apply(false);
        }

        // ------------------------------------------------------------------
        // 热更宏（FT_HOTUPDATE）
        // ------------------------------------------------------------------

        [MenuItem("Tools/塔防/YooAsset 接入/3. 启用 FT_HOTUPDATE 宏（真机热更）", false, 212)]
        public static void EnableHotUpdate()
        {
            ApplySymbol(HotUpdateSymbol, true);
        }

        [MenuItem("Tools/塔防/YooAsset 接入/4. 停用 FT_HOTUPDATE 宏（离线模式）", false, 213)]
        public static void DisableHotUpdate()
        {
            ApplySymbol(HotUpdateSymbol, false);
        }

        [MenuItem("Tools/塔防/YooAsset 接入/0. 查看宏状态", false, 209)]
        public static void ReportStatus()
        {
            List<string> on = new List<string>();
            List<string> off = new List<string>();
            List<string> hotOn = new List<string>();
            List<string> hotOff = new List<string>();

            for (int i = 0; i < Targets.Length; i++)
            {
                NamedBuildTarget target = Targets[i];
                try
                {
                    string symbols = PlayerSettings.GetScriptingDefineSymbols(target);
                    if (HasSymbol(symbols, Symbol))
                    {
                        on.Add(target.TargetName);
                    }
                    else
                    {
                        off.Add(target.TargetName);
                    }

                    if (HasSymbol(symbols, HotUpdateSymbol))
                    {
                        hotOn.Add(target.TargetName);
                    }
                    else
                    {
                        hotOff.Add(target.TargetName);
                    }
                }
                catch (Exception e)
                {
                    off.Add(target.TargetName + "(读取失败:" + e.GetType().Name + ")");
                    hotOff.Add(target.TargetName + "(读取失败:" + e.GetType().Name + ")");
                }
            }

            Debug.Log(string.Format(
                "[YooAsset] 宏状态\n" +
                "  USE_YOOASSET 已启用平台：{0}\n" +
                "  USE_YOOASSET 未启用平台：{1}\n" +
                "  FT_HOTUPDATE 已启用平台：{2}\n" +
                "  FT_HOTUPDATE 未启用平台：{3}\n" +
                "  当前加载器实现：{4}\n" +
                "  当前平台：{5}\n" +
                "  热更服务器地址：{6}（ResServerConfig 常量，编辑器下仅供参考；\n" +
                "    真机以 APK 内打包的值 + persistentDataPath/server.txt 覆盖为准）",
                on.Count == 0 ? "（无）" : string.Join("、", on.ToArray()),
                off.Count == 0 ? "（无）" : string.Join("、", off.ToArray()),
                hotOn.Count == 0 ? "（无）" : string.Join("、", hotOn.ToArray()),
                hotOff.Count == 0 ? "（无）" : string.Join("、", hotOff.ToArray()),
                ResLoader.ImplName,
                EditorUserBuildSettings.activeBuildTarget,
                ResServerConfig.ServerUrl));
        }

        // ==================================================================
        // 实现
        // ==================================================================

        /// <summary>当前在 Build Settings 里选中的平台是否已启用宏（向导状态面板用）。</summary>
        public static bool IsEnabledForActiveTarget()
        {
            try
            {
                // 用 selectedBuildTargetGroup 而不是 BuildPipeline.GetBuildTargetGroup：
                // 后者在 Unity 2022 的官方 API 文档里已经查不到（即将废弃）。
                NamedBuildTarget target = NamedBuildTarget.FromBuildTargetGroup(
                    EditorUserBuildSettings.selectedBuildTargetGroup);
                return HasSymbol(PlayerSettings.GetScriptingDefineSymbols(target), Symbol);
            }
            catch (Exception)
            {
                return false;
            }
        }

        private static void Apply(bool enable)
        {
            ApplySymbol(Symbol, enable);
        }

        /// <summary>
        /// 在全部目标平台上开关一个宏。
        /// 【为什么要按平台组遍历】编译宏是按平台组存的；只改当前平台会静默失效。
        /// 【为什么异常要跳过而不是中断】iOS/WebGL 等平台组在部分环境下不可读写，
        ///   中断会导致"改到一半"，其余平台漏改 —— 统一收集后一并告警更清晰。
        /// </summary>
        private static void ApplySymbol(string symbol, bool enable)
        {
            List<string> changed = new List<string>();
            List<string> skipped = new List<string>();

            for (int i = 0; i < Targets.Length; i++)
            {
                NamedBuildTarget target = Targets[i];
                string name = target.TargetName;

                try
                {
                    string before = PlayerSettings.GetScriptingDefineSymbols(target);
                    string after = Toggle(before, symbol, enable);

                    if (string.Equals(before ?? string.Empty, after, StringComparison.Ordinal))
                    {
                        continue;
                    }

                    PlayerSettings.SetScriptingDefineSymbols(target, after);
                    changed.Add(string.Format("  {0}：{1} → {2}",
                        name,
                        string.IsNullOrEmpty(before) ? "(空)" : before,
                        string.IsNullOrEmpty(after) ? "(空)" : after));
                }
                catch (Exception e)
                {
                    // 某些平台组在当前环境不可读写；跳过而不是中断，其余平台照常处理。
                    skipped.Add(string.Format("  {0}：跳过（{1}）", name, e.GetType().Name));
                }
            }

            AssetDatabase.Refresh();

            string action = enable ? "启用" : "停用";
            if (changed.Count == 0)
            {
                Debug.Log(string.Format("[YooAsset] {0} 在所有目标平台上都已是「{1}」状态，无需改动。", symbol, action));
            }
            else
            {
                Debug.Log(string.Format("[YooAsset] 已{0} {1}，改动 {2} 个平台：\n{3}\n" +
                    "  Unity 正在重新编译；编译完成后菜单「Tools ▸ 塔防 ▸ YooAsset 接入 ▸ 接入向导」才可用。",
                    action, symbol, changed.Count, string.Join("\n", changed.ToArray())));
            }

            if (skipped.Count > 0)
            {
                Debug.LogWarning("[YooAsset] 以下平台未能读写（若确实需要，请在 Player Settings 里手工添加）:\n"
                    + string.Join("\n", skipped.ToArray()));
            }
        }

        /// <summary>在分号分隔的宏列表里增删一个宏；保持原有顺序，不产生空项。</summary>
        private static string Toggle(string symbols, string symbol, bool enable)
        {
            List<string> list = new List<string>();
            if (string.IsNullOrEmpty(symbols) == false)
            {
                string[] parts = symbols.Split(';');
                for (int i = 0; i < parts.Length; i++)
                {
                    string s = parts[i].Trim();
                    if (s.Length == 0)
                    {
                        continue;
                    }
                    if (string.Equals(s, symbol, StringComparison.Ordinal))
                    {
                        continue;
                    }
                    if (list.Contains(s) == false)
                    {
                        list.Add(s);
                    }
                }
            }

            if (enable && list.Contains(symbol) == false)
            {
                list.Add(symbol);
            }

            return string.Join(";", list.ToArray());
        }

        private static bool HasSymbol(string symbols, string symbol)
        {
            if (string.IsNullOrEmpty(symbols))
            {
                return false;
            }

            string[] parts = symbols.Split(';');
            for (int i = 0; i < parts.Length; i++)
            {
                if (string.Equals(parts[i].Trim(), symbol, StringComparison.Ordinal))
                {
                    return true;
                }
            }
            return false;
        }
    }
}
