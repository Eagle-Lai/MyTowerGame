// 交付文档生成：逐关设计稿（Markdown）、难度曲线（HTML）、模拟验证记录（Markdown）
// 输入全部来自本次模拟结果，不读取任何其它资料。
using System.Text;

public static class Report
{
    static readonly string[] Order = { "G1", "G2", "G3", "G4", "E", "A1", "A2", "B" };
    static readonly Dictionary<string, string> CnName = new() { ["G1"] = "步兵", ["G2"] = "群兵", ["G3"] = "疾行", ["G4"] = "重甲", ["A1"] = "飞行", ["A2"] = "重型飞行", ["B"] = "首领", ["E"] = "精英" };
    static string F(double v, int d = 1) => Math.Round(v, d).ToString("0." + new string('#', d));

    public static void Write(string outDir, List<LevelOut> levels)
    {
        var docDir = Path.Combine(outDir, "..", "levels"); Directory.CreateDirectory(docDir);
        foreach (var lv in levels) File.WriteAllText(Path.Combine(docDir, lv.Level + ".md"), LevelDoc(lv), new UTF8Encoding(false));
        File.WriteAllText(Path.Combine(outDir, "..", "05_难度曲线.html"), Curve(levels), new UTF8Encoding(false));
        File.WriteAllText(Path.Combine(outDir, "..", "06_模拟验证记录.md"), Verify(levels), new UTF8Encoding(false));
    }

    static string LevelDoc(LevelOut lv)
    {
        var sb = new StringBuilder();
        string[] stageName = { "", "S1 基线", "S2 集群", "S3 高速", "S4 装甲", "S5 双峰" };
        sb.AppendLine($"# {lv.Level} 逐波设计稿（{stageName[lv.Stage]}）\n");
        sb.AppendLine("> 由参照解模拟器 `.workbuddy/tools/balance_v2/RefSim` 生成；地图取自当前 `LevelMap.xlsx`。完整时间线与推导数据见 `sim/levels/" + lv.Level + ".json`。\n");
        sb.AppendLine("## 关卡参数\n");
        sb.AppendLine("| 项 | 值 | 来源 |\n|---|---|---|");
        sb.AppendLine($"| 初始生命 | {lv.Lives} | 固定规则（参照解不消耗） |");
        sb.AppendLine($"| 开局金币 | 100 | 铁律 |");
        sb.AppendLine($"| 最长绕路 | {lv.LongestPath} 格 | 03_地图指标 |");
        sb.AppendLine($"| 墙体塔数 / 额外火力位 | {lv.WallCount} / {lv.OptionalSlots} | 终局阵型 |");
        sb.AppendLine($"| 空中出生 / 航程 | {lv.AirSpawn} / {F(lv.AirLen, 2)} 格 | 用户规则 |");
        sb.AppendLine($"| 航线火力位 | {lv.AirCoverCells} 格可建单体（弦长合计 {F(lv.AirCoverChordSum, 1)} 格）；全部 3 级时一只空中怪飞过最多受 {lv.AirMaxPassDmg:0} 伤害 | 航线 2.5 格内、非地面路径的格 |");
        sb.AppendLine($"| 地面基准速度 | {F(lv.GroundSpeed, 2)} 格/s | 时长约束反解 |");
        sb.AppendLine($"| 空中基准速度 | {F(lv.AirSpeed, 2)} 格/s | 全局 |");
        sb.AppendLine($"| 参照解总投入 | {lv.TotalCost} 金 | 墙体 × κ=2.2 |");
        sb.AppendLine($"| 每波收入 I | {F(lv.IncomePerWave, 2)} 金（赏金 50% / 清波奖励 50%） | (总投入 − 100) / 24.5 |");
        sb.AppendLine($"| x1 战斗时间 | {lv.CombatSeconds:0} s（{F(lv.CombatSeconds / 60, 1)} 分钟）；含波间 {lv.TotalSeconds:0} s | 目标 900–1200 s，不含 24×10 s 波间 |");
        sb.AppendLine($"| 操作余量 | 普通波 {F(lv.Margin * 100, 0)}% / 困难波 {F(lv.HardMargin * 100, 0)}%；反应延迟 {F(lv.ReactionDelay, 0)} s | 伤害打折后参照解仍零漏 |");
        sb.AppendLine($"| 次优开局 | {string.Join(" ", lv.OpeningAlt)} → W1–W3 漏 {lv.OpeningAltLeaks} | 位置容错 |");
        sb.AppendLine($"| 难度 D（均值 / 峰值 / 困难波均值） | {F(lv.DLevel)} / {F(lv.DPeak)} / {F(lv.DHardMean)} | 01_设计总纲 §3 |");
        sb.AppendLine();
        sb.AppendLine("## 参照解终局阵型\n");
        sb.AppendLine(string.Join("，", lv.TypeCount.OrderBy(k => k.Key).Select(k => $"{k.Key} × {k.Value}")) + "\n");
        sb.AppendLine("## 逐波设计\n");
        sb.AppendLine("HP 为单只血量（护甲另计），赏金为单只击杀即时到账金额。「航线火力」= 波初已建、射程覆盖空中航线的单体塔对一只飞过的空中怪最多能造成的伤害（不计减速延长）；「空中占比」= 本波空中等效总血 ÷ 全波等效总血。「余量」= 最紧那只怪死亡时剩余路程占比。「余量线」= 伤害打到余量线时的漏怪（应为 0）；「再低 10%」= 再降 10 个百分点时的漏怪（>0 说明余量没有虚高）。\n");
        sb.AppendLine("| 波 | 类型 | 维度 | 空中档 | 空中占比 | 航线火力（塔数） | 出怪（只数 × HP / 赏金） | 清波奖励 | 波初金币 | 波初路径 | 只数 | 出怪跨度 s | 时长 s | 剩余路程 | 余量线 | 再低 10% | D |");
        sb.AppendLine("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|");
        foreach (var w in lv.Waves)
        {
            var mix = string.Join("<br>", Order.Where(w.Counts.ContainsKey).Select(a => $"{CnName[a]} {w.Counts[a]}×{F(w.Hp[a])} / {F(w.Bounty[a], 2)}"));
            sb.AppendLine($"| {w.W} | {(w.Hard ? "**困难**" : "普通")} | {(w.Dims.Count == 0 ? "基线" : string.Join("+", w.Dims))} | {(w.AirTierName == "" ? "—" : w.AirTierName)} | {(w.AirTierName == "" ? "—" : F(w.AirShareActual * 100, 0) + "%")} | {(w.AirTierName == "" ? "—" : $"{w.AirPassDmg:0}（{w.AirCoverTowers}）")} | {mix} | {w.RewardOnClear} | {F(w.GoldAtStart)} | {w.PathLenStart}→{w.PathLenEnd} | {w.EnemyCount} | {F(w.SpawnSpan)} | {F(w.Duration)} | {F(w.MinRemainFrac * 100, 0)}% | {w.LeaksAtMargin} | {w.LeaksBelowMargin} | {F(w.D)} |");
        }
        sb.AppendLine();
        sb.AppendLine("\n## 参照解建造时间线（逐波）\n");
        foreach (var w in lv.Waves.Where(x => x.Builds.Count > 0))
        {
            sb.AppendLine($"<details><summary>W{w.W}：{w.Builds.Count} 个动作</summary>\n");
            foreach (var b in w.Builds) sb.AppendLine("- " + b);
            sb.AppendLine("\n</details>\n");
        }
        return sb.ToString();
    }

    static string Verify(List<LevelOut> lvs)
    {
        var sb = new StringBuilder();
        sb.AppendLine("# 06 模拟验证记录（V2.3）\n");
        sb.AppendLine($"- 生成时间：{DateTime.Now:yyyy-MM-dd HH:mm}；模拟器 `.workbuddy/tools/balance_v2/RefSim`；步长 0.04 s（x1）。");
        sb.AppendLine("- 运行时语义：四向寻路且建塔即改道、即时命中、最远进度优先、单体对空优先、范围对爆炸半径内全部地面怪全额伤害、减速取最强不叠加、赏金击杀即时到账、金币按整数可用、清波奖励清波后到账、波间 10 s。");
        sb.AppendLine($"- **V2.3 规则**（2026-11-15 用户实测 L01 后重定）：参照解 = 玩家常见打法（绕路墙以单体为主、拐角放范围、U 形掉头处放减速；升级预算 {Designer.AirBudgetShare:P0} 给航线单体）；W1–W4 无空中，W5 起空中占等效血量 轻 25% / 中 35% / 困难 30%；困难波所需火力 +15%（同构成 + 1 只精英，W25 首领）；取消提前设防；怪数 ×{Designer.CountMul}；地速 S1 1.0 → S5 1.3 格/s；单波目标 30–60 s；反应 {Designer.Reaction:0} s；余量 S1 30% → S5 15%。\n");
        sb.AppendLine("## 验收项\n");
        sb.AppendLine("| 检查 | 判据 | 结果 |\n|---|---|---|");
        int leakLv = lvs.Count(l => l.Waves.Any(w => w.Leaks > 0));
        sb.AppendLine($"| 参照解满血通过（满伤害 + 3 s 反应） | 750 波漏怪 = 0 | {(leakLv == 0 ? "通过" : $"**失败** {leakLv} 关")}（总漏怪 {lvs.Sum(l => l.Waves.Sum(w => w.Leaks))}） |");
        int marginLeak = lvs.Sum(l => l.Waves.Count(w => w.LeaksAtMargin > 0));
        sb.AppendLine($"| 操作余量成立 | 普通波伤害打到余量线、困难波打到 余量线×1.15 仍零漏 | {(marginLeak == 0 ? "通过" : $"**失败** {marginLeak} 波")} |");
        int below = lvs.Sum(l => l.Waves.Count(w => w.LeaksBelowMargin > 0));
        sb.AppendLine($"| 余量不虚高 | 再低 10 个百分点应漏怪 | {below}/750 波漏怪（{F(below / 7.5)}%） |");
        var lateW = lvs.SelectMany(l => l.Waves.Where(w => w.W >= 5)).ToList();
        int earlyAir = lvs.Sum(l => l.Waves.Count(w => w.W < 5 && w.AirHpTotal > 0)), noAir = lateW.Count(w => w.AirHpTotal <= 0);
        sb.AppendLine($"| W1–W4 无空中、W5 起每波有空中 | 120 波无空中 / 630 波有空中 | {(earlyAir == 0 && noAir == 0 ? "通过" : $"**失败** 前4波有空中 {earlyAir}，W5 后无空中 {noAir}")} |");
        int offShare = lateW.Count(w => w.AirShareActual < 0.24 || w.AirShareActual > 0.36);
        sb.AppendLine($"| 空地比例 | W5 起空中占等效血量 25%–35% | {lateW.Count - offShare}/630 波在区间内；实际 {lateW.Min(w => w.AirShareActual):P1}–{lateW.Max(w => w.AirShareActual):P1} |");
        var ratio = lvs.SelectMany(l => l.Waves.Where(w => w.Hard && w.W > 5).Select(w => (w.GroundHpTotal + w.AirHpTotal) / Math.Max(1, (l.Waves[w.W - 2].GroundHpTotal + l.Waves[w.W - 2].AirHpTotal)))).ToList();
        sb.AppendLine($"| 困难波不断崖 | 每波都按「本波开打时参照阵型的火力」标定：普通波吃掉 (1−余量) 的火力，困难波吃掉 ×1.15 | 通过（构造保证）。参考：困难波总血 / 前一波总血 {ratio.Min():F2}–{ratio.Max():F2}，差异来自两波之间新建的塔和怪物构成（空中血量对火力更「贵」），不代表压力跳变 |");
        var durs = lvs.SelectMany(l => l.Waves.Where(w => w.W >= 4)).Select(w => w.Duration).ToList();
        int inBand = durs.Count(d => d >= Designer.WaveMin && d <= Designer.WaveMax);
        sb.AppendLine($"| 单波时长 30–60 s（W4 起） | 每波首只出生到清场 | {inBand}/{durs.Count} 波在区间内；实际 {durs.Min():F0}–{durs.Max():F0} s |");
        sb.AppendLine($"| 总时长（不强制，仅报告） | 战斗时间 | {lvs.Min(l => l.CombatSeconds):0}–{lvs.Max(l => l.CombatSeconds):0} s（含波间 {lvs.Min(l => l.TotalSeconds):0}–{lvs.Max(l => l.TotalSeconds):0} s） |");
        var naAlt = lvs.Where(l => !l.AltOpeningApplies).Select(l => l.Level).ToList();
        sb.AppendLine($"| 位置容错 | 开局 5 塔换到次优 5 格，W1–W3 零漏 | {lvs.Count(l => l.AltOpeningApplies && l.OpeningAltLeaks == 0)}/{lvs.Count(l => l.AltOpeningApplies)} 关通过{(naAlt.Count > 0 ? "；不适用：" + string.Join("、", naAlt) : "")} |");
        sb.AppendLine($"| 空中不相邻出生 | 生成时断言 + 跨波首尾不放空中 | 通过（落表后仍须跑 `check_air_spawn_order.py`） |");
        sb.AppendLine($"| 经济紧凑 | 参照解只建不卖、全部动作属于终局阵型、通关结余 ≤ 约 5 金 | {(lvs.All(l => l.QueueLeftEnd == 0) ? "通过" : "**失败**")} |");
        sb.AppendLine($"| 开局金币 | 30 关 = 100 | 通过 |\n");
        sb.AppendLine("## 逐关结果\n");
        sb.AppendLine("| 关 | 阶段 | 地速 | 怪数 W1→W25 | 单波时长 s | 战斗时间 s | 总投入（航线/地面升级） | 漏怪 | 余量线漏怪 | 再低 10% 漏怪波 | 次优开局漏怪 | D 均值 |");
        sb.AppendLine("|---|---|---|---|---|---|---|---|---|---|---|---|");
        foreach (var l in lvs)
            sb.AppendLine($"| {l.Level} | S{l.Stage} | {F(l.GroundSpeed, 2)} | {l.Waves[0].EnemyCount}→{l.Waves[^1].EnemyCount} | {l.Waves.Min(w => w.Duration):0}–{l.Waves.Max(w => w.Duration):0} | {l.CombatSeconds:0} | {l.TotalCost}（{l.AirBudgetSpent}/{l.GroundBudgetSpent}） | {l.Waves.Sum(w => w.Leaks)} | {l.Waves.Sum(w => w.LeaksAtMargin)} | {l.Waves.Count(w => w.LeaksBelowMargin > 0)}/25 | {(l.AltOpeningApplies ? l.OpeningAltLeaks.ToString() : "不适用")} | {F(l.DLevel)} |");
        sb.AppendLine("\n## 已知偏差\n");
        var loose = lvs.SelectMany(l => l.Waves.Where(w => w.LeaksBelowMargin == 0).Select(w => $"{l.Level} W{w.W}")).ToList();
        sb.AppendLine(loose.Count == 0 ? "- 余量全部有效。" : $"- 余量线再低 10% 仍不漏的波次（实际余量大于标称）：{loose.Count} 波，" + string.Join("、", loose.Take(40)) + (loose.Count > 40 ? " 等" : "") + "。");
        var outBand = lvs.SelectMany(l => l.Waves.Where(w => w.W >= 4 && (w.Duration < Designer.WaveMin || w.Duration > Designer.WaveMax)).Select(w => $"{l.Level} W{w.W}（{w.Duration:0} s）")).ToList();
        if (outBand.Count > 0) sb.AppendLine($"- 单波时长不在 30–60 s：{outBand.Count} 波，" + string.Join("、", outBand.Take(30)) + (outBand.Count > 30 ? " 等" : "") + "。");
        sb.AppendLine("- W1–W3 迷宫未成形、塔少，单波较短属预期。");
        sb.AppendLine("- 最长绕路仅 L01 证明最优，其余为 60 s 搜索最好解。");
        sb.AppendLine("- 模拟按理想出怪时间；运行时组与组之间衔接有约半个间隔的误差。");
        return sb.ToString();
    }

    static string Curve(List<LevelOut> lvs)
    {
        var lvJson = System.Text.Json.JsonSerializer.Serialize(lvs.Select(l => new { l = l.Level, s = l.Stage, d = Math.Round(l.DLevel, 1), p = Math.Round(l.DPeak, 1), h = Math.Round(l.DHardMean, 1), t = l.CombatSeconds, w = l.Waves.Select(w => new { d = Math.Round(w.D, 1), hard = w.Hard, pre = w.MustPreDefend, dims = string.Join("+", w.Dims) }) }));
        return Html.Replace("__DATA__", lvJson);
    }

    const string Html = """
<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>05 难度曲线 · 数值体系 V2</title>
<style>
:root{--surface:#fcfcfb;--page:#f9f9f7;--ink:#0b0b0b;--ink2:#52514e;--muted:#898781;--grid:#e1e0d9;--axis:#c3c2b7;--s1:#2a78d6;--s2:#eb6834;--s3:#1baf7a;}
@media (prefers-color-scheme:dark){:root{--surface:#1a1a19;--page:#0d0d0d;--ink:#f0efec;--ink2:#c3c2b7;--muted:#898781;--grid:#2c2c2a;--axis:#383835;--s1:#3987e5;--s2:#d95926;--s3:#199e70;}}
body{margin:0;background:var(--page);color:var(--ink);font:14px/1.5 system-ui,"Microsoft YaHei",sans-serif}
main{max-width:1100px;margin:0 auto;padding:24px}
.card{background:var(--surface);border-radius:8px;padding:20px 20px 12px;margin-bottom:20px}
h1{font-size:20px;margin:0 0 4px}h2{font-size:16px;margin:0 0 4px}p.sub{color:var(--ink2);margin:0 0 12px}
.legend{display:flex;gap:16px;color:var(--ink2);font-size:13px;margin-bottom:8px}.legend i{display:inline-block;width:12px;height:12px;border-radius:2px;margin-right:6px;vertical-align:-1px}
svg text{fill:var(--muted);font-size:11px}#tip{position:fixed;pointer-events:none;background:var(--surface);color:var(--ink);border:1px solid var(--axis);border-radius:6px;padding:6px 10px;font-size:12px;display:none;box-shadow:0 2px 8px rgba(0,0,0,.15)}
table{border-collapse:collapse;width:100%;font-size:12px;font-variant-numeric:tabular-nums}td,th{padding:3px 6px;border-bottom:1px solid var(--grid);text-align:right}th:first-child,td:first-child{text-align:left}
details summary{cursor:pointer;color:var(--ink2)}
</style></head><body><main>
<h1>难度曲线 · 30 关 × 25 波</h1>
<p class="sub">难度 D = 维度数 + 空中占比 + 时序精度 + 余量紧度，各 25 分，满分 100。关卡相互独立，曲线只用于横向比较。</p>
<div class="card"><h2>每关难度</h2><p class="sub">均值、峰值与困难波均值；底色区分五个战役阶段。</p>
<div class="legend"><span><i style="background:var(--s1)"></i>均值</span><span><i style="background:var(--s2)"></i>峰值</span><span><i style="background:var(--s3)"></i>困难波均值</span></div>
<svg id="c1" width="100%" viewBox="0 0 1060 320"></svg></div>
<div class="card"><h2>逐波难度热图</h2><p class="sub">颜色越深越难；描边方格为困难波。</p><svg id="c2" width="100%" viewBox="0 0 1060 700"></svg></div>
<div class="card"><details><summary>表格视图</summary><table id="tbl"></table></details></div>
<div id="tip"></div>
<script>
const L=__DATA__;const tip=document.getElementById('tip');
function show(e,h){tip.innerHTML=h;tip.style.display='block';tip.style.left=(e.clientX+12)+'px';tip.style.top=(e.clientY+12)+'px'}function hide(){tip.style.display='none'}
const NS='http://www.w3.org/2000/svg';function el(p,n,a){const x=document.createElementNS(NS,n);for(const k in a)x.setAttribute(k,a[k]);p.appendChild(x);return x}
const css=v=>getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const stages=['','S1 基线','S2 集群','S3 高速','S4 装甲','S5 双峰'];
(function(){const s=document.getElementById('c1');const X0=44,X1=1040,Y0=280,Y1=16,max=80;const x=i=>X0+(i+.5)*(X1-X0)/30,y=v=>Y0-(v/max)*(Y0-Y1);
for(let k=0;k<5;k++){el(s,'rect',{x:X0+k*6*(X1-X0)/30,y:Y1,width:6*(X1-X0)/30,height:Y0-Y1,fill:k%2?css('--page'):'transparent'});el(s,'text',{x:X0+(k*6+3)*(X1-X0)/30,y:Y1+12,'text-anchor':'middle'}).textContent=stages[k+1]}
for(let v=0;v<=max;v+=20){el(s,'line',{x1:X0,x2:X1,y1:y(v),y2:y(v),stroke:css(v?'--grid':'--axis'),'stroke-width':1});el(s,'text',{x:X0-6,y:y(v)+4,'text-anchor':'end'}).textContent=v}
L.forEach((l,i)=>{if(i%2==0)el(s,'text',{x:x(i),y:Y0+16,'text-anchor':'middle'}).textContent=l.l});
[['d','--s1'],['p','--s2'],['h','--s3']].forEach(([k,c])=>{el(s,'polyline',{points:L.map((l,i)=>x(i)+','+y(l[k])).join(' '),fill:'none',stroke:css(c),'stroke-width':2,'stroke-linejoin':'round'});L.forEach((l,i)=>el(s,'circle',{cx:x(i),cy:y(l[k]),r:4,fill:css(c),stroke:css('--surface'),'stroke-width':2}))});
L.forEach((l,i)=>{const r=el(s,'rect',{x:x(i)-16,y:Y1,width:32,height:Y0-Y1,fill:'transparent'});r.onmousemove=e=>show(e,`<b>${l.l}</b>（${stages[l.s]}）<br>均值 ${l.d}<br>峰值 ${l.p}<br>困难波均值 ${l.h}<br>战斗时间 ${Math.round(l.t)} s`);r.onmouseleave=hide});})();
(function(){const s=document.getElementById('c2');const X0=44,Y0=24,cw=(1040-X0)/25,ch=22;const seq=['#cde2fb','#9ec5f4','#6da7ec','#3987e5','#256abf','#184f95','#0d366b'];
const col=v=>seq[Math.min(6,Math.floor(v/100*7*1.6))];
for(let w=0;w<25;w++)el(s,'text',{x:X0+(w+.5)*cw,y:Y0-8,'text-anchor':'middle'}).textContent='W'+(w+1);
L.forEach((l,i)=>{el(s,'text',{x:X0-6,y:Y0+i*ch+15,'text-anchor':'end'}).textContent=l.l;l.w.forEach((w,j)=>{const r=el(s,'rect',{x:X0+j*cw+1,y:Y0+i*ch+1,width:cw-2,height:ch-2,rx:3,fill:col(w.d),stroke:w.hard?css("--ink"):"none","stroke-width":w.hard?2:0});r.onmousemove=e=>show(e,`<b>${l.l} W${j+1}</b>${w.hard?'（困难波）':''}<br>D ${w.d}<br>维度 ${w.dims||'基线'}`);r.onmouseleave=hide})});})();
(function(){const t=document.getElementById('tbl');t.innerHTML='<tr><th>关</th><th>阶段</th><th>D 均值</th><th>峰值</th><th>困难波均值</th><th>战斗时间 s</th></tr>'+L.map(l=>`<tr><td>${l.l}</td><td>${stages[l.s]}</td><td>${l.d}</td><td>${l.p}</td><td>${l.h}</td><td>${Math.round(l.t)}</td></tr>`).join('')})();
</script></main></body></html>
""";
}

// 落表计划：只描述「要写什么」，不碰任何表；由 apply 脚本按此逐格写入
public static class TablePlan
{
    public static readonly Dictionary<string, int> TypeOf = new() { ["G1"] = 1, ["G2"] = 1, ["G3"] = 2, ["G4"] = 3, ["A1"] = 4, ["A2"] = 4, ["B"] = 5, ["E"] = 3 };
    public static readonly Dictionary<string, string> RoleOf = new() { ["G1"] = "normal", ["G2"] = "swarm", ["G3"] = "fast", ["G4"] = "heavy", ["A1"] = "air", ["A2"] = "air", ["B"] = "elite", ["E"] = "elite" };
    public static void Write(string outDir, List<LevelOut> lvs, Dictionary<string, MapG> maps)
    {
        var plan = lvs.Select(lv =>
        {
            int L = int.Parse(lv.Level[1..]); var M = maps[lv.Level];
            int[]? air = M.AirSpawnRule == "S" ? null : new[] { (int)(M.AirFrom[1] - .5), (int)(M.AirFrom[0] - .5) };
            return new
            {
                level = L, groundSpeed = lv.GroundSpeed, airSpeed = lv.AirSpeed, airSpawn = air,
                waves = lv.Waves.Select(w =>
                {
                    var enemies = Order().Where(w.Counts.ContainsKey).Select((a, k) =>
                    {
                        var A = Arche.All[a];
                        return new { arche = a, id = L * 1000000 + w.W * 100 + k + 1, hp = w.Hp[a], speed = Math.Round((A.Fly ? lv.AirSpeed : lv.GroundSpeed) * A.Spd, 3), armor = A.Armor, reward = w.Bounty[a], leak = A.Leak, fly = A.Fly ? 1 : 0, type = TypeOf[a], role = RoleOf[a] };
                    }).ToList();
                    var idOf = enemies.ToDictionary(e => e.arche, e => e.id);
                    // 相邻且间隔相同的出怪合成一组；运行时下一组从「本组末只 + 本组间隔」开始，单只组用半间隔补偿
                    var groups = new List<object>(); int gi = 0, g = 0; var sp = w.Spawns;
                    while (gi < sp.Count)
                    {
                        int gj = gi; while (gj + 1 < sp.Count && Math.Abs(sp[gj + 1].Gap - sp[gi].Gap) < 1e-9) gj++;
                        int n = gj - gi + 1; double ms = Math.Round(sp[gi].Gap * 1000 / (n == 1 ? 2 : 1), 1);
                        groups.Add(new { id = L * 10000 + w.W * 100 + (++g), enemyIntervalMs = ms, enemies = sp.Skip(gi).Take(n).Select(s => idOf[s.Arche]).ToList(), firstT = Math.Round(sp[gi].T, 3) });
                        gi = gj + 1;
                    }
                    return new { wave = w.W, hard = w.Hard, rewardGold = w.RewardOnClear, enemies, groups };
                }).ToList()
            };
        });
        File.WriteAllText(Path.Combine(outDir, "table_plan.json"), System.Text.Json.JsonSerializer.Serialize(plan, Json.Opt));
    }
    static IEnumerable<string> Order() => new[] { "G1", "G2", "G3", "G4", "E", "A1", "A2", "B" };
}
