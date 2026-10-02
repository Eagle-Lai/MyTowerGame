using System.Text;
using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 性能探针（M5-3）：滚动统计帧时间，随时打印一份可读报告。
    ///
    /// 【它解决什么问题】设计文档 M5 要求"低端机 200 怪 + 50 塔稳定 60fps"，
    /// 而那必须真机跑。但没有度量就没法判断"够不够快" ——
    /// 本探针把"手感"变成数字（p50 / p95 / p99 / 最差帧 / GC 增量），
    /// 于是压测只需要：真机跑一局 → 按 F3 → 把日志贴出来。
    ///
    /// 【为什么用环形缓冲而不是 List】每帧 Add 会持续分配；
    /// 固定数组 + 覆盖写是零分配的，也不会有"跑久了内存越来越大"的问题。
    ///
    /// 【为什么用 unscaledDeltaTime】暂停时 timeScale=0，用 scaled 时间会得到一堆 0 帧，
    /// 把统计彻底污染（而那恰好是玩家最可能按 F3 的时刻之一）。
    ///
    /// 快捷键：F3 打印报告（由 GameFlowManager 绑定）
    /// </summary>
    public class PerfProbe : MonoBehaviour
    {
        public static PerfProbe Instance { get; private set; }

        /// <summary>采样窗口：600 帧 ≈ 60fps 下的 10 秒</summary>
        private const int Capacity = 600;

        /// <summary>自动打印间隔（秒）。0 = 只在按 F3 时打印。</summary>
        public float autoReportIntervalSec = 0f;

        private readonly float[] _frameMs = new float[Capacity];
        private readonly float[] _scratch = new float[Capacity];
        private int _idx;
        private int _count;
        private float _autoTimer;
        private long _lastGcBytes;
        private long _gcDelta;
        private float _worstSinceReport;

        public static PerfProbe Ensure()
        {
            if (Instance != null)
            {
                return Instance;
            }
            GameObject go = new GameObject("PerfProbe");
            if (Launcher.Instance != null)
            {
                go.transform.SetParent(Launcher.Instance.transform, false);
            }
            return go.AddComponent<PerfProbe>();
        }

        private void Awake()
        {
            Instance = this;
            _lastGcBytes = System.GC.GetTotalMemory(false);
        }

        private void OnDestroy()
        {
            if (Instance == this)
            {
                Instance = null;
            }
        }

        private void Update()
        {
            float ms = Time.unscaledDeltaTime * 1000f;
            _frameMs[_idx] = ms;
            _idx = (_idx + 1) % Capacity;
            if (_count < Capacity)
            {
                _count++;
            }
            if (ms > _worstSinceReport)
            {
                _worstSinceReport = ms;
            }

            if (autoReportIntervalSec > 0f)
            {
                _autoTimer += Time.unscaledDeltaTime;
                if (_autoTimer >= autoReportIntervalSec)
                {
                    _autoTimer = 0f;
                    Debug.Log(Report());
                }
            }
        }

        /// <summary>生成一份报告。排序用的是复用数组，调用本身不产生垃圾。</summary>
        public string Report()
        {
            if (_count == 0)
            {
                return "[Perf] 还没有采到帧";
            }

            System.Array.Copy(_frameMs, _scratch, _count);
            System.Array.Sort(_scratch, 0, _count);

            float p50 = _scratch[Mathf.Clamp(Mathf.RoundToInt(_count * 0.50f) - 1, 0, _count - 1)];
            float p95 = _scratch[Mathf.Clamp(Mathf.RoundToInt(_count * 0.95f) - 1, 0, _count - 1)];
            float p99 = _scratch[Mathf.Clamp(Mathf.RoundToInt(_count * 0.99f) - 1, 0, _count - 1)];
            float worst = _scratch[_count - 1];

            float sum = 0f;
            for (int i = 0; i < _count; i++)
            {
                sum += _scratch[i];
            }
            float avg = sum / _count;

            long now = System.GC.GetTotalMemory(false);
            _gcDelta = now - _lastGcBytes;
            _lastGcBytes = now;

            CombatSystem cs = CombatSystem.Instance;
            StringBuilder sb = new StringBuilder(320);
            sb.Append("[Perf] 采样 ").Append(_count).Append(" 帧");
            sb.Append("\n  平均 ").Append(avg.ToString("F2")).Append(" ms（").Append((1000f / Mathf.Max(0.01f, avg)).ToString("F1")).Append(" fps）");
            sb.Append("\n  p50 ").Append(p50.ToString("F2")).Append(" / p95 ").Append(p95.ToString("F2"))
              .Append(" / p99 ").Append(p99.ToString("F2")).Append(" / 最差 ").Append(worst.ToString("F2")).Append(" ms");
            sb.Append("\n  本轮最差 ").Append(_worstSinceReport.ToString("F2")).Append(" ms");
            sb.Append("\n  托管堆增量 ").Append((_gcDelta / 1024f).ToString("F0")).Append(" KB");
            if (cs != null)
            {
                sb.Append("\n  战斗：怪 ").Append(cs.EnemyCount).Append("（存活 ").Append(cs.AliveEnemyCount)
                  .Append("） 塔 ").Append(cs.TowerCount).Append(" 弹 ").Append(cs.BulletCount);
                sb.Append("\n  自检：索敌 ").Append(cs.StatSearchCount).Append(" 开火 ").Append(cs.StatFireCount)
                  .Append(" 命中 ").Append(cs.StatHitCount).Append(" 空放 ").Append(cs.StatIdleFireAttempt)
                  .Append("（空放必须为 0）");
            }
            sb.Append("\n  判定：p95 ≤ 16.7ms 才算稳 60fps；托管堆增量接近 0 才算无泄漏式分配");

            _worstSinceReport = 0f;
            return sb.ToString();
        }
    }
}
