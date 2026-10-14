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
        ///   本机测试（推荐先用这个）：
        ///     http://192.168.43.100:8000       ← 本机 WLAN 网卡的局域网 IP（换网络会自动变）
        ///
        ///   ⚠️ 别写 localhost / 127.0.0.1 —— 那是"手机自己"，手机访问不到你电脑。
        ///   ⚠️ 真机必须和电脑在**同一个 WiFi / 局域网**下。
        ///   ⚠️ 不确定当前 IP 时：电脑上开 cmd 敲 `ipconfig`，看**无线局域网适配器 WLAN**
        ///      下面那行 "IPv4 地址"。手机与电脑连同一个热点时，这个地址通常形如 192.168.x.x。
        ///
        /// 【平台段是自动拼的，不要手写】
        ///   YooAsset 会在本地址后面自动追加 `/<平台名>/<包裹名>/<版本>/`，
        ///   例如 Android 上最终会请求：
        ///     http://192.168.43.100:8000/Android/FreeTower/1.0.0/FreeTower.version
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
        /// 取最终生效的服务器地址。优先级：
        ///   ① persistentDataPath/server.txt 的第一行（仅当 <see cref="AllowRuntimeOverride"/>）
        ///   ② <see cref="ServerUrl"/> 常量
        /// 返回值保证不含结尾斜杠。
        /// </summary>
        public static string GetServerUrl()
        {
            string url = ServerUrl;

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

            return TrimTrailingSlash(url);
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
