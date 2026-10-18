using System;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using UnityEditor;
using UnityEngine;

namespace FTProject.EditorTools
{
    /// <summary>
    /// 编辑器内的**本地热更静态服务器**（HTTP/1.1，GET/HEAD），把 HotUpdateServer/ 根目录
    /// 按客户端真实请求路径发布出来，用于"一键热更"的最后一步本地运行验证。
    ///
    /// ==================================================================
    /// 【为什么不用 HttpListener】
    ///   ① Windows 上 HttpListener 需要 URL ACL（非管理员常直接 AccessDenied），
    ///      而这里的端口会随用户配置变化，不可能每次去 netsh 加规则；
    ///   ② 它在 Mono/Unity 里的行为随平台差异较大，出错信息也很难懂。
    ///   直接 TcpListener 手写最小 HTTP 反而稳定、零依赖、错误信息可控。
    ///
    /// 【为什么不用现成的 hotupdate_server.py】
    ///   那个脚本要另外开终端（派生进程在 Windows 上无法常驻），而且它顺带做 UDP 广播，
    ///   在编辑器里跑验证只需要 HTTP。本类只服务"验证"这一个场景；
    ///   真机联调仍然用 python 脚本（它负责 UDP 自动发现，本类不替代它）。
    ///
    /// 【只绑 127.0.0.1】
    ///   验证是编辑器自己发请求，绑回环即可（也避开防火墙弹窗）。
    ///   模拟器访问宿主机走 10.0.2.2 → 映射到宿主机回环，同样可用。
    ///   真机（局域网 IP）请用 python 脚本，它绑 0.0.0.0。
    ///
    /// 【验证用的请求不走系统代理】
    ///   本机 Clash/TUN 会把 127.0.0.1 的请求劫持到代理并返回 502，
    ///   校验器（HotUpdateDeployer）里所有 HttpWebRequest 都显式 `Proxy = null`。
    /// ==================================================================
    /// </summary>
    [InitializeOnLoad]
    public static class HotUpdateLocalServer
    {
        private static TcpListener _listener;
        private static Thread _thread;
        private static volatile bool _running;
        private static string _root;
        private static int _port;
        private static long _served;
        private static string _lastError;

        /// <summary>是否正在服务。</summary>
        public static bool IsRunning { get { return _running; } }

        public static int Port { get { return _port; } }

        public static string Root { get { return _root; } }

        /// <summary>服务地址（未启动时按当前端口给出"预期地址"，供探测失败信息使用）。</summary>
        public static string Url
        {
            get { return "http://127.0.0.1:" + (_port > 0 ? _port : HotUpdateSettings.VerifyPort); }
        }

        /// <summary>已受理的请求数（面板显示"已服务 N 个请求"）。</summary>
        public static long ServedCount { get { return Interlocked.Read(ref _served); } }

        public static string LastError { get { return _lastError; } }

        static HotUpdateLocalServer()
        {
            // 域重载 / 退出编辑器时收掉后台线程，避免线程拿着已卸载的代码继续跑。
            AssemblyReloadEvents.beforeAssemblyReload += Stop;
            EditorApplication.quitting += Stop;
        }

        /// <summary>
        /// 启动（幂等：同 root + 同端口时直接返回 true）。
        /// </summary>
        /// <param name="root">要发布的本地目录（一般是 HotUpdateServer）</param>
        /// <param name="port">端口（被占用时返回 false，并把系统错误放进 error）</param>
        public static bool Start(string root, int port, out string error)
        {
            bool ignored;
            return Start(root, port, out ignored, out error);
        }

        /// <summary>
        /// 启动（带"本次是否真的新起了服务"的返回值）。
        /// 【为什么需要 startedNow】流水线在收尾时只应停掉**自己起的**服务：
        /// 用户可能早就用菜单 10c 起着服务在真机上联调，流水线跑完把它关掉很讨人厌。
        /// </summary>
        public static bool Start(string root, int port, out bool startedNow, out string error)
        {
            error = null;
            startedNow = false;
            if (string.IsNullOrEmpty(root) || !Directory.Exists(root))
            {
                error = "要发布的目录不存在：" + root;
                return false;
            }

            if (_running && _port == port
                && string.Equals(_root, Path.GetFullPath(root), StringComparison.OrdinalIgnoreCase))
            {
                return true;
            }

            Stop();

            try
            {
                TcpListener listener = new TcpListener(IPAddress.Loopback, port);
                listener.Start();

                _listener = listener;
                _root = Path.GetFullPath(root);
                _port = port;
                _served = 0;
                _lastError = null;
                _running = true;

                _thread = new Thread(AcceptLoop);
                _thread.IsBackground = true;
                _thread.Name = "FT-HotUpdateHttp";
                _thread.Start();

                Debug.Log("[HotUpdate] 本地热更服务器已启动：" + Url + " → " + _root);
                startedNow = true;
                return true;
            }
            catch (Exception e)
            {
                _running = false;
                _listener = null;
                _lastError = e.Message;
                error = e.Message;
                startedNow = false;
                return false;
            }
        }

        /// <summary>停止服务（幂等）。</summary>
        public static void Stop()
        {
            _running = false;
            try
            {
                if (_listener != null)
                {
                    _listener.Stop();
                }
            }
            catch (Exception)
            {
            }
            _listener = null;
            _thread = null;
        }

        // ------------------------------------------------------------------
        // 受理循环
        // ------------------------------------------------------------------

        private static void AcceptLoop()
        {
            while (_running)
            {
                TcpClient client = null;
                try
                {
                    client = _listener.AcceptTcpClient();
                }
                catch (Exception)
                {
                    // Stop() 会让 AcceptTcpClient 抛异常，属于正常退出路径
                    break;
                }

                try
                {
                    HandleClient(client);
                }
                catch (Exception e)
                {
                    _lastError = e.Message;
                }
                finally
                {
                    try { client.Close(); }
                    catch (Exception) { }
                }
            }
        }

        private static void HandleClient(TcpClient client)
        {
            client.ReceiveTimeout = 5000;
            NetworkStream stream = client.GetStream();

            string header = ReadHeader(stream);
            if (string.IsNullOrEmpty(header))
            {
                return;
            }

            string[] lines = header.Split(new[] { "\r\n" }, StringSplitOptions.None);
            string[] first = lines[0].Split(' ');
            if (first.Length < 3)
            {
                WriteText(stream, 400, "Bad Request", "请求行格式不对");
                return;
            }

            string method = first[0].ToUpperInvariant();
            if (method != "GET" && method != "HEAD")
            {
                WriteText(stream, 405, "Method Not Allowed", "只支持 GET / HEAD");
                return;
            }

            string rawPath = first[1];
            int q = rawPath.IndexOf('?');
            if (q >= 0)
            {
                rawPath = rawPath.Substring(0, q);
            }

            string decoded;
            try
            {
                decoded = Uri.UnescapeDataString(rawPath);
            }
            catch (Exception)
            {
                decoded = rawPath;
            }

            string relative = decoded.TrimStart('/').Replace('/', Path.DirectorySeparatorChar);
            string full = Path.GetFullPath(Path.Combine(_root, relative));

            // 目录穿越防护：解析后的绝对路径必须仍在根目录内
            string guard = _root.EndsWith(Path.DirectorySeparatorChar.ToString())
                ? _root
                : _root + Path.DirectorySeparatorChar;
            if (!full.StartsWith(guard, StringComparison.OrdinalIgnoreCase)
                && !string.Equals(full, _root, StringComparison.OrdinalIgnoreCase))
            {
                WriteText(stream, 403, "Forbidden", "越界路径");
                return;
            }

            if (Directory.Exists(full))
            {
                if (method == "HEAD")
                {
                    WriteHeader(stream, 200, "OK", "text/html; charset=utf-8", 0);
                }
                else
                {
                    WriteText(stream, 200, "OK", BuildListing(full, decoded));
                }
                Interlocked.Increment(ref _served);
                return;
            }

            if (!File.Exists(full))
            {
                WriteText(stream, 404, "Not Found", "文件不存在：" + decoded);
                Interlocked.Increment(ref _served);
                return;
            }

            long length;
            try
            {
                length = new FileInfo(full).Length;
            }
            catch (Exception e)
            {
                WriteText(stream, 500, "Internal Server Error", e.Message);
                return;
            }

            WriteHeader(stream, 200, "OK", ContentTypeOf(full), length);
            if (method == "GET")
            {
                using (FileStream fs = new FileStream(full, FileMode.Open, FileAccess.Read, FileShare.ReadWrite))
                {
                    byte[] buffer = new byte[64 * 1024];
                    long sent = 0;
                    while (sent < length)
                    {
                        int read = fs.Read(buffer, 0, buffer.Length);
                        if (read <= 0)
                        {
                            break;
                        }
                        stream.Write(buffer, 0, read);
                        sent += read;
                    }
                }
            }
            Interlocked.Increment(ref _served);
        }

        /// <summary>读到空行为止（上限 16KB，防恶意长头把线程拖死）。</summary>
        private static string ReadHeader(NetworkStream stream)
        {
            StringBuilder sb = new StringBuilder();
            byte[] one = new byte[1];
            int matched = 0;
            while (sb.Length < 16 * 1024)
            {
                int read;
                try
                {
                    read = stream.Read(one, 0, 1);
                }
                catch (Exception)
                {
                    return null;
                }
                if (read <= 0)
                {
                    break;
                }
                char c = (char)one[0];
                sb.Append(c);
                if ((matched == 0 || matched == 2) && c == '\r') matched++;
                else if ((matched == 1 || matched == 3) && c == '\n') matched++;
                else matched = 0;
                if (matched == 4)
                {
                    break;
                }
            }
            return sb.ToString();
        }

        private static void WriteHeader(NetworkStream stream, int code, string reason, string contentType, long length)
        {
            string head = "HTTP/1.1 " + code + " " + reason + "\r\n"
                + "Content-Type: " + contentType + "\r\n"
                + "Content-Length: " + length + "\r\n"
                + "Cache-Control: no-store\r\n"
                + "Connection: close\r\n\r\n";
            byte[] bytes = Encoding.ASCII.GetBytes(head);
            stream.Write(bytes, 0, bytes.Length);
        }

        private static void WriteText(NetworkStream stream, int code, string reason, string body)
        {
            byte[] bytes = Encoding.UTF8.GetBytes(body ?? "");
            WriteHeader(stream, code, reason, "text/plain; charset=utf-8", bytes.Length);
            stream.Write(bytes, 0, bytes.Length);
        }

        private static string ContentTypeOf(string path)
        {
            string ext = Path.GetExtension(path).ToLowerInvariant();
            if (ext == ".txt" || ext == ".version" || ext == ".json" || ext == ".hash")
            {
                return "text/plain; charset=utf-8";
            }
            return "application/octet-stream";
        }

        /// <summary>目录索引（浏览器打开根地址时能看到版本文件与文件数，便于人工确认）。</summary>
        private static string BuildListing(string dir, string urlPath)
        {
            string[] files;
            string[] dirs;
            try
            {
                files = Directory.GetFiles(dir);
                dirs = Directory.GetDirectories(dir);
            }
            catch (Exception e)
            {
                return "读取目录失败：" + e.Message;
            }

            StringBuilder sb = new StringBuilder();
            sb.Append("<html><meta charset=\"utf-8\"><body style=\"font-family:Consolas,monospace\">");
            sb.Append("<h3>FT HotUpdate · ").Append(WebUtility.HtmlEncode(urlPath)).Append("</h3>");
            sb.Append("<p>root: ").Append(WebUtility.HtmlEncode(dir)).Append("</p><ul>");
            if (!string.Equals(Path.GetFullPath(dir), _root, StringComparison.OrdinalIgnoreCase))
            {
                sb.Append("<li><a href=\"../\">../</a></li>");
            }
            for (int i = 0; i < dirs.Length; i++)
            {
                string name = Path.GetFileName(dirs[i]);
                sb.Append("<li><a href=\"").Append(Uri.EscapeDataString(name)).Append("/\">")
                  .Append(WebUtility.HtmlEncode(name)).Append("/</a></li>");
            }
            for (int i = 0; i < files.Length; i++)
            {
                string name = Path.GetFileName(files[i]);
                long size = 0;
                try { size = new FileInfo(files[i]).Length; }
                catch (Exception) { }
                sb.Append("<li><a href=\"").Append(Uri.EscapeDataString(name)).Append("\">")
                  .Append(WebUtility.HtmlEncode(name)).Append("</a> · ")
                  .Append(HotUpdateFileUtil.FormatSize(size)).Append("</li>");
            }
            sb.Append("</ul></body></html>");
            return sb.ToString();
        }
    }
}
