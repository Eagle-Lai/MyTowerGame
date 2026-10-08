using System.IO;
using UnityEditor;
using UnityEngine;

namespace FTProject.EditorTools
{
    /// <summary>
    /// 程序合成"选关界面"BGM 的占位音源（P3）。
    ///
    /// 【为什么需要它】外部素材里只有 1 首战斗音乐（Tracks/Track1），而规格要求 2 首 BGM
    ///   （选关 / 战斗）。与其等美术或冒版权风险去下歌，不如按"程序生成占位美术"的同一思路
    ///   合成一段**能听、可循环、无版权**的环境铺底。
    ///
    /// 【为什么"无缝循环"不是靠淡化】把正弦频率**吸附到 1/loopLength 的整数倍**，
    ///   整个波形在循环点天然连续（相位对齐），不需要淡入淡出。
    ///   和弦切换用循环互淡（第 4 个和弦的尾巴淡向第 1 个和弦），跨循环点也连续。
    ///
    /// 输出：Assets/Audio/BGM/bgm_select.wav（12s / 44.1kHz / 单声道 16bit）
    /// 菜单：Tools ▸ 塔防 ▸ 高级（单步重建）▸ 生成占位 BGM
    /// </summary>
    public static class PlaceholderBgmGenerator
    {
        private const string OutPath = "Assets/Audio/BGM/bgm_select.wav";
        private const int SampleRate = 44100;
        private const float LoopSeconds = 12f;

        [MenuItem("Tools/塔防/高级（单步重建）/生成占位 BGM（选关）", false, 307)]
        public static void GenerateFromMenu()
        {
            EditorUtil.Report report = new EditorUtil.Report();
            GenerateAll(report);
            EditorUtility.DisplayDialog("生成占位 BGM", report.Text, "好");
        }

        [MenuItem("Tools/塔防/自动化（无弹窗）/生成占位 BGM（选关）", false, 904)]
        public static void GenerateNoDialog()
        {
            EditorUtil.Report report = new EditorUtil.Report();
            GenerateAll(report);
            Debug.Log("[BGM] 占位 BGM 生成结果：\n" + report.Text);
        }

        public static void GenerateAll(EditorUtil.Report report)
        {
            report.Head("生成占位 BGM → " + OutPath);
            EditorUtil.EnsureFolderOfFile(OutPath);

            float[] pcm = Synthesize();
            WriteWav(OutPath, pcm, SampleRate);
            AssetDatabase.ImportAsset(OutPath, ImportAssetOptions.ForceUpdate);

            report.Ok(string.Format("bgm_select.wav  ({0:0.0}s / {1}Hz / 单声道 16bit / 无缝循环)",
                LoopSeconds, SampleRate));
        }

        // 四个和弦：Am - F - C - G（每个 3 秒）
        private static readonly float[][] ChordNotes =
        {
            new[] { 220.00f, 261.63f, 329.63f },   // Am
            new[] { 174.61f, 220.00f, 261.63f },   // F
            new[] { 261.63f, 329.63f, 392.00f },   // C
            new[] { 196.00f, 246.94f, 293.66f },   // G
        };

        private static readonly float[] ChordBass = { 110.00f, 87.31f, 130.81f, 98.00f };

        private static float[] Synthesize()
        {
            int total = Mathf.RoundToInt(SampleRate * LoopSeconds);
            float[] data = new float[total];

            float grid = 1f / LoopSeconds;          // 频率吸附网格
            float chordLen = LoopSeconds / ChordNotes.Length;
            const float xf = 0.55f;                 // 和弦互淡时长（秒）
            float lfo = 3f * grid;                  // 0.25Hz 颤音，恰好 3 个周期 → 循环相位对齐
            float twoPi = Mathf.PI * 2f;

            for (int n = 0; n < total; n++)
            {
                float t = n / (float)SampleRate;
                float p = t / chordLen;
                int idx = Mathf.FloorToInt(p) % ChordNotes.Length;
                float frac = p - Mathf.Floor(p);

                // 循环互淡：靠近结尾时把权重交给下一个和弦（首尾都在网格上，故跨界连续）
                float wNext = 0f;
                if (frac > (1f - xf / chordLen))
                {
                    wNext = (frac - (1f - xf / chordLen)) / (xf / chordLen);
                }
                int next = (idx + 1) % ChordNotes.Length;

                float v = (1f - wNext) * ChordValue(idx, t, grid, twoPi)
                        + wNext * ChordValue(next, t, grid, twoPi);

                // 颤音（周期性）
                v *= 0.82f + 0.18f * Mathf.Sin(twoPi * lfo * t);

                data[n] = v;
            }

            // 归一化到 -0.85，避免削波
            float peak = 0f;
            for (int i = 0; i < data.Length; i++)
            {
                peak = Mathf.Max(peak, Mathf.Abs(data[i]));
            }
            if (peak > 0.0001f)
            {
                float g = 0.85f / peak;
                for (int i = 0; i < data.Length; i++)
                {
                    data[i] *= g;
                }
            }
            return data;
        }

        /// <summary>单个和弦在 t 时刻的采样值（三和音 + 低音）</summary>
        private static float ChordValue(int idx, float t, float grid, float twoPi)
        {
            float v = 0f;
            float[] notes = ChordNotes[idx];
            for (int i = 0; i < notes.Length; i++)
            {
                // 频率吸附到 1/loopLength 的整数倍 → 波形在循环点相位连续
                float f = Snap(notes[i], grid);
                float detune = Snap(notes[i] * 1.0035f, grid);   // 轻微失谐，pad 更厚
                v += 0.30f * Mathf.Sin(twoPi * f * t + i * 0.7f);
                v += 0.18f * Mathf.Sin(twoPi * detune * t + i * 1.9f);
            }
            float bass = Snap(ChordBass[idx], grid);
            v += 0.42f * Mathf.Sin(twoPi * bass * t);
            return v * 0.5f;
        }

        private static float Snap(float freq, float grid)
        {
            float k = Mathf.Max(1f, Mathf.Round(freq / grid));
            return k * grid;
        }

        // ------------------------------------------------------------------
        // WAV 写出（RIFF / PCM 16bit 单声道）
        // ------------------------------------------------------------------

        private static void WriteWav(string path, float[] samples, int sampleRate)
        {
            using (MemoryStream ms = new MemoryStream())
            using (BinaryWriter w = new BinaryWriter(ms))
            {
                int dataBytes = samples.Length * 2;

                w.Write(new[] { 'R', 'I', 'F', 'F' });
                w.Write(36 + dataBytes);
                w.Write(new[] { 'W', 'A', 'V', 'E' });
                w.Write(new[] { 'f', 'm', 't', ' ' });
                w.Write(16);                       // fmt chunk size
                w.Write((short)1);                 // PCM
                w.Write((short)1);                 // 单声道
                w.Write(sampleRate);
                w.Write(sampleRate * 2);           // byte rate = rate * channels * bits/8
                w.Write((short)2);                 // block align
                w.Write((short)16);                // bits per sample
                w.Write(new[] { 'd', 'a', 't', 'a' });
                w.Write(dataBytes);

                for (int i = 0; i < samples.Length; i++)
                {
                    short s = (short)Mathf.Clamp(Mathf.RoundToInt(samples[i] * 32767f), -32768, 32767);
                    w.Write(s);
                }
                w.Flush();
                File.WriteAllBytes(path, ms.ToArray());
            }
        }
    }
}
