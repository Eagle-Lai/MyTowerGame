using System;
using System.Collections.Generic;
using System.IO;
using FTProject;
using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;
using Object = UnityEngine.Object;

namespace FTProject.EditorTools
{
    /// <summary>Per-monster wiring for the vertical (up/down) view.</summary>
    public sealed class EnemyDirectionSpec
    {
        public string Name;
        public string ArtDir;          // .../Directions
        public string PrefabPath;      // Assets/Prefabs/Enemy/Enemy_X.prefab
        public string ControllerSource; // family AnimatorController whose clips drive the rig
        public bool UseRealController;  // true: copy the family controller and add WalkUp/WalkDown states (code controls Dir); false: AnimatorOverrideController (AdvancedHen pattern)
        public Vector2 TorsoPos, HeadPos, WingPos, LegPos;
        public float TorsoHeight, HeadHeight, WingHeight, LegHeight;
        public float TorsoBob, HeadBob, LegStep;      // walk amplitudes
        public float TorsoIdleBob, HeadIdleBob;       // idle amplitudes

        public string ProfilePath { get { return ArtDir + "/" + Name + "_Directions.asset"; } }
        public string AnimDir { get { return ArtDir + "/Animations"; } }
    }

    /// <summary>Single-prefab, repeatable setup. It refuses to install incomplete artwork.</summary>
    public static class EnemyDirectionPrefabBuilder
    {
        private static readonly string[] PartNames = { "HeadNormal", "HeadAngry", "HeadDead", "Body", "Wing", "Leg" };

        public static readonly EnemyDirectionSpec AdvancedHen = new EnemyDirectionSpec
        {
            Name = "AdvancedHen",
            ArtDir = "Assets/_UIAssets/Monsters/Birds/AdvancedHen/Directions",
            PrefabPath = "Assets/Prefabs/Enemy/Enemy_AdvancedHen.prefab",
            ControllerSource = "Assets/_UIAssets/Monsters/_Common/Animations/Rooster/Controller.controller",
            TorsoPos = new Vector2(0f, 1.6f), HeadPos = new Vector2(0f, 2.65f),
            WingPos = new Vector2(0.82f, 1.55f), LegPos = new Vector2(0.42f, 0.4f),
            TorsoHeight = 1.85f, HeadHeight = 1.8f, WingHeight = 1.35f, LegHeight = 0.8f,
            TorsoBob = 0.05f, HeadBob = 0.06f, LegStep = 0.17f,
            TorsoIdleBob = 0.02f, HeadIdleBob = 0.03f
        };

        public static readonly EnemyDirectionSpec Monkey = new EnemyDirectionSpec
        {
            Name = "Monkey",
            ArtDir = "Assets/_UIAssets/Monsters/Apes/Monkey/Directions",
            PrefabPath = "Assets/Prefabs/Enemy/Enemy_Monkey.prefab",
            ControllerSource = "Assets/_UIAssets/Monsters/_Common/Animations/Bunny/Controller.controller",
            UseRealController = true,
            // measured from the side atlas (PPU 100): head 2.2u tall, torso blob 1.5u, legs ~0.8u
            TorsoPos = new Vector2(0f, 0.60f), HeadPos = new Vector2(0f, 1.95f),
            WingPos = new Vector2(0.80f, 0.80f), LegPos = new Vector2(0.36f, -0.20f),
            TorsoHeight = 1.50f, HeadHeight = 2.20f, WingHeight = 1.00f, LegHeight = 0.80f,
            TorsoBob = 0.04f, HeadBob = 0.05f, LegStep = 0.13f,
            TorsoIdleBob = 0.02f, HeadIdleBob = 0.03f
        };

        private static readonly EnemyDirectionSpec[] Specs = { AdvancedHen, Monkey };

        public static bool TryGetSpec(string monsterName, out EnemyDirectionSpec spec)
        {
            foreach (var s in Specs)
            {
                if (s.Name == monsterName) { spec = s; return true; }
            }
            spec = null;
            return false;
        }

        [MenuItem("Tools/塔防/敌人方向示例/1. 接入 AdvancedHen 上下方向")]
        public static void BuildAdvancedHen() { Build(AdvancedHen); }

        [MenuItem("Tools/塔防/敌人方向示例/2. 接入 Monkey 上下方向")]
        public static void BuildMonkey() { Build(Monkey); }

        /// <summary>Unattended entry used by FT_AutoBuildTrigger (mode=monkeydir).</summary>
        public static void BuildAndVerify(EnemyDirectionSpec spec)
        {
            bool ok;
            string report;
            try
            {
                Build(spec);
                ok = Verify(spec, out report);
            }
            catch (Exception e)
            {
                ok = false;
                report = "EXCEPTION " + e;
            }
            File.WriteAllText(StatusPath(spec), (ok ? "OK\n" : "FAIL\n") + report);
            Debug.Log("[EnemyDirection] " + spec.Name + " BuildAndVerify " + (ok ? "OK" : "FAIL") + "\n" + report);
        }

        private static string StatusPath(EnemyDirectionSpec spec)
        {
            return Path.Combine(Path.GetDirectoryName(Application.dataPath) ?? ".", "Library/FT_" + spec.Name + "DIR_STATUS.txt");
        }

        public static void Build(EnemyDirectionSpec spec)
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode || EditorApplication.isCompiling)
                throw new InvalidOperationException("请在非 Play、编译完成后接入方向资源。");
            // Validate all inputs before importing or editing a prefab.
            foreach (string direction in new[] { "Up", "Down" })
                foreach (string part in PartNames)
                    if (!File.Exists(spec.ArtDir + "/" + direction + "/" + part + ".png"))
                        throw new FileNotFoundException("真实方向美术尚未齐全，未修改预制体：" + spec.Name + " " + direction + "/" + part);

            Directory.CreateDirectory(spec.AnimDir);
            AssetDatabase.Refresh();
            var profile = AssetDatabase.LoadAssetAtPath<EnemyDirectionalProfile>(spec.ProfilePath);
            if (!profile)
            {
                profile = ScriptableObject.CreateInstance<EnemyDirectionalProfile>();
                AssetDatabase.CreateAsset(profile, spec.ProfilePath);
            }
            profile.Up = ImportParts(spec, "Up");
            profile.Down = ImportParts(spec, "Down");
            profile.Controller = BuildController(spec);
            EditorUtility.SetDirty(profile);
            AssetDatabase.SaveAssets();

            var root = PrefabUtility.LoadPrefabContents(spec.PrefabPath);
            try
            {
                Apply(root, profile, spec);
                PrefabUtility.SaveAsPrefabAsset(root, spec.PrefabPath);
            }
            finally { PrefabUtility.UnloadPrefabContents(root); }
            Debug.Log("[EnemyDirection] " + spec.Name + " 已接入上下方向；其他预制体未处理。");
        }

        /// <summary>Called by the existing generator to reapply a previously installed profile.</summary>
        public static bool ApplyIfConfigured(GameObject root, string originalAtlasPath)
        {
            if (string.IsNullOrEmpty(originalAtlasPath)) return false;
            string folder = Path.GetDirectoryName(originalAtlasPath).Replace('\\', '/');
            string name = Path.GetFileNameWithoutExtension(originalAtlasPath);
            EnemyDirectionSpec spec;
            if (!TryGetSpec(name, out spec)) return false;
            var profile = AssetDatabase.LoadAssetAtPath<EnemyDirectionalProfile>(folder + "/Directions/" + name + "_Directions.asset");
            if (!profile || !profile.IsComplete) return false;
            Apply(root, profile, spec);
            return true;
        }

        private static EnemyDirectionalProfile.Parts ImportParts(EnemyDirectionSpec spec, string direction)
        {
            var sprites = new Sprite[PartNames.Length];
            for (int i = 0; i < PartNames.Length; i++)
            {
                string path = spec.ArtDir + "/" + direction + "/" + PartNames[i] + ".png";
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

        private static RuntimeAnimatorController BuildController(EnemyDirectionSpec spec)
        {
            var source = AssetDatabase.LoadAssetAtPath<RuntimeAnimatorController>(spec.ControllerSource);
            if (!source) throw new InvalidOperationException(spec.Name + " 源控制器不存在：" + spec.ControllerSource);

            // Build (or refresh) the per-state _Directions clips shared by both controller kinds.
            var dirClips = new Dictionary<string, AnimationClip>();
            var seen = new HashSet<AnimationClip>();
            foreach (AnimationClip clip in source.animationClips)
            {
                if (!clip || !seen.Add(clip)) continue;
                string clipPath = spec.AnimDir + "/" + clip.name + "_Directions.anim";
                AnimationClip copy = Object.Instantiate(clip);
                copy.name = clip.name + "_Directions";
                AddVerticalCurves(copy, clip.name, spec);
                var existing = AssetDatabase.LoadAssetAtPath<AnimationClip>(clipPath);
                if (existing)
                {
                    EditorUtility.CopySerialized(copy, existing);
                    Object.DestroyImmediate(copy);
                    dirClips[clip.name] = existing;
                }
                else
                {
                    AssetDatabase.CreateAsset(copy, clipPath);
                    dirClips[clip.name] = copy;
                }
            }

            RuntimeAnimatorController result;
            if (spec.UseRealController)
            {
                result = BuildRealController(spec, source, dirClips);
                // the old override controller is superseded; remove it so nobody previews the wrong asset
                string stale = spec.AnimDir + "/" + spec.Name + "_Directions.overrideController";
                if (AssetDatabase.LoadAssetAtPath<Object>(stale)) AssetDatabase.DeleteAsset(stale);
            }
            else
            {
                string path = spec.AnimDir + "/" + spec.Name + "_Directions.overrideController";
                var controller = AssetDatabase.LoadAssetAtPath<AnimatorOverrideController>(path);
                if (!controller)
                {
                    controller = new AnimatorOverrideController(source);
                    AssetDatabase.CreateAsset(controller, path);
                }
                controller.runtimeAnimatorController = source;
                var overrides = new List<KeyValuePair<AnimationClip, AnimationClip>>();
                var clipSeen = new HashSet<AnimationClip>();
                foreach (AnimationClip clip in source.animationClips)
                {
                    if (!clip || !clipSeen.Add(clip)) continue;
                    overrides.Add(new KeyValuePair<AnimationClip, AnimationClip>(clip, dirClips[clip.name]));
                }
                controller.ApplyOverrides(overrides);
                EditorUtility.SetDirty(controller);
                result = controller;
            }
            return result;
        }

        /// <summary>
        /// Copies the family controller and extends it with vertical states:
        ///   AnyState + Dir==1/2 → WalkUp/WalkDown; the →Walk/→Run transitions gain a Dir==0 guard.
        /// Runtime switches direction via SetInteger("Dir", 0/1/2) from EnemyDirectionalVisual.Face.
        /// </summary>
        private static RuntimeAnimatorController BuildRealController(EnemyDirectionSpec spec,
            RuntimeAnimatorController source, Dictionary<string, AnimationClip> dirClips)
        {
            string path = spec.AnimDir + "/" + spec.Name + "_Directions.controller";
            if (!AssetDatabase.LoadAssetAtPath<AnimatorController>(path))
            {
                if (!AssetDatabase.CopyAsset(spec.ControllerSource, path))
                    throw new InvalidOperationException("复制源控制器失败：" + spec.ControllerSource);
            }
            var ctrl = AssetDatabase.LoadAssetAtPath<AnimatorController>(path);

            bool hasDir = false;
            foreach (var p in ctrl.parameters) hasDir |= p.name == "Dir";
            if (!hasDir) ctrl.AddParameter("Dir", AnimatorControllerParameterType.Int);

            AnimatorStateMachine sm = null;
            foreach (var layer in ctrl.layers)
            {
                if (layer.stateMachine == null) continue;
                foreach (var child in layer.stateMachine.states)
                {
                    if (child.state != null && child.state.name == "Walk")
                    {
                        sm = layer.stateMachine;
                        break;
                    }
                }
                if (sm != null) break;
            }
            if (sm == null) throw new InvalidOperationException("源控制器缺少 Walk 状态：" + path);

            // Remap every state motion to its _Directions variant (Run/Idle reuse Walk/Ready clips by name).
            foreach (var child in sm.states)
            {
                var clip = child.state != null ? child.state.motion as AnimationClip : null;
                if (clip == null) continue;
                if (dirClips.TryGetValue(clip.name, out var dirClip)) child.state.motion = dirClip;
            }

            // Vertical walk clips: DirectionVisual curves only, so these states drive just the vertical rig.
            var walkUpClip = BuildVerticalOnlyClip(spec, dirClips["Walk"], "WalkUp_Directions");
            var walkDownClip = BuildVerticalOnlyClip(spec, dirClips["Walk"], "WalkDown_Directions");

            var walk = FindState(sm, "Walk");
            var run = FindState(sm, "Run");
            var walkUp = EnsureState(sm, "WalkUp", walkUpClip, new Vector2(-220f, 230f));
            var walkDown = EnsureState(sm, "WalkDown", walkDownClip, new Vector2(-220f, 320f));

            // Idempotent cleanup: drop previously added transitions/conditions.
            var keptAny = new List<AnimatorStateTransition>();
            foreach (var t in sm.anyStateTransitions)
            {
                var dst = t.destinationState;
                if (dst != null && (dst.name == "WalkUp" || dst.name == "WalkDown")) continue;
                keptAny.Add(t);
            }
            sm.anyStateTransitions = keptAny.ToArray();
            foreach (var child in sm.states)
            {
                var st = child.state;
                if (st == null) continue;
                if (st.name == "WalkUp" || st.name == "WalkDown")
                {
                    st.transitions = new AnimatorStateTransition[0];
                    continue;
                }
                var kept = new List<AnimatorStateTransition>();
                foreach (var t in st.transitions)
                {
                    var dst = t.destinationState;
                    if (dst != null && (dst.name == "WalkUp" || dst.name == "WalkDown")) continue;
                    kept.Add(t);
                }
                st.transitions = kept.ToArray();
                foreach (var t in st.transitions)
                {
                    for (int i = t.conditions.Length - 1; i >= 0; i--)
                        if (t.conditions[i].mode == AnimatorConditionMode.Equals && t.conditions[i].parameter == "Dir")
                            t.RemoveCondition(t.conditions[i]);
                }
            }

            // AnyState guard: horizontal Walk/Run only when Dir == 0.
            foreach (var t in sm.anyStateTransitions)
            {
                if (t.destinationState != walk && t.destinationState != run) continue;
                bool hasGuard = false;
                foreach (var c in t.conditions) hasGuard |= c.parameter == "Dir";
                if (!hasGuard) t.AddCondition(AnimatorConditionMode.Equals, 0f, "Dir");
            }

            // New AnyState transitions into the vertical walk states.
            AddAnyState(sm, walkUp,
                new DirCond(AnimatorConditionMode.Equals, 2f, "State"),
                new DirCond(AnimatorConditionMode.IfNot, 0f, "Action"),
                new DirCond(AnimatorConditionMode.Equals, 1f, "Dir"));
            AddAnyState(sm, walkDown,
                new DirCond(AnimatorConditionMode.Equals, 2f, "State"),
                new DirCond(AnimatorConditionMode.IfNot, 0f, "Action"),
                new DirCond(AnimatorConditionMode.Equals, 2f, "Dir"));

            EditorUtility.SetDirty(ctrl);
            AssetDatabase.SaveAssets();
            return ctrl;
        }

        private static AnimationClip BuildVerticalOnlyClip(EnemyDirectionSpec spec, AnimationClip source, string name)
        {
            string path = spec.AnimDir + "/" + name + ".anim";
            var copy = Object.Instantiate(source);
            copy.name = name;
            foreach (var b in AnimationUtility.GetCurveBindings(copy))
                if (!b.path.StartsWith("DirectionVisual/"))
                    AnimationUtility.SetEditorCurve(copy, b, null);
            var existing = AssetDatabase.LoadAssetAtPath<AnimationClip>(path);
            if (existing)
            {
                EditorUtility.CopySerialized(copy, existing);
                Object.DestroyImmediate(copy);
                EditorUtility.SetDirty(existing);
                return existing;
            }
            AssetDatabase.CreateAsset(copy, path);
            return copy;
        }

        private static AnimatorState FindState(AnimatorStateMachine sm, string name)
        {
            foreach (var child in sm.states)
                if (child.state != null && child.state.name == name)
                    return child.state;
            throw new InvalidOperationException("状态不存在：" + name);
        }

        private static AnimatorState EnsureState(AnimatorStateMachine sm, string name, AnimationClip motion, Vector2 position)
        {
            foreach (var child in sm.states)
            {
                if (child.state != null && child.state.name == name)
                {
                    child.state.motion = motion;
                    return child.state;
                }
            }
            var st = sm.AddState(name, position);
            st.motion = motion;
            st.speedParameter = "Speed";
            st.writeDefaultValues = true;
            return st;
        }

        private struct DirCond
        {
            public AnimatorConditionMode Mode;
            public float Threshold;
            public string Name;

            public DirCond(AnimatorConditionMode mode, float threshold, string name)
            {
                Mode = mode;
                Threshold = threshold;
                Name = name;
            }
        }

        private static void AddAnyState(AnimatorStateMachine sm, AnimatorState target, params DirCond[] conds)
        {
            var t = sm.AddAnyStateTransition(target);
            t.hasExitTime = false;
            t.exitTime = 0f;
            t.hasFixedDuration = true;
            t.duration = 0.05f;
            t.offset = 0f;
            t.interruptionSource = TransitionInterruptionSource.None;
            t.canTransitionToSelf = false;
            foreach (var c in conds)
                t.AddCondition(c.Mode, c.Threshold, c.Name);
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

        private static void AddVerticalCurves(AnimationClip clip, string state, EnemyDirectionSpec s)
        {
            bool walking = state.IndexOf("Walk", StringComparison.OrdinalIgnoreCase) >= 0;
            bool attack = state.IndexOf("Attack", StringComparison.OrdinalIgnoreCase) >= 0;
            bool death = state.IndexOf("Death", StringComparison.OrdinalIgnoreCase) >= 0;
            float t = s.TorsoPos.y, h = s.HeadPos.y, l = s.LegPos.y;
            Curve(clip, "", "localEulerAnglesRaw.z", death ? new[] { 0f, -12f, -65f, -80f, -80f } : new[] { 0f, 0f });
            Curve(clip, "", "m_LocalPosition.y", new[] { 0f, 0f });
            Curve(clip, "/Torso", "m_LocalPosition.y", walking
                ? new[] { t, t + s.TorsoBob, t, t + s.TorsoBob, t } : new[] { t, t + s.TorsoIdleBob, t });
            Curve(clip, "/Head", "m_LocalPosition.y", walking
                ? new[] { h, h + s.HeadBob, h, h + s.HeadBob, h } : new[] { h, h + s.HeadIdleBob, h });
            Curve(clip, "/Head", "localEulerAnglesRaw.z", attack
                ? new[] { 0f, -6f, 12f, -5f, 0f } : new[] { 0f, 0f });
            Curve(clip, "/LegL", "m_LocalPosition.y", walking
                ? new[] { l, l + s.LegStep, l, l, l } : new[] { l, l });
            Curve(clip, "/LegR", "m_LocalPosition.y", walking
                ? new[] { l, l, l, l + s.LegStep, l } : new[] { l, l });
            Curve(clip, "/WingL", "localEulerAnglesRaw.z", attack
                ? new[] { 0f, -25f, -40f, -15f, 0f } : walking ? new[] { -3f, 3f, -3f, 3f, -3f } : new[] { 0f, 0f });
            Curve(clip, "/WingR", "localEulerAnglesRaw.z", attack
                ? new[] { 0f, 25f, 40f, 15f, 0f } : walking ? new[] { 3f, -3f, 3f, -3f, 3f } : new[] { 0f, 0f });
        }

        private static void Apply(GameObject root, EnemyDirectionalProfile profile, EnemyDirectionSpec s)
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
            visual.Body = Part(motion, "Torso", parts.Body, s.TorsoPos, s.TorsoHeight, 15);
            visual.Head = Part(motion, "Head", parts.NormalHead, s.HeadPos, s.HeadHeight, 25);
            visual.WingL = Part(motion, "WingL", parts.Wing, new Vector2(-s.WingPos.x, s.WingPos.y), s.WingHeight, 20);
            visual.WingR = Part(motion, "WingR", parts.Wing, s.WingPos, s.WingHeight, 20);
            visual.LegL = Part(motion, "LegL", parts.Leg, new Vector2(-s.LegPos.x, s.LegPos.y), s.LegHeight, 5);
            visual.LegR = Part(motion, "LegR", parts.Leg, s.LegPos, s.LegHeight, 5);
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

        /// <summary>Editor-time integrity checks; writes a report for unattended runs.</summary>
        public static bool Verify(EnemyDirectionSpec s, out string report)
        {
            var lines = new List<string>();
            bool ok = true;
            var profile = AssetDatabase.LoadAssetAtPath<EnemyDirectionalProfile>(s.ProfilePath);
            ok &= Check(lines, "profile", profile != null);
            if (profile)
            {
                ok &= Check(lines, "profile.IsComplete", profile.IsComplete);
                foreach (string d in new[] { "Up", "Down" })
                {
                    var p = d == "Up" ? profile.Up : profile.Down;
                    ok &= Check(lines, d + ".NormalHead", p.NormalHead != null);
                    ok &= Check(lines, d + ".AngryHead", p.AngryHead != null);
                    ok &= Check(lines, d + ".DeadHead", p.DeadHead != null);
                    ok &= Check(lines, d + ".Body", p.Body != null);
                    ok &= Check(lines, d + ".Wing", p.Wing != null);
                    ok &= Check(lines, d + ".Leg", p.Leg != null);
                }
                var overrideCtrl = profile.Controller as AnimatorOverrideController;
                var realCtrl = profile.Controller as AnimatorController;
                ok &= Check(lines, "controller kind=" + (profile.Controller ? profile.Controller.GetType().Name : "null"),
                    overrideCtrl != null || realCtrl != null);
                if (overrideCtrl)
                {
                    var pairs = overrideCtrl.clips;
                    ok &= Check(lines, "override count=" + pairs.Length, pairs.Length > 0);
                    foreach (var pair in pairs)
                    {
                        if (!pair.overrideClip)
                        {
                            ok &= Check(lines, "override clip " + (pair.originalClip ? pair.originalClip.name : "?"), false);
                            continue;
                        }
                        int dirCurves = 0, total = 0;
                        foreach (var b in AnimationUtility.GetCurveBindings(pair.overrideClip))
                        {
                            total++;
                            if (b.path.StartsWith("DirectionVisual/")) dirCurves++;
                        }
                        ok &= Check(lines, pair.overrideClip.name + " curves total=" + total + " direction=" + dirCurves,
                            total > 0 && dirCurves >= 9);
                    }
                }
                else if (realCtrl)
                {
                    AnimatorStateMachine sm = null;
                    foreach (var layer in realCtrl.layers)
                    {
                        if (layer.stateMachine == null) continue;
                        foreach (var child in layer.stateMachine.states)
                            if (child.state != null && child.state.name == "Walk") { sm = layer.stateMachine; break; }
                        if (sm != null) break;
                    }
                    ok &= Check(lines, "state machine found", sm != null);
                    if (sm != null)
                    {
                        var walkUp = FindStateOrNull(sm, "WalkUp");
                        var walkDown = FindStateOrNull(sm, "WalkDown");
                        var walk = FindStateOrNull(sm, "Walk");
                        ok &= Check(lines, "WalkUp state + motion", walkUp != null && walkUp.motion != null);
                        ok &= Check(lines, "WalkDown state + motion", walkDown != null && walkDown.motion != null);
                        if (walkUp != null && walkUp.motion != null)
                        {
                            int dirCurves = 0, total = 0;
                            foreach (var b in AnimationUtility.GetCurveBindings((AnimationClip)walkUp.motion))
                            {
                                total++;
                                if (b.path.StartsWith("DirectionVisual/")) dirCurves++;
                            }
                            ok &= Check(lines, "WalkUp clip vertical-only total=" + total + " direction=" + dirCurves,
                                total > 0 && dirCurves == total);
                        }
                        bool upLink = false, downLink = false, walkGuard = false;
                        foreach (var t in sm.anyStateTransitions)
                        {
                            if (t.destinationState == null) continue;
                            if (t.destinationState == walkUp || t.destinationState == walkDown)
                            {
                                bool dirCond = false;
                                foreach (var c in t.conditions) dirCond |= c.parameter == "Dir";
                                if (t.destinationState == walkUp) upLink = dirCond; else downLink = dirCond;
                            }
                            if (walk != null && t.destinationState == walk)
                                foreach (var c in t.conditions) walkGuard |= c.parameter == "Dir";
                        }
                        ok &= Check(lines, "AnyState→WalkUp has Dir condition", upLink);
                        ok &= Check(lines, "AnyState→WalkDown has Dir condition", downLink);
                        ok &= Check(lines, "AnyState→Walk has Dir==0 guard", walkGuard);
                    }
                }
            }
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(s.PrefabPath);
            ok &= Check(lines, "prefab", prefab != null);
            if (prefab)
            {
                var visual = prefab.GetComponent<EnemyDirectionalVisual>();
                ok &= Check(lines, "prefab EnemyDirectionalVisual", visual != null);
                if (visual)
                {
                    ok &= Check(lines, "visual.IsConfigured", visual.IsConfigured);
                    ok &= Check(lines, "visual.Profile==asset", visual.Profile == profile);
                    ok &= Check(lines, "horizontal renderers=" + (visual.HorizontalRenderers != null ? visual.HorizontalRenderers.Length : 0),
                        visual.HorizontalRenderers != null && visual.HorizontalRenderers.Length > 0);
                    ok &= Check(lines, "parts wired", visual.Head && visual.Body && visual.WingL && visual.WingR && visual.LegL && visual.LegR);
                }
                var animator = prefab.GetComponent<Animator>();
                ok &= Check(lines, "animator", animator != null);
                if (animator && profile)
                    ok &= Check(lines, "animator uses profile controller",
                        animator.runtimeAnimatorController == profile.Controller);
                var group = prefab.transform.Find("DirectionVisual/Motion");
                ok &= Check(lines, "DirectionVisual/Motion hierarchy", group != null);
                if (profile && visual && profile.Controller && group != null)
                    ok &= VerifyAnimationSampling(prefab, profile.Controller, lines);
            }
            report = string.Join("\n", lines.ToArray());
            return ok;
        }

        /// <summary>Samples the controller clips on a temporary prefab instance in the editor,
        /// proving the vertical curves actually drive the DirectionVisual rig during playback.</summary>
        private static bool VerifyAnimationSampling(GameObject prefab, RuntimeAnimatorController controller, List<string> lines)
        {
            bool ok = true;
            var temp = Object.Instantiate(prefab);
            try
            {
                var anim = temp.GetComponent<Animator>();
                if (anim == null) return Check(lines, "sampling needs Animator", false);
                anim.runtimeAnimatorController = controller;
                Transform Root() { return temp.transform.Find("DirectionVisual/Motion"); }
                foreach (var clip in controller.animationClips)
                {
                    if (clip == null) continue;
                    string n = clip.name;
                    if (!n.EndsWith("_Directions")) continue;
                    float t = clip.length;
                    if (n == "Walk_Directions" || n == "WalkUp_Directions" || n == "WalkDown_Directions")
                    {
                        anim.Play(n.Replace("_Directions", string.Empty), 0, 0f);
                        anim.Update(0f);
                        float baseT = Root().Find("Torso").localPosition.y;
                        float baseL = Root().Find("LegL").localPosition.y;
                        anim.Update(t * 0.25f);
                        float torsoQ = Root().Find("Torso").localPosition.y;
                        float legLQ = Root().Find("LegL").localPosition.y;
                        float legRQ = Root().Find("LegR").localPosition.y;
                        ok &= Check(lines, n + " torso bob " + baseT.ToString("0.000") + "->" + torsoQ.ToString("0.000"),
                            Mathf.Abs(torsoQ - baseT) > 0.005f);
                        // same instant: left and right legs must be at different heights
                        ok &= Check(lines, n + " legs alternate L" + legLQ.ToString("0.000") + " R" + legRQ.ToString("0.000"),
                            Mathf.Abs(legLQ - baseL) > 0.005f && Mathf.Abs(legLQ - legRQ) > 0.005f);
                    }
                    else if (n == "Attack_Directions")
                    {
                        anim.Play("Attack", 0, 0f); anim.Update(0f);
                        anim.Update(t * 0.5f);
                        float z = Root().Find("Head").localEulerAngles.z;
                        if (z > 180f) z -= 360f;
                        ok &= Check(lines, "attack head swing " + z.ToString("0.0"), Mathf.Abs(z) > 3f);
                    }
                    else if (n == "Death_Directions")
                    {
                        anim.Play("Death", 0, 0f); anim.Update(0f);
                        anim.Update(t * 0.9f);
                        float z = Root().localEulerAngles.z;
                        if (z > 180f) z -= 360f;
                        ok &= Check(lines, "death rig tilt " + z.ToString("0.0"), z < -60f);
                    }
                }
            }
            finally { Object.DestroyImmediate(temp); }
            return ok;
        }

        private static AnimatorState FindStateOrNull(AnimatorStateMachine sm, string name)
        {
            foreach (var child in sm.states)
                if (child.state != null && child.state.name == name)
                    return child.state;
            return null;
        }

        private static bool Check(List<string> lines, string what, bool pass)
        {
            lines.Add((pass ? "PASS " : "FAIL ") + what);
            return pass;
        }
    }
}
