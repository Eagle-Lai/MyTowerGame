using UnityEditor;
using UnityEngine;
using YooAsset;
using YooAsset.Editor;

namespace FTProject.EditorTools
{
    /// <summary>
    /// 把 Main.unity 加入 YooAsset 收集器（一次性工具，幂等）。
    ///
    /// 【为什么需要】HybridCLR 真机上，**挂了热更脚本的场景打进 Build Settings 会
    /// 被烘焙成空壳**（热更程序集在打包的 IFilterBuildAssemblies 阶段被剔除），
    /// 运行时报 "missing script / serialization layout"。
    /// HybridCLR 官方工作流：这类场景必须打包成 AssetBundle，并在热更 dll 加载后加载。
    /// 本工具把 Assets/Scenes/Main.unity 收进 FreeTower 包裹（Scene 组），
    /// 由 HotUpdateEntry.EnterMainScene 在运行时经 YooAsset SceneHandle 加载。
    ///
    /// 【菜单】Tools ▸ 塔防 ▸ YooAsset 接入 ▸ 5. 把 Main.unity 加入收集器
    /// （入口序号 214，跟在 FTYooAssetDefine 的 3/4 之后）
    /// </summary>
    public static class AddMainSceneCollector
    {
        private const string ScenePath = "Assets/Scenes/Main.unity";

        /// <summary>收集计划：路径 → 组名（幂等，已存在的自动跳过）。</summary>
        private static readonly string[][] Plan =
        {
            new[] { ScenePath, "Scene" },
            new[] { "Assets/HotUpdateUI", "BootUI" },
            new[] { "Assets/Localization", "Localization" },
            // 【2026-10-14】Reporter 运行时图标：Reporter 为运行时动态挂载，
            // Initialize 时经 ResTable Reporter_* 逻辑名动态加载图片，必须被 AB 覆盖
            // （真机从热更服务器下发；见 GameSceneLauncher.EnsureReporter 说明）。
            new[] { "Assets/Reporter/Images", "ReporterData" },
        };

        [MenuItem("Tools/塔防/YooAsset 接入/5. 把 Main.unity 加入收集器（真机场景 AB）", false, 214)]
        public static void Run()
        {
            string error;
            Ensure(out error);   // 成败日志均在 Ensure 内输出
        }

        /// <summary>
        /// 幂等登记全部计划项；返回 false 时 error 为可读原因。
        /// 菜单入口只是外壳 —— 无人值守流水线（ReporterHotfixBuild）靠返回值判断成败。
        /// </summary>
        public static bool Ensure(out string error)
        {
            error = string.Empty;
            try
            {
                BundleCollectorPackage package = FindFreeTowerPackage();
                if (package == null)
                {
                    error = "找不到 FreeTower 包裹 —— 请先跑接入向导生成收集器配置。";
                    Debug.LogError("[YooAsset] " + error);
                    return false;
                }

                int added = 0;
                int skipped = 0;

                for (int i = 0; i < Plan.Length; i++)
                {
                    string path = Plan[i][0];
                    string groupName = Plan[i][1];

                    // 幂等：路径已在收集器里直接跳过
                    bool exists = false;
                    foreach (BundleCollectorGroup g in package.Groups)
                    {
                        foreach (BundleCollector c in g.Collectors)
                        {
                            if (c.CollectPath == path)
                            {
                                exists = true;
                                break;
                            }
                        }
                        if (exists) break;
                    }
                    if (exists)
                    {
                        skipped++;
                        continue;
                    }

                    BundleCollectorGroup group = FindOrCreateGroup(package, groupName);
                    BundleCollector collector = new BundleCollector();
                    collector.CollectPath = path;
                    collector.CollectorGUID = AssetDatabase.AssetPathToGUID(path);
                    collector.CollectorType = ECollectorType.MainAssetCollector;
                    // 可寻址已关闭 → 定位地址 = 资源路径，地址规则名字只是占位。
                    collector.AddressRuleName = nameof(AddressByFileName);
                    collector.PackRuleName = nameof(FTBundlePackRule);
                    collector.FilterRuleName = nameof(CollectAll);
                    collector.AssetTags = string.Empty;
                    collector.UserData = string.Empty;
                    group.Collectors.Add(collector);
                    added++;
                    Debug.Log("[YooAsset] 已加入收集器：" + path + "（组 " + groupName + "）");
                }

                if (added > 0)
                {
                    BundleCollectorSettingData.SaveFile();
                    AssetDatabase.SaveAssets();
                }

                Debug.Log(string.Format(
                    "[YooAsset] 收集器更新完成：新增 {0} 个，已有 {1} 个。场景、引导期 UI 与 Reporter 图标均从 AB 加载（HybridCLR 真机要求）。",
                    added, skipped));
                return true;
            }
            catch (System.Exception e)
            {
                error = e.ToString();
                Debug.LogError("[YooAsset] 收集器更新失败：" + e);
                return false;
            }
        }

        /// <summary>按组名找组，没有就创建（与 FTYooAssetSetupWizard.FindOrCreateGroup 同语义）。</summary>
        private static BundleCollectorGroup FindOrCreateGroup(BundleCollectorPackage package, string groupName)
        {
            foreach (BundleCollectorGroup g in package.Groups)
            {
                if (g.GroupName == groupName)
                {
                    return g;
                }
            }

            BundleCollectorGroup newGroup = new BundleCollectorGroup();
            newGroup.GroupName = groupName;
            newGroup.GroupDesc = "HybridCLR 真机：挂热更脚本的资源必须从 AB 加载";
            newGroup.ActiveRuleName = nameof(EnableGroup);
            package.Groups.Add(newGroup);
            return newGroup;
        }

        /// <summary>找名为 FreeTower 的包裹（与 YooAssetResLoader.PackageName 对应），找不到退回第一个。</summary>
        private static BundleCollectorPackage FindFreeTowerPackage()
        {
            BundleCollectorPackage first = null;
            foreach (BundleCollectorPackage p in BundleCollectorSettingData.Setting.Packages)
            {
                if (p.PackageName == "FreeTower")
                {
                    return p;
                }
                if (first == null)
                {
                    first = p;
                }
            }
            return first;
        }
    }
}
