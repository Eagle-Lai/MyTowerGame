# AI 交付实施手册 · 界面补全

> 本手册是 `Docs/ArtDesign_坚守阵地_补全策划案_v1.md` 的**执行配套**。
> 策划案回答"做成什么样"，本手册回答"**怎么一步步做出来、怎么验证**"。
> **目标读者：接手本工程执行的 AI / 开发者。照着做即可，不需要额外追问。**

---

## 〇、执行前必读（5 条铁律）

```
1. 所有改动都在本工程内进行
2. 所有 prefab 一律走 UIPrefabBuilder 生成，禁止手搓
3. 跑任何生成类菜单前，必须确认 isCompiling == false && isPlaying == false
4. 每改一个 .cs，立刻跑 §四 的静态校验
5. 每完成一个界面，必须实机截图验证（Unity MCP screenshot）
```

⚠️ **第 3 条的后果**：如果编译未完成就跑生成器，会用**旧程序集**静默生成**旧结果**——
表面上"命令执行成功"，实际上生成的还是上一版 prefab。这是本工程反复踩过的坑。

---

## 一、环境与工具

### 1.1 运行环境

| 项 | 值 |
|---|---|
| Unity | 2022.3.62f3c1，Built-in RP（**无后处理**，发光只能烘进贴图） |
| 主场景 | `Assets/Scenes/Main.unity`（**单场景架构**，靠常驻根节点 + 管理器） |
| Unity MCP | 可用（`read_console` / `execute_code` / `screenshot` / 菜单调用） |
| Python | `C:\Users\lzy\.workbuddy\binaries\python\versions\3.13.12\python.exe` |

### 1.2 关键目录

```
Assets/Editor/UIPrefabBuilder.cs        ← UI prefab 生成器（主战场）
Assets/Editor/UISkinArtGenerator.cs     ← UI 皮肤贴图生成器（配色令牌源）
Assets/Editor/SceneMainBuilder.cs       ← 主场景搭建
Assets/Scripts/UI/*.cs                  ← 各界面 View
Assets/Scripts/Core/UI/UIManager.cs     ← 界面打开/关闭
Assets/Scripts/Core/Res/ResTable.cs     ← 资源逻辑名登记（唯一寻址源）
Assets/Scripts/Core/Res/YooAssetResLoader.cs  ← 热更新（需扩展）
Assets/Scripts/Core/Event/EventName.cs  ← 事件名
Assets/Prefabs/UI/*.prefab              ← 产出的界面资产
Docs/ui_mockups/*.svg                   ← 效果图（几何唯一参照）
.workbuddy/tools/                       ← 静态校验脚本
```

---

## 二、执行顺序（严格按此推进）

### 阶段一 · 启动链路（上线阻塞，必须最先做）

```
步骤 1.1  扩展 YooAssetResLoader：CheckUpdateCo / DownloadCo / Pause / Resume
步骤 1.2  新增 EventName：SplashFinished / LoadingProgress / HotUpdate* / OpenMainMenu ...
步骤 1.3  ResTable 登记 9 个新界面逻辑名
步骤 1.4  UIPrefabBuilder 新增 BuildSplash / BuildLoading / BuildHotUpdate
步骤 1.5  写 SplashView.cs / LoadingView.cs / HotUpdateView.cs
步骤 1.6  改造 Launcher.BootResAndConfig：拆分阶段 + 派发进度事件
步骤 1.7  跑校验 + 实机截图
```

### 阶段二 · 门面与内容

```
步骤 2.1  UIPrefabBuilder 新增 BuildMainMenu + MainMenuView.cs
步骤 2.2  改造 GameFlowManager.OnConfigLoaded：先进主菜单
步骤 2.3  UIPrefabBuilder 新增 BuildTowerCodex + TowerCodexItem + TowerCodexView.cs
步骤 2.4  UIPrefabBuilder 新增 BuildLevelDetail + LevelDetailView.cs
步骤 2.5  改造 SelectView：点居中卡 → 先开详情
步骤 2.6  跑校验 + 实机截图
```

### 阶段三 · 打磨

```
步骤 3.1  BuildSellConfirm + SellConfirmView.cs + 改造 GameFlowManager.OnTowerSellRequest
步骤 3.2  BuildConfirm + ConfirmView.cs + 接入 SettingView/MainMenuView
步骤 3.3  CameraController 加屏幕震动
步骤 3.4  切关 Loading 遮罩
步骤 3.5  BuildMonsterCodex + MonsterCodexItem + MonsterCodexView.cs
步骤 3.6  跑校验 + 实机截图
```

---

## 三、核心接口速查

### 3.1 CreateDialogShell（所有新界面都用它）

```csharp
/// 生成"全屏 Bg + Panel + Title"的标准骨架。
/// 【为什么必须用它】三个既有界面（Select/Pause/Setting）共用同一骨架，
///   各抄一遍迟早分叉 —— 而"改一处忘一处"正是本项目反复踩的坑。
///
/// stretchInset >= 0f  → 整页口径：Panel 四边各内缩该值铺满屏幕（panelSize 忽略）
/// stretchInset <  0f  → 弹窗口径：Panel 居中，尺寸 = panelSize
private static GameObject CreateDialogShell(
    string rootName,          // prefab 名，如 "MainMenuView"
    string title,             // 标题文字（整页 64 号，弹窗 48 号，由本方法自动定）
    Vector2 panelSize,        // 弹窗尺寸；整页传 Vector2.zero
    EditorUtil.Report report,
    out GameObject panel,     // ★ 输出 Panel，后续所有子节点挂它下面
    float stretchInset = -1f);

// 用法示例（整页）：
GameObject panel;
GameObject root = CreateDialogShell("MainMenuView", "主菜单",
    Vector2.zero, report, out panel, 0f);
root.AddComponent<MainMenuView>();
// → 之后 CreateText(panel.transform, ...) / CreatePanelButton(panel.transform, ...)
```

### 3.2 子节点创建

```csharp
// 按钮（anchoredPos 以 Panel 中心为原点）
private static void CreatePanelButton(
    Transform parent, string name, string label,
    Vector2 anchoredPos,
    float width = 340f,
    bool primary = false,      // true = 青色实心主按钮
    float height = 84f,
    float fontSize = 32f);

// 文字（统一 TMP，禁止 UGUI Text）
private static void CreateText(
    Transform parent, string name, string content,
    Vector2 anchor,            // 如 new Vector2(0.5f, 0.5f)
    Vector2 anchoredPos,
    Vector2 size,
    TextAnchor align,          // TextAnchor.MiddleCenter
    int fontSize,
    Color? color = null);

// 九宫格贴图
private static void ApplySlicedSkin(Image img, string spriteName, Color fallbackColor);
// 例：ApplySlicedSkin(img, "UI_Panel_Cyan", new Color(0.12f, 0.16f, 0.24f, 0.96f));
// ★ 生成的 Image 必须 type = Sliced，否则切角被拉成斜楔
```

### 3.3 Report 上报

```csharp
EditorUtil.Report report = new EditorUtil.Report();
report.Head("生成 XxxView → " + path);
report.Ok("...");
report.Warn("...");
report.Error("...");
int errCount = report.Errors;   // 属性，用于决定是否 SaveAssets
```

### 3.4 Unity MCP 调用范式

```python
# 1) 确认不在编译/播放
mcp__unity__execute_code(code="EditorApplication.isCompiling || EditorApplication.isPlaying")
# 期望 false

# 2) 跑生成器（用无弹窗入口，带 DisplayDialog 的会阻塞编辑器）
mcp__unity__execute_code(code="FTProject.EditorTools.UIPrefabBuilder.BuildNoDialog()")

# 3) 读控制台
mcp__unity__read_console(action="get", types=["error"])

# 4) 截图
mcp__unity__screenshot()
```

---

## 四、静态校验（每改必跑）

```bash
# 在工程根目录下执行
PY=C:/Users/lzy/.workbuddy/binaries/python/versions/3.13.12/python.exe
$PY .workbuddy/tools/check_code.py         # 代码扫描
$PY .workbuddy/tools/check_ui_contract.py  # UI 节点契约（Find 的节点名 vs prefab）
$PY .workbuddy/tools/check_events.py       # 事件订阅/派发配对
$PY .workbuddy/tools/check_members.py      # 成员引用
$PY .workbuddy/tools/check_arity.py        # 方法参数元数
$PY .workbuddy/tools/check_usings.py       # using 完整性
$PY .workbuddy/tools/check_svg_layout.py   # 效果图排版（0 重叠 / 0 越界）★改 SVG 后必跑
```

⚠️ 三条硬约束：

1. **`check_code.py` 只扫 `Get("字面量")`，不扫 `Configs.ConfigKeys`** → 改 `ResTable` 后必须**手工同步**。
2. **`check_arity.py` 的 `_CHANGED` 不许留已删文件** → 新增 .cs 要加进去，删了要移除。
3. **shell 跑 Python 别用 `\s` / `\b` / `\w`** → 会被 shell 转义。

⚠️ 若 `check_svg_layout.py` 报 XML 解析失败 → 用 `$PY .workbuddy/tools/fix_svg_comments.py` 修注释（见陷阱 #25）。

---

## 五、每个界面的标准作业流程（SOP）

以 `MainMenuView` 为例：

```
① 读效果图
   Docs/ui_mockups/18_MainMenuView.svg
   → 记下每个节点的坐标（SVG 坐标 → 画布坐标：X = x_svg − 960，Y = 540 − y_svg）

② 加资产常量
   在 UIPrefabBuilder 顶部：
   public const string MainMenuPath = "Assets/Prefabs/UI/MainMenuView.prefab";

③ 写 Build 方法
   private static void BuildMainMenu(EditorUtil.Report report)
   {
       // 【必须】重建前安全检查
       string extra;
       if (!EditorUtil.IsSafeToRebuild(MainMenuPath, MainMenuChildren, out extra))
       {
           report.Error("MainMenuView.prefab 检测到生成器不识别的节点：" + extra + "　→ 已中止");
           return;
       }
       AssetDatabase.DeleteAsset(MainMenuPath);
       EditorUtil.EnsureFolderOfFile(MainMenuPath);

       GameObject panel;
       GameObject root = CreateDialogShell("MainMenuView", "主菜单",
           Vector2.zero, report, out panel, 0f);
       root.AddComponent<MainMenuView>();

       // 按效果图坐标逐个 CreateText / CreatePanelButton / 手搓 Image
       ...
   }

④ 注册到 BuildInternal + EnsureMissing
   → BuildInternal 里调用 BuildMainMenu(report)
   → EnsureMissing 的补缺列表加上 MainMenuPath

⑤ 写 View 脚本
   Assets/Scripts/UI/MainMenuView.cs
   → 用 transform.Find("Panel/StartBtn") 取节点
   ⚠️ 节点名必须与生成器一致（契约无映射层，写岔只静默打「缺少节点」）

⑥ ResTable 登记
   Add("MainMenuView", "ui_mainmenu", "Assets/Prefabs/UI/MainMenuView.prefab");

⑦ 跑生成器 + 校验 + 截图
```

---

## 六、常见陷阱清单（**逐条对照，不要跳**）

| # | 陷阱 | 症状 | 规避 |
|---|---|---|---|
| 1 | 编译未完成就跑生成器 | 命令"成功"但生成旧结果 | 先查 `isCompiling == false` |
| 2 | 手搓 prefab 而不走生成器 | 下次全量重建被 `IsSafeToRebuild` 判为陌生节点 → 中止 | 一律走 `CreateDialogShell` |
| 3 | 新增节点名与 View 的 `Find` 不一致 | 静默打「缺少节点」，界面空白 | 成对改 + `check_ui_contract.py` |
| 4 | 用 UGUI `Text` | 中文缺字形 | 统一 TMP |
| 5 | 九宫格图没设 `type = Sliced` | 四角拉成斜楔 | `ApplySlicedSkin` 已处理，别绕过 |
| 6 | `border < 切角 + 发光半径` | 拉伸时四角变形 | 用 §2.4 的现成尺寸表 |
| 7 | 塔按钮锚点写左下 | 整排塔按钮出屏、无法建塔 | 必须 `(0.5, 0.5)` |
| 8 | LoopListView2 的 `InitListView` 调两次 | 列表错乱 | `_listInited` 守护（界面复用） |
| 9 | 条目 `onClick` 重复挂 | 滚动一圈后点一次触发 N 次 | 只在 `IsInitHandlerCalled` 首次为 false 时挂 |
| 10 | 用 `mOnSnapItemFinished` 判断"滑到位" | 提前触发/传错索引 | 每帧轮询目标条目到视口中心距离 |
| 11 | `Viewport.pivot.x` 不是 0 | 所有卡片跑偏 350px | 预置 0，用 `offsetMin/offsetMax` 描述矩形 |
| 12 | 缩放入口条目**根节点** | 卡片偏心 | 缩放挂 `Body` 子节点（根 pivot=(0,0.5)） |
| 13 | 新增生僻字不验证字体图集 | 新字渲染成**空白且不报错** | `SiYuanSongTi SDF.asset` 必须动态+多图集；`TryAddCharacters("难★")` 验证 |
| 14 | 破坏 YooAsset 三步初始化契约 | 之后每次加载报 `Active package manifest not found.` | `InitializePackageAsync` → `RequestPackageVersionAsync` → `LoadPackageManifestAsync`（最后 `SetActiveManifest`） |
| 15 | 截图丢失 Overlay 层 | 界面看不到 | 重截即可（已知偶发） |
| 16 | 往 `BoardRoot` 等常驻节点建东西不清空 | 切关后残留"幽灵格子/幽灵塔" | 自带清空并登记到 `TeardownLevel` |
| 17 | 新增 `PlayerPrefs` | 违反存档规范 | 只走 `SaveManager`（例外 `KeyProvider`） |
| 18 | 改 `ResTable` 后不跑 `check_code.py` | 漏登记不报错 | 该脚本扫不到 `ConfigKeys`，必须手工同步 |
| 19 | 热更新的版本比对插错位置 | 清单加载失败 | 必须插在 `RequestPackageVersionAsync` 之后、`LoadPackageManifestAsync` 之前 |
| 20 | 进度条直接赋真实值 | 数字"啪"地跳变 | DOTween 0.3s EaseOut 补间 |
| 21 | **按钮/导航元素压住卡片或面板内容** | 图上"看着还行"，实机叠在一起点不到 | 按策划案的 y_svg 分段排布，跑 `check_svg_layout.py` 回归 |
| 22 | **元素超出面板底边** | 按钮悬在弹窗外面 | 面板高度按内容反算，底部留 ≥68px；本策划案已把 SellConfirm→620 / Confirm→560 / LevelDetail→900 / TowerInfo→486 |
| 23 | **元素超出画布 0..1080** | 底部按钮被裁 | 最底元素 ≤ 1006（预留 74px 给注解/安全区） |
| 24 | **图鉴箭头压住 peek 邻卡** | 邻卡标题被箭头挡住 | 箭头必须落在卡片列几何之外（TowerCodex：x ≤ 200 或 ≥ 1720） |
| 25 | SVG 注释里写 `--` | 整张图 XML 解析失败、浏览器不渲染 | 注释体禁连续 `--`、禁 `-` 结尾；`fix_svg_comments.py` 批量修 |
| 26 | 改完效果图不重跑排版校验 | 旧错误复发 | 每次改 SVG 后必跑 `check_svg_layout.py`（期望 0 重叠 0 越界） |

---

## 七、热更新专项（阶段一最关键）

### 7.1 现状

`YooAssetResLoader.cs` 已完成：

```
✅ InitializePackageAsync      初始化包裹
✅ RequestPackageVersionAsync  请求版本
✅ LoadPackageManifestAsync    加载清单（最后 SetActiveManifest）
❌ UpdatePackageVersionAsync   版本比对        ← 缺
❌ CreateResourceDownloader    差异下载        ← 缺
❌ 下载进度回调 / 暂停 / 续传    ← 缺
```

### 7.2 需要新增的代码骨架

```csharp
#if USE_YOOASSET
/// <summary>
/// 检查并执行资源更新。
/// 【为什么单独一个方法】它必须插在 RequestPackageVersionAsync 之后、
///   LoadPackageManifestAsync 之前 —— 放错位置会让包清单与下载结果不一致，
///   后续所有加载都报 Active package manifest not found.
/// </summary>
public IEnumerator CheckAndUpdateCo(
    Action<string> onPhase,                 // 阶段文案（驱动 PhaseText）
    Action<int, int> onProgress,            // (已下载文件数, 总文件数)
    Action<long, long> onBytes,             // (已下载字节, 总字节)
    Action<string> onError,
    Action<bool> onDone)                    // 参数：是否发生过更新
{
    // 1) 请求远端最新版本
    var versionOp = _package.UpdatePackageVersionAsync();
    yield return versionOp;
    if (versionOp.Status != EOperationStatus.Succeed)
    {
        onError?.Invoke(versionOp.Error);
        yield break;
    }
    string latest = versionOp.PackageVersion;
    if (latest == _package.GetPackageVersion())
    {
        onDone?.Invoke(false);              // 版本一致，无需更新
        yield break;
    }

    // 2) 拉取最新清单
    var manifestOp = _package.UpdatePackageManifestAsync(latest);
    yield return manifestOp;
    if (manifestOp.Status != EOperationStatus.Succeed)
    {
        onError?.Invoke(manifestOp.Error);
        yield break;
    }

    // 3) 创建下载器并执行
    var downloader = _package.CreateResourceDownloader(10, 3);  // 并发10, 重试3
    if (downloader.TotalDownloadCount == 0)
    {
        onDone?.Invoke(false);
        yield break;
    }
    downloader.OnDownloadProgressCallback = (cur, total, bytes, totalBytes) =>
    {
        onProgress?.Invoke(cur, total);
        onBytes?.Invoke(bytes, totalBytes);
    };
    downloader.BeginDownload();
    yield return downloader;
    if (downloader.Status != EOperationStatus.Succeed)
    {
        onError?.Invoke(downloader.Error);
        yield break;
    }
    onDone?.Invoke(true);
}
#endif
```

### 7.3 验收（必测）

- [ ] 本地起一个 http 服务放新版本资源 → 真机包能检测到更新并下载
- [ ] 下载完重进游戏，加载的是新资源
- [ ] 断网 → 显示失败 + 重试可恢复
- [ ] 下载中暂停 → 网络请求停止；继续 → 续传
- [ ] 全程**不出现** `Active package manifest not found.`

---

## 八、交付物清单

| 文件 | 说明 | 状态 |
|---|---|---|
| `Docs/ArtDesign_坚守阵地_补全策划案_v1.md` | 美术与效果图策划案（主文档） | ✅ 已产出 |
| `Docs/AI交付实施手册_界面补全.md` | 本手册 | ✅ 已产出 |
| `Docs/ui_mockups/15_SplashView.svg` | 开屏页效果图 | ✅ 已产出 |
| `Docs/ui_mockups/16_LoadingView.svg` | 加载进度效果图 | ✅ 已产出 |
| `Docs/ui_mockups/17_HotUpdateView.svg` | 热更新效果图 | ✅ 已产出 |
| `Docs/ui_mockups/18_MainMenuView.svg` | 主菜单效果图 | ✅ 已产出 |
| `Docs/ui_mockups/19_TowerCodexView.svg` | 塔图鉴效果图 | ✅ 已产出 |
| `Docs/ui_mockups/20_MonsterCodexView.svg` | 怪物图鉴效果图 | ✅ 已产出 |
| `Docs/ui_mockups/21_LevelDetailView.svg` | 关卡详情效果图 | ✅ 已产出 |
| `Docs/ui_mockups/22_ConfirmView.svg` | 确认弹窗（含出售）效果图 | ✅ 已产出 |
| `Assets/Editor/UIPrefabBuilder.cs` | 需新增 9 个 Build 方法 | ⬜ 待执行 |
| `Assets/Scripts/UI/*.cs` | 需新增 9 个 View | ⬜ 待执行 |
| `Assets/Scripts/Core/Res/YooAssetResLoader.cs` | 需扩展热更新 | ⬜ 待执行 |
| `Assets/Scripts/Core/Res/ResTable.cs` | 需登记 9 个逻辑名 | ⬜ 待执行 |
| `Assets/Scripts/Core/Event/EventName.cs` | 需新增 9 个事件 | ⬜ 待执行 |

---

## 九、收尾要求

每完成一个阶段：

1. 跑 §四 全部 6 个静态校验（全 PASS）
2. Unity `read_console` 零 error
3. 实机截图（每个新界面至少 1 张）
4. 追加 `.workbuddy/memory/YYYY-MM-DD.md`：
   - 改动的文件清单
   - 试出来的硬约束（若有）
   - 验证方式与结果（实测数据，非推测）
5. 若发现新的"踩坑就返工"的不变量 → 同步到 `.workbuddy/memory/MEMORY.md`

---

*手册版本：v1.0　|　编制日期：2026-10-09　|　配套：`Docs/ArtDesign_坚守阵地_补全策划案_v1.md`*
