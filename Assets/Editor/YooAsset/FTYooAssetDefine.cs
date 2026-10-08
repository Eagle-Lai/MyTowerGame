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

        [MenuItem("Tools/塔防/YooAsset 接入/0. 查看宏状态", false, 209)]
        public static void ReportStatus()
        {
            List<string> on = new List<string>();
            List<string> off = new List<string>();

            for (int i = 0; i < Targets.Length; i++)
            {
                NamedBuildTarget target = Targets[i];
                try
                {
                    if (HasSymbol(PlayerSettings.GetScriptingDefineSymbols(target), Symbol))
                    {
                        on.Add(target.TargetName);
                    }
                    else
                    {
                        off.Add(target.TargetName);
                    }
                }
                catch (Exception e)
                {
                    off.Add(target.TargetName + "(读取失败:" + e.GetType().Name + ")");
                }
            }

            Debug.Log(string.Format(
                "[YooAsset] USE_YOOASSET 宏状态\n" +
                "  已启用平台：{0}\n" +
                "  未启用平台：{1}\n" +
                "  当前加载器实现：{2}\n" +
                "  当前平台：{3}",
                on.Count == 0 ? "（无）" : string.Join("、", on.ToArray()),
                off.Count == 0 ? "（无）" : string.Join("、", off.ToArray()),
                ResLoader.ImplName,
                EditorUserBuildSettings.activeBuildTarget));
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
            List<string> changed = new List<string>();
            List<string> skipped = new List<string>();

            for (int i = 0; i < Targets.Length; i++)
            {
                NamedBuildTarget target = Targets[i];
                string name = target.TargetName;

                try
                {
                    string before = PlayerSettings.GetScriptingDefineSymbols(target);
                    string after = Toggle(before, Symbol, enable);

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
                Debug.Log(string.Format("[YooAsset] USE_YOOASSET 在所有目标平台上都已是「{0}」状态，无需改动。", action));
            }
            else
            {
                Debug.Log(string.Format("[YooAsset] 已{0} USE_YOOASSET，改动 {1} 个平台：\n{2}\n" +
                    "  Unity 正在重新编译；编译完成后菜单「Tools ▸ 塔防 ▸ YooAsset 接入 ▸ 接入向导」才可用。",
                    action, changed.Count, string.Join("\n", changed.ToArray())));
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
