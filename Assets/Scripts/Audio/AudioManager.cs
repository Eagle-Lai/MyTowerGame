using UnityEngine;

namespace FTProject
{
    public sealed class AudioManager : BaseManager<AudioManager>
    {
        public override void OnInit()
        {
            if (AudioRuntime.Current != null) return;
            var root = new GameObject("GameAudio");
            Object.DontDestroyOnLoad(root);
            root.AddComponent<AudioRuntime>();
        }

        public override void OnDestroy()
        {
            if (AudioRuntime.Current != null)
            {
                AudioRuntime.Current.Shutdown();
                Object.Destroy(AudioRuntime.Current.gameObject);
            }
        }
    }

    /// <summary>Notifications never create services, block gameplay, or consume combat random numbers.</summary>
    public static class GameAudio
    {
        public static void Play(SoundCue cue) { if (AudioRuntime.Current != null) AudioRuntime.Current.Play(cue); }
        public static void EnemyHit(BaseEnemy enemy) { if (AudioRuntime.Current != null) AudioRuntime.Current.EnemyHit(enemy); }
        public static void FrostPulse(BaseTower tower) { if (AudioRuntime.Current != null) AudioRuntime.Current.FrostPulse(tower); }
        public static void BeginLevel() { if (AudioRuntime.Current != null) AudioRuntime.Current.BeginLevel(); }
        public static void EndLevel() { if (AudioRuntime.Current != null) AudioRuntime.Current.EndLevel(); }
        public static void CancelRating() { if (AudioRuntime.Current != null) AudioRuntime.Current.CancelRating(); }
        public static void ApplySettings() { if (AudioRuntime.Current != null) AudioRuntime.Current.ApplySettings(); }
    }
}
