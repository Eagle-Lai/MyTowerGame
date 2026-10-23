# Prompt：按测试报告批量回放关卡并录制视频（静默无人值守）

> **用途**：把本文整段交给 AI Agent（WorkBuddy / Claude Code / Cursor 等），即可在本工程内实现「读操作序列 → Unity 固定步长回放 → 录制 mp4」的完整链路。
> **前置已核实**：本文所有路径、API 签名、JSON 字段、towerId 映射均由 2026-10-23 实地读码与读配置确认，可直接依赖，不需要重新猜测。
> **工作目录**：`E:\MyTowerGame`（Unity 2022.3.62f3c1）。家用机为 `D:\FreedomTower_1`，若在该版本执行需重新核对路径。

---

## 一、任务目标

对 `L01`–`L30` 共 30 个关卡，按每关已封存的**最优操作序列**，在 Unity 内以固定步长真实回放（真实 A*、真实战斗、真实经济，不注资不改血不跳波），并录制为 **mp4 视频**，每关一个文件，输出到 `Docs/LevelVideos/`。

视频验收标准：画面包含棋盘与 HUD，能看清每次建塔/升级/出售，时长与关卡完整时长一致（不是快放），波次推进与报告表格逐条对应。

---

## 二、硬约束（违反即返工）

1. **全程静默无人值守**（用户明确要求，最高优先级）
   - 禁止 `EditorUtility.DisplayDialog` / `DisplayProgressBar` / 任何模态窗口、任何需要点确认的交互。
   - 禁止抢占窗口焦点、禁止 `SetForegroundWindow` / `ShowWindow`、禁止打开新的 EditorWindow。
   - 进度与状态**只写日志文件**（`Debug.Log` + 落盘 JSON），不刷 `Debug.LogError`（会触发 Console 红色高亮与弹窗）。
   - 外部进程一律 `UseShellExecute=false` + `CreateNoWindow=true`，输出重定向到文件，不弹控制台。
   - 单关失败**不得中断整批**：记录失败原因，进入下一关，最后汇总。
   - 整批跑完后自行退出 PlayMode、恢复 GameView 原尺寸与语言，不残留 `SessionState` 键。

2. **不得改动数值与存档**
   - 禁止修改 `Luban/Config/Datas/**`、`Assets/ConfigJson/**`、`Assets/Gen/**`。
   - 禁止注资、改血、跳波、改倍速、改 `Time.timeScale`。
   - 必须走隔离测试存档：录制期间 `SaveManager.IsTestStorage` 必须为 `true`（`BalanceGameplayCapture.Begin` 已有该断言，照用）。
   - 不写正式游戏进度。

3. **不得为了"方便"绕开既有回放器**
   - 唯一回放入口是 `BalancePlayModeVerifier.StartBatch(string requestPath)`。不要另写一套模拟循环。

---

## 三、已核实的工程事实（直接使用，勿猜）

### 3.1 操作序列来源

| 关卡 | 路径 |
|---|---|
| L02–L30 | `Docs/BalanceEvidence/L02-L30-ManualBalance-100Gold/Lxx/best-operations.json` |
| L01 | `Docs/BalanceEvidence/L02-L30-ManualBalance-100Gold/L01-reference/best-operations.json` |

- 30 关全部齐备，条目数与报告「交易笔数」逐关一致（如 L02=87、L03=67、L30=155、L01=77）。
- 桌面「待测试文件夹」里**只有 .md 和 .png，没有 .json**；优先从工程取 json，报告仅用于核对。

### 3.2 操作 JSON 格式（实测样例）

```json
[
  { "waveOrdinal": 1, "timeMs": 0, "action": "build", "row": 3, "col": 1, "towerId": 1, "cost": 32, "balanceAfter": 68 }
]
```

- `action` ∈ `build` / `upgrade` / `sell`；`timeMs` 是**波内战斗时间**，`0` 表示波前执行。
- `towerId` 是 `TowerConfig.Id`，回放器用 `Configs.GetTowerSilent(towerId)` 解析；`upgrade` 还要求该格当前塔的 `Config.UpgradeTo == cfg.Id`。
- `cost` / `balanceAfter` 仅供对账，回放器不读。

### 3.3 towerId 映射（已从 `Assets/ConfigJson/tbtowerinfo.json` 核实）

| 塔 | id | 价格 | 升级目标 |
|---|---:|---:|---:|
| 普1 / 普2 / 普3 | 1 / 2 / 3 | 32 / 90 / 180 | 2 / 3 / 0 |
| 爆1 / 爆2 / 爆3 | 4 / 5 / 6 | 44 / 110 / 210 | 5 / 6 / 0 |
| 缓1 / 缓2 / 缓3 | 7 / 8 / 9 | 30 / 85 / 170 | 8 / 9 / 0 |

映射规则：`towerId = (type-1)*3 + level`，`type` 1=普通 2=爆破 3=减速。仅当必须从 .md 文本还原操作时才需要。

### 3.4 回放请求 JSON（`StartBatch` 读取）

```json
{
  "output": "Library/BalanceWorkbench/Video-L02",
  "stepSeconds": 0.0666667,
  "stepsPerUpdate": 1,
  "runs": [{
    "profileId": "D04",
    "levelId": 2,
    "strategy": "replay",
    "speed": 1,
    "waitForFunds": false,
    "captureStages": false,
    "screenshots": false,
    "operationsPath": "…/L02/best-operations.json"
  }]
}
```

- `stepSeconds` 合法区间 `(0, 0.1]`；`1/15 = 0.0667` 可用，`1/30 = 0.0333` 也可用。
- `operationsPath` 存在时走精确回放，`strategy` 不参与决策，填 `"replay"` 即可。
- 全部 30 关 `profileId` 均为 `D04`，`levelId` 取 1–30。

> ⚠️ **隐蔽陷阱**：`_plannedOperations` 只在 `File.Exists(run["operationsPath"])` 为真时才加载；路径写错或文件缺失时它**不会报错**，而是静默回落到 `Shop()` 自动买塔策略——你会录出一段"看起来正常但完全不是报告方案"的视频。
> 因此 `StartBatch` 前必须断言：文件存在、JSON 可解析、数组非空、条目含 `waveOrdinal`/`timeMs`/`action`/`row`/`col`/`towerId`，且条数与报告「交易笔数」一致；任一不符立即中止该关并记 `failed`。
> 同理 `renderedPerformance` 必须保持 `false`，否则会触发 `BalanceRenderSampler` 与 `BalanceGameplayCapture` 截图流程，干扰录制。

### 3.5 关键 API（`Assets/Scripts/Core/GameClock.cs`）

```csharp
GameClock.BeginManualSimulation()        // 返回 IDisposable，手动时钟接管
GameClock.StepManualFrame(double delta)  // 推进一步模拟（未 Begin 会抛异常）
GameClock.CombatElapsedSeconds           // 当前战斗累计秒
GameClock.Speed                          // 倍速，录制必须为 1
GameClock.SetBackground(bool)            // 录制中必须 SetBackground(false)
```

### 3.6 场景与配置

- 回放启动场景固定为 `Assets/Scenes/main.unity`（`StartBatch` 内部已写死）。
- 封印/运行时哈希：`0135233bbe9cd3e5595063faf8ef222cfca1c0806565061d900f507fd56db4ce`（`tblevelrating.json` 中 30 行完全一致，录制前应校验，不一致立即中止）。
- 菜单命名空间沿用 `Tools/塔防/数值验证/…`。

### 3.7 现成可复用的两段代码

- `Assets/Editor/Balance/BalanceGameplayCapture.cs`：**GameView 分辨率反射设置 + 恢复**的完整写法（`selectedSizeIndex`、`GameViewSize`、`AddCustomSize` / `RemoveCustomSize`、`ScreenCapture.CaptureScreenshot` 后校验 PNG 宽高）。直接搬这段逻辑，不要重写反射。
- `Assets/Editor/LubanExporter.cs:97`、`BalanceWorkbenchProcess.cs:189`：本工程既有的 `ProcessStartInfo` 静默调用写法，照抄风格。

---

## 四、必须先解决的三个拦路虎（否则一定失败）

### 拦路虎 1：单关 300 秒墙钟超时

`BalancePlayModeVerifier.cs:266`：

```csharp
if (EditorApplication.timeSinceStartup - _runWall > 300) { RecordResult(flow, run, "wall_timeout"); return; }
```

L02 完整时长 1075 秒，录制实际耗时必然超过 300 秒 → **必然被掐断**。
→ 改法：把 300 改成可配置项，读取 `run["wallTimeoutSeconds"]`，缺省仍为 300，录制请求里设 7200。

### 拦路虎 2：整批 3600 秒超时

`BalancePlayModeVerifier.cs:144`：

```csharp
if (EditorApplication.timeSinceStartup - _startWall > 3600) { Finish("batch_timeout"); return; }
```

30 关一起跑必然超。
→ 改法：改为读 `_request["batchTimeoutSeconds"]`，缺省 3600；批量时**一次只排 1 关**，由外部脚本循环触发，超时设为 7200。

### 拦路虎 3：固定步长与视频帧不对应

现有默认 `stepSeconds=0.05` + `stepsPerUpdate=40`，一次 update 推进 2 秒模拟，画面只反映 chunk 末尾 → 录出来会跳帧。
→ 录制模式必须 `stepsPerUpdate = 1`，`stepSeconds = 1/fps`，**每一步抓一帧**，模拟时间与视频帧严格 1:1。

---

## 五、录制方案（选定方案与理由）

**不要用 Unity Recorder，也不要用 OBS/系统录屏。**

- Unity Recorder 按**真实帧时间**录制，而本回放是固定步长快进，两者时钟不一致，输出会变成忽快忽慢的卡顿视频；且需改 `Packages/manifest.json` 联网拉包。
- OBS/系统录屏需要 GameView 前置、抢焦点，与「全程静默」直接冲突。

**采用：Unity 端逐帧抓取 → 原始像素经 stdin 管道送入 ffmpeg → 直接编码 mp4，零中间文件。**

理由：帧率由我们按模拟时间精确控制，画面绝对均匀；不落盘不产生几十 GB 临时 PNG；ffmpeg 进程 `CreateNoWindow` 完全静默。

### 5.1 新增 `Assets/Editor/Balance/BalanceVideoRecorder.cs`

```csharp
public static class BalanceVideoRecorder
{
    public static bool Running { get; }
    public static void Begin(string outputMp4, int width, int height, int fps, string ffmpegPath);
    public static void PushFrame();   // 抓当前 GameView 画面，写入 ffmpeg stdin
    public static bool End();         // 关 stdin、WaitForExit、返回 mp4 是否有效
    public static void Abort();
}
```

实现要点：

1. **ffmpeg 启动参数**（720p 示例）：
   ```
   -y -f rawvideo -pixel_format rgba -video_size 1280x720 -framerate 15 -i -
   -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p -movflags +faststart out.mp4
   ```
   `RedirectStandardInput=true`，`CreateNoWindow=true`，`UseShellExecute=false`。

2. **抓帧**：优先 `ScreenCapture.CaptureScreenshotAsTexture()`，`GetRawTextureData<byte>()` 取 RGBA32 后 `StandardInput.BaseStream.Write`。
   - 若该 API 在 `EditorApplication.update` 中返回空/黑屏（Editor 下有可能），**降级为** `ScreenCapture.CaptureScreenshot(png)` + 读文件回传，并在日志中标注降级原因；此时把 fps 降到 10 以控制 IO。
   - 抓帧后必须 `UnityEngine.Object.DestroyImmediate(tex)`，否则显存持续增长。

3. **分辨率**：照搬 `BalanceGameplayCapture` 的反射流程设置 GameView 为 FixedResolution，等待 `Screen.width/height` 与目标一致（给它 5 帧）；`End()` 时把 `selectedSizeIndex` 还原并 `RemoveCustomSize`，并校验 `GetTotalCount` 回到原值。

4. **HUD 必须可见**：HUD 是 Screen Space Overlay，不在相机 RT 里。**不要**改用 `Camera.targetTexture` 抓帧，会丢掉金币/生命/波次显示。

### 5.2 在 `BalancePlayModeVerifier` 里接钩子

- 新增 `_request["recordVideo"]`（bool）与 `_request["videoOutput"]`（string）、`_request["videoWidth"/"videoHeight"/"videoFps"]`。
- 在 `_levelInitialized` 初始化末尾（`_runWall = EditorApplication.timeSinceStartup;` 之前）：`recordVideo` 为 true 时 `BalanceVideoRecorder.Begin(...)`。
- 在主步进循环里，`GameClock.StepManualFrame(...)` 与 `_flowLate()` 之后、`UnityEngine.Rendering.SortingGroup.UpdateAllSortingGroups()` 之前，调 `BalanceVideoRecorder.PushFrame()`。
- **收口点只有一处**：`Finish(string phase)`（第 678 行）。在它第 682 行 `_manualClock.Dispose()` **之前**统一调用：
  ```csharp
  if (BalanceVideoRecorder.Running)
  {
      if (phase == "complete") BalanceVideoRecorder.End();   // 正常收尾，写 moov、校验时长
      else BalanceVideoRecorder.Abort();                     // 任何异常/取消立即终止 ffmpeg
  }
  ```
  不要在 `RecordResult` 里调，那只是单 run 结束，不是整批结束。
- 录制请求里 `keepPlaying` 必须为 `false`，否则结束后停在 PlayMode，下一关无法启动。

### 5.3 新增菜单

```
Tools/塔防/数值验证/录制关卡视频（单关）
Tools/塔防/数值验证/停止录制
```

菜单只负责：选关卡 → 生成 request JSON 到 `Library/BalanceWorkbench/video-request-Lxx.json` → `StartBatch(path)`。**不要弹配置对话框**，参数从 `SessionState` 或固定默认值取。

### 5.4 批量驱动

外部 Python 脚本 `Tools/record_level_videos.py`：

1. 逐关生成 request JSON（一关一个）。
2. 触发录制：优先用 Unity MCP `execute_menu_item`；MCP 不可用时写一个 `EditorPrefs`/`SessionState` 队列文件，由 `BalanceVideoRecorder` 的 `EditorApplication.update` 轮询消费（**不要**依赖点击菜单）。
3. 轮询 `Library/BalanceWorkbench/Video-Lxx/status.json`，直到 `phase` ∈ `complete` / `cancelled` / `exception` / `wall_timeout` / `operation_rejected` / `batch_timeout`，带超时。
   - `status.json` 现有字段：`phase`、`completed`、`total`、`elapsedSeconds`、`round`、`combatMs`、`levelMs`、`hp`、`gold`。
   - `phase == "running"` 时 `completed/total` 均为 1（一次只排一关）。
   - 成功判据以 `phase == "complete"` 且 `Library/…/unity-results.json` 中 `leaked == 0` 为准，不要只看 status。
4. 所有关卡串行，独占编辑器，不并行。

---

## 六、参数（默认值，可用命令行覆盖）

| 参数 | 默认 | 说明 |
|---|---|---|
| 分辨率 | `1280x720` | 1080p 时管道约 124 MB/s，编码易掉帧，仅在确认机器跟得上时再开 |
| 采集帧率 | `15` fps | `stepSeconds = 1/15 = 0.0666667` |
| 输出帧率 | `30` fps | ffmpeg 加 `-r 30`，靠复制帧补齐，观感更顺 |
| 时间轴 | 1x | 模拟时间与视频时间一致，不做快放 |
| 编码 | `libx264 / crf 20 / veryfast / yuv420p` | 兼容播放器与网页 |
| 单关墙钟超时 | `7200` 秒 | 见拦路虎 1 |
| 批量超时 | `7200` 秒 | 见拦路虎 2，且一次只排 1 关 |
| 输出目录 | `Docs/LevelVideos/Lxx/Lxx_完整通关.mp4` | 与 `Docs/BalanceEvidence` 同级归档 |

**耗时预估**：L02 完整 1075.88 秒 → 约 16000 帧 → 单关 10–15 分钟；30 关合计约 5–7 小时。属于过夜任务，必须能断点续跑（已存在的有效 mp4 跳过）。

### ffmpeg 获取（本机没有）

- 目标目录：`C:\Users\Administrator\.workbuddy\tools\ffmpeg\bin\ffmpeg.exe`（**放在工程外**，避免进 git）。
- 下载源任选其一：
  - `https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip`
  - `https://github.com/BtbN/FFmpeg-Builds/releases`（`ffmpeg-master-latest-win64-gpl.zip`）
- **本机必须走代理**：先读环境变量 `http_proxy` 取端口（不要硬编码，历史上 7897/62114/56630 都变过）；大文件用 `curl -L -C -` 断点续传，单次 `--max-time` 不超过 900 秒。
- 装完跑 `ffmpeg -version` 校验，把绝对路径写进 `Tools/record_level_videos.py` 的配置，不要依赖 PATH。

---

## 七、实施顺序（每步都要有可验证的产出）

| 阶段 | 动作 | 验收 |
|---|---|---|
| P1 | 下载配置 ffmpeg | `ffmpeg -version` 输出正常 |
| P2 | 新增 `BalanceVideoRecorder.cs` | 编译 0 error；`refresh_unity` 后无 CS 错误 |
| P3 | 改两处超时为可配置 | 默认值不变（300/3600），仅新增字段，不回归既有回放 |
| P4 | 接钩子 + 菜单 | 单关 L02 能跑通，产出可播放 mp4 |
| P5 | 抽帧核对 | 从 mp4 抽 5 帧，塔位与 `L02/最终布阵图.png` 一致 |
| P6 | 批量脚本 | 串行跑完 30 关，产出 30 个 mp4 + 汇总 json |

---

## 八、验收标准（逐条必须成立）

1. 30 个 mp4 全部可播放，`ffprobe` 显示分辨率 1280x720、H.264、yuv420p。
2. 每个视频时长 ≈ 报告中的「完整关卡秒数」±3%（L02 应约 1075 秒）。
3. 视频内金币/生命变化与报告「逐波结果与现金流」对得上（抽查 L02 第 1、13、25 波）。
4. 最后一帧的塔位、塔数与报告「最终逐塔清单」一致（L02 = 50 座：普通 28 / 群攻 17 / 减速 5）。
5. 录制结束后：`EditorApplication.isPlaying == false`，GameView 尺寸回到原值，`SessionState` 无 `FT.Balance.*` 残留。
6. 正式存档 mtime 未变；`ConfigJson` 与 `Luban/Config/Datas` 的哈希未变。
7. 全过程无任何弹窗，无焦点抢占，无人工介入。
8. 完整录像中，第 25 波结束后应呈现胜利结算画面，不得提前截断。

---

## 九、失败处理

| 现象 | 处理 |
|---|---|
| `Scene_or_config_timeout` | 配置未加载完，等 Launcher 完成；查 `Configs.IsLoaded` |
| `operation_rejected` | 操作时间点金币不足或塔位不符 → 说明 `operationsPath` 与当前配置不匹配，**不要改数值迁就**，先核对封印哈希 |
| `wall_timeout` / `batch_timeout` | 超时未被替换成功，回查 4.1 / 4.2 |
| mp4 只有开头几秒 | ffmpeg stdin 提前关闭，检查 `End()` 是否在异常路径被调用两次 |
| 画面全黑 | `CaptureScreenshotAsTexture` 在 Editor 下失效 → 走 PNG 降级路径 |
| 画面无 HUD | 误用了 `Camera.targetTexture`，改回屏幕抓取 |
| 编译中断 MCP | 等 5 秒重连，重新 `set_active_instance` 并核对 `data.projectRoot == E:/MyTowerGame` |
| 录制中 Unity 崩溃 | 检查是否握有 `Texture2D` 未销毁导致显存爆掉；每帧必须 `DestroyImmediate` |

---

## 十、明确禁止

- 禁止装 `com.unity.recorder` 或任何新 UPM 包来解决录制。
- 禁止用系统录屏软件、禁止 `ScreenRecording` 类第三方工具。
- 禁止为了让回放"通过"而改 `best-operations.json` 的 `timeMs` 或金额。
- 禁止用 md 表格文本反推操作序列（除非对应 json 缺失，且需逐条与报告对账并在日志中记录）。
- 禁止把视频、帧序列、ffmpeg 放进 git 仓库（`Docs/LevelVideos/**` 应加入 `.gitignore` 或仅保留小样本）。
- 禁止在 `Assets/` 下生成任何录制产物。

---

## 十一、交付物清单

```
Assets/Editor/Balance/BalanceVideoRecorder.cs          新增
Assets/Editor/Balance/BalancePlayModeVerifier.cs       改：两处超时可配置 + 抓帧钩子
Tools/record_level_videos.py                           新增：批量驱动
Docs/LevelVideos/L01..L30/Lxx_完整通关.mp4             产出
Docs/LevelVideos/record-summary.json                   产出：每关时长/帧数/校验结果
Docs/Prompt_关卡回放视频录制.md                        本文
```

完成后按工程规范更新 `.workbuddy/memory/2026-10-23.md`，并在 `Docs/` 写一份录制报告（含 ffprobe 实测值、抽帧比对结论、异常关列表）。

---

## 十二、实测落地记录（2026-10-23，L02 首次跑通）

以下是在本机真实执行后确认的事实，**优先于第三节的初版设计**。重做时直接照这里来。

### 12.1 抓帧方案必须换：`CaptureScreenshotAsTexture` 不可用

`ScreenCapture.CaptureScreenshotAsTexture()` 在 `EditorApplication.update` 阶段调用返回 `null`，Console 报：

```
CaptureScreenshotAsTexture() failed to generate texture!
Was method called before the 'end of frame' state was reached?
```

→ 改用 **`ScreenCapture.CaptureScreenshot(path)` 异步落盘 + 编号 PNG 序列**，整关跑完后由 ffmpeg 一次性合成：

```
ffmpeg -y -framerate 16.667 -i "frame_%06d.png" -c:v libx264 -preset veryfast -crf 20 \
       -pix_fmt yuv420p -r 30 -movflags +faststart out.mp4
```

- 每帧要等 PNG 落盘才能推进下一步，所以 `Ready` 必须由 `ProbeReady()` 在等待期间解析，**不能只在 PushFrame 里置位**（否则死锁：验证器等 Ready 才肯步进，而 Ready 只有步进后调 PushFrame 才会置位）。
- 落盘后必须校验 PNG 头里的真实宽高，不能只信 `Screen.width`。
- 帧目录约 `718×1280×4B ≈ 单关 3–5 GB`，必须在 `End()` 成功后自动清理，且 `Docs/LevelVideos/**` 已加入 `.gitignore`。

### 12.2 GameView 被最小化时画面尺寸会静默错位

最小化状态下 `Screen.width/height` 仍报告 1280×720，但真实渲染目标只有 `100×957`，Console 报：

```
CaptureScreenshot(L:0, B:0, W:1280, H:720) requested a region that exceeds
the active Render Target sized [W:100, H:957]
```

→ `Begin()` 里先检查宿主窗口是否最小化（`IsIconic`），用 `ShowWindow(hwnd, 4)`（`SW_SHOWNOACTIVATE`）恢复，**不激活、不抢焦点**。恢复后再设 GameView 尺寸。

### 12.3 残留的 `cancel.request` 会让下一批开机即死

`Cancel()` 会在 `output` 目录写 `cancel.request` 作为取消信号，但原实现 `Finish()` 后不清除。下次运行的 `Update()` 第一行就命中该文件，直接 `Finish("cancelled")`，表现为"点了录制却什么都没发生"。

→ `Finish()` 收尾时必须删除该文件。

### 12.4 游戏内倍速对固定步长回放完全无效

`BalancePlayModeVerifier` 调用 `GameClock.StepManualFrame(step / Speed)`，而 `GameClock.StepManualFrame` 内部是 `_cachedDelta = unscaledDelta * _speed`，两者正好抵消，**每步推进的模拟时长恒为 `step`**。

结论：**点游戏左下角的 2x 按钮既不会加快录制，也不会让视频变快**，只会改 `Speed` 这个字段值。
真正的倍速只能在输出端做：

```
ffmpeg -i in.mp4 -vf "setpts=0.5*PTS" -r 30 -c:v libx264 -crf 20 ... out_2x.mp4
```

已提供 `Tools/make_video_speed.py L02 --speed 2` 做这件事，源文件保留。

### 12.5 实测速度基准（L02）

| 指标 | 实测 |
|---|---|
| 模拟步长 | 0.02 秒（与存档证据一致，勿改大，否则可能改变战斗结果） |
| 采样 | stride=3 → 16.667 fps |
| 推进速度 | 约 1.0–1.05 倍实时（模拟 332 秒耗墙钟 321 秒） |
| 单关总时长 | L02 约 17–18 分钟 |

### 12.6 触发方式

`EditorApplication.ExecuteMenuItem` 与 MCP 的 `execute_menu_item` 都可能返回成功但实际未进入 PlayMode；最可靠的是 MCP `execute_code` 里直接调用：

```csharp
FTProject.EditorTools.BalancePlayModeVerifier.RunVideoCapture();
```

调用后必须复核三件事：`playing=True`、`status.json` 的 `phase` 变为 `running`、`_frames_*` 目录开始出现 PNG。

