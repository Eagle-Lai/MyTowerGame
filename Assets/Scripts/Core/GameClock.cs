using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 全局模拟时钟（P2b 新增）——**全工程唯一的速度源**。
    ///
    /// 【为什么要一个独立的速度参数，而不是直接用 Time.timeScale】
    ///   `Time.timeScale` 在本工程里语义已经被**收窄为"暂停开关"**（只允许 0 / 1）。
    ///   若拿它做倍速，会连带影响所有 unscaled 之外的系统：UI 动画、相机震动、
    ///   对象池回收倒计时…… 全都会一起变快，而它们本该是"实时"的。
    ///   所以倍速走独立的 <see cref="Speed"/> 参数，只有真正参与"模拟推进"的系统
    ///   才消费 <see cref="DeltaTime"/>（消费清单见策划案 §7.3.1）。
    ///
    /// 【同帧同值：DeltaTime 必须只有一份】
    ///   如果各系统各自写 `Time.deltaTime * GameClock.Speed`，同一帧里不同系统读到的
    ///   Speed 可能不同（改档恰好发生在两帧之间），表现为"怪物走一步、塔的 CD 少两格"。
    ///   因此 DeltaTime 按**帧号**缓存：同帧内无论谁先取、谁取几次，拿到的都是同一个值。
    ///
    /// 【为什么用帧号惰性缓存，而不是只靠 Tick() 主动刷新】
    ///   Unity 不保证 `Launcher.Update`（驱动 CombatSystem）与 `GameFlowManager.Update`
    ///   的先后顺序。若只靠 GameFlowManager.Update 里调 Tick()，一旦它的 Update 排在后面，
    ///   本帧的模拟就会用到上一帧的缓存值（首帧甚至可能是 0）。
    ///   用帧号做键后，"谁先取谁负责算"，执行顺序就完全无关紧要了 —— Tick() 仍然保留，
    ///   当作一个"提前算好"的显式入口（也满足程序案里对 Tick() 的要求）。
    ///
    /// 【暂停怎么走】暂停仍然靠 `Time.timeScale = 0`：此时 `Time.deltaTime` 为 0，
    ///   于是 DeltaTime 也为 0，全部模拟自然停摆 —— 倍速与暂停是两条互不写入的通道。
    /// </summary>
    public static class GameClock
    {
        /// <summary>
        /// 合法档位。**只有这里定义一次**：HudView 的"循环切档"与 GameFlowManager 的
        /// "档位合法性校验"都读它，避免两处各写一份 1/2/3 而改一处漏一处。
        /// 需要"降档"（例如 ×3 帧率不达标改 ×2.5）时，只改这里一个数字即可，结构不变。
        /// </summary>
        public static readonly float[] Tiers = { 1f, 2f, 3f };

        private static float _speed = 1f;

        private static float _cachedDelta;
        private static int _cachedFrame = -1;

        /// <summary>
        /// 当前模拟速度倍率（默认 1）。
        /// 设 0 或负数会静默回落到 1 —— 0 会让整个世界无声冻结，是极难排查的状态，
        /// 宁可忽略这次非法写入。
        /// </summary>
        public static float Speed
        {
            get { return _speed; }
            set { _speed = value > 0f ? value : 1f; }
        }

        /// <summary>
        /// 本帧的模拟步长 = `Time.deltaTime × Speed`。同帧内恒为同一个值。
        /// 所有"参与模拟推进"的系统都从这里取时间，而不是自己乘 Speed。
        /// </summary>
        public static float DeltaTime
        {
            get
            {
                if (_cachedFrame != Time.frameCount)
                {
                    _cachedFrame = Time.frameCount;
                    _cachedDelta = Time.deltaTime * _speed;
                }
                return _cachedDelta;
            }
        }

        /// <summary>显式刷新本帧缓存值（调用时机不敏感，见类注释）。</summary>
        public static void Tick()
        {
            _cachedFrame = Time.frameCount;
            _cachedDelta = Time.deltaTime * _speed;
        }

        /// <summary>回到 ×1（GameOver / 重开 / 回选关 / 进 Loading 时必须调用）。</summary>
        public static void Reset()
        {
            _speed = 1f;
            _cachedFrame = -1;   // 强制下一次取值重算，避免残留上一帧缓存
        }

        /// <summary>是否是一个合法档位（用于校验来自 UI 的请求，防止越界值）。</summary>
        public static bool IsValidTier(float value)
        {
            for (int i = 0; i < Tiers.Length; i++)
            {
                if (Mathf.Approximately(Tiers[i], value))
                {
                    return true;
                }
            }
            return false;
        }

        /// <summary>取当前档位的下一档（循环：×1→×2→×3→×1）。当前值不在档位表里时回落到第一档。</summary>
        public static float NextTier(float current)
        {
            for (int i = 0; i < Tiers.Length; i++)
            {
                if (Mathf.Approximately(Tiers[i], current))
                {
                    return Tiers[(i + 1) % Tiers.Length];
                }
            }
            return Tiers[0];
        }
    }
}
