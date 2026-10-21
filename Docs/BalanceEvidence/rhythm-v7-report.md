# 节奏验收报告 · balance-30x25-tight-v7 / D04

离线由 `balance_pipeline.generate()` 产出的解析计划计算，不含真实 Unity 证据。

## 7.2 逐项结论

| 指标 | 通过线 | 实测 | 结论 |
|---|---|---|---|
| 1 坎/普比 ≥1.40（坎波环比 ÷ 非坎波中位） | ≥ 1.40 | 1.567 | ✅ 通过 |
| 1b 坎/普比（备用口径：坎波 ÷ 前一普通波） | ≥ 1.40 | 1.441 | ✅ 通过 |
| 2 普通波环比区间 | [1.01, 1.30] | 1.020 ~ 1.312 | ⚠️ 未达标 |
| 3 相邻波数量环比 | ≤ 1.20 | 1.194 | ✅ 通过 |
| 4 开局可建塔数（L1） | [2.5, 3.5] | 3.12 | ✅ 通过 |
| 4b 开局可建塔数相邻关比值 | ≤ 1.25 | 1.200 | ✅ 通过 |
| 5 单关节拍（含波间空档） | [420, 540] s | 509.8 ~ 536.2 | ✅ 通过 |
| 6 单波 span W1 | [5, 9] s | 8.40 ~ 13.10 | ⚠️ 未达标 |
| 6b 单波 span W25 | [18, 28] s | 22.27 ~ 25.98 | ✅ 通过 |
| 8 漏怪痛感 | initialHp = 12 | 12 | ✅ 通过 |
| 9a 空军首现波 | W3 | W3 | ✅ 通过 |
| 9b 含飞行波间隔 | ≤ 5 波 | 1 | ✅ 通过 |
| 9c 空军占比（含飞行波） | [12%, 18%] | 11.1% ~ 13.0% | ⚠️ 未达标 |
| 派生 W25/W1 EHP 倍率 | [120, 200] | 148.6 ~ 199.5 | ✅ 通过 |

## 每关明细

| 关 | 开局金币 | 可建塔 | 时长 s | W1 span | W25 span | 坎比 W5/10/15/20/25 | 坎/普比 | W25÷W1 |
|---:|---:|---:|---:|---:|---:|---|---:|---:|
| 1 | 100 | 3.12 | 509.8 | 8.4 | 22.3 | 1.93/1.85/1.75/1.68/2.00 | 1.57 | 199.5 |
| 2 | 120 | 3.75 | 510.6 | 8.6 | 22.4 | 1.93/1.85/1.75/1.68/2.00 | 1.57 | 195.5 |
| 3 | 140 | 4.38 | 511.3 | 8.8 | 22.5 | 1.92/1.85/1.75/1.68/2.00 | 1.57 | 191.9 |
| 4 | 160 | 5.00 | 512.1 | 9.0 | 22.7 | 1.92/1.85/1.75/1.68/2.00 | 1.57 | 188.5 |
| 5 | 180 | 5.62 | 512.9 | 9.2 | 22.8 | 1.92/1.85/1.75/1.68/2.00 | 1.57 | 185.3 |
| 6 | 200 | 6.25 | 513.7 | 9.4 | 22.9 | 1.91/1.85/1.75/1.68/2.00 | 1.57 | 182.3 |
| 7 | 220 | 6.88 | 514.4 | 9.6 | 23.0 | 1.91/1.85/1.75/1.68/2.00 | 1.57 | 179.6 |
| 8 | 240 | 7.50 | 515.3 | 9.8 | 23.2 | 1.91/1.85/1.75/1.68/2.00 | 1.57 | 177.0 |
| 9 | 260 | 8.12 | 516.1 | 10.0 | 23.3 | 1.90/1.85/1.75/1.68/2.00 | 1.57 | 174.6 |
| 10 | 280 | 8.75 | 516.9 | 10.2 | 23.4 | 1.90/1.85/1.75/1.68/2.00 | 1.57 | 172.3 |
| 11 | 300 | 9.38 | 517.7 | 10.4 | 23.6 | 1.90/1.85/1.75/1.68/2.00 | 1.57 | 170.2 |
| 12 | 320 | 10.00 | 518.6 | 10.6 | 23.7 | 1.89/1.85/1.75/1.68/2.00 | 1.57 | 168.3 |
| 13 | 340 | 10.62 | 519.4 | 10.8 | 23.8 | 1.89/1.85/1.75/1.68/2.00 | 1.57 | 166.4 |
| 14 | 360 | 11.25 | 520.2 | 10.9 | 23.9 | 1.89/1.84/1.75/1.68/2.00 | 1.57 | 164.7 |
| 15 | 380 | 11.88 | 521.1 | 11.1 | 24.1 | 1.89/1.84/1.75/1.68/2.00 | 1.57 | 163.1 |
| 16 | 400 | 12.50 | 522.1 | 11.2 | 24.2 | 1.88/1.84/1.75/1.68/2.00 | 1.57 | 161.5 |
| 17 | 420 | 13.12 | 522.9 | 11.4 | 24.3 | 1.88/1.84/1.75/1.68/2.00 | 1.57 | 160.1 |
| 18 | 440 | 13.75 | 523.8 | 11.6 | 24.4 | 1.88/1.84/1.75/1.68/2.00 | 1.57 | 158.8 |
| 19 | 460 | 14.38 | 524.8 | 11.7 | 24.6 | 1.88/1.84/1.75/1.68/2.00 | 1.57 | 157.6 |
| 20 | 480 | 15.00 | 525.7 | 11.9 | 24.7 | 1.87/1.84/1.75/1.68/2.00 | 1.57 | 156.4 |
| 21 | 500 | 15.62 | 526.6 | 12.0 | 24.8 | 1.87/1.84/1.75/1.68/2.00 | 1.57 | 155.3 |
| 22 | 520 | 16.25 | 527.6 | 12.1 | 25.0 | 1.87/1.84/1.75/1.68/2.00 | 1.57 | 154.3 |
| 23 | 540 | 16.88 | 528.7 | 12.3 | 25.1 | 1.87/1.84/1.75/1.68/2.00 | 1.57 | 153.4 |
| 24 | 560 | 17.50 | 529.6 | 12.4 | 25.2 | 1.87/1.84/1.75/1.68/2.00 | 1.57 | 152.5 |
| 25 | 580 | 18.12 | 530.6 | 12.5 | 25.3 | 1.87/1.84/1.75/1.68/2.00 | 1.57 | 151.7 |
| 26 | 600 | 18.75 | 531.8 | 12.7 | 25.5 | 1.87/1.84/1.75/1.68/2.00 | 1.57 | 151.0 |
| 27 | 620 | 19.38 | 532.8 | 12.8 | 25.6 | 1.86/1.84/1.75/1.68/2.00 | 1.57 | 150.3 |
| 28 | 640 | 20.00 | 533.8 | 12.9 | 25.7 | 1.86/1.84/1.75/1.68/2.00 | 1.57 | 149.7 |
| 29 | 660 | 20.62 | 535.0 | 13.0 | 25.9 | 1.86/1.84/1.74/1.68/2.00 | 1.57 | 149.1 |
| 30 | 680 | 21.25 | 536.2 | 13.1 | 26.0 | 1.86/1.84/1.74/1.68/2.00 | 1.57 | 148.6 |

## Fill-gate（更严格的附加判据）

| 关 | 满驻防漏血 | 剩余血量 | 用时/Par | 备注 |
|---:|---:|---:|---:|---|
| 1 | 0 | 12 | 0.8724 | full maze (33/33): clear=True policy=True budget=True time=False ratio=0.872 leaked=0 |
| 2 | 0 | 12 | 0.942 | full maze (59/59): clear=True policy=True budget=True time=True ratio=0.942 leaked=0 |
| 3 | 1 | 11 | 0.8974 | full maze (52/52): clear=False policy=True budget=True time=False ratio=0.897 leaked=1 |
| 4 | 0 | 12 | 0.9827 | full maze (59/59): clear=True policy=True budget=True time=True ratio=0.983 leaked=0 |
| 5 | 0 | 12 | 1.0013 | full maze (52/52): clear=True policy=True budget=True time=True ratio=1.001 leaked=0 |
| 6 | 0 | 12 | 0.845 | full maze (58/58): clear=True policy=True budget=True time=False ratio=0.845 leaked=0 |
| 7 | 0 | 12 | 0.915 | full maze (55/55): clear=True policy=True budget=True time=True ratio=0.915 leaked=0 |
| 8 | 0 | 12 | 1.0435 | full maze (59/59): clear=True policy=True budget=True time=True ratio=1.043 leaked=0 |
| 9 | 0 | 12 | 0.9901 | full maze (59/59): clear=True policy=True budget=True time=True ratio=0.990 leaked=0 |
| 10 | 0 | 12 | 1.0285 | full maze (58/58): clear=True policy=True budget=True time=True ratio=1.028 leaked=0 |
| 11 | 0 | 12 | 1.0253 | full maze (48/48): clear=True policy=True budget=True time=True ratio=1.025 leaked=0 |
| 12 | 0 | 12 | 1.1142 | full maze (48/48): clear=True policy=True budget=True time=False ratio=1.114 leaked=0 |
| 13 | 0 | 12 | 0.8726 | full maze (59/59): clear=True policy=True budget=True time=False ratio=0.873 leaked=0 |
| 14 | 0 | 12 | 0.9932 | full maze (59/59): clear=True policy=True budget=True time=True ratio=0.993 leaked=0 |
| 15 | 0 | 12 | 1.0114 | full maze (60/60): clear=True policy=True budget=True time=True ratio=1.011 leaked=0 |
| 16 | 0 | 12 | 1.0188 | full maze (60/60): clear=True policy=True budget=True time=True ratio=1.019 leaked=0 |
| 17 | 0 | 12 | 0.9816 | full maze (49/49): clear=True policy=True budget=True time=True ratio=0.982 leaked=0 |
| 18 | 0 | 12 | 0.96 | full maze (56/56): clear=True policy=True budget=True time=True ratio=0.960 leaked=0 |
| 19 | 0 | 12 | 1.0749 | full maze (57/57): clear=True policy=True budget=True time=False ratio=1.075 leaked=0 |
| 20 | 0 | 12 | 1.0183 | full maze (58/58): clear=True policy=True budget=True time=True ratio=1.018 leaked=0 |
| 21 | 0 | 12 | 1.0119 | full maze (56/56): clear=True policy=True budget=True time=True ratio=1.012 leaked=0 |
| 22 | 0 | 12 | 0.8964 | full maze (56/56): clear=True policy=True budget=True time=False ratio=0.896 leaked=0 |
| 23 | 0 | 12 | 1.0307 | full maze (59/59): clear=True policy=True budget=True time=True ratio=1.031 leaked=0 |
| 24 | 0 | 12 | 1.0296 | full maze (59/59): clear=True policy=True budget=True time=True ratio=1.030 leaked=0 |
| 25 | 0 | 12 | 1.068 | full maze (58/58): clear=True policy=True budget=True time=False ratio=1.068 leaked=0 |
| 26 | 0 | 12 | 0.9566 | full maze (50/50): clear=True policy=True budget=True time=True ratio=0.957 leaked=0 |
| 27 | 0 | 12 | 1.0345 | full maze (60/60): clear=True policy=True budget=True time=True ratio=1.035 leaked=0 |
| 28 | 0 | 12 | 0.9531 | full maze (57/57): clear=True policy=True budget=True time=True ratio=0.953 leaked=0 |
| 29 | 0 | 12 | 1.0664 | full maze (58/58): clear=True policy=True budget=True time=False ratio=1.066 leaked=0 |
| 30 | 0 | 12 | 1.0896 | full maze (58/58): clear=True policy=True budget=True time=False ratio=1.090 leaked=0 |
