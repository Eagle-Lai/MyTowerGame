using System.Collections.Generic;
using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 音效管理器（M2-W6）。
    ///
    /// 【本轮交付的是"系统 + 配置 + 调用点"】
    ///   工程内当前 **0 个音频文件**（已全盘扫描确认）。按设计文档 §3.5
    ///   「功能缺失不应阻塞」，音效这一层必须做到：没有文件时**完全静默、不影响玩法**，
    ///   文件到位后**不改一行代码就能发声**。
    ///
    /// 【三段式查找】Play(logicalName) →
    ///   ① Configs.GetAudio 取音量/音高/循环（TBAudio 表）
    ///   ② ResLoader 取 Audio_&lt;logicalName&gt; 的 AudioClip（ResTable，由 AudioCatalog 生成）
    ///   ③ 从 AudioSource 池取一个播放
    ///   任一环节缺失 → 跳过 + 限流警告一次。三段都能独立缺失，所以每条都要判空。
    ///
    /// 【为什么警告要限流】没有音频文件时，每次开火都会走到"取不到 Clip"这一支。
    ///   不限流的话 Console 会被瞬间刷爆，反而把真正的错误淹掉 ——
    ///   这是本项目已经踩过的坑（见 CombatSystem.TickStats 的注释）。
    /// </summary>
    public class AudioManager : BaseManager<AudioManager>
    {
        /// <summary>AudioSource 池大小。同一帧最多这么多音效同时播放，超出则复用最旧的一个。</summary>
        private const int SourcePoolSize = 12;

        /// <summary>最多打印多少条"缺资源"警告（每种逻辑名最多一条）</summary>
        private const int MaxWarnings = 8;

        private AudioSource[] _sources;
        private int _next;
        private bool _inited;
        private readonly HashSet<string> _warned = new HashSet<string>();
        private int _warnCount;

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

            _sources = new AudioSource[SourcePoolSize];
            for (int i = 0; i < SourcePoolSize; i++)
            {
                AudioSource src = root.AddComponent<AudioSource>();
                src.playOnAwake = false;
                src.loop = false;
                src.spatialBlend = 0f;
                _sources[i] = src;
            }
        }

        public override void OnDestroy()
        {
            base.OnDestroy();
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
        // 对外接口
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

        /// <summary>静音开关（预留给将来的设置界面）</summary>
        public bool Muted { get; set; }

        // ------------------------------------------------------------------
        // 内部
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
            src.volume = cfg.Volume;
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
