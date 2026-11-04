param([int]$Attempt = 4)
$ErrorActionPreference = 'Stop'
$runDir = $PSScriptRoot
$events = @(Get-Content -LiteralPath (Join-Path $runDir "attempt$Attempt-live.json") -Raw | ConvertFrom-Json)
$state = Get-Content -LiteralPath (Join-Path $runDir 'final-state.json') -Raw | ConvertFrom-Json
$metrics = $state.run
if (-not $metrics.victory -or $metrics.leaked -ne 0 -or $state.hp -ne $state.maxHp -or $metrics.completedWaveCount -ne 25 -or $metrics.debugOverride) {
    throw 'Final state is not a genuine zero-leak victory.'
}
if ($metrics.killed -ne $metrics.expectedEnemyCount -or $metrics.successfulSpawned -ne $metrics.expectedEnemyCount) {
    throw 'Enemy accounting is incomplete.'
}
$sequence = 0
$operations = @($events | Where-Object { $_.kind -in @('build','upgrade','sell') -and $_.detail.success -eq $true } | ForEach-Object {
    $sequence++
    $d = $_.detail
    $name = switch ([int]$d.type) { 1 {'普通塔'} 2 {'爆破塔'} 3 {'冰霜塔'} }
    [pscustomobject][ordered]@{
        step = $sequence
        after_wave = $d.afterWave
        before_wave = if ($_.state -eq 'Preparing') {([int]$d.afterWave + 1)} else {$null}
        during_wave = if ($_.state -eq 'RoundRunning') {$_.wave} else {$null}
        phase = if ($_.state -eq 'RoundRunning') {'mid_wave'} else {'between_waves'}
        trigger = $d.trigger
        action = $_.kind
        tower_type = $d.type
        tower_name = $name
        row_zero_based = $d.row
        column_zero_based = $d.col
        row_one_based = ([int]$d.row + 1)
        column_one_based = ([int]$d.col + 1)
        level_before = $d.levelBefore
        level_after = $d.level
        cost = $d.cost
        gold_before = $d.goldBefore
        gold_after = $d.goldAfter
        combat_seconds = $_.combatSeconds
        level_seconds = $_.levelSeconds
        utc = $_.utc
        success = $d.success
    }
})
$operations | Export-Csv -LiteralPath (Join-Path $runDir 'operations.csv') -NoTypeInformation -Encoding UTF8
$operations | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $runDir 'operations.json') -Encoding UTF8
$metrics.waves | Export-Csv -LiteralPath (Join-Path $runDir 'waves.csv') -NoTypeInformation -Encoding UTF8
$state.towers | Sort-Object row,col | Export-Csv -LiteralPath (Join-Path $runDir 'final-towers.csv') -NoTypeInformation -Encoding UTF8
$metrics | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $runDir 'final-metrics.json') -Encoding UTF8
Copy-Item -LiteralPath (Join-Path $runDir "attempt$Attempt-live.json") -Destination (Join-Path $runDir 'successful-run-events.json')
$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add('# 第一关零漏怪通关记录')
$lines.Add('')
$lines.Add('日期：2026-11-03；工程：E:/MyTowerGame；Unity 2022.3.62f3c1；MCP unityMCP / 8086。')
$lines.Add('')
$lines.Add("最终结果：25/25 波，生命 $($state.hp)/$($state.maxHp)，击杀 $($metrics.killed)，漏怪 $($metrics.leaked)，Boss 漏怪 $($metrics.bossLeaked)，debugOverride=$($metrics.debugOverride)。")
$lines.Add("成功出怪 $($metrics.successfulSpawned) / 预期 $($metrics.expectedEnemyCount)；战斗时间 $([math]::Round($metrics.combatElapsedSeconds,3)) 秒；关卡计时 $([math]::Round($metrics.levelElapsedSeconds,3)) 秒；剩余金币 $($state.gold)。")
$lines.Add("本次会话第 $Attempt 次尝试成功。未读取历史通关记录或历史防御塔布局；采用用户本轮提供的 user-reference-layout.png 作为新参考，并根据本次会话实时战斗反馈调整采购顺序与等级。")
$lines.Add('')
$lines.Add('## 执行条件')
$lines.Add('')
$lines.Add('- 从第一关空棋盘开始，恢复已存布局关闭（StartLevel(1, false)）；初始金币 100，生命 10。')
$lines.Add('- 使用现有游戏接口建塔、升级、开始波次与暂停；实时 Play Mode，游戏支持的 3 倍速。每波结束自动暂停，执行采购后恢复并开始下一波；波中采购在收入足够时立即执行。速度以 start_wave 和 speed_change_confirmed 事件中的实际值为准。')
$lines.Add('- 未修改游戏源码、配置、金币、生命、敌人属性或胜负状态；没有手动推进模拟或强制通关。正常游戏自身会保存本次进度和通关成绩。')
$lines.Add('- 坐标 row/col 均从 0 开始：row 从上到下 0–6，col 从左到右 0–12；CSV 另含从 1 开始的坐标。')
$lines.Add('- 类型 1=普通塔，2=爆破塔，3=冰霜塔。build 为建造一级塔，upgrade 为升一级。每行成功操作均有金币前后值与实际计时。')
$lines.Add('- between_waves：按“完成波次”执行同组操作，再开始下一波；完成波次 0 表示第一波开始前。mid_wave：在 during_wave 指定波次，按 trigger 和实际计时执行；first_affordable 表示金币首次足够，danger_pause 表示临近终点时暂停后补防。')
$lines.Add('- 采用图示五道蛇形墙体：col=1、3、5、7、9 交替留底部/顶部开口，中后段地面主路径长 42 格。末波首次需要改道时，正常出售 (0,9) 爆破塔打开上侧连接；之后在出口 col=12 的 row=2 与 row=4 间切换开口：先卖另一侧挡路的普通塔，再在敌人正接近的开口建一级普通塔。游戏正常重算路径，让剩余地面怪再次经过火力区。后续每次切换净花费 10 金币。实际操作和触发位置见操作表与 exit_route_switch 事件。')
$lines.Add('- 飞行怪不受绕行路线影响；对接近终点且仍存活的飞行怪设置提前暂停观察。相关暂停、恢复与调整以 successful-run-events.json 为准。')
$lines.Add('- 本游戏当前通关即给 5 星；零漏怪结论来自完整出怪/击杀/漏怪统计与满血结果。')
$lines.Add('')
$lines.Add('## 文件')
$lines.Add('')
$lines.Add('- final-victory.png：未经后期处理的完整 Game View 通关截图。')
$lines.Add('- operations.csv / operations.json：成功一局逐条实际建造、升级记录。')
$lines.Add('- successful-run-events.json：空棋盘起点、所有采购、波次开始/结束、结算的原始实战事件记录。')
$lines.Add('- waves.csv：25 波的预期出怪、实际出怪、击杀、漏怪、波后金币/生命和计时。')
$lines.Add('- final-towers.csv：最终坐标、塔型、等级、投入金币、累计伤害和对空命中。')
$lines.Add('- final-state.json / final-metrics.json：最终运行状态与统计。')
$lines.Add('- runtime-config.json / config-file-hashes.json：本次实测时读取的配置与初始哈希。')
$lines.Add('- console-errors.json：末次读取的 Unity 错误/断言；没有清空 Console。')
$lines.Add('')
$lines.Add('## 实际采购步骤')
$lines.Add('')
$lines.Add('| 步骤 | 阶段 | 完成波次/进行波次 | 操作 | 塔 | row,col | 等级 | 花费 | 金币前→后 |')
$lines.Add('|---:|---|---|---|---|---|---|---:|---|')
foreach ($op in $operations) {
    $actionText = if ($op.action -eq 'build') {'建造'} elseif ($op.action -eq 'sell') {'出售'} else {'升级'}
    $waveLabel = if ($op.phase -eq 'mid_wave') {"正在第 $($op.during_wave) 波"} else {"完成第 $($op.after_wave) 波"}
    $lines.Add("| $($op.step) | $($op.phase) | $waveLabel | $actionText | $($op.tower_name) | $($op.row_zero_based),$($op.column_zero_based) | $($op.level_before)→$($op.level_after) | $($op.cost) | $($op.gold_before)→$($op.gold_after) |")
}
$lines | Set-Content -LiteralPath (Join-Path $runDir 'README_操作与结果.md') -Encoding UTF8
[pscustomobject]@{operations=$operations.Count;waves=@($metrics.waves).Count;towers=@($state.towers).Count;victory=$metrics.victory;killed=$metrics.killed;leaked=$metrics.leaked;hp=$state.hp;gold=$state.gold} | ConvertTo-Json -Compress

