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
    /// 【一键写入的完整链路】点一次「一键写入 xlsx」按钮，按顺序做完这 5 步，中途失败即停：
    ///     ① 页面数据自检（行长 / S 与 E 各一个 / S→E 可达）—— 不合格绝不落盘
    ///     ② 读页面数据 → 导出 .workbuddy/levelmap_export.json
    ///     ③ 调 Python 脚本把 json 写回 Luban/Config/Datas/LevelMap.xlsx（自动备份原表）
    ///     ④ 跑 Luban 重导，生成 Assets/ConfigJson/tblevelmap.json
    ///     ⑤ 刷新资源库 → 从重导后的 json 回读本关，逐格比对"画进去的"和"读回来的"
    ///   第 ⑤ 步是这套流程的价值所在：它把"写表成功"升级成"往返一致"，
    ///   否则 Luban 因字段/类型问题静默丢数据时，你只会看到一份没生效的地图。
    ///
    /// 【为什么写 xlsx 要绕一趟外部 Python】
    /// 工程里能在编辑器侧读写 Excel 的库（ClosedXML）只存在于 Luban 工具目录，
    /// 引进来会污染运行时/编辑器程序集。所以分工是"编辑器画 + 校验，Python 落盘"。
    /// Python 解释器必须有 openpyxl；窗口顶部的「Python」栏可手填，也会自动探测并记住。
    ///
    /// 菜单：Tools ▸ 塔防 ▸ 地图编辑器（可视化刷格子）
    /// </summary>
    public class LevelMapEditorWindow : EditorWindow
    {
        private const int MaxCols = 26;
        private const int MaxRows = 14;
        private const float CellPx = 34f;

        /// <summary>页面数据导出的中转文件（相对工程根）</summary>
        private const string ExportRelPath = ".workbuddy/levelmap_export.json";
        /// <summary>把中转文件写回 xlsx 的 Python 脚本</summary>
        private const string ApplierRelPath = ".workbuddy/tools/apply_levelmap_export.py";
        /// <summary>Luban 重导后的产物，也是本窗口加载棋盘的唯一数据源</summary>
        private const string LocalJsonRelPath = "Assets/ConfigJson/tblevelmap.json";
        /// <summary>记住 Python 解释器的 EditorPrefs 键</summary>
        private const string PythonPrefKey = "FTProject.LevelMapEditor.PythonPath";

        /// <summary>
        /// 探测解释器的超时。
        /// 【为什么不给大】探测是同步的、会冻住编辑器，而且最多要试 8 个候选；
        /// 正常一次 `import openpyxl` 远不到 1 秒，8 秒已经是"这解释器坏了"的量级，
        /// 给 30 秒只会让最坏情况从"等一会儿"变成"以为编辑器死了"。
        /// </summary>
        private const int ProbeTimeoutMs = 8000;
        /// <summary>写表（纯本地读写 xlsx，正常 1~3 秒）</summary>
        private const int ApplierTimeoutMs = 60000;

        /// <summary>工程内虚拟环境优先（相对工程根）</summary>
        private static readonly string[] PythonRelCandidates =
        {
            ".venv/Scripts/python.exe",
            "Tools/.venv/Scripts/python.exe",
            ".venv/bin/python",
            "Tools/.venv/bin/python",
        };

        /// <summary>PATH 上的候选，按顺序试</summary>
        private static readonly string[] PythonPathCandidates = { "python", "python3", "py" };

        /// <summary>
        /// 本机已知可用（已装 openpyxl）的解释器兜底。
        /// 【为什么要留这个】openpyxl 不是标准库 —— PATH 上的 python 很可能没装它，
        /// 探测全失败时这一条能让"一键写入"在开发机上开箱可用。
        /// 换机器只需在窗口顶部改一次，之后会自动记住（EditorPrefs）。
        /// </summary>
        private static readonly string[] PythonAbsFallback =
        {
            "C:/Users/78296/.workbuddy/binaries/python/envs/default/Scripts/python.exe",
        };

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
        private string _pythonPath = "";
        private Vector2 _scroll;
        private Vector2 _statusScroll;

        /// <summary>逐步执行日志（用 ASCII 标记，避免 HelpBox 字体缺字形变豆腐块）</summary>
        private readonly List<string> _log = new List<string>();
        private bool _logHasError;

        private void OnEnable()
        {
            _pythonPath = EditorPrefs.GetString(PythonPrefKey, "");
            EnsureCells();
        }

        [MenuItem("Tools/塔防/地图编辑器（可视化刷格子）", false, 20)]
        public static void Open()
        {
            LevelMapEditorWindow w = GetWindow<LevelMapEditorWindow>("关卡地图编辑器");
            w.minSize = new Vector2(760f, 560f);
            w.LoadLevel(w._levelId);
        }

        private void OnGUI()
        {
            EnsureCells();
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
                SetStatus("已清空（记得补上 S 与 E）", false);
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

            DrawPythonRow();
        }

        /// <summary>
        /// Python 解释器行。
        /// 手填的值会立刻落到 EditorPrefs，"一键写入"下次直接用，不再重复探测。
        /// </summary>
        private void DrawPythonRow()
        {
            EditorGUILayout.BeginHorizontal();
            GUILayout.Label("Python", EditorStyles.label, GUILayout.Width(44f));

            string typed = EditorGUILayout.TextField(_pythonPath);
            if (typed != _pythonPath)
            {
                _pythonPath = typed == null ? "" : typed.Trim();
                EditorPrefs.SetString(PythonPrefKey, _pythonPath);
            }

            if (GUILayout.Button("自动探测", EditorStyles.miniButton, GUILayout.Width(70f)))
            {
                string py, note;
                if (ResolvePython(out py, out note))
                {
                    _pythonPath = py;
                    EditorPrefs.SetString(PythonPrefKey, py);
                    SetStatus("Python 解释器已就绪：" + py + (string.IsNullOrEmpty(note) ? "" : "（" + note + "）"), false);
                }
                else
                {
                    SetStatus("没有找到装了 openpyxl 的 Python。\n" +
                              "  请在上面填解释器的完整路径，或执行： <python> -m pip install openpyxl\n" +
                              "  （写 xlsx 需要 openpyxl，标准库不带）", true);
                }
            }

            if (GUILayout.Button("清空", EditorStyles.miniButton, GUILayout.Width(44f)))
            {
                _pythonPath = "";
                EditorPrefs.DeleteKey(PythonPrefKey);
                SetStatus("已清空记录的解释器，下次点「自动探测」或「一键写入」时重新查找", false);
            }
            GUILayout.EndHorizontal();
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
                ValidateAndReport();
            }
            if (GUILayout.Button("导出到文件", GUILayout.Height(26f)))
            {
                ExportAndReport();
            }
            if (GUILayout.Button("复制 cells 字符串", GUILayout.Height(26f)))
            {
                EditorGUIUtility.systemCopyBuffer = BuildCellsString();
                SetStatus("cells 字符串已复制到剪贴板（可直接粘进 Excel 的 cells 列）", false);
            }

            // 主操作：一次点完"写表 + 重导 + 回读"
            Color old = GUI.backgroundColor;
            GUI.backgroundColor = new Color(0.55f, 0.85f, 0.55f);
            if (GUILayout.Button("一键写入 xlsx（写表 + 重导 + 回读）", GUILayout.Height(26f)))
            {
                OneClickWrite();
            }
            GUI.backgroundColor = old;
            EditorGUILayout.EndHorizontal();
        }

        private void DrawStatus()
        {
            if (string.IsNullOrEmpty(_status))
            {
                return;
            }
            MessageType t = _statusIsError ? MessageType.Error : MessageType.Info;
            _statusScroll = EditorGUILayout.BeginScrollView(_statusScroll, GUILayout.MaxHeight(170f));
            EditorGUILayout.HelpBox(_status, t);
            EditorGUILayout.EndScrollView();
        }

        private void SetStatus(string msg, bool isError)
        {
            _status = msg;
            _statusIsError = isError;
            Repaint();
        }

        // ------------------------------------------------------------------
        // ★ 一键写入：读页面 → 写 xlsx → Luban 重导 → 回读校验
        // ------------------------------------------------------------------

        private void OneClickWrite()
        {
            LogReset();
            LogSkip("一键写入开始：读页面 → 写 xlsx → Luban 重导 → 回读");

            // ── ① 页面数据自检。不合格就直接停，一个文件都不碰
            int buildable, pathLen;
            List<string> problems = CollectProblems(out buildable, out pathLen);
            if (problems.Count > 0)
            {
                LogErr("页面数据未通过自检，已中止（没有改动任何文件）：");
                for (int i = 0; i < problems.Count; i++)
                {
                    _log.Add("      · " + problems[i]);
                }
                FlushStatus(true);
                return;
            }
            LogOk(string.Format("页面数据自检通过：{0}×{1}，可建造格 {2}，最短路径 {3} 格",
                _cols, _rows, buildable, pathLen));

            string root = Directory.GetCurrentDirectory();

            // ── ② 读页面数据 → 导出中转 json
            string exportErr;
            if (!WriteExportFile(out exportErr))
            {
                LogErr(exportErr);
                FlushStatus(true);
                return;
            }
            LogOk("已读取页面数据 → " + ExportRelPath);

            // ── ③ 定位 Python（必须有 openpyxl，否则写不了 xlsx）
            string python, pyNote;
            if (!ResolvePython(out python, out pyNote))
            {
                LogErr("找不到可用（装了 openpyxl）的 Python 解释器，已中止。");
                _log.Add("      · 在窗口顶部「Python」栏填入解释器完整路径，或执行：");
                _log.Add("        <python> -m pip install openpyxl");
                FlushStatus(true);
                return;
            }
            LogSkip("Python = " + python + (string.IsNullOrEmpty(pyNote) ? "" : "（" + pyNote + "）"));

            string script = Path.Combine(root, ApplierRelPath.Replace('/', Path.DirectorySeparatorChar));
            if (!File.Exists(script))
            {
                LogErr("找不到写表脚本：" + ApplierRelPath);
                FlushStatus(true);
                return;
            }

            // ── ④ 写回 LevelMap.xlsx
            // 【为什么先给初值】out 实参在 try/finally 里赋值时，确定赋值（CS0165）的判定
            //   依赖编译器对 finally 控制流的分析；这里显式初始化，把"能不能编过"变成确定的事。
            string outp = null, errp = null;
            int code = -3;
            EditorUtility.DisplayProgressBar("一键写入 xlsx", "正在写回 Luban/Config/Datas/LevelMap.xlsx …", 0.33f);
            try
            {
                code = RunProcess(python, "\"" + script + "\"", root, out outp, out errp, ApplierTimeoutMs);
            }
            finally
            {
                EditorUtility.ClearProgressBar();
            }

            if (!string.IsNullOrEmpty(outp)) UnityEngine.Debug.Log("[地图编辑器] 写表输出：\n" + outp.TrimEnd());
            if (!string.IsNullOrEmpty(errp)) UnityEngine.Debug.LogWarning("[地图编辑器] 写表 stderr：\n" + errp.TrimEnd());

            if (code != 0)
            {
                LogErr(string.Format("写表脚本返回非 0（exitCode={0}），LevelMap.xlsx 未改动。", code));
                AppendToolTail(outp, errp);
                FlushStatus(true);
                return;
            }
            LogOk("已写回 LevelMap.xlsx" + ExtractBackupHint(outp));
            LogSkip(ExtractSceneHint(outp));

            // ── ⑤ Luban 重导（这一步把 xlsx 变成运行时真正读的 tblevelmap.json）
            EditorUtil.Report luban = new EditorUtil.Report();
            bool lubanOk = LubanExporter.ExportInternal(luban);
            UnityEngine.Debug.Log("[地图编辑器] Luban：\n" + luban.Text);
            if (!lubanOk)
            {
                LogErr("Luban 重导失败 —— xlsx 已改好，但没有生成到 Assets/ConfigJson（细节见 Console）。");
                FlushStatus(true);
                return;
            }
            LogOk("已重新导入配置表（Assets/ConfigJson）");

            // ── ⑥ 回读校验：把"写表成功"升级成"往返一致"
            AssetDatabase.Refresh();
            string drawn = BuildCellsString();
            LoadLevel(_levelId, true);
            string back = BuildCellsString();
            if (back == drawn)
            {
                LogOk(string.Format("回读一致：重导后的 tblevelmap.json 与页面数据逐格相同（{0}×{1}）", _cols, _rows));
            }
            else
            {
                LogWarn("回读不一致 —— Luban 可能对 cells 做了规范化，请对照棋盘核对（页面已按重导结果重载）");
            }

            LogOk("一键写入完成。");
            FlushStatus(true);
        }

        /// <summary>从脚本输出里摘出备份目录，直接展示给用户，方便回滚。</summary>
        private static string ExtractBackupHint(string text)
        {
            string line = FindLine(text, "已备份到");
            return string.IsNullOrEmpty(line) ? "" : "（" + line + "）";
        }

        /// <summary>脚本提示"SceneInfo 里没登记这一关"时，把它抬到窗口上（否则只在 Console 里）。</summary>
        private static string ExtractSceneHint(string text)
        {
            string line = FindLine(text, "[提示]");
            return string.IsNullOrEmpty(line) ? "" : line;
        }

        private static string FindLine(string text, string keyword)
        {
            if (string.IsNullOrEmpty(text))
            {
                return null;
            }
            string[] lines = text.Replace("\r\n", "\n").Split('\n');
            for (int i = 0; i < lines.Length; i++)
            {
                string s = lines[i].Trim();
                if (s.Length > 0 && s.StartsWith(keyword))
                {
                    return s;
                }
            }
            return null;
        }

        /// <summary>失败时把工具输出的头几行贴进状态框，省得用户还要去翻 Console。</summary>
        private void AppendToolTail(string outp, string errp)
        {
            string t = errp == null ? "" : errp.Trim();
            if (t.Length == 0)
            {
                t = outp == null ? "" : outp.Trim();
            }
            if (t.Length == 0)
            {
                return;
            }
            string[] lines = t.Replace("\r\n", "\n").Split('\n');
            int n = Mathf.Min(lines.Length, 8);
            for (int i = 0; i < n; i++)
            {
                _log.Add("      | " + lines[i]);
            }
        }

        // ------------------------------------------------------------------
        // 数据
        // ------------------------------------------------------------------

        /// <summary>保证 _cells 存在且尺寸与 _cols/_rows 一致（第一次打开、或载入失败时兜底）。</summary>
        private void EnsureCells()
        {
            if (_cells == null || _cells.GetLength(0) != _rows || _cells.GetLength(1) != _cols)
            {
                Resize(_cols, _rows);
            }
        }

        private void Resize(int cols, int rows)
        {
            char[,] next = new char[rows, cols];
            for (int r = 0; r < rows; r++)
            {
                for (int c = 0; c < cols; c++)
                {
                    next[r, c] = (_cells != null && r < _rows && c < _cols) ? _cells[r, c] : '.';
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
            LoadLevel(levelId, false);
        }

        /// <summary>
        /// 从 Luban 产物 tblevelmap.json 载入本关棋盘。
        /// silent=true 时不写状态框（"一键写入"的回读校验要用，免得覆盖流程日志）。
        /// 【要点】棋盘数据全部读完之后才提交到字段，避免中途失败留下半截棋盘。
        /// </summary>
        private void LoadLevel(int levelId, bool silent)
        {
            string path = Path.Combine(Directory.GetCurrentDirectory(), LocalJsonRelPath.Replace('/', Path.DirectorySeparatorChar));
            if (!File.Exists(path))
            {
                if (!silent)
                {
                    SetStatus("找不到 " + LocalJsonRelPath + " —— 请先跑一次 Luban 导出", true);
                }
                return;
            }

            try
            {
                JSONNode root = JSONNode.Parse(File.ReadAllText(path, Encoding.UTF8));
                if (root == null || !root.IsArray)
                {
                    if (!silent) SetStatus(LocalJsonRelPath + " 不是数组，格式异常", true);
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
                    int useCols = Mathf.Clamp(cols, 1, MaxCols);
                    int useRows = Mathf.Clamp(rows, 1, MaxRows);

                    char[,] next = new char[useRows, useCols];
                    for (int r = 0; r < useRows; r++)
                    {
                        for (int c = 0; c < useCols; c++)
                        {
                            next[r, c] = '.';
                        }
                    }
                    JSONNode cells = row["cells"];
                    if (cells != null && cells.IsArray)
                    {
                        for (int r = 0; r < useRows && r < cells.Count; r++)
                        {
                            string line = cells[r].Value;
                            for (int c = 0; c < useCols && line != null && c < line.Length; c++)
                            {
                                next[r, c] = line[c];
                            }
                        }
                    }

                    _levelId = levelId;
                    _cols = useCols;
                    _rows = useRows;
                    _cells = next;
                    _desc = row["desc"] != null ? row["desc"].Value : "";

                    if (!silent)
                    {
                        SetStatus(string.Format("已载入关卡 {0}（{1}×{2}）", levelId, _cols, _rows), false);
                    }
                    return;
                }

                if (!silent)
                {
                    SetStatus(string.Format("tblevelmap.json 里没有 id={0} 的棋盘（新图请先设好行列再画）", levelId), false);
                }
            }
            catch (System.Exception ex)
            {
                if (!silent)
                {
                    SetStatus("解析 " + LocalJsonRelPath + " 失败：" + ex.Message, true);
                }
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

        private void ValidateAndReport()
        {
            LogReset();
            int buildable, pathLen;
            List<string> problems = CollectProblems(out buildable, out pathLen);

            if (problems.Count > 0)
            {
                LogErr("校验未通过：");
                for (int i = 0; i < problems.Count; i++)
                {
                    _log.Add("      · " + problems[i]);
                }
            }
            else
            {
                LogOk(string.Format("校验通过：棋盘 {0}×{1}，可建造格 {2}，最短路径 {3} 格",
                    _cols, _rows, buildable, pathLen));
                LogSkip("参考：可建造格越少越难（当前 8 张图是 142→70 递减）");
            }
            FlushStatus(false);
        }

        /// <summary>
        /// 收集页面数据的全部问题（顺带返回可建造格数与最短路径）。
        /// 【注意】这里和 Python 脚本里的自检是**同一套口径**：
        /// 窗口先挡一遍是为了"不合格就别白跑外部进程"，脚本再挡一遍是因为导出文件可能被手改。
        /// </summary>
        private List<string> CollectProblems(out int buildable, out int pathLen)
        {
            List<string> problems = new List<string>();
            int sCount = 0, eCount = 0;
            buildable = 0;

            for (int r = 0; r < _rows; r++)
            {
                for (int c = 0; c < _cols; c++)
                {
                    char ch = _cells[r, c];
                    if (ch == 'S') sCount++;
                    else if (ch == 'E') eCount++;
                    else if (ch == '.') buildable++;
                }
            }

            pathLen = -1;
            if (sCount != 1) problems.Add(string.Format("起点 S 有 {0} 个（必须恰好 1 个）", sCount));
            if (eCount != 1) problems.Add(string.Format("终点 E 有 {0} 个（必须恰好 1 个）", eCount));

            if (sCount == 1 && eCount == 1)
            {
                pathLen = BfsPathLength();
                if (pathLen < 0)
                {
                    problems.Add("S 到 E 不可达 —— 障碍把路封死了（这是最致命的一条，进关会直接卡住）");
                }
            }
            return problems;
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
        // 导出（读页面数据 → 中转 json）
        // ------------------------------------------------------------------

        private void ExportAndReport()
        {
            LogReset();
            string err;
            if (WriteExportFile(out err))
            {
                LogOk("已读取页面数据并导出到 " + ExportRelPath);
                LogSkip("接着点「一键写入 xlsx」即可自动写表 + 重导");
            }
            else
            {
                LogErr(err);
            }
            FlushStatus(false);
        }

        /// <summary>把页面当前关卡的数据写成中转 json（无 BOM，Python 侧按 UTF-8 读）。</summary>
        private bool WriteExportFile(out string error)
        {
            error = null;
            try
            {
                string full = Path.Combine(Directory.GetCurrentDirectory(),
                    ExportRelPath.Replace('/', Path.DirectorySeparatorChar));
                string dir = Path.GetDirectoryName(full);
                if (!string.IsNullOrEmpty(dir))
                {
                    Directory.CreateDirectory(dir);
                }

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
                return true;
            }
            catch (System.Exception ex)
            {
                error = "导出失败：" + ex.Message;
                return false;
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

        // ------------------------------------------------------------------
        // 外部进程
        // ------------------------------------------------------------------

        /// <summary>
        /// 定位一个"装了 openpyxl"的 Python 解释器，顺带把结果记进 EditorPrefs。
        /// 【为什么必须探测而不是直接用 "python"】openpyxl 是第三方库，
        /// PATH 上的 python 大概率没装；直接调用会在写表那一步才失败，
        /// 报出来的还是一串 import 错误，远不如在这里就明确挡住。
        /// 顺序：已记住 → 工程内 venv → PATH → 本机兜底。
        /// </summary>
        private bool ResolvePython(out string python, out string note)
        {
            note = "";
            string saved = EditorPrefs.GetString(PythonPrefKey, "");
            if (!string.IsNullOrEmpty(saved))
            {
                if (ProbePython(saved))
                {
                    python = saved;
                    note = "已记住";
                    return true;
                }
                note = "已记住的解释器不可用，重新探测";
            }

            string root = Directory.GetCurrentDirectory();

            for (int i = 0; i < PythonRelCandidates.Length; i++)
            {
                string p = Path.Combine(root, PythonRelCandidates[i].Replace('/', Path.DirectorySeparatorChar));
                if (!File.Exists(p))
                {
                    continue;
                }
                if (ProbePython(p))
                {
                    return AcceptPython(p, out python);
                }
            }

            for (int i = 0; i < PythonPathCandidates.Length; i++)
            {
                if (ProbePython(PythonPathCandidates[i]))
                {
                    note = "来自 PATH";
                    return AcceptPython(PythonPathCandidates[i], out python);
                }
            }

            for (int i = 0; i < PythonAbsFallback.Length; i++)
            {
                if (!File.Exists(PythonAbsFallback[i]))
                {
                    continue;
                }
                if (ProbePython(PythonAbsFallback[i]))
                {
                    note = "本机兜底";
                    return AcceptPython(PythonAbsFallback[i], out python);
                }
            }

            python = null;
            return false;
        }

        /// <summary>探测成功后统一落地：记住到 EditorPrefs + 回填窗口输入框。</summary>
        private bool AcceptPython(string exe, out string python)
        {
            python = exe;
            EditorPrefs.SetString(PythonPrefKey, exe);
            _pythonPath = exe;
            return true;
        }

        /// <summary>跑一次 `python -c "import openpyxl"`，退出码为 0 才算可用。</summary>
        private static bool ProbePython(string exe)
        {
            // py 是 Windows 启动器，必须显式指定大版本，否则可能落到 Python 2
            string args = (exe == "py") ? "-3 -c \"import openpyxl\"" : "-c \"import openpyxl\"";
            string outp, errp;
            int code = RunProcess(exe, args, Directory.GetCurrentDirectory(), out outp, out errp, ProbeTimeoutMs);
            return code == 0;
        }

        /// <summary>
        /// 同步跑一个进程并收回输出。
        /// 【要点】用 BeginOutputReadLine 异步读 —— 顺序 ReadToEnd 在"子进程边写边等"时会死锁。
        /// 【要点】两次 WaitForExit：第一次等退出，第二次等异步读取回调把剩余行刷完，
        /// 少第二次会丢结尾几行（恰恰是最关键的报错）。
        /// </summary>
        private static int RunProcess(string fileName, string arguments, string workDir,
                                      out string stdout, out string stderr, int timeoutMs)
        {
            stdout = "";
            stderr = "";
            StringBuilder so = new StringBuilder();
            StringBuilder se = new StringBuilder();

            System.Diagnostics.ProcessStartInfo psi = new System.Diagnostics.ProcessStartInfo();
            psi.FileName = fileName;
            psi.Arguments = arguments;
            psi.WorkingDirectory = workDir;
            psi.UseShellExecute = false;
            psi.RedirectStandardOutput = true;
            psi.RedirectStandardError = true;
            psi.CreateNoWindow = true;
            // Python 侧已把 stdout 切到 UTF-8，这里必须同样按 UTF-8 解，否则中文全乱码
            psi.StandardOutputEncoding = new UTF8Encoding(false);
            psi.StandardErrorEncoding = new UTF8Encoding(false);

            try
            {
                using (System.Diagnostics.Process p = System.Diagnostics.Process.Start(psi))
                {
                    p.OutputDataReceived += delegate(object s, System.Diagnostics.DataReceivedEventArgs e)
                    {
                        if (e.Data != null) { lock (so) { so.AppendLine(e.Data); } }
                    };
                    p.ErrorDataReceived += delegate(object s, System.Diagnostics.DataReceivedEventArgs e)
                    {
                        if (e.Data != null) { lock (se) { se.AppendLine(e.Data); } }
                    };
                    p.BeginOutputReadLine();
                    p.BeginErrorReadLine();

                    if (!p.WaitForExit(timeoutMs))
                    {
                        try { p.Kill(); }
                        catch (System.Exception) { }
                        stdout = so.ToString();
                        stderr = se.ToString() + "\n[超时] 超过 " + (timeoutMs / 1000) + " 秒未结束，已终止";
                        return -1;
                    }
                    p.WaitForExit();
                    stdout = so.ToString();
                    stderr = se.ToString();
                    return p.ExitCode;
                }
            }
            catch (System.Exception ex)
            {
                stdout = so.ToString();
                stderr = ex.Message;
                return -2;
            }
        }

        // ------------------------------------------------------------------
        // 状态日志
        // ------------------------------------------------------------------

        private void LogReset()
        {
            _log.Clear();
            _logHasError = false;
        }

        private void LogOk(string msg) { _log.Add("[OK] " + msg); }
        private void LogSkip(string msg) { if (!string.IsNullOrEmpty(msg)) _log.Add("[--] " + msg); }

        private void LogWarn(string msg)
        {
            _log.Add("[! ] " + msg);
        }

        private void LogErr(string msg)
        {
            _log.Add("[X ] " + msg);
            _logHasError = true;
        }

        private void FlushStatus(bool alsoLogConsole)
        {
            _status = string.Join("\n", _log.ToArray());
            _statusIsError = _logHasError;
            if (alsoLogConsole)
            {
                UnityEngine.Debug.Log("[地图编辑器] 一键写入日志：\n" + _status);
            }
            Repaint();
        }
    }
}
