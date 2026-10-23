using System;
using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Text;
using Unity.Collections;
using UnityEditor;
using UnityEngine;
using Debug = UnityEngine.Debug;

namespace FTProject.EditorTools
{
    /// <summary>
    /// Silent, unattended frame capture for the fixed-step balance replay.
    /// Raw RGBA frames are streamed into an ffmpeg child process over stdin, so no
    /// intermediate PNG sequence ever touches disk. No dialogs, no focus stealing,
    /// no new windows: progress is written to a log file next to the mp4.
    /// </summary>
    [InitializeOnLoad]
    public static class BalanceVideoRecorder
    {
        private static readonly BindingFlags Flags =
            BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance;

        private static Process _ffmpeg;
        private static Stream _stdin;
        private static string _output;
        private static string _logPath;
        private static int _width, _height, _fps, _frames, _sizeWait;
        private static bool _ready, _formatChecked;
        private static byte[] _buffer;
        private static EditorWindow _view;
        private static object _group;
        private static PropertyInfo _selection;
        private static int _oldIndex = -1, _originalCount = -1, _addedIndex = -1;
        private static readonly StringBuilder Stderr = new StringBuilder();

        public static bool Running { get; private set; }
        public static int FrameCount { get { return _frames; } }
        public static string LastError { get; private set; }

        /// <summary>True once the GameView actually reports the requested capture size.</summary>
        public static bool Ready { get { return Running && _ready; } }

        // Diagnostics only; the replay never waits on this.
        static BalanceVideoRecorder() { }

        public static void Begin(string outputMp4, int width, int height, int fps, string ffmpegPath)
        {
            if (Running) throw new InvalidOperationException("BalanceVideoRecorder is already running.");
            if (!EditorApplication.isPlaying || !SaveManager.IsTestStorage)
                throw new InvalidOperationException("Video capture requires an isolated PlayMode scene.");
            if (string.IsNullOrEmpty(ffmpegPath) || !File.Exists(ffmpegPath))
                throw new FileNotFoundException("ffmpeg executable not found: " + ffmpegPath);
            if (width < 16 || height < 16) throw new ArgumentOutOfRangeException("width");
            if (fps < 1 || fps > 60) throw new ArgumentOutOfRangeException("fps");

            LastError = null; _frames = 0; _sizeWait = 0; _ready = false;
            _formatChecked = false; _buffer = null;
            Stderr.Length = 0;
            _width = width; _height = height; _fps = fps;
            _output = Path.GetFullPath(outputMp4);
            Directory.CreateDirectory(Path.GetDirectoryName(_output));
            _logPath = Path.ChangeExtension(_output, ".log.txt");
            if (File.Exists(_output)) File.Delete(_output);

            ApplyGameViewSize(width, height);

            string arguments = string.Format(
                "-y -hide_banner -loglevel warning " +
                "-f rawvideo -pixel_format rgba -video_size {0}x{1} -framerate {2} -i - " +
                "-vf vflip -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p " +
                "-r 30 -movflags +faststart \"{3}\"",
                width, height, fps, _output);

            var info = new ProcessStartInfo
            {
                FileName = ffmpegPath,
                Arguments = arguments,
                UseShellExecute = false,
                CreateNoWindow = true,
                RedirectStandardInput = true,
                RedirectStandardError = true,
                RedirectStandardOutput = false,
                WorkingDirectory = Path.GetDirectoryName(_output)
            };
            _ffmpeg = Process.Start(info);
            if (_ffmpeg == null) throw new InvalidOperationException("ffmpeg process failed to start.");
            _stdin = _ffmpeg.StandardInput.BaseStream;
            _ffmpeg.ErrorDataReceived += delegate(object sender, DataReceivedEventArgs e)
            {
                if (string.IsNullOrEmpty(e.Data)) return;
                if (Stderr.Length < 8192) Stderr.AppendLine(e.Data);
            };
            _ffmpeg.BeginErrorReadLine();

            Running = true;
            Log("begin " + _output + " " + width + "x" + height + "@" + fps + "ffmpeg=" + ffmpegPath);
        }

        /// <summary>
        /// Captures exactly one frame. The replay steps one fixed tick before calling this,
        /// so video time always advances by 1/fps per frame regardless of editor frame rate.
        /// </summary>
        public static void PushFrame()
        {
            if (!Running) return;
            try
            {
                if (Screen.width != _width || Screen.height != _height)
                {
                    if (++_sizeWait > 900)
                        throw new InvalidOperationException(
                            "GameView did not reach " + _width + "x" + _height + " (actual " + Screen.width + "x" + Screen.height + ").");
                    return;
                }
                _sizeWait = 0;
                if (!_ready) { _ready = true; Log("gameview ready " + _width + "x" + _height); }

                Texture2D frame = ScreenCapture.CaptureScreenshotAsTexture();
                if (frame == null) throw new InvalidOperationException("ScreenCapture returned no texture.");
                try
                {
                    if (frame.width != _width || frame.height != _height)
                        throw new InvalidDataException("Captured frame is " + frame.width + "x" + frame.height +
                                                       ", expected " + _width + "_" + _height + ".");
                    if (!_formatChecked)
                    {
                        _formatChecked = true;
                        Log("frame format=" + frame.format + " size=" + frame.width + "x" + frame.height);
                        if (frame.format != TextureFormat.RGBA32 && frame.format != TextureFormat.ARGB32)
                            throw new InvalidDataException("Unexpected capture format " + frame.format +
                                                           "; expecting RGBA32.");
                    }
                    int expected = _width * _height * 4;
                    NativeArray<byte> raw = frame.GetRawTextureData<byte>();
                    if (raw.Length < expected)
                        throw new InvalidDataException("Frame payload " + raw.Length + " < " + expected + ".");
                    if (_buffer == null || _buffer.Length != expected) _buffer = new byte[expected];
                    raw.CopyTo(_buffer);
                    _stdin.Write(_buffer, 0, expected);
                    _frames++;
                }
                finally { UnityEngine.Object.DestroyImmediate(frame); }
            }
            catch (Exception error)
            {
                LastError = error.Message;
                Log("frame error: " + error);
                Abort();
            }
        }

        public static bool End()
        {
            if (!Running) return false;
            bool ok = false;
            try
            {
                try { _stdin.Flush(); _stdin.Close(); } catch { }
                _stdin = null;
                if (!_ffmpeg.WaitForExit(180000))
                {
                    try { _ffmpeg.Kill(); } catch { }
                    LastError = "ffmpeg did not exit within 180s.";
                }
                else if (_ffmpeg.ExitCode != 0)
                    LastError = "ffmpeg exit " + _ffmpeg.ExitCode + ": " + Stderr.ToString().Trim();
                else if (!File.Exists(_output) || new FileInfo(_output).Length < 4096)
                    LastError = "mp4 missing or empty.";
                else
                    ok = true;
            }
            catch (Exception error) { LastError = error.Message; }
            finally { Cleanup(); Log("end ok=" + ok + " frames=" + _frames + (LastError == null ? "" : " error=" + LastError)); }
            return ok;
        }

        public static void Abort()
        {
            if (!Running) return;
            try { if (_ffmpeg != null && !_ffmpeg.HasExited) { try { _stdin.Close(); } catch { } _ffmpeg.Kill(); } }
            catch { }
            finally
            {
                Cleanup();
                try { if (File.Exists(_output)) File.Delete(_output); } catch { }
                Log("abort frames=" + _frames + (LastError == null ? "" : " error=" + LastError));
            }
        }

        private static void Cleanup()
        {
            Running = false; _ready = false; _stdin = null;
            try { if (_ffmpeg != null) _ffmpeg.Dispose(); } catch { }
            _ffmpeg = null;
            RestoreGameViewSize();
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
            _originalCount = (int)_group.GetType().GetMethod("GetTotalCount").Invoke(_group, null);

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
                if (!string.IsNullOrEmpty(_logPath))
                    File.AppendAllText(_logPath, line, Encoding.UTF8);
            }
            catch { }
            Debug.Log("[BalanceVideo] " + message);
        }
    }
}
