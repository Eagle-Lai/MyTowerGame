// 逐关设计 V2.3（2026-11-15 用户实测 L01 至 W20 后重做）：
//   参照解 = 玩家常见打法（绕路墙以单体为主、拐角放范围、U 形掉头处放减速；升级预算 30% 给航线单体、70% 给地面火力）
//   每波空地比例固定：W1–W4 无空中；W5 起空中占等效血量 25%（轻）/ 35%（中）/ 30%（困难波）
//   困难波 = 所需火力 +15%（同构成 + 1 只精英，W25 为首领）；取消「必须提前设防」
//   怪数约 2.5 倍、速度 S1 1.0 → S5 1.3 格/s；出怪间隔随当前路径长度自适应，单波 30–60 s；总时长不强制
public class WaveOut
{
    public int W; public bool Hard; public List<string> Dims = new(); public List<Spawn> Spawns = new();
    public Dictionary<string, int> Counts = new(); public Dictionary<string, double> Hp = new(); public Dictionary<string, double> Bounty = new();
    public double GroundScale, AirScale, GroundScaleMax, AirScaleMax; public int RewardOnClear;
    public double GoldAtStart, BountyTotal, Duration, MinRemainFrac; public int Leaks, PathLenStart, PathLenEnd, TowersStart, TowersEnd;
    public double MaxSafeDelay; public double D1, D2, D3, D4, D;
    public double FireScale; public int LeaksAtMargin, LeaksBelowMargin; public string AirTierName = "";
    public double AirShareTarget, AirShareActual, GroundHpTotal, AirHpTotal, AirPassDmg, AirHpPerUnit, AirHpToPass, SpawnSpan; public int AirCoverTowers, EnemyCount;
    public bool MustPreDefend; public int Reserve, LeaksWithoutPreDefend; public List<string> PreDefendActions = new();   // V2.3 已取消，字段保留兼容报表
    public List<string> Builds = new();
}
public class LevelOut
{
    public string Level = ""; public int Stage, Lives; public string AirSpawn = ""; public double AirLen; public int LongestPath, WallCount, OptionalSlots;
    public double GroundSpeed, AirSpeed = Designer.Va; public double TotalSeconds, CombatSeconds; public int TotalCost; public double IncomePerWave, Rho = 0.5;
    public double Margin, HardMargin, CountMul = Designer.CountMul, ReactionDelay = Designer.Reaction; public bool AltOpeningApplies = true; public int OpeningAltLeaks = -1; public List<string> OpeningAlt = new();
    public double DLevel, DPeak, DHardMean; public List<string> QueueText = new(); public List<WaveOut> Waves = new();
    public Dictionary<string, int> TypeCount = new();
    public int AirCoverCells; public double AirCoverChordSum, AirMaxPassDmg; public int AirSinglesL3End, AirSlowEnd, AirAoeEnd, QueueLeftEnd;
    public int AirBudgetSpent, GroundBudgetSpent;
}

public static class Designer
{
    public const double Kappa = 2.2, Rho = 0.5, Va = 1.0, Reaction = 3.0, CountMul = 2.5, HardBoost = 1.15, AirBudgetShare = 0.30;
    public static readonly double[] MarginOf = { 0, 0.30, 0.26, 0.22, 0.18, 0.15 };
    public static readonly double[] SpeedOf = { 0, 1.0, 1.08, 1.15, 1.22, 1.3 };
    public const double WaveMin = 30, WaveMax = 60, SpawnPer = 0.7, SpanMin = 29, SpanMax = 40;

    // 空中档：每 4 个普通波里中压个数 S1 1 → S5 3（优先困难波前一波 k=4，其次 k=1、k=3）；轻 25% / 中 35% / 困难 30%
    public static int AirTier(int s, int w) { if (w < 5) return -1; if (w % 5 == 0) return 0; int k = w % 5; int m = new[] { 0, 1, 1, 2, 2, 3 }[s]; int[] pref = { 4, 1, 3, 2 }; return Array.IndexOf(pref, k) < m ? 2 : 1; }
    public static double AirShareOf(int s, int w) => AirTier(s, w) switch { -1 => 0, 0 => 0.30, 1 => 0.25, _ => 0.35 };
    static string TierName(int s, int w) => AirTier(s, w) switch { -1 => "", 0 => "困难 30%", 1 => "轻 25%", _ => "中 35%" };

    public static LevelOut Run(MapIn m)
    {
        int lvNo = int.Parse(m.Level[1..]); int stage = (lvNo - 1) / 6 + 1;
        var map = new MapG(m);
        var queue = Plan(map, stage, out int walls, out int optional, out var typeCount, out var altOpening, out int airSpent, out int groundSpent);
        var lv = Calibrate(m, map, stage, queue, SpeedOf[stage], altOpening);
        lv.WallCount = walls; lv.OptionalSlots = optional; lv.TypeCount = typeCount; lv.AirBudgetSpent = airSpent; lv.GroundBudgetSpent = groundSpent;
        OpeningCheck(map, lv, queue, altOpening);
        return lv;
    }

    static void OpeningCheck(MapG M, LevelOut lv, List<Act> queue, List<int> altOpening)
    {
        var alt = altOpening.Select(c => new Act(c, 1, false, 1, TowerDef.Of(1, 1).Cost, "开局替代位")).ToList();
        var q = alt.Concat(queue.Where(a => a.Upgrade || !altOpening.Contains(a.Cell))).ToList();
        var sim = new Sim(M, q) { Gold = 100, BuildDelay = Reaction }; sim.BuildAll(0, 0, "开局替代");
        int leaks = 0;
        foreach (var w in lv.Waves.Take(3))
        {
            var r = sim.RunWave(w.W, w.Spawns, a => w.Hp[a.Id], a => Math.Round((a.Fly ? Va : lv.GroundSpeed) * a.Spd, 3), a => w.Bounty[a.Id]);
            leaks += r.Leaks; sim.Gold += w.RewardOnClear; sim.BuildAll(w.W, 0, "替代");
        }
        lv.OpeningAltLeaks = leaks; lv.OpeningAlt = altOpening.Select(c => $"({c % M.W},{c / M.W})").ToList();
    }

    // ------------------------------------------------------------ 参照解：玩家常见打法
    public static List<Act> Plan(MapG M, int stage, out int wallCount, out int optionalCount, out Dictionary<string, int> typeCount, out List<int> altOpening, out int airSpentOut, out int groundSpentOut, int upBudgetFixed = -1)
    {
        var pathIdx = new Dictionary<int, int>(); for (int i = 0; i < M.FinalPath.Count; i++) pathIdx[M.FinalPath[i]] = i;
        var free = Enumerable.Range(0, M.W * M.H).Where(i => M.Free[i] && i != M.S && i != M.E && !M.PathSet.Contains(i)).ToList();
        var walls = free.Where(c => M.Nb(c).Any(n => M.PathSet.Contains(n))).OrderBy(c => M.Nb(c).Where(n => pathIdx.ContainsKey(n)).Min(n => pathIdx[n])).ThenBy(c => c).ToList();
        var optional = free.Except(walls).ToList();
        List<int> Opening(IEnumerable<int> exclude)
        {   // 逐座贪心覆盖「当前所有最短路」，按层宽加权
            var wl = new bool[M.W * M.H]; var pick = new List<int>(); var ex = exclude.ToHashSet();
            for (int k = 0; k < 5; k++)
            {
                var dE = M.Bfs(wl); var dS = Enumerable.Repeat(int.MaxValue, M.W * M.H).ToArray(); var qq = new Queue<int>(); dS[M.S] = 0; qq.Enqueue(M.S);
                while (qq.Count > 0) { int u = qq.Dequeue(); foreach (var v in M.Nb(u)) if (M.Free[v] && !wl[v] && dS[v] == int.MaxValue) { dS[v] = dS[u] + 1; qq.Enqueue(v); } }
                int L0 = dE[M.S]; var sp = Enumerable.Range(0, M.W * M.H).Where(i => dS[i] != int.MaxValue && dE[i] != int.MaxValue && dS[i] + dE[i] == L0).ToList();
                var layer = sp.GroupBy(i => dS[i]).ToDictionary(g => g.Key, g => g.Count());
                var c = walls.Where(x => !pick.Contains(x) && !ex.Contains(x)).OrderByDescending(x => sp.Sum(p => Math.Pow(M.Cx(p) - M.Cx(x), 2) + Math.Pow(M.Cy(p) - M.Cy(x), 2) <= 4.0 ? 1.0 / layer[dS[p]] : 0)).ThenBy(x => walls.IndexOf(x)).First();
                pick.Add(c); wl[c] = true;
            }
            return pick;
        }
        var opening = Opening(Array.Empty<int>()); altOpening = Opening(opening);
        walls = opening.Concat(walls.Except(opening)).ToList();
        wallCount = walls.Count; optionalCount = optional.Count;
        double D2(int a, int b) => Math.Pow(M.Cx(a) - M.Cx(b), 2) + Math.Pow(M.Cy(a) - M.Cy(b), 2);
        double CovG(int c, double r) => M.FinalPath.Count(p => D2(p, c) <= r * r);
        double CovA(int c, double r) => M.AirChord(c, r);
        int Overlap(int a, int b, double ra, double rb) => M.FinalPath.Count(p => D2(p, a) <= ra * ra && D2(p, b) <= rb * rb);
        int PathNb(int c) => M.Nb(c).Count(n => M.PathSet.Contains(n));

        // 塔型（玩家常见打法）：
        //   范围塔 = 拐角：被路径从两侧以上包住的墙格（四邻里 ≥2 格是路径），按覆盖路径格数取前若干
        //   减速塔 = 路口：U 形掉头的尖端（四邻里 ≥3 格是路径）优先，其次火力重叠最大的拐角；互相隔开
        var type = walls.ToDictionary(c => c, c => 1);
        int nAoe = (int)Math.Round(walls.Count * new[] { 0, 0.12, 0.15, 0.18, 0.18, 0.18 }[stage]);
        int nSlow = (int)Math.Round(walls.Count * new[] { 0, 0.05, 0.06, 0.08, 0.08, 0.08 }[stage]);
        var cand = walls.Skip(5).ToList();
        foreach (var c in cand.Where(c => PathNb(c) >= 2).OrderByDescending(c => CovG(c, 1.5)).ThenByDescending(c => CovG(c, 2.0)).ThenBy(c => c).Take(nAoe)) type[c] = 2;
        var slows = new List<int>();
        foreach (var c in cand.Where(c => type[c] == 1).OrderByDescending(c => PathNb(c) >= 3 ? 1 : 0).ThenByDescending(c => walls.Where(t => t != c).Sum(t => Overlap(c, t, 2.0, 2.0))).ThenBy(c => c))
        { if (slows.Count >= nSlow) break; if (slows.Any(x => Math.Abs(x % M.W - c % M.W) + Math.Abs(x / M.W - c / M.W) <= 2)) continue; slows.Add(c); type[c] = 3; }

        var q = new List<Act>();
        foreach (var c in walls) q.Add(new Act(c, type[c], false, 1, TowerDef.Of(type[c], 1).Cost, "绕路墙#" + (q.Count + 1)));
        int wallCost = q.Sum(a => a.Cost); int upBudget = upBudgetFixed >= 0 ? upBudgetFixed : (int)Math.Round(wallCost * Kappa) - wallCost;
        int airBudget = (int)Math.Round(upBudget * AirBudgetShare), groundBudget = upBudget - airBudget;

        // 升级/补建分两池：航线池 = 射程覆盖空中航线的单体（升级或可选位新建）；地面池 = 其余。
        // 每步选「花费占本池预算比例更低」的池，池内按单位金币增伤取最优 —— 两条线同步成长。
        var lv = walls.ToDictionary(c => c, c => 1); var tp = new Dictionary<int, int>(type);
        double kc = 2.0;   // 2.5 倍怪数下地面更密，范围塔按 2 只同时命中计
        bool IsAir(int c, int t, int toLv) => t == 1 && CovA(c, TowerDef.Of(1, toLv).Range) > 0;
        double Score(int c, int t, int toLv, bool airPool)
        {
            var a = TowerDef.Of(t, toLv); var b = toLv > 1 ? TowerDef.Of(t, toLv - 1) : null; double dd = a.Dps - (b?.Dps ?? 0);
            if (t == 1) return dd * (airPool ? CovA(c, a.Range) : CovG(c, a.Range)) / a.Cost;
            if (t == 2) return dd * CovG(c, a.Range) * kc / a.Cost;
            double g(double s) => s / (1 - s); double cov = Math.Max(1, CovG(c, a.Range));
            double X = lv.Where(kv => kv.Key != c && tp[kv.Key] != 3).Sum(kv => TowerDef.Of(tp[kv.Key], Math.Max(2, kv.Value)).Dps * Overlap(c, kv.Key, a.Range, TowerDef.Of(tp[kv.Key], kv.Value).Range)) / cov;
            return X * (g(a.Slow) - g(b?.Slow ?? 0)) / a.Cost;
        }
        int airSpent = 0, groundSpent = 0;
        while (true)
        {
            (double s, Act a)? bestAir = null, bestGround = null;
            void Consider(int c, int t, int toLv, bool upg)
            {
                int cst = TowerDef.Of(t, toLv).Cost; bool air = IsAir(c, t, toLv);
                if (air ? airSpent + cst > airBudget : groundSpent + cst > groundBudget) return;
                double sc = Score(c, t, toLv, air); if (sc <= 0) return;
                var act = new Act(c, t, upg, toLv, cst, (air ? "航线" : "地面") + $" 增伤/金={sc:F2}");
                if (air) { if (bestAir == null || sc > bestAir.Value.s) bestAir = (sc, act); } else { if (bestGround == null || sc > bestGround.Value.s) bestGround = (sc, act); }
            }
            foreach (var kv in lv) if (kv.Value < 3) Consider(kv.Key, tp[kv.Key], kv.Value + 1, true);
            foreach (var c in optional) if (!lv.ContainsKey(c)) { Consider(c, 1, 1, false); if (CovA(c, 2.0) == 0) Consider(c, 2, 1, false); }
            if (bestAir == null && bestGround == null) break;
            bool pickAir = bestGround == null || (bestAir != null && (double)airSpent / Math.Max(1, airBudget) <= (double)groundSpent / Math.Max(1, groundBudget));
            var act2 = pickAir ? bestAir!.Value.a : bestGround!.Value.a;
            q.Add(act2); if (pickAir) airSpent += act2.Cost; else groundSpent += act2.Cost;
            if (act2.Upgrade) lv[act2.Cell] = act2.ToLv; else { lv[act2.Cell] = 1; tp[act2.Cell] = act2.Type; }
        }
        typeCount = lv.GroupBy(kv => $"{Sim.Name(tp[kv.Key])}{kv.Value}级").ToDictionary(g => g.Key, g => g.Count());
        airSpentOut = airSpent; groundSpentOut = groundSpent;
        return q;
    }

    // ------------------------------------------------------------ 出怪构成（相对间隔；实际间隔在校准时按目标时长缩放）
    static (List<(string a, double rel)> seq, List<string> dims) Compose(int s, int w, double airLen)
    {
        bool hard = w % 5 == 0; int k = w % 5; int n = (int)Math.Round((6 + w / 2) * CountMul);
        var ground = new List<(string a, double rel)>(); var air = new List<string>();
        void G(string a, int cnt, double rel) { for (int i = 0; i < cnt; i++) ground.Add((a, rel)); }
        // 阶段维度：S2 集群 / S3 高速 / S4 装甲；普通波按 k 轮换主题，困难波把本阶段已解锁的维度各放一点（同构成）
        void Mix(bool all)
        {
            bool cl = s >= 2 && (all || k == 2 || k == 4), sp = s >= 3 && (all || k == 3), ar = s >= 4 && (all || (k == 1 && w > 1));
            int parts = 1 + (cl ? 1 : 0) + (sp ? 1 : 0) + (ar ? 1 : 0);
            int gN = n / parts; G("G1", n - gN * (parts - 1), 1.0);
            if (cl) G("G2", (int)(gN * 2.2), 0.4); if (sp) G("G3", gN, 0.8); if (ar) G("G4", Math.Max(1, gN / 2), 1.4);
        }
        Mix(hard);
        if (hard) ground.Insert((int)(ground.Count * 0.6), (w == 25 ? "B" : "E", 2.0));   // 精英/首领放在约 60% 处，不拖长尾巴
        if (w >= 5)
        {   // 空中只数：约占总只数 15%，按航程缩放（航程短 → 只数少、单只更硬）；S4+ 中/困难波夹 1–2 只重型
            int na = Math.Max(2, (int)Math.Round(ground.Count * 0.15 * Math.Clamp(airLen / 10.0, 0.6, 1.4)));
            int heavy = s >= 4 && AirTier(s, w) != 1 ? s - 3 : 0;
            for (int i = 0; i < na - heavy; i++) air.Add("A1"); for (int i = 0; i < heavy; i++) air.Add("A2");
        }
        // 空中均匀穿插（压力平稳），保证不相邻、首尾为地面
        var seq = new List<(string a, double rel)>();
        if (air.Count > 0)
        {
            while (ground.Count < air.Count + 2) ground.Add(("G1", 1.0));
            double step = (double)(ground.Count - 1) / air.Count; var after = new HashSet<int>();
            for (int i = 0; i < air.Count; i++) after.Add(Math.Min(ground.Count - 2, (int)Math.Floor(step * (i + 0.5))));
            int ai = 0; for (int gi = 0; gi < ground.Count; gi++) { seq.Add(ground[gi]); if (after.Contains(gi) && ai < air.Count) seq.Add((air[ai++], 1.0)); }
            while (ai < air.Count) throw new Exception($"空中插入不足 W{w}");
        }
        else seq.AddRange(ground);
        for (int i = 1; i < seq.Count; i++) if (Arche.All[seq[i].a].Fly && Arche.All[seq[i - 1].a].Fly) throw new Exception($"空中相邻 W{w}");
        if (Arche.All[seq[0].a].Fly || Arche.All[seq[^1].a].Fly) throw new Exception($"空中在首尾 W{w}");
        var dims = new List<string>();
        if (ground.Any(x => x.a == "G2")) dims.Add("集群"); if (ground.Any(x => x.a == "G3")) dims.Add("高速");
        if (ground.Any(x => x.a == "G4") || air.Contains("A2")) dims.Add("装甲"); if (air.Count > 0) dims.Add("空中");
        if (hard) dims.Add(w == 25 ? "首领" : "精英");
        return (seq, dims);
    }

    static List<Spawn> Timeline(List<(string a, double rel)> seq, double span)
    {
        double relSum = seq.Take(seq.Count - 1).Sum(x => x.rel); double f = relSum > 0 ? span / relSum : 1;
        var sp = new List<Spawn>(); double t = 0;
        foreach (var (a, rel) in seq) { double g = Math.Round(Math.Max(0.15, rel * f), 3); sp.Add(new Spawn(a, t, g)); t += g; }
        return sp;
    }

    // ------------------------------------------------------------ 逐波校准
    static LevelOut Calibrate(MapIn m, MapG M, int stage, List<Act> queue, double vg, List<int> altOpening)
    {
        int lvNo = int.Parse(m.Level[1..]);
        var lv = new LevelOut { AltOpeningApplies = true, Level = m.Level, Stage = stage, Lives = lvNo <= 2 ? 10 : 12, AirSpawn = M.AirSpawnRule, AirLen = Math.Round(M.AirLen, 2), LongestPath = m.LongestCells, GroundSpeed = Math.Round(vg, 3), AirSpeed = Va };
        double margin = MarginOf[stage]; double fsN = 1 - margin, fsH = Math.Min(1.0, fsN * HardBoost);
        lv.Margin = margin; lv.HardMargin = Math.Round(1 - fsH, 3);
        int C = queue.Sum(a => a.Cost); lv.TotalCost = C;
        double I = (C - 100 + 5) / (25 * Rho + 24 * (1 - Rho)); lv.IncomePerWave = Math.Round(I, 2);   // +5 金取整余量
        lv.QueueText = queue.Select((a, i) => $"{i + 1}. {(a.Upgrade ? "升级" : "建造")} ({a.Cell % M.W},{a.Cell / M.W}) {Sim.Name(a.Type)}{a.ToLv}级 {a.Cost}金 [{a.Why}]").ToList();
        {   var cells = Enumerable.Range(0, M.W * M.H).Where(i => M.Free[i] && i != M.S && i != M.E && !M.PathSet.Contains(i) && M.AirChord(i, TowerDef.Of(1, 3).Range) > 0).ToList();
            lv.AirCoverCells = cells.Count; lv.AirCoverChordSum = Math.Round(cells.Sum(c => M.AirChord(c, TowerDef.Of(1, 3).Range)), 2);
            lv.AirMaxPassDmg = Math.Round(cells.Sum(c => TowerDef.Of(1, 3).Dps * M.AirChord(c, TowerDef.Of(1, 3).Range) / Va), 0); }
        var sim = new Sim(M, new List<Act>(queue)) { Gold = 100, BuildDelay = Reaction }; sim.BuildAll(0, 0, "开局");
        var altQ = altOpening.Select(c => new Act(c, 1, false, 1, TowerDef.Of(1, 1).Cost, "开局替代位")).Concat(queue.Where(a => a.Upgrade || !altOpening.Contains(a.Cell))).ToList();
        var simAlt = new Sim(M, altQ) { Gold = 100, BuildDelay = Reaction }; simAlt.BuildAll(0, 0, "开局替代");
        bool altFeasible;
        { var (s1, _) = Compose(stage, 1, M.AirLen); var t1 = simAlt.Clone(); t1.FireScale = fsN; altFeasible = t1.RunWave(1, Timeline(s1, 20), a => 1.0 * a.Hp, a => Math.Round(vg * a.Spd, 3), a => 0).Leaks == 0; }
        lv.AltOpeningApplies = altFeasible;
        double prevG = 5; double total = 0;
        for (int w = 1; w <= 25; w++)
        {
            var (seq, dims) = Compose(stage, w, M.AirLen);
            // 出怪跨度 = 只数 × 0.7 s，W4 起限 29–40 s（怪成串而不成团）；标定后测满伤害时长，不在 30–60 s 就调跨度重标（最多 3 轮）
            double span = w <= 3 ? Math.Clamp(seq.Count * SpawnPer, 15, SpanMax) : Math.Clamp(seq.Count * SpawnPer, SpanMin, SpanMax);
            List<Spawn> spawns = null!; WaveOut wo = null!; double hgMax = 0, hg = 0, r = AirShareOf(stage, w), fs = 0, bountyW = Rho * I;
            Func<Arche, double> bountyOf = null!, spdOf = a => Math.Round((a.Fly ? Va : vg) * a.Spd, 3); Func<double, double> haOf = null!;
            bool early = w <= 3 && altFeasible;
            for (int fit = 0; fit < 3; fit++)
            {
                spawns = Timeline(seq, span);
                wo = new WaveOut { W = w, Hard = w % 5 == 0, Dims = dims, Spawns = spawns, SpawnSpan = Math.Round(spawns[^1].T, 1), EnemyCount = spawns.Count };
                wo.Counts = spawns.GroupBy(s => s.Arche).ToDictionary(g => g.Key, g => g.Count());
                double hpeSum = spawns.Sum(s => Arche.All[s.Arche].HpeMult);
                bountyOf = a => Math.Round(bountyW * a.HpeMult / hpeSum, 3);
                wo.AirShareTarget = r; wo.AirTierName = TierName(stage, w);
                // 空地按固定比例绑定：空中等效总血 = r/(1−r) × 地面等效总血
                double gHpe = spawns.Where(s => !Arche.All[s.Arche].Fly).Sum(s => Arche.All[s.Arche].HpeMult), aHpe = spawns.Where(s => Arche.All[s.Arche].Fly).Sum(s => Arche.All[s.Arche].HpeMult);
                haOf = h => aHpe > 0 ? h * gHpe * r / (1 - r) / aHpe : 0;
                fs = wo.Hard ? fsH : fsN; wo.FireScale = Math.Round(fs, 3);
                var sp2 = spawns; var bo2 = bountyOf; var ha2 = haOf; double fs2 = fs;
                Func<double, int> run = h =>
                {
                    double ha = ha2(h);
                    var c = sim.Clone(); c.FireScale = fs2; var rr = c.RunWave(w, sp2, a => HpQ(a, h, ha), spdOf, bo2);
                    if (rr.Leaks == 0 && early) { var c2 = simAlt.Clone(); c2.FireScale = fs2; rr = c2.RunWave(w, sp2, a => HpQ(a, h, ha), spdOf, bo2); }
                    if (rr.Leaks == 0) { rr = sim.Clone().RunWave(w, sp2, a => HpQ(a, h, ha), spdOf, bo2); }   // 满伤害也须零漏
                    return rr.Leaks;
                };
                hgMax = MaxScale(h => run(h) == 0, prevG); hg = hgMax;
                for (int guard = 0; guard < 40 && run(hg) > 0; guard++) hg *= 0.97;
                if (w <= 3) break;
                double hgC = hg, haC = haOf(hg);
                double dur = sim.Clone().RunWave(w, spawns, a => HpQ(a, hgC, haC), spdOf, bountyOf).Duration;
                if (dur > WaveMax - 1 && span > 12) span = Math.Max(12, span - (dur - (WaveMax - 4)));
                else if (dur < WaveMin && span < 50) span = Math.Min(50, span + (WaveMin + 2 - dur));
                else break;
            }
            double haF = haOf(hg); prevG = hg;
            wo.GroundScaleMax = Math.Round(hgMax, 3); wo.GroundScale = Math.Round(hg, 3); wo.AirScale = Math.Round(haF, 3); wo.AirScaleMax = wo.AirScale;
            foreach (var a in wo.Counts.Keys) { var A = Arche.All[a]; wo.Hp[a] = HpQ(A, hg, haF); wo.Bounty[a] = Math.Round(bountyOf(A), 3); }
            wo.GroundHpTotal = Math.Round(wo.Counts.Where(kv => !Arche.All[kv.Key].Fly).Sum(kv => kv.Value * wo.Hp[kv.Key] / (1 - Arche.All[kv.Key].Armor)), 1);
            wo.AirHpTotal = Math.Round(wo.Counts.Where(kv => Arche.All[kv.Key].Fly).Sum(kv => kv.Value * wo.Hp[kv.Key] / (1 - Arche.All[kv.Key].Armor)), 1);
            wo.AirShareActual = wo.AirHpTotal + wo.GroundHpTotal > 0 ? Math.Round(wo.AirHpTotal / (wo.AirHpTotal + wo.GroundHpTotal), 3) : 0;
            { var c = sim.Clone(); c.FireScale = fs; wo.LeaksAtMargin = c.RunWave(w, spawns, a => HpQ(a, hg, haF), spdOf, bountyOf).Leaks; }
            { var c = sim.Clone(); c.FireScale = fs - 0.10; wo.LeaksBelowMargin = c.RunWave(w, spawns, a => HpQ(a, hg, haF), spdOf, bountyOf).Leaks; }
            wo.MaxSafeDelay = 16;
            foreach (var d in new[] { 1.0, 2, 4, 8, 16 }) { var ds = sim.Clone(); ds.BuildDelay = Reaction + d; if (ds.RunWave(w, spawns, a => HpQ(a, hg, haF), spdOf, bountyOf).Leaks > 0) { wo.MaxSafeDelay = d / 2; break; } }
            { var cov = sim.Towers.Where(t => t.D.Air && t.D.Power > 0 && M.AirChord(t.Cell, t.D.Range) > 0).ToList(); wo.AirCoverTowers = cov.Count;
              wo.AirPassDmg = Math.Round(cov.Sum(t => t.D.Dps * M.AirChord(t.Cell, t.D.Range) / Va), 1);
              var airA = wo.Counts.Keys.Where(a => Arche.All[a].Fly).ToList();
              wo.AirHpPerUnit = airA.Count == 0 ? 0 : Math.Round(airA.Max(a => wo.Hp[a] / (1 - Arche.All[a].Armor)), 1);
              wo.AirHpToPass = wo.AirPassDmg > 0 ? Math.Round(wo.AirHpPerUnit / wo.AirPassDmg, 3) : 0; }
            wo.GoldAtStart = Math.Round(sim.Gold, 1); wo.PathLenStart = sim.PathLen; wo.TowersStart = sim.QIdx;
            var res = sim.RunWave(w, spawns, a => HpQ(a, hg, haF), spdOf, bountyOf);
            wo.Builds = sim.Log.ToList(); sim.Log.Clear();
            wo.Leaks = res.Leaks; wo.Duration = Math.Round(res.Duration, 1); wo.MinRemainFrac = Math.Round(res.MinRemainFrac, 3); wo.BountyTotal = Math.Round(bountyW, 1);
            wo.RewardOnClear = w < 25 ? (int)Math.Ceiling((1 - Rho) * I) : 0;
            if (early) { simAlt.RunWave(w, spawns, a => HpQ(a, hg, haF), spdOf, bountyOf); simAlt.Gold += wo.RewardOnClear; simAlt.BuildAll(w, 0, "替代"); }
            sim.Gold += wo.RewardOnClear; sim.BuildAll(w, 0, $"W{w}后");
            wo.Builds.AddRange(sim.Log); sim.Log.Clear();
            wo.PathLenEnd = sim.PathLen; wo.TowersEnd = sim.QIdx;
            // 难度刻度 V2.3：维度数 / 空中占比 / 时序窗口 / 剩余路程
            wo.D1 = dims.Count / 5.0; wo.D2 = r / 0.35; wo.D3 = 1 - wo.MaxSafeDelay / 16.0; wo.D4 = 1 - Math.Min(1, wo.MinRemainFrac / 0.5);
            wo.D = 25 * (wo.D1 + wo.D2 + wo.D3 + wo.D4);
            lv.Waves.Add(wo); total += res.Duration;
        }
        lv.CombatSeconds = Math.Round(total, 0); lv.TotalSeconds = Math.Round(total + 24 * 10, 0);
        { var onLine = sim.Towers.Where(t => M.AirChord(t.Cell, TowerDef.Of(1, 3).Range) > 0).ToList(); lv.AirSinglesL3End = onLine.Count(t => t.Type == 1 && t.Lv == 3); lv.AirSlowEnd = onLine.Count(t => t.Type == 3); lv.AirAoeEnd = onLine.Count(t => t.Type == 2); lv.QueueLeftEnd = sim.Queue.Count - sim.QIdx; }
        lv.DLevel = Math.Round(lv.Waves.Average(w => w.D), 2); lv.DPeak = Math.Round(lv.Waves.Max(w => w.D), 2); lv.DHardMean = Math.Round(lv.Waves.Where(w => w.Hard).Average(w => w.D), 2);
        return lv;
    }

    public static double HpQ(Arche a, double hg, double ha) => Math.Floor((a.Fly ? ha : hg) * a.Hp * 10) / 10;

    static double MaxScale(Func<double, bool> ok, double guess)
    {
        double lo = 0, hi = Math.Max(1, guess * 1.5);
        while (ok(hi) && hi < 1e6) { lo = hi; hi *= 2; }
        for (int i = 0; i < 14 && hi - lo > Math.Max(0.05, lo * 0.01); i++) { double mid = (lo + hi) / 2; if (ok(mid)) lo = mid; else hi = mid; }
        return lo;
    }
}
