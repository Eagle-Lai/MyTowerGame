# 本地数据持久化（SQLite + AES）实现说明

> 目标：把工程里分散的本地存档逻辑，统一到一个**分层、可替换、带加密**的数据层上。
> 业务层的调用方式**完全没有变化**（`SaveManager.Instance` 的公开成员一字未改）。

---

## 一、分层结构

```
      业务层 / UI
  SelectView · SettingView · GameFlowManager · PopMain
                    │  只调用 SaveManager
                    ▼
  ┌──────────────────────────────────────────────┐
  │ Core/Manager/SaveManager.cs   （业务门面）    │
  │ 关卡解锁/星级 · 会话设置 · 局内快照 · 通用KV   │
  └──────────────────┬───────────────────────────┘
                     │ ISaveStorage（语义化契约）
                     ▼
  ┌──────────────────────────────────────────────┐
  │ Data/Persistence/  （数据层）                 │
  │  SaveStorageFactory ──► SqliteSaveStorage     │
  │        │                    │                 │
  │        │                    ▼                 │
  │        │              IDatabase ──► SqliteDatabase ──► P/Invoke ──► 原生 sqlite3
  │        │                                     │
  │        ├─ ICryptoService（AES-256-CBC+HMAC）  │
  │        ├─ IKeyProvider（分片密钥，无硬编码）   │
  │        └─ SaveSchema（建表 + 版本迁移）        │
  │                                              │
  │   JsonSaveStorage（SQLite 不可用时的回退，兼旧档迁移）
  └──────────────────────────────────────────────┘
```

---

## 二、各模块职责

| 文件 | 职责 | 关键点 |
|---|---|---|
| `DbRow.cs` | 一行查询结果容器（列名 → 值） | 列名大小写不敏感；取值**不抛异常**；`"1"` 按不变文化解析（不受系统语言影响） |
| `IDatabase.cs` | 数据库抽象 + 事务接口 + `DatabaseException` | 业务层只依赖它，换后端不动上层 |
| `SqliteNative.cs` | SQLite 原生库 P/Invoke 声明 | 只用签名与常量；`SQLITE_TRANSIENT` 防 GC 后读到脏内存 |
| `SqliteDatabase.cs` | 连接管理、语句准备/绑定/读取、事务、标量转换 | 一个长连接 + `FULLMUTEX` + 托管锁；所有语句 `try/finally` finalize |
| `SqliteTransaction.cs` | 事务句柄 | 支持嵌套，只有最外层提交；未提交即 Dispose → 回滚 |
| `ICryptoService` / `CryptoService.cs` | 字段级 AES 加解密 | 随机 IV；Encrypt-then-MAC；两把独立子密钥；**明文入参原样返回**（兼容旧数据） |
| `KeyProvider.cs` | 主密钥的分片生成/加载/一致性校验 | 代码内**零密钥常量**；两片分处文件与 PlayerPrefs；带 8 字节一致性校验 |
| `SaveSchema.cs` | 表结构 DDL + 版本迁移框架 | `CREATE TABLE IF NOT EXISTS` 可重复执行；迁移用 switch 逐版本升级 |
| `ISaveStorage.cs` | 语义化存储契约 | 读**不抛异常**，缺数据给默认值；`Initialize` 例外（要能降级） |
| `SqliteSaveStorage.cs` | 表 ↔ 业务对象映射，敏感列自动加解密 | 写穿透；快照主表+子表走事务；业务层看不到任何 SQL |
| `JsonSaveStorage.cs` | SQLite 不可用时的回退后端 | 整体 JSON 再整体加密；**路径复用旧档名，老存档无缝读入** |
| `SaveStorageFactory.cs` | 组装：密钥 → 加密服务 → (SQLite → JSON) | 任一步失败都降级而非崩溃 |

---

## 三、数据表

| 表 | 行数 | 说明 |
|---|---|---|
| `meta` | 多行 | `schema_version` / `created_at`；重置存档时**保留** |
| `player_profile` | 单行 `CHECK(id=1)` | 账号级数据（昵称/金币/钻石/等级），预留 |
| `level_progress` | 每关一行 | `stars` / `best_hp_left` / `clear_count` —— **加密列** |
| `game_settings` | 单行 | 音量、静音（明文） |
| `level_snapshot` | 单行 | 局内快照主表（明文） |
| `snapshot_tower` | 多行 | 快照的塔列表，按 `slot` 排序；保存时整批替换 |
| `kv_store` | 多行 | 通用键值，`sensitive` 逐行标记是否加密 |

**加密列为什么是 TEXT**：密文以 Base64 信封存进 TEXT 列，代价是不能用于 SQL 排序/聚合。
本工程不需要 —— 总星数、已通关数都是在 C# 里遍历累加的。

---

## 四、调用方式

### 4.1 业务侧（已接入，无需改动）

```csharp
// 关卡结算
int stars = SaveManager.EvaluateStars(pd.Hp, pd.MaxHp);
SaveManager.Instance.RecordClear(levelId, stars, pd.Hp);

// 判定解锁 / 读星级
bool open = SaveManager.Instance.IsUnlocked(levelId);
int star  = SaveManager.Instance.GetStars(levelId);
int total = SaveManager.Instance.TotalStars;

// 设置
SaveManager.Instance.SetVolume(0.6f);
SaveManager.Instance.SetMuted(true);

// 局内快照
SaveManager.Instance.SetSnapshot(snap);
if (SaveManager.Instance.HasSnapshot) { var s = SaveManager.Instance.Snapshot; }

// 重置
SaveManager.Instance.ResetAll();
```

### 4.2 其它模块要存自己的零散数据 → 用通用键值

```csharp
// 非敏感（界面偏好等）：密钥缺失时仍可读
SaveManager.Instance.SetUserValue("Ui.LastTab", "2", false);

// 敏感（货币 / 隐私 / 内购凭证）：加密落库
SaveManager.Instance.SetUserValue("Player.Nickname", name, true);

string v;
if (SaveManager.Instance.TryGetUserValue("Player.Nickname", out v)) { /* 已自动解密 */ }
SaveManager.Instance.DeleteUserValue("Ui.LastTab");
```

### 4.3 自检信息

```csharp
SaveManager.Instance.BackendName       // "SQLite 3.50.2" / "JSON 文件（SQLite 回退）"
SaveManager.Instance.StorageLocation   // 实际落盘路径
SaveManager.Instance.EncryptionEnabled // 敏感字段是否真的在加密
```

### 4.4 要新增一张表 / 新增一个持久化字段

1. 在 `SaveSchema.CreateStatements` 里加 `CREATE TABLE IF NOT EXISTS ...`；
2. `SaveSchema.CurrentVersion` +1，并在 `RunMigrations` 的 switch 里补一段 `ALTER TABLE`；
3. 在 `ISaveStorage` 加语义方法 → 在 `SqliteSaveStorage` 与 `JsonSaveStorage` 各实现一次；
4. `SaveManager` 暴露业务入口。

---

## 五、加解密细节

```
密文信封（Base64 后加前缀 "ft1:" 存进 TEXT 列）
┌──────┬──────────┬──────────┬──────────────────────┐
│ 版本 │  IV(16)  │ MAC(16)  │  密文（AES-CBC/PKCS7）│
└──────┴──────────┴──────────┴──────────────────────┘
MAC = HMAC-SHA256(macKey, 版本 ‖ IV ‖ 密文)[0..16]     ← Encrypt-then-MAC
```

- **主密钥**：首次运行随机生成 32 字节，拆成两半分处存放
  - 分片 A → `{persistentDataPath}/ft_keystore.bin`（原子写：临时文件 + 替换）
  - 分片 B → PlayerPrefs（Windows 注册表 / iOS NSUserDefaults / Android SharedPreferences）
  - `master = HMAC-SHA256("FT.Persistence/master/v1", A ‖ B)`
  - 文件内附 8 字节一致性校验，能识别"只还原了其中一处备份"这种隐蔽故障
- **子密钥**：`encKey = HMAC(master,".../enc/v1")`、`macKey = HMAC(master,".../mac/v1")`
- **调试覆盖**：环境变量 `FT_SAVE_KEY`（Base64 的 32 字节）可强制指定主密钥，仅用于自动化测试

### 威胁模型（务必知情）

| 能防 | 不能防 |
|---|---|
| 直接改存档文件、翻看明文、篡改字段（MAC 会拦住） | 有 root/越权能力、能 dump 进程内存或 hook 运行时的攻击者 |

本地加密的固有上限是**密钥必须在客户端参与运算**。需要真正抗作弊时，
关键数值的权威判定要放到服务端，本地加密只当第一道门槛。

---

## 六、平台与原生库

| 平台 | 原生库 | 是否随包分发 |
|---|---|---|
| Windows（编辑器/独立版） | `winsqlite3.dll`（Windows 10 1709+ 自带） | **否**，零配置即可运行 |
| Android | **自带 `libsqlite3.so`**（见下） | **是** |
| iOS | `__Internal`（系统库静态链接） | 否 |

### 6.1 Android 为什么要自带 libsqlite3.so（重要，容易想当然）

Android 系统里**确实**有 `/system/lib64/libsqlite3.so`，但它属于**平台私有库**：
应用 targetSdk ≥ 24 时，链接器的 namespace 机制会拒绝应用 `dlopen` 非公开 NDK 库，
运行时会直接抛异常（不是"能用但版本旧"，是**加载失败**）。

所以工程里自带了一份，与 `PlayerSettings → AndroidTargetArchitectures = ARMv7 | ARM64` 对齐：

```
Assets/Plugins/Android/libs/arm64-v8a/libsqlite3.so
Assets/Plugins/Android/libs/armeabi-v7a/libsqlite3.so
```

构建方式（可复现）：SQLite 官方 amalgamation + Android NDK 交叉编译。
一键重建脚本已入库：**`Tools/build_android_sqlite.sh`**（自动下载源码与 NDK、
编译两个 ABI、用 `llvm-readelf` 校验并回写 `Assets/Plugins/Android/libs/`）：

```bash
bash Tools/build_android_sqlite.sh          # 默认 SQLite 3.50.2 / NDK r25c / API 22
SQLITE_VER=3510000 bash Tools/build_android_sqlite.sh   # 升版只需改这一个变量
```

脚本内核心命令（两个 ABI 只差目标三元组）：

```bash
# 取源码
curl -O https://www.sqlite.org/2025/sqlite-amalgamation-3500200.zip

# 用 NDK 的 clang 包装器编译（arm64）
$NDK/toolchains/llvm/prebuilt/windows-x86_64/bin/aarch64-linux-android22-clang \
    -shared -O2 -fPIC -DHAVE_USLEEP=1 -DSQLITE_OMIT_LOAD_EXTENSION -DSQLITE_DQS=0 \
    -Wl,-soname,libsqlite3.so -s -o libsqlite3.so sqlite3.c

# armv7 同理，换成 armv7a-linux-androideabi22-clang
```

> 下载 NDK 若走 `dl.google.com` 容易中断，脚本里备了腾讯云镜像
> `https://mirrors.cloud.tencent.com/AndroidSDK/android-ndk-r25c-windows.zip`。

`DllImport("sqlite3")` 在 Android 上解析到 `libsqlite3.so`；应用私有库目录的优先级
高于系统目录，所以**一定是** APK 里这一份被加载。

`-DSQLITE_OMIT_LOAD_EXTENSION`：不加载扩展，省掉 dlopen 依赖、也缩小体积；
`-DHAVE_USLEEP=1`：开忙等退避，Android 上更省电。`AndroidMinSdkVersion = 22`，与编译时的 API 22 一致。

### 6.1.1 `.meta` 必须手写，不能靠 Unity 自动生成（★ 容易漏）

`.so` 放进 `libs/<abi>/` **并不等于** ABI 就配对上了 —— `libs/<abi>/` 只是目录约定，
真正决定"进哪个 APK 的 lib 目录、给哪个 CPU"的是 **Plugin Inspector 设置，也就是 `.meta`**。
`.meta` 缺失时 Unity 会自动生成一份默认设置，平台/CPU 完全不受我们控制。

所以每个 `.so` 旁边都有一份显式 `.meta`，把设置钉死：

| 文件 | Android | CPU | Any | Editor |
|---|---|---|---|---|
| `libs/arm64-v8a/libsqlite3.so.meta` | enabled=1 | `ARM64` | 0 | 0 |
| `libs/armeabi-v7a/libsqlite3.so.meta` | enabled=1 | `ARMv7` | 0 | 0 |

- `Any: enabled=0` —— 否则会被塞进所有平台；
- `Editor: enabled=0` —— 编辑器走 `winsqlite3`（见 `SqliteNative` 的 `#if` 分支），
  让编辑器去加载 Android `.so` 只会失败。
- guid 固定（`4141aed6…` / `78681d4c…`），不要重新生成 —— 换 guid 会让 Unity 视为新资源。

这两条（CPU 与目录一致、各平台开关正确）由 `check_native_symbols.py` 每次自动核对。

> **ARMv7 浮点 ABI**：`BindDouble(IntPtr, int, double)` 传 `double`，
> 若编成 hard-float，参数会**静默错位**（不报错、只是数值乱）。
> Android `armeabi-v7a` 要求 **softfp**；本产物 `e_flags = 0x05000200`（含 `EF_ARM_ABI_FLOAT_SOFT`），
> 校验脚本会检查这一位。

### 6.2 Windows 独立版（可选）

若不想依赖操作系统自带的 SQLite：把自备 `sqlite3.dll` 放进 `Assets/Plugins/x86_64/`，
再把 `SqliteNative.WindowsLibrary` 从 `"winsqlite3"` 改成 `"sqlite3"` —— **只改这一处**。

### 6.3 iOS

SQLite 属系统库且被静态链接，用 `__Internal`，无需分发。

---

## 七、已验证 / 待验证

**已在本机验证**（沙箱内无 C# 编译器，故用等价手段）：

- 7 个静态校验脚本全部 PASS（`check_code` / `check_usings` / `check_arity` /
  `check_members` / `check_unity_api` / `check_events` / `check_native_symbols`），
  均实际扫描 104 个 `.cs` 文件；
- 14 个新增/修改文件的括号平衡全部 OK，无类型重名；
- **新增 `check_arity.py`（调用参数个数校验，补 CS1501 这类只有编译器才报的错）**，
  并用一个"故意写错实参个数"的样本验证过它确实能报出来 —— 它修掉了
  `CryptoService.Concat` 传 4 个实参（信封由 4 段拼成，而 helper 只接受 3 个）这个编译错误；
- **新增 `check_native_symbols.py`**：解析 `.so` 的 `.dynsym`，核对
  `SqliteNative.cs` 里 26 个 `DllImport` 入口点是否全部导出（少一个 →
  真机 `EntryPointNotFoundException`，编译期完全看不出来），并顺带校验
  ELF 机器类型、ARMv7 浮点 ABI（必须 softfp）、以及 `.meta` 的平台/CPU 设置。
  对应的 `test_native_symbols_guard.py` 用 7 个注入故障的用例证明它**真的会 FAIL**
  （一个"永远 PASS"的检查等于没有检查）；
- **把 C# 源码里的 SQL 字面量原样抽取出来，交给真实 SQLite 跑通完整流程**：
  建 7 张表 → 版本登记 → 设置写读 → `CHECK(id=1)` 拦截非法行 → 密文列幂等复写
  → 快照主表+子表事务替换（二次保存不累加）→ KV 敏感/非敏感两路 → `ResetAll` 保留 meta → PRAGMA；
- **Android 的 `libsqlite3.so` 由 SQLite 官方 amalgamation（3.50.2）+
  Android NDK r25c 交叉编译得到**，两个 ABI 各导出 271 个 `sqlite3_*` 符号，
  所需 26 个全部为已定义符号；`.meta` 已显式写明 Android + CPU。

**顺手修掉的工具链问题**（否则上面的 PASS 不可信）：

- `check_code.py` / `check_members.py` / `check_unity_api.py` / `check_events.py`
  的 `ROOT` 都写成了 **`D:\FreedomTower\Assets`**（少了 `_1`）—— 该目录不存在，
  `os.walk` 扫 0 个文件，却一律打印 `PASS`。现已全部改为从脚本自身位置推导，
  并加了"扫到 0 个文件就 FAIL"的自检；
- `check_unity_api.py` 按**简单类名**索引 Unity 类型，工程自己的 `Launcher`
  撞上文档里的 `UnityEngine.WSA.Launcher`，把正确的 `Launcher.Instance`
  误报成 CS0117。现已收集工程自声明类型名，同名冲突整体跳过并单独列出（不静默忽略）；
- `check_code.py` 把 `Load<AudioClip>("Audio_" + name)` 里的拼接前缀 `"Audio_"`
  当成完整逻辑名，误报"未登记"。现已识别拼接、跳过片段。

**需在 Unity / 真机里验证**：

- 首次编译（本沙箱无法编译 C#）；
- Editor Play 一局：确认生成 `freetower.db`、`ft_keystore.bin`，日志出现
  `[Save] 存档库就绪：SQLite 3.50.2 …敏感字段加密：已启用`；
- 用 DB 工具打开 `freetower.db`，确认 `level_progress.stars` 等列是 `ft1:` 开头的密文；
- Unity 里选中 `libsqlite3.so` 确认 Plugin Inspector 显示 Android / CPU 正确（应与 `.meta` 一致）；
- **Android 真机**：打包后确认 APK 内含 `lib/arm64-v8a/libsqlite3.so` 与 `lib/armeabi-v7a/libsqlite3.so`，
  且日志显示后端是 `SQLite`（而不是回退成 `JSON 文件`）。
