# L02 W15 空中怪在减速范围内掉血排查

日期：2026-11-11（Asia/Shanghai）。

用户现象：编辑器 L02 第 15 波，空中怪经过减速塔范围，附近同时有火力塔和普通塔，血量快速减少。

## 当前判断

当前加载的编译后战斗代码中，减速并未让火力塔获得对空伤害。18 组隔离组合中，火力塔对空命中均为 0；空中血量变化完全对应普通塔命中。正常塔持续攻击与减速延长停留时间能够产生明显掉血。

尚未逐帧重放用户当时的完整阵型，不能把这个机制验证当作原现场伤害归因已经完成。

## 工程与运行配置

- 工程：D:/FreedomTower_1；Unity 2022.3.62f3c1；manifest Unity MCP v10.3.0。
- 当前原生服务：unityMCP；实例 FreedomTower_1@520e2c6d；实际工具 transport=stdio、实例桥接 6400；EditorPrefs HTTP URL=http://127.0.0.1:8082。仅为本次实测，不是后续默认端口。
- DLL：Library/ScriptAssemblies/FTProject.Runtime.dll；编辑器停止运行，Boot 场景。
- 当前内存 ActiveLevelId=2，FailedTables=[]，scriptCompilationFailed=false。
- W15 roundId=2015，waveType=2；Bat ID=6000145，isFlying=1，困难波实际 HP=700.006958。
- 当前 L02 三级火力塔 canAttackAir 均为 0；普通塔均为 1。
- Console 原有 Unity Remote requirements check failed；没有发现其与战斗伤害之间的证据。

## 隔离组合检查

在临时 PreviewScene 中调用当前已编译的 TickSlowAura、PickBestTarget、DetonateAt、HurtEnemy、TickEffects 方法，采用当前实际加载配置。每组包含一只 W15 Bat 和一只地面 Crawler，后者作为爆炸确实生效的阳性对照。销毁临时对象并恢复原 Grid、统计计数和场景。

3 个火力塔等级 × 3 个减速塔等级 × 是否加入同等级普通塔命中，共 18 组。每组施加 10 次光环并结算 10 次爆炸；加入普通塔的组另结算 10 次普通塔命中。这是按次调用验证，不是按攻速计算的波次模拟。

- 不加入普通塔：9 组 Bat HP 均为 700.006958 → 700.006958；爆炸对地面怪正常扣血。
- 加入一级普通塔 10 次命中：Bat HP → 640.006958，伤害 60。
- 加入二级普通塔 10 次命中：Bat HP → 610.006958，伤害 90。
- 加入三级普通塔 10 次命中：Bat HP → 557.0071，伤害约 143。
- 全部火力塔 EvidenceAirHits=0；普通塔相应组 EvidenceAirHits=10。
- 减速不改变飞行配置，未施加 DOT，状态效果推进不额外扣血。
- 原始数据：isolated-results.json；诊断代码：isolated-diagnostic.cs.txt。

## 实际移动与普通塔攻速检查

使用实际 BaseEnemy.Tick 与 BaseTower.TickAttack，120Hz 步进，让 W15 Bat 沿穿过塔中心的合成直线路径飞过，使用三级普通塔和不同等级减速塔。普通塔对空单次伤害 13×1.1=14.3、CD=0.41s、射程=2.3。

| 减速 | 普通塔射程内时间 | 普通塔命中数 | 总伤害 |
|---|---:|---:|---:|
| 无 | 4.292s | 10 | 143.0 |
| 一级，30% | 6.058s | 14 | 200.2 |
| 二级，40% | 7.083s | 17 | 243.1 |
| 三级，50% | 8.550s | 20 | 286.0 |

三级减速使本例累计伤害约翻倍。减速改变停留时间，不提高单发伤害或单位时间攻速。多个普通塔对空优先集火时，可进一步造成明显的快速掉血；该解释与用户报告中“附近有普通塔”一致，但未据此断言原现场全部伤害来源。

原始数据：transit-results.json；诊断代码：transit-diagnostic.cs.txt。

## 验证边界

没有改动游戏代码、配置源表、导出 JSON、场景文件或玩家存档；没有启动或停止 Play Mode。没有实施原阵型整波回放、血条视觉复现或 Android 验证。如果要最终认定用户那一局的直接伤害来源，仍需在同一阵型中记录逐次扣血的塔实例、塔型、怪物 ID、时间和实际扣血。

