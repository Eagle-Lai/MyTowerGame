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
        public bool UseSeparateViewRigs;
        public bool UseRealController;  // true: copy the family controller and add WalkUp/WalkDown states (code controls Dir); false: AnimatorOverrideController (AdvancedHen pattern)
        public Vector2 TorsoPos, HeadPos, WingPos, LegPos;
        public Vector2 TorsoSize, HeadSize, WingSize, LegSize;   // target box (0 = fall back to the height below)
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
            TorsoPos = new Vector2(0f, 1.4f), HeadPos = new Vector2(0f, 2.65f),
            WingPos = new Vector2(0.91f, 1.4f), LegPos = new Vector2(0.32f, 0.4f),
            TorsoHeight = 2.1f, HeadHeight = 1.8f, WingHeight = 1.32f, LegHeight = 0.8f,
            TorsoBob = 0.05f, HeadBob = 0.06f, LegStep = 0.09f,
            TorsoIdleBob = 0.02f, HeadIdleBob = 0.03f
        };

        public static readonly EnemyDirectionSpec Monkey = new EnemyDirectionSpec
        {
            Name = "Monkey",
            ArtDir = "Assets/_UIAssets/Monsters/Apes/Monkey/Directions",
            PrefabPath = "Assets/Prefabs/Enemy/Enemy_Monkey.prefab",
            ControllerSource = "Assets/_UIAssets/Monsters/_Common/Animations/Bunny/Controller.controller",
            UseRealController = true,
            // Vertical (front/back) layout, in rig units (root scale 0.5 on screen).
            // Calibrated against the side view: feet on the ground line (0), total height ~2.75
            // so turning up/down does not change the monster's size, head sits on the torso and
            // the arms hang from the shoulders instead of growing out of the cheeks.
            TorsoPos = new Vector2(0f, 1.175f), TorsoSize = new Vector2(1.30f, 1.25f),
            HeadPos = new Vector2(0f, 2.225f), HeadSize = new Vector2(1.95f, 1.45f),
            WingPos = new Vector2(0.60f, 1.00f), WingSize = new Vector2(0.42f, 1.05f),
            LegPos = new Vector2(0.24f, 0.375f), LegSize = new Vector2(0.46f, 0.70f),
            TorsoHeight = 1.25f, HeadHeight = 1.45f, WingHeight = 1.05f, LegHeight = 0.75f,
            TorsoBob = 0.025f, HeadBob = 0.03f, LegStep = 0.10f,
            TorsoIdleBob = 0.012f, HeadIdleBob = 0.018f
        };

        private static readonly EnemyDirectionSpec[] Specs = { AdvancedHen, Monkey };

        public static bool TryGetSpec(string monsterName, out EnemyDirectionSpec spec)
        {
            if (EnemyDirectionalRigBuilder.TryGetSpec(monsterName, out spec)) return true;
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

        /// <summary>
        /// Rebakes only WalkUp/WalkDown (motion + direction showcase) so the Animation window can
        /// preview the vertical walk. Prefab / controller / other clips stay untouched.
        /// </summary>
        [MenuItem("Tools/塔防/敌人方向示例/4. 重建上下行走片段（不改预制体）")]
        public static void RebuildVerticalClips()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode || EditorApplication.isCompiling)
            {
                Debug.LogError("[EnemyDirection] 请在非 Play、编译完成后再重建上下行走片段。");
                return;
            }
            var spec = Monkey;
            var source = AssetDatabase.LoadAssetAtPath<AnimationClip>(spec.AnimDir + "/Walk_Directions.anim");
            if (!source)
            {
                Debug.LogError("[EnemyDirection] 找不到 Walk_Directions.anim：" + spec.AnimDir);
                return;
            }
            var up = BuildVerticalOnlyClip(spec, source, "WalkUp_Directions");
            var down = BuildVerticalOnlyClip(spec, source, "WalkDown_Directions");
            EditorUtility.SetDirty(up);
            EditorUtility.SetDirty(down);
            var ctrl = AssetDatabase.LoadAssetAtPath<AnimatorController>(spec.AnimDir + "/" + spec.Name + "_Directions.controller");
            if (ctrl)
            {
                NormalizeTransformCurves(spec, ctrl.animationClips);
                EnforceWriteDefaultsOff(ctrl);
            }
            AssetDatabase.SaveAssets();
            Debug.Log("[EnemyDirection] WalkUp/WalkDown 已重建（动作 + 方向展示曲线）；其余资源未改动。");
        }

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
            if (spec.UseSeparateViewRigs) { EnemyDirectionalRigBuilder.Build(spec); return; }
            if (EditorApplication.isPlayingOrWillChangePlaymode || EditorApplication.isCompiling)
                throw new InvalidOperationException("请在非 Play、编译完成后接入方向资源。");
            // Validate all inputs before importing or editing a prefab.
            if (!File.Exists(AtlasPath(spec)))
                throw new FileNotFoundException("方向美术图集不存在，未修改预制体：" + spec.Name + " " + AtlasPath(spec));
            if (!File.Exists(AtlasManifestPath(spec)))
                throw new FileNotFoundException("方向图集缺少切片清单，未修改预制体：" + AtlasManifestPath(spec));

            Directory.CreateDirectory(spec.AnimDir);
            AssetDatabase.Refresh();
            var profile = AssetDatabase.LoadAssetAtPath<EnemyDirectionalProfile>(spec.ProfilePath);
            if (!profile)
            {
                profile = ScriptableObject.CreateInstance<EnemyDirectionalProfile>();
                AssetDatabase.CreateAsset(profile, spec.ProfilePath);
            }
            var parts = ImportAtlas(spec);
            profile.Up = ImportParts(parts, "Up");
            profile.Down = ImportParts(parts, "Down");
            profile.Down.WingsBehindBody = spec.Name == "AdvancedHen";
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
            if (spec.UseSeparateViewRigs) EnemyDirectionalRigBuilder.Apply(root, profile, spec);
            else Apply(root, profile, spec);
            return true;
        }

        private static string AtlasPath(EnemyDirectionSpec spec)
        {
            return spec.ArtDir + "/" + spec.Name + "_Directions.png";
        }

        private static string AtlasManifestPath(EnemyDirectionSpec spec)
        {
            return spec.ArtDir + "/" + spec.Name + "_Directions.sprites.json";
        }

        /// <summary>Slice description produced by the atlas builder (bottom-left rects, PPU 100).</summary>
        [Serializable]
        private class AtlasManifest
        {
            public string texture;
            public int width;
            public int height;
            public int ppu;
            public AtlasSprite[] sprites;
        }

        [Serializable]
        private class AtlasSprite
        {
            public string name;
            public int x, y, w, h;
        }

        /// <summary>
        /// Imports the merged direction atlas (one PNG, twelve named slices — same shape as the side
        /// Monkey.png) and returns its sprites keyed by name. Replaces the per-part PNG workflow.
        /// </summary>
        private static Dictionary<string, Sprite> ImportAtlas(EnemyDirectionSpec spec)
        {
            string path = AtlasPath(spec);
            AssetDatabase.ImportAsset(path, ImportAssetOptions.ForceSynchronousImport);
            var manifest = JsonUtility.FromJson<AtlasManifest>(File.ReadAllText(AtlasManifestPath(spec)));
            if (manifest == null || manifest.sprites == null || manifest.sprites.Length == 0)
                throw new InvalidOperationException("方向图集清单不可用：" + AtlasManifestPath(spec));

            var importer = (TextureImporter)AssetImporter.GetAtPath(path);
            importer.textureType = TextureImporterType.Sprite;
            importer.spriteImportMode = SpriteImportMode.Multiple;
            importer.spritePixelsPerUnit = manifest.ppu > 0 ? manifest.ppu : 100;
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

            var metas = new SpriteMetaData[manifest.sprites.Length];
            for (int i = 0; i < metas.Length; i++)
            {
                var s = manifest.sprites[i];
                metas[i] = new SpriteMetaData
                {
                    name = s.name,
                    rect = new Rect(s.x, s.y, s.w, s.h),
                    alignment = (int)SpriteAlignment.Center,
                    pivot = new Vector2(0.5f, 0.5f)
                };
            }
            importer.spritesheet = metas;
            importer.SaveAndReimport();

            var byName = new Dictionary<string, Sprite>();
            foreach (var obj in AssetDatabase.LoadAllAssetsAtPath(path))
            {
                var sprite = obj as Sprite;
                if (sprite && !byName.ContainsKey(sprite.name)) byName[sprite.name] = sprite;
            }
            foreach (var s in manifest.sprites)
                if (!byName.ContainsKey(s.name))
                    throw new InvalidOperationException("图集切片缺失：" + s.name + " @ " + path);
            return byName;
        }

        private static EnemyDirectionalProfile.Parts ImportParts(Dictionary<string, Sprite> atlas, string direction)
        {
            var sprites = new Sprite[PartNames.Length];
            for (int i = 0; i < PartNames.Length; i++)
            {
                string key = direction + "_" + PartNames[i];
                if (!atlas.TryGetValue(key, out sprites[i]))
                    throw new InvalidOperationException("图集里没有切片：" + key);
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
            if (spec.Name == "AdvancedHen")
            {
                result = BuildAdvancedHenController(spec, dirClips);
            }
            else if (spec.UseRealController)
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

        internal static RuntimeAnimatorController BuildAdvancedHenController(EnemyDirectionSpec spec,
            Dictionary<string, AnimationClip> clips)
        {
            string path = spec.AnimDir + "/" + spec.Name + "_Directions.controller";
            var controller = AssetDatabase.LoadAssetAtPath<AnimatorController>(path);
            if (!controller) controller = AnimatorController.CreateAnimatorControllerAtPath(path);
            controller.parameters = new[]
            {
                new AnimatorControllerParameter { name = "State", type = AnimatorControllerParameterType.Int },
                new AnimatorControllerParameter { name = "Speed", type = AnimatorControllerParameterType.Float, defaultFloat = 1f },
                new AnimatorControllerParameter { name = "Attack", type = AnimatorControllerParameterType.Trigger },
                new AnimatorControllerParameter { name = "Action", type = AnimatorControllerParameterType.Bool }
            };
            var sm = controller.layers[0].stateMachine;
            sm.anyStateTransitions = new AnimatorStateTransition[0];
            string[] names = { "Idle", "Ready", "Walk", "Run", "Death", "Attack" };
            int[] values = { 0, 1, 2, 3, 9 };
            var states = new AnimatorState[names.Length];
            for (int i = 0; i < names.Length; i++)
            {
                states[i] = FindStateOrNull(sm, names[i]) ?? sm.AddState(names[i], new Vector2(i % 3 * 230f, i / 3 * 100f));
                states[i].transitions = new AnimatorStateTransition[0];
                states[i].motion = clips[i < 2 ? "Ready" : i < 4 ? "Walk" : names[i]];
                states[i].writeDefaultValues = true;
                states[i].speedParameter = "Speed";
                states[i].speedParameterActive = true;
            }
            sm.defaultState = states[0];
            AddAnyState(sm, states[4], new DirCond(AnimatorConditionMode.Equals, 9, "State"));
            AddAnyState(sm, states[5], new DirCond(AnimatorConditionMode.If, 0, "Attack"),
                new DirCond(AnimatorConditionMode.NotEqual, 9, "State"));
            // Locomotion has no AnyState re-entry. Direction changes only swap sprites.
            for (int from = 0; from < states.Length; from++)
            {
                if (from == 4) continue;
                for (int to = 0; to < 4; to++)
                {
                    if (from == to) continue;
                    var transition = states[from].AddTransition(states[to]);
                    transition.hasExitTime = from == 5;
                    transition.exitTime = 1f;
                    transition.hasFixedDuration = true;
                    transition.duration = 0f;
                    transition.AddCondition(AnimatorConditionMode.Equals, values[to], "State");
                    transition.AddCondition(AnimatorConditionMode.IfNot, 0, "Action");
                }
            }
            EditorUtility.SetDirty(controller);
            return controller;
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

            // The vertical walk clips carry the view (which renderers are on, which sprites they use).
            // With Write Defaults on, every other state would reset those renderers to the prefab
            // defaults — the monster would flip back to the side view as soon as it idles or attacks
            // while facing up/down. Turning Write Defaults off keeps whatever ApplyView() decided —
            // but then every clip must animate the same transform set, otherwise a pose lingers
            // across states (e.g. attack leg swing surviving into idle). Normalise first, then switch.
            NormalizeTransformCurves(spec, ctrl.animationClips);
            EnforceWriteDefaultsOff(ctrl);

            EditorUtility.SetDirty(ctrl);
            AssetDatabase.SaveAssets();
            return ctrl;
        }

        /// <summary>
        /// Gives every clip the union of all Transform bindings, filling the missing ones with the
        /// rest pose. Required once Write Defaults is off, and it also makes the vertical clips
        /// independent of whatever the previous state left behind.
        /// </summary>
        private static void NormalizeTransformCurves(EnemyDirectionSpec spec, AnimationClip[] clips)
        {
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(spec.PrefabPath);
            if (!prefab || clips == null) return;
            var union = new Dictionary<string, EditorCurveBinding>();
            foreach (var clip in clips)
            {
                if (!clip) continue;
                foreach (var b in AnimationUtility.GetCurveBindings(clip))
                    if (b.type == typeof(Transform))
                    {
                        string key = b.path + "|" + b.propertyName;
                        if (!union.ContainsKey(key)) union[key] = b;
                    }
            }
            foreach (var clip in clips)
            {
                if (!clip) continue;
                var have = new HashSet<string>();
                foreach (var b in AnimationUtility.GetCurveBindings(clip)) have.Add(b.path + "|" + b.propertyName);
                float end = Mathf.Max(0.01f, clip.length);
                bool dirty = false;
                foreach (var kv in union)
                {
                    if (have.Contains(kv.Key)) continue;
                    AnimationUtility.SetEditorCurve(clip, kv.Value,
                        AnimationCurve.Constant(0f, end, RestValue(prefab.transform, kv.Value)));
                    dirty = true;
                }
                if (dirty) EditorUtility.SetDirty(clip);
            }
        }

        private static float RestValue(Transform root, EditorCurveBinding binding)
        {
            var node = string.IsNullOrEmpty(binding.path) ? root : root.Find(binding.path);
            if (!node) return 0f;
            string p = binding.propertyName;
            if (p.StartsWith("m_LocalPosition")) return Axis(node.localPosition, p);
            if (p.StartsWith("m_LocalScale")) return Axis(node.localScale, p);
            if (p.StartsWith("localEulerAnglesRaw") || p.StartsWith("m_LocalEulerAngles"))
            {
                var e = node.localEulerAngles;
                e.x = e.x > 180f ? e.x - 360f : e.x;
                e.y = e.y > 180f ? e.y - 360f : e.y;
                e.z = e.z > 180f ? e.z - 360f : e.z;
                return Axis(e, p);
            }
            return 0f;
        }

        private static float Axis(Vector3 v, string property)
        {
            if (property.EndsWith(".x")) return v.x;
            if (property.EndsWith(".y")) return v.y;
            return v.z;
        }

        private static void EnforceWriteDefaultsOff(AnimatorController ctrl)
        {
            foreach (var layer in ctrl.layers)
            {
                if (layer.stateMachine == null) continue;
                foreach (var child in layer.stateMachine.states)
                {
                    if (child.state != null) child.state.writeDefaultValues = false;
                }
            }
            EditorUtility.SetDirty(ctrl);
        }

        private static AnimationClip BuildVerticalOnlyClip(EnemyDirectionSpec spec, AnimationClip source, string name)
        {
            string path = spec.AnimDir + "/" + name + ".anim";
            var copy = Object.Instantiate(source);
            copy.name = name;
            float end = Mathf.Max(0.01f, copy.length);
            foreach (var b in AnimationUtility.GetCurveBindings(copy))
                if (!b.path.StartsWith("DirectionVisual/"))
                    AnimationUtility.SetEditorCurve(copy, b, null);
            foreach (var b in AnimationUtility.GetObjectReferenceCurveBindings(copy))
                if (!b.path.StartsWith("DirectionVisual/"))
                    AnimationUtility.SetObjectReferenceCurve(copy, b, null);
            BakeVerticalShowcase(spec, copy, name.IndexOf("Up", StringComparison.Ordinal) >= 0, end);
            // Adding curves bumps stopTime by one frame; restore the exact source cycle length.
            var settings = AnimationUtility.GetAnimationClipSettings(copy);
            settings.stopTime = end;
            AnimationUtility.SetAnimationClipSettings(copy, settings);
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

        /// <summary>
        /// The two vertical clips are exclusive to the up/down view, so they also carry the view itself:
        /// horizontal rig hidden, vertical rig shown with that direction's sprites / sorting / flip.
        /// Values are identical to EnemyDirectionalVisual.ApplyView, so runtime playback is unchanged —
        /// but the Animation window (and Animator preview) can now show the real up/down animation
        /// instead of a motionless side view.
        /// </summary>
        private static void BakeVerticalShowcase(EnemyDirectionSpec spec, AnimationClip clip, bool up, float end)
        {
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(spec.PrefabPath);
            var profile = AssetDatabase.LoadAssetAtPath<EnemyDirectionalProfile>(spec.ProfilePath);
            if (!prefab || !profile || !profile.IsComplete) return;
            var parts = up ? profile.Up : profile.Down;

            Transform hpBar = prefab.transform.Find("HpBar");
            Transform rig = prefab.transform.Find("DirectionVisual");
            foreach (var sr in prefab.GetComponentsInChildren<SpriteRenderer>(true))
            {
                if (sr.name == "Shadow") continue;
                if (hpBar && sr.transform.IsChildOf(hpBar)) continue;
                if (rig && sr.transform.IsChildOf(rig)) continue;
                BakeConstant(clip, RelativePath(prefab.transform, sr.transform), "m_Enabled", 0f, end);
            }

            // Back view (up) puts the head behind the torso; front view keeps it in front.
            BakePartClip(clip, "Torso", parts.Body, 15, false, end);
            BakePartClip(clip, "Head", parts.NormalHead, 25, false, end);
            BakePartClip(clip, "WingL", parts.Wing, 20, false, end);
            BakePartClip(clip, "WingR", parts.Wing, 20, true, end);
            BakePartClip(clip, "LegL", parts.Leg, 5, false, end);
            BakePartClip(clip, "LegR", parts.Leg, 5, false, end);
        }

        private static void BakePartClip(AnimationClip clip, string node, Sprite sprite, int order, bool flipX, float end)
        {
            string path = "DirectionVisual/Motion/" + node + "/Sprite";
            BakeConstant(clip, path, "m_Enabled", 1f, end);
            BakeConstant(clip, path, "m_SortingOrder", order, end);
            BakeConstant(clip, path, "m_FlipX", flipX ? 1f : 0f, end);
            if (!sprite) return;
            var binding = EditorCurveBinding.PPtrCurve(path, typeof(SpriteRenderer), "m_Sprite");
            // A single key holds the sprite for the whole clip and does not stretch clip.length
            // (a key exactly on stopTime makes Unity add one extra sample frame to the loop).
            AnimationUtility.SetObjectReferenceCurve(clip, binding, new[]
            {
                new ObjectReferenceKeyframe { time = 0f, value = sprite }
            });
        }

        private static void BakeConstant(AnimationClip clip, string path, string property, float value, float end)
        {
            // NOTE: clip.length grows by one frame every time a curve is added, so the end time
            // must be captured once before baking, otherwise the loop gets longer and longer.
            var curve = AnimationCurve.Constant(0f, Mathf.Max(0.01f, end), value);
            AnimationUtility.SetEditorCurve(clip, EditorCurveBinding.FloatCurve(path, typeof(SpriteRenderer), property), curve);
        }

        private static string RelativePath(Transform root, Transform node)
        {
            var parts = new List<string>();
            while (node && node != root)
            {
                parts.Add(node.name);
                node = node.parent;
            }
            parts.Reverse();
            return string.Join("/", parts.ToArray());
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

        private static void Curve(AnimationClip clip, string node, string property, float[] values, float length)
        {
            var keys = new Keyframe[values.Length];
            length = Mathf.Max(0.01f, length);
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
            float duration = clip.length;
            void RigCurve(string node, string property, float[] values) { Curve(clip, node, property, values, duration); }
            bool walking = state.IndexOf("Walk", StringComparison.OrdinalIgnoreCase) >= 0;
            bool attack = state.IndexOf("Attack", StringComparison.OrdinalIgnoreCase) >= 0;
            bool death = state.IndexOf("Death", StringComparison.OrdinalIgnoreCase) >= 0;
            float t = s.TorsoPos.y, h = s.HeadPos.y, l = s.LegPos.y;
            // Position is stored as a full Vector3 curve, so an axis left unkeyed is baked as 0.
            // Without these, every left/right part collapses onto the centre line (legs merge into
            // one and the arms sit at x=0, behind the torso) as soon as the Animator plays a state.
            RigCurve("/Torso", "m_LocalPosition.x", new[] { s.TorsoPos.x, s.TorsoPos.x });
            RigCurve("/Head", "m_LocalPosition.x", new[] { s.HeadPos.x, s.HeadPos.x });
            RigCurve("/WingL", "m_LocalPosition.x", new[] { -s.WingPos.x, -s.WingPos.x });
            RigCurve("/WingR", "m_LocalPosition.x", new[] { s.WingPos.x, s.WingPos.x });
            RigCurve("/LegL", "m_LocalPosition.x", new[] { -s.LegPos.x, -s.LegPos.x });
            RigCurve("/LegR", "m_LocalPosition.x", new[] { s.LegPos.x, s.LegPos.x });
            // Same for the z axis and for the arms' height: every axis of a position curve that
            // exists must be keyed, otherwise the unkeyed ones are baked as 0 as well.
            string[] rigNodes = { "", "/Torso", "/Head", "/WingL", "/WingR", "/LegL", "/LegR" };
            for (int i = 0; i < rigNodes.Length; i++)
                RigCurve(rigNodes[i], "m_LocalPosition.z", new[] { 0f, 0f });
            RigCurve("/WingL", "m_LocalPosition.y", new[] { s.WingPos.y, s.WingPos.y });
            RigCurve("/WingR", "m_LocalPosition.y", new[] { s.WingPos.y, s.WingPos.y });
            RigCurve("", "localEulerAnglesRaw.z", death ? new[] { 0f, -12f, -65f, -80f, -80f } : new[] { 0f, 0f });
            RigCurve("", "m_LocalPosition.y", new[] { 0f, 0f });
            RigCurve("/Torso", "m_LocalPosition.y", walking
                ? new[] { t, t + s.TorsoBob, t, t + s.TorsoBob, t } : new[] { t, t + s.TorsoIdleBob, t });
            RigCurve("/Head", "m_LocalPosition.y", walking
                ? new[] { h, h + s.HeadBob, h, h + s.HeadBob, h } : new[] { h, h + s.HeadIdleBob, h });
            RigCurve("/Head", "localEulerAnglesRaw.z", attack
                ? new[] { 0f, -6f, 12f, -5f, 0f } : new[] { 0f, 0f });
            RigCurve("/LegL", "m_LocalPosition.y", walking
                ? new[] { l, l + s.LegStep, l, l, l } : new[] { l, l });
            RigCurve("/LegR", "m_LocalPosition.y", walking
                ? new[] { l, l, l, l + s.LegStep, l } : new[] { l, l });
            RigCurve("/WingL", "localEulerAnglesRaw.z", attack
                ? new[] { 0f, -25f, -40f, -15f, 0f } : walking ? new[] { -3f, 3f, -3f, 3f, -3f } : new[] { 0f, 0f });
            RigCurve("/WingR", "localEulerAnglesRaw.z", attack
                ? new[] { 0f, 25f, 40f, 15f, 0f } : walking ? new[] { 3f, -3f, 3f, -3f, 3f } : new[] { 0f, 0f });
            var settings = AnimationUtility.GetAnimationClipSettings(clip);
            settings.stopTime = duration;
            AnimationUtility.SetAnimationClipSettings(clip, settings);
        }

        private static void Apply(GameObject root, EnemyDirectionalProfile profile, EnemyDirectionSpec s)
        {
            if (!profile.IsComplete) throw new InvalidOperationException("方向配置未完成。");
            var old = root.transform.Find("DirectionVisual");
            if (old) Object.DestroyImmediate(old.gameObject);
            // User art rule: all directions of each newly adapted enemy have no ground shadow.
            // Editor-only removal is reapplied by MonsterPrefabBuilder, with no runtime traversal.
            foreach (var node in root.GetComponentsInChildren<Transform>(true))
                if (node && node != root.transform && node.name == "Shadow")
                    Object.DestroyImmediate(node.gameObject);
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
            visual.Body = Part(motion, "Torso", parts.Body, s.TorsoPos, s.TorsoSize, s.TorsoHeight, 15);
            visual.Head = Part(motion, "Head", parts.NormalHead, s.HeadPos, s.HeadSize, s.HeadHeight, 25);
            visual.WingL = Part(motion, "WingL", parts.Wing, new Vector2(-s.WingPos.x, s.WingPos.y), s.WingSize, s.WingHeight, 20);
            visual.WingR = Part(motion, "WingR", parts.Wing, s.WingPos, s.WingSize, s.WingHeight, 20);
            visual.LegL = Part(motion, "LegL", parts.Leg, new Vector2(-s.LegPos.x, s.LegPos.y), s.LegSize, s.LegHeight, 5);
            visual.LegR = Part(motion, "LegR", parts.Leg, s.LegPos, s.LegSize, s.LegHeight, 5);
            root.GetComponent<Animator>().runtimeAnimatorController = profile.Controller;
            if (s.Name == "AdvancedHen")
            {
                string materialPath = s.ArtDir + "/AdvancedHenFlash.mat";
                var material = AssetDatabase.LoadAssetAtPath<Material>(materialPath);
                if (!material)
                {
                    var shader = AssetDatabase.LoadAssetAtPath<Shader>(s.ArtDir + "/AdvancedHenFlash.shader");
                    if (!shader) throw new InvalidOperationException("AdvancedHen hit-flash shader missing.");
                    material = new Material(shader);
                    AssetDatabase.CreateAsset(material, materialPath);
                }
                foreach (var sr in side) sr.sharedMaterial = material;
                foreach (var sr in new[] { visual.Head, visual.Body, visual.WingL, visual.WingR, visual.LegL, visual.LegR })
                    sr.sharedMaterial = material;
            }
            visual.ResetForSpawn();
        }

        private static SpriteRenderer Part(Transform parent, string name, Sprite sprite, Vector2 position,
            Vector2 size, float fallbackHeight, int order)
        {
            var node = new GameObject(name);
            node.transform.SetParent(parent, false);
            node.transform.localPosition = position;
            // Fit the artwork inside its target box; the source parts were cropped individually,
            // so height-only scaling distorts the head/arms badly. Falls back to the legacy
            // height rule for specs that only define heights (AdvancedHen).
            var pixels = sprite.bounds.size;
            float scale;
            if (size.x > 0.001f && size.y > 0.001f) scale = Mathf.Min(size.x / pixels.x, size.y / pixels.y);
            else if (size.x > 0.001f) scale = size.x / pixels.x;
            else scale = fallbackHeight / pixels.y;
            // Animate the pivot transform; place scale on a leaf so source curves cannot overwrite it.
            var leaf = new GameObject("Sprite");
            leaf.transform.SetParent(node.transform, false);
            leaf.transform.localScale = new Vector3(scale, scale, 1);
            var sr = leaf.AddComponent<SpriteRenderer>();
            sr.sprite = sprite;
            sr.sortingLayerName = BoardSorting.LayerMain;
            sr.sortingOrder = order;
            return sr;
        }

        /// <summary>Editor-time integrity checks; writes a report for unattended runs.</summary>
        public static bool Verify(EnemyDirectionSpec s, out string report)
        {
            if (s.UseSeparateViewRigs) return EnemyDirectionalRigBuilder.Verify(s, out report);
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
                            int dirCurves = 0, total = 0, showcase = 0;
                            foreach (var b in AnimationUtility.GetCurveBindings((AnimationClip)walkUp.motion))
                            {
                                total++;
                                if (b.path.StartsWith("DirectionVisual/")) dirCurves++;
                                if (b.type == typeof(SpriteRenderer)) showcase++;
                            }
                            ok &= Check(lines, "WalkUp clip motion=" + dirCurves + " showcase=" + showcase + " total=" + total,
                                dirCurves >= 9 && showcase > 0);
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
                        if (n != "Walk_Directions")
                        {
                            var rigSr = Root().Find("Torso/Sprite").GetComponent<SpriteRenderer>();
                            var sideSr = temp.transform.Find("Body").GetComponent<SpriteRenderer>();
                            ok &= Check(lines, n + " preview shows vertical rig (rig=" + rigSr.enabled + " side=" + sideSr.enabled + ")",
                                rigSr.enabled && !sideSr.enabled);
                        }
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
