using UnityEditor;
using UnityEngine;

namespace FTProject.EditorTools
{
    /// <summary>
    /// 按 ResTable 给资源自动打 AssetBundle 标记。
    ///
    /// 【为什么必须自动打标】
    ///   逻辑名 → (包名, 包内资产名, 编辑器路径) 这条映射只有一份数据源（ResTable）。
    ///   如果打标靠人手在 Inspector 里填，迟早会和 ResTable 分叉，
    ///   症状是"编辑器下一切正常，打包后某个资源变成白色/丢失" —— 这是 AB 项目最难查的一类问题。
    ///
    /// 菜单：
    ///   Tools ▸ 塔防 ▸ 4. 按 ResTable 打 AssetBundle 标记
    ///   Tools ▸ 塔防 ▸ 高级（单步重建） ▸ 清除 ResTable 范围内的 AssetBundle 标记
    ///
    /// 【M-5 改动】原来 8c 会"清除工程内所有资源的标记"，范围过宽 ——
    ///   一旦有第三方/插件资源也被打了标记，就会被误清，且无法逐条核对。
    ///   现在改为**只清 ResTable 登记的那些路径**，范围明确、可复核。
    /// </summary>
    public static class ABNameSetter
    {
        [MenuItem("Tools/塔防/4. 按 ResTable 打 AssetBundle 标记", false, 104)]
        public static void ApplyFromMenu()
        {
            EditorUtil.Report report = new EditorUtil.Report();
            Apply(report);
            AssetDatabase.Refresh();
            Debug.Log("[M0] AssetBundle 打标结果：\n" + report.Text);
            EditorUtility.DisplayDialog("AssetBundle 打标",
                string.Format("{0}\n\n{1}",
                    report.Errors > 0 ? "有错误，请查看 Console" : "完成", report.Text), "好");
        }

        /// <summary>供向导与打包脚本调用</summary>
        public static void Apply(EditorUtil.Report report)
        {
            report.Head("按 ResTable 打 AssetBundle 标记");

            int applied = 0;
            int unchanged = 0;
            int missing = 0;

            AssetDatabase.StartAssetEditing();
            try
            {
                foreach (System.Collections.Generic.KeyValuePair<string, ResAddress> kv in ResTable.All)
                {
                    string logicalName = kv.Key;
                    ResAddress addr = kv.Value;
                    if (!addr.IsValid)
                    {
                        continue;
                    }

                    AssetImporter importer = AssetImporter.GetAtPath(addr.EditorPath);
                    if (importer == null)
                    {
                        missing++;
                        report.Error(string.Format(
                            "资源不存在：{0}\n      逻辑名「{1}」\n      " +
                            "请检查 ResTable 的 EditorPath，或先执行对应的生成脚本" +
                            "（配置表要先跑 Luban/gen_code_json.bat）",
                            addr.EditorPath, logicalName));
                        continue;
                    }

                    if (importer.assetBundleName == addr.Bundle)
                    {
                        unchanged++;
                        continue;
                    }
                    importer.assetBundleName = addr.Bundle;
                    applied++;
                }
            }
            finally
            {
                AssetDatabase.StopAssetEditing();
                AssetDatabase.Refresh();
            }

            if (applied > 0)
            {
                report.Ok(string.Format("新打标 {0} 个资源", applied));
            }
            if (unchanged > 0)
            {
                report.Ok(string.Format("{0} 个资源标记已正确，无需改动", unchanged));
            }
            if (missing == 0)
            {
                report.Ok("ResTable 中登记的资源全部存在");
            }

            // 汇总每个包收了哪些资源，方便核对分包是否符合预期
            for (int i = 0; i < ResBundle.All.Length; i++)
            {
                string bundle = ResBundle.All[i];
                System.Collections.Generic.List<string> keys = ResTable.GetKeysByBundle(bundle);
                report.Ok(string.Format("包 {0,-14} 共 {1} 个资源", bundle, keys.Count));
            }
        }

        [MenuItem("Tools/塔防/高级（单步重建）/清除 ResTable 范围内的 AssetBundle 标记", false, 310)]
        public static void ClearAll()
        {
            if (!EditorUtility.DisplayDialog("清除 AssetBundle 标记",
                    "将清除 **ResTable 登记范围内**资源的 AssetBundle 标记" +
                    "（不再清全工程，避免误伤插件资源）。\n\n" +
                    "清除后必须重新执行「8a. 打标记」才能打包。",
                    "确认清除", "取消"))
            {
                return;
            }

            // ★ 只遍历 ResTable 登记的路径，逐条清除
            int cleared = 0;
            int scanned = 0;
            AssetDatabase.StartAssetEditing();
            try
            {
                foreach (System.Collections.Generic.KeyValuePair<string, ResAddress> kv in ResTable.All)
                {
                    ResAddress addr = kv.Value;
                    if (!addr.IsValid)
                    {
                        continue;
                    }
                    scanned++;
                    AssetImporter importer = AssetImporter.GetAtPath(addr.EditorPath);
                    if (importer != null && !string.IsNullOrEmpty(importer.assetBundleName))
                    {
                        importer.assetBundleName = string.Empty;
                        importer.assetBundleVariant = string.Empty;
                        cleared++;
                    }
                }
            }
            finally
            {
                AssetDatabase.StopAssetEditing();
                AssetDatabase.Refresh();
            }

            Debug.Log(string.Format("[M0] 已扫描 ResTable 内 {0} 条，清除 {1} 个资源的 AssetBundle 标记",
                scanned, cleared));
            EditorUtility.DisplayDialog("清除完成",
                string.Format("已扫描 {0} 条，清除 {1} 个资源。", scanned, cleared), "好");
        }
    }
}
