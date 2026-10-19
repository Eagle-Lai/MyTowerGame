using System;
using UnityEngine;

namespace FTProject.AOT
{
    // The only UI/control bridge across the AOT / hot-update boundary.
    public static class BootUpdateSession
    {
        public static string Phase = "Preparing";
        public static string Detail = "";
        public static float Overall;
        public static float Stage = -1;
        public static int Files, TotalFiles;
        public static long Bytes, TotalBytes;
        public static Action Pause, Resume, Retry;
        public static bool Paused;
        public static event Action Changed;

        public static void Report(string phase, float overall, float stage = -1, string detail = "")
        {
            Phase = phase; Overall = Mathf.Clamp01(overall); Stage = stage; Detail = detail ?? "";
            Changed?.Invoke();
        }

        public static void Controls(Action pause = null, Action resume = null, Action retry = null)
        {
            Pause = pause; Resume = resume; Retry = retry;
            Changed?.Invoke();
        }

        public static void Progress(int files, int total, long bytes, long totalBytes)
        {
            Files = files; TotalFiles = total; Bytes = bytes; TotalBytes = totalBytes;
            float p = totalBytes > 0 ? (float)bytes / totalBytes : total > 0 ? (float)files / total : -1;
            Report("Resources", p < 0 ? .45f : .45f + .5f * p, p);
        }
    }
}
