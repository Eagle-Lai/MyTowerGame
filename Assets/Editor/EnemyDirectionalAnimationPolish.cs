using System;
using UnityEditor;
using UnityEngine;

namespace FTProject.EditorTools
{
    // Offline curve authoring only. The existing Animator drives the installed clips;
    // there is no new runtime component, material, update loop or combat displacement.
    internal static class EnemyDirectionalAnimationPolish
    {
        public static bool TryAdd(AnimationClip clip, string action, EnemyDirectionalRigBuilder.Layout layout)
        {
            if (layout.name != "BlackBear" && layout.name != "BlackWolf" && layout.name != "BlueScorpion") return false;
            bool scorpion = layout.name == "BlueScorpion", wolf = layout.name == "BlackWolf";
            bool walk = action == "Walk", attack = action == "Attack", death = action == "Death";
            float duration = Mathf.Max(.01f, clip.length), h = layout.referenceHeight;
            float center = layout.referenceBottom + h * .5f;
            foreach (var view in layout.views)
            {
                float forward = view.direction == "Up" ? 1f : -1f;
                string motion = "DirectionVisual/" + view.direction + "/Motion";
                Func<float, float> recoil = t => Envelope(t, 0, -.025f, -.035f, scorpion ? .045f : wolf ? .09f : .065f, .025f, -.008f, 0, 0);
                Func<float, float> fall = t => Smooth(.10f, .62f, t);
                // The root is visual only. Path movement, HP and hitboxes retain their transforms.
                Set(clip, motion, "m_LocalPosition.x", duration, walk ? (Func<float,float>)(t => h * (scorpion ? .002f : wolf ? .004f : .007f) * Sin(t)) : t => death ? h * .025f * fall(t) : 0, walk);
                Set(clip, motion, "m_LocalPosition.y", duration, t => center + (attack ? forward * h * recoil(t) : death ? -h * .06f * fall(t) : 0), false);
                Constant(clip, motion, "m_LocalPosition.z", duration, 0);
                Set(clip, motion, "localEulerAnglesRaw.z", duration, t => death ? -58f * fall(t) : walk ? (scorpion ? .6f : wolf ? 1.1f : 1.8f) * Sin(t) : attack ? Envelope(t, 0, -2, -4, 3, 1, -1, 0, 0) : .3f * Sin(t), walk || (!attack && !death));
                Set(clip, motion, "m_LocalScale.x", duration, t => death ? 1 + .07f * fall(t) : 1, false);
                Set(clip, motion, "m_LocalScale.y", duration, t => death ? 1 - .24f * fall(t) : 1, false);
                Constant(clip, motion, "m_LocalScale.z", duration, 1);
                foreach (var p in view.parts)
                {
                    string path = motion + "/" + p.name;
                    bool leg = p.role == "leg", tail = p.role == "tail", head = p.role == "head", body = p.role == "body", claw = p.role == "claw";
                    float side = p.flipX ? 1f : -1f;
                    float phase = Phase(p, scorpion, wolf);
                    Func<float,float> swing = t => Mathf.Pow(Mathf.Max(0, Sin(t + phase)), 1.5f);
                    Func<float,float> bob = t => h * (scorpion ? .002f : wolf ? .008f : .005f) * (1 - Mathf.Cos(4 * Mathf.PI * t)) * .5f;
                    // Limb pivots remain inside the torso. A lift shortens the limb about
                    // that fixed joint, rather than translating a detached shoulder cap.
                    Set(clip, path, "m_LocalPosition.x", duration, t => p.x + (attack && head ? h * .006f * Envelope(t, 0, 0, -1, 1, .3f, 0, 0, 0) : 0), false);
                    Set(clip, path, "m_LocalPosition.y", duration, t => p.y - center + (walk ? bob(t) * (head ? .65f : 1) : attack && head ? forward * h * Envelope(t, 0, -.01f, -.018f, .035f, .012f, 0, 0, 0) : !attack && !death ? h * .003f * (1 - Mathf.Cos(2 * Mathf.PI * t)) : 0), walk || (!attack && !death));
                    Constant(clip, path, "m_LocalPosition.z", duration, 0);
                    Set(clip, path, "localEulerAnglesRaw.z", duration, t =>
                    {
                        float angle = p.angle;
                        if (walk)
                        {
                            if (leg) angle += side * (scorpion ? 13f : wolf ? 11f : 8f) * Sin(t + phase);
                            if (tail) angle += (wolf ? 10f : scorpion ? 5f : 5f) * Sin(t - .18f);
                            if (claw) angle += side * (3.5f * Sin(t + (side < 0 ? .08f : .58f)));
                            if (head) angle += (wolf ? 1.2f : .7f) * Sin(t - .12f);
                            if (body) angle -= (scorpion ? .4f : 1f) * Sin(t);
                        }
                        else if (attack)
                        {
                            if (claw) angle += side * forward * Envelope(t, 0, -8, -16, 30, 24, -4, 0, 0);
                            if (tail) angle += Envelope(t, 0, -5, -12, scorpion ? 18 : 9, 5, -4, 0, 0);
                            if (head) angle += Envelope(t, 0, -2, -5, wolf ? 5 : 3, 1, -1, 0, 0);
                            if (leg)
                            {
                                bool fore = p.name.StartsWith("Fore", StringComparison.Ordinal);
                                float strength = scorpion ? 8 : fore ? (wolf ? 16 : 22) : 5;
                                float delay = !scorpion && !wolf && side > 0 && fore ? .09f : 0;
                                angle += side * Envelope(Mathf.Clamp01(t - delay), 0, -4, -10, strength, strength * .5f, -3, 0, 0);
                            }
                        }
                        else if (death)
                        {
                            if (leg) angle += side * (scorpion ? -35 : 24) * fall(t);
                            if (claw) angle += side * forward * 30 * fall(t);
                            if (tail) angle += (scorpion ? -23 : -18) * fall(t);
                            if (head) angle += 12 * fall(t);
                        }
                        else if (tail || claw) angle += (tail ? 2f : side * 1.2f) * Sin(t - .18f);
                        return angle;
                    }, walk || (!attack && !death));
                    Constant(clip, path, "m_LocalScale.x", duration, 1);
                    Set(clip, path, "m_LocalScale.y", duration, t =>
                    {
                        if (walk && leg) return 1 - (scorpion ? .12f : wolf ? .23f : .16f) * swing(t);
                        if (attack && leg)
                        {
                            bool fore = p.name.StartsWith("Fore", StringComparison.Ordinal);
                            return 1 + Envelope(t, 0, -.03f, -.10f, fore ? .10f : -.04f, .025f, -.02f, 0, 0);
                        }
                        if (attack && tail && scorpion) return 1 + Envelope(t, 0, -.02f, -.08f, .05f, -.05f, 0, 0, 0);
                        if (death && leg) return 1 - (scorpion ? .24f : .30f) * fall(t);
                        return 1;
                    }, walk);
                    Constant(clip, path, "m_LocalScale.z", duration, 1);
                }
            }
            var settings = AnimationUtility.GetAnimationClipSettings(clip);
            settings.stopTime = duration;
            AnimationUtility.SetAnimationClipSettings(clip, settings);
            return true;
        }

        private static float Phase(EnemyDirectionalRigBuilder.Part p, bool scorpion, bool wolf)
        {
            if (scorpion)
                return p.phase * .5f + (p.name.Contains("Front") ? .04f : p.name.Contains("Back") ? -.04f : 0);
            if (wolf) return p.phase * .5f;
            // A rolling four-beat walk for the bear, diagonal pairs for the wolf.
            if (p.name == "ForeL") return 0;
            if (p.name == "HindL") return .65f;
            if (p.name == "ForeR") return .5f;
            if (p.name == "HindR") return .15f;
            return 0;
        }

        private static float Sin(float phase) { return Mathf.Sin(2 * Mathf.PI * phase); }
        private static float Smooth(float start, float end, float t) { return Mathf.SmoothStep(0, 1, Mathf.InverseLerp(start, end, t)); }
        private static readonly float[] AttackTimes = { 0, .12f, .25f, .36f, .48f, .66f, .84f, 1 };
        private static float Envelope(float t, params float[] values)
        {
            for (int i = 1; i < AttackTimes.Length; i++)
                if (t <= AttackTimes[i]) return Mathf.Lerp(values[i-1], values[i], Smooth(AttackTimes[i-1], AttackTimes[i], t));
            return values[values.Length-1];
        }
        private static void Constant(AnimationClip clip, string path, string property, float duration, float value)
        {
            AnimationUtility.SetEditorCurve(clip, EditorCurveBinding.FloatCurve(path, typeof(Transform), property),
                new AnimationCurve(new Keyframe(0, value), new Keyframe(duration, value)));
        }
        private static void Set(AnimationClip clip, string path, string property, float duration, Func<float,float> sample, bool cyclic)
        {
            const int segments = 64;
            const float epsilon = .0005f;
            var keys = new Keyframe[segments+1];
            for (int i = 0; i <= segments; i++)
            {
                float t = (float)i / segments;
                float left = cyclic ? t-epsilon : Mathf.Max(0, t-epsilon);
                float right = cyclic ? t+epsilon : Mathf.Min(1, t+epsilon);
                float tangent = (sample(right)-sample(left)) / ((right-left)*duration);
                keys[i] = new Keyframe(t*duration, sample(t), tangent, tangent);
            }
            bool constant = true;
            for (int i = 0; i < keys.Length; i++)
                if (Mathf.Abs(keys[i].value-keys[0].value) > .000001f || Mathf.Abs(keys[i].inTangent) > .000001f) { constant = false; break; }
            if (constant) { Constant(clip, path, property, duration, keys[0].value); return; }
            var curve = new AnimationCurve(keys);
            AnimationUtility.SetEditorCurve(clip, EditorCurveBinding.FloatCurve(path, typeof(Transform), property), curve);
        }
    }
}
