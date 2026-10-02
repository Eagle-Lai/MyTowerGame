using System.Collections.Generic;
using System.IO;
using System.Text;
using SimpleJSON;
using UnityEditor;
using UnityEngine;

namespace FTProject.EditorTools
{
    /// <summary>
    /// 可视化关卡地图编辑器（M3-7）。
    ///
    /// 【为什么需要它】棋盘是 16×9 的字符网格，手写 "S..............." 这种字符串
    /// 既看不出形状、也极易把某一行写多/少一个字符 —— 而**行长不匹配是静默失败**：
    /// LevelMapConfig.GetCell 越界会按空地兜底，于是地图"看起来能跑"，实际边界被吃掉。
    ///
    /// 【工作流】本窗口只负责"画"和"校验"，**不直接写 xlsx** ——
    /// 工程里能在编辑器侧写 Excel 的库（ClosedXML）只存在于 Luban 工具目录，
    /// 引进来会污染运行时/编辑器程序集。所以：
    ///     窗口画图 → 导出到 .workbuddy/levelmap_export.json → 跑 Python 脚本写回 xlsx → Luban 导出
    ///   "一键写入"按钮会替你跑那条 Python 命令（若 Python 路径不对，按提示改一下即可）。
    ///
    /// 菜单：Tools ▸ 塔防 ▸ 地图编辑器（可视化刷格子）
    /// </summary>
    public class LevelMapEditorWindow : EditorWindow
    {
        private const int MaxCols = 26;
        private const int MaxRows = 14;
        private const float CellPx = 34f;

        private const string ExportRelPath = ".workbuddy/levelmap_export.json";
        private const string PythonPrefKey = "FTProject.LevelMapEditor.PythonPath";

        /// <summary>可绘制的字符与含义（顺序即工具栏顺序）</summary>
        private static readonly char[] Palette = { '.', '#', 'X', 'P', 'S', 'E' };
        private static readonly string[] PaletteTip =
        {
            "空地（可建造、可通行）", "障碍（不可通行、不可建造）", "空洞（同障碍，语义上表示坑）",
            "装饰地砖（可通行、不可建造）", "起点（每张图必须恰好一个）", "终点（每张图必须恰好一个）"
        };

        private int _levelId = 1;
        private int _cols = 16;
        private int _rows = 9;
        private char[,] _cells;
        private char _brush = '.';
        private string _status = "";
        private bool _statusIsError;
        private string _desc = "";
        private Vector2 _scroll;

        [MenuItem("Tools/塔防/地图编辑器（可视化刷格子）", false, 20)]
        public static void Open()
        {
            LevelMapEditorWindow w = GetWindow<LevelMapEditorWindow>("关卡地图编辑器");
            w.minSize = new Vector2(760f, 560f);
            w.LoadLevel(w._levelId);
        }

        private void OnGUI()
        {
            DrawToolbar();
            EditorGUILayout.Space();
            DrawGrid();
            EditorGUILayout.Space();
            DrawActions();
            EditorGUILayout.Space();
            DrawStatus();
        }

        // ------------------------------------------------------------------
        // 工具栏
        // ------------------------------------------------------------------

        private void DrawToolbar()
        {
            EditorGUILayout.BeginHorizontal(EditorStyles.toolbar);

            GUILayout.Label("关卡", EditorStyles.label, GUILayout.Width(34f));
            int newLevel = EditorGUILayout.IntField(_levelId, GUILayout.Width(40f));
            if (newLevel != _levelId && newLevel >= 1)
            {
                _levelId = newLevel;
                LoadLevel(_levelId);
            }

            GUILayout.Label("列", EditorStyles.label, GUILayout.Width(24f));
            int nc = EditorGUILayout.IntField(_cols, GUILayout.Width(36f));
            GUILayout.Label("行", EditorStyles.label, GUILayout.Width(24f));
            int nr = EditorGUILayout.IntField(_rows, GUILayout.Width(36f));
            if ((nc != _cols || nr != _rows) && nc > 0 && nr > 0 && nc <= MaxCols && nr <= MaxRows)
            {
                Resize(nc, nr);
            }

            if (GUILayout.Button("重新载入本关", EditorStyles.toolbarButton, GUILayout.Width(100f)))
            {
                LoadLevel(_levelId);
            }
            if (GUILayout.Button("清空为全空地", EditorStyles.toolbarButton, GUILayout.Width(100f)))
            {
                Fill('.');
                _status = "已清空（记得补上 S 与 E）";
                _statusIsError = false;
            }

            GUILayout.FlexibleSpace();
            GUILayout.EndHorizontal();

            // 画笔
            EditorGUILayout.BeginHorizontal();
            GUILayout.Label("画笔：", GUILayout.Width(44f));
            for (int i = 0; i < Palette.Length; i++)
            {
                bool on = _brush == Palette[i];
                Color old = GUI.backgroundColor;
                if (on) GUI.backgroundColor = new Color(0.5f, 0.9f, 0.5f);
                if (GUILayout.Button(new GUIContent(Palette[i].ToString(), PaletteTip[i]),
                        EditorStyles.miniButton, GUILayout.Width(40f)))
                {
                    _brush = Palette[i];
                }
                GUI.backgroundColor = old;
            }
            GUILayout.FlexibleSpace();
            EditorGUILayout.EndHorizontal();

            _desc = EditorGUILayout.TextField("备注", _desc);
        }

        // ------------------------------------------------------------------
        // 网格
        // ------------------------------------------------------------------

        private void DrawGrid()
        {
            _scroll = EditorGUILayout.BeginScrollView(_scroll, GUILayout.ExpandHeight(true));
            Rect area = GUILayoutUtility.GetRect(_cols * CellPx + 4f, _rows * CellPx + 4f, GUILayout.ExpandWidth(false));

            if (Event.current.type == EventType.Repaint)
            {
                for (int r = 0; r < _rows; r++)
                {
                    for (int c = 0; c < _cols; c++)
                    {
                        Rect cell = new Rect(area.x + c * CellPx, area.y + r * CellPx, CellPx - 1f, CellPx - 1f);
                        EditorGUI.DrawRect(cell, ColorOf(_cells[r, c]));
                        GUI.Label(cell, _cells[r, c].ToString(), CenteredLabel());
                    }
                }
            }

            HandlePaint(area);
            EditorGUILayout.EndScrollView();
        }

        private static GUIStyle _centered;

        private static GUIStyle CenteredLabel()
        {
            if (_centered == null)
            {
                _centered = new GUIStyle(EditorStyles.boldLabel);
                _centered.alignment = TextAnchor.MiddleCenter;
                _centered.normal.textColor = Color.black;
            }
            return _centered;
        }

        private static Color ColorOf(char ch)
        {
            switch (ch)
            {
                case '#': return new Color(0.28f, 0.28f, 0.33f);
                case 'X': return new Color(0.15f, 0.15f, 0.18f);
                case 'P': return new Color(0.55f, 0.52f, 0.42f);
                case 'S': return new Color(0.35f, 0.85f, 0.42f);
                case 'E': return new Color(0.90f, 0.38f, 0.38f);
                default: return new Color(0.86f, 0.86f, 0.86f);
            }
        }

        /// <summary>
        /// 点/拖上色。
        /// 【要点】按住鼠标拖拽要能连续刷 —— 所以用 MouseDown/MouseDrag 两个事件，
        /// 只看 MouseDown 的话必须一格一格点，16×9 的图会点到手酸。
        /// </summary>
        private void HandlePaint(Rect area)
        {
            Event e = Event.current;
            if (e == null)
            {
                return;
            }
            if (e.type != EventType.MouseDown && e.type != EventType.MouseDrag)
            {
                return;
            }
            if (!area.Contains(e.mousePosition))
            {
                return;
            }

            int c = Mathf.FloorToInt((e.mousePosition.x - area.x) / CellPx);
            int r = Mathf.FloorToInt((e.mousePosition.y - area.y) / CellPx);
            if (r < 0 || r >= _rows || c < 0 || c >= _cols)
            {
                return;
            }

            if (e.button == 1)
            {
                _cells[r, c] = '.';        // 右键 = 擦除，比"切回空地把笔"快得多
            }
            else
            {
                // S / E 全图唯一：先清掉旧的，避免出现两个起点导致 A* 取到哪个都不确定
                if (_brush == 'S' || _brush == 'E')
                {
                    for (int rr = 0; rr < _rows; rr++)
                    {
                        for (int cc = 0; cc < _cols; cc++)
                        {
                            if (_cells[rr, cc] == _brush)
                            {
                                _cells[rr, cc] = '.';
                            }
                        }
                    }
                }
                _cells[r, c] = _brush;
            }

            e.Use();
            Repaint();
        }

        // ------------------------------------------------------------------
        // 操作
        // ------------------------------------------------------------------

        private void DrawActions()
        {
            EditorGUILayout.BeginHorizontal();
            if (GUILayout.Button("校验连通性", GUILayout.Height(26f)))
            {
                Validate();
            }
            if (GUILayout.Button("导出到文件", GUILayout.Height(26f)))
            {
                ExportToFile();
            }
            if (GUILayout.Button("复制 cells 字符串", GUILayout.Height(26f)))
            {
                EditorGUIUtility.systemCopyBuffer = BuildCellsString();
                _status = "cells 字符串已复制到剪贴板（可直接粘进 Excel 的 cells 列）";
                _statusIsError = false;
            }
            if (GUILayout.Button("一键写入 xlsx", GUILayout.Height(26f)))
            {
                ExportToFile();
                RunApplier();
            }
            EditorGUILayout.EndHorizontal();
        }

        private void DrawStatus()
        {
            if (string.IsNullOrEmpty(_status))
            {
                return;
            }
            MessageType t = _statusIsError ? MessageType.Error : MessageType.Info;
            EditorGUILayout.HelpBox(_status, t);
        }

        // ------------------------------------------------------------------
        // 数据
        // ------------------------------------------------------------------

        private void Resize(int cols, int rows)
        {
            char[,] next = new char[rows, cols];
            for (int r = 0; r < rows; r++)
            {
                for (int c = 0; c < cols; c++)
                {
                    next[r, c] = (r < _rows && c < _cols) ? _cells[r, c] : '.';
                }
            }
            _cols = cols;
            _rows = rows;
            _cells = next;
        }

        private void Fill(char ch)
        {
            for (int r = 0; r < _rows; r++)
            {
                for (int c = 0; c < _cols; c++)
                {
                    _cells[r, c] = ch;
                }
            }
        }

        private void LoadLevel(int levelId)
        {
            _cells = new char[_rows, _cols];
            Fill('.');

            string path = Path.Combine(Directory.GetCurrentDirectory(), "Assets/ConfigJson/tblevelmap.json");
            if (!File.Exists(path))
            {
                _status = "找不到 Assets/ConfigJson/tblevelmap.json —— 请先跑一次 Luban 导出";
                _statusIsError = true;
                return;
            }

            try
            {
                JSONNode root = JSONNode.Parse(File.ReadAllText(path, Encoding.UTF8));
                if (root == null || !root.IsArray)
                {
                    _status = "tblevelmap.json 不是数组，格式异常";
                    _statusIsError = true;
                    return;
                }
                for (int i = 0; i < root.Count; i++)
                {
                    JSONNode row = root[i];
                    if (row == null || row["id"] == null || row["id"].AsInt != levelId)
                    {
                        continue;
                    }
                    int cols = row["cols"] != null ? row["cols"].AsInt : 16;
                    int rows = row["rows"] != null ? row["rows"].AsInt : 9;
                    _cols = Mathf.Clamp(cols, 1, MaxCols);
                    _rows = Mathf.Clamp(rows, 1, MaxRows);
                    _desc = row["desc"] != null ? row["desc"].Value : "";

                    JSONNode cells = row["cells"];
                    _cells = new char[_rows, _cols];
                    Fill('.');
                    if (cells != null && cells.IsArray)
                    {
                        for (int r = 0; r < _rows && r < cells.Count; r++)
                        {
                            string line = cells[r].Value;
                            for (int c = 0; c < _cols && line != null && c < line.Length; c++)
                            {
                                _cells[r, c] = line[c];
                            }
                        }
                    }
                    _status = string.Format("已载入关卡 {0}（{1}×{2}）", levelId, _cols, _rows);
                    _statusIsError = false;
                    return;
                }
                _status = string.Format("tblevelmap.json 里没有 id={0} 的棋盘（新图请先设好行列再画）", levelId);
                _statusIsError = false;
            }
            catch (System.Exception ex)
            {
                _status = "解析 tblevelmap.json 失败：" + ex.Message;
                _statusIsError = true;
            }
        }

        private string[] BuildCellLines()
        {
            string[] lines = new string[_rows];
            StringBuilder sb = new StringBuilder(_cols);
            for (int r = 0; r < _rows; r++)
            {
                sb.Length = 0;
                for (int c = 0; c < _cols; c++)
                {
                    sb.Append(_cells[r, c]);
                }
                lines[r] = sb.ToString();
            }
            return lines;
        }

        /// <summary>xlsx 里 cells 列的格式：(list#sep=|),string —— 用 | 分隔每一行</summary>
        private string BuildCellsString()
        {
            return string.Join("|", BuildCellLines());
        }

        // ------------------------------------------------------------------
        // 校验
        // ------------------------------------------------------------------

        private void Validate()
        {
            List<string> problems = new List<string>();

            int sCount = 0, eCount = 0;
            for (int r = 0; r < _rows; r++)
            {
                for (int c = 0; c < _cols; c++)
                {
                    if (_cells[r, c] == 'S') sCount++;
                    else if (_cells[r, c] == 'E') eCount++;
                }
            }
            if (sCount != 1) problems.Add(string.Format("起点 S 有 {0} 个（必须恰好 1 个）", sCount));
            if (eCount != 1) problems.Add(string.Format("终点 E 有 {0} 个（必须恰好 1 个）", eCount));

            int buildable = 0;
            for (int r = 0; r < _rows; r++)
            {
                for (int c = 0; c < _cols; c++)
                {
                    if (_cells[r, c] == '.') buildable++;
                }
            }

            int pathLen = -1;
            if (sCount == 1 && eCount == 1)
            {
                pathLen = BfsPathLength();
                if (pathLen < 0)
                {
                    problems.Add("S 到 E 不可达 —— 障碍把路封死了（这是最致命的一条，进关会直接卡住）");
                }
            }

            if (problems.Count > 0)
            {
                _status = "校验未通过：\n  · " + string.Join("\n  · ", problems.ToArray());
                _statusIsError = true;
                return;
            }

            // 难度参考：与 balance_sim.py 的口径一致（可建造格越少越难）
            _status = string.Format(
                "校验通过。\n  棋盘 {0}×{1}，可建造格 {2}，最短路径 {3} 格\n" +
                "  参考：可建造格越少越难（当前 8 张图是 142→70 递减）",
                _cols, _rows, buildable, pathLen);
            _statusIsError = false;
        }

        /// <summary>BFS 求最短路径长度（障碍与空洞不可通行）。不可达返回 -1。</summary>
        private int BfsPathLength()
        {
            int sr = -1, sc = -1, er = -1, ec = -1;
            for (int r = 0; r < _rows; r++)
            {
                for (int c = 0; c < _cols; c++)
                {
                    if (_cells[r, c] == 'S') { sr = r; sc = c; }
                    else if (_cells[r, c] == 'E') { er = r; ec = c; }
                }
            }
            if (sr < 0 || er < 0)
            {
                return -1;
            }

            int[,] dist = new int[_rows, _cols];
            for (int r = 0; r < _rows; r++)
            {
                for (int c = 0; c < _cols; c++)
                {
                    dist[r, c] = -1;
                }
            }
            Queue<int> q = new Queue<int>();
            dist[sr, sc] = 0;
            q.Enqueue(sr * _cols + sc);
            int[] dr = { 1, -1, 0, 0 };
            int[] dc = { 0, 0, 1, -1 };
            while (q.Count > 0)
            {
                int cur = q.Dequeue();
                int r = cur / _cols;
                int c = cur % _cols;
                if (r == er && c == ec)
                {
                    return dist[r, c];
                }
                for (int k = 0; k < 4; k++)
                {
                    int nr = r + dr[k];
                    int nc = c + dc[k];
                    if (nr < 0 || nr >= _rows || nc < 0 || nc >= _cols)
                    {
                        continue;
                    }
                    if (dist[nr, nc] >= 0)
                    {
                        continue;
                    }
                    char ch = _cells[nr, nc];
                    if (ch == '#' || ch == 'X')
                    {
                        continue;
                    }
                    dist[nr, nc] = dist[r, c] + 1;
                    q.Enqueue(nr * _cols + nc);
                }
            }
            return -1;
        }

        // ------------------------------------------------------------------
        // 导出
        // ------------------------------------------------------------------

        private void ExportToFile()
        {
            try
            {
                string full = Path.Combine(Directory.GetCurrentDirectory(), ExportRelPath);
                Directory.CreateDirectory(Path.GetDirectoryName(full));

                StringBuilder sb = new StringBuilder();
                sb.Append("{\n");
                sb.Append("  \"levelId\": ").Append(_levelId).Append(",\n");
                sb.Append("  \"cols\": ").Append(_cols).Append(",\n");
                sb.Append("  \"rows\": ").Append(_rows).Append(",\n");
                sb.Append("  \"desc\": ").Append(JsonStr(_desc)).Append(",\n");
                sb.Append("  \"cells\": [");
                string[] lines = BuildCellLines();
                for (int i = 0; i < lines.Length; i++)
                {
                    if (i > 0) sb.Append(", ");
                    sb.Append(JsonStr(lines[i]));
                }
                sb.Append("]\n}\n");

                File.WriteAllText(full, sb.ToString(), new UTF8Encoding(false));
                _status = "已导出到 " + ExportRelPath + "\n  下一步：跑 .workbuddy/tools/apply_levelmap_export.py 写回 xlsx，再跑 Luban 导出";
                _statusIsError = false;
            }
            catch (System.Exception ex)
            {
                _status = "导出失败：" + ex.Message;
                _statusIsError = true;
            }
        }

        private static string JsonStr(string s)
        {
            if (s == null)
            {
                return "\"\"";
            }
            return "\"" + s.Replace("\\", "\\\\").Replace("\"", "\\\"") + "\"";
        }

        /// <summary>
        /// 调 Python 把导出文件写回 xlsx。
        /// 【为什么允许失败】Python 路径因机器而异，写死必然有人跑不通；
        /// 失败时给出明确的手工命令，用户复制粘贴即可，不至于卡住。
        /// </summary>
        private void RunApplier()
        {
            string python = EditorPrefs.GetString(PythonPrefKey, "python");
            string script = Path.Combine(Directory.GetCurrentDirectory(), ".workbuddy/tools/apply_levelmap_export.py");
            if (!File.Exists(script))
            {
                _status += "\n\n（找不到 " + script + "，请手工执行）";
                return;
            }
            try
            {
                System.Diagnostics.ProcessStartInfo psi = new System.Diagnostics.ProcessStartInfo();
                psi.FileName = python;
                psi.Arguments = "\"" + script + "\"";
                psi.WorkingDirectory = Directory.GetCurrentDirectory();
                psi.UseShellExecute = false;
                psi.RedirectStandardOutput = true;
                psi.RedirectStandardError = true;
                psi.CreateNoWindow = true;
                System.Diagnostics.Process p = System.Diagnostics.Process.Start(psi);
                string outp = p.StandardOutput.ReadToEnd();
                string err = p.StandardError.ReadToEnd();
                p.WaitForExit();
                _status += "\n\nPython 输出：\n" + outp + (string.IsNullOrEmpty(err) ? "" : "\n[stderr] " + err);
                _statusIsError = p.ExitCode != 0;
                AssetDatabase.Refresh();
            }
            catch (System.Exception ex)
            {
                _status += "\n\n调用 Python 失败（" + ex.Message + "）。\n" +
                           "请手工执行： python .workbuddy/tools/apply_levelmap_export.py";
                _statusIsError = true;
            }
        }
    }
}
