#if USE_YOOASSET
using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEngine;
using YooAsset;
using YooAsset.Editor;

namespace FTProject.EditorTools
{
    /// <summary>
    /// YooAsset 接入向导：把 YooAsset 真正跑起来所需的四件事做成按钮。
    ///
    ///   ① 生成 / 修复收集器配置（Bundle Collector）
    ///   ② 静态一致性校验：ResTable ↔ 分包规则 ↔ 文件存在性 ↔ 收集器覆盖
    ///   ③ 构建：模拟清单（编辑器 Play 用）/ 真实资源包
    ///   ④ 回读校验：用**真实加载器**逐个解析 ResTable 逻辑名
    ///
    /// 【为什么要有 ② 和 ④】"配置写进去了"和"资源真能加载到"是两件事。
    ///   ② 能离线抓出"登记了但目录没收集到""包名与 ResTable 不一致"这类配置错误；
    ///   ④ 才是端到端真相 —— 它走的是运行时同一个适配器、同一条探测路径。
    ///   没有 ④ 的话，"构建成功"很容易被误读成"跑得通"。
    ///
    /// 【本窗口自身也套 USE_YOOASSET】所以宏关闭时菜单不会出现。
    ///   开宏请用同一菜单下的「1. 启用 USE_YOOASSET 宏」（那个文件没套宏，专为打破这个循环）。
    /// </summary>
    public class FTYooAssetSetupWizard : EditorWindow
    {
        private const string OpenMenuPath = "Tools/塔防/YooAsset 接入/接入向导";
        private const string EnableSymbolMenuPath = "Tools/塔防/YooAsset 接入/1. 启用 USE_YOOASSET 宏";

        /// <summary>
        /// 收集器覆盖的资源根目录（分组名，目录）。
        /// 这些目录与 ResTable 里登记的资源路径一一对应（见 Docs/YooAsset_Integration.md）。
        ///
        /// ⚠️ 不要图省事改成收集整个 `Assets`：那会把 Scenes / Scripts / TextMesh Pro /
        ///    Reporter 等一并打进资源包，既涨包体又会把与游戏无关的资源暴露给加载器。
        /// </summary>
        private static readonly string[][] CollectPlan =
        {
            new[] { "Config", "Assets/ConfigJson" },
            new[] { "Art", "Assets/Art" },
            new[] { "Art", "Assets/_UIAssets" },
            new[] { "Prefab", "Assets/Prefabs" },
            new[] { "Font", "Assets/Font" },
            new[] { "Audio", "Assets/Audio" },
        };

        private string _version = "1.0.0";

        /// <summary>
        /// 是否"彻底重建"：清空 SBP 构建缓存 + 删掉整个包裹根目录。
        ///
        /// 默认**关**。默认路径只精确删掉本次的版本目录
        /// （`{BuildOutputRoot}/{平台}/{包裹}/{版本}`），因为"清空整个包裹根目录"会连
        /// `Simulate` 一起删掉 —— 那是编辑器模拟模式当前正在用的清单，而向导第 ④ 步的
        /// 回读校验就在同一次编辑器会话里跑。怀疑 Unity 构建缓存不一致时再打开它。
        /// </summary>
        private bool _fullRebuild;
        private Vector2 _scroll;
        private readonly List<string> _log = new List<string>();
        private int _logErrors;
        private int _logWarns;

        /// <summary>
        /// 状态缓存。OnGUI 每帧都跑，而 HasSettingAsset 内部是 AssetDatabase.FindAssets ——
        /// 不缓存的话拖窗口都会反复查资产库。所有动作执行完调 InvalidateStatus() 让它重算。
        /// </summary>
        private bool _statusValid;
        private bool _hasSettingCache;
        private int _collectorCountCache;

        /// <summary>包名与运行时适配器强一致，避免两处各写一份字符串。</summary>
        private static string PackageName
        {
            get { return YooAssetResLoader.PackageName; }
        }

        // ==================================================================
        // 窗口
        // ==================================================================

        [MenuItem(OpenMenuPath, false, 208)]
        public static void Open()
        {
            FTYooAssetSetupWizard window = GetWindow<FTYooAssetSetupWizard>(true, "YooAsset 接入向导");
            window.minSize = new Vector2(560f, 480f);
            window.Show();
        }

        [MenuItem(EnableSymbolMenuPath, true)]
        private static bool ValidateEnableMenu()
        {
            return FTYooAssetDefine.IsEnabledForActiveTarget() == false;
        }

        private void OnGUI()
        {
            DrawStatus();
            EditorGUILayout.Space();

            DrawSection("① 收集器配置", "把 ResTable 的分包方案写进 YooAsset 的 Bundle Collector 配置资产。", () =>
            {
                if (GUILayout.Button("生成 / 修复收集器配置（幂等）", GUILayout.Height(26f)))
                {
                    GenerateCollectorSettings();
                }
            });

            DrawSection("② 静态一致性校验", "不构建也能跑：核对分包规则、文件存在性、收集器覆盖、包名一致性。", () =>
            {
                if (GUILayout.Button("执行静态校验", GUILayout.Height(26f)))
                {
                    RunStaticCheck();
                }
            });

            DrawSection("③ 构建", "模拟清单供编辑器 Play 使用；真实资源包供真机 / FORCE_AB 使用。", () =>
            {
                EditorGUILayout.BeginHorizontal();
                if (GUILayout.Button("构建模拟清单", GUILayout.Height(26f)))
                {
                    BuildSimulate();
                }
                if (GUILayout.Button("构建真实资源包", GUILayout.Height(26f)))
                {
                    BuildRealBundles();
                }
                EditorGUILayout.EndHorizontal();

                _version = EditorGUILayout.TextField("资源包版本", _version);
                _fullRebuild = EditorGUILayout.Toggle(
                    new GUIContent("彻底重建", "清空 SBP 构建缓存 + 删掉整个包裹根目录（含 Simulate）。" +
                        "默认关闭：只删本次版本目录，重建更快，也不影响编辑器模拟模式正在用的清单。"),
                    _fullRebuild);
            });

            DrawSection("④ 回读校验", "用运行时同一个加载器逐个解析 ResTable 逻辑名 —— 这是端到端的真相。", () =>
            {
                if (GUILayout.Button("执行回读校验（会实际加载全部资源）", GUILayout.Height(26f)))
                {
                    RunRuntimeProbe();
                }
            });

            EditorGUILayout.Space();
            DrawLog();
        }

        private void DrawStatus()
        {
            EditorGUILayout.LabelField("状态", EditorStyles.boldLabel);

            string define = FTYooAssetDefine.IsEnabledForActiveTarget()
                ? "已启用（当前平台）"
                : "未启用（当前平台）";
            EditorGUILayout.LabelField("USE_YOOASSET 宏", define);

            EditorGUILayout.LabelField("当前加载器实现", ResLoader.ImplName);
            EditorGUILayout.LabelField("包裹名称", PackageName);

            bool hasSetting = HasSettingAsset();
            EditorGUILayout.LabelField("收集器配置资产", hasSetting ? "已存在" : "尚未生成");
            if (hasSetting)
            {
                EditorGUILayout.LabelField("  收集器数量", CollectorCount().ToString());
            }
            else
            {
                EditorGUILayout.HelpBox("还没有 BundleCollectorSetting.asset —— 点下面的「生成 / 修复收集器配置」。", MessageType.Info);
            }

            if (ResLoader.ImplName != "YooAssetResLoader")
            {
                EditorGUILayout.HelpBox(
                    "当前加载器不是 YooAssetResLoader，说明 USE_YOOASSET 只在部分平台生效。" +
                    "请先执行菜单里的「1. 启用 USE_YOOASSET 宏」。",
                    MessageType.Warning);
            }
        }

        private void DrawSection(string title, string hint, Action body)
        {
            EditorGUILayout.Space();
            EditorGUILayout.LabelField(title, EditorStyles.boldLabel);
            EditorGUILayout.LabelField(hint, EditorStyles.wordWrappedMiniLabel);
            body();
        }

        private void DrawLog()
        {
            EditorGUILayout.LabelField(
                string.Format("报告（{0} 个错误 / {1} 个警告）", _logErrors, _logWarns),
                EditorStyles.boldLabel);

            _scroll = EditorGUILayout.BeginScrollView(_scroll, GUILayout.ExpandHeight(true));
            for (int i = 0; i < _log.Count; i++)
            {
                EditorGUILayout.LabelField(_log[i], EditorStyles.wordWrappedMiniLabel);
            }
            EditorGUILayout.EndScrollView();
        }

        // ==================================================================
        // 日志
        // ==================================================================

        private void ClearLog()
        {
            _log.Clear();
            _logErrors = 0;
            _logWarns = 0;
        }

        private void Info(string message)
        {
            _log.Add("· " + message);
        }

        private void Warn(string message)
        {
            _logWarns++;
            _log.Add("⚠ " + message);
        }

        private void Fail(string message)
        {
            _logErrors++;
            _log.Add("✗ " + message);
        }

        private void Success(string message)
        {
            _log.Add("✓ " + message);
        }

        // ==================================================================
        // ① 收集器配置
        // ==================================================================

        private void GenerateCollectorSettings()
        {
            ClearLog();
            InvalidateStatus();
            try
            {
                BundleCollectorPackage package = FindOrCreatePackage();

                // 【本向导最关键的一行】关闭可寻址。
                //
                // 打开可寻址时，Must 保证"每个资源的寻址地址全局唯一"，而本工程
                // 收集目录里存在 123 组同名文件（Bat / Bear / Controller …），
                // 用文件名寻址会在收集阶段直接抛 "Address already exists"。
                //
                // 关掉之后，YooAsset 用**资源路径**当定位地址（并自动附加"去扩展名"变体，
                // 因为 SupportExtensionless = true）。而 ResTable 里的 EditorPath 本来就是
                // 资源路径 —— 于是：
                //   · 不需要任何地址映射，ResTable 仍是唯一寻址源；
                //   · 路径天然唯一，不存在重名冲突；
                //   · 运行时适配器的探测候选（去扩展名全路径 / 带扩展名全路径）正好命中。
                package.EnableAddressable = false;
                package.SupportExtensionless = true;
                package.LocationToLower = false;
                package.IncludeAssetGUID = false;
                package.AutoCollectShaders = true;      // 着色器自动收进 unityshaders 包
                package.IgnoreRuleName = nameof(NormalIgnoreRule);
                package.PackageDesc = "FreeTower 主包裹（由接入向导生成，请勿手工改寻址开关）";

                // 分组按用途拆，便于在 YooAsset 窗口里查看；分组名不影响寻址与分包。
                string[][] plan = CollectPlan;

                int added = 0;
                int skipped = 0;

                for (int i = 0; i < plan.Length; i++)
                {
                    string groupName = plan[i][0];
                    string path = plan[i][1];

                    if (AssetDatabase.IsValidFolder(path) == false)
                    {
                        Warn(string.Format("收集目录不存在，已跳过：{0}", path));
                        continue;
                    }

                    if (HasCollector(package, path))
                    {
                        skipped++;
                        continue;
                    }

                    BundleCollectorGroup group = FindOrCreateGroup(package, groupName);
                    BundleCollector collector = new BundleCollector();
                    collector.CollectPath = path;
                    collector.CollectorGUID = AssetDatabase.AssetPathToGUID(path);
                    collector.CollectorType = ECollectorType.MainAssetCollector;
                    // 寻址规则在"关闭可寻址"时不起作用，但仍必须是合法规则名，否则配置校验会报错。
                    collector.AddressRuleName = nameof(AddressByFileName);
                    collector.PackRuleName = nameof(FTBundlePackRule);
                    collector.FilterRuleName = nameof(CollectAll);
                    collector.AssetTags = string.Empty;
                    collector.UserData = string.Empty;
                    BundleCollectorSettingData.CreateCollector(group, collector);
                    added++;
                }

                BundleCollectorSettingData.SaveFile();
                AssetDatabase.SaveAssets();

                Success(string.Format("收集器配置已就绪：新增 {0} 个收集器，已有 {1} 个（幂等，不重复添加）。", added, skipped));
                Info("打包规则 = FTBundlePackRule（按 ResTable 分包）；过滤规则 = CollectAll；忽略规则 = NormalIgnoreRule");
                Info("可寻址 = 关闭 → 定位地址就是资源路径，与 ResTable 的 EditorPath 天然对齐。");
                Info("配置文件位置：Assets/BundleCollectorSetting.asset");

                if (added > 0)
                {
                    EditorUtility.DisplayDialog(
                        "收集器配置已生成",
                        string.Format("新增 {0} 个收集器，已保存到 Assets/BundleCollectorSetting.asset。\n\n" +
                                      "下一步建议执行「静态一致性校验」，确认没有漏收或错配。", added),
                        "好");
                }
            }
            catch (Exception e)
            {
                Fail("生成收集器配置失败：" + e.Message);
                Debug.LogException(e);
            }
        }

        private BundleCollectorPackage FindOrCreatePackage()
        {
            BundleCollectorSetting setting = BundleCollectorSettingData.Setting;
            for (int i = 0; i < setting.Packages.Count; i++)
            {
                if (setting.Packages[i].PackageName == PackageName)
                {
                    return setting.Packages[i];
                }
            }
            return BundleCollectorSettingData.CreatePackage(PackageName);
        }

        private static BundleCollectorGroup FindOrCreateGroup(BundleCollectorPackage package, string groupName)
        {
            for (int i = 0; i < package.Groups.Count; i++)
            {
                if (package.Groups[i].GroupName == groupName)
                {
                    return package.Groups[i];
                }
            }
            return BundleCollectorSettingData.CreateGroup(package, groupName);
        }

        private static bool HasCollector(BundleCollectorPackage package, string collectPath)
        {
            for (int i = 0; i < package.Groups.Count; i++)
            {
                List<BundleCollector> collectors = package.Groups[i].Collectors;
                for (int j = 0; j < collectors.Count; j++)
                {
                    if (collectors[j].CollectPath == collectPath)
                    {
                        return true;
                    }
                }
            }
            return false;
        }

        private void InvalidateStatus()
        {
            _statusValid = false;
        }

        private bool HasSettingAsset()
        {
            RefreshStatus();
            return _hasSettingCache;
        }

        private int CollectorCount()
        {
            RefreshStatus();
            return _collectorCountCache;
        }

        private void RefreshStatus()
        {
            if (_statusValid)
            {
                return;
            }

            _statusValid = true;
            _hasSettingCache = BundleCollectorSettingData.HasSettingAsset();
            _collectorCountCache = 0;

            if (_hasSettingCache == false)
            {
                return;
            }

            BundleCollectorSetting setting = BundleCollectorSettingData.Setting;
            for (int i = 0; i < setting.Packages.Count; i++)
            {
                if (setting.Packages[i].PackageName != PackageName)
                {
                    continue;
                }

                BundleCollectorPackage package = setting.Packages[i];
                for (int g = 0; g < package.Groups.Count; g++)
                {
                    _collectorCountCache += package.Groups[g].Collectors.Count;
                }
                break;
            }
        }

        // ==================================================================
        // ② 静态一致性校验
        // ==================================================================

        private void RunStaticCheck()
        {
            ClearLog();

            if (HasSettingAsset() == false)
            {
                Fail("还没有收集器配置资产，请先执行「生成 / 修复收集器配置」。");
                return;
            }

            FTBundlePackRule.ResetReport();

            CheckBundleNameConsistency();
            CheckAssetFilesExist();
            CheckCollectorCoverage();

            EditorGUILayout.Space();
            if (_logErrors == 0 && _logWarns == 0)
            {
                Success("静态校验全部通过。");
            }
        }

        /// <summary>ResTable 声明的包名 与 打包规则算出的包名 必须逐条一致。</summary>
        private void CheckBundleNameConsistency()
        {
            int total = 0;
            int mismatch = 0;
            List<string> samples = new List<string>();

            foreach (KeyValuePair<string, ResAddress> kv in ResTable.All)
            {
                string path = kv.Value.EditorPath;
                if (string.IsNullOrEmpty(path))
                {
                    continue;
                }

                total++;
                string actual = FTBundlePackRule.ResolveBundle(path);
                if (string.Equals(actual, kv.Value.Bundle, StringComparison.Ordinal) == false)
                {
                    mismatch++;
                    if (samples.Count < 10)
                    {
                        samples.Add(string.Format("{0}（{1}）：ResTable={2}，规则算出={3}",
                            kv.Key, path, kv.Value.Bundle, actual));
                    }
                }
            }

            if (mismatch == 0)
            {
                Success(string.Format("包名一致性：{0} 条登记资源全部与打包规则算出的一致。", total));
            }
            else
            {
                Fail(string.Format("包名一致性：{0}/{1} 条不一致 —— ResTable 与打包规则分叉了：", mismatch, total));
                for (int i = 0; i < samples.Count; i++)
                {
                    Info("  " + samples[i]);
                }
            }
        }

        private void CheckAssetFilesExist()
        {
            int missing = 0;
            List<string> samples = new List<string>();

            foreach (KeyValuePair<string, ResAddress> kv in ResTable.All)
            {
                string path = kv.Value.EditorPath;
                if (string.IsNullOrEmpty(path))
                {
                    continue;
                }

                if (AssetDatabase.LoadAssetAtPath<UnityEngine.Object>(path) == null)
                {
                    missing++;
                    if (samples.Count < 10)
                    {
                        samples.Add(kv.Key + " → " + path);
                    }
                }
            }

            if (missing == 0)
            {
                Success("文件存在性：ResTable 里登记的每个资源都能在工程里找到。");
            }
            else
            {
                Fail(string.Format("文件存在性：{0} 条登记资源在磁盘上找不到：", missing));
                for (int i = 0; i < samples.Count; i++)
                {
                    Info("  " + samples[i]);
                }
            }
        }

        /// <summary>
        /// 用 YooAsset 自己的收集入口跑一遍（不落盘），核对：
        ///   · 登记资源是否都被收集目录覆盖到（没覆盖 = 运行时定位不到）
        ///   · 哪些资源被收集了但 ResTable 里没有登记（走降级分包，需要人工确认）
        /// </summary>
        private void CheckCollectorCoverage()
        {
            CollectResult result;
            try
            {
                result = BundleCollectorSettingData.Setting.BeginCollect(
                    PackageName,
                    true,       // simulateBuild：与编辑器模拟模式口径一致
                    false,      // useAssetDependencyDB：走实时依赖，避免用到过期缓存
                    false);     // enableAssetPathValidation
            }
            catch (Exception e)
            {
                Fail("收集器执行失败（配置本身有错）：" + e.Message);
                return;
            }

            Dictionary<string, string> collected = new Dictionary<string, string>(StringComparer.Ordinal);
            for (int i = 0; i < result.CollectAssets.Count; i++)
            {
                CollectAssetInfo info = result.CollectAssets[i];
                string path = info.AssetInfo.AssetPath;
                if (collected.ContainsKey(path) == false)
                {
                    collected.Add(path, info.BundleName);
                }
            }

            Info(string.Format("收集器共收进 {0} 个资源。", collected.Count));

            // 覆盖度：ResTable 里登记的资源，是否真的落在收集范围内
            int uncovered = 0;
            List<string> uncoveredSamples = new List<string>();
            foreach (KeyValuePair<string, ResAddress> kv in ResTable.All)
            {
                string path = kv.Value.EditorPath;
                if (string.IsNullOrEmpty(path) || collected.ContainsKey(path))
                {
                    continue;
                }

                uncovered++;
                if (uncoveredSamples.Count < 10)
                {
                    uncoveredSamples.Add(kv.Key + " → " + path);
                }
            }

            if (uncovered == 0)
            {
                Success("收集覆盖：ResTable 里登记的每个资源都在收集范围内。");
            }
            else
            {
                Fail(string.Format("收集覆盖：{0} 条登记资源**不在任何收集目录内**（运行时必然定位失败）：", uncovered));
                for (int i = 0; i < uncoveredSamples.Count; i++)
                {
                    Info("  " + uncoveredSamples[i]);
                }
            }

            // 反查：收集了但没登记的资源（走降级分包）
            List<string> unregistered = FTBundlePackRule.GetUnregisteredReport();
            if (unregistered.Count == 0)
            {
                Success("未登记资源：没有。ResTable 覆盖了全部被收集的资源。");
            }
            else
            {
                Warn(string.Format(
                    "未登记资源：{0} 个（已自动降级分包，不是错误；但请确认它们确实该被打进包里）：",
                    unregistered.Count));
                int show = Mathf.Min(unregistered.Count, 20);
                for (int i = 0; i < show; i++)
                {
                    Info("  " + unregistered[i]);
                }
                if (unregistered.Count > show)
                {
                    Info(string.Format("  …（还有 {0} 条，完整清单见控制台）", unregistered.Count - show));
                }

                Debug.Log("[YooAsset] 未登记但被收集的资源清单：\n" + string.Join("\n", unregistered.ToArray()));
            }
        }

        // ==================================================================
        // ③ 构建
        // ==================================================================

        private void BuildSimulate()
        {
            ClearLog();

            if (HasSettingAsset() == false)
            {
                Fail("还没有收集器配置资产，请先执行「生成 / 修复收集器配置」。");
                return;
            }

            FTBundlePackRule.ResetReport();

            try
            {
                PackageBuildParameters param = new PackageBuildParameters(PackageName);
                param.BuildPipelineName = EBuildPipeline.EditorSimulateBuildPipeline.ToString();
                param.BuildBundleType = (int)EBundleType.VirtualAssetBundle;

                PackageBuildResult result = BundleSimulateBuilder.SimulateBuild(param);

                Success("模拟清单构建成功。");
                Info("输出目录：" + result.PackageRootDirectory);
                Info("编辑器 Play 时，适配器会**重新构建一次**并把该目录交给文件系统（见 YooAssetResLoader.CreateInitOptions）。");
            }
            catch (Exception e)
            {
                Fail("模拟清单构建失败：" + e.Message);
                Debug.LogException(e);
            }
        }

        private void BuildRealBundles()
        {
            ClearLog();

            if (HasSettingAsset() == false)
            {
                Fail("还没有收集器配置资产，请先执行「生成 / 修复收集器配置」。");
                return;
            }

            if (string.IsNullOrEmpty(_version))
            {
                Fail("资源包版本不能为空。");
                return;
            }

            FTBundlePackRule.ResetReport();

            try
            {
                ScriptableBuildParameters param = new ScriptableBuildParameters();
                param.BuildOutputRoot = BundleBuilderHelper.GetDefaultBuildOutputRoot();
                param.BundledFileRoot = BundleBuilderHelper.GetStreamingAssetsRoot();
                param.BuildPipeline = EBuildPipeline.ScriptableBuildPipeline.ToString();
                param.BuildBundleType = (int)EBundleType.AssetBundle;
                param.BuildTarget = EditorUserBuildSettings.activeBuildTarget;
                param.PackageName = PackageName;
                param.PackageVersion = _version;
                param.FileNameStyle = EFileNameStyle.HashName;
                // 首包：把资源包拷进 StreamingAssets/yoo（离线模式直接读它）。
                // ClearAndCopyAll 清的是 yoo 子目录，不会碰到旧的 StreamingAssets/AssetBundles。
                param.BundledCopyOption = EBundledCopyOption.ClearAndCopyAll;
                param.BundledCopyParams = string.Empty;
                param.UseAssetDependencyDB = true;
                param.VerifyBuildingResult = true;
                // 未被收集目录覆盖的依赖（例如 Assets/TextMesh Pro 下的材质）单独进 share_ 包，
                // 而不是被静默丢弃或被复制进每个引用它的包。
                param.EnableSharePackRule = true;
                param.SingleReferencedPackAlone = true;
                param.CompressOption = ECompressOption.LZ4;
                param.BuiltinShadersBundleName = DefaultBundlePackRule.ShadersBundleName;
                param.MonoScriptsBundleName = DefaultBundlePackRule.MonosBundleName;

                // ⚠️ 同名版本重建必须先清掉输出目录，否则 TaskPrepare_SBP 会直接抛
                //    `[ErrorCode115] Package output directory exists: '…/FreeTower/1.0.0'`。
                //    这不是本工程特有的用法问题 —— YooAsset 官方构建窗口的"清空构建缓存"
                //    开关默认也是关的，在它那里点第二次构建同样会报这个错。
                param.ClearBuildCacheFiles = _fullRebuild;
                if (_fullRebuild)
                {
                    Warn("「彻底重建」已开启：会清空整个包裹根目录（含编辑器模拟清单 Simulate）" +
                         "与 Unity SBP 构建缓存，本次构建会比较慢。Simulate 会在下次进 Play 时自动重建。");
                }
                else
                {
                    string cleanError;
                    if (CleanPackageOutputDirectory(param, out cleanError) == false)
                    {
                        Fail("清理上一次的同版本输出目录失败：" + cleanError);
                        return;
                    }
                }

                ScriptableBuildPipeline pipeline = new ScriptableBuildPipeline();
                BuildResult result = pipeline.Run(param, true);

                if (result.Success)
                {
                    Success("真实资源包构建成功。");
                    Info("输出目录：" + result.OutputPackageDirectory);
                    Info("随包目录：" + param.BundledFileRoot + "（离线模式读这里）");
                }
                else
                {
                    Fail(string.Format("构建失败于任务 {0}：{1}", result.FailedTask, result.ErrorInfo));
                }
            }
            catch (Exception e)
            {
                Fail("真实资源包构建异常：" + e.Message);
                Debug.LogException(e);
            }
        }

        /// <summary>
        /// 构建前置清理：只删掉本次要写入的那个"包裹输出目录"。
        ///
        /// 【为什么必须做】YooAsset 的 `TaskPrepare.PrepareOutputDirectory` 一旦发现
        /// 包裹输出目录已存在，就直接抛 `[ErrorCode115] Package output directory exists` ——
        /// 也就是说**同一个版本号构建第二次必然失败**。
        /// （这不是本工程特有的用法问题：YooAsset 官方构建窗口里的"清空构建缓存"开关
        ///   默认也是关的，在那儿点第二次构建同样会报这个错。）
        ///
        /// 【为什么默认只精确删这一个目录】`ClearBuildCacheFiles = true` 会连
        /// `{BuildOutputRoot}/{平台}/{包裹}` 整个根目录一起删，其中包含 `Simulate` ——
        /// 而 `Simulate` 正是编辑器模拟模式当前正在用的清单，向导第 ④ 步「回读校验」
        /// 就在同一次编辑器会话里跑。只删本次版本目录的另一个好处是 Unity 的
        /// SBP 构建缓存保持温热，重建更快。要彻底重建时用界面上的「彻底重建」开关。
        /// </summary>
        private bool CleanPackageOutputDirectory(ScriptableBuildParameters param, out string error)
        {
            error = string.Empty;
            string dir = param.GetPackageOutputDirectory();
            try
            {
                if (Directory.Exists(dir) == false)
                {
                    return true;
                }

                // 输出根目录在工程根下的 Bundles/，不在 Assets/ 下，因此不需要 AssetDatabase.Refresh()。
                Directory.Delete(dir, true);
                Info("已清掉上一次的同版本输出目录：" + dir);
                return true;
            }
            catch (Exception e)
            {
                error = e.Message;
                return false;
            }
        }

        // ==================================================================
        // ④ 回读校验
        // ==================================================================

        private void RunRuntimeProbe()
        {
            ClearLog();

            if (HasSettingAsset() == false)
            {
                Fail("还没有收集器配置资产，请先执行「生成 / 修复收集器配置」。");
                return;
            }

            IResLoader loader = ResLoader.Instance;
            if (loader == null)
            {
                Fail("拿不到加载器实例。");
                return;
            }

            Info("加载器实现：" + loader.GetType().Name);
            Info("说明：编辑器下适配器走「模拟模式」并**当场构建模拟清单**，因此本步骤同时也验证了构建链路。");

            try
            {
                loader.Init(null);
            }
            catch (Exception e)
            {
                Fail("初始化抛异常：" + e.Message);
                Debug.LogException(e);
                return;
            }

            if (loader.IsReady == false)
            {
                Fail("加载器初始化未成功（IsReady=false）。常见原因：");
                Info("  · 收集器配置为空 → 先执行「生成 / 修复收集器配置」");
                Info("  · 收集目录里没有可用资源 → 先看「静态校验」的报告");
                Info("  · 上一行日志里的 YooAsset 具体报错");
                return;
            }

            Success("初始化完成。开始逐个解析 ResTable 逻辑名 ……");

            List<string> names = new List<string>(ResTable.AllKeys);

            // 分批：几百个资源一次性加载会长时间卡住编辑器，分批 + 进度条更好受。
            List<string> failed = new List<string>();
            int ok = 0;
            const int BatchSize = 40;

            for (int i = 0; i < names.Count; i++)
            {
                if (i % BatchSize == 0)
                {
                    bool canceled = EditorUtility.DisplayCancelableProgressBar(
                        "YooAsset 回读校验",
                        string.Format("{0} / {1}", i, names.Count),
                        (float)i / Mathf.Max(1, names.Count));
                    if (canceled)
                    {
                        Warn("已被手动中断。");
                        break;
                    }
                }

                string logical = names[i];
                UnityEngine.Object asset = null;
                try
                {
                    asset = loader.Load<UnityEngine.Object>(logical);
                }
                catch (Exception e)
                {
                    failed.Add(logical + "（抛异常：" + e.GetType().Name + "）");
                    continue;
                }

                if (asset == null)
                {
                    failed.Add(logical);
                }
                else
                {
                    ok++;
                    // 校验完立刻释放，避免把整工程的资源都攥在手里
                    loader.Release(logical);
                }
            }

            EditorUtility.ClearProgressBar();

            if (failed.Count == 0)
            {
                Success(string.Format("回读校验通过：{0} 个逻辑名全部解析成功。", ok));
                Info("这表示「ResTable → 打包规则 → YooAsset 定位地址 → 实际资源」整条链是通的。");
            }
            else
            {
                Fail(string.Format("回读校验：{0} 个成功 / {1} 个失败。失败清单：", ok, failed.Count));
                int show = Mathf.Min(failed.Count, 30);
                for (int i = 0; i < show; i++)
                {
                    Info("  " + failed[i]);
                }
                if (failed.Count > show)
                {
                    Info(string.Format("  …（还有 {0} 条）", failed.Count - show));
                }
                Debug.LogWarning("[YooAsset] 回读校验失败清单：\n" + string.Join("\n", failed.ToArray()));
            }

            Info("当前引用计数快照：\n" + loader.DumpDebugInfo());
        }
    }
}
#endif
