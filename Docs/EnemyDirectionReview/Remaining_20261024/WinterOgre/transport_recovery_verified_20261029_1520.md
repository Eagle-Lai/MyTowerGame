# WinterOgre 图像传输故障修复验证记录（2026-10-29 15:20）

记录人：WorkBuddy（受用户指示"读取 codex 相关内容，修复测试工程任务中的失败问题"）。
本文件为**新增独立证据**，不覆盖、不修改任何既有 uncertain/request/result/progress/chain 文件及 generate.mjs。

## 结论

任务阻断的根因是**间歇性网络传输故障**，分两层：

1. **直连大体积 multipart 上传被中途掐断**（Curl 55/56：71KB 处 abort、连接重置）——发生于 14:18~14:28 的多次尝试，为直连路径上的中间设备/运营商/边缘节点行为，与密钥、参数、端点无关（同期小请求直连全部正常）。
2. **上游短暂空回复窗口**（Curl 52：代理路径 660KB 完整上传后约 10 秒无任何 HTTP 字节即断开，revision_04 于 14:28:19）——中转站上游在该时间窗内处理异常。

**14:59 起线路已自行恢复**（同主线路 /v1/images/generations 连续 5 次 200）。本次按任务同形态复测，全部通过。

## 修复验证证据（2026-10-29 15:15~15:20）

免费（无鉴权，预期 401，不计费）：
- 未鉴权小图 multipart 直连：HTTP 401，0.30s，上传完整
- 未鉴权 655KB 任务双图直连：**HTTP 401，0.50s，655375B 完整上传**（上午 71KB 即断的缺陷已消失）
- 未鉴权 660KB 任务双图走 127.0.0.1:7897 代理（14:24 既有对照）：401，0.38s，完整上传

付费（鉴权，`POST https://aihub.dog/v1/images/edits`，与任务同 key）：
- **T1 最小形态直连**：gpt-image-2 / 1024x1024 / low / 1 张 564B 小图 / 中性提示词 → **HTTP 200**，21.6s，返回 1.55MB PNG
- **T2 生产形态直连**：gpt-image-2 / medium / 1536x1024 / 双参考图（WinterOgre.png 248591B + source_prefab_offline.png 405884B，SHA 与 request.json 一致）/ 中性提示词 → **HTTP 200**，27.7s，返回 1.16MB PNG（871KB 实图，已解码目验有效）

T1/T2 均为**传输验证**，使用中性提示词（红圆），非任务出图，产物存于 WorkBuddy 工作区，不进入 WinterOgre 证据链；既有 5 次不确定请求的目录与文件一律未动。

## 给恢复线程的执行配方

1. 直连 `--curl-transport`（不带 --system-local-proxy）当前可用，按协议正常恢复（先 Preflight、Unity 8088 身份/空闲核对）。
2. 若再次出现 **Curl 55/56（发送中断/重置）**：切换 `--system-local-proxy`（127.0.0.1:7897 上传路径已证可用）。注意 generate.mjs 第 20 行把代理 scope 限定为 WinterOgre Up revision_04 / Down 无 revision；换新 revision 使用代理需按变更协议先行扩 scope 并留痕。
3. 若再次出现 **Curl 52（上传完整但空回复）**：属上游处理窗口异常，等待 5~15 分钟后按协议单次重试，勿连续重复（上游确认正常响应需 20~40s；若 60s 内连接被无响应断开即为该故障）。
4. 判定"空回复"与"已出图"：无 request ID 可查，中转站无按请求明细端点（/v1/usage/logs 等 4 个路径均 404），只能以 /v1/usage 日聚合间接观察。

## 计费与余额（/v1/usage 实测）

- key（sk-473...，与聊天 key sk-7e08... 为两把不同 key）：有效，余额 **83.41**
- 今日（10-29）该 key 日聚合：20 次请求 / $1.25；其中含本任务 5 次"结果不明"请求（≈$0.5~1.0 疑似已被上游处理计费，无法逐笔确认），及本次 T1/T2 两次验证请求
- 10-28：33 次 / $2.22

## 关键路径备查

- 失败现场：`generation/Up/uncertain_result.json`（Curl55, 05:31Z）、`revision_03`（Curl55, 06:18Z 直连）、`revision_04`（Curl52, 06:28Z 代理）
- 既有诊断：`transport_fix_20261029.json`、`unauthenticated_upload_diagnosis_20261029_14*.json`
- 交接：`../conversation_handoffs/20261029_143535_WinterOgre_blocked.md`、`../../NEXT_ENEMY_TASK.md`
