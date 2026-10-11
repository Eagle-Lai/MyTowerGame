# 引入 HybridCLR（C# 代码热更新）

> 目标：把 [HybridCLR](https://github.com/focus-creative-games/hybridclr) 接进本工程，
> 让**绝大多数业务代码**变成可热更的，且**尽量不改动既有业务逻辑**。
>
> 版本：**8.14.1**（Unity 包 `com.code-philosophy.hybridclr`）。
> ⚠️ 包版本必须与 `HybridCLRData/LocalIl2CppData-WindowsEditor` 里已安装的 il2cpp **版本戳**一致
> （见 `libil2cpp/hybridclr/generated/libil2cpp-version.txt`），否则 `Generate/All` 会报
> `You must run HybridCLR/Installer after upgrading package`。

---

## 一、核心约束（先理解这条，后面全都围绕它）

HybridCLR 的**铁律**：

> **AOT 主程序集（打进包体的那部分）不能引用热更程序集里的任何类型。**

本工程原本**零 asmdef**，所有代码都在默认的 `Assembly-CSharp` 里。而 `main.unity` 场景
与所有 UI prefab **挂载的全是 `Assets/Scripts/` 下的业务脚本**（`Launcher`、`GameFlowManager`、
各 View、塔 / 怪 / 弹 ……）。既然要求"尽可能全划入热更"，这些挂载脚本就都成了"热更类型"。

于是必须解决两件事：

1. **划分程序集**：把业务代码移出 `Assembly-CSharp`，放进热更程序集。
2. **新增 AOT 启动场景**：`main` 场景的脚本是热更类型，AOT 侧不能直接加载它 ——
   必须由一个**纯 AOT 的 Boot 场景**先 `Assembly.Load` 热更 dll，再进 `main`。

---

## 二、程序集划分

### 最终结构

| 程序集 | 目录 | 角色 | 说明 |
|---|---|---|---|
| `FTProject.AOT` | `Assets/AOTAssembly/` | **AOT** | 新建。唯一承载场景挂载的引导层 |
| `FTProject.ThirdParty.AOT` (+`.Editor`) | `Assets/Demigiant/` | AOT | DOTween 源码模块（DLL 本体另计） |
| `FTProject.ThirdParty.iTween` | `Assets/Plugins/iTween/` | AOT | iTween 源码（工程内零使用） |
| `FTProject.Editor` | `Assets/Editor/` | 编辑器 | 22 个编辑器工具，**不进包体** |
| `FTProject.LubanLib` | `Assets/LubanLib/` | **热更** | Luban 序列化基础库（`Bright.Serialization`） |
| `FTProject.Gen` | `Assets/Gen/` | **热更** | Luban 生成的配置表类（`cfg` 命名空间） |
| `FTProject.ThirdParty.SuperScrollView` (+`.Editor`) | `Assets/SuperScrollView/` | **热更** | 列表控件 |
| `FTProject.ThirdParty.Reporter` (+`.Editor`) | `Assets/Reporter/` | **热更** | 调试面板 |
| `FTProject.Runtime` | `Assets/Scripts/` | **热更（主体）** | 101 个业务脚本。**引用 `FTProject.AOT`**（为了 `: IHotUpdateEntry`） |
| `FTProject.HybridCLRGenerate` | `Assets/HybridCLRGenerate/` | **AOT** | ★ 只为 `AOTGenericReferences.cs` 建的（见下） |
| **`Assembly-CSharp`** | `Assets/` 根目录（无 asmdef） | **热更** | ★ Unity 默认集。谁都不属于的脚本落这里 |

### ★ 关于 `Assembly-CSharp`（Unity 默认程序集）

它**不是**我们主动划进去的，而是 Unity 的兜底规则：

> 任何脚本，只要**不在**任何 asmdef 的覆盖目录下，就自动编进 `Assembly-CSharp.dll`。

当前它的全部内容是 `Assets/TestNull.cs`（一个空的测试 MonoBehaviour，落在 `Assets/` 根目录）。

**处理方式：纳入热更**（`HybridCLRSettings.hotUpdateAssemblies` + `HotUpdateAssembler.HotUpdateAssemblies` 都已加入）。

> ✅ **好处**：以后往 `Assets/` 根目录随手丢的脚本会自动进热更，不用改配置。
> ⚠️ **风险**：热更集的数量会随"根目录有没有散落脚本"波动。若某天把 `TestNull.cs`
> 删了或移进 asmdef，`Assembly-CSharp.dll` 就不再生成 → `HotUpdateAssembler` 会**报"缺少热更 dll"**。
> 所以：**增删 `Assets/` 根目录的脚本后，务必重跑 `Generate ▸ All` 并核对拷贝日志**（见第五节）。

### ★ 关于 `FTProject.HybridCLRGenerate`（为什么单独建一个 AOT 程序集）

`Assets/HybridCLRGenerate/AOTGenericReferences.cs` 是 HybridCLR **自动生成**的产物，
它提供 `PatchedAOTAssemblyList`（AOT 补充元数据的权威名单），**必须属于 AOT 层**。

问题：这个目录**原本没有 asmdef** → 该文件掉进了 `Assembly-CSharp`。
一旦 `Assembly-CSharp` 被加入热更，它就会**变成热更类型** —— 而这直接违反铁律
（AOT 补充元数据清单必须是 AOT 的）。

所以给它建了专属 asmdef `FTProject.HybridCLRGenerate.asmdef`，把它钉在 AOT 层。
**已验证**：HybridCLR 的生成器只用 `File.WriteAllText` 写这一个文件，
**不会删除目录内其它文件**（源码见 `GenericReferenceWriter.Write`），所以 asmdef 放同目录安全。

> 备选方案：把 `HybridCLRSettings.outputAOTGenericReferenceFile` 改指到
> `AOTAssembly/AOTGenericReferences.cs`（让它天然归属 `FTProject.AOT`）。
> 当前选择保留默认路径 + 专属 asmdef，是为了**少偏离 HybridCLR 官方默认结构**。

### ⚠️ 程序集引用方向（铁律的准确表述）

HybridCLR 的铁律是「**AOT 不得引用热更**」，**反向是允许的**（热更集可以引用 AOT 集）。

本工程现有两条符合方向要求的引用：

| 引用 | 方向 | 用途 |
|---|---|---|
| `FTProject.Runtime` → `FTProject.AOT` | 热更 → AOT ✅ 合法 | 为让热更侧 `: IHotUpdateEntry` |
| `FTProject.AOT` → `HybridCLR.Runtime` | AOT → AOT ✅ | 用 HybridCLR 自己的 RuntimeApi |

**判据**：只看 `FTProject.AOT` 侧是否**零热更引用**。它目前只引 `HybridCLR.Runtime`，✅。

### 热更 dll 的加载顺序（拓扑序，写错会运行时报错）

```
Assembly-CSharp  →  LubanLib  →  Gen  →  SuperScrollView / Reporter  →  Runtime
（零依赖，兜底）   （零依赖）  （依赖 LubanLib）（零业务依赖）        （依赖以上全部）
```

> `Assembly-CSharp` 排最前：它当前只含零依赖的散落脚本，被依赖的可能性最低。
> 若将来它开始引用其它热更集，需要把它往后挪。

### 为什么 DOTween / LitJson 没进热更

它们是 **预编译 `.dll`**（`DOTween.dll`、`DOTweenPro.dll`、`DemiLib.dll`、`LitJson.dll`），
不是 C# 源码。HybridCLR 的热更对象是**由源码编译出的程序集**，预编译 DLL **物理上无法**作为
热更集，只能作 AOT。这不是取舍，是硬限制。

> 附带发现：DOTween 与 iTween 在本工程**零使用**（`Assets/Scripts` 里仅有两处注释提到
> "为什么不用 DOTween"）。若将来想彻底瘦身，这些可以直接删掉。

---

## 三、启动流程（接入后的完整链路）

```
Boot 场景（纯 AOT）
  └─ Boot 对象 → FTProject.AOT.BootLoader.Awake
       ├─ ① HotUpdateAssembler.LoadHotUpdateAssemblies()
       │     • 加载 AOT 补充元数据（AOTMetaAssemblies，6 项）
       │     • 按拓扑序 Assembly.Load 全部热更 dll
       │     • ⚠️ 编辑器下热更 dll 已在 AppDomain → 自动跳过（不报"已加载"）
       ├─ ② HotUpdateEntryLocator.CreateEntry() → IHotUpdateEntry 实例
       │     • 拿到接口引用后**强类型**调用 entry.Start()（热更侧接管）
       └─ ③ SceneManager.LoadScene("main")
              └─ main 场景 → Launcher（Splash → Loading → 资源热更 → Ready）
                          → GameSceneLauncher（注入场景引用）
```

**Build Settings 顺序**：`Boot.unity`（index 0）→ `main.unity`（index 1）。

### 跨程序集契约：**接口**（而不是字符串反射）

热更侧入口**不再是"字符串类型名 + 反射方法名"**，而是：

```
AOT 侧定义接口  FTProject.AOT.IHotUpdateEntry   （Assets/AOTAssembly/IHotUpdateEntry.cs）
       ↑ 由热更侧实现
热更侧          FTProject.HotUpdateEntry : IHotUpdateEntry
       ↑ AOT 侧通过 HotUpdateEntryLocator 拿到接口引用
调用方          BootLoader → entry.Start()
```

| 契约 | AOT 侧 | 热更侧 | 保障方式 |
|---|---|---|---|
| 入口方法签名 | `IHotUpdateEntry.Start()` | `HotUpdateEntry.Start()` | **编译器**（改签名两边同时报错） |
| 入口类名 | `HotUpdateEntryLocator.EntryTypeNames` 候选表 | `FTProject.HotUpdateEntry` | ⚠️ 仍是字符串；但有**兜底扫描**，名字变了仍能找到并打 Warning |
| 热更 dll 名单 | `HotUpdateAssembler.HotUpdateAssemblies` | `HybridCLRSettings.asset` 的 `hotUpdateAssemblies` | 手工同步（无编译保障） |

**为什么比旧方案好**

| | 旧：字符串反射 | 新：接口 |
|---|---|---|
| 改名入口类/方法 | 只在**运行时**炸，错误来自反射、难定位 | **编译期**报错 |
| 漏实现接口成员 | 不存在"接口"，无从校验 | 编译失败 |
| 方法能否带强类型参数 | ❌ 只能无参（`MethodInfo.Invoke`） | ✅ 可带任意强类型参数 |
| IDE 支持 | 跳不了、重命名找不到引用 | 可跳转 / 重命名 / 查引用 |
| 失败时的错误信息 | "找不到类型「XXX」"（可能是名字写错，也可能别的原因） | "没有任何类型实现 IHotUpdateEntry"（语义确定） |

**为什么"找到实现者"这一步仍必须用反射**

AOT 侧**不能 `new` 热更类型**（形成编译期符号依赖 → IL2CPP 打包直接失败）。
所以"谁来实现、怎么实例化"只能运行时完成 —— 这就是 `HotUpdateEntryLocator` 存在的原因。
它把反射**收窄到只做一件事**（找到并实例化实现者），一旦拿到接口引用，后续全部强类型：
`entry.Start()`。

> ⚠️ **实现类必须能被无参构造**（`Activator.CreateInstance`）。
> 所以 `HotUpdateEntry` 是普通 class + 无参构造，**不是 static class**
> —— static 类无法实例化，也就无法作为接口实现被调起。
> 实例本身无状态价值，"是否已启动"用静态标记 `Started` 记录。


---

## 四、dll 从哪里读（`HotUpdateAssembler.ReadDllBytes` 的查找顺序）

| 优先级 | 位置 | 用途 |
|---|---|---|
| ① | `Application.persistentDataPath/HybridCLR/` | **真机热更产物落点**（可写，优先级最高） |
| ② | `StreamingAssets/HybridCLR/` | 随包分发的首包版本 |
| ③ | `Library/ScriptAssemblies/` | **仅编辑器**，免拷贝，开发期快速验证 |

**为什么 persistentDataPath 排最前**：Android 上 `StreamingAssets` 是**包内只读**的，
热更下来的新 dll 没法覆盖它，必须有一个"可写且优先"的位置。

---

## 五、日常操作流程

### 改了热更代码后

```
菜单：HybridCLR ▸ Generate ▸ All          # 重编译热更 dll + link.xml + 桥接 + AOT 泛型引用
菜单：Tools ▸ 塔防 ▸ HybridCLR ▸ 1. 拷贝热更 dll 到 StreamingAssets   # 6 热更 + 6 AOT，一次拷全
```

> 编辑器里调试**不需要**每次拷贝 —— 引导器会走 ③ 分支直接读编译产物。
> 拷到 StreamingAssets 是**打包前**必须做的。
> ⚠️ 改了 `Assets/` **根目录**下的脚本（即 `Assembly-CSharp` 那批）后，同样要重跑上面两步
> —— 因为 `Assembly-CSharp.dll` 也在热更名单里。

### 改了 AOT 代码后（`Assets/AOTAssembly/`、DOTween 等）

AOT 代码改动**无法热更**，必须重新出包。这是热更方案的固有边界，不是本工程的问题。

### 打包前 checklist

1. `HybridCLR ▸ Generate ▸ All` 无报错
2. `Tools ▸ 塔防 ▸ HybridCLR ▸ 1. 拷贝热更 dll` 成功（日志里 **热更 6 个 + AOT 6 个**，
   且出现「AOT 元数据名单与 AOTGenericReferences.cs 一致」）
3. `Assets/HybridCLRGenerate/link.xml` 存在（**否则热更引用的 AOT 类型会被 IL2CPP 裁剪掉**）
4. 若增删了 `Assets/` 根目录的脚本 → 确认 `Assembly-CSharp.dll` 仍在热更产物里（第 2 步日志可见）

---

## 六、HybridCLR 相关菜单

| 菜单 | 作用 |
|---|---|
| `HybridCLR ▸ Installer...` | 安装 / 更新 il2cpp（**换包版本后必须重跑**） |
| `HybridCLR ▸ Settings...` | 配置热更程序集列表、AOT 补充元数据等 |
| `HybridCLR ▸ Generate ▸ All` | 一键生成全部产物（编译 dll / link.xml / 桥接 / 裁剪 AOT dll / AOT 泛型引用） |
| `HybridCLR ▸ Generate ▸ LinkXml` | 单独生成 link.xml（不依赖平台构建，可随时跑） |
| `Tools ▸ 塔防 ▸ HybridCLR ▸ 1. 拷贝热更 dll 到 StreamingAssets` | 本工程新增：拷 6 热更 + 6 AOT，并核对名单一致性 |
| `Tools ▸ 塔防 ▸ HybridCLR ▸ 2. 查看热更 dll 状态` | 本工程新增：查看编译 / 拷贝状态 |
| `Tools ▸ 塔防 ▸ HybridCLR ▸ 3. 拷贝 AOT 补充元数据 dll 到 StreamingAssets` | 本工程新增：只拷 AOT 那 6 个（调试用） |

> ⚠️ **跑 `Generate ▸ All` 前必须确认 `isCompiling == false && isPlaying == false`**：
> 编辑器正在编译时跑，会拿**旧程序集**静默生成旧结果（不报错，但产物是过期的）。
> 另外该菜单会跑一次完整 Android 构建，耗时数分钟，MCP 调用会**超时返回**
> —— 这是预期的，改看 Console 轮询即可。

### 热更 dll 的下载通道（`HotUpdateDllDownloader`）

Boot 阶段在加载 dll 前，会先从服务器同步一遍 dll。**注意这条通道刻意不走 YooAsset**：

```
热更 dll 要在 Boot 场景加载（早）
而 YooAsset 在 main 场景的 Launcher 里才初始化（晚）
想让 YooAsset 去下 dll → 就得先初始化 YooAsset
可 YooAsset 的初始化代码本身就在热更 dll 里 → "要用 dll 才能下 dll" 死结
```

所以 **dll 走独立 HTTP，AB 资源走 YooAsset**，两条通道各管一摊。

| 项 | 值 |
|---|---|
| 服务器目录约定 | `{服务器根}/{平台}/HybridCLR/{dll 文件名}` |
| 下载落点 | `persistentDataPath/HybridCLR/`（读取优先级最高，见第四节 ①） |
| 地址来源 | `BootLoader.ServerUrlForAOT` 常量；可用 `persistentDataPath/server.txt` 覆盖 |
| 失败策略 | **静默回退**：任一文件失败只打 Warning，继续用包内/上次版本，**绝不阻断启动** |
| 404 语义 | 视为"服务器上没有 = 无需更新"，计入 `Skipped` 而非错误 |

> ⚠️ `ServerUrlForAOT` 是 AOT 侧的**刻意复制常量**（AOT 不能引用热更集里的 `ResServerConfig`）。
> **改地址要两处同步**：`BootLoader.ServerUrlForAOT` ↔ `Core/Res/ResServerConfig.cs`。

---

## 七、真机（Android）打包注意事项

`HybridCLR ▸ Generate ▸ All` 的后两步（裁剪 AOT dll、生成 AOT 泛型引用）**需要平台构建环境**：
它会跑一次 `buildScriptsOnly` 的 Android 构建来产出裁剪后的 AOT dll。

裁剪产物落在 `HybridCLRData/AssembliesPostIl2CppStrip/{平台}/`，
是运行时"AOT 泛型补充"（`AOTMetaAssemblies`）的数据源。

### ⚠️ 环境要求（踩过的坑，务必对齐）

| 组件 | 要求 | 说明 |
|---|---|---|
| JDK | **11** | Unity 2022.3 LTS 官方只支持 JDK 11 |
| Android SDK | build-tools **34.0.0** / platform **android-34** / platform-tools | |
| **cmdline-tools** | **6.0** | ★ 见下 |
| NDK | **r23b (23.1.7779620)** | Unity 2022.3 硬要求 |

**★ cmdline-tools 必须是 6.0（Unity 2022.3 LTS 官方基线）。**

构建时 Unity 的 `SDKToolsDetector` 会跑：
```
java -Xmx… -Dcom.android.sdkmanager.toolsdir="<sdk>/cmdline-tools/latest" \
     -Dfile.encoding=UTF8 -jar sdktools.jar android update sdk "cmdline-tools;…" … --sdk_root=…
```
若 `cmdline-tools/latest` 装的是 **11+**（例如 12.0），其 `sdklib/libsdkmanager_lib.jar`
编译在 **class file version 61（JDK 17）**；而 Unity 跑它的 JVM 是 **JDK 11**（只认到 55.0）→

```
java.lang.UnsupportedClassVersionError: com/android/sdklib/tool/sdkmanager/SdkManagerCli
  has been compiled by a more recent version of the Java Runtime
  (class file version 61.0), this version of the Java Runtime only recognizes
  class file versions up to 55.0
CommandInvokationFailure: Failed to update Android SDK package list.
Exception: GenerateStripedAOTDlls failed
```

**❌ 错误解法：装 JDK 17 去迁就 cmdline-tools。**
Unity 2022.3 的 Gradle 7.5 打包管线只认证 JDK 11，换 17 会把"明确报错"变成"更难查的静默失败"。
**✅ 正解：把 cmdline-tools 换成 6.0**（class major 52，JDK 8 编译，JDK 11 完全兼容）。

下载与安装（`commandlinetools-win-8092744_latest.zip`，约 114 MB）：
```bash
# 1) 下载
curl -L -o clt6.zip https://dl.google.com/android/repository/commandlinetools-win-8092744_latest.zip
# 2) 解压出的顶层目录名是 cmdline-tools/，其中的内容要落到 <sdk>/cmdline-tools/latest/
#    （即把 zip 里的 cmdline-tools/* 内容拷进 <sdk>/cmdline-tools/latest/）
# 3) 验证
<sdk>/cmdline-tools/latest/bin/sdkmanager.bat --version   # 应输出 6.0
```

**诊断技巧**：`class file version 61.0` = JDK 17，`55.0` = JDK 11。判断一个 jar 编译在哪个 JDK：
读每个 `.class` 的前 8 字节，`major = struct.unpack('>HH', data[4:8])[1]`。

> 注意：Unity 自带的 `AndroidPlayer/Tools/sdktools.jar` 本身是 class 55（JDK 11 安全）；
> 它是在**运行时**去 `<sdk>/cmdline-tools/latest` 加载 `sdklib`，所以换 cmdline-tools 版本才是对症改法。

### AOT 补充元数据（`AOTMetaAssemblies`）

`Generate/All` 完成后，`Assets/HybridCLRGenerate/AOTGenericReferences.cs` 会产出
`PatchedAOTAssemblyList`（当前 6 项）。**必须把它同步到两处**（两份名单要一致）：

1. `Assets/AOTAssembly/HotUpdateAssembler.AOTMetaAssemblies`（运行时加载用）
2. `Assets/Editor/HybridCLRDllCopier.AOTMetaAssemblies`（编辑器侧拷贝用 —— 编辑器工具
   不能引用 AOT 程序集，所以只能各写一份）

拷贝工具会**自动比对**这两份名单与 `AOTGenericReferences.cs`，不一致直接打 Warning。

> **编辑器工具不能引用 `FTProject.AOT`**，否则会绕开"编辑器工具只依赖 Runtime"的分层约定，
> 所以两处名单只能手工同步 —— 这是刻意的取舍，不是疏漏。

---

## 八、涉及的文件清单

| 文件 | 说明 |
|---|---|
| `Packages/manifest.json` | 新增 `com.code-philosophy.hybridclr` git 依赖 |
| `ProjectSettings/HybridCLRSettings.asset` | 热更程序集配置（**首次由本工程脚本生成**，不在 Unity 默认产物里） |
| `Assets/AOTAssembly/FTProject.AOT.asmdef` | AOT 程序集定义（引用 `HybridCLR.Runtime`） |
| `Assets/AOTAssembly/IHotUpdateEntry.cs` | **热更入口接口**（定义在 AOT，由热更侧实现） |
| `Assets/AOTAssembly/BootLoader.cs` | Boot 场景挂载脚本（AOT） |
| `Assets/AOTAssembly/HotUpdateAssembler.cs` | 热更 dll 加载器（AOT） |
| `Assets/AOTAssembly/HotUpdateEntryLocator.cs` | 查找 `IHotUpdateEntry` 实现并实例化（AOT，唯一保留的反射点） |
| `Assets/AOTAssembly/HotUpdateDllDownloader.cs` | 热更 dll 的**独立 HTTP 下载器**（AOT，不走 YooAsset，见第六节末） |
| `Assets/Scripts/HotUpdateEntry.cs` | 热更侧入口（**`IHotUpdateEntry` 的实现**） |
| `Assets/Scripts/FTProject.Runtime.asmdef` | 业务主体程序集（热更，**引用 `FTProject.AOT`**） |
| `Assets/HybridCLRGenerate/FTProject.HybridCLRGenerate.asmdef` | ★ 把 `AOTGenericReferences.cs` 钉在 AOT 层（见第二节） |
| `Assets/TestNull.cs` | 落在 `Assets/` 根目录的散落脚本 → 使 `Assembly-CSharp` 存在并纳入热更 |
| `Assets/Gen/FTProject.Gen.asmdef` 等 | 各热更程序集定义 |
| `Assets/Editor/FTProject.Editor.asmdef` | 编辑器工具程序集 |
| `Assets/Editor/HybridCLRDllCopier.cs` | 热更 dll + AOT 补充元数据 搬运工具（含名单一致性核对） |
| `Assets/Scenes/Boot.unity` | 新增启动场景 |
| `Assets/HybridCLRGenerate/link.xml` | 自动生成，防 AOT 类型被裁剪 |
| `Assets/HybridCLRGenerate/AOTGenericReferences.cs` | 自动生成，`PatchedAOTAssemblyList` 是 AOT 元数据名单的来源 |
| `Assets/StreamingAssets/HybridCLR/` | 12 个 dll（6 热更 + 6 AOT 元数据），随包分发。**入 git**（是首包的一部分） |
| `HybridCLRData/` | 已加进 `.gitignore`（本机安装产物，约 800MB，可重装） |

> ⚠️ `.gitignore` 里忽略的是 `/HybridCLRData/`（第 66 行，本机安装产物）；
> `Assets/StreamingAssets/HybridCLR/` **不在忽略列表** —— 它是首包内容，必须入库。

---

## 九、已验证的运行链路（Boot → main）

编辑器内实测过一次完整启动（Play 模式），链路各环节均通过：

| 环节 | 预期 | 实测结果 |
|---|---|---|
| Boot 场景加载 | `Boot.unity` 为 Build index 0 | ✅ 场景 `Boot`，`Boot` 对象带 `BootLoader`（guid `9c6e8e237b58094459684bac834637a5`） |
| 首启预取 | 把 StreamingAssets 的 dll 释放到 `persistentDataPath` | ✅ 日志 `[Boot] 正在准备热更程序集…`，目录已创建 |
| dll 下载 | HTTP 同步 12 个 dll | ✅ 地址不可达时 `[Boot] 部分热更 dll 同步失败（不影响启动，将继续使用本地版本）`，**未阻断启动** |
| AOT 补充元数据 | 6 个 `AOTMetaAssemblies` 全部 `LoadMetadataForAOTAssembly` 成功 | ✅ 无 `LoadImageErrorCode` 报错 |
| 热更 dll 加载 | 编辑器下已在 AppDomain → 跳过 | ✅ 日志 `…跳过加载：Assembly-CSharp / LubanLib / Gen / SuperScrollView / Reporter / Runtime`，最终 **`12/12`** |
| 接口入口定位 | `HotUpdateEntryLocator.CreateEntry()` 拿到 `IHotUpdateEntry` | ✅ 反查确认：`FTProject.HotUpdateEntry` 实现接口、非抽象、有无参构造 |
| 接口调用 | `entry.Start()` 被调到 | ✅ 日志 `[Boot] 热更入口已执行：FTProject.HotUpdateEntry.Start()` |
| 进 main 场景 | `SceneManager.LoadScene("main")` | ✅ 最终活动场景 = `main`（6 个根对象） |
| 后续启动链 | Launcher 完成 Splash→Loading→YooAsset→配置 | ✅ `[Res] YooAsset 模式初始化完成`、`9 个资源全部就绪`、`[Config] 配置加载完成`（8 张表）、`交叉引用自检通过` |

实际抓到的完整 Boot 链日志（编辑器）：
```
[Boot] 正在加载热更程序集…
[Boot] 正在准备热更程序集…          ← 首启预取（StreamingAssets → persistentDataPath）
[Boot] 正在检查热更 dll…
[Boot] 同步热更 dll 0/12
[Boot] 部分热更 dll 同步失败（不影响启动，将继续使用本地版本）：未配置服务器地址
[HybridCLR] 程序集已在 AppDomain，跳过加载：Assembly-CSharp（编辑器下属正常）
[HybridCLR] 程序集已在 AppDomain，跳过加载：FTProject.LubanLib（编辑器下属正常）
…（Gen / SuperScrollView / Reporter / Runtime 同理）
[Boot] 加载热更程序集 12/12
[Boot] 正在启动游戏…
[HotUpdate] 热更程序集加载完成，HotUpdateEntry.Start() 已执行。
            （经 IHotUpdateEntry 接口调用，非反射）接下来的启动流程由 main 场景的 Launcher 接管。
[Boot] 热更入口已执行：FTProject.HotUpdateEntry.Start()
[Boot] 准备就绪
```

> 上面这次抓取把 `ServerUrlForAOT` **临时置空**以跳过 12×30s 的网络超时（验证完已还原）。
> 置空时 `DownloadAll` 立即 `yield break` 并给出「未配置服务器地址」——**启动不受任何影响**，
> 这恰好验证了下载器的"失败不阻断"设计。

> **注意**：编辑器下 Boot 与 main 之间切换极快（编辑器不做真机的 dll 加载），
> 肉眼/截图抓不到 Boot 中间态，属正常。真机上会明显停留数秒加载 dll。
> ⚠️ **`Boot` 日志其实一直有**：`BootLoader.SetStatus` 里的 `Debug.Log("[Boot] ")` **无条件执行**，
> 只有赋 `_statusText.text` 那行受 null 判断保护。判据仍推荐看**活动场景是否变成 `main`**。


---

## 十、已知边界与后续

- **AOT 代码无法热更**（`FTProject.AOT`、DOTween 等）。改 AOT = 重新出包。
- **热更 dll 的 CDN 通道已就绪**：`HotUpdateDllDownloader` 会在 Boot 阶段从
  `{服务器根}/{平台}/HybridCLR/` 同步 dll 到 `persistentDataPath/HybridCLR/`（读取优先级最高）。
  首包仍随 `StreamingAssets` 分发；服务器上没有的文件按"无需更新"跳过。
- 每次重跑 `Generate/All` 后，若 `AOTGenericReferences.cs` 的清单有变化，
  **必须同步两处 `AOTMetaAssemblies`**（见第七节末）。
- **增删 `Assets/` 根目录的脚本后**，`Assembly-CSharp.dll` 的有无会变化
  → 必须重跑 `Generate ▸ All` + 拷贝，否则 `HotUpdateAssembler` 会报"缺少热更 dll"。
- **未验证：真机（Android APK）启动链路。** 编辑器下已验证。
  真机特有路径（`Assembly.Load(bytes)` 真正执行、`UnityWebRequest` 读 StreamingAssets、
  HTTP 下载 dll）尚未实测 —— 需要真机 + 一台可达的资源服务器。
  > ✅ APK 内 `StreamingAssets` 读不到 dll 的问题**已有解法**：
  > `HotUpdateAssembler.PrefetchStreamingAssetsToPersistent` 用 `UnityWebRequest` 异步读，
  > 首启一次性释放到 `persistentDataPath`（Boot 第一步就会跑）。
