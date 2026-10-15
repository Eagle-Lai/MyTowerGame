using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 资源服务器地址配置（热更资源从哪里下载）。
    ///
    /// ==================================================================
    /// 【本文件在热更链路里的位置】
    ///   打包端（编辑器）：BuildAssetBundles 产出 .bundle + 清单 → 手工/脚本上传到本文件的 URL
    ///   运行端（真机 APK）：YooAsset 走 HostPlayMode，按本文件的 URL 去拉清单与 .bundle
    ///   两端读的是**同一份**配置，改一处即可，不会分叉。
    ///
    /// 【为什么用普通静态类而不是 ScriptableObject】
    ///   ScriptableObject 是**资源**，要让真机读到就得进包（或进 YooAsset 收集）。
    ///   而这份配置恰恰要在"资源系统还没起来"时就用（它是资源系统的入参），
    ///   用资源来配资源是鸡生蛋。所以用最朴素的静态常量 + 可选的命令行覆盖。
    /// ==================================================================
    /// </summary>
    public static class ResServerConfig
    {
        /// <summary>
        /// 是否启用热更（联机运行模式）。
        ///
        ///   false（默认）→ 走"离线模式"，只读随包资源。适合还没有服务器的阶段，
        ///                  以及 **首次出包**（首包必须自带完整资源，否则新装的玩家无网可下）。
        ///   true          → 走 HostPlayMode，启动时去 <see cref="ServerUrl"/> 比对版本并下载差异。
        ///
        /// ⚠️ 首包务必为 false：首包若自带资源又开了热更比对，玩家首次启动就能正常进游戏；
        ///    但若首包资源是空的又开了热更，一旦服务器连不上就是"新玩家完全玩不了"。
        /// </summary>
        public const bool EnableHotUpdate = true;

        /// <summary>
        /// 热更资源服务器根地址（**必须带协议、不带结尾斜杠、不要带平台段**）。
        ///
        /// 【格式】http://<主机>:<端口>/<资源根目录>
        ///
        /// 【多环境支持（公司 / 家 / 模拟器）】
        ///   本常量只是**兜底地址**（优先级最低）。多环境自动切换靠
        ///   BootLoader 启动时对 BootServerSelection.Candidates 的并发探测：
        ///   第一个可达的候选会经 FTProject.AOT.BootServerSelection.SelectedUrl
        ///   传回本类（见 <see cref="GetServerUrl"/> 优先级），改 IP 只动
        ///   BootServerSelection.Candidates 一个地方。
        ///
        ///   本机测试（模拟器内 10.0.2.2 = 宿主机 127.0.0.1）：
        ///     http://10.0.2.2:8000
        ///
        ///   ⚠️ 别写 localhost / 127.0.0.1 —— 那是"手机自己"，手机访问不到你电脑。
        ///   ⚠️ 真机与电脑必须在**同一个 WiFi / 局域网**下。
        ///   ⚠️ 不确定当前 IP 时：电脑上开 cmd 敲 `ipconfig`，看**无线局域网适配器 WLAN**
        ///      下面那行 "IPv4 地址"。
        ///
        /// 【平台段是自动拼的，不要手写】
        ///   YooAsset 会在本地址后面自动追加 `/<平台名>/<包裹名>/<版本>/`，
        ///   例如 Android 上最终会请求：
        ///     http://10.0.2.2:8000/Android/FreeTower/1.0.0/FreeTower.version
        ///   所以这里**只写到平台之前**。多写一段就是 404。
        /// </summary>
        public const string ServerUrl = "http://10.0.2.2:8000";

        /// <summary>
        /// 运行期是否要覆盖地址（调试用）。
        ///   勾上后，启动时会尝试从 persistentDataPath/server.txt 读一行地址覆盖 ServerUrl，
        ///   这样**不用重新打包**就能换服务器 —— 测试阶段非常省时间。
        ///   正式发布前把本开关设为 false 即可（那一行读取本身几乎零成本，保留也无妨）。
        /// </summary>
        public const bool AllowRuntimeOverride = true;

        /// <summary>运行期覆盖文件的位置（放在可写目录，真机上也能改）</summary>
        public static string OverrideFilePath
        {
            get { return System.IO.Path.Combine(Application.persistentDataPath, "server.txt"); }
        }

        /// <summary>
        /// 启动时是否启用热更日志（会把最终使用的地址与来源打出来，排查必备）。
        /// </summary>
        public const bool VerboseLog = true;

        /// <summary>
        /// 取最终生效的服务器地址。优先级（从高到低）：
        ///   ① persistentDataPath/server.txt 的第一行（仅当 <see cref="AllowRuntimeOverride"/>；
        ///      手工覆盖，诊断用，写了就只认它）
        ///   ② Boot 阶段并发探测选中的可达地址（FTProject.AOT.BootServerSelection.SelectedUrl，
        ///      公司/家/模拟器多环境自动切换的产物；dll 热更与 AB 热更因此同源）
        ///   ③ <see cref="ServerUrl"/> 常量（兜底：编辑器直接跑 main 场景、或探测链未执行时）
        /// 返回值保证不含结尾斜杠。
        /// </summary>
        public static string GetServerUrl()
        {
            string url = ServerUrl;

            // ② 启动探测的胜出地址（AOT 侧 Boot 链写入；null = 未探测 / 全部不可达）
            string selected = FTProject.AOT.BootServerSelection.SelectedUrl;
            if (string.IsNullOrEmpty(selected) == false)
            {
                url = selected;
            }

            // ① 手工覆盖文件：最高优先级，存在即生效（跳过空行与 # 注释行）
            if (AllowRuntimeOverride)
            {
                try
                {
                    string file = OverrideFilePath;
                    if (System.IO.File.Exists(file))
                    {
                        // 只取第一行、去空白：允许在文件里写注释行（以 # 开头）方便自己看
                        string[] lines = System.IO.File.ReadAllLines(file);
                        for (int i = 0; i < lines.Length; i++)
                        {
                            string line = lines[i].Trim();
                            if (line.Length == 0 || line.StartsWith("#"))
                            {
                                continue;
                            }
                            url = line;
                            break;
                        }
                    }
                }
                catch (System.Exception)
                {
                    // 读取失败不影响主流程：静默回退到常量地址。
                    // 【为什么不打日志】这个文件本来就常常不存在，"没文件"不是异常。
                }
            }

            string finalUrl = TrimTrailingSlash(url);

            if (VerboseLog)
            {
                string source = "常量 ServerUrl";
                if (selected != null && selected == url)
                {
                    source = "启动探测（BootServerSelection）";
                }
                if (AllowRuntimeOverride && System.IO.File.Exists(OverrideFilePath))
                {
                    source = "server.txt 覆盖";
                }
                Debug.Log("[Res] 生效服务器地址：" + finalUrl + "（来源：" + source + "）");
            }

            return finalUrl;
        }

        /// <summary>地址是否是一个可用的远端地址（用于把"没配服务器"和"配错了"区分开）</summary>
        public static bool IsValidServerUrl(string url)
        {
            if (string.IsNullOrEmpty(url))
            {
                return false;
            }
            return url.StartsWith("http://", System.StringComparison.OrdinalIgnoreCase)
                || url.StartsWith("https://", System.StringComparison.OrdinalIgnoreCase);
        }

        /// <summary>
        /// 远端热更（AB 资源 + dll 两条链路共用的总闸门）当前是否应当启用。
        ///
        /// 【为什么需要这个判定 — 2026-10-15 修复】
        ///   真机曾出现"服务器不可用 → 启动一直等待 → 最终进不去游戏"：
        ///   dll 侧有探测兜底，但 AB 侧此前**无条件**走 HostPlayMode，
        ///   会对不可达地址请求包裹版本（默认 60s 超时且硬失败），把启动拖死。
        ///   修复后两条链路共用同一判定：启动最早期由 BootLoader 以 1 秒超时探测服务器
        ///   （BootServerSelection），结论"不可达"时本方法返回 false，此时：
        ///     · AB 侧 → YooAsset 直接走离线模式（只读随包资源，不发任何网络请求）；
        ///     · 更新检查 → 跳过版本比对与下载，立刻用本地资源继续启动（onDone(false)）。
        ///
        /// 判定 = ①总开关开启 ∧ ②地址是合法 http(s) 地址 ∧
        ///        ③启动链未判定"服务器不可达"（未探测过的环境不做第③条，维持旧行为）。
        /// </summary>
        public static bool IsRemoteHotUpdateAllowed()
        {
            // 【为什么先落到局部变量】EnableHotUpdate 是 const，直接与 false 比较会被
            // 编译器折叠成"永不执行的分支"并报 CS0162（Unreachable code）；落到局部
            // 变量后语义不变且无警告 —— 该开关本就是"改源码切换"的配置项，
            // 两种取值的代码路径都要保留。
            bool hotEnabled = EnableHotUpdate;
            if (hotEnabled == false)
            {
                return false;
            }

            // ③ 启动探测结论：已探测且无胜出 → 服务器不可达（跳过地址读取，最快返回）
            if (FTProject.AOT.BootServerSelection.RemoteHotUpdateAllowed == false)
            {
                return false;
            }

            // ② 地址合法性（GetServerUrl 内部按 优先级 决定最终地址）
            return IsValidServerUrl(GetServerUrl());
        }

        private static string TrimTrailingSlash(string url)
        {
            if (string.IsNullOrEmpty(url))
            {
                return url;
            }
            return url.TrimEnd('/');
        }
    }
}
