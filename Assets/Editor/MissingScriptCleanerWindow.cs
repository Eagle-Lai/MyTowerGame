//------------------------------------------------------------------------------
// 预制体 Missing Script 批量清理工具（可视化面板）
//
// 提供：拖拽选择文件夹、预览/执行切换、结果列表与一键定位。
//------------------------------------------------------------------------------
using System.Collections.Generic;
using System.Text;
using UnityEditor;
using UnityEngine;

namespace FTProject.EditorTools
{
    /// <summary>
    /// 清理工具面板：选择文件夹 → 扫描/清理 → 查看结果
    /// </summary>
    public class MissingScriptCleanerWindow : EditorWindow
    {
        /// <summary>待处理的目标（文件夹或预制体）</summary>
        private UnityEngine.Object _target;

        /// <summary>true = 只扫描不修改</summary>
        private bool _dryRun = true;

        /// <summary>是否输出每个文件的详细日志</summary>
        private bool _verbose = false;

        /// <summary>结果列表是否只展示有改动/有错误的条目</summary>
        private bool _onlyChanged = true;

        private Vector2 _scroll;

        // GUIStyle 必须在 OnGUI 期间按需创建，避免在静态构造 / 序列化阶段触发 Unity 警告
        private GUIStyle _titleStyle;
        private GUIStyle _itemStyle;

        /// <summary>打开面板（若已存在则聚焦）</summary>
        public static void ShowWindow()
        {
            MissingScriptCleanerWindow win = GetWindow<MissingScriptCleanerWindow>("Missing Script 清理");
            win.minSize = new Vector2(560f, 480f);
            win.Show();
        }

        private void OnEnable()
        {
            // 打开面板时自动带入 Project 窗口的选中项
            PickFromSelection();
        }

        private void EnsureStyles()
        {
            if (_titleStyle == null)
            {
                _titleStyle = new GUIStyle(EditorStyles.boldLabel);
                _titleStyle.fontSize = 13;
                _titleStyle.margin = new RectOffset(0, 0, 6, 4);
            }
            if (_itemStyle == null)
            {
                _itemStyle = new GUIStyle(EditorStyles.label);
                _itemStyle.richText = true;
                _itemStyle.wordWrap = false;
                _itemStyle.padding = new RectOffset(4, 4, 2, 2);
            }
        }

        private void OnGUI()
        {
            EnsureStyles();

            DrawHeader();
            EditorGUILayout.Space();

            DrawTargetField();
            EditorGUILayout.Space();

            DrawOptions();
            EditorGUILayout.Space();

            DrawActionButtons();
            EditorGUILayout.Space();

            DrawReport();
        }

        #region 界面分区

        private void DrawHeader()
        {
            EditorGUILayout.LabelField("预制体 Missing Script 批量清理", _titleStyle);
            EditorGUILayout.HelpBox(
                "选择目标文件夹后，工具会递归遍历其中全部 .prefab（含子文件夹、子物体与未激活物体），"
                + "移除残留的 Missing Script 组件。\n"
                + "建议先点“预览扫描”确认影响范围，再执行清理；该操作会写回资源文件且无法 Ctrl+Z 撤销，请先提交版本控制。",
                MessageType.Info);
        }

        private void DrawTargetField()
        {
            EditorGUILayout.LabelField("目标文件夹 / 预制体", EditorStyles.boldLabel);

            EditorGUI.BeginChangeCheck();
            _target = EditorGUILayout.ObjectField(_target, typeof(UnityEngine.Object), false);
            if (EditorGUI.EndChangeCheck())
            {
                ValidateTarget();
            }

            using (new EditorGUILayout.HorizontalScope())
            {
                if (GUILayout.Button("使用 Project 窗口选中项", GUILayout.Height(22f)))
                {
                    PickFromSelection();
                }
                if (GUILayout.Button("清空目标", GUILayout.Height(22f), GUILayout.Width(90f)))
                {
                    _target = null;
                }
            }

            string path = _target != null ? AssetDatabase.GetAssetPath(_target) : null;
            if (_target == null)
            {
                EditorGUILayout.HelpBox("请拖入一个文件夹（或预制体），也可以先在 Project 窗口中选中后点击上方按钮。",
                    MessageType.Warning);
            }
            else if (!AssetDatabase.IsValidFolder(path) && !path.EndsWith(".prefab"))
            {
                EditorGUILayout.HelpBox("目标必须是文件夹或 .prefab 文件。", MessageType.Error);
            }
            else
            {
                EditorGUILayout.LabelField("解析路径", path, EditorStyles.miniLabel);
            }
        }

        private void DrawOptions()
        {
            EditorGUILayout.LabelField("执行选项", EditorStyles.boldLabel);
            _dryRun = EditorGUILayout.ToggleLeft("预览模式（只扫描统计，不修改任何文件）", _dryRun);
            _verbose = EditorGUILayout.ToggleLeft("输出详细日志（包含无变化的预制体）", _verbose);
            _onlyChanged = EditorGUILayout.ToggleLeft("结果列表仅显示有改动 / 有错误的条目", _onlyChanged);
        }

        private void DrawActionButtons()
        {
            bool valid = IsTargetValid();

            using (new EditorGUI.DisabledScope(!valid))
            {
                using (new EditorGUILayout.HorizontalScope())
                {
                    Color old = GUI.backgroundColor;
                    GUI.backgroundColor = _dryRun ? new Color(0.75f, 0.9f, 1f) : new Color(1f, 0.85f, 0.75f);

                    string label = _dryRun ? "预览扫描" : "开始清理";
                    if (GUILayout.Button(label, GUILayout.Height(30f)))
                    {
                        List<string> paths = new List<string> { AssetDatabase.GetAssetPath(_target) };
                        MissingScriptCleaner.RunAndReport(paths, _dryRun, _verbose, false);
                    }

                    GUI.backgroundColor = old;

                    if (GUILayout.Button(_dryRun ? "预览并弹窗确认" : "弹窗确认后清理",
                            GUILayout.Height(30f), GUILayout.Width(150f)))
                    {
                        List<string> paths = new List<string> { AssetDatabase.GetAssetPath(_target) };
                        MissingScriptCleaner.RunWithConfirm(paths, _dryRun, true);
                    }
                }
            }
        }

        private void DrawReport()
        {
            CleanReport report = MissingScriptCleaner.LastReport;
            if (report == null)
            {
                return;
            }

            EditorGUILayout.Space();
            EditorGUILayout.LabelField("执行结果", _titleStyle);

            using (new EditorGUILayout.VerticalScope(EditorStyles.helpBox))
            {
                EditorGUILayout.LabelField(string.Format(
                    "扫描 {0} 个 · 发现 Missing Script {1} 个 · 受影响 {2} 个 · 跳过 {3} 个 · 失败 {4} 个 · 耗时 {5:F0}ms",
                    report.Scanned, report.RemovedTotal, report.Modified, report.Skipped, report.Failed, report.ElapsedMs));

                if (report.DryRun)
                {
                    EditorGUILayout.LabelField("（预览模式：以上为预估结果，未修改任何文件）", EditorStyles.miniLabel);
                }
                if (report.Canceled)
                {
                    EditorGUILayout.LabelField("（任务被手动取消，未处理项保持原样）", EditorStyles.miniLabel);
                }
            }

            using (new EditorGUILayout.HorizontalScope())
            {
                if (GUILayout.Button("复制报告到剪贴板", GUILayout.Height(22f)))
                {
                    EditorGUIUtility.systemCopyBuffer = BuildReportText(report);
                    Debug.Log("[MissingScript清理] 报告已复制到剪贴板。");
                }
                if (GUILayout.Button("清空结果", GUILayout.Height(22f), GUILayout.Width(90f)))
                {
                    MissingScriptCleaner.LastReport = null;
                }
            }

            EditorGUILayout.Space();
            _scroll = EditorGUILayout.BeginScrollView(_scroll, GUILayout.MinHeight(180f));

            int shown = 0;
            foreach (CleanResult item in report.Details)
            {
                if (_onlyChanged && !item.HasChange)
                {
                    continue;
                }
                shown++;
                DrawResultRow(item);
            }

            if (shown == 0)
            {
                EditorGUILayout.LabelField(_onlyChanged ? "没有需要关注的条目，全部干净。" : "无明细数据。",
                    EditorStyles.miniLabel);
            }

            EditorGUILayout.EndScrollView();
        }

        private void DrawResultRow(CleanResult item)
        {
            using (new EditorGUILayout.HorizontalScope(EditorStyles.helpBox))
            {
                string tag;
                if (!string.IsNullOrEmpty(item.Error))
                {
                    tag = "<color=#c0392b>[失败]</color>";
                }
                else if (item.IsSkipped)
                {
                    tag = "<color=#7f8c8d>[跳过]</color>";
                }
                else
                {
                    tag = "<color=#d35400>[清理]</color>";
                }

                string info = item.IsSkipped
                    ? string.Format("{0} {1}  <color=#7f8c8d>({2})</color>", tag, item.AssetPath, item.SkipReason)
                    : string.Format("{0} 移除 {1} 个  {2}", tag, item.RemovedCount, item.AssetPath);

                EditorGUILayout.LabelField(info, _itemStyle);

                if (GUILayout.Button("定位", GUILayout.Width(52f)))
                {
                    GameObject asset = AssetDatabase.LoadAssetAtPath<GameObject>(item.AssetPath);
                    if (asset != null)
                    {
                        // 先改选中，再 Ping，否则选中动作会清掉高亮
                        Selection.activeObject = asset;
                        EditorGUIUtility.PingObject(asset);
                    }
                    else
                    {
                        Debug.LogWarning(string.Format("[MissingScript清理] 无法加载资源（可能已被移动或删除）：{0}",
                            item.AssetPath));
                    }
                }
            }
        }

        #endregion

        #region 辅助方法

        private bool IsTargetValid()
        {
            if (_target == null)
            {
                return false;
            }
            string path = AssetDatabase.GetAssetPath(_target);
            return AssetDatabase.IsValidFolder(path) || path.EndsWith(".prefab");
        }

        private void ValidateTarget()
        {
            if (_target != null)
            {
                string path = AssetDatabase.GetAssetPath(_target);
                if (!AssetDatabase.IsValidFolder(path) && !path.EndsWith(".prefab"))
                {
                    EditorUtility.DisplayDialog("目标无效", "请选择文件夹或 .prefab 文件。", "知道了");
                    _target = null;
                }
            }
        }

        private void PickFromSelection()
        {
            UnityEngine.Object active = Selection.activeObject;
            if (active == null)
            {
                return;
            }
            string path = AssetDatabase.GetAssetPath(active);
            if (AssetDatabase.IsValidFolder(path) || path.EndsWith(".prefab"))
            {
                _target = active;
                Repaint();
            }
        }

        private static string BuildReportText(CleanReport report)
        {
            StringBuilder sb = new StringBuilder();
            sb.AppendLine("===== 预制体 Missing Script 清理报告 =====");
            sb.AppendLine(report.Describe());
            sb.AppendLine();
            sb.AppendLine("----- 明细 -----");
            foreach (CleanResult item in report.Details)
            {
                if (item.IsSkipped)
                {
                    sb.AppendLine(string.Format("[跳过] {0} （{1}）", item.AssetPath, item.SkipReason));
                }
                else if (!string.IsNullOrEmpty(item.Error))
                {
                    sb.AppendLine(string.Format("[失败] {0} ：{1}", item.AssetPath, item.Error));
                }
                else if (item.RemovedCount > 0)
                {
                    sb.AppendLine(string.Format("[清理] 移除 {0} 个 · {1}", item.RemovedCount, item.AssetPath));
                }
            }
            return sb.ToString();
        }

        #endregion
    }
}
