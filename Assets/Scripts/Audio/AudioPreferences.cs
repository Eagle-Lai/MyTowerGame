using System;
using UnityEngine;

namespace FTProject
{
    /// <summary>Optional versioned payload: null/unknown version is a legacy silent save, zero is a real volume.</summary>
    [Serializable]
    public sealed class AudioPreferences
    {
        public int version;
        public float master;
        public float music;
        public float sfx;
        public bool muted;

        public static AudioPreferences Defaults()
        {
            return new AudioPreferences { version = 1, master = .8f, music = .65f, sfx = .8f };
        }

        public static AudioPreferences Normalize(AudioPreferences value)
        {
            if (value == null || value.version != 1) return Defaults();
            return new AudioPreferences { version = 1, master = Valid(value.master, .8f),
                music = Valid(value.music, .65f), sfx = Valid(value.sfx, .8f), muted = value.muted };
        }

        private static float Valid(float value, float fallback)
        {
            return float.IsNaN(value) || float.IsInfinity(value) ? fallback : Mathf.Clamp01(value);
        }
    }
}
