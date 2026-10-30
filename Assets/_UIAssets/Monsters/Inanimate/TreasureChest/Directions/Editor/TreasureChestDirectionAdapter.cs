// Target-only Container adapter. No shared builder, source clip, or runtime C# is modified.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using FTProject;
using UnityEditor;
using UnityEngine;
using Object = UnityEngine.Object;
namespace FTProject.EditorTools
{
    public static class TreasureChestDirectionAdapter
    {
        private static object Builder(string name, params object[] args)
        {
            return typeof(EnemyDirectionalRigBuilder).GetMethod(name, BindingFlags.NonPublic | BindingFlags.Static).Invoke(null, args);
        }
        public static void Build()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode || EditorApplication.isCompiling)
                throw new InvalidOperationException("TreasureChest requires idle Edit mode.");
            EnemyDirectionSpec spec;
            if (!EnemyDirectionalRigBuilder.TryGetSpec("TreasureChest", out spec)
                || spec.PrefabPath != "Assets/Prefabs/Enemy/Enemy_TreasureChest.prefab")
                throw new InvalidOperationException("Unexpected TreasureChest spec.");
            var layout = EnemyDirectionalRigBuilder.ReadLayout(spec);
            string atlasPath = spec.ArtDir + "/TreasureChest_Directions.png";
            var manifest = JsonUtility.FromJson<EnemyDirectionalRigBuilder.Atlas>(File.ReadAllText(spec.ArtDir + "/TreasureChest_Directions.sprites.json"));
            Builder("ValidateManifest", manifest, layout);
            var sprites = (Dictionary<string, Sprite>)Builder("ImportAtlas", atlasPath, manifest);
            Directory.CreateDirectory(spec.AnimDir);
            AssetDatabase.ImportAsset(spec.AnimDir);
            var source = AssetDatabase.LoadAssetAtPath<RuntimeAnimatorController>(spec.ControllerSource);
            var originals = source.animationClips.Distinct().ToDictionary(c => c.name);
            if (originals.Count != 2 || !originals.ContainsKey("Idle") || !originals.ContainsKey("Death"))
                throw new InvalidOperationException("Unexpected Container source; re-inspect before adapting.");
            var clips = new Dictionary<string, AnimationClip>();
            foreach (string action in new[] { "Idle", "Death", "Walk", "Attack" })
            {
                var copy = Object.Instantiate(originals[action == "Death" ? "Death" : "Idle"]);
                copy.name = action + "_Directions";
                if (action == "Walk" || action == "Attack")
                {
                    var settings = AnimationUtility.GetAnimationClipSettings(copy);
                    settings.stopTime = .5f; settings.loopTime = action == "Walk";
                    AnimationUtility.SetAnimationClipSettings(copy, settings);
                }
                EnemyDirectionRemainingMotion.TryAdd(copy, action, layout, sprites);
                if (action == "Death")
                {
                    // Whole-chest vertical art follows the source Container bounce/wobble,
                    // rather than the generic anatomical fall/lid rotation.
                    foreach (var view in layout.views)
                    {
                        string motion = "DirectionVisual/" + view.direction + "/Motion";
                        var y = AnimationUtility.GetEditorCurve(originals["Death"], EditorCurveBinding.FloatCurve("Body", typeof(Transform), "m_LocalPosition.y"));
                        var keys = y.keys;
                        for (int i = 0; i < keys.Length; i++) { keys[i].value = keys[i].value * .4f + layout.referenceBottom + layout.referenceHeight * .5f; keys[i].inTangent *= .4f; keys[i].outTangent *= .4f; }
                        y.keys = keys;
                        AnimationUtility.SetEditorCurve(copy, EditorCurveBinding.FloatCurve(motion, typeof(Transform), "m_LocalPosition.y"), y);
                        var rotation = AnimationUtility.GetEditorCurve(originals["Death"], EditorCurveBinding.FloatCurve("Body", typeof(Transform), "localEulerAnglesRaw.z"));
                        AnimationUtility.SetEditorCurve(copy, EditorCurveBinding.FloatCurve(motion, typeof(Transform), "localEulerAnglesRaw.z"), rotation);
                        AnimationUtility.SetEditorCurve(copy, EditorCurveBinding.FloatCurve(motion + "/Head", typeof(Transform), "localEulerAnglesRaw.z"), AnimationCurve.Constant(0, copy.length, 0));
                    }
                }
                // Original Death float curves remain byte-for-key identical. Non-death clips
                // explicitly restore closed source art after pooling/reuse, since source Idle is empty.
                if (action != "Death")
                {
                    foreach (string axis in new[] { "x", "y", "z" })
                    {
                        AnimationUtility.SetEditorCurve(copy, EditorCurveBinding.FloatCurve("Body", typeof(Transform), "m_LocalPosition." + axis), AnimationCurve.Constant(0, copy.length, 0));
                        AnimationUtility.SetEditorCurve(copy, EditorCurveBinding.FloatCurve("Body", typeof(Transform), "localEulerAnglesRaw." + axis), AnimationCurve.Constant(0, copy.length, 0));
                    }
                    AnimationUtility.SetEditorCurve(copy, EditorCurveBinding.FloatCurve("Body/Normal", typeof(GameObject), "m_IsActive"), AnimationCurve.Constant(0, copy.length, 1));
                    AnimationUtility.SetEditorCurve(copy, EditorCurveBinding.FloatCurve("Body/Broken", typeof(GameObject), "m_IsActive"), AnimationCurve.Constant(0, copy.length, 0));
                }
                if (action == "Death") AnimationUtility.SetAnimationEvents(copy, new[] { new AnimationEvent { functionName = "SetHead", intParameter = 2, time = .03f } });
                if (action == "Attack") AnimationUtility.SetAnimationEvents(copy, new[] {
                    new AnimationEvent { functionName = "SetHead", intParameter = 1, time = .09f },
                    new AnimationEvent { functionName = "SetHead", intParameter = 0, time = .48f }
                });
                string path = spec.AnimDir + "/" + copy.name + ".anim";
                if (AssetDatabase.LoadAssetAtPath<AnimationClip>(path)) throw new InvalidOperationException("Existing clip; use explicit repair revision: " + path);
                AssetDatabase.CreateAsset(copy, path); clips[action] = copy;
            }
            clips["Ready"] = clips["Idle"];
            var profile = ScriptableObject.CreateInstance<EnemyDirectionalProfile>();
            profile.SeparateViewRigs = true;
            profile.Up = new EnemyDirectionalProfile.Parts { NormalHead=sprites["Up_HeadNormal"], AngryHead=sprites["Up_HeadAngry"], DeadHead=sprites["Up_HeadDead"], Body=sprites["Up_Body"] };
            profile.Down = new EnemyDirectionalProfile.Parts { NormalHead=sprites["Down_HeadNormal"], AngryHead=sprites["Down_HeadAngry"], DeadHead=sprites["Down_HeadDead"], Body=sprites["Down_Body"] };
            profile.Controller = EnemyDirectionPrefabBuilder.BuildAdvancedHenController(spec, clips);
            AssetDatabase.CreateAsset(profile, spec.ProfilePath);
            var root = PrefabUtility.LoadPrefabContents(spec.PrefabPath);
            try { EnemyDirectionalRigBuilder.Apply(root, profile, spec); PrefabUtility.SaveAsPrefabAsset(root, spec.PrefabPath); }
            finally { PrefabUtility.UnloadPrefabContents(root); }
            AssetDatabase.SaveAssets();
        }
        // Explicit repair entry: only the two generated vertical lift curves are changed.
        // The opened lid otherwise reaches the unchanged original HP bar during the source-sized hop.
        public static void RepairVerticalDeathLift()
        {
            EnemyDirectionSpec spec; EnemyDirectionalRigBuilder.TryGetSpec("TreasureChest", out spec);
            var layout = EnemyDirectionalRigBuilder.ReadLayout(spec);
            var source = AssetDatabase.LoadAssetAtPath<AnimationClip>("Assets/_UIAssets/Monsters/_Common/Animations/Container/Death.anim");
            var clip = AssetDatabase.LoadAssetAtPath<AnimationClip>(spec.AnimDir + "/Death_Directions.anim");
            if (!clip || EditorApplication.isPlayingOrWillChangePlaymode) throw new InvalidOperationException("Repair requires installed TreasureChest in Edit mode.");
            foreach (var view in layout.views)
            {
                var curve = AnimationUtility.GetEditorCurve(source, EditorCurveBinding.FloatCurve("Body", typeof(Transform), "m_LocalPosition.y"));
                var keys = curve.keys;
                for (int i = 0; i < keys.Length; i++) { keys[i].value = keys[i].value * .4f + layout.referenceBottom + layout.referenceHeight * .5f; keys[i].inTangent *= .4f; keys[i].outTangent *= .4f; }
                curve.keys = keys;
                AnimationUtility.SetEditorCurve(clip, EditorCurveBinding.FloatCurve("DirectionVisual/" + view.direction + "/Motion", typeof(Transform), "m_LocalPosition.y"), curve);
            }
            EditorUtility.SetDirty(clip); AssetDatabase.SaveAssets();
        }
    }
}
