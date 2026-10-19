using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using SimpleJSON;
using UnityEditor;
using UnityEngine;

namespace FTProject.EditorTools
{
    public sealed class BalanceDraft : ScriptableObject { public string json; }

    /// <summary>The editor is a view over the CLI's resolved plan, never a second formula implementation.</summary>
    public sealed class LevelBalanceWorkbench : EditorWindow
    {
        private const string RecipeRel = "Luban/BalanceDesign/balance_design.json";
        private const string LocalRel = "Library/BalanceWorkbench";
        private static readonly string[] BuiltinNames =
            { "D01 非常容易", "D02 容易", "D03 中等偏下", "D04 中等", "D05 中等偏上", "D06 困难", "D07 非常困难", "D08 极度困难" };
        private static readonly string[] Tabs = { "波次与覆盖", "塔与配方", "地图", "差异与曲线", "策略与报告", "任务日志" };
        private BalanceDraft _draft;
        private JSONNode _recipe, _preview, _plan;
        private string _raw, _status = "选择预设，编辑草稿后运行候选预览。";
        private string _lastOutput, _rollbackPath = "", _newPreset = "CUSTOM01";
        private string _field = "targetEhp", _value = "1.1";
        private int _preset = 3, _level = 1, _wave = 1, _scope, _lastWave = 20, _operation = 1, _tab, _curve;
        private int _strategy = 2;
        private int _comparisonPolicy;
        private int _target, _towerId = 1;
        private float _step = 0.05f;
        private int _seed = 42;
        private string _mapBrush = "#";
        private Vector2 _scroll, _logScroll;
        private bool _autoPreview = true, _allProfiles, _showRaw;
        private bool _overlayProfiles;
        private readonly Dictionary<string, JSONNode> _comparisonFiles = new Dictionary<string, JSONNode>();
        private double _dirtyAt = -1;
        private readonly Dictionary<string, bool> _folds = new Dictionary<string, bool>();
        private string Root { get { return BalanceWorkbenchProcess.ProjectRoot; } }
        private int CampaignLevels { get { return _recipe != null && _recipe["campaignLevelCount"].AsInt > 0 ? _recipe["campaignLevelCount"].AsInt : 20; } }
        private int CampaignWaves { get { return _recipe != null && _recipe["wavesPerLevel"].AsInt > 0 ? _recipe["wavesPerLevel"].AsInt : 20; } }
        private string Local { get { return Path.Combine(Root, LocalRel); } }
        private string DraftPath { get { return Path.Combine(Local, "draft.json"); } }
        private string ProfileId
        {
            get
            {
                var profiles = ProfileNodes();
                return _preset < profiles.Count ? profiles[_preset]["id"].Value : "D04";
            }
        }

        [MenuItem("Tools/塔防/关卡数值工作台", false, 120)]
        public static void Open() { GetWindow<LevelBalanceWorkbench>("关卡数值工作台").Show(); }

        private void OnEnable()
        {
            minSize = new Vector2(940, 650);
            Directory.CreateDirectory(Local);
            _draft = CreateInstance<BalanceDraft>(); _draft.hideFlags = HideFlags.HideAndDontSave;
            string path = File.Exists(DraftPath) ? DraftPath : Path.Combine(Root, RecipeRel);
            LoadRecipe(path);
            _lastOutput = EditorPrefs.GetString("FT.Balance.LastOutput", "");
            _rollbackPath = EditorPrefs.GetString("FT.Balance.LastBackup", "");
            LoadPreview();
            Undo.undoRedoPerformed += UndoChanged;
            EditorApplication.update += UpdatePreview;
            BalanceWorkbenchProcess.Completed += JobCompleted;
        }

        private void OnDisable()
        {
            PersistDraft();
            Undo.undoRedoPerformed -= UndoChanged;
            EditorApplication.update -= UpdatePreview;
            BalanceWorkbenchProcess.Completed -= JobCompleted;
            if (_draft != null) DestroyImmediate(_draft);
        }

        private void LoadRecipe(string path)
        {
            try
            {
                _raw = File.Exists(path) ? File.ReadAllText(path) : "{}";
                _recipe = JSON.Parse(_raw); _draft.json = _raw;
                var selected = _recipe["selectedProfileId"].Value;
                if (string.IsNullOrEmpty(selected)) selected = _recipe["activeProfileId"].Value;
                int index = ProfileNodes().FindIndex(n => n["id"].Value == selected);
                if (index >= 0) _preset = index;
            }
            catch (Exception ex) { _status = ex.Message; _recipe = new JSONObject(); }
        }

        private List<JSONNode> ProfileNodes()
        {
            var list = new List<JSONNode>();
            var source = _recipe == null ? null : _recipe["profiles"];
            if (source != null)
            {
                foreach (var kv in source)
                {
                    JSONNode n = kv.Value;
                    if (n.IsObject)
                    {
                        if (string.IsNullOrEmpty(n["id"].Value) && !source.IsArray) n["id"] = kv.Key;
                        list.Add(n);
                    }
                }
            }
            if (list.Count == 0)
                for (int i = 0; i < BuiltinNames.Length; i++)
                {
                    JSONNode n = new JSONObject(); n["id"] = "D" + (i + 1).ToString("00"); n["name"] = BuiltinNames[i]; list.Add(n);
                }
            return list;
        }

        private void BeforeEdit(string name) { Undo.RecordObject(_draft, name); }
        private void Changed()
        {
            _draft.json = _recipe.ToString(2); _raw = _draft.json;
            _dirtyAt = EditorApplication.timeSinceStartup;
            PersistDraft();
        }
        private void UndoChanged()
        {
            try { _recipe = JSON.Parse(_draft.json); _raw = _draft.json; int i = ProfileNodes().FindIndex(n => n["id"].Value == _recipe["selectedProfileId"].Value); if (i >= 0) _preset = i; PersistDraft(); _dirtyAt = EditorApplication.timeSinceStartup; Repaint(); }
            catch (Exception ex) { _status = ex.Message; }
        }
        private void PersistDraft()
        {
            if (_recipe == null) return;
            Directory.CreateDirectory(Local);
            File.WriteAllText(DraftPath, _recipe.ToString(2), new System.Text.UTF8Encoding(false));
        }
        private void UpdatePreview()
        {
            if (_dirtyAt >= 0 && _autoPreview && !BalanceWorkbenchProcess.Running &&
                EditorApplication.timeSinceStartup - _dirtyAt >= 0.2 && !EditorApplication.isCompiling)
            { _dirtyAt = -1; Run("preview"); }
            if (BalanceWorkbenchProcess.Running) Repaint();
        }

        private void OnGUI()
        {
            DrawHeader();
            _tab = GUILayout.Toolbar(_tab, Tabs, GUILayout.Height(28));
            _scroll = EditorGUILayout.BeginScrollView(_scroll);
            if (_tab == 0) DrawWaves();
            else if (_tab == 1) DrawRecipe();
            else if (_tab == 2) DrawMap();
            else if (_tab == 3) DrawComparison();
            else if (_tab == 4) DrawStrategy();
            else DrawJob();
            EditorGUILayout.EndScrollView();
            EditorGUILayout.HelpBox(_status, MessageType.Info);
            DrawActions();
        }

        private void DrawHeader()
        {
            EditorGUILayout.Space(8);
            EditorGUILayout.LabelField("关卡数值 / 五星评定", EditorStyles.boldLabel);
            using (new EditorGUILayout.HorizontalScope())
            {
                var p = ProfileNodes();
                string[] names = p.Select(n => n["id"].Value + "  " + n["name"].Value).ToArray();
                EditorGUI.BeginChangeCheck();
                int chosen = EditorGUILayout.Popup("草稿预设", Mathf.Clamp(_preset, 0, names.Length - 1), names);
                if (EditorGUI.EndChangeCheck())
                {
                    BeforeEdit("切换数值预设"); _preset = chosen;
                    _recipe["selectedProfileId"] = ProfileId; Changed();
                }
                _level = EditorGUILayout.IntSlider("关卡", _level, 1, CampaignLevels);
                _wave = EditorGUILayout.IntSlider("波", _wave, 1, CampaignWaves);
            }
            string formal = "尚未读取正式版本";
            string ratings = Path.Combine(Root, "Assets/ConfigJson/tblevelrating.json");
            if (File.Exists(ratings))
            {
                try
                {
                    var n = JSON.Parse(File.ReadAllText(ratings))[0];
                    formal = n["profileId"].Value + " / balance " + n["balanceRevision"].Value + " / rating " + n["ratingRevision"].Value;
                }
                catch (Exception ex) { formal = "正式评级读取失败: " + ex.Message; }
            }
            EditorGUILayout.LabelField("正式已应用", formal);
            EditorGUILayout.LabelField("草稿", DraftPath + (_recipe?["overrides"].Count > 0 ? "  · 已自定义" : ""), EditorStyles.miniLabel);
        }

        private void DrawWaves()
        {
            JSONNode w = CurrentWave();
            if (w != null)
            {
                EditorGUILayout.Space(7);
                EditorGUILayout.LabelField("本波候选", "L" + _level + " · " + _wave + "/" + CampaignWaves + " · " + w["count"] + " 只");
                EditorGUILayout.LabelField("EHP / 出怪间隔", w["actualEhp"].AsDouble.ToString("F2") + " / " + w["spawnIntervalMs"] + " ms");
                EditorGUILayout.LabelField("击杀金 / 清场奖", w["killGold"] + " / " + w["rewardGold"]);
                EditorGUILayout.LabelField("飞行 / 重型 / 精英 / 首领", w["flyingCount"] + " / " + w["heavyCount"] + " / " + w["eliteCount"] + " / " + w["bossCount"]);
                DrawComposition(w);
                if (_plan != null)
                    foreach (var pair in _plan["capacityEconomy"])
                        if (pair.Value["levelId"].AsInt == _level)
                        {
                            var audit = pair.Value;
                            EditorGUILayout.LabelField("可建 B / 合法容量 C", audit["buildableCells"] + " / " + audit["capacity"]);
                            EditorGUILayout.LabelField("一级混合 F / 末波前收入上限", audit["mixedLevelOneCost"] + " / " + audit["perfectIncomeBeforeFinalWave"]);
                            EditorGUILayout.LabelField("旧 85% 占用对照", audit["legacyOccupancyComparisonTowers"] + " 座（长路线优先，不作为达标条件）");
                            EditorGUILayout.LabelField("长路线参考 / 重复覆盖塔", audit["mazePathLength"] + " 步 / " + audit["mazeRepeatedCoverageTowers"] + " 座");
                            EditorGUILayout.LabelField("路线施工塔数 / 一级预算", audit["mazeTowerCount"] + " / " + audit["mazeLevelOneCost"]);
                            EditorGUILayout.HelpBox("先比较真实 S→E 路径和同塔分段复用，再比较资金与战斗贡献；参考图不自动落塔，实际结果须匹配当前 hash。", MessageType.Info);
                        }
            }
            EditorGUILayout.Space(10);
            EditorGUILayout.LabelField("精确覆盖 · 后设置的更细作用域优先", EditorStyles.boldLabel);
            _scope = EditorGUILayout.Popup("作用域", _scope, new[] { "单波", "本关连续波段", "整关", "全战役" });
            if (_scope == 1) _lastWave = EditorGUILayout.IntSlider("至第几波", _lastWave, _wave, CampaignWaves);
            _target = EditorGUILayout.Popup("对象", _target, new[] { "波次 wave", "关卡经济 level", "评级 rating", "塔 tower" });
            if (_target == 3) _towerId = EditorGUILayout.IntSlider("塔配置 ID", _towerId, 1, 9);
            _field = EditorGUILayout.TextField("字段", _field);
            EditorGUILayout.LabelField(_target == 0 ? "count / targetEhp / spawnIntervalMs / speedMultiplier / rewardGold" : _target == 1 ? "initialGold / initialHp" : _target == 2 ? "parCombatTimeMs / maxFourStarLeaks / fourStarTimePermille" : "power / CD / radius / prices / effectValue / canAttackAir", EditorStyles.wordWrappedMiniLabel);
            EditorGUILayout.LabelField("支持字段由配方/core定义；数量和间隔必须是整数。塔与地图请在各自页编辑。", EditorStyles.wordWrappedMiniLabel);
            _operation = EditorGUILayout.Popup("操作", _operation, new[] { "最终值 set", "增量倍率 multiply" });
            _value = EditorGUILayout.TextField("值（按字段单位）", _value);
            if (GUILayout.Button("加入覆盖并预览受影响范围", GUILayout.Height(28))) AddOverride();
            EditorGUILayout.Space(8);
            DrawNode(_recipe["overrides"], "overrides", 0);
            if (GUILayout.Button("移除本关/本波覆盖（可撤销）"))
            {
                BeforeEdit("移除波次覆盖");
                var array = _recipe["overrides"].AsArray;
                if (array != null)
                    for (int i = array.Count - 1; i >= 0; i--)
                    {
                        var s = array[i];
                        if (s["levelId"].AsInt == _level && (s["waveOrdinal"].AsInt == _wave || s["waveStart"].AsInt == _wave)) array.Remove(i);
                    }
                Changed();
            }
        }

        private void DrawComposition(JSONNode w)
        {
            EditorGUILayout.LabelField("原型 / 角色 / 数量 / HP / 速度 / 变体", EditorStyles.boldLabel);
            foreach (var entry in w["composition"])
            {
                var n = entry.Value;
                EditorGUILayout.LabelField(n["canonicalEnemyId"] + "  " + n["role"] + " × " + n["count"],
                    n["hp"].AsDouble.ToString("F3") + " HP · " + n["speed"].AsDouble.ToString("F3") + " 格/s · #" + n["variantId"]);
            }
        }

        private void AddOverride()
        {
            double value;
            if (!double.TryParse(_value, NumberStyles.Float, CultureInfo.InvariantCulture, out value) || double.IsNaN(value) || double.IsInfinity(value))
            { _status = "请输入有限数值（小数点使用 .）。"; return; }
            BeforeEdit("添加范围覆盖");
            if (!_recipe["overrides"].IsArray) _recipe["overrides"] = new JSONArray();
            JSONNode n = new JSONObject(); n["id"] = "edit-" + Guid.NewGuid().ToString("N").Substring(0, 12);
            n["target"] = new[] { "wave", "level", "rating", "tower" }[_target];
            n["profileId"] = ProfileId;
            n["field"] = _field; n["mode"] = _operation == 0 ? "replace" : "multiply"; n["value"] = value;
            n["scope"] = new[] { "wave", "range", "level", "global" }[_scope];
            n["levelId"] = _level;
            if (_scope == 0) n["waveOrdinal"] = _wave;
            if (_scope == 1) { n["waveStart"] = _wave; n["waveEnd"] = _lastWave; }
            if (_target == 3) n["targetId"] = _towerId;
            _recipe["overrides"].Add(n); Changed();
        }

        private void DrawRecipe()
        {
            EditorGUILayout.HelpBox("这些控件直接编辑配方草稿，生成和校验仍由同一核心执行。改变塔、经济、地图或评分参数后旧 Par 校准证据失效。", MessageType.Info);
            foreach (var kv in _recipe)
                if (kv.Key != "overrides") DrawNode(kv.Value, kv.Key, 0);
            _showRaw = EditorGUILayout.Foldout(_showRaw, "高级配方 JSON / 导入", true);
            if (_showRaw)
            {
                _raw = EditorGUILayout.TextArea(_raw ?? "", GUILayout.MinHeight(220));
                if (GUILayout.Button("解析 JSON 为草稿（可撤销）"))
                {
                    try { var n = JSON.Parse(_raw); if (!n.IsObject) throw new FormatException("Recipe root must be object"); BeforeEdit("导入配方"); _recipe = n; Changed(); }
                    catch (Exception ex) { _status = "JSON错误: " + ex.Message; }
                }
            }
        }

        private void DrawNode(JSONNode node, string path, int depth)
        {
            if (node == null || node.IsNull) return;
            if (node.IsArray || node.IsObject)
            {
                bool open; _folds.TryGetValue(path, out open);
                open = EditorGUILayout.Foldout(open, path + "  [" + node.Count + "]", true);
                _folds[path] = open;
                if (!open) return;
                EditorGUI.indentLevel++;
                var keys = new List<KeyValuePair<string, JSONNode>>();
                if (node.IsArray)
                    for (int i = 0; i < node.Count; i++) keys.Add(new KeyValuePair<string, JSONNode>(i.ToString(), node[i]));
                else foreach (var kv in node) keys.Add(new KeyValuePair<string, JSONNode>(kv.Key, kv.Value));
                foreach (var kv in keys)
                {
                    var n = kv.Value; string label = kv.Key;
                    if (n.IsArray || n.IsObject) DrawNode(n, path + "/" + label, depth + 1);
                    else
                    {
                        EditorGUI.BeginChangeCheck();
                        string next = n.IsBoolean
                            ? (EditorGUILayout.Toggle(label, n.AsBool) ? "true" : "false")
                            : EditorGUILayout.TextField(label, n.Value);
                        if (EditorGUI.EndChangeCheck())
                        {
                            double number;
                            if (n.IsNumber && (!double.TryParse(next, NumberStyles.Float, CultureInfo.InvariantCulture, out number) || double.IsNaN(number) || double.IsInfinity(number))) continue;
                            BeforeEdit("编辑 " + path + "/" + label);
                            JSONNode replacement = n.IsNumber ? (JSONNode)double.Parse(next, CultureInfo.InvariantCulture) : n.IsBoolean ? (JSONNode)(next == "true") : (JSONNode)next;
                            if (node.IsArray) node[int.Parse(label, CultureInfo.InvariantCulture)] = replacement; else node[label] = replacement;
                            Changed();
                        }
                    }
                }
                EditorGUI.indentLevel--;
            }
        }

        private JSONNode CurrentWave()
        {
            if (_preview == null) return null;
            foreach (var kv in _preview["waves"])
                if (kv.Value["levelId"].AsInt == _level && kv.Value["waveOrdinal"].AsInt == _wave) return kv.Value;
            return null;
        }

        private JSONNode CurrentMap()
        {
            if (_plan == null) return null;
            int id = _level;
            foreach (var l in _plan["tables"]["tbsceneinfo"])
                if (l.Value["id"].AsInt == _level) id = l.Value["mapId"].AsInt;
            foreach (var m in _plan["tables"]["tblevelmap"])
                if (m.Value["id"].AsInt == id) return m.Value;
            return null;
        }

        private void DrawMap()
        {
            var map = CurrentMap();
            if (map == null) { EditorGUILayout.HelpBox("先生成候选以读取同一计划中的地图。", MessageType.Info); return; }
            EditorGUILayout.LabelField("地图 cells · 候选与波次共享 planHash", EditorStyles.boldLabel);
            _mapBrush = new[] { ".", "P", "#", "X", "S", "E" }[GUILayout.Toolbar(Array.IndexOf(new[] { ".", "P", "#", "X", "S", "E" }, _mapBrush), new[] { ". 可建", "P 禁建", "# 障碍", "X 空洞", "S 出口", "E 终点" })];
            var cells = map["cells"].AsArray;
            for (int row = 0; cells != null && row < cells.Count; row++)
            {
                using (new EditorGUILayout.HorizontalScope())
                {
                    GUILayout.Label(row.ToString("00"), GUILayout.Width(25));
                    string line = cells[row].Value;
                    for (int col = 0; col < line.Length; col++)
                    {
                        Color old = GUI.backgroundColor;
                        GUI.backgroundColor = line[col] == '#' || line[col] == 'X' ? new Color(.5f, .5f, .5f) : line[col] == 'S' ? new Color(.45f, .8f, .55f) : line[col] == 'E' ? new Color(.95f, .6f, .4f) : Color.white;
                        if (GUILayout.Button(line[col].ToString(), GUILayout.Width(30), GUILayout.Height(28)))
                        {
                            BeforeEdit("地图刷格");
                            char[] chars = line.ToCharArray(); chars[col] = _mapBrush[0]; cells[row] = new string(chars);
                            SetMapOverride(map); Changed();
                        }
                        GUI.backgroundColor = old;
                    }
                }
            }
            EditorGUILayout.LabelField("S/E唯一、四方向连通和正式应用安全检查由核心执行。", EditorStyles.miniLabel);
        }

        private void SetMapOverride(JSONNode map)
        {
            if (!_recipe["overrides"].IsArray) _recipe["overrides"] = new JSONArray();
            var array = _recipe["overrides"].AsArray;
            JSONNode n = null;
            foreach (var kv in array)
                if (kv.Value["id"].Value == "map-" + ProfileId + "-" + _level) { n = kv.Value; break; }
            if (n == null) { n = new JSONObject(); array.Add(n); }
            n["id"] = "map-" + ProfileId + "-" + _level; n["target"] = "map"; n["scope"] = "level";
            n["profileId"] = ProfileId; n["levelId"] = _level; n["field"] = "cells"; n["mode"] = "replace";
            n["value"] = JSON.Parse(map["cells"].ToString());
        }

        private void DrawComparison()
        {
            if (_preview == null) return;
            _curve = GUILayout.Toolbar(_curve, new[] { "数量", "有效生命", "间隔", "收益", "出生跨度", "余额", "清场", "占用", "塔数", "支出", "路线", "复用" });
            string field = new[] { "count", "actualEhp", "spawnIntervalMs", "killGold", "plannedSpawnSpanMs", "balance", "combatElapsedMs", "occupancy", "towerCount", "spent", "pathLength", "repeatedCoverageTowers" }[_curve];
            _comparisonPolicy = EditorGUILayout.Popup("布防对照", _comparisonPolicy, new[] { "三类常规策略", "长路线扩建", "Ksmall 稀疏", "Klow 稀疏", "旧密铺对照" });
            _overlayProfiles = EditorGUILayout.Toggle("叠加八档报告", _overlayProfiles);
            if (GUILayout.Button("重新读取已生成的对比报告")) _comparisonFiles.Clear();
            if (_curve >= 5) EditorGUILayout.HelpBox("余额/清场曲线来自最近离线 " + new[] { "normal", "power", "mixed" }[_strategy] + " 策略，绑定该次 planHash。缺失或过期时不画预测曲线，请先生成对应策略报告。", MessageType.Info);
            Rect rect = GUILayoutUtility.GetRect(600, 210, GUILayout.ExpandWidth(true));
            EditorGUI.DrawRect(rect, new Color(.12f, .14f, .17f));
            var series = new Dictionary<string, List<JSONNode>>();
            foreach (string profile in _overlayProfiles ? Enumerable.Range(1, 8).Select(i => "D" + i.ToString("00")) : new[] { ProfileId })
            {
                JSONNode source;
                if (_curve < 5) source = profile == ProfileId ? _preview["waves"] : ComparisonFile(Path.Combine(Root, "Luban/BalanceDesign/Evidence30x25/Reports", profile, "waves.json"));
                else
                {
                    string strategy = _comparisonPolicy == 0 ? new[] { "normal", "power", "mixed" }[_strategy] : "mixed";
                    string policy = new[] { "baseline", "maze", "small", "low", "high" }[_comparisonPolicy];
                    source = ComparisonFile(Path.Combine(Root, "Luban/BalanceDesign/Evidence30x25/Simulation", policy, profile, strategy, "L" + _level.ToString("00") + "-" + strategy, "result.json"));
                    if (source != null && profile == ProfileId)
                    {
                        string hash = "";
                        foreach (var l in _preview["levels"]) if (l.Value["levelId"].AsInt == _level) hash = l.Value["planHash"].Value;
                        if (source["planHash"].Value != hash) source = null;
                    }
                    source = source == null ? null : source["waves"];
                }
                var points = new List<JSONNode>();
                if (source != null) foreach (var kv in source)
                    if (_curve >= 5 || kv.Value["levelId"].AsInt == _level) points.Add(kv.Value);
                if (points.Count > 0) series[profile] = points;
            }
            double max = Math.Max(1, series.Values.SelectMany(s => s).Select(n => n[field].AsDouble).DefaultIfEmpty(1).Max());
            Handles.BeginGUI();
            int colorIndex = 0;
            foreach (var pair in series)
            {
                Handles.color = Color.HSVToRGB((colorIndex++ * .115f + .48f) % 1, .6f, .95f);
                Vector3 prior = Vector3.zero;
                for (int i = 0; i < pair.Value.Count; i++)
                {
                    Vector3 point = new Vector3(rect.x + 12 + (rect.width - 24) * i / Math.Max(1, pair.Value.Count - 1),
                        rect.yMax - 15 - (float)(pair.Value[i][field].AsDouble / max) * (rect.height - 30));
                    if (i > 0) Handles.DrawLine(prior, point);
                    if (GUI.Button(new Rect(point.x - 6, point.y - 6, 12, 12), GUIContent.none, GUIStyle.none))
                    { _wave = i + 1; _tab = 0; _status = pair.Key + " 报告 · L" + _level + " 波" + _wave + " · " + field + "=" + pair.Value[i][field]; }
                    Handles.DrawSolidDisc(point, Vector3.forward, _wave == i + 1 ? 4 : 2); prior = point;
                }
            }
            Handles.EndGUI();
            EditorGUILayout.LabelField("L" + _level + " · 1—" + CampaignWaves + " 波 · max " + max.ToString("F2"));
            EditorGUILayout.LabelField("已显示报告快照", string.Join(" / ", series.Keys));
            EditorGUILayout.LabelField("字段差异（源表/行/字段/修改前→修改后）", EditorStyles.boldLabel);
            int shown = 0;
            foreach (var kv in _preview["changes"])
            {
                var n = kv.Value;
                if (++shown > 250) { EditorGUILayout.LabelField("其余差异见完整 preview.json / 导出报告。"); break; }
                EditorGUILayout.LabelField(n["table"] + " #" + n["id"] + "." + n["field"], n["before"].ToString() + " → " + n["after"].ToString());
            }
        }

        private JSONNode ComparisonFile(string path)
        {
            JSONNode node;
            if (_comparisonFiles.TryGetValue(path, out node)) return node;
            try { node = File.Exists(path) ? JSON.Parse(File.ReadAllText(path)) : null; }
            catch (Exception ex) { _status = "报告读取失败: " + ex.Message; node = null; }
            _comparisonFiles[path] = node; return node;
        }

        private void DrawStrategy()
        {
            _strategy = EditorGUILayout.Popup("可复现策略", _strategy, new[] { "普通塔为主 normal", "火力聚怪 power", "减速混合 mixed" });
            _step = EditorGUILayout.Slider("固定步长 秒", _step, .01f, .1f);
            _seed = EditorGUILayout.IntField("固定种子", _seed);
            _allProfiles = EditorGUILayout.Toggle("八档×" + CampaignLevels + "关", _allProfiles);
            EditorGUILayout.HelpBox("离线输出标为预测。真实回放从合法初始余额开始，使用隔离测试存档；单波调试不作为通关证据。正式应用和已有对局间以新局为重载边界。", MessageType.Info);
            using (new EditorGUI.DisabledScope(BalanceWorkbenchProcess.Running))
            {
                if (GUILayout.Button("运行离线策略矩阵")) Run("simulate");
                bool fresh = _plan != null && _recipe != null && _plan["recipe"].ToString() == _recipe.ToString() && _plan["profileId"].Value == ProfileId;
                using (new EditorGUI.DisabledScope(!fresh))
                if (GUILayout.Button("准备所选关的隔离实测（需进入 PlayMode）"))
                {
                    SessionState.SetInt("FT.Balance.TestLevel", _level);
                    SessionState.SetString("FT.Balance.TestProfile", ProfileId);
                    SessionState.SetString("FT.Balance.TestStrategy", new[] { "normal", "power", "mixed" }[_strategy]);
                    SessionState.SetString("FT.Balance.TestCandidatePlan", _lastOutput == null ? "" : Path.Combine(_lastOutput, "resolved-plan.json"));
                    _status = "已登记测试请求。使用 Tools/塔防/数值验证/运行隔离回放 执行。";
                }
                if (!fresh) EditorGUILayout.HelpBox("草稿尚未成功生成当前候选，请先运行候选预览。", MessageType.Info);
            }
            EditorGUILayout.Space(10);
            if (GUILayout.Button("导出本次 JSON/CSV/Markdown 报告目录"))
            {
                string dest = EditorUtility.OpenFolderPanel("选择报告目标", Root, "");
                if (!string.IsNullOrEmpty(dest) && Directory.Exists(_lastOutput))
                {
                    foreach (string file in Directory.GetFiles(_lastOutput))
                        if (new[] { ".json", ".csv", ".md", ".log" }.Contains(Path.GetExtension(file))) File.Copy(file, Path.Combine(dest, Path.GetFileName(file)), true);
                    _status = "报告已导出至 " + dest;
                }
            }
            _rollbackPath = EditorGUILayout.TextField("应用记录/备份路径", _rollbackPath);
            using (new EditorGUI.DisabledScope(BalanceWorkbenchProcess.Running || EditorApplication.isPlaying))
                if (GUILayout.Button("从应用记录回滚整批内容")) Run("rollback");
            if (_preview != null)
            {
                foreach (var kv in _preview["levels"])
                {
                    var l = kv.Value;
                    if (l["levelId"].AsInt == _level)
                    {
                        EditorGUILayout.LabelField("本关计划摘要", l["planHash"]);
                        EditorGUILayout.LabelField("五星战斗上限", l["parCombatTimeMs"] + " ms · " + l["calibrationStatus"]);
                    }
                }
            }
        }

        private void DrawJob()
        {
            EditorGUILayout.LabelField("任务", (BalanceWorkbenchProcess.JobId ?? "无") + " · " + BalanceWorkbenchProcess.Command);
            EditorGUILayout.LabelField("耗时", BalanceWorkbenchProcess.ElapsedSeconds.ToString("F2") + "s");
            EditorGUILayout.LabelField("产物", BalanceWorkbenchProcess.DirectoryPath ?? _lastOutput);
            if (BalanceWorkbenchProcess.Running && GUILayout.Button("取消本任务（提交阶段在安全边界退出）")) BalanceWorkbenchProcess.Cancel();
            _logScroll = EditorGUILayout.BeginScrollView(_logScroll, GUILayout.MinHeight(300));
            EditorGUILayout.TextArea(BalanceWorkbenchProcess.Log, GUILayout.ExpandHeight(true));
            EditorGUILayout.EndScrollView();
        }

        private void DrawActions()
        {
            using (new EditorGUILayout.HorizontalScope())
            {
                _autoPreview = GUILayout.Toggle(_autoPreview, "200ms防抖预览", GUILayout.Width(135));
                using (new EditorGUI.DisabledScope(BalanceWorkbenchProcess.Running || EditorApplication.isCompiling || EditorApplication.isUpdating))
                {
                    if (GUILayout.Button("候选 / 差异")) Run("preview");
                    if (GUILayout.Button("快速校验")) Run("validate");
                    using (new EditorGUI.DisabledScope(EditorApplication.isPlaying))
                        if (GUILayout.Button("验证并正式应用")) Run("apply");
                }
                if (GUILayout.Button("撤销")) Undo.PerformUndo();
                if (GUILayout.Button("重做")) Undo.PerformRedo();
            }
            using (new EditorGUILayout.HorizontalScope())
            {
                if (GUILayout.Button("恢复已应用配方")) { BeforeEdit("恢复已应用值"); LoadRecipe(Path.Combine(Root, RecipeRel)); Changed(); }
                if (GUILayout.Button("导出草稿"))
                {
                    string p = EditorUtility.SaveFilePanel("导出配方", Root, "balance_design.custom.json", "json");
                    if (!string.IsNullOrEmpty(p)) File.WriteAllText(p, _recipe.ToString(2));
                }
                _newPreset = GUILayout.TextField(_newPreset, GUILayout.Width(110));
                if (GUILayout.Button("另存预设")) SaveAsPreset();
                BalanceWorkbenchProcess.Python = EditorGUILayout.TextField("Python", BalanceWorkbenchProcess.Python);
            }
        }

        private void SaveAsPreset()
        {
            if (string.IsNullOrWhiteSpace(_newPreset) || ProfileNodes().Any(n => n["id"].Value == _newPreset))
            { _status = "预设ID必须非空且唯一；内置八档不能覆盖。"; return; }
            BeforeEdit("另存自定义预设");
            string oldProfile = ProfileId;
            var source = JSON.Parse(ProfileNodes()[_preset].ToString()); source["id"] = _newPreset;
            source["name"] = "自定义 " + _newPreset;
            if (_recipe["profiles"].IsArray) _recipe["profiles"].Add(source);
            else _recipe["profiles"][_newPreset] = source;
            _preset = ProfileNodes().Count - 1; _recipe["selectedProfileId"] = _newPreset;
            if (_recipe["overrides"].IsArray)
            {
                var copies = new List<JSONNode>();
                foreach (var kv in _recipe["overrides"])
                    if (kv.Value["profileId"].Value == oldProfile)
                    { var copy = JSON.Parse(kv.Value.ToString()); copy["profileId"] = _newPreset; copy["id"] = copy["id"].Value + "-" + _newPreset; copies.Add(copy); }
                foreach (var n in copies) _recipe["overrides"].Add(n);
            }
            Changed(); _status = "自定义预设已写入草稿；正式应用后纳入权威配方版本。";
        }

        private void Run(string command)
        {
            PersistDraft(); _dirtyAt = -1;
            string job = DateTime.UtcNow.ToString("yyyyMMdd-HHmmss-fff") + "-" + command;
            _lastOutput = Path.Combine(Local, job);
            string args = "--profile " + BalanceWorkbenchProcess.Quote(ProfileId) + " --recipe " + BalanceWorkbenchProcess.Quote(DraftPath) + " --out " + BalanceWorkbenchProcess.Quote(_lastOutput);
            if (command == "simulate")
                args += " --strategy " + new[] { "normal", "power", "mixed" }[_strategy] + " --step " + _step.ToString("R", CultureInfo.InvariantCulture) + " --seed " + _seed + (_allProfiles ? " --all-profiles" : " --level-min " + _level + " --level-max " + _level);
            if (command == "rollback") args += " --transaction " + BalanceWorkbenchProcess.Quote(_rollbackPath);
            if (BalanceWorkbenchProcess.Start(command, args, _lastOutput))
            {
                _status = "运行 " + command + " · " + job;
                EditorPrefs.SetString("FT.Balance.LastOutput", _lastOutput);
            }
            else _status = "未启动。检查任务日志、Python和编译状态。";
        }

        private void LoadPreview()
        {
            _preview = null; _plan = null;
            if (string.IsNullOrEmpty(_lastOutput)) return;
            string p = Path.Combine(_lastOutput, "preview.json");
            string plan = Path.Combine(_lastOutput, "resolved-plan.json");
            try
            {
                if (File.Exists(p)) _preview = JSON.Parse(File.ReadAllText(p));
                if (File.Exists(plan)) _plan = JSON.Parse(File.ReadAllText(plan));
            }
            catch (Exception ex) { _status = "候选读取失败: " + ex.Message; }
        }

        private void JobCompleted()
        {
            _lastOutput = BalanceWorkbenchProcess.DirectoryPath; LoadPreview();
            bool ok = BalanceWorkbenchProcess.ExitCode == 0;
            _status = (ok ? "已完成 " : "失败（正式应用未认证成功） ") + BalanceWorkbenchProcess.Command + " · " + BalanceWorkbenchProcess.ElapsedSeconds.ToString("F2") + "s · " + _lastOutput;
            if (ok && BalanceWorkbenchProcess.IsMutation)
            {
                if (BalanceWorkbenchProcess.Command == "apply") _rollbackPath = Path.Combine(_lastOutput, "transaction.json");
                string result = Path.Combine(_lastOutput, "result.json");
                if (File.Exists(result))
                {
                    var n = JSON.Parse(File.ReadAllText(result));
                    if (!string.IsNullOrEmpty(n["backup"].Value)) _rollbackPath = n["backup"];
                }
                EditorPrefs.SetString("FT.Balance.LastBackup", _rollbackPath);
                AssetDatabase.Refresh();
            }
            Repaint();
        }
    }
}
