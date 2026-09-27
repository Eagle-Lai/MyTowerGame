using System.Collections.Generic;
using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 波次管理器（P0-8）。
    ///
    /// 【设计要点】把"回合 → 多个波次编组 → 每组的若干怪物与间隔"在回合开始时
    /// **一次性展开成一条扁平的 (时刻, 怪物id) 时间轴**，之后只用一个累加计时器推进。
    ///
    /// 为什么不用每只怪一个 TimerManager 定时器：
    ///   v1.0 用 `TimerManager.AddTimer(interval, count, cb)` 递归补时，
    ///   一波 40 只怪就是 40 个定时器，且 TimerManager 用 `Time.fixedDeltaTime` 驱动
    ///   （Launcher 里传的正是 fixedDeltaTime），改帧率后波次节奏会漂。
    ///   单计时器 + 时间轴是 O(n) 且与帧率无关。
    ///
    /// 【单位】时间轴统一用秒（表里是毫秒，展开时换算）。
    /// </summary>
    public class WaveManager
    {
        /// <summary>时间轴上的一个出生点</summary>
        private struct SpawnEntry
        {
            public float TimeSec;
            public int EnemyId;
            /// <summary>所属波次编组在回合内的序号（从 0 计）</summary>
            public int GroupIndex;
        }

        private readonly List<SpawnEntry> _timeline = new List<SpawnEntry>(256);
        private readonly List<float> _groupStartTime = new List<float>(16);
        private readonly List<bool> _groupCleared = new List<bool>(16);

        private RoundConfig _round;
        private float _timer;
        private int _cursor;
        private bool _running;
        private bool _allSpawned;

        public bool IsRunning { get { return _running; } }
        public bool AllSpawned { get { return _allSpawned; } }
        public int SpawnedCount { get { return _cursor; } }
        public int TotalCount { get { return _timeline.Count; } }
        public int GroupCount { get { return _groupStartTime.Count; } }
        public RoundConfig Round { get { return _round; } }

        /// <summary>当前波次序号（从 0 计，供 UI 显示）</summary>
        public int CurrentGroupIndex { get; private set; }

        /// <summary>时间轴总时长（秒），供 UI 显示进度</summary>
        public float TotalDurationSec
        {
            get { return _timeline.Count > 0 ? _timeline[_timeline.Count - 1].TimeSec : 0f; }
        }

        // ------------------------------------------------------------------
        // 回合开始
        // ------------------------------------------------------------------

        /// <summary>
        /// 开始一个回合：展开时间轴并复位。
        /// 若配置有缺失（例如某波次 id 不存在），跳过该组并告警，不阻塞其余内容 ——
        /// 符合"功能缺失不应阻塞实现"的要求。
        /// </summary>
        public void BeginRound(RoundConfig round)
        {
            _round = round;
            _timeline.Clear();
            _groupStartTime.Clear();
            _groupCleared.Clear();
            _timer = 0f;
            _cursor = 0;
            _allSpawned = false;
            CurrentGroupIndex = 0;

            if (round == null || round.WaveIds == null || round.WaveIds.Count == 0)
            {
                Debug.LogWarning("[Wave] 回合配置为空，本回合不会有怪物");
                _running = false;
                _allSpawned = true;
                return;
            }

            // 回合自身的准备时间（StartDelayMs）作为时间轴起点
            float offset = round.StartDelayMs > 0 ? round.StartDelayMs / 1000f : 0f;
            int groupIndex = 0;

            for (int i = 0; i < round.WaveIds.Count; i++)
            {
                int waveId = round.WaveIds[i];
                WaveGroupConfig group = Configs.GetWaveGroup(waveId);
                if (group == null || group.EnemyIds == null || group.EnemyIds.Count == 0)
                {
                    Debug.LogWarning(string.Format(
                        "[Wave] 回合 {0} 的第 {1} 个波次（id={2}）无有效怪物，已跳过", round.Id, i, waveId));
                    continue;
                }

                // 相对回合开始的绝对时刻
                float groupStart = offset + group.StartDelayMs / 1000f;
                float gap = group.SpawnIntervalSec;

                _groupStartTime.Add(groupStart);
                _groupCleared.Add(false);

                for (int k = 0; k < group.EnemyIds.Count; k++)
                {
                    SpawnEntry e;
                    e.TimeSec = groupStart + gap * k;
                    e.EnemyId = group.EnemyIds[k];
                    e.GroupIndex = groupIndex;
                    _timeline.Add(e);
                }

                // 下一组的偏移以本组结束时间为基准（各组 Interval 通常已是相对回合开始，
                // 这里取"本组最后一只是时刻 + 一个间隔"与"下一组自身延迟"的最大值，避免重叠）
                float groupEnd = groupStart + gap * Mathf.Max(1, group.EnemyIds.Count - 1);
                offset = Mathf.Max(offset, groupEnd + gap);
                groupIndex++;
            }

            if (_timeline.Count == 0)
            {
                Debug.LogWarning(string.Format("[Wave] 回合 {0} 展开后没有任何怪物", round.Id));
                _running = false;
                _allSpawned = true;
                return;
            }

            _timeline.Sort(CompareEntry);
            _running = true;

            Debug.Log(string.Format(
                "[Wave] 回合 {0} 开始：{1} 个波次 / {2} 只怪 / 时间轴 {3:F1} 秒",
                round.Id, _groupStartTime.Count, _timeline.Count, TotalDurationSec));
        }

        private static int CompareEntry(SpawnEntry a, SpawnEntry b)
        {
            return a.TimeSec.CompareTo(b.TimeSec);
        }

        public void Stop()
        {
            _running = false;
        }

        // ------------------------------------------------------------------
        // 推进
        // ------------------------------------------------------------------

        /// <summary>推进计时器并按时间轴生成怪物</summary>
        public void Tick(float dt)
        {
            if (!_running)
            {
                return;
            }

            _timer += dt;

            while (_cursor < _timeline.Count && _timer >= _timeline[_cursor].TimeSec)
            {
                SpawnEntry e = _timeline[_cursor];

                // 进入新的波次编组 → 广播（HUD 可据此显示"第 N 波"）
                if (e.GroupIndex != CurrentGroupIndex)
                {
                    CurrentGroupIndex = e.GroupIndex;
                    EventDispatcher.TriggerEvent<int>(EventName.WaveStartEvent, CurrentGroupIndex + 1);
                }

                EnemyManager.Instance.Spawn(e.EnemyId);
                _cursor++;
            }

            if (_cursor >= _timeline.Count)
            {
                _allSpawned = true;
                _running = false;
            }
        }

        /// <summary>
        /// 回合是否已结束：全部出生完毕且场上无存活怪物。
        /// aliveCount 由调用方传入（取自 CombatSystem），避免本类依赖战斗系统。
        /// </summary>
        public bool IsRoundFinished(int aliveCount)
        {
            return _allSpawned && aliveCount <= 0;
        }

        /// <summary>
        /// 检查并广播波次清空。
        /// 判定：该组的怪已全部出生 且 场上无存活（简单可靠，M0 够用）。
        /// </summary>
        public void CheckGroupCleared(int aliveCount)
        {
            if (aliveCount > 0 || _timeline.Count == 0)
            {
                return;
            }
            for (int g = 0; g < _groupCleared.Count; g++)
            {
                if (_groupCleared[g])
                {
                    continue;
                }
                // 该组是否还有未出生的怪
                bool fullySpawned = true;
                for (int i = 0; i < _timeline.Count; i++)
                {
                    if (_timeline[i].GroupIndex == g && i >= _cursor)
                    {
                        fullySpawned = false;
                        break;
                    }
                }
                if (fullySpawned)
                {
                    _groupCleared[g] = true;
                    EventDispatcher.TriggerEvent<int>(EventName.WaveClearEvent, g + 1);
                }
            }
        }

        public string DumpDebugInfo()
        {
            return string.Format("[Wave] 回合={0} 波次={1} 已出生={2}/{3} 波内序号={4} 运行中={5}",
                _round != null ? _round.Id : 0, _groupStartTime.Count,
                _cursor, _timeline.Count, CurrentGroupIndex + 1, _running);
        }
    }
}
