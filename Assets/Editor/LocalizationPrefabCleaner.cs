using TMPro;
using UnityEditor;
using UnityEngine;

namespace FTProject.EditorTools
{
    /// <summary>
    /// 清理：把**运行时动态文本**节点上误挂的 <see cref="TextLocalizer"/> 移除。
    ///
    /// 【为什么单独一个菜单】批量挂载工具白名单外扩时，很容易把
    ///   "View 运行时会覆盖内容"的节点也挂上 —— 那会在切语言时把代码算好的
    ///   内容冲掉。本菜单按**节点名黑名单**兜底清理，幂等、可反复跑。
    /// </summary>
    public static class LocalizationPrefabCleaner
    {
        private static readonly string[] TargetPrefabs =
        {
            "Assets/Prefabs/UI/HudView.prefab",
            "Assets/Prefabs/UI/TipsView.prefab",
            "Assets/Prefabs/UI/TowerInfoView.prefab",
            "Assets/Prefabs/UI/SelectView.prefab",
            "Assets/Prefabs/UI/SelectLevelItem.prefab",
            "Assets/Prefabs/UI/PauseView.prefab",
            "Assets/Prefabs/UI/SettingView.prefab",
            "Assets/Prefabs/UI/LevelClearView.prefab",
            "Assets/Prefabs/UI/MainMenuView.prefab",
            "Assets/Prefabs/UI/LevelDetailView.prefab",
            "Assets/Prefabs/UI/SellConfirmView.prefab",
            "Assets/Prefabs/UI/ConfirmView.prefab",
            "Assets/Prefabs/UI/TowerCodexView.prefab",
            "Assets/Prefabs/UI/TowerCodexItem.prefab",
            // 游戏介绍弹窗（2026-10-14）
            "Assets/Prefabs/UI/GameIntroView.prefab",
            "Assets/HotUpdateUI/SplashView.prefab",
            "Assets/HotUpdateUI/LoadingView.prefab",
        };

        private static readonly System.Collections.Generic.HashSet<string> DynamicNames =
            new System.Collections.Generic.HashSet<string>
        {
            "GoldText", "HpText", "RoundText", "PriceText",
            "Title",
            "Stats", "StarDetail", "RecordTip", "LevelName", "BestStarText",
            "Info1", "Info2", "Info3", "Info4", "Info5", "Info6",
            "EnemyLabel", "Summary", "ClearText", "StarText", "Stars",
            "RefundValue", "TowerName", "WarnText", "BodyText",
            "TypeName", "Role", "DescText", "DpsRow", "RangeRow", "SpeedRow", "PriceRow",
            "PageText",
            "StatusText", "PercentText", "TipText", "PhaseText", "SizeText", "SpeedText",
            "DetailText", "FailText", "LoadingDots", "VolumeText",
        };

        [MenuItem("Tools/塔防/高级（单步重建）/清理误挂的多语言组件", false, 309)]
        public static void CleanFromMenu()
        {
            EditorUtil.Report report = new EditorUtil.Report();
            report.Head("清理动态文本节点上误挂的 TextLocalizer");
            int removed = 0;
            for (int i = 0; i < TargetPrefabs.Length; i++)
            {
                removed += CleanOne(TargetPrefabs[i], report);
            }
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            report.Ok(string.Format("共移除 {0} 个误挂组件", removed));
            Debug.Log("[多语言清理] 完成：\n" + report.Text);
        }

        private static int CleanOne(string path, EditorUtil.Report report)
        {
            GameObject root = PrefabUtility.LoadPrefabContents(path);
            if (root == null)
            {
                return 0;
            }
            TextLocalizer[] all = root.GetComponentsInChildren<TextLocalizer>(true);
            int removed = 0;
            for (int i = 0; i < all.Length; i++)
            {
                TextLocalizer tl = all[i];
                if (tl == null)
                {
                    continue;
                }
                if (DynamicNames.Contains(tl.gameObject.name) || IsSymbolOnly(TMPTextOf(tl)))
                {
                    Object.DestroyImmediate(tl, true);
                    removed++;
                }
            }
            if (removed > 0)
            {
                PrefabUtility.SaveAsPrefabAsset(root, path);
                report.Ok(System.IO.Path.GetFileName(path) + "：移除 " + removed + " 个");
            }
            PrefabUtility.UnloadPrefabContents(root);
            return removed;
        }

        private static string TMPTextOf(TextLocalizer tl)
        {
            TextMeshProUGUI t = tl.GetComponent<TextMeshProUGUI>();
            return t != null ? t.text : null;
        }

        /// <summary>纯符号文本（箭头 &lt; &gt; 等）：语言无关，不该挂本地化。</summary>
        private static bool IsSymbolOnly(string s)
        {
            if (string.IsNullOrEmpty(s))
            {
                return true;
            }
            for (int i = 0; i < s.Length; i++)
            {
                if (char.IsLetter(s[i]))
                {
                    return false;
                }
            }
            return true;
        }
    }
}
