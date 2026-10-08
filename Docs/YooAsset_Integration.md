# 引入 YooAsset（资源管理系统）

> 目标：把开源资源管理系统 [YooAsset](https://github.com/tuyoogame/YooAsset) 接进本工程，
> 但**不改变业务代码**——业务仍然只认 `ResLoader.Instance` 的逻辑名。
>
> 版本：**3.0.6**（官方 latest / 默认分支 `yoo3`）。包名 `com.tuyoogame.yooasset`。

---

## 一、已经做完的部分（代码侧）

| 改动 | 文件 | 说明 |
|---|---|---|
| 引入依赖 | `Packages/manifest.json` | 通过 Git URL 添加，见下 |
| 适配器 | `Assets/Scripts/Core/Res/YooAssetResLoader.cs` | 新增，实现 `IResLoader` |
| 实现选择 | `Assets/Scripts/Core/Res/ResLoader.cs` | 新增 `USE_YOOASSET` 分支 |
| 分包规则 | `Assets/Editor/YooAsset/FTBundlePackRule.cs` | 新增，按 ResTable 分包（见第三节） |
| 宏开关 | `Assets/Editor/YooAsset/FTYooAssetDefine.cs` | 新增，**不套宏**，专用于打破鸡生蛋 |
| 接入向导 | `Assets/Editor/YooAsset/FTYooAssetSetupWizard.cs` | 新增，配置 / 校验 / 构建 / 回读 |
| 校验工具 | `.workbuddy/tools/check_arity.py`、`check_usings.py` | 登记新文件 / 新类型 |

`manifest.json` 里加的是：

```json
"com.tuyoogame.yooasset": "https://github.com/tuyoogame/YooAsset.git?path=Assets/YooAsset#3.0.6"
```

YooAsset 自身依赖 `com.unity.scriptablebuildpipeline`（1.21.25）与 assetbundle / unitywebrequest
三个模块，Unity 解析时会**自动一并拉下来**，不需要手写进 manifest。

### 为什么要做成编译宏而不是直接替换实现

YooAsset 是 UPM 包：**包拉不下来时，只要代码里 `using YooAsset;`，整个工程就编译不过**
（CS0246）。所以适配器整个文件包在 `#if USE_YOOASSET` 里：

- **不加宏** → 该文件编译为空，工程照常构建，YooAsset 等同没装
- **加宏** → 才真正启用 YooAsset

这与工程里既有的 `FORCE_AB` 是同一套思路（见 `ResLoader.cs` 顶部注释）。

编辑器侧的两个工具（分包规则、接入向导）**同样套宏**，保持"一个开关管全部"的一致性。
代价是宏关闭时它们也不存在，于是宏开关自己不能再依赖它们 —— 这就是
`FTYooAssetDefine.cs` 单独存在、且刻意不引用任何 YooAsset 类型的原因。

---

## 二、首次打开工程要做的事

### 步骤 0：确认 git 能连上 GitHub（★ 最容易卡在这）

Unity 用 `git` 拉这个包，走的是**全局 git 配置**。本机 `~/.gitconfig` 里有一条 GitHub 专用代理：

```ini
[http "https://github.com"]
    proxy = http://127.0.0.1:7892
```

**这条配置是"写死端口"的 —— 代理软件的端口一变，UPM 拉包立刻失败**，报错形如：

```
Project has invalid dependencies:
com.tuyoogame.yooasset: Error when executing git command.
fatal: unable to access 'https://github.com/tuyoogame/YooAsset.git/':
Failed to connect to github.com:443 over proxy 127.0.0.1 after 11 ms: Could not connect to server
```

> **2026-10-07 实际踩过一次**：`~/.gitconfig` 写着 `7890`，但代理实际听在 **`7892`**，于是 Unity 报上面这个错。

**排查三步（别猜，直接验）：**

```bash
# 1. 看配置里写的是哪个端口
git config --global --get http.https://github.com.proxy

# 2. 看该端口到底有没有在监听、本机真实代理端口是几号
netstat -ano | grep LISTENING | grep 127.0.0.1

# 3. 拿候选端口直接打 GitHub（返回 200 就是它）
curl -o /dev/null -w "%{http_code}\n" -x http://127.0.0.1:<候选端口> https://api.github.com
```

**修法（按推荐顺序）：**

1. **端口变了 → 改配置**（本次采用）：
   ```bash
   git config --global http.https://github.com.proxy  http://127.0.0.1:<正确端口>
   git config --global https.https://github.com.proxy http://127.0.0.1:<正确端口>
   ```
2. **代理没在跑 → 把代理客户端起来**，并确认端口与配置一致。
3. **想彻底摆脱端口依赖 → 删掉代理配置走直连**（国内通常直连不通，谨慎）：
   ```bash
   git config --global --unset http.https://github.com.proxy
   git config --global --unset https.https://github.com.proxy
   ```
4. **还不行 → 改用 OpenUPM 官方源**（见本文末尾「备选安装方式」），或直接内嵌包到 `Packages/` 彻底免网络。

验证修好了（GitHub + Unity 包注册表**都要通**，因为 YooAsset 依赖 `com.unity.scriptablebuildpipeline`）：

```bash
git ls-remote --tags https://github.com/tuyoogame/YooAsset.git | grep 3.0.6
curl -o /dev/null -w "%{http_code}\n" https://packages.unity.com/com.unity.scriptablebuildpipeline
```

### 步骤 1：让 Unity 解析包

打开工程，等待 UPM 解析完成。`Packages/packages-lock.json` 里应出现
`com.tuyoogame.yooasset`（以及 `com.unity.scriptablebuildpipeline`）。

命令行自检（不需要开 Unity）：

```bash
grep -n "yooasset\|scriptablebuildpipeline" Packages/packages-lock.json
```

### 步骤 2：打开开关

菜单 **`Tools ▸ 塔防 ▸ YooAsset 接入 ▸ 1. 启用 USE_YOOASSET 宏`**

它会把 `USE_YOOASSET` 写进 **Standalone / Android / iOS / WebGL 四个平台组**
（编译宏是**按平台**存的，只加当前平台的话换平台出包会静默失效）。

> 这一步必须用菜单、不能在接入向导里点 —— 向导自己也套了 `USE_YOOASSET` 宏，
> 宏关闭时它根本没被编译出来。这个"鸡生蛋"问题由 `FTYooAssetDefine.cs` 单独解决：
> 那个文件**不引用任何 YooAsset 类型**，所以在宏关闭时也能编译、能执行。

等 Unity 重新编译完成，菜单 **`Tools ▸ 塔防 ▸ YooAsset 接入 ▸ 接入向导`** 就会出现。

（想同时验证"用 YooAsset 且走真资源包"，再在 Player Settings 里加一个 `FORCE_AB`。）

### 步骤 3：跑接入向导（四步走）

菜单 `Tools ▸ 塔防 ▸ YooAsset 接入 ▸ 接入向导`，从上往下依次点：

| 步骤 | 作用 | 说明 |
|---|---|---|
| ① 生成 / 修复收集器配置 | 写入 `Assets/BundleCollectorSetting.asset` | 幂等，重复点不会重复加收集器 |
| ② 执行静态校验 | 不构建也能跑 | 核对**包名一致性 / 文件存在性 / 收集覆盖度 / 未登记资源** |
| ③ 构建模拟清单 | 产编辑器 Play 用的清单 | 若要走真机，再点「构建真实资源包」 |
| ④ 执行回读校验 | **端到端真相** | 用运行时同一个加载器逐个解析 ResTable 全部逻辑名 |

**② 和 ④ 缺一不可**：② 能离线抓出"目录没收集到""包名分叉"这类配置错误；
④ 才真正走一遍 `ResTable → 打包规则 → YooAsset 定位地址 → 实际资源`。
只看 ③ 的"构建成功"很容易误判 —— 构建成功不等于加载得到。

向导里配置的收集目录就是步骤 2 列出的那六个；**别改成收集整个 `Assets`**，
那会把 Scenes / Scripts / TextMesh Pro / Reporter 一并打进资源包。

#### 关于 ③ 里的两个构建按钮

| 按钮 | 用途 | 什么时候点 |
|---|---|---|
| **构建模拟清单** | 产编辑器 Play 用的清单，**不产出 `.bundle`** | 编辑器里 Play 其实会**自动**构建一次（见 `CreateInitOptions()`），这个按钮主要用于手动排查 |
| **构建真实资源包** | 走 `ScriptableBuildPipeline` 真出 `.bundle` | 要上真机、或要在编辑器里用 `FORCE_AB` 验证真 AB 链路时 |

**「资源包版本」是目录名**：输出落在
`{工程根}/Bundles/{平台}/{包裹名}/{版本}/`，并同步拷一份首包到 `StreamingAssets/yoo/`。

⚠️ **同一个版本号构建第二次会报错，这是 YooAsset 的行为，不是配错了**：

```
System.InvalidOperationException: [ErrorCode115]
Package output directory exists: '…/Bundles/Android/FreeTower/1.0.0'
  at YooAsset.Editor.TaskPrepare.PrepareOutputDirectory(...)
```

`TaskPrepare.PrepareOutputDirectory` 只要发现包裹输出目录已存在就直接抛。
（YooAsset **官方构建窗口**里的「清空构建缓存」开关默认也是关的，在那儿点第二次同样报这个错。）

向导的「构建真实资源包」已经处理掉了，两种口径：

- **默认（不勾「彻底重建」）**：构建前**只精确删掉本次的版本目录**
  `{BuildOutputRoot}/{平台}/{包裹}/{版本}`。好处是 Unity 的 SBP 构建缓存保持温热、重建快，
  而且**不会碰到 `Simulate`** —— 那是编辑器模拟模式当前正在用的清单，
  第 ④ 步回读校验就在同一次编辑器会话里跑，删了它校验会读到不存在的清单。
- **勾选「彻底重建」**：等价于 YooAsset 官方 Sample 的写法
  （`ClearBuildCacheFiles = true`）—— 清空 SBP 构建缓存 **并删掉整个包裹根目录**，
  会连 `Simulate` 一起删（下次进 Play 自动重建）。怀疑构建缓存不一致时再用。

要"另存一份"而不想清目录，直接**改版本号**即可（例如 `1.0.1`）。

### 步骤 4：验证

按工程既有习惯验证即可，不需要专门写测试：

- 进关卡 → 塔能建、怪能出、HUD 正常 → 正常通关 → 结算弹窗正常
- 调试键 **F2 强制获胜** 会走完整结算（含记星），可快速过一遍
- 启动日志里应出现：
  ```
  [Res] YooAsset 模式初始化完成。包裹=FreeTower，版本=Simulate，常驻包 3 个（不参与卸载）。
  ```
  ⚠️ **版本号必须是真实值**。若打印成 `版本=(未知)`，说明**清单没被激活**（见
  [四 ▸ 初始化必须走三步](#-初始化必须走三步30x-的正确用法漏一步就整片加载失败)），
  此时后面所有资源都会加载失败。
- 若某资源加载失败，日志会打印**逻辑名 + 定位地址 + 排查清单**，直接照着查

---

## 三、分包口径：按 ResTable 分包（★ 这是本次最关键的取舍）

### 为什么不能直接用 YooAsset 的目录规则

本工程的分包是**跨目录按玩法语义**分的，任何"按目录"的规则都复现不出来：

| 资源包 | 包含的目录（分居两棵树） |
|---|---|
| `enemy_rats` | `Assets/Prefabs/Enemy/Enemy_Rat.prefab` + `Assets/_UIAssets/Monsters/Rats/Rat/Rat.png` |
| `tower_normal` | `Assets/Prefabs/Tower/Normal/*` + `Assets/_UIAssets/Tower/Normal/*` |

而且怪物**必须按家族分包**：119 个怪物打成一包的话，进任意一关都要整体加载。
（详见 `ResBundle.cs` 与 `MonsterCatalog` 的注释。）

所以本次实现了一个自定义打包规则 **`FTBundlePackRule`**（`Assets/Editor/YooAsset/`），
它直接读 `ResTable` 的 `Bundle` 字段决定去向 —— 与既有 `ABNameSetter` 用的是**同一份数据**，
不会出现"两套分包规则分叉"。

未在 ResTable 登记、但被目录收集到的资源，按三级降级，且**全部记入向导报告**：
① 跟随同目录已登记资源 → ② 跟随最近的、有已登记资源的祖先目录 → ③ `misc_<顶层目录>` 兜底。
（①/② 命中是常态：怪物源预制体、字体图集、`SiYuanSongTi.ttf` 都会自然落进正确的包。）

### 寻址：刻意**关闭**"可寻址"

`FTBundlePackRule` 只负责**分包**；**寻址**走的是"关闭可寻址"这条路：

| 设置 | 值 | 理由 |
|---|---|---|
| `EnableAddressable` | **false** | 见下 |
| `SupportExtensionless` | true | 定位时带不带扩展名都能查到 |
| 打包规则 | `FTBundlePackRule` | 按 ResTable 分包 |
| 过滤规则 | `CollectAll` | 整目录收集 |
| 忽略规则 | `NormalIgnoreRule` | 自动排除 `.cs` / `/Editor/` / `DefaultAsset` 等 |

**为什么必须关掉可寻址**：打开之后，YooAsset 会强制要求"每个资源的寻址地址全局唯一"。
而本工程六个收集目录里存在 **123 组同名文件**（`Bat` / `Bear` / `Controller` / `Rat` …），
用"文件名"寻址会在收集阶段直接抛：

```
Address already exists: 'Bat' in collector: 'Assets/Prefabs'
```

关掉之后，YooAsset 的定位键就是**资源路径**本身（并因 `SupportExtensionless` 自动附加
"去扩展名"变体）。而 `ResTable` 里的 `EditorPath` 本来就是资源路径，于是：

- **不需要任何地址映射**，`ResTable` 仍是唯一寻址源；
- 路径天然唯一，不存在重名冲突；
- 适配器 `YooAssetResLoader.ResolveLocation()` 的探测候选
  （`EditorPath` 去扩展名 / `EditorPath` 原样）**正好命中**，一行都不用改。

> ⚠️ 唯一要守住的前提：`ResTable` 里登记的每个逻辑名，其对应资源**必须被收集器覆盖**。
> 漏了就会看到 `[Res] 逻辑名「xxx」在 YooAsset 清单里找不到对应定位地址`。
> 向导的「静态校验 → 收集覆盖」就是专门自动查这一条的，不必靠人眼。
> （这跟原来"漏登记 ResTable 就找不到资源"是同一类问题，只是提前到了打包期。）

---

## 四、与既有实现的关系

三套实现并存，由编译宏决定用哪个：

| 条件 | 实现 | 用途 |
|---|---|---|
| 定义 `USE_YOOASSET` | `YooAssetResLoader` | 本次接入的目标 |
| 编辑器 且 未定义 `FORCE_AB` | `EditorResLoader` | 原有默认（AssetDatabase 直读） |
| 编辑器 且 定义 `FORCE_AB`；或打包后 | `BundleResLoader` | 原有 AssetBundle 链路 |

**回退方式**：把 `USE_YOOASSET` 从 Define Symbols 里删掉即可，代码一行不用动。

`YooAssetResLoader` 内部**也复用 `FORCE_AB`** 来区分"编辑器模拟模式 / 离线模式"，
语义与 `EditorResLoader` / `BundleResLoader` 的选择口径完全一致。

### 语义对齐上的三处刻意差异（都写进了代码注释）

1. **`ReleaseBundle` 只在引用计数真正归零时才释放句柄。**
   AB 版是"无条件清掉资源缓存"——因为物理包还在，资源随时能取回来；
   而 YooAsset 里**释放句柄 = 资源引用计数归零**，紧接着的 `UnloadUnusedAssets` 会把它直接回收，
   场景还在用的话会当场变白。所以宁可更保守。

2. **异常一律在适配器内兜住。**
   YooAsset 的加载入口在异常路径上是**抛异常**而不是返回失败句柄。
   业务侧（`Launcher` 的启动回调、`GameFlowManager` 的建关流程）都没有 try/catch，
   一旦抛出去就是"启动卡死且看不到原因"，所以统一转成"返回 null + 明确日志"。

3. **编辑器模拟模式必须"当场构建模拟清单"，不能传空目录。**
   `EditorFileSystem.OnCreate` 在 `packageRoot` 为空时**直接抛**
   `package root is null or empty`；而模拟清单的内容又必须与当前资源一致。
   所以 `CreateInitOptions()` 走官方 Sample 的写法：先
   `EditorSimulateBuildInvoker.Build(packageName, (int)EBundleType.VirtualAssetBundle)`
   拿到输出目录，再交给文件系统。
   （`EditorSimulateBuildInvoker` 位于**运行时**程序集、内部反射转发到 `YooAsset.Editor`，
   因此运行时脚本可以安全引用它，不需要引用编辑器程序集。）

### ★ 初始化必须走三步（3.0.x 的正确用法，漏一步就整片加载失败）

3.0.x 把"初始化"和"加载清单"拆开了：**`InitializePackageAsync` 只初始化文件系统，
不加载清单**。完整流程是：

| 步骤 | 调用 | 作用 |
|---|---|---|
| ① | `package.InitializePackageAsync(options)` | 建文件系统（模拟清单 / 内置包 / 沙盒缓存） |
| ② | `package.RequestPackageVersionAsync()` | 拿包裹版本号 |
| ③ | `package.LoadPackageManifestAsync(new LoadPackageManifestOptions(version, 60))` | **这一步内部才 `SetActiveManifest`** |

漏掉 ②③ 的症状**极具欺骗性**（本工程实际踩过）：

- 初始化日志**一切正常**，`[Res] YooAsset 模式初始化完成` 照打；
- 但之后**每一次**加载都失败，报 `Active package manifest not found.`；
- 堆栈全部指向业务侧的加载调用，看上去像"资源没被收进收集器"，
  根因其实在初始化阶段；
- `package.GetPackageVersion()` 会抛异常（适配器捕获后打成 `版本=(未知)`）——
  **看到 `版本=(未知)` 就等于 ②③ 没走。**

另外两个配套注意点：

- `InitializePackageAsync` 有**重复初始化检测**，包裹已初始化过再调会抛
  `Resource package 'X' is already initialized.`。编辑器向导的探针可以在同一次
  编辑器会话里被反复点，所以适配器先看 `package.InitializeStatus`，已成功的直接复用。
  （进 Play 时 YooAsset 自己会通过 `RuntimeInitializeOnLoadMethod(SubsystemRegistration)`
  重置静态状态，"先跑探针、再进 Play"是安全的。）
- 三个阶段共用**同一个等待函数**（运行态让出帧、非运行态 `WaitForCompletion` 推到底），
  并带 30 秒超时。**不要**给同步/异步各写一份初始化流程 —— 本工程第一次实现时就是
  异步路径补了 ②③、同步路径没补，导致编辑器探针"看起来全绿"而 Play 必挂。

### 真实资源包构建参数上的两处选择

- **`EnableSharePackRule = true`**：没被收集目录覆盖到的依赖（例如
  `Assets/TextMesh Pro/` 下的材质）会单独进 `share_<目录>` 包，
  而不是被静默丢弃、也不会被复制进每一个引用它的包。
- **`BundledCopyOption = ClearAndCopyAll`**：清空的是 `StreamingAssets/**yoo**` 子目录
  （`YooAssetSettings.YooFolderName` 默认值 `yoo`），**不会碰到旧的
  `StreamingAssets/AssetBundles` 与 `build_info`** —— 旧 AB 链路的产物是安全的。

### 一处已知的现状（非本次引入）

`ResLoader.ReleaseBundle` **在业务代码里没有任何调用方**（`TeardownLevel` 也不调）。
也就是说 `Preload` 取得的引用计数只增不减，资源会一直留在内存里。

这在原来那套 AB 实现里就已是如此（包只加载不卸载），属于**现状对齐**，不是本次引入的回归。
若之后要做"切关回收"，正确的接入点是 `GameFlowManager.TeardownLevel()` 的第三段
（场景视觉残留之后、界面之前），届时三套实现都要一起考虑。

---

## 五、预期内的"噪声"，不用管

以下几项会在构建日志 / 向导报告里出现，都是**已知且无害**的，不要当成故障：

| 现象 | 原因 | 处理 |
|---|---|---|
| `Default asset cannot be packed: 'Assets/Audio/README.md'` | `.md` 被 Unity 认成 `DefaultAsset`，被 `NormalIgnoreRule` 挡下并打一句 warning | 无需处理；若嫌吵可把 README 移出 `Assets/` |
| 向导报告里 `Assets/_UIAssets/Monsters/<家族>/<怪名>/<怪名>.prefab` 属"未登记资源" | 那是**怪物源预制体**，ResTable 只登记了两样产出物：战斗预制体与图集 | 走"跟随同目录"降级，仍会进 `enemy_<家族>` 包，符合预期 |
| 向导报告里 `Assets/Font/SiYuanSongTi.ttf` 属"未登记资源" | ResTable 登记的是 TMP 字体资产与描边材质，不含源 ttf | 同上，会落进 `font` 包 |
| `Explicit folder is not exist` 之类收集路径告警 | 某个收集目录被删了 | 向导「生成 / 修复收集器配置」会跳过不存在的目录并提示 |

**真正的异常信号**只有一个：向导报告里出现**兜底包名 `misc_*`**。
那意味着某个资源既不在 ResTable 里、其所在目录树也没有任何已登记资源可跟随 ——
要么该登记进 ResTable，要么该把它排除出收集范围。

---

## 六、后续可选的扩展点

- **热更新 / 下载**：`YooAssetResLoader.CurrentPackage` 直接暴露 `ResourcePackage`，
  要做版本更新、按标签下载、边玩边下时从它入手，不用改业务层。
- **`Preload` 的预热类型**：目前用 `typeof(UnityEngine.Object)` 预热，目的是把**物理包**拉进内存
  （这是大头成本）。若之后发现某类资源（例如按 Sprite 加载的贴图）在预热后又被重载一次，
  可以在 `ResTable` 里给 `ResAddress` 加一个类型提示字段，届时预热就能用精确类型。
- **诊断**：`YooAssetResLoader.DumpDebugInfo()` / `HasLeak()` 与两个旧实现同名同义，可直接用。
- **减小收集面**：目前按目录整收，会把怪物源预制体、源 ttf 一并打进包（体积很小）。
  要做精细控制，可以给收集器换一个自定义 `IAssetFilterRule`，只收 ResTable 里出现过的路径。

---

## 备选安装方式

若 git 通道长期不可用，可改用 OpenUPM 官方源：

```json
{
  "scopedRegistries": [
    {
      "name": "package.openupm.com",
      "url": "https://package.openupm.com",
      "scopes": ["com.tuyoogame.yooasset"]
    }
  ],
  "dependencies": {
    "com.tuyoogame.yooasset": "3.0.6"
  }
}
```

> 注意：国内镜像 `https://package.openupm.cn` 经实测**不可达**，只能用官方 `package.openupm.com`。

另一种是源码内嵌：把仓库 `Assets/YooAsset/` 整个拷进本工程 `Packages/`（或 `Assets/`），
完全离线、可二次修改，代价是升级要手动替换。
