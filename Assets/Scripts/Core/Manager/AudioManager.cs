using System.Collections.Generic;
using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 音效 / 背景乐管理器（M2-W6 建系统，M4-W7 补 BGM）。
    ///
    /// 【设计口径：没有文件时完全静默、不影响玩法】
    ///   三段式查找任一环节缺失都只是"跳过 + 限流警告一次"，
    ///   绝不抛异常、绝不阻塞流程 —— 音效是最不该阻塞玩法的功能。
    ///   文件到位后**不改一行代码就能发声**（把文件丢进 Assets/Audio/ 跑生成器即可）。
    ///
    /// 【三段式查找】Play(logicalName) →
    ///   ① Configs.GetAudio 取音量/音高/循环（TBAudio 表）
    ///   ② ResLoader 取 Audio_&lt;logicalName&gt; 的 AudioClip（ResTable，由 AudioCatalog 生成）
    ///   ③ 从 AudioSource 池取一个播放
    ///
    /// 【为什么警告要限流】没有音频文件时，每次开火都会走到"取不到 Clip"这一支。
    ///   不限流的话 Console 会被瞬间刷爆，反而把真正的错误淹掉 ——
    ///   这是本项目已经踩过的坑（见 CombatSystem.TickStats 的注释）。
    ///
    /// 【音效 与 BGM 是两套通道】
    ///   音效：池化（12 个源）、点完即弃、可 3D。
    ///   BGM：**固定 2 个源**（A/B 槽做交叉淡化）、常驻循环、只能 2D。
    ///   两者分开的原因：BGM 是长音且唯一，扔进池里会被"顶掉最旧的一个"逻辑误杀。
    ///
    /// ⚠️ 本类继承 BaseManager&lt;T&gt;，是**纯 C# 单例，没有 Update**；
    ///    BGM 的逐帧淡化由挂在 AudioRoot 上的 <see cref="AudioFadeDriver"/> 负责。
    /// </summary>
    public class AudioManager : BaseManager<AudioManager>
    {
        /// <summary>音效 AudioSource 池大小。同一帧最多这么多音效同时播放，超出则复用最旧的一个。</summary>
        private const int SourcePoolSize = 12;

        /// <summary>最多打印多少条"缺资源"警告（每种逻辑名最多一条）</summary>
        private const int MaxWarnings = 8;

        /// <summary>换 BGM / 停止 BGM 的默认交叉淡化时长（秒）。</summary>
        private const float BgmCrossFadeSec = 0.8f;

        private AudioSource[] _sources;
        private int _next;
        private bool _inited;
        private readonly HashSet<string> _warned = new HashSet<string>();
        private int _warnCount;

        // ---- BGM 通道 ----
        private AudioSource[] _bgmSources;
        private readonly float[] _bgmBase = new float[AudioFadeDriver.Slots];
        private AudioFadeDriver _fadeDriver;
        private int _bgmActive = -1;          // 当前在播的槽；-1 = 无 BGM
        private string _currentBgm;           // 当前曲目的逻辑名
        private bool _pendingStop;            // 正在"淡出后停止"

        public override void OnInit()
        {
            base.OnInit();

            // 幂等：重复初始化会再建一池 AudioSource，之前正在播的引用就找不回来了
            if (_inited)
            {
                Debug.LogWarning("[Audio] OnInit 被重复调用，已忽略");
                return;
            }
            _inited = true;

            GameObject root = new GameObject("AudioRoot");
            // 挂在 Launcher 下（它已 DontDestroyOnLoad），跨场景不会被销毁
            if (Launcher.Instance != null)
            {
                root.transform.SetParent(Launcher.Instance.transform, false);
            }
            // 【只在完全没有 Listener 时才加】场景相机通常自带一个；
            // 无脑再加一个会让 Unity 持续报 "There are 2 audio listeners in the scene"，
            // 这种刷屏警告会掩盖真正的错误。
            if (Object.FindObjectOfType<AudioListener>() == null)
            {
                root.AddComponent<AudioListener>();
            }

            // ① 音效池
            _sources = new AudioSource[SourcePoolSize];
            for (int i = 0; i < SourcePoolSize; i++)
            {
                AudioSource src = root.AddComponent<AudioSource>();
                src.playOnAwake = false;
                src.loop = false;
                src.spatialBlend = 0f;
                _sources[i] = src;
            }

            // ② BGM 池（固定 2 槽，交叉淡化用）
            _bgmSources = new AudioSource[AudioFadeDriver.Slots];
            for (int i = 0; i < _bgmSources.Length; i++)
            {
                AudioSource src = root.AddComponent<AudioSource>();
                src.playOnAwake = false;
                src.loop = true;
                src.spatialBlend = 0f;
                src.volume = 0f;
                _bgmSources[i] = src;
            }

            // ③ 淡化驱动：只保存 0~1 系数，绝对音量统一由本类算（单一写入方）
            _fadeDriver = root.AddComponent<AudioFadeDriver>();
            _fadeDriver.Changed += ApplyBgmVolume;
            _fadeDriver.Finished += OnBgmFadeFinished;
        }

        public override void OnDestroy()
        {
            base.OnDestroy();

            if (_fadeDriver != null)
            {
                _fadeDriver.Changed -= ApplyBgmVolume;
                _fadeDriver.Finished -= OnBgmFadeFinished;
                _fadeDriver = null;
            }
            if (_bgmSources != null)
            {
                for (int i = 0; i < _bgmSources.Length; i++)
                {
                    if (_bgmSources[i] != null)
                    {
                        _bgmSources[i].Stop();
                        _bgmSources[i] = null;
                    }
                }
                _bgmSources = null;
            }
            _bgmActive = -1;
            _currentBgm = null;

            if (_sources != null)
            {
                for (int i = 0; i < _sources.Length; i++)
                {
                    if (_sources[i] != null)
                    {
                        _sources[i].Stop();
                        _sources[i] = null;
                    }
                }
            }
            _inited = false;
        }

        // ------------------------------------------------------------------
        // 对外接口 · 音效
        // ------------------------------------------------------------------

        /// <summary>播放一个 2D 全局音效（UI、提示类）</summary>
        public void Play(string logicalName)
        {
            PlayInternal(logicalName, Vector3.zero, false);
        }

        /// <summary>在指定世界坐标播放一个音效（战斗类）</summary>
        public void PlayAt(string logicalName, Vector3 worldPos)
        {
            PlayInternal(logicalName, worldPos, true);
        }

        // ------------------------------------------------------------------
        // 对外接口 · BGM
        // ------------------------------------------------------------------

        /// <summary>当前正在播放的 BGM 逻辑名；没有则 null。</summary>
        public string CurrentBgm { get { return _currentBgm; } }

        /// <summary>
        /// 播放背景乐（循环）。
        /// 【幂等】同一首正在播则直接返回，不会"重头再放一遍" ——
        ///   否则每次重开选关界面音乐都会跳回开头，听感很糟。
        /// 【换曲】用交叉淡化：新曲 0→1 的同时旧曲 1→0，中途不会有静音空档。
        /// </summary>
        public void PlayBgm(string logicalName)
        {
            PlayBgm(logicalName, BgmCrossFadeSec);
        }

        /// <summary>播放背景乐，可指定淡化时长（0 = 立即切换）。</summary>
        public void PlayBgm(string logicalName, float fadeSeconds)
        {
            if (string.IsNullOrEmpty(logicalName) || !_inited || _bgmSources == null || _fadeDriver == null)
            {
                return;
            }

            // 幂等：同一首且确实还在播 → 什么都不做
            if (_currentBgm == logicalName && _bgmActive >= 0 &&
                _bgmSources[_bgmActive] != null && _bgmSources[_bgmActive].isPlaying)
            {
                return;
            }

            AudioConfig cfg = Configs.GetAudio(logicalName);
            if (cfg == null)
            {
                WarnOnce(logicalName, "TBAudio 表中没有这一行");
                return;
            }

            AudioClip clip = ResLoader.Instance.Load<AudioClip>("Audio_" + logicalName);
            if (clip == null)
            {
                WarnOnce(logicalName, "找不到音频资源（把文件放进 Assets/Audio/ 并重跑 gen_audio_catalog.py）");
                return;
            }

            // 取"另一槽"承载新曲：_bgmActive 为 -1 时用 0 号槽
            int next = (_bgmActive < 0) ? 0 : (1 - _bgmActive);
            AudioSource src = _bgmSources[next];
            if (src == null)
            {
                return;
            }

            src.clip = clip;
            src.loop = true;
            src.pitch = cfg.Pitch;
            src.spatialBlend = 0f;
            _bgmBase[next] = cfg.Volume;
            _currentBgm = logicalName;
            _pendingStop = false;

            // 新曲从 0 起步，避免以上一次的残留音量"闪一下"
            _fadeDriver.Prime(next, 0f);
            src.Play();

            _bgmActive = next;
            float target0 = (next == 0) ? 1f : 0f;
            float target1 = (next == 1) ? 1f : 0f;
            _fadeDriver.Begin(target0, target1, fadeSeconds);
            ApplyBgmVolume();   // 立即应用一次，避免零时长时依赖事件时序
        }

        /// <summary>淡出并停止当前 BGM（默认 0.8 秒）。</summary>
        public void StopBgm()
        {
            StopBgm(BgmCrossFadeSec);
        }

        /// <summary>淡出并停止当前 BGM，可指定淡化时长（0 = 立即停止）。</summary>
        public void StopBgm(float fadeSeconds)
        {
            if (!_inited || _fadeDriver == null || _bgmActive < 0)
            {
                _currentBgm = null;
                _bgmActive = -1;
                return;
            }
            _pendingStop = true;
            _fadeDriver.Begin(0f, 0f, fadeSeconds);
        }

        // ------------------------------------------------------------------
        // 音量 / 静音
        // ------------------------------------------------------------------

        private bool _muted;

        /// <summary>
        /// 静音开关（由设置界面写入）。
        /// 【为什么可以把 BGM 音量直接压成 0 而不是停止播放】停止/重播会有明显断点；
        ///   压成 0 后再次取消静音是"无缝恢复"，体验更好。
        /// </summary>
        public bool Muted
        {
            get { return _muted; }
            set
            {
                if (_muted == value)
                {
                    return;
                }
                _muted = value;
                ApplyBgmVolume();   // BGM 是长音，必须立刻生效
            }
        }

        private float _masterVolume = 1f;

        /// <summary>
        /// 主音量 0~1（由设置界面写入）。
        /// 【为什么乘在每条音效自己的 volume 上，而不是去改 AudioListener.volume】
        /// 改全局 Listener 音量会连带影响以后可能加入的其它音频来源；
        /// 乘在这里则"每条音效的相对轻重"保持不变，符合玩家的直觉。
        /// </summary>
        public float MasterVolume
        {
            get { return _masterVolume; }
            set
            {
                _masterVolume = value;
                ApplyBgmVolume();   // BGM 立即跟随；音效是短音，下次播放时自然带上新值
            }
        }

        /// <summary>
        /// 重算两条 BGM 源的实际音量。
        /// 实际音量 = 该曲基准音量 × 淡化系数 × 主音量 × (静音 ? 0 : 1)。
        /// **本方法是 BGM 音量的唯一写入方** —— 淡化驱动只改系数、从不直接写 volume，
        /// 这样"设置里调音量"和"正在进行的淡化"不会互相覆盖。
        /// </summary>
        private void ApplyBgmVolume()
        {
            if (_bgmSources == null || _fadeDriver == null)
            {
                return;
            }
            float master = _muted ? 0f : Mathf.Clamp01(_masterVolume);
            for (int i = 0; i < _bgmSources.Length; i++)
            {
                AudioSource src = _bgmSources[i];
                if (src == null)
                {
                    continue;
                }
                float scale = _fadeDriver.Scale(i);
                src.volume = _bgmBase[i] * scale * master;
            }
        }

        /// <summary>一次淡化结束时收拾残局：停旧槽或完成"淡出停止"。</summary>
        private void OnBgmFadeFinished()
        {
            if (_bgmSources == null)
            {
                return;
            }

            if (_pendingStop)
            {
                _pendingStop = false;
                for (int i = 0; i < _bgmSources.Length; i++)
                {
                    StopSlot(i);
                }
                _bgmActive = -1;
                _currentBgm = null;
                ApplyBgmVolume();
                return;
            }

            // 交叉淡化结束：把非当前槽（旧曲）停掉并清引用，释放它的资源
            for (int i = 0; i < _bgmSources.Length; i++)
            {
                if (i == _bgmActive)
                {
                    continue;
                }
                StopSlot(i);
            }
        }

        private void StopSlot(int index)
        {
            if (_bgmSources == null || index < 0 || index >= _bgmSources.Length)
            {
                return;
            }
            AudioSource src = _bgmSources[index];
            if (src != null)
            {
                src.Stop();
                src.clip = null;
            }
            _bgmBase[index] = 0f;
        }

        // ------------------------------------------------------------------
        // 内部 · 音效
        // ------------------------------------------------------------------

        private void PlayInternal(string logicalName, Vector3 worldPos, bool atPosition)
        {
            if (Muted || string.IsNullOrEmpty(logicalName) || !_inited)
            {
                return;
            }

            // ① 配置
            AudioConfig cfg = Configs.GetAudio(logicalName);
            if (cfg == null)
            {
                WarnOnce(logicalName, "TBAudio 表中没有这一行");
                return;
            }

            // ② 资源（AudioCatalog 生成 → ResTable 登记）
            AudioClip clip = ResLoader.Instance.Load<AudioClip>("Audio_" + logicalName);
            if (clip == null)
            {
                WarnOnce(logicalName, "找不到音频资源（把文件放进 Assets/Audio/ 并重跑 gen_audio_catalog.py）");
                return;
            }

            // ③ 播放
            AudioSource src = TakeSource();
            if (src == null)
            {
                return;
            }
            src.clip = clip;
            src.volume = cfg.Volume * (_muted ? 0f : Mathf.Clamp01(_masterVolume));
            src.pitch = cfg.Pitch;
            src.loop = cfg.Loop;
            src.spatialBlend = cfg.Is3d ? 1f : 0f;
            if (atPosition)
            {
                src.transform.position = new Vector3(worldPos.x, worldPos.y, 0f);
            }
            src.Play();
        }

        /// <summary>优先取"空闲"的源；都在播就轮转顶掉最旧的一个。</summary>
        private AudioSource TakeSource()
        {
            if (_sources == null || _sources.Length == 0)
            {
                return null;
            }
            for (int i = 0; i < _sources.Length; i++)
            {
                int idx = (_next + i) % _sources.Length;
                if (_sources[idx] != null && !_sources[idx].isPlaying)
                {
                    _next = (idx + 1) % _sources.Length;
                    return _sources[idx];
                }
            }
            AudioSource fallback = _sources[_next];
            _next = (_next + 1) % _sources.Length;
            return fallback;
        }

        private void WarnOnce(string logicalName, string reason)
        {
            if (_warned.Contains(logicalName))
            {
                return;
            }
            _warned.Add(logicalName);
            if (_warnCount >= MaxWarnings)
            {
                return;
            }
            _warnCount++;
            Debug.LogWarning(string.Format(
                "[Audio] 「{0}」{1} —— 已跳过（不影响玩法）。\n" +
                "  补齐方式：把音频文件放进 Assets/Audio/ 并执行 .workbuddy/tools/gen_audio_catalog.py，" +
                "无需改动任何代码。", logicalName, reason));
        }
    }
}
