using System;
using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// BGM 交叉淡入淡出驱动（M4-W7）。
    ///
    /// 【为什么要单独一个 MonoBehaviour】
    ///   `AudioManager` 继承 `BaseManager&lt;T&gt;`，是**纯 C# 单例，没有 Update**。
    ///   而淡入淡出必须逐帧推进。所以把"逐帧的那部分"抽成本组件，
    ///   挂在 AudioRoot 上（它挂在 Launcher 下，DontDestroyOnLoad，跨场景常驻）。
    ///
    /// 【为什么只保存"系数"而不是直接改 AudioSource.volume】
    ///   实际音量 = 基准音量(TBAudio) × 本驱动的淡入淡出系数 × 主音量 × (静音?0:1)。
    ///   如果本驱动直接写 `AudioSource.volume`，那么玩家在设置里调音量 / 切静音时，
    ///   会和正在进行的淡化**互相覆盖**（表现为"调了音量又自己弹回去"）。
    ///   所以本驱动只维护 0~1 的系数，绝对音量统一由 AudioManager 计算 —— 单一写入方。
    ///
    /// 【两个槽】A/B 两槽分别对应换曲前的旧曲与换曲后的新曲：
    ///   新曲 0→1、旧曲 1→0 同时进行，就是"交叉淡化"；任一时刻最多只有两首在播。
    ///
    /// 【时间口径】用 `unscaledDeltaTime`：暂停界面把 `Time.timeScale` 设成 0，
    ///   若用缩放时间，淡化会连同游戏一起冻住（音量卡在半途，恢复时听感突兀）。
    /// </summary>
    public class AudioFadeDriver : MonoBehaviour
    {
        /// <summary>交叉淡化用的槽数（旧曲 / 新曲）。</summary>
        public const int Slots = 2;

        private readonly float[] _cur = new float[Slots];
        private readonly float[] _from = new float[Slots];
        private readonly float[] _target = new float[Slots];

        private float _elapsed;
        private float _duration;
        private bool _running;

        /// <summary>系数发生变化时触发，AudioManager 借此重算实际音量。</summary>
        public event Action Changed;

        /// <summary>一次过渡结束时触发（用于停掉旧槽、完成 StopBgm）。</summary>
        public event Action Finished;

        /// <summary>当前过渡是否在进行中。</summary>
        public bool Running { get { return _running; } }

        /// <summary>取某槽当前的淡入淡出系数（0~1）。越界返回 1（不淡）。</summary>
        public float Scale(int slot)
        {
            return (slot >= 0 && slot < Slots) ? _cur[slot] : 1f;
        }

        /// <summary>
        /// 直接把某槽设成给定系数，**不产生过渡**。
        /// 用途：新曲开始播放前先归零，避免它以上一次的残留音量"闪一下"。
        /// </summary>
        public void Prime(int slot, float value)
        {
            if (slot < 0 || slot >= Slots)
            {
                return;
            }
            value = Mathf.Clamp01(value);
            _cur[slot] = value;
            _from[slot] = value;
            _target[slot] = value;
            RaiseChanged();
        }

        /// <summary>
        /// 开始一次过渡：所有槽在 duration 秒内平滑趋近各自目标。
        /// duration ≤ 0 时立即到位并同步触发 Finished（调用方无需区分零时长）。
        /// </summary>
        public void Begin(float target0, float target1, float duration)
        {
            _from[0] = _cur[0];
            _from[1] = _cur[1];
            _target[0] = Mathf.Clamp01(target0);
            _target[1] = Mathf.Clamp01(target1);
            _elapsed = 0f;
            _duration = Mathf.Max(0f, duration);

            if (_duration <= 0.0001f)
            {
                _cur[0] = _target[0];
                _cur[1] = _target[1];
                _running = false;
                RaiseChanged();
                RaiseFinished();
                return;
            }

            _running = true;
        }

        /// <summary>放弃当前过渡（保持当前系数，不再推进）。</summary>
        public void Cancel()
        {
            _running = false;
        }

        private void Update()
        {
            if (!_running)
            {
                return;
            }

            _elapsed += Time.unscaledDeltaTime;
            float t = Mathf.Clamp01(_elapsed / _duration);
            float s = t * t * (3f - 2f * t);   // SmoothStep：两端速度为 0，听感更自然

            _cur[0] = Mathf.Lerp(_from[0], _target[0], s);
            _cur[1] = Mathf.Lerp(_from[1], _target[1], s);
            RaiseChanged();

            if (t >= 1f)
            {
                _cur[0] = _target[0];
                _cur[1] = _target[1];
                _running = false;
                RaiseChanged();
                RaiseFinished();
            }
        }

        private void RaiseChanged()
        {
            if (Changed != null)
            {
                Changed();
            }
        }

        private void RaiseFinished()
        {
            if (Finished != null)
            {
                Finished();
            }
        }
    }
}
