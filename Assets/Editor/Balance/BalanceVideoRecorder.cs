using System;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Reflection;
using System.Text;
using UnityEditor;
using UnityEngine;
using Debug = UnityEngine.Debug;

namespace FTProject.EditorTools
{
    /// <summary>
    /// Silent, unattended frame capture for the fixed-step balance replay.
    ///
    /// ScreenCapture.CaptureScreenshotAsTexture is not usable from EditorApplication.update
    /// (it returns no texture outside the end of a frame), so this recorder writes numbered
    /// PNG frames through the asynchronous ScreenCapture.CaptureScreenshot API and lets ffmpeg
    /// assemble them once the run finishes. Every frame is produced by a rendered GameView
    /// frame, so the HUD is included. No dialogs, no focus stealing, no extra windows.
    ///
    /// 【为什么倍速在录制端做，而且只出倍速片】
    ///   回放是固定步长手动时钟：<c>BalancePlayModeVerifier</c> 调
    ///   <c>GameClock.StepManualFrame(step / GameClock.Speed)</c>，而 <c>GameClock</c> 内部又乘回
    ///   <c>Speed</c>，两者精确抵消，每步推进恒为 step 秒。所以游戏内切 2x/3x 只会改一个显示值，
    ///   既不会加快录制、也不会让视频变快（这是刻意设计：保证 1x/2x/3x 对比时战斗结果完全一致）。
    ///   真正的倍速只能在输出端把同一批帧按更高帧率声明 —— 按 <c>fps × speed</c> 声明输入帧率即可，
    ///   时长精确为 1/speed。
    ///
    ///   2026-10-23 起按用户要求**只产出倍速成片**，不再另写 1x 母版：<c>outputMp4</c> 仍按母版命名
    ///   传入（帧目录与日志也用它，保持稳定），带倍速时实际文件加 <c>_Nx</c> 后缀。
    ///   L02 实测：17931 帧，1x 为 1075.858s、2x 为 537.931s，精确对半且一帧不丢。
    /// </summary>
    [InitializeOnLoad]
    public static class BalanceVideoRecorder
    {
        private const int MaxFrameWaitFrames = 900;

        private static readonly BindingFlags Flags =
            BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance;

        private static string _output;
        private static string _frameDir;
        private static string _logPath;
        private static string _ffmpegPath;
        private static int _width, _height, _frames, _stride, _strideCounter, _pendingFrame;
        private static double _actualFps, _speed;
        private static bool _sizeReady;
        private static int _sizeWait, _frameWait;
        private static EditorWindow _view;
        private static object _group;
        private static PropertyInfo _selection;
        private static int _oldIndex = -1, _addedIndex = -1;
        private static long _lastFrameBytes = -1;

        [System.Runtime.InteropServices.DllImport("user32.dll")]
        private static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
        [System.Runtime.InteropServices.DllImport("user32.dll")]
        private static extern bool IsIconic(IntPtr hWnd);

        public static bool Running { get; private set; }
        public static int FrameCount { get { return _frames; } }
        public static string LastError { get; private set; }

        /// <summary>True when the replay may advance one more fixed tick.</summary>
        public static bool Ready
        {
            get { return Running && _sizeReady && _pendingFrame <= 0; }
        }

        static BalanceVideoRecorder() { }

        public static void Begin(string outputMp4, int width, int height, double targetFps,
                                 double stepSeconds, string ffmpegPath, double videoSpeed = 1.0)
        {
            if (Running) throw new InvalidOperationException("BalanceVideoRecorder is already running.");
            if (!EditorApplication.isPlaying || !SaveManager.IsTestStorage)
                throw new InvalidOperationException("Video capture requires an isolated PlayMode scene.");
            if (string.IsNullOrEmpty(ffmpegPath) || !File.Exists(ffmpegPath))
                throw new FileNotFoundException("ffmpeg executable not found: " + ffmpegPath);
            if (width < 16 || height < 16) throw new ArgumentOutOfRangeException("width");
            if (targetFps < 1 || targetFps > 60) throw new ArgumentOutOfRangeException("targetFps");
            if (stepSeconds <= 0 || stepSeconds > 0.1) throw new ArgumentOutOfRangeException("stepSeconds");

            // Small simulation step (matching the stored evidence) + every Nth tick captured.
            _stride = Mathf.Max(1, (int)Math.Round(1.0 / (targetFps * stepSeconds)));
            _actualFps = 1.0 / (stepSeconds * _stride);
            _strideCounter = 0;

            LastError = null; _frames = 0; _pendingFrame = 0;
            _sizeReady = false; _sizeWait = 0; _frameWait = 0; _lastFrameBytes = -1;
            _width = width; _height = height;
            _ffmpegPath = ffmpegPath;
            string requested = Path.GetFullPath(outputMp4);
            _speed = videoSpeed > 0 ? videoSpeed : 1.0;
            // Only the requested cut is written; with a speed it gets the _Nx suffix and no 1x
            // master is produced (user decision 2026-10-23: only the fast cut is wanted).
            _output = DeliveredPath(requested, _speed);
            string dir = Path.GetDirectoryName(requested);
            Directory.CreateDirectory(dir);
            _frameDir = Path.Combine(dir, "_frames_" + Path.GetFileNameWithoutExtension(requested));
            Directory.CreateDirectory(_frameDir);
            foreach (string stale in Directory.GetFiles(_frameDir, "frame_*.png")) File.Delete(stale);
            _logPath = Path.ChangeExtension(requested, ".log.txt");
            if (File.Exists(_output)) File.Delete(_output);

            EnsureHostWindowVisible();
            ApplyGameViewSize(width, height);
            Running = true;
            Log("begin " + _output + " " + width + "x" + height + " step=" + stepSeconds.ToString("0.#####") +
                " stride=" + _stride + " fps=" + (_actualFps * _speed).ToString("0.###") +
                (Math.Abs(_speed - 1.0) < 0.001 ? "" : " speed=" + _speed.ToString("0.###")));
        }

        /// <summary>
        /// A minimized editor cannot render the GameView backbuffer, which would silently
        /// produce frames of the wrong size. Restore it without activating (no focus steal).
        /// </summary>
        private static void EnsureHostWindowVisible()
        {
            try
            {
                IntPtr handle = System.Diagnostics.Process.GetCurrentProcess().MainWindowHandle;
                if (handle == IntPtr.Zero) return;
                if (IsIconic(handle))
                {
                    ShowWindow(handle, 4); // SW_SHOWNOACTIVATE
                    Log("host window was minimized; restored without activation");
                }
            }
            catch (Exception error) { Log("ensure window visible failed: " + error.Message); }
        }

        /// <summary>
        /// Resolves pending work. Returns true once the recorder can accept another tick.
        /// The replay calls this while waiting, so readiness must never depend on PushFrame.
        /// </summary>
        public static void ProbeReady()
        {
            if (!Running) return;
            if (!_sizeReady)
            {
                if (Screen.width == _width && Screen.height == _height)
                {
                    _sizeReady = true; _sizeWait = 0;
                    Log("gameview ready " + _width + "x" + _height);
                }
                else if (++_sizeWait > 3000)
                    throw new InvalidOperationException("GameView did not reach " + _width + "x" + _height +
                                                        " (actual " + Screen.width + "x" + Screen.height + ").");
                return;
            }
            if (_pendingFrame <= 0) return;

            string path = FramePath(_pendingFrame);
            if (!File.Exists(path))
            {
                if (++_frameWait > MaxFrameWaitFrames)
                    throw new TimeoutException("Screenshot frame " + _pendingFrame + " never appeared: " + path);
                return;
            }
            var info = new FileInfo(path);
            if (info.Length < 1024) return;
            // Wait one poll for the size to settle so we never read a half-written PNG.
            if (_lastFrameBytes >= 0 && info.Length != _lastFrameBytes) { _lastFrameBytes = info.Length; return; }
            _lastFrameBytes = -1;

            int pngWidth, pngHeight;
            if (!TryReadPngSize(path, out pngWidth, out pngHeight)) return;
            if (pngWidth != _width || pngHeight != _height)
                throw new InvalidDataException("Captured frame is " + pngWidth + "x" + pngHeight + ", expected " +
                                               _width + "x" + _height +
                                               ". The editor GameView was probably minimized or too small.");
            _frames = _pendingFrame; _pendingFrame = 0; _frameWait = 0;
        }

        private static bool TryReadPngSize(string path, out int width, out int height)
        {
            width = height = 0;
            try
            {
                using (var stream = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite))
                {
                    if (stream.Length < 24) return false;
                    byte[] head = new byte[24];
                    int read = stream.Read(head, 0, 24);
                    if (read < 24) return false;
                    width = (head[16] << 24) | (head[17] << 16) | (head[18] << 8) | head[19];
                    height = (head[20] << 24) | (head[21] << 16) | (head[22] << 8) | head[23];
                    return width > 0 && height > 0;
                }
            }
            catch { return false; }
        }

        /// <summary>Requests one rendered frame; the replay blocks on Ready until it lands.</summary>
        public static void PushFrame()
        {
            if (!Running || !_sizeReady) return;
            if (++_strideCounter < _stride) return;
            _strideCounter = 0;
            if (_pendingFrame > 0) return;
            _pendingFrame = _frames + 1;
            ScreenCapture.CaptureScreenshot(FramePath(_pendingFrame));
        }

        public static bool End()
        {
            if (!Running) return false;
            bool ok = false;
            try
            {
                // Drain the last requested frame before encoding.
                double deadline = EditorApplication.timeSinceStartup + 30;
                while (_pendingFrame > 0 && EditorApplication.timeSinceStartup < deadline)
                {
                    try { ProbeReady(); } catch { break; }
                    if (_pendingFrame > 0) System.Threading.Thread.Sleep(20);
                }
                if (_frames <= 0) { LastError = "no frames were captured."; return false; }

                string pattern = Path.Combine(_frameDir, "frame_%06d.png");
                // The declared input rate already carries the playback speed: one frame per
                // (stepSeconds * stride / speed) of game time, so the cut is exactly 1/speed long.
                // L02 verified with ffprobe: 17931 frames, 537.931s at 2x (half of 1075.858s),
                // no frame dropped or duplicated.
                string arguments = string.Format(CultureInfo.InvariantCulture,
                    "-y -hide_banner -loglevel warning -framerate {0:0.####} -i \"{1}\" " +
                    "-c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p -movflags +faststart \"{2}\"",
                    _actualFps * _speed, pattern, _output);

                var info = new ProcessStartInfo
                {
                    FileName = _ffmpegPath, Arguments = arguments,
                    UseShellExecute = false, CreateNoWindow = true,
                    RedirectStandardError = true, RedirectStandardOutput = true,
                    WorkingDirectory = Path.GetDirectoryName(_output)
                };
                using (var ffmpeg = Process.Start(info))
                {
                    string stderr = ffmpeg.StandardError.ReadToEnd();
                    ffmpeg.WaitForExit();
                    if (ffmpeg.ExitCode != 0)
                        LastError = "ffmpeg exit " + ffmpeg.ExitCode + ": " + Trim(stderr);
                    else if (!File.Exists(_output) || new FileInfo(_output).Length < 4096)
                        LastError = "mp4 missing or empty.";
                    else ok = true;
                }
            }
            catch (Exception error) { LastError = error.Message; }
            finally
            {
                Running = false; _sizeReady = false; _pendingFrame = 0;
                RestoreGameViewSize();
                Log("end ok=" + ok + " frames=" + _frames + (LastError == null ? "" : " error=" + LastError));
                try { if (ok) CleanupFrames(); } catch { }
            }
            return ok;
        }

        public static void Abort()
        {
            if (!Running) return;
            Running = false; _sizeReady = false; _pendingFrame = 0;
            RestoreGameViewSize();
            Log("abort frames=" + _frames + (LastError == null ? "" : " error=" + LastError));
            try { if (File.Exists(_output)) File.Delete(_output); } catch { }
        }

        private static void CleanupFrames()
        {
            try
            {
                if (!Directory.Exists(_frameDir)) return;
                foreach (string file in Directory.GetFiles(_frameDir, "frame_*.png")) File.Delete(file);
                if (Directory.GetFileSystemEntries(_frameDir).Length == 0) Directory.Delete(_frameDir);
            }
            catch { }
        }

        private static string FramePath(int index)
        {
            return Path.Combine(_frameDir, "frame_" + index.ToString("D6") + ".png");
        }

        /// <summary>
        /// 母版名 + 倍速 → 实际交付文件名（speed=1 时原样返回）。
        /// "L02_完整通关.mp4" + 2.0 → "L02_完整通关_2x.mp4"（1.5 → "_1p5x"）。
        /// 批量驱动也用它判断某一关是否已经录过，实现断点续跑。
        /// </summary>
        public static string DeliveredPath(string requestedPath, double speed)
        {
            if (speed <= 0) speed = 1.0;
            if (Math.Abs(speed - 1.0) < 0.001) return requestedPath;
            string tag = Math.Abs(speed % 1.0) < 0.001
                ? ((int)Math.Round(speed)).ToString(CultureInfo.InvariantCulture)
                : speed.ToString("0.##", CultureInfo.InvariantCulture).Replace(".", "p");
            return Path.Combine(Path.GetDirectoryName(requestedPath),
                Path.GetFileNameWithoutExtension(requestedPath) + "_" + tag + "x" + Path.GetExtension(requestedPath));
        }

        private static string Trim(string text)
        {
            if (string.IsNullOrEmpty(text)) return "";
            text = text.Trim();
            return text.Length > 400 ? text.Substring(0, 400) : text;
        }

        // ---- GameView resolution: same reflection route used by BalanceGameplayCapture ----

        private static void ApplyGameViewSize(int width, int height)
        {
            var assembly = typeof(Editor).Assembly;
            var viewType = assembly.GetType("UnityEditor.GameView");
            _view = EditorWindow.GetWindow(viewType);
            _selection = viewType.GetProperty("selectedSizeIndex", Flags);
            _oldIndex = (int)_selection.GetValue(_view, null);

            var sizesType = assembly.GetType("UnityEditor.GameViewSizes");
            var sizes = sizesType.BaseType.GetProperty("instance", BindingFlags.Public | BindingFlags.Static)
                .GetValue(null, null);
            _group = sizesType.GetProperty("currentGroup", Flags).GetValue(sizes, null);

            var sizeType = assembly.GetType("UnityEditor.GameViewSize");
            var mode = Enum.Parse(assembly.GetType("UnityEditor.GameViewSizeType"), "FixedResolution");
            var size = Activator.CreateInstance(sizeType,
                new object[] { mode, width, height, "Balance video " + width + "x" + height });
            int index = (int)_group.GetType().GetMethod("GetTotalCount").Invoke(_group, null);
            _group.GetType().GetMethod("AddCustomSize").Invoke(_group, new[] { size });
            _addedIndex = index;
            _selection.SetValue(_view, index, null);
            _view.Repaint();
        }

        private static void RestoreGameViewSize()
        {
            try
            {
                if (_view == null || _selection == null) return;
                if (_oldIndex >= 0) _selection.SetValue(_view, _oldIndex, null);
                if (_addedIndex >= 0 && _group != null)
                    _group.GetType().GetMethod("RemoveCustomSize").Invoke(_group, new object[] { _addedIndex });
                _view.Repaint();
            }
            catch (Exception error) { Log("restore gameview failed: " + error.Message); }
            finally { _view = null; _group = null; _selection = null; _addedIndex = -1; _oldIndex = -1; }
        }

        private static void Log(string message)
        {
            try
            {
                string line = DateTime.Now.ToString("HH:mm:ss") + " " + message + Environment.NewLine;
                if (!string.IsNullOrEmpty(_logPath)) File.AppendAllText(_logPath, line, Encoding.UTF8);
            }
            catch { }
            Debug.Log("[BalanceVideo] " + message);
        }
    }
}
