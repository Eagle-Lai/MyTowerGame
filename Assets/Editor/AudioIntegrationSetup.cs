using System;
using System.Linq;
using System.Reflection;
using UnityEditor;
using UnityEngine;
using UnityEngine.Audio;

namespace FTProject.EditorTools
{
    /// <summary>Scoped, repeatable setup. Does not build bundles, touch balancing, or enter Play Mode.</summary>
    public static class AudioIntegrationSetup
    {
        [MenuItem("Tools/塔防/声音/生成音频配置与设置控件", false, 390)]
        public static void Configure()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode) throw new InvalidOperationException("Audio setup requires Edit Mode.");
            if (!AssetDatabase.IsValidFolder(AudioResourceMap.RuntimePath)) AssetDatabase.CreateFolder("Assets/Audio", "Runtime");
            string path = AudioResourceMap.RuntimePath + "/GameAudioCatalog.asset";
            var catalog = AssetDatabase.LoadAssetAtPath<AudioCatalog>(path);
            if (catalog == null) { catalog = ScriptableObject.CreateInstance<AudioCatalog>(); AssetDatabase.CreateAsset(catalog, path); }
            catalog.cues = AudioResourceMap.Assets.GroupBy(a => a.cue).Select(group => Policy(group.Key, group.Select(a => a.key).ToArray())).ToArray();
            EditorUtility.SetDirty(catalog);
            CreateMixer();
            TacticalForgePrefabBuilder.UpdateExisting("Assets/Prefabs/UI/SettingView.prefab");
#if USE_YOOASSET
            var wizard = ScriptableObject.CreateInstance<FTYooAssetSetupWizard>();
            try { typeof(FTYooAssetSetupWizard).GetMethod("GenerateCollectorSettings", BindingFlags.Instance | BindingFlags.NonPublic).Invoke(wizard, null); }
            finally { UnityEngine.Object.DestroyImmediate(wizard); }
#endif
            AssetDatabase.SaveAssets();
            Debug.Log("[Audio] Catalog, mixer, settings prefab and collectors configured. WAV import uses separate scoped command.");
        }

        private static AudioCueDefinition Policy(SoundCue cue, string[] names)
        {
            var d = new AudioCueDefinition { cue = cue, logicalNames = names, gain = .5f, priority = 75, cooldown = .08f, maxConcurrent = 3 };
            d.gameplay = (cue >= SoundCue.TowerSelect && cue <= SoundCue.HeavyDeath) || (cue >= SoundCue.RoundStart && cue <= SoundCue.LowHp);
            if (cue <= SoundCue.Rating) { d.gain = cue <= SoundCue.Pressure ? .55f : .7f; d.priority = 100; d.maxConcurrent = 1; d.cooldown = 0; }
            if (cue == SoundCue.NormalFire) { d.gain = .27f; d.priority = 45; d.cooldown = .05f; d.maxConcurrent = 4; }
            if (cue == SoundCue.NormalHit) { d.gain = .22f; d.priority = 30; d.cooldown = .08f; }
            if (cue == SoundCue.BlastFire || cue == SoundCue.BlastHit) { d.gain = .38f; d.priority = 55; d.cooldown = .1f; }
            if (cue == SoundCue.FrostPulse || cue == SoundCue.FrostLoop) { d.gain = cue == SoundCue.FrostLoop ? .18f : .25f; d.priority = 20; d.cooldown = .3f; d.maxConcurrent = 2; }
            if (cue >= SoundCue.LightHit && cue <= SoundCue.HeavyDeath)
            {
                bool death = ((int)cue - (int)SoundCue.LightHit) % 2 == 1;
                d.gain = death ? .36f : .22f; d.priority = death ? 60 : 25;
                d.cooldown = death ? .08f : .12f; d.maxConcurrent = death ? 3 : 2;
            }
            if (cue == SoundCue.EnemyLeak || cue == SoundCue.LowHp) { d.priority = 95; d.cooldown = .2f; d.maxConcurrent = 1; d.gain = .6f; }
            return d;
        }

        private static void CreateMixer()
        {
            string path = AudioResourceMap.RuntimePath + "/GameAudioMixer.mixer";
            var existing = AssetDatabase.LoadAssetAtPath<AudioMixer>(path);
            var type = typeof(UnityEditor.Editor).Assembly.GetType("UnityEditor.Audio.AudioMixerController", true);
            const BindingFlags flags = BindingFlags.Public | BindingFlags.NonPublic;
            var create = type.GetMethod("CreateMixerControllerAtPath", flags | BindingFlags.Static, null, new[] { typeof(string) }, null);
            var mixer = existing != null ? (object)existing : create.Invoke(null, new object[] { path });
            var master = type.GetProperty("masterGroup", flags | BindingFlags.Instance).GetValue(mixer);
            var makeGroup = type.GetMethod("CreateNewGroup", flags | BindingFlags.Instance, null, new[] { typeof(string), typeof(bool) }, null);
            var addChild = type.GetMethod("AddChildToParent", flags | BindingFlags.Instance);
            foreach (string name in new[] { "Music", "SFX" })
            {
                if (((AudioMixer)mixer).FindMatchingGroups(name).Length > 0) continue;
                var group = makeGroup.Invoke(mixer, new object[] { name, false });
                addChild.Invoke(mixer, new[] { group, master });
            }
            EditorUtility.SetDirty((UnityEngine.Object)mixer);
        }

        [MenuItem("Tools/塔防/声音/应用 93 个 WAV 导入策略", false, 391)]
        public static void ImportAudio()
        {
            foreach (var entry in AudioResourceMap.Assets)
            {
                var importer = AssetImporter.GetAtPath(entry.path) as AudioImporter;
                if (importer == null) throw new InvalidOperationException("Missing WAV importer: " + entry.path);
                bool bgm = entry.cue <= SoundCue.Pressure, stinger = entry.cue >= SoundCue.Victory && entry.cue <= SoundCue.Rating;
                importer.forceToMono = !bgm && !stinger;
                importer.loadInBackground = bgm;
                var settings = importer.defaultSampleSettings;
                settings.preloadAudioData = !bgm;
                settings.loadType = bgm ? AudioClipLoadType.Streaming : AudioClipLoadType.DecompressOnLoad;
                settings.compressionFormat = bgm ? AudioCompressionFormat.Vorbis : AudioCompressionFormat.PCM;
                settings.sampleRateSetting = AudioSampleRateSetting.PreserveSampleRate;
                settings.quality = bgm ? .75f : 1;
                importer.defaultSampleSettings = settings;
                importer.SetOverrideSampleSettings("Android", settings);
                var serialized = new SerializedObject(importer); var normalize = serialized.FindProperty("m_Normalize");
                if (normalize != null) { normalize.boolValue = false; serialized.ApplyModifiedPropertiesWithoutUndo(); }
                importer.SaveAndReimport();
            }
            Debug.Log("[Audio] Exactly 93 WAV importers updated; source WAVs and GUIDs preserved.");
        }

        public static string Validate()
        {
            foreach (var entry in AudioResourceMap.Assets)
            {
                ResAddress address;
                if (!ResTable.TryGet(entry.key, out address) || address.EditorPath != entry.path || AssetDatabase.LoadAssetAtPath<AudioClip>(entry.path) == null)
                    throw new InvalidOperationException("Audio registration failed: " + entry.key);
            }
            var catalog = AssetDatabase.LoadAssetAtPath<AudioCatalog>(AudioResourceMap.RuntimePath + "/GameAudioCatalog.asset");
            if (catalog == null || catalog.cues.Sum(c => c.logicalNames.Length) != 93) throw new InvalidOperationException("Catalog coverage failed");
            var mixer = AssetDatabase.LoadAssetAtPath<AudioMixer>(AudioResourceMap.RuntimePath + "/GameAudioMixer.mixer");
            if (mixer == null || mixer.FindMatchingGroups("Music").Length != 1 || mixer.FindMatchingGroups("SFX").Length != 1) throw new InvalidOperationException("Mixer groups failed");
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>("Assets/Prefabs/UI/SettingView.prefab");
            if (prefab.GetComponentsInChildren<UnityEngine.UI.Slider>(true).Length != 3 || prefab.GetComponentsInChildren<UnityEngine.UI.Toggle>(true).Count(t => t.name == "AudioMuteToggle") != 1)
                throw new InvalidOperationException("Settings controls failed");
            return "93 WAVs / " + catalog.cues.Length + " cues / 27 maximum service voices / mixer groups / 3 sliders + mute: configured";
        }
    }
}
