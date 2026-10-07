using TMPro;
using UnityEditor;
using UnityEngine;
using UnityEngine.UI;

namespace FTProject.EditorTools
{
    /// <summary>
    /// 一次性迁移工具：把 UI 预制体里的 **UGUI Text 组件就地替换为 TextMeshProUGUI**。
    ///
    /// 【为什么需要它，而不是直接跑 UIPrefabBuilder 重建】
    ///   UIPrefabBuilder 是「DeleteAsset + 重建」——重建会抹掉人在编辑器里手工做的一切
    ///   （历史上 HudView 手工加过塔按钮、手工调过坐标）。
    ///   本工具是**就地替换组件**：不动节点树、不动 RectTransform、不动按钮与事件，
    ///   只把每个 `Text` 换成 `TextMeshProUGUI`，于是手工成果 100% 保留。
    ///
    /// 【为什么 YAML 手改不行、必须在编辑器里跑】
    ///   Text 与 TextMeshProUGUI 的序列化字段完全不同：
    ///   前者引用 Font + 一堆 horizontalOverflow 字段，后者引用 TMP_FontAsset + 材质；
    ///   且换了组件类型后 m_Script guid 也要换。手工拼 YAML 极易漏字段导致
    ///   "组件丢失 / 字不显示 / prefab 报错"。走 Unity API（AddComponent / DestroyImmediate +
    ///   CopySerializableValues）才是可靠路径。
    ///
    /// 【转移的字段】文本内容、字号、颜色、对齐、是否 raycast —— 视觉尽量等价；
    ///   UGUI 的 Outline 描边组件无法 1:1 转移（TMP 描边是材质属性），
    ///   这里统一给迁移后的文本挂上项目的中文字体描边材质（若存在）。
    ///
    /// 【幂等】已是 TMP 的节点会跳过；重复执行安全。
    ///
    /// 菜单：Tools ▸ 塔防 ▸ 高级（单步重建） ▸ 把 UI 预制体的 Text 迁移为 TextMeshPro
    /// </summary>
    public static class UiTmpMigrator
    {
        /// <summary>需要迁移的 UI 预制体（与 UIPrefabBuilder 生成的六个一致）</summary>
        private static readonly string[] TargetPrefabs =
        {
            "Assets/Prefabs/UI/HudView.prefab",
            "Assets/Prefabs/UI/TipsView.prefab",
            "Assets/Prefabs/UI/TowerInfoView.prefab",
            "Assets/Prefabs/UI/SelectView.prefab",
            "Assets/Prefabs/UI/PauseView.prefab",
            "Assets/Prefabs/UI/SettingView.prefab",
        };

        /// <summary>统一的中文字体描边材质（由 UIPrefabBuilder 生成；不存在则跳过描边）</summary>
        private const string OutlineMaterialPath = "Assets/Font/SiYuanSongTi SDF - Outline.mat";

        [MenuItem("Tools/塔防/高级（单步重建）/把 UI 预制体的 Text 迁移为 TextMeshPro", false, 306)]
        public static void MigrateFromMenu()
        {
            EditorUtil.Report report = new EditorUtil.Report();
            int files = MigrateAll(report);
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();

            Debug.Log("[TMP 迁移] 结果：\n" + report.Text);
            EditorUtility.DisplayDialog("Text → TextMeshPro 迁移",
                string.Format("{0}\n\n处理 {1} 个预制体\n\n{2}",
                    report.Errors > 0 ? "有错误，请查看 Console" : "完成", files, report.Text), "好");
        }

        /// <summary>供向导调用（不弹窗）。返回处理的预制体数量。</summary>
        public static int MigrateAll(EditorUtil.Report report)
        {
            report.Head("Text → TextMeshPro 迁移（就地替换组件）");
            int count = 0;
            for (int i = 0; i < TargetPrefabs.Length; i++)
            {
                if (MigrateOne(TargetPrefabs[i], report))
                {
                    count++;
                }
            }
            return count;
        }

        private static bool MigrateOne(string path, EditorUtil.Report report)
        {
            GameObject root = PrefabUtility.LoadPrefabContents(path);
            if (root == null)
            {
                report.Skip(path + " 不存在，跳过");
                return false;
            }

            TMP_FontAsset font = EditorUtil.GetDefaultTmpFont();
            Material outlineMat = AssetDatabase.LoadAssetAtPath<Material>(OutlineMaterialPath);

            // 收集全部 Text（含隐藏节点：模板按钮通常是 SetActive(false) 的）
            Text[] texts = root.GetComponentsInChildren<Text>(true);
            if (texts.Length == 0)
            {
                PrefabUtility.UnloadPrefabContents(root);
                report.Skip(System.IO.Path.GetFileName(path) + " 没有 UGUI Text，跳过");
                return false;
            }

            int converted = 0;
            for (int i = 0; i < texts.Length; i++)
            {
                Text old = texts[i];
                if (old == null)
                {
                    continue;
                }
                if (ConvertOne(old, font, outlineMat))
                {
                    converted++;
                }
            }

            PrefabUtility.SaveAsPrefabAsset(root, path);
            PrefabUtility.UnloadPrefabContents(root);

            report.Ok(string.Format("{0}：迁移 {1} 个文本组件为 TextMeshProUGUI",
                System.IO.Path.GetFileName(path), converted));
            return true;
        }

        /// <summary>
        /// 把单个 UGUI Text 就地替换为 TextMeshProUGUI。
        /// 【为什么先读旧值再删】删完 old 后访问它会抛异常，所有拷贝必须在 DestoryImmediate 之前完成。
        /// </summary>
        private static bool ConvertOne(Text old, TMP_FontAsset font, Material outlineMat)
        {
            GameObject go = old.gameObject;

            // ---- 先读出旧组件的所有要保留的属性 ----
            string content = old.text;
            int fontSize = old.fontSize;
            Color color = old.color;
            TextAnchor anchor = old.alignment;
            bool raycast = old.raycastTarget;
            FontStyle style = old.fontStyle;

            // ---- 删掉旧的 Text 与它可能带的 Outline（TMP 不支持 UGUI Outline）----
            Object.DestroyImmediate(old, true);
            Outline outline = go.GetComponent<Outline>();
            if (outline != null)
            {
                Object.DestroyImmediate(outline, true);
            }

            // ---- 挂 TMP 组件 ----
            TextMeshProUGUI t = go.GetComponent<TextMeshProUGUI>();
            if (t == null)
            {
                t = go.AddComponent<TextMeshProUGUI>();
            }
            if (font != null)
            {
                t.font = font;
            }
            if (outlineMat != null)
            {
                t.fontSharedMaterial = outlineMat;
            }
            t.text = content;
            t.fontSize = fontSize;
            t.color = color;
            t.alignment = ToTmpAlignment(anchor);
            t.raycastTarget = raycast;
            t.enableWordWrapping = false;
            t.overflowMode = TextOverflowModes.Overflow;

            // 粗体/斜体在 TMP 里是 fontStyles（位标志）；这里显式取或再赋值，
            // 不用 |=（枚举属性上的复合赋值可读性差，也易被误认为原地修改）。
            FontStyles fs = t.fontStyle;
            if ((style & FontStyle.Bold) != 0)
            {
                fs |= FontStyles.Bold;
            }
            if ((style & FontStyle.Italic) != 0)
            {
                fs |= FontStyles.Italic;
            }
            t.fontStyle = fs;

            return true;
        }

        private static TextAlignmentOptions ToTmpAlignment(TextAnchor a)
        {
            switch (a)
            {
                case TextAnchor.UpperLeft:    return TextAlignmentOptions.TopLeft;
                case TextAnchor.UpperCenter:  return TextAlignmentOptions.Top;
                case TextAnchor.UpperRight:   return TextAlignmentOptions.TopRight;
                case TextAnchor.MiddleLeft:   return TextAlignmentOptions.Left;
                case TextAnchor.MiddleCenter: return TextAlignmentOptions.Center;
                case TextAnchor.MiddleRight:  return TextAlignmentOptions.Right;
                case TextAnchor.LowerLeft:    return TextAlignmentOptions.BottomLeft;
                case TextAnchor.LowerCenter:  return TextAlignmentOptions.Bottom;
                case TextAnchor.LowerRight:   return TextAlignmentOptions.BottomRight;
                default:                      return TextAlignmentOptions.Center;
            }
        }
    }
}
