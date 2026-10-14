// 触发记录：2026-10-14 17:07 借道构建（资产变更 → 域重载 → 消费 trigger）
using System.IO;
using UnityEditor;
using UnityEngine;

namespace FTProject.EditorTools
{
    /// <summary>
    /// 【无人值守】标志文件驱动的构建触发器。
    ///
    /// 场景：Unity 编辑器（GUI）开着、但外部（脚本 / CI / 助手）需要发起一次热更构建，
    /// 而 batchmode 因工程锁不可用。此时在 `Library/FT_AUTOBUILD.trigger` 写入：
    ///   - "full"（或任意非 "dll" 内容）→ 跑完整流水线（dll ▸ 拷贝 ▸ 收集器 ▸ AB）；
    ///   - "dll"  → 仅重编热更 dll（dll-only 模式）。
    /// 编辑器在下一次域重载 / 启动后自动消费标志文件并执行对应流水线；
    /// 与菜单 9 / 9a、batchmode Start / StartDllOnly 完全同源。
    ///
    /// 【为什么挂在 [InitializeOnLoad】域重载是"编辑器检测到脚本变更"的必然副产物：
    /// 把标志文件与代码改动**一起**准备好，重载后本触发器立即接手，全流程无需人工点菜单。
    /// </summary>
    [InitializeOnLoad]
    public static class FT_AutoBuildTrigger
    {
        private const string TriggerRel = "Library/FT_AUTOBUILD.trigger";

        static FT_AutoBuildTrigger()
        {
            EditorApplication.delayCall += Check;
        }

        private static void Check()
        {
            try
            {
                string root = Path.GetDirectoryName(Application.dataPath);
                string path = Path.Combine(root, TriggerRel);
                if (!File.Exists(path))
                {
                    return;
                }

                string mode = File.ReadAllText(path).Trim().ToLowerInvariant();
                File.Delete(path);   // 先删再跑：后续域重载续跑时不会二次触发
                Debug.Log("[AutoBuild] 标志文件触发构建，mode=" + mode);

                if (mode == "dll")
                {
                    ReporterHotfixBuild.StartDllOnly();
                }
                else
                {
                    ReporterHotfixBuild.Start();
                }
            }
            catch (System.Exception e)
            {
                Debug.LogError("[AutoBuild] 触发器异常：" + e);
            }
        }
    }
}
