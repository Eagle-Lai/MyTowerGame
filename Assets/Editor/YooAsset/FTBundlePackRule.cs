#if USE_YOOASSET
using System;
using System.Collections.Generic;
using YooAsset.Editor;

namespace FTProject.EditorTools
{
    /// <summary>
    /// 塔防分包规则：**按 ResTable 决定每个资源进哪个资源包**。
    ///
    /// 【为什么不能直接用 YooAsset 的目录规则】
    ///   本工程的分包是**跨目录按玩法语义**分的，任何"按目录"的规则都复现不出来：
    ///     - `enemy_rats` 同时含 `Assets/Prefabs/Enemy/Enemy_Rat.prefab`
    ///       与 `Assets/_UIAssets/Monsters/Rats/Rat/Rat.png`（prefab 与图集分居两棵树）；
    ///     - `tower_normal` 同时含 `Assets/Prefabs/Tower/Normal/*` 与
    ///       `Assets/_UIAssets/Tower/Normal/*`。
    ///   而 ResTable 已经把"哪个资源属于哪个包"写死了（Bundle 字段），
    ///   所以这里直接读它 —— 保持"ResTable 是唯一寻址源"这条工程铁律，
    ///   与既有 `ABNameSetter` 用的是同一份数据，不会出现两套规则分叉。
    ///
    /// 【未登记资源怎么办】按三级降级，且**全部记入报告**（向导会打出来）：
    ///   ① 同目录已有登记资源 → 跟随它（图集、材质等依赖自然落进同一个包）
    ///   ② 向上找最近的"有登记资源的祖先目录" → 跟随它
    ///   ③ 都没有 → `misc_<顶层目录名>` 兜底
    ///   注意：ResTable 只登记"要主动加载"的资源，而 YooAsset 收集的是整个目录树，
    ///   所以①/②命中是常态（例如字体图集、怪物源预制体），③是真正的异常信号。
    ///
    /// ⚠️ 本类被 YooAsset 通过 `TypeCache.GetTypesDerivedFrom(IBundlePackRule)` 自动发现，
    ///    不需要注册；但**必须在收集器的"打包规则"列里选中它**（向导生成的配置已经选好）。
    /// </summary>
    [DisplayName("塔防：按 ResTable 分包（enemy_xxx / tower_normal …）")]
    public class FTBundlePackRule : IBundlePackRule
    {
        /// <summary>兜底包名前缀</summary>
        public const string FallbackPrefix = "misc_";

        /// <summary>资源路径 → 资源包名（来自 ResTable，精确匹配优先）</summary>
        private static Dictionary<string, string> s_byAssetPath;

        /// <summary>目录 → 资源包名（用于"跟随同目录已登记资源"）</summary>
        private static Dictionary<string, string> s_byDirectory;

        /// <summary>本次收集期间遇到的"ResTable 里没登记"的资源：资源路径 → 「去向 + 原因」</summary>
        private static readonly Dictionary<string, string> s_unregistered =
            new Dictionary<string, string>(StringComparer.Ordinal);

        // ==================================================================
        // 报告（向导读取）
        // ==================================================================

        /// <summary>清空未登记报告。每次校验/构建前调用一次。</summary>
        public static void ResetReport()
        {
            s_unregistered.Clear();
        }

        /// <summary>未登记资源条目数</summary>
        public static int UnregisteredCount
        {
            get { return s_unregistered.Count; }
        }

        /// <summary>未登记资源报告（按路径排序，便于比对）</summary>
        public static List<string> GetUnregisteredReport()
        {
            List<string> lines = new List<string>(s_unregistered.Count);
            foreach (KeyValuePair<string, string> kv in s_unregistered)
            {
                lines.Add(kv.Key + "  →  " + kv.Value);
            }
            lines.Sort(StringComparer.Ordinal);
            return lines;
        }

        // ==================================================================
        // IBundlePackRule
        // ==================================================================

        public BundlePackRuleResult GetPackRuleResult(BundlePackRuleData data)
        {
            string bundle = ResolveBundle(data.AssetPath);
            return new BundlePackRuleResult(bundle, DefaultBundlePackRule.AssetBundleFileExtension);
        }

        /// <summary>
        /// 给定资源路径，算出应该进哪个资源包。
        /// 公开是为了让接入向导能"离线复算一遍"并与 ResTable 比对（见静态校验）。
        /// </summary>
        public static string ResolveBundle(string assetPath)
        {
            EnsureIndex();

            string path = Normalize(assetPath);
            if (path.Length == 0)
            {
                return FallbackPrefix + "unknown";
            }

            string bundle;
            if (s_byAssetPath.TryGetValue(path, out bundle))
            {
                return bundle;
            }

            // ① / ② 跟随同目录、或最近的有登记资源的祖先目录
            string dir = GetDirectory(path);
            while (dir.Length > 0)
            {
                if (s_byDirectory.TryGetValue(dir, out bundle))
                {
                    Record(path, bundle, "跟随同树已登记资源所在包（" + dir + "）");
                    return bundle;
                }

                string parent = GetDirectory(dir);
                if (parent.Length == 0 || string.Equals(parent, dir, StringComparison.Ordinal))
                {
                    break;
                }
                dir = parent;
            }

            // ③ 兜底
            bundle = FallbackPrefix + Sanitize(TopFolder(path));
            Record(path, bundle, "无已登记资源可跟随，按顶层目录兜底");
            return bundle;
        }

        // ==================================================================
        // 索引
        // ==================================================================

        private static void EnsureIndex()
        {
            if (s_byAssetPath != null)
            {
                return;
            }

            s_byAssetPath = new Dictionary<string, string>(1024, StringComparer.Ordinal);
            s_byDirectory = new Dictionary<string, string>(512, StringComparer.Ordinal);

            foreach (KeyValuePair<string, ResAddress> kv in ResTable.All)
            {
                string path = Normalize(kv.Value.EditorPath);
                if (path.Length == 0 || string.IsNullOrEmpty(kv.Value.Bundle))
                {
                    continue;
                }

                // 同一个资源可能被多个逻辑名指向（如 Cell_Buildable 与 Cell_Ground 同文件），
                // 只要包名一致就无歧义；真出现不一致时保留先登记的，并在向导报告里体现不出来 ——
                // 这种情况属于 ResTable 配置错误，跑 verify 的"包名一致性"检查会报出来。
                if (s_byAssetPath.ContainsKey(path) == false)
                {
                    s_byAssetPath.Add(path, kv.Value.Bundle);
                }

                string dir = GetDirectory(path);
                if (dir.Length > 0 && s_byDirectory.ContainsKey(dir) == false)
                {
                    s_byDirectory.Add(dir, kv.Value.Bundle);
                }
            }
        }

        private static void Record(string assetPath, string bundle, string reason)
        {
            if (s_unregistered.ContainsKey(assetPath))
            {
                return;
            }
            s_unregistered.Add(assetPath, bundle + "（" + reason + "）");
        }

        // ==================================================================
        // 路径小工具
        // ==================================================================

        private static string Normalize(string path)
        {
            if (string.IsNullOrEmpty(path))
            {
                return string.Empty;
            }
            return path.Replace('\\', '/');
        }

        private static string GetDirectory(string assetPath)
        {
            int idx = assetPath.LastIndexOf('/');
            return idx <= 0 ? string.Empty : assetPath.Substring(0, idx);
        }

        private static string TopFolder(string assetPath)
        {
            const string prefix = "Assets/";
            if (assetPath.StartsWith(prefix, StringComparison.Ordinal))
            {
                string rest = assetPath.Substring(prefix.Length);
                int idx = rest.IndexOf('/');
                return idx < 0 ? "root" : rest.Substring(0, idx);
            }
            return "external";
        }

        /// <summary>包名只保留字母数字下划线并转小写（与 ResBundle 的命名规范一致）。</summary>
        private static string Sanitize(string name)
        {
            if (string.IsNullOrEmpty(name))
            {
                return "unknown";
            }

            char[] chars = name.ToCharArray();
            for (int i = 0; i < chars.Length; i++)
            {
                char c = chars[i];
                bool ok = (c >= 'a' && c <= 'z')
                          || (c >= 'A' && c <= 'Z')
                          || (c >= '0' && c <= '9')
                          || c == '_';
                if (ok == false)
                {
                    chars[i] = '_';
                }
            }

            string result = new string(chars).Trim('_').ToLowerInvariant();
            return result.Length == 0 ? "unknown" : result;
        }
    }
}
#endif
