using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace FTProject.EditorTools
{
    /// <summary>Builds real BoardView cells in a preview scene; never calls InitLevel or touches saves.</summary>
    [InitializeOnLoad]
    public static class LevelPreviewCapture
    {
        public const int Width = 1024, Height = 576;
        private const string Request = "FT.LevelPreview.Request";
        private const string OldScene = "FT.LevelPreview.OldStartScene";
        private const string OldStorage = "FT.LevelPreview.OldStorage";
        private const string StorageKey = "FT.Balance.TestStorageContext";
        private const string PendingIds = "FT.LevelPreview.PendingIds";
        private static readonly List<int> Queue = new List<int>();
        private static readonly List<int> Completed = new List<int>();
        private static Scene _scene;
        private static Camera _camera;
        private static BoardView _board;
        private static int _index, _readyFrame;
        private static double _started;
        private static bool _running;
        private static string _ids;
        public static bool Running { get { return _running || SessionState.GetBool(Request, false); } }
        public static string LastResult { get; private set; }

        static LevelPreviewCapture()
        {
            EditorApplication.update += Update;
            EditorApplication.playModeStateChanged += OnPlayState;
            AssemblyReloadEvents.beforeAssemblyReload += BeforeReload;
            EditorApplication.quitting += BeforeReload;
        }

        [MenuItem("Tools/塔防/关卡地图预览/生成全部关卡预览")]
        public static void CaptureAll()
        {
            if (Running) throw new InvalidOperationException("A level preview capture is already running");
            if (EditorApplication.isCompiling || EditorApplication.isUpdating)
                throw new InvalidOperationException("Wait until compilation and asset import finish");
            if (EditorApplication.isPlaying) { Begin(ValidIds()); return; }
            if (EditorApplication.isPlayingOrWillChangePlaymode || EditorUtility.scriptCompilationFailed)
                throw new InvalidOperationException("An idle, compilable editor is required");
            var main = AssetDatabase.LoadAssetAtPath<SceneAsset>("Assets/Scenes/main.unity");
            if (main == null) throw new FileNotFoundException("Assets/Scenes/main.unity");
            SessionState.SetString(OldScene, EditorSceneManager.playModeStartScene != null
                ? AssetDatabase.GetAssetPath(EditorSceneManager.playModeStartScene) : "");
            SessionState.SetString(OldStorage, SessionState.GetString(StorageKey, ""));
            SessionState.SetString(StorageKey, "level-preview-" + Guid.NewGuid().ToString("N"));
            SessionState.SetBool(Request, true);
            SessionState.SetBool(Request + "Finishing", false);
            SessionState.SetString(Request + "Started", DateTime.UtcNow.Ticks.ToString());
            EditorSceneManager.playModeStartScene = main;
            EditorApplication.isPlaying = true;
        }

        [MenuItem("Tools/塔防/关卡地图预览/截取当前关卡预览")]
        public static void CaptureCurrent()
        {
            if (!EditorApplication.isPlaying || GameFlowManager.Instance == null || GameFlowManager.Instance.Level == null)
                throw new InvalidOperationException("Enter a level in Play Mode first");
            if (Running) throw new InvalidOperationException("A level preview capture is already running");
            // Read the current ID only. Rebuild a pristine board, ignoring towers/highlights/snapshots.
            Begin(new[] { GameFlowManager.Instance.Level.Id });
        }

        [MenuItem("Tools/塔防/关卡地图预览/取消生成")]
        public static void Cancel() { if (Running) Finish("Cancelled"); }

        private static int[] ValidIds()
        {
            if (!Configs.IsLoaded || Configs.LevelTable == null)
                throw new InvalidOperationException("Runtime configuration is not ready");
            return Configs.LevelTable.DataList.Where(level => level != null).Select(level => level.Id).Distinct().ToArray();
        }

        private static void Begin(int[] ids)
        {
            if (!EditorApplication.isPlaying || !Configs.IsLoaded || !ResLoader.Instance.IsReady)
                throw new InvalidOperationException("Booted Play Mode and runtime resources are required");
            if (ids.Length == 0) throw new InvalidOperationException("Campaign has no levels");
            Queue.Clear(); Queue.AddRange(ids); Completed.Clear();
            _ids = string.Join(", ", ValidIds().Select(id => id.ToString(System.Globalization.CultureInfo.InvariantCulture)));
            _index = 0; _started = EditorApplication.timeSinceStartup; _running = true; LastResult = null;
            Directory.CreateDirectory(LevelPreviewCatalog.Directory);
            Debug.Log("[LevelPreview] Capturing " + Queue.Count + " pristine runtime boards in isolated preview scenes.");
        }

        private static void Update()
        {
            try
            {
                if (!_running)
                {
                    if (SessionState.GetBool(Request + "Finishing", false)) return;
                    if (SessionState.GetBool(Request, false) && EditorApplication.isPlaying && Configs.IsLoaded && ResLoader.Instance.IsReady)
                        Begin(ValidIds());
                    else if (SessionState.GetBool(Request, false))
                    {
                        long ticks;
                        if (long.TryParse(SessionState.GetString(Request + "Started", ""), out ticks) && DateTime.UtcNow.Ticks - ticks > TimeSpan.FromSeconds(120).Ticks)
                            Finish("Runtime resources did not become ready within 120 seconds");
                    }
                    return;
                }
                if (!EditorApplication.isPlaying) { Finish("Play Mode ended"); return; }
                if (EditorApplication.timeSinceStartup - _started > 300) throw new TimeoutException("Level preview capture exceeded five minutes");
                int id = Queue[_index];
                if (EditorUtility.DisplayCancelableProgressBar("关卡地图预览",
                    "Level " + id + " (" + (_index + 1) + "/" + Queue.Count + ")", (float)_index / Queue.Count))
                { Finish("Cancelled"); return; }
                if (!_scene.IsValid()) { BuildStage(id); return; }
                if (Time.frameCount < _readyFrame) return;
                ValidateBoard(id);
                string path = LevelPreviewCatalog.AssetPath(id);
                SaveFrame(_camera, path);
                ImportSprite(path);
                Completed.Add(id); ClearStage();
                if (++_index == Queue.Count) Finish(null);
            }
            catch (Exception error) { Finish(error.ToString()); }
        }

        private static void BuildStage(int levelId)
        {
            LevelMapConfig map = Configs.GetLevelMapOfLevel(levelId);
            if (map == null || !string.IsNullOrEmpty(map.Validate()))
                throw new InvalidDataException("Invalid map for level " + levelId);
            _scene = EditorSceneManager.NewPreviewScene();
            var geometry = new GameObject("LevelPreview pristine geometry " + levelId);
            SceneManager.MoveGameObjectToScene(geometry, _scene);
            // An inactive owner never runs Awake, so BoardView.Instance remains the live gameplay board.
            var owner = new GameObject("Inactive BoardView builder"); owner.SetActive(false);
            SceneManager.MoveGameObjectToScene(owner, _scene);
            _board = owner.AddComponent<BoardView>();
            float size = Configs.Global.CellSize;
            Vector2 origin = new Vector2(-map.Cols * size * .5f, map.Rows * size * .5f);
            _board.Build(map, size, origin, geometry.transform);
            var cameraObject = new GameObject("LevelPreview camera");
            SceneManager.MoveGameObjectToScene(cameraObject, _scene);
            _camera = cameraObject.AddComponent<Camera>(); _camera.enabled = false;
            _camera.scene = _scene; _camera.orthographic = true;
            _camera.transform.position = new Vector3(0f, 0f, -10f);
            _camera.clearFlags = CameraClearFlags.SolidColor;
            _camera.backgroundColor = new Color(.055f, .085f, .13f, 1f);
            _camera.aspect = (float)Width / Height;
            _camera.orthographicSize = Mathf.Max(map.Rows * size * .5f, map.Cols * size * .5f / _camera.aspect) * 1.06f;
            _camera.nearClipPlane = .1f; _camera.farClipPlane = 30f;
            _camera.allowHDR = false; _camera.allowMSAA = false;
            _readyFrame = Time.frameCount + 2;
        }

        private static void ValidateBoard(int levelId)
        {
            var map = Configs.GetLevelMapOfLevel(levelId);
            if (_board == null || !_board.IsBuilt || _board.Rows != map.Rows || _board.Cols != map.Cols)
                throw new InvalidOperationException("Board dimensions do not match level " + levelId);
            for (int row = 0; row < map.Rows; row++)
                for (int col = 0; col < map.Cols; col++)
                {
                    var view = _board.GetView(row, col);
                    var renderer = view != null ? view.GetComponent<SpriteRenderer>() : null;
                    if (renderer == null || renderer.sprite == null || renderer.sprite.texture == null)
                        throw new InvalidOperationException("Missing cell sprite at level " + levelId + ": " + row + "," + col);
                }
            if (_board.SpawnCell == null || _board.EndCell == null) throw new InvalidOperationException("Missing spawn/end cell");
        }

        public static void SaveFrame(Camera camera, string path)
        {
            var previous = RenderTexture.active; var previousTarget = camera.targetTexture;
            RenderTexture target = RenderTexture.GetTemporary(Width, Height, 24, RenderTextureFormat.ARGB32);
            Texture2D image = null;
            try
            {
                camera.targetTexture = target; camera.Render(); RenderTexture.active = target;
                image = new Texture2D(Width, Height, TextureFormat.RGB24, false);
                image.ReadPixels(new Rect(0, 0, Width, Height), 0, 0); image.Apply();
                File.WriteAllBytes(path, image.EncodeToPNG());
            }
            finally
            {
                camera.targetTexture = previousTarget; RenderTexture.active = previous;
                RenderTexture.ReleaseTemporary(target);
                if (image != null) UnityEngine.Object.DestroyImmediate(image);
            }
        }

        private static void ImportSprite(string path)
        {
            AssetDatabase.ImportAsset(path, ImportAssetOptions.ForceSynchronousImport);
            var importer = AssetImporter.GetAtPath(path) as TextureImporter;
            if (importer == null) throw new InvalidDataException("PNG importer missing: " + path);
            importer.textureType = TextureImporterType.Sprite; importer.spriteImportMode = SpriteImportMode.Single;
            importer.mipmapEnabled = false; importer.isReadable = false; importer.alphaIsTransparency = false;
            importer.maxTextureSize = 1024; importer.textureCompression = TextureImporterCompression.Uncompressed;
            importer.npotScale = TextureImporterNPOTScale.None; importer.wrapMode = TextureWrapMode.Clamp;
            importer.filterMode = FilterMode.Bilinear; importer.SaveAndReimport();
        }

        private static void ClearStage()
        {
            _camera = null; _board = null;
            if (_scene.IsValid()) EditorSceneManager.ClosePreviewScene(_scene);
            _scene = default(Scene);
        }
        private static void Finish(string error)
        {
            ClearStage(); _running = false; EditorUtility.ClearProgressBar();
            LastResult = error == null ? "Captured " + Completed.Count + " level previews" : "Stopped after " + Completed.Count + " previews: " + error;
            if (error == null)
            {
                SessionState.SetString(PendingIds, _ids ?? "");
                Debug.Log("[LevelPreview] " + LastResult);
            }
            else Debug.LogWarning("[LevelPreview] " + LastResult);
            Directory.CreateDirectory("Temp/LevelPreviewAgent");
            File.WriteAllText("Temp/LevelPreviewAgent/capture-result.json", JsonUtility.ToJson(
                new CaptureReport { success = error == null, message = LastResult, levelIds = Completed.ToArray(), width = Width, height = Height }, true));
            if (SessionState.GetBool(Request, false))
            {
                SessionState.SetBool(Request + "Finishing", true);
                EditorApplication.isPlaying = false;
            }
        }
        [Serializable] private sealed class CaptureReport
        { public bool success; public string message; public int[] levelIds; public int width, height; }

        private static void OnPlayState(PlayModeStateChange state)
        {
            if (state == PlayModeStateChange.ExitingPlayMode)
            {
                if (_running) Finish("Play Mode ended");
                ClearStage(); EditorUtility.ClearProgressBar();
            }
            if (state != PlayModeStateChange.EnteredEditMode) return;
            if (SessionState.GetBool(Request, false))
            {
                string old = SessionState.GetString(OldScene, "");
                EditorSceneManager.playModeStartScene = string.IsNullOrEmpty(old) ? null : AssetDatabase.LoadAssetAtPath<SceneAsset>(old);
                string storage = SessionState.GetString(OldStorage, "");
                if (string.IsNullOrEmpty(storage)) SessionState.EraseString(StorageKey); else SessionState.SetString(StorageKey, storage);
                SessionState.EraseBool(Request); SessionState.EraseString(OldScene); SessionState.EraseString(OldStorage);
                SessionState.EraseString(Request + "Started");
                SessionState.EraseBool(Request + "Finishing");
            }
            SynchronizeCatalog();
        }
        private static void SynchronizeCatalog()
        {
            string ids = SessionState.GetString(PendingIds, "");
            if (string.IsNullOrEmpty(ids)) return;
            SessionState.EraseString(PendingIds);
            string path = "Assets/Scripts/Core/Res/LevelPreviewIds.cs";
            string source = "// Generated by LevelPreviewCapture from the valid campaign. Do not edit Assets/Gen.\r\nnamespace FTProject\r\n{\r\n    internal static class LevelPreviewIds\r\n    {\r\n        internal static readonly int[] All = { " + ids + " };\r\n    }\r\n}\r\n";
            if (!File.Exists(path) || File.ReadAllText(path) != source)
            { File.WriteAllText(path, source, new System.Text.UTF8Encoding(false)); AssetDatabase.ImportAsset(path); }
        }
        private static void BeforeReload()
        {
            if (_running) Finish("Capture interrupted by script reload or editor shutdown");
            ClearStage(); EditorUtility.ClearProgressBar(); _running = false;
        }
    }
}
