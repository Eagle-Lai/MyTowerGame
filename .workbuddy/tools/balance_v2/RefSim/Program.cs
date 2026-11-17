// RefSim —— 数值体系 V2 参照解模拟器（只读：不写任何配置源表 / 导出产物）
// 输入：Docs/BalanceV2/map_metrics.json（由 MapMetrics 从当前 LevelMap.xlsx 生成）
// 输出：<outDir>/levels/Lxx.json + summary.json
// 运行时语义对齐（2026-11-14 代码核对）：四向寻路、即时命中、最远进度优先、单体对空优先、
// 范围对爆炸半径内全部地面怪全额伤害、减速取最强不叠加（持续 CD+0.1s）、赏金击杀即时到账、波次奖励清波到账。
using System.Text.Json;
using System.Text.Json.Serialization;

if (args.Length > 0 && args[0] == "baseline") { Baseline.Run(args.Skip(1).ToArray()); return; }
var metricsPath = args.Length > 0 ? args[0] : "Docs/BalanceV2/map_metrics.json";
var outDir = args.Length > 1 ? args[1] : "Docs/BalanceV2/sim";
var only = args.Length > 2 ? args[2].Split(',').ToHashSet() : null;
Directory.CreateDirectory(Path.Combine(outDir, "levels"));

var maps = JsonSerializer.Deserialize<List<MapIn>>(File.ReadAllText(metricsPath), new JsonSerializerOptions { PropertyNameCaseInsensitive = true })!;
var results = new System.Collections.Concurrent.ConcurrentBag<LevelOut>();
Parallel.ForEach(maps.Where(m => only == null || only.Contains(m.Level)), new ParallelOptions { MaxDegreeOfParallelism = Environment.ProcessorCount }, m =>
{
    var sw = System.Diagnostics.Stopwatch.StartNew();
    var lv = Designer.Run(m);
    File.WriteAllText(Path.Combine(outDir, "levels", m.Level + ".json"), JsonSerializer.Serialize(lv, Json.Opt));
    results.Add(lv);
    Console.WriteLine($"{m.Level} S{lv.Stage} vg={lv.GroundSpeed:F2} waves={lv.Waves.Min(w => w.Duration):F0}-{lv.Waves.Max(w => w.Duration):F0}s n={lv.Waves[0].EnemyCount}-{lv.Waves[^1].EnemyCount} air%={lv.Waves.Where(w => w.W >= 5).Min(w => w.AirShareActual):F2}-{lv.Waves.Where(w => w.W >= 5).Max(w => w.AirShareActual):F2} combat={lv.CombatSeconds:F0}s C={lv.TotalCost} D={lv.DLevel:F1} leaks={lv.Waves.Sum(w => w.Leaks)} marginLeaks={lv.Waves.Sum(w => w.LeaksAtMargin)} belowLeakWaves={lv.Waves.Count(w => w.LeaksBelowMargin > 0)}/25 pre={lv.Waves.Count(w => w.MustPreDefend)} altOpen={lv.OpeningAltLeaks} ({sw.Elapsed.TotalSeconds:F0}s)");
});
if (only == null) { Report.Write(outDir, results.OrderBy(r => r.Level).ToList()); TablePlan.Write(outDir, results.OrderBy(r => r.Level).ToList(), maps.ToDictionary(m => m.Level, m => new MapG(m))); }
File.WriteAllText(Path.Combine(outDir, "summary.json"), JsonSerializer.Serialize(results.OrderBy(r => r.Level).Select(r => new
{
    r.Level, r.Stage, r.Lives, r.GroundSpeed, r.AirSpeed, r.CombatSeconds, r.TotalSeconds, r.Margin, r.HardMargin, r.TotalCost, r.DLevel, r.DPeak, r.DHardMean,
    waveD = r.Waves.Select(w => Math.Round(w.D, 1)),
}), Json.Opt));

static class Json { public static readonly JsonSerializerOptions Opt = new() { WriteIndented = true, IncludeFields = true, Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping, DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull }; }

public record MapIn(string Level, int Cols, int Rows, int[] Start, int[] Goal, int LongestCells, int[][] Path, string[] Cells);

// ---------------------------------------------------------------- 全局参数（02_全局参数.md）
public record TowerDef(int Type, int Lv, int Cost, double Power, double Cd, double Range, double Splash, double Slow, bool Air, double AirMul = 1)
{
    public double Dps => Cd > 0 && Power > 0 ? Power / Cd : 0;
    public static TowerDef[,] T =
    {
        { new(1,1,20, 8,0.80,2.00,0,0,true), new(1,2,30,20,0.80,2.25,0,0,true), new(1,3,50,44,0.80,2.50,0,0,true) },
        { new(2,1,30,12,1.50,2.00,0.90,0,false), new(2,2,40,30,1.50,2.10,1.05,0,false), new(2,3,60,60,1.50,2.20,1.20,0,false) },
        { new(3,1,25, 0,0.25,2.00,0,0.20,true), new(3,2,35, 0,0.25,2.25,0,0.30,true), new(3,3,50, 0,0.25,2.50,0,0.40,true) },
    };
    public static TowerDef Of(int type, int lv) => T[type - 1, lv - 1];
}

public record Arche(string Id, bool Fly, double Hp, double Spd, double Armor, int Leak)
{
    public static readonly Dictionary<string, Arche> All = new()
    {
        ["G1"] = new("G1", false, 1.00, 1.00, 0.00, 1),
        ["G2"] = new("G2", false, 0.30, 1.05, 0.00, 1),
        ["G3"] = new("G3", false, 0.60, 1.80, 0.00, 1),
        ["G4"] = new("G4", false, 2.50, 0.80, 0.40, 2),
        ["A1"] = new("A1", true, 1.00, 1.00, 0.00, 2),
        ["A2"] = new("A2", true, 2.20, 0.80, 0.20, 3),
        ["B"] = new("B", false, 12.0, 0.80, 0.25, 5),
        ["E"] = new("E", false, 4.00, 0.90, 0.15, 3),   // V2.3 困难波精英
    };
    public double HpeMult => Hp / (1 - Armor);
}

// ---------------------------------------------------------------- 地图
public class MapG
{
    public int W, H; public bool[] Free; public int S, E; public double[] AirFrom = new double[2], AirTo = new double[2];
    public string AirSpawnRule = "S";
    public List<int> FinalPath = new(); public HashSet<int> PathSet = new();
    public int[] Dist = Array.Empty<int>();
    public MapG(MapIn m)
    {
        W = m.Cols; H = m.Rows; Free = new bool[W * H];
        for (int y = 0; y < H; y++) for (int x = 0; x < W; x++) { char c = m.Cells[y][x]; Free[y * W + x] = c != '#'; if (c == 'S') S = y * W + x; if (c == 'E') E = y * W + x; }
        FinalPath = m.Path.Select(p => p[1] * W + p[0]).ToList(); PathSet = FinalPath.ToHashSet();
        double sx = S % W + .5, sy = S / W + .5, ex = E % W + .5, ey = E / W + .5;
        if (Math.Sqrt((sx - ex) * (sx - ex) + (sy - ey) * (sy - ey)) < 5)
        {   // 用户规则：S–E 直线 < 5 格 → 左上角 (0,0) 出生；若 S 即左上角（L28）→ 右上角 (0, W-1)
            if (S == 0) { sx = W - 1 + .5; sy = .5; AirSpawnRule = "右上(0," + (W - 1) + ")"; }
            else { sx = .5; sy = .5; AirSpawnRule = "左上(0,0)"; }
        }
        AirFrom = new[] { sx, sy }; AirTo = new[] { ex, ey };
    }
    public double AirLen => Math.Sqrt(Math.Pow(AirFrom[0] - AirTo[0], 2) + Math.Pow(AirFrom[1] - AirTo[1], 2));
    public static readonly (int dx, int dy)[] Dirs = { (0, 1), (0, -1), (-1, 0), (1, 0) }; // 与 A* 邻居加入顺序一致：row+1,row-1,col-1,col+1
    public IEnumerable<int> Nb(int i) { int x = i % W, y = i / W; foreach (var (dx, dy) in Dirs) { int nx = x + dx, ny = y + dy; if (nx >= 0 && ny >= 0 && nx < W && ny < H) yield return ny * W + nx; } }
    public int[] Bfs(bool[] wall)
    {
        var d = Enumerable.Repeat(int.MaxValue, W * H).ToArray(); var q = new Queue<int>(); d[E] = 0; q.Enqueue(E);
        while (q.Count > 0) { int u = q.Dequeue(); foreach (var v in Nb(u)) if (Free[v] && !wall[v] && d[v] == int.MaxValue) { d[v] = d[u] + 1; q.Enqueue(v); } }
        return d;
    }
    public double Cx(int i) => i % W + .5; public double Cy(int i) => i / W + .5;
    public double AirChord(int cell, double r)
    {   // 空中直线落在以 cell 为心、半径 r 的圆内的长度
        double px = Cx(cell), py = Cy(cell), ax = AirFrom[0], ay = AirFrom[1], bx = AirTo[0], by = AirTo[1];
        double dx = bx - ax, dy = by - ay, L = Math.Sqrt(dx * dx + dy * dy); if (L < 1e-9) return 0; dx /= L; dy /= L;
        double t0 = (px - ax) * dx + (py - ay) * dy, dist2 = Math.Pow(px - ax - t0 * dx, 2) + Math.Pow(py - ay - t0 * dy, 2);
        if (dist2 >= r * r) return 0; double h = Math.Sqrt(r * r - dist2);
        return Math.Max(0, Math.Min(L, t0 + h) - Math.Max(0, t0 - h));
    }
}

// ---------------------------------------------------------------- 建造动作
public record Act(int Cell, int Type, bool Upgrade, int ToLv, int Cost, string Why);

// ---------------------------------------------------------------- 一波的出怪
public record Spawn(string Arche, double T, double Gap);

// ---------------------------------------------------------------- 战斗模拟
public class Sim
{
    public const double Dt = 0.04;
    public class Tw { public int Cell, Type, Lv; public TowerDef D => TowerDef.Of(Type, Lv); public double Timer; public En? Tgt; public int Invested; public int BuiltWave; public double BuiltT; }
    public class En { public Arche A = null!; public double Hp, MaxHp, X, Y, Spd; public int Cell, Next = -1; public bool Dead, Leaked; public double SlowR, SlowT; public double Bounty; public double Born; public double DieRemain = -1; public int Idx; }

    public MapG M; public List<Tw> Towers = new(); public bool[] Wall; public int[] Dist; public double Gold; public int QIdx; public List<Act> Queue;
    public double FireScale = 1, BuildDelay = 0;
    public List<string> Log = new();
    public Sim(MapG m, List<Act> q) { M = m; Queue = q; Wall = new bool[m.W * m.H]; Dist = m.Bfs(Wall); }
    public Sim Clone(bool copyQueue = false)
    {
        var s = (Sim)MemberwiseClone(); s.Wall = (bool[])Wall.Clone(); s.Dist = (int[])Dist.Clone(); s.Log = new();
        if (copyQueue) s.Queue = new List<Act>(Queue);
        s.Towers = Towers.Select(t => new Tw { Cell = t.Cell, Type = t.Type, Lv = t.Lv, Invested = t.Invested, BuiltWave = t.BuiltWave, BuiltT = t.BuiltT }).ToList(); return s;
    }
    public int PathLen => Dist[M.S] + 1;

    // 在不阻塞、格子空闲时执行队列下一动作
    bool TryBuild(List<En> live, int wave, double t, string phase)
    {
        if (QIdx >= Queue.Count) return false; var a = Queue[QIdx]; if (Math.Floor(Gold + 1e-6) < a.Cost) return false; // 运行时金币只按整数可用
        if (!a.Upgrade)
        {
            foreach (var e in live) if (!e.A.Fly && (e.Cell == a.Cell || e.Next == a.Cell)) return false;
            Wall[a.Cell] = true; Dist = M.Bfs(Wall);
            if (Dist[M.S] == int.MaxValue) throw new Exception("堵死");
            Towers.Add(new Tw { Cell = a.Cell, Type = a.Type, Lv = 1, Invested = a.Cost, BuiltWave = wave, BuiltT = t });
        }
        else { var tw = Towers.First(x => x.Cell == a.Cell); tw.Lv = a.ToLv; tw.Invested += a.Cost; tw.Tgt = null; }
        Gold -= a.Cost; QIdx++;
        Log.Add($"{phase} t={t:F1}s {(a.Upgrade ? "升级" : "建造")} ({a.Cell % M.W},{a.Cell / M.W}) {Name(a.Type)}{(a.Upgrade ? a.ToLv : 1)}级 -{a.Cost}金 余{Gold:F0} 路径{PathLen}格 [{a.Why}]");
        return true;
    }
    public static string Name(int t) => t == 1 ? "单体" : t == 2 ? "范围" : "减速";

    public void BuildAll(int wave, double t, string phase) { while (TryBuild(new List<En>(), wave, t, phase)) { } }

    public record Result(int Leaks, int LeakHp, double Duration, double MinRemainFrac, double TAir, List<En> Enemies, double GoldEnd);

    // 运行一波：spawns + hp 表；mid-wave 以赏金实时建造
    public Result RunWave(int wave, List<Spawn> spawns, Func<Arche, double> hpOf, Func<Arche, double> spdOf, Func<Arche, double> bountyOf, double maxT = 600)
    {
        foreach (var tw0 in Towers) { tw0.Timer = 0; tw0.Tgt = null; }
        var all = new List<En>(); int si = 0; double t = 0; var live = new List<En>(); double tAir = -1;
        var order = spawns.OrderBy(s => s.T).ToList(); double pendingBuildAt = BuildDelay > 0 ? 0 : -1;
        while (t < maxT)
        {
            while (si < order.Count && order[si].T <= t + 1e-9)
            {
                var a = Arche.All[order[si].Arche]; var e = new En { A = a, MaxHp = hpOf(a), Spd = spdOf(a), Bounty = bountyOf(a), Born = t, Idx = si };
                e.Hp = e.MaxHp;
                if (a.Fly) { e.X = M.AirFrom[0]; e.Y = M.AirFrom[1]; } else { e.Cell = M.S; e.X = M.Cx(M.S); e.Y = M.Cy(M.S); }
                live.Add(e); all.Add(e); si++;
            }
            // 建造（赏金实时到账后）
            if (BuildDelay <= 0) { while (TryBuild(live, wave, t, $"W{wave}中")) { } }
            else if (QIdx < Queue.Count && Math.Floor(Gold + 1e-6) >= Queue[QIdx].Cost) { if (pendingBuildAt < 0) pendingBuildAt = t + BuildDelay; if (t >= pendingBuildAt) { while (TryBuild(live, wave, t, $"W{wave}中")) { } pendingBuildAt = -1; } }
            // 移动
            foreach (var e in live)
            {
                if (e.SlowT > 0) { e.SlowT -= Dt; if (e.SlowT <= 0) e.SlowR = 0; }
                double sp = e.Spd * (1 - Math.Min(0.95, e.SlowR)) * Dt;
                if (e.A.Fly)
                {
                    double dx = M.AirTo[0] - e.X, dy = M.AirTo[1] - e.Y, d = Math.Sqrt(dx * dx + dy * dy);
                    if (d <= sp + 0.08) { e.Leaked = true; continue; }
                    e.X += dx / d * sp; e.Y += dy / d * sp;
                }
                else
                {
                    if (e.Next < 0 || Wall[e.Next]) e.Next = NextCell(e.Cell);
                    double tx = M.Cx(e.Next), ty = M.Cy(e.Next), dx = tx - e.X, dy = ty - e.Y, d = Math.Sqrt(dx * dx + dy * dy);
                    if (d <= sp + 0.08) { e.X = tx; e.Y = ty; e.Cell = e.Next; if (e.Cell == M.E) { e.Leaked = true; continue; } e.Next = NextCell(e.Cell); }
                    else { e.X += dx / d * sp; e.Y += dy / d * sp; }
                }
            }
            live.RemoveAll(e => e.Leaked);
            if (tAir < 0 && live.Any(e => e.A.Fly && Towers.Any(tw => tw.D.Air && tw.D.Power > 0 && InRange(tw, e)))) tAir = t;
            // 塔
            foreach (var tw in Towers)
            {
                var d = tw.D;
                if (d.Type == 3)
                {
                    tw.Timer += Dt;
                    while (tw.Timer >= d.Cd) { tw.Timer -= d.Cd; foreach (var e in live) if (!e.Dead && InRange(tw, e)) { if (d.Slow > e.SlowR || e.SlowT <= 0) { e.SlowR = d.Slow; e.SlowT = d.Cd + 0.1; } else if (Math.Abs(d.Slow - e.SlowR) < 1e-9) e.SlowT = Math.Max(e.SlowT, d.Cd + 0.1); } }
                    continue;
                }
                if (tw.Tgt != null && (tw.Tgt.Dead || tw.Tgt.Leaked || !InRange(tw, tw.Tgt))) tw.Tgt = null;
                if (d.Air && tw.Tgt != null && !tw.Tgt.A.Fly && live.Any(e => e.A.Fly && !e.Dead && InRange(tw, e))) tw.Tgt = null;
                tw.Tgt ??= Pick(tw, live);
                if (tw.Tgt == null) continue;
                tw.Timer += Dt;
                while (tw.Timer >= d.Cd && tw.Tgt != null)
                {
                    tw.Timer -= d.Cd; double p = d.Power * FireScale;
                    if (d.Type == 1) Hit(tw.Tgt, p * (tw.Tgt.A.Fly ? d.AirMul : 1), t);
                    else { double cx = tw.Tgt.X, cy = tw.Tgt.Y; foreach (var e in live) if (!e.A.Fly && !e.Dead && (e.X - cx) * (e.X - cx) + (e.Y - cy) * (e.Y - cy) <= d.Splash * d.Splash) Hit(e, p, t); }
                    if (tw.Tgt.Dead) tw.Tgt = Pick(tw, live);
                }
            }
            live.RemoveAll(e => e.Dead);
            t += Dt;
            if (si >= order.Count && live.Count == 0) break;
        }
        int leaks = all.Count(e => e.Leaked), leakHp = all.Where(e => e.Leaked).Sum(e => e.A.Leak);
        double minRem = all.Where(e => e.Dead).Select(e => e.DieRemain).DefaultIfEmpty(1).Min();
        return new Result(leaks, leakHp, t, minRem, tAir, all, Gold);
    }

    int NextCell(int c) { int best = -1, bd = int.MaxValue; foreach (var n in M.Nb(c)) if (M.Free[n] && !Wall[n] && Dist[n] < bd) { bd = Dist[n]; best = n; } return best; }
    bool InRange(Tw tw, En e) { double dx = M.Cx(tw.Cell) - e.X, dy = M.Cy(tw.Cell) - e.Y; return dx * dx + dy * dy <= tw.D.Range * tw.D.Range; }
    double Remain(En e) => e.A.Fly ? Math.Sqrt(Math.Pow(M.AirTo[0] - e.X, 2) + Math.Pow(M.AirTo[1] - e.Y, 2)) : (e.Next >= 0 && Dist[e.Next] != int.MaxValue ? Dist[e.Next] + Math.Sqrt(Math.Pow(M.Cx(e.Next) - e.X, 2) + Math.Pow(M.Cy(e.Next) - e.Y, 2)) : Dist[e.Cell]);
    En? Pick(Tw tw, List<En> live)
    {
        En? best = null; double br = double.MaxValue; bool air = tw.D.Air;
        if (air) foreach (var e in live) if (e.A.Fly && !e.Dead && InRange(tw, e)) { double r = Remain(e); if (r < br) { br = r; best = e; } }
        if (best != null) return best;
        foreach (var e in live) if (!e.Dead && (!e.A.Fly) && InRange(tw, e)) { double r = Remain(e); if (r < br) { br = r; best = e; } }
        return best;
    }
    void Hit(En e, double p, double t)
    {
        if (e.Dead) return; e.Hp -= p * (1 - e.A.Armor);
        if (e.Hp <= 1e-9) { e.Dead = true; Gold += e.Bounty; double total = e.A.Fly ? M.AirLen : PathLen; e.DieRemain = Math.Min(1, Remain(e) / Math.Max(1, total)); }
    }
}
