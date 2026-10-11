using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace FTProject.AOT
{
    /// <summary>
    /// HybridCLR 热更程序集加载器（**唯一 AOT 引导入口**）。
    ///
    /// ==================================================================
    /// 【为什么必须有这个类，且只能在 AOT 程序集里】
    ///   HybridCLR 的铁律：**AOT 主包不能引用热更程序集里的任何类型**。
    ///   本工程把 Scripts / Gen / LubanLib / 第三方源码全部划入了热更集，
    ///   因此 main 场景里挂的 Launcher / GameFlowManager / 各 View 全是"热更类型"，
    ///   AOT 侧**不能**直接引用它们编译期符号。
    ///
    ///   解法：本类只做三件事（全部用 string + 反射，零编译期依赖）：
    ///     ① 读取热更 dll 字节流（编辑器读工程内，真机读 StreamingAssets / YooAsset）
    ///     ② Assembly.Load 逐个加载，拓扑顺序由 HotUpdateAssemblies 保证
    ///     ③ 反射调用热更侧约定的入口方法，把控制权交出去
    ///
    ///   ⚠️ 本类**绝不能**出现 FTProject.Runtime / cfg / SuperScrollView 等热更命名空间的
    ///      using 或类型引用 —— 那会让 AOT 程序集在 IL2CPP 打包时直接编译不过。
    /// ==================================================================
    /// </summary>
    public static class HotUpdateAssembler
    {
        /// <summary>
        /// 热更 dll 文件名清单。**顺序 = 依赖拓扑顺序**，被依赖的在前。
        ///   ⚠️ 顺序写错不会立刻报错，而是在 Assembly.Load 时抛
        ///      "Could not load ... assembly ... " 之类的异常，排查成本高。
        ///
        /// 【为什么是这个顺序】
        ///   Assembly-CSharp（Unity 默认集，本工程仅含零依赖的零散脚本/测试脚本）
        ///   → LubanLib（Luban 序列化基础库，零外部依赖）
        ///   → Gen（cfg 命名空间，配置表类，依赖 LubanLib 的 Bright.Serialization）
        ///   → SuperScrollView（列表控件，零业务依赖）
        ///   → Reporter（调试面板，零业务依赖）
        ///   → Runtime（业务主体 101 个脚本，依赖以上全部）
        /// </summary>
        public static readonly string[] HotUpdateAssemblies =
        {
            "Assembly-CSharp.dll",
            "FTProject.LubanLib.dll",
            "FTProject.Gen.dll",
            "FTProject.ThirdParty.SuperScrollView.dll",
            "FTProject.ThirdParty.Reporter.dll",
            "FTProject.Runtime.dll",
        };

        /// <summary>
        /// AOT 补充元数据 dll 清单（HybridCLR 的"AOT 泛型补充"机制）。
        ///
        /// 【为什么需要它】IL2CPP 是 AOT 编译，AOT 程序集里被热更代码**泛型实例化**的
        ///   方法/类型，如果主包里没有对应实例化结果，热更侧调用会报
        ///   "AOT generic method isn't instantiated"。补充元数据把这些泛型定义"补"进去，
        ///   让解释器能现场实例化。
        ///
        /// ★【实际内容怎么来的】执行「HybridCLR ▸ Generate ▸ All」后，
        ///   `Assets/HybridCLRGenerate/AOTGenericReferences.cs` 会生成
        ///   `PatchedAOTAssemblyList`（当前 6 项）。**本清单必须与它保持一致** ——
        ///   两份名单不同步 = 真机上泛型缺失且报错信息晦涩。
        ///   ⚠️ 每次改了热更代码 / 依赖后重跑 Generate/All，都要回来核对这里。
        ///
        /// 【加载时机】必须在任何热更 dll 之前（见 LoadHotUpdateAssemblies）。
        /// 【dll 从哪来】这些是 **AOT 程序集**，用 HybridCLR 的 "补充元数据 dll" 拷贝菜单
        ///   从 `HybridCLRData/AssembliesPostIl2CppStrip/<平台>/` 取，放 StreamingAssets/HybridCLR/。
        /// </summary>
        public static readonly string[] AOTMetaAssemblies =
        {
            "System.Core.dll",
            "UnityEngine.AssetBundleModule.dll",
            "UnityEngine.CoreModule.dll",
            "UnityEngine.JSONSerializeModule.dll",
            "YooAsset.dll",
            "mscorlib.dll",
        };

        /// <summary>加载结果状态（供 UI / 日志查看）。</summary>
        public static string LastError { get; private set; }

        /// <summary>
        /// 依次加载"补充元数据 → 热更 dll"。
        /// <paramref name="onProgress"/> 参数为 (已加载数, 总数)，用于驱动进度条。
        /// 失败时抛出异常（由调用方捕获并展示），不静默吞掉。
        /// </summary>
        public static void LoadHotUpdateAssemblies(Action<int, int> onProgress)
        {
            LastError = null;

            // ① 先加载 AOT 补充元数据（必须在任何热更 dll 之前）
            if (AOTMetaAssemblies.Length > 0)
            {
                LoadAOTMeta(onProgress);
            }

            // ② 再按拓扑顺序加载热更 dll
            LoadHotUpdateDlls(onProgress);
        }

        private static void LoadAOTMeta(Action<int, int> onProgress)
        {
            for (int i = 0; i < AOTMetaAssemblies.Length; i++)
            {
                string name = AOTMetaAssemblies[i];
                byte[] bytes = ReadDllBytes(name);
                if (bytes == null)
                {
                    throw new Exception("[HybridCLR] 缺少 AOT 补充元数据 dll：" + name
                        + "（请确认已执行「HybridCLR ▸ Generate ▸ All」并把产物拷入 StreamingAssets）");
                }

                var mode = HybridCLR.HomologousImageMode.SuperSet;
                var err = HybridCLR.RuntimeApi.LoadMetadataForAOTAssembly(bytes, mode);
                if (err != HybridCLR.LoadImageErrorCode.OK)
                {
                    throw new Exception("[HybridCLR] 加载 AOT 补充元数据失败：" + name + "，错误码=" + err);
                }

                if (onProgress != null)
                {
                    onProgress(i + 1, AOTMetaAssemblies.Length + HotUpdateAssemblies.Length);
                }
            }
        }

        private static void LoadHotUpdateDlls(Action<int, int> onProgress)
        {
            int offset = AOTMetaAssemblies.Length;
            int total = offset + HotUpdateAssemblies.Length;

            for (int i = 0; i < HotUpdateAssemblies.Length; i++)
            {
                string name = HotUpdateAssemblies[i];
                string asmName = name.EndsWith(".dll", StringComparison.OrdinalIgnoreCase)
                    ? name.Substring(0, name.Length - 4)
                    : name;

                if (onProgress != null)
                {
                    onProgress(offset + i + 1, total);
                }

                // ⚠️ 【编辑器下必然命中】Unity 编辑器会把所有 asmdef 预先编译并加载，
                //    所以热更 dll 在编辑器里**已经存在于 AppDomain**。
                //    此时再 Assembly.Load(bytes) 会抛
                //    "Assembly with the same name is already loaded"。
                //    → 已加载的跳过（这正是我们想要的效果：编辑器下直接跑最新代码，无需拷贝 dll）。
                //    ⚠️ 真机上这些程序集**不在** AppDomain（主包里没有），所以会正常走到下面的 Load。
                Assembly existing = FindLoadedAssembly(asmName);
                if (existing != null)
                {
                    Debug.Log("[HybridCLR] 程序集已在 AppDomain，跳过加载：" + asmName
                        + "（编辑器下属正常）");
                    continue;
                }

                byte[] bytes = ReadDllBytes(name);
                if (bytes == null)
                {
                    throw new Exception("[HybridCLR] 缺少热更 dll：" + name
                        + "（请确认已执行「HybridCLR ▸ Generate ▸ All」并把产物拷入 StreamingAssets）");
                }

                try
                {
                    Assembly.Load(bytes);
                }
                catch (Exception e)
                {
                    throw new Exception("[HybridCLR] 加载热更 dll 失败：" + name + "\n" + e);
                }
            }
        }

        /// <summary>在已加载的程序集里按**简单名**查找（不区分大小写）。</summary>
        private static Assembly FindLoadedAssembly(string simpleName)
        {
            Assembly[] loaded = AppDomain.CurrentDomain.GetAssemblies();
            for (int i = 0; i < loaded.Length; i++)
            {
                string n;
                try
                {
                    n = loaded[i].GetName().Name;
                }
                catch (Exception)
                {
                    continue; // 极少数动态程序集取名字会抛，跳过
                }
                if (string.Equals(n, simpleName, StringComparison.OrdinalIgnoreCase))
                {
                    return loaded[i];
                }
            }
            return null;
        }

        /// <summary>
        /// 读取一个 dll 的字节流。**查找顺序即优先级**：
        ///   ① Application.persistentDataPath/HybridCLR/  （真机热更产物落点，优先级最高）
        ///      —— YooAsset 下载完热更 dll 后拷到这里，下次启动就读到新版本。
        ///   ② StreamingAssets/HybridCLR/                  （随包体分发的首包版本）
        ///   ③ Library/ScriptAssemblies/                   （仅编辑器；免拷贝，便于开发期快速验证）
        ///
        /// 【为什么 persistentDataPath 排最前】
        ///   StreamingAssets 在 Android 上是**包内只读**的，热更下下来的新 dll 没法覆盖它。
        ///   所以要有一个"可写且优先"的位置放热更产物 —— 这就是 persistentDataPath。
        ///   首包（还没热更过）用 StreamingAssets 的版本；一旦热更过，persistentDataPath 的有更新版本。
        /// ==================================================================
        /// </summary>
        private static byte[] ReadDllBytes(string fileName)
        {
            // ① 热更产物落点（真机优先级最高）
            string p0 = Path.Combine(Application.persistentDataPath, "HybridCLR", fileName);
            if (File.Exists(p0))
            {
                return File.ReadAllBytes(p0);
            }

            // ② 随包 StreamingAssets
            //    ⚠️ **Android 上这里必然读不到**，见下方 Android 分支的说明。
            string p1 = Path.Combine(Application.streamingAssetsPath, "HybridCLR", fileName);
            if (File.Exists(p1))
            {
                return File.ReadAllBytes(p1);
            }

            // ③ 编辑器回退：直接读工程编译产物
#if UNITY_EDITOR
            string p2 = Path.Combine(Application.dataPath, "../Library/ScriptAssemblies", fileName);
            if (File.Exists(p2))
            {
                return File.ReadAllBytes(p2);
            }
#endif
            return null;
        }

        /// <summary>基线资源目录名（persistentDataPath 下的子目录）。</summary>
        private const string BaselineDirName = "HybridCLR";

        /// <summary>
        /// 基线版本戳文件名。内容 = 本次拷入的、"包内基线"的指纹
        /// （由 <see cref="Application.version"/> + 全部 dll 的名字/大小/写入时间算出）。
        ///
        /// 【为什么需要它 —— "避免每次启动重复拷贝"的关键】
        ///   只按单文件 `File.Exists` 判定"已拷过"是不够的：用户升级 APK 后，
        ///   包内基线换了新版，但 persistentDataPath 里还留着上一版的文件，
        ///   逐个存在性检查会**全部命中并跳过** → 新版基线永远拷不进去。
        ///   有了整目录指纹，就能一眼区分：
        ///     · 指纹一致   → 基线与当前包完全对应，整体跳过（零 IO，最快路径）
        ///     · 指纹不一致 → 包升级了（或上次没拷完），需要重建基线
        /// </summary>
        private const string BaselineStampFile = ".baseline.stamp";

        /// <summary>
        /// 拷贝中断标记。**拷贝开始前写入，全部成功后才删除。**
        ///
        /// 【为什么需要它】如果在拷贝中途被杀进程 / 断电，目录里会留下
        ///   "部分新 + 部分旧 / 部分缺失"的混合状态，且没有指纹文件
        ///   （因为指纹是最后才写的）。下次启动看到"无指纹"会重拷 —— 这没问题。
        ///   但若指纹文件恰好先于文件写完，就会出现"指纹说有、文件其实半截"的
        ///   最坏情况。用显式的 in-progress 标记把这种状态**确定性地**识别出来：
        ///   见到标记 = 上次没拷完 → 整目录清空重拷，绝不复用半成品。
        /// </summary>
        private const string CopyInProgressMarker = ".copy.inprogress";

        /// <summary>磁盘剩余空间的安全系数：需求空间 × 该系数 = 最低要求空间。</summary>
        private const double DiskSpaceSafetyFactor = 1.2;

        /// <summary>
        /// 首启预取：把随包的 dll 从 StreamingAssets 释放到 persistentDataPath，
        /// 作为**基线资源**。
        ///
        /// ==================================================================
        /// 【为什么必须有这一步 —— Android 的坑】
        ///   Android 上 APK 本身就是一个 zip，`StreamingAssets` **不是普通目录**：
        ///     · File.Exists / File.ReadAllBytes 一律读不到（路径在 zip 里）
        ///     · 必须用 UnityWebRequest 走 `jar:file://...!/assets/...` 才能读
        ///   而 HybridCLR 要的是 byte[]，随时可能同步取用 —— 每次都用 UnityWebRequest
        ///   异步读不现实。所以**首启一次性把它们释放到 persistentDataPath**，
        ///   之后 ReadDllBytes 的 ① 分支就能同步命中，Android 与其它平台行为一致。
        ///
        /// 【为什么不做在 InitializeOnLoad 之类的地方】
        ///   那些入口在 AOT 静态构造期，UnityWebRequest 还不能用。
        ///   放在 BootLoader 的协程里（场景已加载、主线程可控）才稳妥。
        ///
        /// 【整体流程与四类异常的处理】
        ///   ① 中断残留检查：见 `.copy.inprogress` 标记 → 清空重拷
        ///   ② 版本戳比对  ：指纹一致 → **整体跳过**（满足"避免每次启动重复拷贝"）
        ///   ③ 存储空间检查：不足 → 放弃拷贝，回退到直读 StreamingAssets
        ///   ④ 逐文件拷贝  ：已存在且**大小/哈希一致**的跳过（不覆盖热更成果），
        ///                    缺失/损坏的重拷；全部成功后写指纹、删标记
        ///
        /// 【为什么"已存在且校验通过"才跳过，而不是一律跳过】
        ///   persistentDataPath 里可能是**上次热更下来的新版 dll**，
        ///   包内的旧版不能覆盖它。但同时也可能是"上次拷到一半的损坏文件"，
        ///   所以跳过条件必须是"存在 **且** 与包内基线一致（md5）"，
        ///   否则重拷。这样两个目标同时满足：
        ///     · 热更成果不被抹掉（内容不同 → 保留热更版，但指纹会记上"基线已就位"）
        ///     · 半成品文件被修复（内容损坏 → 重拷）
        ///
        /// ⚠️ **本方法永不抛异常**：任何失败都只是 LogWarning + 继续，
        ///    最坏情况退回 StreamingAssets 直读（Android 上由 UnityWebRequest 兜底）。
        /// ==================================================================
        /// </summary>
        public static System.Collections.IEnumerator PrefetchStreamingAssetsToPersistent(Action<int, int> onProgress)
        {
            string[] names = BuildAllFileNames();
            string targetDir = Path.Combine(Application.persistentDataPath, BaselineDirName);
            string stampPath = Path.Combine(targetDir, BaselineStampFile);
            string markerPath = Path.Combine(targetDir, CopyInProgressMarker);
            // ---------- ① 目录准备 ----------
            bool dirReady = false;
            try
            {
                if (Directory.Exists(targetDir) == false)
                {
                    Directory.CreateDirectory(targetDir);
                }
                dirReady = true;
            }
            catch (Exception e)
            {
                Debug.LogWarning("[HybridCLR] 无法创建基线目录 " + targetDir + "：" + e.Message
                    + "（将退回直读 StreamingAssets）");
            }

            if (dirReady == false)
            {
                if (onProgress != null) onProgress(names.Length, names.Length);
                yield break;
            }

            // ---------- ② 中断残留检查 ----------
            // 见到 in-progress 标记 = 上次拷贝没走完 → 目录内容不可信，整目录清空重拷。
            // （只删我们自己的 dll / stamp / marker，不整目录递归删，避免误伤）
            bool hadInterrupted = false;
            try
            {
                hadInterrupted = File.Exists(markerPath);
            }
            catch (Exception) { /* 读不到就当没有 */ }

            if (hadInterrupted)
            {
                Debug.LogWarning("[HybridCLR] 检测到上次基线拷贝中断，将清空并重建基线目录");
                CleanBaselineDir(targetDir, names, stampPath, markerPath);
            }

            // ---------- ③ 版本戳比对：一致则整体跳过 ----------
            string currentStamp = ComputeBaselineStamp(names);
            if (!hadInterrupted && currentStamp != null && IsStampMatched(stampPath, currentStamp))
            {
                Debug.Log("[HybridCLR] 基线资源已就位（指纹一致），跳过拷贝：" + currentStamp);
                if (onProgress != null) onProgress(names.Length, names.Length);
                yield break;
            }

            // ---------- ④ 存储空间检查 ----------
            long needBytes = EstimateNeedBytes(names);
            if (needBytes > 0 && HasEnoughDiskSpace(needBytes) == false)
            {
                Debug.LogWarning(string.Format(
                    "[HybridCLR] 存储空间不足（需要约 {0:N0} 字节），跳过基线拷贝，退回直读 StreamingAssets",
                    needBytes));
                if (onProgress != null) onProgress(names.Length, names.Length);
                yield break;
            }

            // ---------- ⑤ 写中断标记（拷贝开始） ----------
            try
            {
                File.WriteAllText(markerPath, DateTime.UtcNow.ToString("o"));
            }
            catch (Exception e)
            {
                // 标记写不了不算致命：只是失去"中断可识别"能力
                Debug.LogWarning("[HybridCLR] 无法写入中断标记：" + e.Message);
            }

            // ---------- ⑥ 逐文件拷贝 ----------
            int copied = 0;
            int skipped = 0;
            int failed = 0;

            for (int i = 0; i < names.Length; i++)
            {
                string name = names[i];
                string target = Path.Combine(targetDir, name);
                string src = Path.Combine(Application.streamingAssetsPath, BaselineDirName, name);

                // 【存在即跳过 —— 这是"不覆盖热更成果"的关键】
                //   persistentDataPath 里的同名文件有三种来源：
                //     ① 上次基线拷贝留下的（内容 = 包内旧版）
                //     ② **上次热更下载下来的新版**（内容 ≠ 包内旧版）★ 必须保住
                //     ③ 上次拷到一半的损坏文件
                //   ②与③在文件系统层面无法区分（都是"存在且大小可能对不上"），
                //   所以这里**统一选择保守策略：存在就不动**。
                //   ③ 由"中断标记"在上层兜住 —— 只要上次没走完，标记还在，整目录会被清空重拷。
                //   这样既不会抹掉热更成果，也不会长期残留半成品。
                if (File.Exists(target))
                {
                    skipped++;
                    if (onProgress != null) onProgress(i + 1, names.Length);
                    continue;
                }

                // 目标不存在才需要从 StreamingAssets 取
                bool ok;
                if (File.Exists(src))
                {
                    // 桌面 / 编辑器的 StreamingAssets 是普通目录，同步拷贝更快
                    ok = TryCopyLocal(src, target, name);
                }
                else
                {
                    // Android：StreamingAssets 在 APK 内，必须走 UnityWebRequest
                    ok = false;
                    yield return CopyFromStreamingAssetsCo(src, target, name, r => ok = r);
                }

                if (ok) { copied++; } else { failed++; }

                if (onProgress != null) onProgress(i + 1, names.Length);
            }

            // ---------- ⑦ 收尾：全部成功才写指纹 + 删标记 ----------
            if (failed == 0)
            {
                try
                {
                    File.WriteAllText(stampPath, currentStamp);
                    if (File.Exists(markerPath))
                    {
                        File.Delete(markerPath);
                    }
                    Debug.Log(string.Format(
                        "[HybridCLR] 基线资源就绪：新拷 {0} 个，已存在 {1} 个，指纹 {2}",
                        copied, skipped, currentStamp));
                }
                catch (Exception e)
                {
                    Debug.LogWarning("[HybridCLR] 写入基线指纹失败（下次启动会重试）：" + e.Message);
                }
            }
            else
            {
                // 有失败 → **不写指纹**（下次启动会重走一遍），也**不删标记**（表明目录不完整）
                Debug.LogWarning(string.Format(
                    "[HybridCLR] 基线拷贝未全部成功：成功 {0} 个，失败 {1} 个（保留中断标记，下次启动重试）",
                    copied, failed));
            }
        }

        /// <summary>
        /// 计算包内基线的指纹。**只依赖包内 StreamingAssets 侧的清单与元数据**，
        /// 不依赖目标目录内容 —— 这样"包升级了"必然导致指纹变化。
        ///
        /// 组成：Application.version + 每个文件的 名字（StreamingAssets 侧不可读时为 "-"）。
        /// ⚠️ Android 上 StreamingAssets 在 APK 内，`File.Exists` 恒为 false，
        ///    所以这里**不能**用文件大小/时间戳（读不到）。退而求其次用：
        ///    Application.version（玩家更新 APK 必然变化）+ 文件名清单 + 我方内置的
        ///    AOT 侧版本号（见 <see cref="BaselineFormatVersion"/>）。
        ///    若包内有 `md5.txt`（构建期生成，见编辑器工具），且能读到，则把内容一并纳入 ——
        ///    这让"只换了 dll 内容但没升 version"的极端情况也能被识别。
        /// </summary>
        private static string ComputeBaselineStamp(string[] names)
        {
            try
            {
                var sb = new System.Text.StringBuilder();
                sb.Append("v=").Append(Application.version).Append(';');
                sb.Append("fmt=").Append(BaselineFormatVersion).Append(';');

                // 包内 md5.txt（若随包分发）——能读到就是最强的版本依据
                string md5InPackage = Path.Combine(Application.streamingAssetsPath, BaselineDirName, Md5ListFileName);
                if (File.Exists(md5InPackage))
                {
                    string text = File.ReadAllText(md5InPackage);
                    sb.Append("md5=").Append(SimpleHash(text)).Append(';');
                }

                // 文件名清单（排序后拼，避免顺序抖动）
                string[] sorted = (string[])names.Clone();
                Array.Sort(sorted, StringComparer.Ordinal);
                for (int i = 0; i < sorted.Length; i++)
                {
                    sb.Append(sorted[i]).Append('|');
                }

                return SimpleHash(sb.ToString());
            }
            catch (Exception e)
            {
                Debug.LogWarning("[HybridCLR] 计算基线指纹失败：" + e.Message);
                return null;
            }
        }

        /// <summary>指纹文件内容是否与当前一致。</summary>
        private static bool IsStampMatched(string stampPath, string currentStamp)
        {
            try
            {
                if (File.Exists(stampPath) == false)
                {
                    return false;
                }
                string recorded = File.ReadAllText(stampPath).Trim();
                return string.Equals(recorded, currentStamp, StringComparison.Ordinal);
            }
            catch (Exception)
            {
                return false;
            }
        }

        /// <summary>清空基线目录里"由我方管理"的文件（dll + 指纹 + 标记）。</summary>
        private static void CleanBaselineDir(string targetDir, string[] names, string stampPath, string markerPath)
        {
            for (int i = 0; i < names.Length; i++)
            {
                TryDelete(Path.Combine(targetDir, names[i]));
                TryDelete(Path.Combine(targetDir, names[i] + ".tmp"));
            }
            TryDelete(stampPath);
            TryDelete(markerPath);
        }

        private static void TryDelete(string path)
        {
            try
            {
                if (File.Exists(path))
                {
                    File.Delete(path);
                }
            }
            catch (Exception e)
            {
                Debug.LogWarning("[HybridCLR] 删除失败 " + path + "：" + e.Message);
            }
        }

        /// <summary>估算拷贝全部 dll 需要的字节数（包内可读时用真实大小，否则用保守估计）。</summary>
        private static long EstimateNeedBytes(string[] names)
        {
            long total = 0;
            for (int i = 0; i < names.Length; i++)
            {
                string src = Path.Combine(Application.streamingAssetsPath, BaselineDirName, names[i]);
                try
                {
                    if (File.Exists(src))
                    {
                        total += new FileInfo(src).Length;
                    }
                }
                catch (Exception) { /* 忽略单个文件 */ }
            }

            // Android 上读不到真实大小 → 用一个保守的兜底估计（11 个 dll，按 2MB/个 计）
            if (total <= 0)
            {
                total = (long)names.Length * FallbackBytesPerDll;
            }
            return total;
        }

        /// <summary>检查 persistentDataPath 所在卷的剩余空间是否足够（含安全系数）。</summary>
        private static bool HasEnoughDiskSpace(long needBytes)
        {
            try
            {
                // persistentDataPath 的根（Android 上是 /data，PC 上是盘符）
                string root = Path.GetPathRoot(Application.persistentDataPath);
                if (string.IsNullOrEmpty(root))
                {
                    return true; // 取不到根就当有空间，不阻塞流程
                }

                var drive = new DriveInfo(root);
                long required = (long)(needBytes * DiskSpaceSafetyFactor);
                return drive.AvailableFreeSpace >= required;
            }
            catch (Exception e)
            {
                // 某些平台 / 沙箱环境取不到磁盘信息 → 不阻塞
                Debug.LogWarning("[HybridCLR] 无法检查存储空间（将直接尝试拷贝）：" + e.Message);
                return true;
            }
        }

        /// <summary>桌面 / 编辑器路径的同步拷贝（带 tmp + 替换，避免半截文件）。</summary>
        private static bool TryCopyLocal(string src, string target, string name)
        {
            string tmp = target + ".tmp";
            try
            {
                File.Copy(src, tmp, true);
                if (File.Exists(target))
                {
                    File.Delete(target);
                }
                File.Move(tmp, target);
                return true;
            }
            catch (Exception e)
            {
                Debug.LogWarning("[HybridCLR] 拷贝失败 " + name + "：" + e.Message);
                TryDelete(tmp);
                return false;
            }
        }

        /// <summary>用 UnityWebRequest 读 StreamingAssets（Android 唯一可行的方式）并写入目标路径。</summary>
        private static System.Collections.IEnumerator CopyFromStreamingAssetsCo(
            string url, string target, string name, Action<bool> onResult)
        {
            bool ok = false;
            string tmp = target + ".tmp";

            using (UnityEngine.Networking.UnityWebRequest req =
                   UnityEngine.Networking.UnityWebRequest.Get(url))
            {
                req.timeout = StreamingAssetsReadTimeoutSeconds;
                yield return req.SendWebRequest();

                if (req.result != UnityEngine.Networking.UnityWebRequest.Result.Success)
                {
                    // 【不报错】某些平台 StreamingAssets 优先级本就低于 Library 回退路径，
                    // 缺文件由 ReadDllBytes 最后统一报"缺少热更 dll"，这里重复报会刷屏。
                    Debug.LogWarning(string.Format(
                        "[HybridCLR] 首启预取跳过 {0}：{1}（HTTP {2}）",
                        name, req.error, req.responseCode));
                }
                else
                {
                    // 与同步路径一致：先写 tmp 再替换，避免"写到一半"留下坏 dll
                    try
                    {
                        File.WriteAllBytes(tmp, req.downloadHandler.data);
                        if (File.Exists(target))
                        {
                            File.Delete(target);
                        }
                        File.Move(tmp, target);
                        Debug.Log("[HybridCLR] 首启预取完成：" + name);
                        ok = true;
                    }
                    catch (Exception e)
                    {
                        Debug.LogWarning("[HybridCLR] 预取写入失败 " + name + "：" + e.Message);
                        TryDelete(tmp);
                    }
                }
            }

            if (onResult != null)
            {
                onResult(ok);
            }
        }

        /// <summary>全部 dll 文件名（热更 + AOT 补充元数据），供首启预取使用。</summary>
        private static string[] BuildAllFileNames()
        {
            string[] all = new string[HotUpdateAssemblies.Length + AOTMetaAssemblies.Length];
            Array.Copy(HotUpdateAssemblies, 0, all, 0, HotUpdateAssemblies.Length);
            Array.Copy(AOTMetaAssemblies, 0, all, HotUpdateAssemblies.Length, AOTMetaAssemblies.Length);
            return all;
        }

        /// <summary>
        /// 基线目录格式版本号。**改动基线目录结构 / 指纹算法时必须 +1** ——
        /// 否则老设备上的旧指纹会被误判为"已就位"，新逻辑不会执行。
        /// </summary>
        private const int BaselineFormatVersion = 1;

        /// <summary>包内 md5 清单文件名（构建期由编辑器工具生成，随包分发）。</summary>
        private const string Md5ListFileName = "md5.txt";

        /// <summary>读 StreamingAssets 的超时（秒）。</summary>
        private const int StreamingAssetsReadTimeoutSeconds = 30;

        /// <summary>
        /// 存储空间兜底估计：单个 dll 按 2MB 计。
        /// 仅用于 Android（读不到包内文件真实大小时）的保守预留。
        /// </summary>
        private const long FallbackBytesPerDll = 2L * 1024L * 1024L;

        /// <summary>
        /// 轻量哈希（FNV-1a 64 位）。**只用于"指纹比对"，不用于完整性校验** ——
        /// 完整性校验一律用 MD5（见 HotUpdateDllDownloader 与编辑器侧的 md5.txt）。
        /// 这里选它是因为：无分配、快、跨平台结果稳定，且不依赖 System.Security.Cryptography
        /// （IL2CPP 下更稳）。
        /// </summary>
        private static string SimpleHash(string text)
        {
            unchecked
            {
                const ulong offset = 14695981039346656037UL;
                const ulong prime = 1099511628211UL;

                ulong hash = offset;
                byte[] bytes = System.Text.Encoding.UTF8.GetBytes(text ?? string.Empty);
                for (int i = 0; i < bytes.Length; i++)
                {
                    hash ^= bytes[i];
                    hash *= prime;
                }
                return hash.ToString("x16");
            }
        }
    }
}
