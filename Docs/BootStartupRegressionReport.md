# Boot 入口与离线首启回归修复

日期：2026-10-19。工程：`E:\MyTowerGame`，Unity `2022.3.62f3c1`。

编辑器从 Boot 无法进入 Main 的回归已修复。此次还通过干净安装发现并修复了 APK 首次离线启动请求远端清单的问题，以及错误页重试按钮被父节点隐藏的问题。此前直接运行 Main 的验证不足以证明 Boot 正常；原交付报告中的对应验收结论应以本次补充记录为准。

## 故障与实际修复

| 故障 | 现场证据 | 修复 |
|---|---|---|
| 编辑器 Boot 使用真实 AB 版本查找模拟清单 | `Could not find simulation package hash file ... Simulate/FreeTower_3.1.2.hash` | 普通编辑器模式不准备 APK 基线、不下载 DLL、不探测服务器；使用已编译程序集和当前工程模拟资源。版本请求在模拟模式下始终读取模拟清单自身版本 |
| 干净 APK 首次离线无法加载清单 | `Regression/50-first-offline-initial-failure/logcat.txt`，请求远端 `FreeTower_3.1.3.hash` 失败 | Host 模式沙盒初始化后，将匹配 APK 基线的内置清单与 hash 写入 YooAsset 清单缓存；二进制清单写入前核对发布描述符 MD5。更新版本不会被旧 APK 清单覆盖 |
| 错误页不能点击重试 | 中间包错误截图没有按钮；编辑器探针确认 RetryBtn 的父节点 BtnGroup 为 inactive | HotUpdateView 同时管理父节点和各按钮状态。最终 APK 错误截图显示 Retry，真实 adb 点击后同一进程恢复成功 |
| 可达服务器提供无效发布或 DLL 时阻塞完整本地版本 | 无效 JSON、AOT 不兼容、DLL 404、MD5 错误注入 | 在加载热更程序集前保留并恢复本地候选；重新核验候选 DLL，并由后续资源闸门验证同一版本全部资源。没有混用单个旧 DLL |

修改文件与职责：

- `Assets/AOTAssembly/BootLoader.cs`：编辑器模拟入口隔离；远端描述符和 DLL 失败时，在程序集加载前选择已核验的本地候选。
- `Assets/AOTAssembly/BootReleaseStore.cs`：清理启动选择状态；提供编辑器模拟重置、本地候选恢复和内置清单匹配判断。
- `Assets/AOTAssembly/HotUpdateView.cs`：修正按钮父节点的可见性，保留现有暂停、继续与重试回调。
- `Assets/Scripts/Core/Res/YooAssetResLoader.cs`：模拟模式版本隔离；Host 模式内置清单准备与 MD5 校验；沿用 YooAsset 文件系统及完整资源检查。
- `.workbuddy/tools/boot_regression_20261019.py`：限定独立包及隔离 HTTP 子目录的回归矩阵、恢复操作和交付校验。

## 启动行为与边界

普通编辑器（`UNITY_EDITOR && !FORCE_AB`）：Boot 首屏 → 当前工程程序集入口 → 构建模拟清单 → 资源检查 → Main → Loading → Splash → 主菜单。与服务器、APK 旧基线和已导出 DLL 无关。直接运行 Main 仍可用。`FORCE_AB` 保留真实 AB 测试路径，本次未重新验证该开发宏。

APK：保留原先 Boot → DLL → YooAsset/AB → Main → Loading → Splash → 主菜单顺序。首次完全无缓存且断网时，完整内置基线可正常进入游戏；已更新版本在本地完整时可以离线使用。服务器不可达、发布文件 404、探测超时、无效 JSON、不兼容描述符、DLL 缺失和校验失败均已在最终 APK 上实测。

可用性有明确边界：本次自动回退发生在加载热更程序集之前。若新 DLL 已加载后才发现新清单或 AB 不可用，仍停留在可点击重试的更新页，恢复服务器后补齐固定版本，不能在同一进程中卸载新 DLL 再混入旧版本。若本地资源被破坏且网络不能补齐，也不能承诺无条件进入游戏。这符合原 prompt 对完整性和可恢复错误页的要求；本报告不将这种情形标为“故障期间仍能进游戏”。

## 最终交付版本

| 项目 | 值 |
|---|---|
| 最终实测 APK | `E:\MyTowerGame\Builds\BootRefactor\Regression\Final\boot-fixed-3.1.7.apk` |
| 包名 | `com.ftproject.freedomtower.bootregression20261019c`，独立测试包 |
| 构建 | Development、IL2CPP，APK 同时含 `arm64-v8a` 和 `armeabi-v7a` |
| APK 大小 | 108,492,181 字节 |
| APK SHA256 | `70f4467b32b6f2a0c6c0d3d760e1b2943fa447c9744a5a884caefe0b034855a6` |
| 完整测试发布 ZIP | `E:\MyTowerGame\Builds\BootRefactor\Regression\Final\release-3.1.9.zip`，26,441,827 字节 |
| ZIP SHA256 | `ebec7abb608e951f55b34aee44d4c449212ff98ec28fc8e1ea71149e3cf868ab` |
| 内置基线 | `3.1.7-50d32c4297431172` |
| 更新回归 | `3.1.8-c16ea75e23378f50` |
| 清单故障及恢复版本 | `3.1.9-2f7520c9851f2405` |
| 最终 AOT signature | `b97a93a939ab8eddc2ed0e3741e5ae69a3fe44e1ebe8a40e192d8eefdd1bb460` |
| 当前工程内置版本 | `3.1.7`，与 `boot-release.json` 和最终 APK 一致 |
| 测试服务实际指针 | `http://127.0.0.1:18000/Regression/release.json` → `3.1.9` |

本次修改了 AOT 代码，需要重发 APK。旧 APK 不能只下载新热更 DLL 就获得 Boot/首屏修复。工程内置文件已恢复为匹配的 3.1.7；使用现有完整构建菜单可重新生成正常包名 APK。原 `Builds/Android/freedomtower.apk` 未被本次独立测试构建覆盖，不能把该旧文件当作此次修复包。

现有构建发布流程继续有效：先生成 HybridCLR DLL/AOT 元数据 → 拷贝 DLL 并生成 MD5 → 构建新版本 AB → 发布匹配基线描述符 → 构建 APK。后续热更使用相同 AOT signature，构建并发布完整不可变 release，最后激活根指针。不要覆盖已发布的相同版本内容。

## 最终实测矩阵

MuMu 实例 0，Android 15，设备 `SM-A5560`，现场发现 ADB `127.0.0.1:16384`。最终包首次安装时间为 2026-10-19 15:48:35；没有借用中间包缓存。隔离服务 18000，通过 adb reverse 连接；服务器覆盖为 `/Regression` 子目录，未更改正式 8000 服务或旧测试根指针。

证据根：`E:\MyTowerGame\Builds\BootRefactor\Regression\Final`。

| 证据目录 | 场景与结果 |
|---|---|
| `50-first-offline` | 首装无资源缓存、移除 reverse，8.62 秒 GameReady |
| `51-online-no-update` | 在线无更新，8.21 秒 GameReady |
| `52-release-404-local` | 发布指针 404，本地完整基线可玩 |
| `53-probe-timeout-local` | 发布请求延迟超过探测超时，本地完整基线可玩 |
| `54-incompatible-release-local` | AOT signature 不匹配，回退本地完整组合 |
| `55-malformed-release-local` | 非法 JSON，回退本地完整组合 |
| `56-dll-404-local` | DLL 404，加载程序集前回退本地完整组合 |
| `57-dll-checksum-local` | DLL 校验失败，经有限重试后回退本地完整组合 |
| `58-offline-repeat` | 重复离线启动正常 |
| `59-online-resource-update` | 从 3.1.7 切换至固定 3.1.8 清单，进入游戏 |
| `60-updated-offline` | 3.1.8 的本地完整组合离线可用 |
| `61-manifest-failure` | 3.1.9 清单 hash 注入 404；停在错误页、显示 Retry，未进入 Main |
| `62-manifest-retry-recovery` | 解除 404、真实点击 Retry，同一 PID 下 3.55 秒进入游戏 |
| `63-recovered-offline` | 恢复后的 3.1.9 重启离线正常 |

所有成功启动均核对 GameReady 一次、配置第一次加载成功、Main → Loading → Splash → GameReady 顺序及采样中无 missing script、序列化布局错误、MissingMethodException、NullReferenceException、FATAL。61 的通过含义是正确阻止不完整发布进入 Main；不是故障当时已可玩。

`editor-boot.json/png`：最终源码从 Boot 进入 Main，Configs=true，Launcher=1，HotUpdateView=0，未选 APK 发布。`editor-main.json/png`：直接 Main 同样通过且控制台无错误。`editor-gameplay.json/png` 与原始 MCP 结果记录关卡运行；Android 另经菜单 → 选关 → Start Challenge → Start，日志记录 `[Wave] 回合 1 开始`，截图与日志在 `android-level.png`、`android-gameplay.png`、`android-gameplay-logcat.txt`。

`evidence-index.json` 复核最终 14 个场景零失败，以及 APK 内置描述符、全部 DLL MD5 和 manifest MD5。`http-audit.json` 记录对实际 HTTP 响应的 46 个有效载荷逐项大小及 MD5 校验，零失败。`mcp-verification.json` 记录最终强制刷新后 compilation/domain reload/updating 均 false、ready=true、scriptCompilationFailed=false、控制台 error 为 0。未清空控制台；Play Mode 自身的 Console Clear on Play 设置沿用现场。

中间包 3.1.3、3.1.4 的失败和修复前记录保留在 `Regression` 根部，包括首次离线失败、不可点击重试截图及失败断言；没有将它们混入最终 14 项通过统计。此次 3.1.8/3.1.9 用相同资源内容的新版本清单验证版本选择及恢复，没有重复上一轮可见标记的 DLL/AB/语言差异矩阵。原完整差异测试属于旧 APK 的历史证据，不能冒称全部已在最终 APK 重跑。

本次未覆盖物理 Android 真机、正式非 Development 包、长期运行以及断开域重载的编辑器配置。没有卸载、清数据、覆盖安装原游戏或修改用户配置业务代码。保留用户原有 3.1.2 发布文件及 APK；工程包名、产品名、development=false 已恢复，当前场景 Boot，未在 Play。

复核命令（使用真实 Python，而非 WindowsApps 占位程序）：

```powershell
& 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'E:\MyTowerGame\.workbuddy\tools\boot_regression_20261019.py' --serial 127.0.0.1:16384 --phase audit
```

`matrix/update/recovery` 参数用于上述独立包重新执行场景；会停止该测试包，并在隔离服务临时注入故障，结束时恢复 faults.json。不得将这些故障脚本指向正式目录或生产应用。
