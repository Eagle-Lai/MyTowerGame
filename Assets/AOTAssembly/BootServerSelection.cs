using System;
using System.Collections.Generic;
using System.Net;
using System.Net.Sockets;
using System.Threading;
using UnityEngine;

namespace FTProject.AOT
{
    /// <summary>
    /// 热更服务器选址（**单一来源**）：常量兜底候选 + UDP 自动发现 + 探测胜出结果。
    ///
    /// ==================================================================
    /// 【解决什么问题】
    ///   开发机在两个环境跑：
    ///     · 公司＝模拟器（MuMu/AVD）→ 访问宿主机走 10.0.2.2（NAT 网关常量，
    ///       与局域网 IP 无关，**永不变**）；
    ///     · 家＝手机真机 → 需要电脑的局域网 IP，但 DHCP 下 **IP 会变**。
    ///   以前单常量地址换环境就得改代码重打包，漏改即"热更静默失效"
    ///   （探测超时 → 跳过热更 → 玩本地旧版本，不报错）。
    ///
    /// 【自动发现怎么工作】
    ///   电脑上跑 `.workbuddy/tools/hotupdate_server.py`（HTTP 8000 + UDP 广播），
    ///   每秒向局域网广播 "FTHOTUPD1|port=8000"；本类 <see cref="StartDiscovery"/>
    ///   在 Boot 阶段开后台线程监听 UDP 28000，收到广播后取**来源 IP** 拼
    ///   http 地址作为候选 —— 电脑 IP 怎么变都能自动拿到。
    ///   随后 BootLoader 对候选做 HTTP 探测（md5.txt 200 校验），
    ///   天然过滤误报（别的设备恰好在 8000 端口上开了非本项目的服务）。
    ///
    /// 【选址优先级（与 ResServerConfig.GetServerUrl 一致）】
    ///   ① persistentDataPath/server.txt 第一行（手工覆盖，诊断用）
    ///   ② <see cref="SelectedUrl"/>（UDP 发现 / 常量候选中**探测可达**者）
    ///   ③ ResServerConfig.ServerUrl 常量（兜底）
    ///
    /// 【可达性结论（2026-10-15 新增）】探测段结束后 BootLoader 无条件调用
    ///   <see cref="MarkReachabilityChecked"/>；<see cref="RemoteHotUpdateAllowed"/>
    ///   是 AB 资源与 dll 两条链路共用的闸门 —— 服务器不可达时全部改用本地资源。
    ///
    /// 【为什么放 AOT 侧】dll 下载发生在热更程序集加载**之前**，只能由 AOT 驱动；
    ///   热更侧允许引用 AOT，ResServerConfig 经本类读胜出地址，两链路同源。
    /// ==================================================================
    /// </summary>
    public static class BootServerSelection
    {
        /// <summary>
        /// 常量兜底候选（UDP 发现失败时的最后阵地）。
        ///   · 10.0.2.2 = 模拟器 NAT 网关（公司场景主路径，永不变）；
        ///   · 若某环境 IP 长期固定（或有公网/内网穿透地址），可在此追加一行，
        ///     例如 "http://192.168.1.100:8000"。
        /// 家里真机的 IP **不需要**写在这里 —— 由 UDP 自动发现接管。
        /// </summary>
        public static readonly string[] Candidates = new string[]
        {
            "http://10.0.2.2:8000",
        };

        // ---------------- UDP 自动发现（与 hotupdate_server.py 配对） ----------------

        /// <summary>UDP 监听端口。**必须与 hotupdate_server.py --udp-port 一致**。</summary>
        public const int UdpListenPort = 28000;

        /// <summary>广播包魔数前缀。**必须与 hotupdate_server.py 的 MAGIC 一致**。</summary>
        private const string UdpMagic = "FTHOTUPD1|";

        /// <summary>
        /// 未收到任何广播时的监听窗口（秒）。期间常量候选探测在并行跑，不白等。
        ///
        /// 【2026-10-15 起 1.5s（原 2.5s）】取值依据：hotupdate_server.py 默认
        /// --interval 1.0s，即广播间隔 ≈1s —— 任何长度 ≥1s 的窗口都**必然**收到
        /// 至少一轮广播（间隔 1s + 网络抖动余量）。窗口缩短的直接收益：
        /// "服务器不在场"时最多只多等 1.5s 就回退本地资源（与 1s 探测并存）。
        /// </summary>
        private const float UdpWindowSeconds = 1.5f;

        /// <summary>收到首个广播后的收尾窗口（秒）：多网卡会重复广播，留时间汇总去重。</summary>
        private const float UdpTailSeconds = 0.6f;

        private static UdpClient _udp;
        private static Thread _udpThread;
        private static volatile bool _udpStop;
        private static readonly object _udpLock = new object();
        private static readonly List<string> _discovered = new List<string>();
        private static float _udpElapsed;
        private static bool _udpFinished = true;

        /// <summary>后台监听是否已结束（收满窗口 / 收到首包后再收尾 / 被提前停止）。</summary>
        public static bool DiscoveryFinished
        {
            get { return _udpFinished; }
        }

        /// <summary>UDP 监听已运行的总时长（秒），供启动日志/状态条显示。</summary>
        public static float DiscoveryElapsed
        {
            get { return _udpElapsed; }
        }

        /// <summary>启动后台 UDP 自动发现（仅 Boot 启动链调用一次；重复调用幂等）。</summary>
        public static void StartDiscovery()
        {
            lock (_udpLock)
            {
                if (_udpThread != null && _udpThread.IsAlive)
                {
                    return;
                }
                _udpStop = false;
                _udpFinished = false;
                _udpElapsed = 0f;
                lock (_discovered)
                {
                    _discovered.Clear();
                }
                _udpThread = new Thread(UdpListenLoop);
                _udpThread.IsBackground = true;
                _udpThread.Start();
                Debug.Log("[Boot] UDP 自动发现启动（监听 :" + UdpListenPort + "，窗口 "
                    + UdpWindowSeconds + "s）");
            }
        }

        /// <summary>停止并释放 UDP 监听（拿到胜出者或决定离线时调用；幂等）。</summary>
        public static void StopDiscovery()
        {
            lock (_udpLock)
            {
                _udpStop = true;
                _udpFinished = true;
                if (_udp != null)
                {
                    try { _udp.Close(); } catch (Exception) { }
                    _udp = null;
                }
            }
        }

        /// <summary>取走当前已发现的候选地址（快照并清空内部缓冲）。</summary>
        public static string[] TakeDiscovered()
        {
            lock (_discovered)
            {
                if (_discovered.Count == 0)
                {
                    return new string[0];
                }
                string[] snapshot = _discovered.ToArray();
                _discovered.Clear();
                return snapshot;
            }
        }

        /// <summary>后台线程：阻塞收包 + 窗口控制（收到首包后进入收尾窗口）。</summary>
        private static void UdpListenLoop()
        {
            // 用 Stopwatch 计时（UnityEngine API 在后台线程不可靠）
            System.Diagnostics.Stopwatch watch = System.Diagnostics.Stopwatch.StartNew();
            double windowEnd = UdpWindowSeconds;
            bool gotPacket = false;
            UdpClient client = null;

            try
            {
                client = new UdpClient(UdpListenPort);
                _udp = client;
                Debug.Log("[Boot] UDP 监听已绑定 :" + UdpListenPort);

                while (_udpStop == false)
                {
                    _udpElapsed = (float)watch.Elapsed.TotalSeconds;

                    if (client.Available > 0)
                    {
                        IPEndPoint ep = new IPEndPoint(IPAddress.Any, 0);
                        byte[] data = client.Receive(ref ep);
                        if (gotPacket == false)
                        {
                            // 首包到达：窗口收窄为"已等时长 + 收尾窗"（汇总多网卡重复包）
                            gotPacket = true;
                            windowEnd = _udpElapsed + UdpTailSeconds;
                            Debug.Log("[Boot] UDP 收到首个广播 ← " + ep.Address);
                        }
                        string url = ParseBroadcast(data, ep);
                        if (string.IsNullOrEmpty(url) == false)
                        {
                            lock (_discovered)
                            {
                                if (_discovered.Contains(url) == false)
                                {
                                    _discovered.Add(url);
                                    Debug.Log("[Boot] UDP 发现热更服务器候选：" + url);
                                }
                            }
                        }
                    }
                    else if (watch.Elapsed.TotalSeconds >= windowEnd)
                    {
                        break;
                    }
                    else
                    {
                        Thread.Sleep(50);
                    }
                }
            }
            catch (ObjectDisposedException)
            {
                // StopDiscovery 关闭 socket 的正常打断
            }
            catch (SocketException e)
            {
                // 端口被占 / 绑定失败：UDP 发现不可用，静默退化（常量候选仍有效）
                Debug.LogWarning("[Boot] UDP 自动发现不可用（" + e.Message
                    + "），退回常量候选探测。");
            }
            catch (Exception e)
            {
                Debug.LogWarning("[Boot] UDP 自动发现异常（不影响启动）：" + e.Message);
            }
            finally
            {
                if (client != null)
                {
                    try { client.Close(); } catch (Exception) { }
                }
                if (ReferenceEquals(_udp, client))
                {
                    _udp = null;
                }
                _udpFinished = true;
                _udpElapsed = (float)watch.Elapsed.TotalSeconds;
            }
        }

        /// <summary>校验广播包（魔数 + port=）并拼出候选地址；非法包返回 null。</summary>
        private static string ParseBroadcast(byte[] data, IPEndPoint ep)
        {
            try
            {
                string text = System.Text.Encoding.ASCII.GetString(data);
                if (text.StartsWith(UdpMagic, StringComparison.Ordinal) == false)
                {
                    return null;
                }
                string port = "8000";
                foreach (string part in text.Substring(UdpMagic.Length).Split('|'))
                {
                    string kv = part.Trim();
                    if (kv.StartsWith("port=", StringComparison.Ordinal))
                    {
                        port = kv.Substring(5).Trim();
                    }
                }
                return "http://" + ep.Address.ToString() + ":" + port;
            }
            catch (Exception)
            {
                return null;
            }
        }

        // ---------------- 探测胜出结果（跨链路共享给热更侧） ----------------

        /// <summary>启动探测的胜出地址（null = 尚未探测 / 全部不可达）。</summary>
        public static string SelectedUrl { get; private set; }

        /// <summary>胜出地址的来源说明（日志用，如"UDP 发现"）。</summary>
        public static string SelectedSource { get; private set; }

        /// <summary>是否有已选中的可达地址。</summary>
        public static bool HasSelection
        {
            get { return string.IsNullOrEmpty(SelectedUrl) == false; }
        }

        /// <summary>记录探测胜出地址（仅 BootLoader 启动链调用）。</summary>
        public static void SetSelected(string url, string source)
        {
            SelectedUrl = string.IsNullOrEmpty(url) ? null : url.TrimEnd('/');
            SelectedSource = source;
            Debug.Log(string.Format("[Boot] 热更服务器选定：{0}（{1}）", SelectedUrl, source));
        }

        // ---------------- 可达性结论（AB 与 dll 两条链路的共用闸门） ----------------

        /// <summary>
        /// 本次启动是否已完成服务器可达性探测
        /// （BootLoader 探测段跑完后经 <see cref="MarkReachabilityChecked"/> 置位）。
        /// </summary>
        public static bool ReachabilityChecked { get; private set; }

        /// <summary>
        /// 远端热更（AB 资源 + dll）是否应当启用 —— 两条链路共用的总闸门：
        ///   · 尚未探测（编辑器直跑 main、工具脚本等特殊入口）
        ///     → true（维持旧行为，由配置层把关）；
        ///   · 已探测且选出可达地址 → true（走远端，地址见 <see cref="SelectedUrl"/>）；
        ///   · 已探测但无胜出 → false（**服务器不可达 → 全部用本地资源与本地 dll**）。
        /// 消费方：ResServerConfig.IsRemoteHotUpdateAllowed（热更侧据此决定
        /// YooAsset 走离线模式、并跳过热更新检查）。
        /// </summary>
        public static bool RemoteHotUpdateAllowed
        {
            get { return ReachabilityChecked == false || HasSelection; }
        }

        /// <summary>
        /// 记录"可达性探测已完成"。BootLoader 在探测段（server.txt 覆盖 / 常量候选 /
        /// UDP 发现三个分支）结束后**无条件**调用一次 —— 无论结论是可达还是不可达。
        ///
        /// 【为什么必须有这个标记】没有它时，"未探测"与"探测过且不可达"无法区分：
        /// 热更侧见到 SelectedUrl=null 会退回常量地址继续发网络请求 —— 服务器不在场时
        /// 请求要等到超时（YooAsset 版本请求默认 60s 且硬失败），表现为"启动一直等待、
        /// 最终进不去游戏"。置位后下游即可在"不可达"时直接改用本地资源启动。
        /// </summary>
        public static void MarkReachabilityChecked()
        {
            ReachabilityChecked = true;
            Debug.Log("[Boot] 可达性探测完成 → " + (HasSelection
                ? ("服务器可达：" + SelectedUrl)
                : "服务器不可达：本次启动使用本地资源与本地 dll"));
        }
    }
}
