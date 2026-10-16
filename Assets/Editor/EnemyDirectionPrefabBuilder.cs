using System;
using System.Collections.Generic;
using System.IO;
using FTProject;
using UnityEditor;
using UnityEngine;
using Object = UnityEngine.Object;

namespace FTProject.EditorTools
{
    /// <summary>Single-prefab, repeatable setup. It refuses to install incomplete artwork.</summary>
    public static class EnemyDirectionPrefabBuilder
    {
        public const string ArtDir = "Assets/_UIAssets/Monsters/Birds/AdvancedHen/Directions";
        public const string ProfilePath = ArtDir + "/AdvancedHen_Directions.asset";
        public const string PrefabPath = "Assets/Prefabs/Enemy/Enemy_AdvancedHen.prefab";
        private static readonly string[] PartNames = { "HeadNormal", "HeadAngry", "HeadDead", "Body", "Wing", "Leg" };

        [MenuItem("Tools/塔防/敌人方向示例/1. 接入 AdvancedHen 上下方向")]
        public static void BuildAdvancedHen()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode || EditorApplication.isCompiling)
                throw new InvalidOperationException("请在非 Play、编译完成后接入方向资源。");
            // Validate all inputs before importing or editing a prefab.
            foreach (string direction in new[] { "Up", "Down" })
                foreach (string part in PartNames)
                    if (!File.Exists(ArtDir + "/" + direction + "/" + part + ".png"))
                        throw new FileNotFoundException("真实方向美术尚未齐全，未修改预制体：" + direction + "/" + part);

            Directory.CreateDirectory(ArtDir + "/Animations");
            AssetDatabase.Refresh();
            var profile = AssetDatabase.LoadAssetAtPath<EnemyDirectionalProfile>(ProfilePath);
            if (!profile)
            {
                profile = ScriptableObject.CreateInstance<EnemyDirectionalProfile>();
                AssetDatabase.CreateAsset(profile, ProfilePath);
            }
            profile.Up = ImportParts("Up");
            profile.Down = ImportParts("Down");
            profile.Controller = BuildController();
            EditorUtility.SetDirty(profile);
            AssetDatabase.SaveAssets();

            var root = PrefabUtility.LoadPrefabContents(PrefabPath);
            try
            {
                Apply(root, profile);
                PrefabUtility.SaveAsPrefabAsset(root, PrefabPath);
            }
            finally { PrefabUtility.UnloadPrefabContents(root); }
            Debug.Log("[EnemyDirection] 仅 AdvancedHen 已接入；其他预制体未处理。");
        }

        /// <summary>Called by the existing generator to reapply a previously installed profile.</summary>
        public static bool ApplyIfConfigured(GameObject root, string originalAtlasPath)
        {
            if (string.IsNullOrEmpty(originalAtlasPath)) return false;
            string folder = Path.GetDirectoryName(originalAtlasPath).Replace('\\', '/');
            string name = Path.GetFileNameWithoutExtension(originalAtlasPath);
            var profile = AssetDatabase.LoadAssetAtPath<EnemyDirectionalProfile>(folder + "/Directions/" + name + "_Directions.asset");
            if (!profile || !profile.IsComplete) return false;
            Apply(root, profile);
            return true;
        }

        private static EnemyDirectionalProfile.Parts ImportParts(string direction)
        {
            var sprites = new Sprite[PartNames.Length];
            for (int i = 0; i < PartNames.Length; i++)
            {
                string path = ArtDir + "/" + direction + "/" + PartNames[i] + ".png";
                AssetDatabase.ImportAsset(path, ImportAssetOptions.ForceSynchronousImport);
                var importer = (TextureImporter)AssetImporter.GetAtPath(path);
                importer.textureType = TextureImporterType.Sprite;
                importer.spriteImportMode = SpriteImportMode.Single;
                importer.spritePixelsPerUnit = 100;
                importer.spritePivot = new Vector2(0.5f, 0.5f);
                var settings = new TextureImporterSettings();
                importer.ReadTextureSettings(settings);
                settings.spriteAlignment = (int)SpriteAlignment.Center;
                settings.spriteMeshType = SpriteMeshType.FullRect;
                importer.SetTextureSettings(settings);
                importer.alphaIsTransparency = true;
                importer.mipmapEnabled = false;
                importer.filterMode = FilterMode.Bilinear;
                importer.wrapMode = TextureWrapMode.Clamp;
                importer.textureCompression = TextureImporterCompression.Uncompressed;
                importer.SaveAndReimport();
                sprites[i] = AssetDatabase.LoadAssetAtPath<Sprite>(path);
            }
            return new EnemyDirectionalProfile.Parts
            {
                NormalHead = sprites[0], AngryHead = sprites[1], DeadHead = sprites[2],
                Body = sprites[3], Wing = sprites[4], Leg = sprites[5]
            };
        }

        private static RuntimeAnimatorController BuildController()
        {
            var source = AssetDatabase.LoadAssetAtPath<RuntimeAnimatorController>(
                "Assets/_UIAssets/Monsters/_Common/Animations/Rooster/Controller.controller");
            if (!source) throw new InvalidOperationException("Rooster 控制器不存在。");
            string path = ArtDir + "/Animations/AdvancedHen_Directions.overrideController";
            var controller = AssetDatabase.LoadAssetAtPath<AnimatorOverrideController>(path);
            if (!controller)
            {
                controller = new AnimatorOverrideController(source);
                AssetDatabase.CreateAsset(controller, path);
            }
            controller.runtimeAnimatorController = source;
            var overrides = new List<KeyValuePair<AnimationClip, AnimationClip>>();
            var seen = new HashSet<AnimationClip>();
            foreach (AnimationClip clip in source.animationClips)
            {
                if (!clip || !seen.Add(clip)) continue;
                string clipPath = ArtDir + "/Animations/" + clip.name + "_Directions.anim";
                AnimationClip copy = Object.Instantiate(clip);
                copy.name = clip.name + "_Directions";
                AddVerticalCurves(copy, clip.name);
                var existing = AssetDatabase.LoadAssetAtPath<AnimationClip>(clipPath);
                if (existing)
                {
                    EditorUtility.CopySerialized(copy, existing);
                    Object.DestroyImmediate(copy);
                    copy = existing;
                }
                else AssetDatabase.CreateAsset(copy, clipPath);
                overrides.Add(new KeyValuePair<AnimationClip, AnimationClip>(clip, copy));
            }
            controller.ApplyOverrides(overrides);
            EditorUtility.SetDirty(controller);
            return controller;
        }

        private static void Curve(AnimationClip clip, string node, string property, float[] values)
        {
            var keys = new Keyframe[values.Length];
            float length = Mathf.Max(0.01f, clip.length);
            for (int i = 0; i < keys.Length; i++) keys[i] = new Keyframe(length * i / (keys.Length - 1), values[i]);
            var curve = new AnimationCurve(keys);
            for (int i = 0; i < keys.Length; i++)
            {
                AnimationUtility.SetKeyLeftTangentMode(curve, i, AnimationUtility.TangentMode.ClampedAuto);
                AnimationUtility.SetKeyRightTangentMode(curve, i, AnimationUtility.TangentMode.ClampedAuto);
            }
            AnimationUtility.SetEditorCurve(clip, EditorCurveBinding.FloatCurve("DirectionVisual/Motion" + node,
                typeof(Transform), property), curve);
        }

        private static void AddVerticalCurves(AnimationClip clip, string state)
        {
            bool walking = state.IndexOf("Walk", StringComparison.OrdinalIgnoreCase) >= 0;
            bool attack = state.IndexOf("Attack", StringComparison.OrdinalIgnoreCase) >= 0;
            bool death = state.IndexOf("Death", StringComparison.OrdinalIgnoreCase) >= 0;
            Curve(clip, "", "localEulerAnglesRaw.z", death ? new[] { 0f, -12f, -65f, -80f, -80f } : new[] { 0f, 0f });
            Curve(clip, "", "m_LocalPosition.y", new[] { 0f, 0f });
            Curve(clip, "/Torso", "m_LocalPosition.y", walking
                ? new[] { 1.6f, 1.65f, 1.6f, 1.65f, 1.6f } : new[] { 1.6f, 1.62f, 1.6f });
            Curve(clip, "/Head", "m_LocalPosition.y", walking
                ? new[] { 2.65f, 2.71f, 2.65f, 2.71f, 2.65f } : new[] { 2.65f, 2.68f, 2.65f });
            Curve(clip, "/Head", "localEulerAnglesRaw.z", attack
                ? new[] { 0f, -6f, 12f, -5f, 0f } : new[] { 0f, 0f });
            Curve(clip, "/LegL", "m_LocalPosition.y", walking
                ? new[] { 0.4f, 0.57f, 0.4f, 0.4f, 0.4f } : new[] { 0.4f, 0.4f });
            Curve(clip, "/LegR", "m_LocalPosition.y", walking
                ? new[] { 0.4f, 0.4f, 0.4f, 0.57f, 0.4f } : new[] { 0.4f, 0.4f });
            Curve(clip, "/WingL", "localEulerAnglesRaw.z", attack
                ? new[] { 0f, -25f, -40f, -15f, 0f } : walking ? new[] { -3f, 3f, -3f, 3f, -3f } : new[] { 0f, 0f });
            Curve(clip, "/WingR", "localEulerAnglesRaw.z", attack
                ? new[] { 0f, 25f, 40f, 15f, 0f } : walking ? new[] { 3f, -3f, 3f, -3f, 3f } : new[] { 0f, 0f });
        }

        private static void Apply(GameObject root, EnemyDirectionalProfile profile)
        {
            if (!profile.IsComplete) throw new InvalidOperationException("方向配置未完成。");
            var old = root.transform.Find("DirectionVisual");
            if (old) Object.DestroyImmediate(old.gameObject);
            var side = new List<SpriteRenderer>();
            Transform hpBar = root.transform.Find("HpBar");
            foreach (var sr in root.GetComponentsInChildren<SpriteRenderer>(true))
            {
                if (sr.name == "Shadow" || (hpBar && sr.transform.IsChildOf(hpBar))) continue;
                side.Add(sr);
            }
            var visual = root.GetComponent<EnemyDirectionalVisual>();
            if (!visual) visual = root.AddComponent<EnemyDirectionalVisual>();
            visual.Profile = profile;
            visual.HorizontalRenderers = side.ToArray();
            Transform group = new GameObject("DirectionVisual").transform;
            group.SetParent(root.transform, false);
            Transform motion = new GameObject("Motion").transform;
            motion.SetParent(group, false);
            var parts = profile.Down;
            visual.Body = Part(motion, "Torso", parts.Body, new Vector2(0, 1.6f), 1.85f, 15);
            visual.Head = Part(motion, "Head", parts.NormalHead, new Vector2(0, 2.65f), 1.8f, 25);
            visual.WingL = Part(motion, "WingL", parts.Wing, new Vector2(-0.82f, 1.55f), 1.35f, 20);
            visual.WingR = Part(motion, "WingR", parts.Wing, new Vector2(0.82f, 1.55f), 1.35f, 20);
            visual.LegL = Part(motion, "LegL", parts.Leg, new Vector2(-0.42f, 0.4f), 0.8f, 5);
            visual.LegR = Part(motion, "LegR", parts.Leg, new Vector2(0.42f, 0.4f), 0.8f, 5);
            root.GetComponent<Animator>().runtimeAnimatorController = profile.Controller;
            visual.ResetForSpawn();
        }

        private static SpriteRenderer Part(Transform parent, string name, Sprite sprite, Vector2 position, float height, int order)
        {
            var node = new GameObject(name);
            node.transform.SetParent(parent, false);
            node.transform.localPosition = position;
            float scale = height / sprite.bounds.size.y;
            // Animate the pivot transform; place scale on a leaf so source curves cannot overwrite it.
            var leaf = new GameObject("Sprite");
            leaf.transform.SetParent(node.transform, false);
            leaf.transform.localScale = new Vector3(scale, scale, 1);
            var sr = leaf.AddComponent<SpriteRenderer>();
            sr.sprite = sprite;
            sr.sortingOrder = order;
            return sr;
        }
    }
}
