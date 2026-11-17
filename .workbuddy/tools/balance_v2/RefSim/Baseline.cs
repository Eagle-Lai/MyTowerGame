// V3「以定稿 L01 为唯一基准」（用户 2026-11-16）：
//   · 塔、子弹、卖塔规则 = git tag「L01关卡数值定稿！！！」原值，30 关通用；L01 整关恢复 tag 原样
//   · 其余 29 关：出怪序列、只数、间隔、速度、护甲、漏怪扣血、波型与 L01 完全相同（逐只一一对应）
//   · 只按地图换算两样东西：
//       ① 经济系数 k = 本图参照迷宫墙体造价 / L01 参照迷宫墙体造价；赏金 ×k、清波奖励 ×k，
//         开局 100 金的相对差（100k−100）摊进 W1–W4 奖励（AGENTS：initialGold 恒 100）
//       ② 血量：同一参照打法（玩家常见阵型 + 3 s 反应）在 L01 与本图上逐波测「零漏上限」：
//            地面系数 = 本图地面上限 / L01 地面上限；空中系数 = 本图空中上限 / L01 空中上限；
//            再测合并上限，统一修正使「定稿血量 ÷ 合并上限」与 L01 同波完全一致 —— 这就是「强度一致」
//   · 怪物外观：每关从工程 119 个敌人预制体中按角色挑选一套（表 Looks），L01 保持 tag 原外观
using System.Text.Json;

public static class Baseline
{
    public const int TemplateStage = 3;              // 统一阵型模板：拐角 18% 范围、U 形尖端 8% 减速（与关卡编号无关）
    public const double Reaction = 3.0;
    static readonly string[] Roles = { "normal", "swarm", "medium", "heavy", "elite", "air" };

    // 每关外观（normal, swarm, medium, heavy, elite, air）；全部取自 Assets/Prefabs/Enemy
    public static readonly Dictionary<int, string[]> Looks = new()
    {
        [1] = new[] { "Chicken", "Larva", "Crawler", "Scarab", "Rat", "Bat" },
        [2] = new[] { "Chick", "Caterpillar", "Hen", "PurpleScarab", "Pig", "EvilEye" },
        [3] = new[] { "Duck", "MeatBug", "Goose", "Ox", "Bull", "MohawkBat" },
        [4] = new[] { "Rooster", "CaveCaterpillar", "Turkey", "Cow", "Bear", "DreadEye" },
        [5] = new[] { "Bunny", "Larva", "DarkBunny", "Ram", "Wolf", "Wasp" },
        [6] = new[] { "Piggy", "Chick", "Hog", "Boar", "RoyalBoar", "Bat" },
        [7] = new[] { "Rat", "MeatBug", "CaveRat", "Porcupine", "RatKing", "Ghost" },
        [8] = new[] { "Pug", "Caterpillar", "Husky", "Watchdog", "Cerberus", "MosquitoParasite" },
        [9] = new[] { "Sheep", "Larva", "Goat", "Burro", "Horse", "EvilEye" },
        [10] = new[] { "GreenParasite", "Crawler", "FancyParasite", "IceParasite", "VolcanoParasite", "Wasp" },
        [11] = new[] { "Monkey", "Chicken", "Pony", "Donkey", "Ogre", "MohawkBat" },
        [12] = new[] { "Hen", "SlugQueen", "Gobbler", "ForestTurkey", "Troll", "DreadEye" },
        [13] = new[] { "CaveRat", "Larva", "CrystalLizard", "InfectedRat", "Juggernaut", "FlyingDemon" },
        [14] = new[] { "Swine", "CaveCaterpillar", "Porky", "MinerBoar", "PirateBoar", "Bat" },
        [15] = new[] { "Wolf", "Crawler", "WolfHound", "Warg", "Tiger", "EvilEye" },
        [16] = new[] { "Panther", "Larva", "Lion", "SabretoothTiger", "BattlePanther", "Wasp" },
        [17] = new[] { "Scarab", "Caterpillar", "PurpleScarab", "ScarabMounted", "BugQueen", "MosquitoParasite" },
        [18] = new[] { "Cow", "Chick", "Sheep", "Ox", "BullMounted", "MohawkBat" },
        [19] = new[] { "Pig", "MeatBug", "Hog", "BlackBoar", "Butcher", "Ghost" },
        [20] = new[] { "Husky", "Larva", "Watchdog", "BlackWolf", "Nightmare", "DreadEye" },
        [21] = new[] { "Bunny", "Crawler", "DarkBunny", "Porcupine", "Mimic", "Bat" },
        [22] = new[] { "Rat", "SlugQueen", "CaveRat", "BlueScorpion", "RedScorpion", "FlyingDemon" },
        [23] = new[] { "WinterWolfTypeA", "Chick", "WinterWolfTypeB", "WinterBoar", "WinterOgre", "EvilEye" },
        [24] = new[] { "MechanicalParasiteTypeA", "Larva", "MechanicalParasiteTypeB", "IceParasite", "Dreadnought", "Wasp" },
        [25] = new[] { "Turkey", "Caterpillar", "WildRooster", "Goat", "BearMounted", "MosquitoParasite" },
        [26] = new[] { "PossessedRat", "MeatBug", "PossessedWatchdog", "PossessedBlackBoar", "PossessedBlackBear", "Ghost" },
        [27] = new[] { "Pony", "Chicken", "Horse", "Donkey", "Maneater", "MohawkBat" },
        [28] = new[] { "Monkey", "CaveCaterpillar", "MimicChest", "Mimic", "Punisher", "DreadEye" },
        [29] = new[] { "WhiteWolf", "Larva", "WinterWarg", "WinterBear", "Cannibal", "Bat" },
        [30] = new[] { "Drake", "SlugQueen", "AdvancedHen", "MossQueen", "Zombie", "FlyingDemon" },
    };

    public record BEnemy(int id, double speed, double hp, string name, int type, int interval, string resName, double armor, double reward, int damageToPlayer, double scale, double bodyRadius, int isFlying, string animController, string desc, int levelId, string role);
    public record BWave(int wave, int roundId, int groupId, int waveType, int rewardGold, double enemyIntervalMs, int groupInterval, List<int> sequence);
    public record BTower(int type, int level, double radius, double power, double CD, int prices, int sellPrice, double effectValue, int canAttackAir, double airDamageScale, double aoeRadius);
    public record BFile(string source, int initialGold, int initialHp, List<BTower> towers, List<BWave> waves, Dictionary<string, BEnemy> enemies);

    public class WaveRes
    {
        public int W, WaveType, Count, AirCount, Reward; public double GroundMul, AirMul, Fix;
        public double CapG, CapA, CapC, CapG01, CapA01, CapC01, Tight, Tight01, Duration, MinRemain; public int Leaks, LeaksAt01Tight;
        public double GroundHp, AirHp, Bounty; public int GoldStart, PathStart, Built;
    }
    public class LevelRes
    {
        public string Level = ""; public int Walls, WallCost, Built; public double K; public int LongestPath; public string AirSpawn = ""; public double AirLen;
        public List<string> Looks = new(); public Dictionary<string, int> Layout = new(); public List<WaveRes> Waves = new(); public double Seconds;
        public List<object> Enemies = new(); public List<object> Groups = new(); public List<int> Rewards = new();
    }

    static BFile B = null!;
    static Dictionary<int, BEnemy> E = new();

    public static void Run(string[] a)
    {
        string basePath = a.Length > 0 ? a[0] : "Docs/BalanceV2/baseline/tag_L01_baseline.json";
        string metrics = a.Length > 1 ? a[1] : "Docs/BalanceV2/map_metrics.json";
        string outDir = a.Length > 2 ? a[2] : "Docs/BalanceV2/v3";
        var only = a.Length > 3 ? a[3].Split(',').ToHashSet() : null;
        Directory.CreateDirectory(Path.Combine(outDir, "levels"));
        var opt = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
        B = JsonSerializer.Deserialize<BFile>(File.ReadAllText(basePath), opt)!;
        E = B.enemies.ToDictionary(kv => int.Parse(kv.Key), kv => kv.Value);
        // 塔 = tag 原值
        var T = new TowerDef[3, 3];
        foreach (var t in B.towers) T[t.type - 1, t.level - 1] = new TowerDef(t.type, t.level, t.prices, t.power, t.CD / 1000.0, t.radius, t.aoeRadius, t.type == 3 ? t.effectValue : 0, t.canAttackAir == 1, t.airDamageScale);
        TowerDef.T = T;
        // 每个 tag 怪物行登记成一个原型（血量/速度在模拟时按行取值）
        foreach (var e in E.Values) Arche.All["e" + e.id] = new Arche("e" + e.id, e.isFlying == 1, 1, 1, e.armor, e.damageToPlayer);

        var maps = JsonSerializer.Deserialize<List<MapIn>>(File.ReadAllText(metrics), opt)!.ToDictionary(m => m.Level);
        // L01 基准：参照阵型、经济、逐波上限
        var L01 = Measure(maps["L01"], 1.0, null);
        File.WriteAllText(Path.Combine(outDir, "levels", "L01.json"), JsonSerializer.Serialize(L01, Json.Opt));
        Console.WriteLine($"L01 walls={L01.Walls} wallCost={L01.WallCost} k=1 seconds={L01.Seconds:F0} leaks={L01.Waves.Sum(w => w.Leaks)}");
        var results = new System.Collections.Concurrent.ConcurrentBag<LevelRes> { L01 };
        Parallel.ForEach(maps.Keys.Where(k => k != "L01" && (only == null || only.Contains(k))).OrderBy(k => k), new ParallelOptions { MaxDegreeOfParallelism = Environment.ProcessorCount }, key =>
        {
            var sw = System.Diagnostics.Stopwatch.StartNew();
            var r = Measure(maps[key], 0, L01);
            File.WriteAllText(Path.Combine(outDir, "levels", key + ".json"), JsonSerializer.Serialize(r, Json.Opt));
            results.Add(r);
            Console.WriteLine($"{key} walls={r.Walls} k={r.K:F3} seconds={r.Seconds:F0} leaks={r.Waves.Sum(w => w.Leaks)} tightDiffMax={r.Waves.Max(w => Math.Abs(w.Tight - w.Tight01)):F3} gMul={r.Waves.Min(w => w.GroundMul):F2}-{r.Waves.Max(w => w.GroundMul):F2} aMul={r.Waves.Where(w => w.AirCount > 0).Select(w => w.AirMul).DefaultIfEmpty(0).Min():F2}-{r.Waves.Where(w => w.AirCount > 0).Select(w => w.AirMul).DefaultIfEmpty(0).Max():F2} ({sw.Elapsed.TotalSeconds:F0}s)");
        });
        var all = results.OrderBy(r => r.Level).ToList();
        if (only == null) File.WriteAllText(Path.Combine(outDir, "plan_v3.json"), JsonSerializer.Serialize(all.Select(r => new { level = int.Parse(r.Level[1..]), k = r.K, looks = r.Looks, rewards = r.Rewards, groups = r.Groups, enemies = r.Enemies }), Json.Opt));
        File.WriteAllText(Path.Combine(outDir, "summary_v3.json"), JsonSerializer.Serialize(all.Select(r => new { r.Level, r.Walls, r.WallCost, r.K, r.Seconds, r.Layout, leaks = r.Waves.Sum(w => w.Leaks), tight = r.Waves.Select(w => Math.Round(w.Tight, 3)), tight01 = r.Waves.Select(w => Math.Round(w.Tight01, 3)), gMul = r.Waves.Select(w => Math.Round(w.GroundMul, 3)), aMul = r.Waves.Select(w => Math.Round(w.AirMul, 3)) }), Json.Opt));
    }

    static List<Spawn> Spawns(BWave w) => w.sequence.Select((id, i) => new Spawn("e" + id, i * w.enemyIntervalMs / 1000.0, w.enemyIntervalMs / 1000.0)).ToList();

    // 合并上限：所有血量同乘 x 仍零漏的最大 x；地面/空中上限：另一侧压到 1% 时的最大 x
    static double Cap(Sim s, BWave w, Func<BEnemy, double> hp, double bk, int mode, double guess)
    {
        var sp = Spawns(w);
        bool Ok(double x) => s.Clone().RunWave(w.wave, sp, a => { var e = E[int.Parse(a.Id[1..])]; double m = mode == 0 ? x : (mode == 1 ? (e.isFlying == 0 ? x : 0.01) : (e.isFlying == 1 ? x : 0.01)); return hp(e) * m; }, a => E[int.Parse(a.Id[1..])].speed, a => E[int.Parse(a.Id[1..])].reward * bk).Leaks == 0;
        double lo = 0, hi = Math.Max(0.05, guess * 1.25);
        if (Ok(hi)) { lo = hi; hi *= 2; while (Ok(hi) && hi < 1e4) { lo = hi; hi *= 2; } }
        else { while (!Ok(hi / 2) && hi > 1e-3) hi /= 2; lo = hi / 2; }
        for (int i = 0; i < 9 && hi - lo > lo * 0.012; i++) { double mid = (lo + hi) / 2; if (Ok(mid)) lo = mid; else hi = mid; }
        return lo;
    }

    static LevelRes Measure(MapIn m, double kFixed, LevelRes? L01)
    {
        int L = int.Parse(m.Level[1..]); var M = new MapG(m);
        // 参照阵型：先只取墙（预算 0）得墙体造价 → 经济系数 → 再按全部经济排完整建造队列
        Designer.Plan(M, TemplateStage, out int walls, out _, out _, out _, out _, out _, 0);
        var wallQ = Designer.Plan(M, TemplateStage, out _, out _, out _, out _, out _, out _, 0);
        int wallCost = wallQ.Sum(x => x.Cost);
        double k = L01 == null ? 1.0 : (double)wallCost / L01.WallCost;
        double bountyAll = B.waves.Sum(w => w.sequence.Sum(id => E[id].reward)) * k;
        var rewards = B.waves.Select(w => (int)Math.Round(w.rewardGold * k)).ToList();
        if (L01 != null) { int extra = (int)Math.Round(100 * k - 100); for (int i = 0; i < 4; i++) rewards[i] += extra / 4 + (i < extra % 4 ? 1 : 0); }
        else rewards = B.waves.Select(w => w.rewardGold).ToList();
        int econ = 100 + (int)Math.Floor(bountyAll) + rewards.Take(24).Sum();   // W25 清波奖励在通关后到账，不进建造
        var queue = Designer.Plan(M, TemplateStage, out _, out _, out var layout, out _, out _, out _, Math.Max(0, econ - wallCost));
        var r = new LevelRes { Level = m.Level, Walls = walls, WallCost = wallCost, K = Math.Round(k, 4), LongestPath = m.LongestCells, AirSpawn = M.AirSpawnRule, AirLen = Math.Round(M.AirLen, 2), Looks = Looks[L].ToList(), Layout = layout, Rewards = rewards };
        var sim = new Sim(M, new List<Act>(queue)) { Gold = 100, BuildDelay = Reaction }; sim.BuildAll(0, 0, "开局");
        double gG = 1, gA = 1, gC = 1; double secs = 0;
        foreach (var w in B.waves)
        {
            var wr = new WaveRes { W = w.wave, WaveType = w.waveType, Count = w.sequence.Count, AirCount = w.sequence.Count(id => E[id].isFlying == 1), Reward = rewards[w.wave - 1] };
            bool hasAir = wr.AirCount > 0; var sp = Spawns(w);
            wr.GoldStart = (int)sim.Gold; wr.PathStart = sim.PathLen; wr.Built = sim.QIdx;
            double gm = 1, am = 1, fix = 1;
            if (L01 != null)
            {
                var b = L01.Waves[w.wave - 1];
                wr.CapG01 = b.CapG; wr.CapA01 = b.CapA; wr.CapC01 = b.CapC; wr.Tight01 = b.Tight;
                double cg = Cap(sim, w, e => e.hp, k, 1, gG * b.CapG); gG = cg / Math.Max(1e-6, b.CapG);
                gm = cg / b.CapG; wr.CapG = cg;
                if (hasAir) { double ca = Cap(sim, w, e => e.hp, k, 2, gA * b.CapA); am = ca / b.CapA; gA = am; wr.CapA = ca; }
                // 合并修正：让「定稿血量 ÷ 合并上限」与 L01 同波相同
                Func<BEnemy, double> hp1 = e => e.hp * (e.isFlying == 1 ? am : gm);
                double cc = Cap(sim, w, hp1, k, 0, gC);
                fix = cc / b.CapC; gC = cc;
                gm *= fix; am *= fix;
                Func<BEnemy, double> hpF = e => Math.Round(e.hp * (e.isFlying == 1 ? am : gm), 2);
                wr.CapC = Cap(sim, w, hpF, k, 0, 1); wr.Tight = 1 / Math.Max(1e-6, wr.CapC);
            }
            else
            {
                wr.CapG = Cap(sim, w, e => e.hp, 1, 1, gG); gG = wr.CapG;
                if (hasAir) { wr.CapA = Cap(sim, w, e => e.hp, 1, 2, gA); gA = wr.CapA; }
                wr.CapC = Cap(sim, w, e => e.hp, 1, 0, gC); gC = wr.CapC; wr.Tight = 1 / Math.Max(1e-6, wr.CapC); wr.Tight01 = wr.Tight;
            }
            wr.GroundMul = Math.Round(gm, 4); wr.AirMul = hasAir ? Math.Round(am, 4) : 0; wr.Fix = Math.Round(fix, 4);
            double gmF = gm, amF = am;
            Func<Arche, double> hpOf = a => { var e = E[int.Parse(a.Id[1..])]; return L01 == null ? e.hp : Math.Round(e.hp * (e.isFlying == 1 ? amF : gmF), 2); };
            var res = sim.RunWave(w.wave, sp, hpOf, a => E[int.Parse(a.Id[1..])].speed, a => E[int.Parse(a.Id[1..])].reward * k);
            wr.Leaks = res.Leaks; wr.Duration = Math.Round(res.Duration, 1); wr.MinRemain = Math.Round(res.MinRemainFrac, 3); secs += res.Duration;
            wr.GroundHp = Math.Round(w.sequence.Where(id => E[id].isFlying == 0).Sum(id => hpOf(Arche.All["e" + id]) / (1 - E[id].armor)), 0);
            wr.AirHp = Math.Round(w.sequence.Where(id => E[id].isFlying == 1).Sum(id => hpOf(Arche.All["e" + id])), 0);
            wr.Bounty = Math.Round(w.sequence.Sum(id => E[id].reward) * k, 1);
            sim.Log.Clear(); sim.Gold += wr.Reward; sim.BuildAll(w.wave, 0, $"W{w.wave}后"); sim.Log.Clear();
            r.Waves.Add(wr);
            // 落表行（L01 不落表：整关恢复 tag 原样）
            if (L01 != null)
            {
                var ids = w.sequence.Distinct().ToList(); var newId = new Dictionary<int, int>();
                foreach (var id in ids)
                {
                    var e = E[id]; int ri = Array.IndexOf(Roles, e.role); string look = "Enemy_" + Looks[L][ri];
                    int nid = 80000000 + L * 100000 + w.wave * 100 + newId.Count + 1;   // 8000 万段：避开 tag L01 的 5000000–5000245 与历史各关 id newId[id] = nid;
                    r.Enemies.Add(new { id = nid, speed = e.speed, hp = Math.Round(e.hp * (e.isFlying == 1 ? am : gm), 2), name = Looks[L][ri], type = e.type, interval = e.interval, resName = look, armor = e.armor, reward = Math.Round(e.reward * k, 4), damageToPlayer = e.damageToPlayer, scale = e.scale, bodyRadius = e.bodyRadius, isFlying = e.isFlying, animController = e.animController ?? "", desc = $"V3 tag-L01 基准; srcId={id}; role={e.role}; level={L}; wave={w.wave}; gMul={gm:F4}; aMul={am:F4}; k={k:F4}", levelId = L });
                }
                r.Groups.Add(new { wave = w.wave, roundId = w.roundId, id = L * 10000 + w.wave * 100 + 1, enemies = w.sequence.Select(id => newId[id]).ToList(), enemyIntervalMs = w.enemyIntervalMs, waveType = w.waveType, rewardGold = rewards[w.wave - 1] });
            }
        }
        r.Seconds = Math.Round(secs, 0); r.Built = sim.QIdx;
        return r;
    }
}
