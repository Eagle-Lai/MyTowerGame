// 只读工具：以当前配置源表 Levels/Lxx/LevelMap.xlsx 为唯一依据，计算每关地图的长度指标。
//   直线距离（飞行）、空板最短路（地面无塔）、最长诱导路径（全部可建格建塔后可逼出的最长地面路）。
// 不写任何源表 / 导出产物；结果输出到 --out 指定的 JSON。
// 用法: dotnet run -- <Levels目录> <out.json> [每关秒数=60] [diag=0|1]
using System.Diagnostics;
using System.IO.Compression;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;

var levelsDir = args.Length > 0 ? args[0] : "Luban/Config/Datas/Levels";
var outPath = args.Length > 1 ? args[1] : "map_metrics.json";
double limit = args.Length > 2 ? double.Parse(args[2]) : 60;
bool diag = args.Length > 3 && args[3] == "1";

var results = new List<object>();
foreach (var dir in Directory.GetDirectories(levelsDir, "L*").OrderBy(d => d))
{
    var file = Path.Combine(dir, "LevelMap.xlsx");
    var (cols, rows, cells) = ReadMap(file);
    var g = new Grid(cols, rows, cells, diag);
    var sw = Stopwatch.StartNew();
    var (best, proven) = g.LongestInducedPath(limit);
    results.Add(new
    {
        level = Path.GetFileName(dir),
        source = file.Replace('\\', '/'),
        sourceSha256 = Convert.ToHexString(System.Security.Cryptography.SHA256.HashData(File.ReadAllBytes(file))),
        cols, rows,
        start = new[] { g.S % cols, g.S / cols },
        goal = new[] { g.E % cols, g.E / cols },
        obstacles = cells.Sum(r => r.Count(c => c == '#')),
        straight = Math.Round(Math.Sqrt(Math.Pow(g.S % cols - g.E % cols, 2) + Math.Pow(g.S / cols - g.E / cols, 2)), 3),
        shortestCells = g.Shortest(),
        longestCells = best.Count,
        longestProven = proven,
        towerCellsInLongest = g.FreeCount - best.Count,
        seconds = Math.Round(sw.Elapsed.TotalSeconds, 1),
        path = best.Select(i => new[] { i % cols, i / cols }),
        cells,
    });
    Console.WriteLine($"{Path.GetFileName(dir)} {cols}x{rows} straight={((dynamic)results[^1]).straight} shortest={g.Shortest()} longest={best.Count} proven={proven} {sw.Elapsed.TotalSeconds:F1}s");
}
File.WriteAllText(outPath, JsonSerializer.Serialize(results, new JsonSerializerOptions { WriteIndented = true, Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping }));

static (int, int, string[]) ReadMap(string path)
{
    using var zip = ZipFile.OpenRead(path);
    string Read(string n) { var e = zip.GetEntry(n); if (e == null) return ""; using var s = new StreamReader(e.Open(), Encoding.UTF8); return s.ReadToEnd(); }
    var shared = Regex.Matches(Read("xl/sharedStrings.xml"), "<si>(.*?)</si>", RegexOptions.Singleline)
        .Select(m => Regex.Replace(m.Groups[1].Value, "<[^>]+>", "")).ToList();
    var sheet = Read("xl/worksheets/sheet1.xml");
    string Cell(string r)
    {
        var m = Regex.Match(sheet, $"<c r=\"{r}\"([^>]*)>(.*?)</c>", RegexOptions.Singleline);
        if (!m.Success) throw new Exception($"{path}: 缺少单元格 {r}");
        var v = Regex.Replace(m.Groups[2].Value, "<[^>]+>", "");
        return m.Groups[1].Value.Contains("t=\"s\"") ? shared[int.Parse(v)] : System.Net.WebUtility.HtmlDecode(v);
    }
    if (Cell("D1") != "cols" || Cell("E1") != "rows" || Cell("F1") != "cells") throw new Exception($"{path}: 表头不符");
    int cols = int.Parse(Cell("D4")), rows = int.Parse(Cell("E4"));
    var cells = Cell("F4").Split('|');
    if (cells.Length != rows || cells.Any(r => r.Length != cols)) throw new Exception($"{path}: cells 尺寸与 cols/rows 不符");
    return (cols, rows, cells);
}

class Grid
{
    readonly int W, H; readonly bool[] free; readonly int[][] adj;
    public readonly int S, E; public int FreeCount => free.Count(f => f);

    public Grid(int w, int h, string[] cells, bool diag)
    {
        W = w; H = h; free = new bool[w * h];
        for (int y = 0; y < h; y++) for (int x = 0; x < w; x++)
        {
            char c = cells[y][x]; int i = y * w + x;
            free[i] = c != '#';
            if (c == 'S') S = i; if (c == 'E') E = i;
        }
        var dirs = new List<(int, int)> { (1, 0), (-1, 0), (0, 1), (0, -1) };
        if (diag) dirs.AddRange(new[] { (1, 1), (1, -1), (-1, 1), (-1, -1) });
        adj = new int[w * h][];
        for (int i = 0; i < w * h; i++)
        {
            int x = i % w, y = i / w; var l = new List<int>();
            if (free[i]) foreach (var (dx, dy) in dirs)
            {
                int nx = x + dx, ny = y + dy;
                if (nx < 0 || ny < 0 || nx >= w || ny >= h || !free[ny * w + nx]) continue;
                if (dx != 0 && dy != 0 && (!free[y * w + nx] || !free[ny * w + x])) continue; // 斜走不切角
                l.Add(ny * w + nx);
            }
            adj[i] = l.ToArray();
        }
    }

    public int Shortest()
    {
        var d = Enumerable.Repeat(-1, W * H).ToArray(); var q = new Queue<int>(); d[S] = 1; q.Enqueue(S);
        while (q.Count > 0) { int u = q.Dequeue(); foreach (var v in adj[u]) if (d[v] < 0) { d[v] = d[u] + 1; q.Enqueue(v); } }
        return d[E];
    }

    // 最长诱导路径：路径上任意两格若相邻，必须是路径上的前后格，否则敌人会抄近路。
    // block[i] > 0 表示该格已与路径上某个非末端格相邻、不能再被选入路径（将建塔）。
    int[] block = null!; List<int> cur = new(), best = new(); Stopwatch sw = null!; double lim; bool timedOut; long nodes;
    public (List<int>, bool) LongestInducedPath(double seconds)
    {
        block = new int[W * H]; cur = new() { S }; best = new(); sw = Stopwatch.StartNew(); lim = seconds; timedOut = false;
        Dfs(S);
        return (best, !timedOut);
    }

    void Dfs(int u)
    {
        if (timedOut) return;
        if ((++nodes & 1023) == 0 && sw.Elapsed.TotalSeconds > lim) { timedOut = true; return; }
        if (u == E) { if (cur.Count > best.Count) best = new List<int>(cur); return; }
        if (cur.Count + Bound(u) <= best.Count) return;
        // u 成为非末端后，它的邻居（除即将走向的那个）都必须被封锁
        foreach (var v in adj[u].OrderBy(v => adj[v].Count(n => block[n] == 0)))
        {
            if (block[v] > 0 || cur.Contains(v)) continue;
            foreach (var n in adj[u]) block[n]++;
            block[v]--;
            if (InducedOk(v)) { cur.Add(v); Dfs(v); cur.RemoveAt(cur.Count - 1); }
            block[v]++;
            foreach (var n in adj[u]) block[n]--;
            if (timedOut) return;
        }
    }

    // v 不得与路径上除 u（末端）以外的格相邻
    bool InducedOk(int v)
    {
        int u = cur[^1];
        foreach (var n in adj[v]) if (n != u && cur.Contains(n)) return false;
        return true;
    }

    // 上界：从 u 出发、不经过被封锁格与已在路径上的格，可达的格数（须含 E，否则剪掉）
    int Bound(int u)
    {
        var seen = new bool[W * H]; var st = new Stack<int>(); st.Push(u); seen[u] = true; int cnt = 0; bool hasE = false;
        foreach (var c in cur) seen[c] = true;
        while (st.Count > 0)
        {
            int x = st.Pop(); cnt++; if (x == E) hasE = true;
            foreach (var n in adj[x]) if (!seen[n] && block[n] == 0) { seen[n] = true; st.Push(n); }
        }
        return hasE ? cnt - 1 : int.MinValue / 2;
    }
}
