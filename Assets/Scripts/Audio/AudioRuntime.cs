using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Audio;

namespace FTProject
{
    /// <summary>One real-time driver, bounded voices, one owner of each cached resource handle.</summary>
    public sealed class AudioRuntime : MonoBehaviour
    {
        public static AudioRuntime Current { get; private set; }
        private sealed class Voice
        {
            public AudioSource source;
            public AudioMixerGroup bus;
            public SoundCue cue;
            public float gain;
            public int priority;
            public bool gameplay, paused;
            public BaseTower owner;
            public BaseEnemy enemy;
        }
        private sealed class Aura
        {
            public BaseTower tower;
            public float lastActivity, nextPulse;
        }

        private readonly Dictionary<SoundCue, AudioCueDefinition> _definitions = new Dictionary<SoundCue, AudioCueDefinition>();
        private readonly Dictionary<string, AudioClip> _clips = new Dictionary<string, AudioClip>();
        private readonly HashSet<string> _wanted = new HashSet<string>();
        private readonly HashSet<string> _loading = new HashSet<string>();
        private readonly HashSet<string> _failed = new HashSet<string>();
        private readonly HashSet<string> _warnings = new HashSet<string>();
        private readonly Dictionary<SoundCue, float> _next = new Dictionary<SoundCue, float>();
        private readonly Dictionary<SoundCue, int> _lastVariant = new Dictionary<SoundCue, int>();
        private readonly Dictionary<string, SoundCue> _enemyGroups = new Dictionary<string, SoundCue>();
        private readonly Dictionary<BaseEnemy, float> _enemyNext = new Dictionary<BaseEnemy, float>();
        private readonly List<Aura> _auras = new List<Aura>();
        private readonly System.Random _random = new System.Random();
        private Voice[] _short = new Voice[0], _loops = new Voice[0];
        private Voice[] _music = new Voice[0];
        private Voice _stinger;
        private AudioCatalog _catalog;
        private AudioMixer _mixer;
        private AudioMixerGroup _musicBus, _sfxBus;
        private AudioPreferences _settings;
        private AudioListener _listener;
        private bool _alive = true, _starting, _ready, _inLevel, _combatWarm, _settled, _low;
        private bool _paused, _background, _focused = true, _settingsDirty;
        private int _epoch, _musicTarget = -1;
        private SoundCue? _desired;
        private readonly string[] _musicKeys = new string[2];
        private readonly float[] _musicFades = new float[2];
        private GameFlowState _state = GameFlowState.None;
        private bool _pressure;
        private float _musicChangedAt, _saveAt, _ratingAt = -1;
        private int _ratingEpoch;
        private bool _ratingPending, _ratingAllowed = true;
        private bool? _pendingSettlement;
        private float _pauseStarted;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetStatics() { Current = null; }

        private void Awake()
        {
            if (Current != null && Current != this) { _alive = false; Destroy(gameObject); return; }
            Current = this;
            var listeners = FindObjectsOfType<AudioListener>();
            if (listeners.Length == 0) _listener = gameObject.AddComponent<AudioListener>();
            else
            {
                // A listener on a scene camera is transferred to this persistent owner, preventing loss on scene changes.
                foreach (var listener in listeners) listener.enabled = false;
                _listener = gameObject.AddComponent<AudioListener>();
            }
            UnityEngine.SceneManagement.SceneManager.sceneLoaded += OnSceneLoaded;
            AudioSettings.OnAudioConfigurationChanged += OnAudioConfigurationChanged;
            EventDispatcher.AddEventListener<BaseEnemy, int>(EventName.EnemyKilledEvent, OnEnemyKilled);
            EventDispatcher.AddEventListener<BaseEnemy, int>(EventName.EnemyReachedEndEvent, OnLeak);
            EventDispatcher.AddEventListener<BaseEnemy>(EventName.EnemyResetEvent, OnEnemyReset);
            EventDispatcher.AddEventListener<int, int>(EventName.PlayerHpChangeEvent, OnHp);
            EventDispatcher.AddEventListener<int>(EventName.RoundStartEvent, OnRoundStart);
            EventDispatcher.AddEventListener<int>(EventName.RoundClearEvent, OnRoundClear);
            EventDispatcher.AddEventListener<bool>(EventName.GameOverEvent, OnGameOver);
            EventDispatcher.AddEventListener<bool>(EventName.PauseStateChangedEvent, OnPause);
        }

        private void OnSceneLoaded(UnityEngine.SceneManagement.Scene scene, UnityEngine.SceneManagement.LoadSceneMode mode)
        {
            if (!_alive || _listener == null) return;
            foreach (var listener in FindObjectsOfType<AudioListener>()) if (listener != _listener) listener.enabled = false;
        }

        private void Update()
        {
            if (!_alive) return;
            if (!_starting && Launcher.Instance != null && Launcher.Instance.IsBootComplete && ResLoader.Instance.IsReady)
            {
                _starting = true;
                StartCoroutine(Initialize());
            }
            if (!_ready) return;
            SyncState();
            bool gamePaused = _inLevel && GameClock.IsPaused;
            if (gamePaused != _paused) SetGamePaused(gamePaused, false);
            if (_settingsDirty && Time.realtimeSinceStartup >= _saveAt) FlushSettings();
            if (!Suspended)
            {
                UpdateMusic();
                UpdateAuras();
                if (_ratingPending && !_stinger.paused && !_stinger.source.isPlaying)
                {
                    if (_ratingAt < 0) _ratingAt = Time.realtimeSinceStartup + .2f;
                    if (Time.realtimeSinceStartup >= _ratingAt)
                    {
                        _ratingPending = false; _ratingAt = -1;
                        if (_ratingEpoch == _epoch && _settled && _inLevel) StartStinger(SoundCue.Rating);
                    }
                }
            }
            foreach (var voice in _short) UpdateVoice(voice);
            foreach (var voice in _loops) UpdateVoice(voice);
            foreach (var voice in _music) UpdateVoice(voice);
            UpdateVoice(_stinger);
        }

        private void OnAudioConfigurationChanged(bool deviceWasChanged)
        {
            // Device resets can stop native voices without changing application focus.
            // Music and owner loops are revalidated by the next active update.
            RefreshSuspension();
        }

        private bool Suspended { get { return _background || !_focused; } }

        private IEnumerator Initialize()
        {
            bool done = false, expired = false;
            ResLoader.Instance.LoadAsync<AudioCatalog>(AudioResourceMap.CatalogKey, value =>
            {
                if (!_alive || expired) { ResLoader.Instance.Release(AudioResourceMap.CatalogKey); return; }
                _catalog = value; done = true;
            });
            float until = Time.realtimeSinceStartup + 10;
            while (!done && Time.realtimeSinceStartup < until) yield return null;
            if (!done || _catalog == null) { expired = true; Warn("catalog", "GameAudioCatalog missing or timed out at Assets/Audio/Runtime/GameAudioCatalog.asset; optional audio disabled."); yield break; }
            foreach (var def in _catalog.cues)
                if (def != null && def.logicalNames != null && def.logicalNames.Length > 0) _definitions[def.cue] = def;
            done = false; expired = false;
            ResLoader.Instance.LoadAsync<AudioMixer>(AudioResourceMap.MixerKey, value =>
            {
                if (!_alive || expired) { ResLoader.Instance.Release(AudioResourceMap.MixerKey); return; }
                _mixer = value; done = true;
            });
            until = Time.realtimeSinceStartup + 10;
            while (!done && Time.realtimeSinceStartup < until) yield return null;
            if (!done) expired = true;
            if (_mixer != null)
            {
                var groups = _mixer.FindMatchingGroups("Music"); if (groups.Length > 0) _musicBus = groups[0];
                groups = _mixer.FindMatchingGroups("SFX"); if (groups.Length > 0) _sfxBus = groups[0];
            }
            else Warn("mixer", "GameAudioMixer unavailable; source gain fallback is active.");
            _short = MakeVoices("SFX", Mathf.Clamp(_catalog.shortVoices, 4, 20), false);
            _loops = MakeVoices("Aura", Mathf.Clamp(_catalog.loopVoices, 0, 4), false);
            _music = MakeVoices("Music", 2, true);
            _stinger = MakeVoices("Stinger", 1, true)[0];
            _settings = AudioPreferences.Normalize(SaveManager.Instance.Settings.audio);
            BuildEnemyGroups();
            _ready = true;
            StartCoroutine(Warm(false, _epoch));
            if (_pendingSettlement.HasValue) { bool victory = _pendingSettlement.Value; _pendingSettlement = null; OnGameOver(victory); }
            Debug.Log("[Audio] Ready: 20 short / up to 4 aura / 2 music / 1 stinger; catalog=" + _definitions.Count);
        }

        private Voice[] MakeVoices(string prefix, int count, bool music)
        {
            var result = new Voice[count];
            for (int i = 0; i < count; i++)
            {
                var child = new GameObject(prefix + i); child.transform.SetParent(transform, false);
                var source = child.AddComponent<AudioSource>(); source.playOnAwake = false;
                source.spatialBlend = 0; source.dopplerLevel = 0; source.pitch = 1;
                source.outputAudioMixerGroup = music ? _musicBus : _sfxBus;
                result[i] = new Voice { source = source, bus = source.outputAudioMixerGroup };
            }
            return result;
        }

        private IEnumerator Warm(bool combat, int epoch)
        {
            float warmDeadline = Time.realtimeSinceStartup + 20;
            foreach (var pair in _definitions)
            {
                if (pair.Key <= SoundCue.Rating || pair.Value.gameplay != combat) continue;
                foreach (string key in pair.Value.logicalNames)
                {
                    if (!_alive || Time.realtimeSinceStartup >= warmDeadline || (combat && (epoch != _epoch || !_inLevel))) yield break;
                    _wanted.Add(key); EnsureClip(key);
                    float until = Time.realtimeSinceStartup + 10;
                    while (_loading.Contains(key) && Time.realtimeSinceStartup < until) yield return null;
                    if (Time.realtimeSinceStartup >= until) Warn(key, "Audio warmup timed out: " + key);
                }
            }
        }

        private void EnsureClip(string key)
        {
            if (_clips.ContainsKey(key) || _loading.Contains(key) || _failed.Contains(key)) return;
            _loading.Add(key);
            ResLoader.Instance.LoadAsync<AudioClip>(key, clip =>
            {
                _loading.Remove(key);
                if (!_alive || !_wanted.Contains(key)) { ResLoader.Instance.Release(key); return; }
                if (clip == null)
                {
                    _failed.Add(key);
                    ResAddress address; ResTable.TryGet(key, out address);
                    Warn(key, "AudioClip unavailable: " + key + " at " + address.EditorPath); return;
                }
                _clips[key] = clip;
                if (clip.loadType != AudioClipLoadType.Streaming && clip.loadState == AudioDataLoadState.Unloaded) clip.LoadAudioData();
            });
        }

        public void Play(SoundCue cue, BaseEnemy enemyOwner = null)
        {
            if (!_ready || Suspended) return;
            AudioCueDefinition def;
            if (!_definitions.TryGetValue(cue, out def)) { Warn(cue.ToString(), "Missing cue: " + cue); return; }
            if (def.gameplay && (!_inLevel || _settled || _paused)) return;
            float now = Time.realtimeSinceStartup, next;
            if (_next.TryGetValue(cue, out next) && now < next) return;
            int active = 0;
            Voice slot = null;
            foreach (var voice in _short)
            {
                if (voice.source.clip == null || (!voice.paused && !voice.source.isPlaying)) { if (slot == null) slot = voice; }
                else if (voice.cue == cue) active++;
            }
            if (active >= def.maxConcurrent) return;
            // The final four slots cannot be filled by ordinary battle noise.
            if (def.priority < 70 && slot != null && Array.IndexOf(_short, slot) >= _short.Length - 4) slot = null;
            if (slot == null)
            {
                int priority = def.priority;
                foreach (var voice in _short)
                    if (voice.priority < priority && (def.priority >= 70 || Array.IndexOf(_short, voice) < _short.Length - 4))
                    { priority = voice.priority; slot = voice; }
            }
            if (slot == null) return;
            AudioClip clip = PickClip(def);
            if (clip == null) return;
            ResetVoice(slot); slot.enemy = enemyOwner; slot.cue = cue; slot.gain = def.gain; slot.priority = def.priority; slot.gameplay = def.gameplay;
            slot.source.clip = clip; slot.source.pitch = .97f + (float)_random.NextDouble() * .06f;
            slot.source.priority = Mathf.Clamp(256 - def.priority * 2, 0, 256);
            slot.source.volume = 0; slot.source.Play(); UpdateVoice(slot); _next[cue] = now + def.cooldown;
        }

        private AudioClip PickClip(AudioCueDefinition def)
        {
            int last, count = def.logicalNames.Length;
            int index = _random.Next(count);
            if (count > 1 && _lastVariant.TryGetValue(def.cue, out last) && index == last) index = (index + 1 + _random.Next(count - 1)) % count;
            AudioClip clip;
            if (!_clips.TryGetValue(def.logicalNames[index], out clip)) return null;
            if (clip.loadState == AudioDataLoadState.Loading || clip.loadState == AudioDataLoadState.Failed) return null;
            _lastVariant[def.cue] = index; return clip;
        }

        private void SyncState()
        {
            var flow = GameFlowManager.Instance;
            GameFlowState state = flow != null ? flow.State : GameFlowState.None;
            if (_inLevel && !_combatWarm) { _combatWarm = true; StartCoroutine(Warm(true, _epoch)); }
            if (state != _state)
            {
                _state = state; _pressure = false;
                if (state == GameFlowState.GameOver && !_settled) OnGameOver(false);
            }
            SoundCue? desired = SoundCue.Menu;
            if (_inLevel)
            {
                if (state == GameFlowState.Loading || state == GameFlowState.None) desired = null;
                else if (_settled || state == GameFlowState.GameOver) desired = null;
                else if (state == GameFlowState.RoundRunning)
                {
                    var player = PlayerDataManager.Instance;
                    float ratio = player.MaxHp > 0 ? (float)player.Hp / player.MaxHp : 1;
                    if (Time.realtimeSinceStartup - _musicChangedAt >= _catalog.musicMinResidence)
                    {
                        if (!_pressure && ratio <= _catalog.pressureEnter) _pressure = true;
                        else if (_pressure && ratio >= _catalog.pressureExit) _pressure = false;
                    }
                    desired = _pressure ? SoundCue.Pressure : SoundCue.Battle;
                }
                else desired = SoundCue.Prepare;
            }
            if (_desired != desired) { _desired = desired; _musicChangedAt = Time.realtimeSinceStartup; }
        }

        private void UpdateMusic()
        {
            string desiredKey = null;
            AudioCueDefinition definition;
            if (_desired.HasValue && _definitions.TryGetValue(_desired.Value, out definition))
            {
                desiredKey = definition.logicalNames[0]; _wanted.Add(desiredKey); EnsureClip(desiredKey);
                AudioClip clip;
                if (_clips.TryGetValue(desiredKey, out clip) && (_musicTarget < 0 || _musicKeys[_musicTarget] != desiredKey))
                {
                    int index = _musicKeys[0] == desiredKey ? 0 : _musicKeys[1] == desiredKey ? 1 : (_musicTarget == 0 ? 1 : 0);
                    if (_musicKeys[index] != desiredKey)
                    {
                        string old = _musicKeys[index]; ResetVoice(_music[index]); _musicFades[index] = 0;
                        _musicKeys[index] = desiredKey; _music[index].cue = _desired.Value; _music[index].gain = definition.gain;
                        _music[index].source.clip = clip; _music[index].source.loop = true; _music[index].source.priority = 0;
                        _music[index].source.volume = 0; _music[index].source.Play();
                        ReleaseMusic(old);
                    }
                    _musicTarget = index;
                }
            }
            else _musicTarget = -1;
            for (int i = 0; i < _music.Length; i++)
            {
                if (_music[i].source.clip != null && !_music[i].paused && !_music[i].source.isPlaying) _music[i].source.Play();
                _musicFades[i] = Mathf.MoveTowards(_musicFades[i], i == _musicTarget ? 1 : 0,
                    Time.unscaledDeltaTime / Mathf.Max(.05f, _catalog.fadeSeconds));
                if (_musicFades[i] <= 0 && i != _musicTarget && _musicKeys[i] != null)
                {
                    string old = _musicKeys[i]; ResetVoice(_music[i]); _musicKeys[i] = null; ReleaseMusic(old);
                }
            }
            // Pending music superseded before completion is no longer wanted. Its callback releases the handle.
            foreach (var pair in _definitions)
                if (pair.Key <= SoundCue.Pressure)
                    foreach (string key in pair.Value.logicalNames) if (key != desiredKey) ReleaseMusic(key);
        }

        private void ReleaseMusic(string key)
        {
            if (key == null || key == _musicKeys[0] || key == _musicKeys[1]) return;
            AudioCueDefinition desired;
            if (_desired.HasValue && _definitions.TryGetValue(_desired.Value, out desired) && desired.logicalNames[0] == key) return;
            _wanted.Remove(key);
            if (_clips.Remove(key)) ResLoader.Instance.Release(key);
        }

        private void UpdateVoice(Voice voice)
        {
            if (voice == null || voice.source == null) return;
            bool pause = Suspended || (voice.gameplay && _paused);
            if (pause != voice.paused)
            {
                if (pause) voice.source.Pause(); else voice.source.UnPause();
                voice.paused = pause;
            }
            bool music = voice == _stinger || Array.IndexOf(_music, voice) >= 0;
            float gain = voice.gain;
            int index = Array.IndexOf(_music, voice);
            if (index >= 0) gain *= _musicFades[index] * (_paused ? _catalog.pausedMusicGain : 1);
            voice.source.volume = Mathf.Clamp01(gain * _settings.master * (music ? _settings.music : _settings.sfx));
            voice.source.mute = _settings.muted || Suspended;
            if (Array.IndexOf(_short, voice) >= 0 && !voice.paused && voice.source.clip != null && !voice.source.isPlaying)
                ResetVoice(voice);
        }

        private static void ResetVoice(Voice voice)
        {
            if (voice == null) return;
            voice.source.Stop(); voice.source.clip = null; voice.source.loop = false;
            voice.source.pitch = 1; voice.source.volume = 0; voice.source.mute = false;
            voice.source.outputAudioMixerGroup = voice.bus;
            voice.owner = null; voice.enemy = null; voice.priority = 0; voice.gameplay = false; voice.paused = false;
        }

        public void BeginLevel()
        {
            EndLevel(); _ratingAllowed = true; _inLevel = true; _settled = false; _low = false; _paused = GameClock.IsPaused;
        }

        public void EndLevel()
        {
            _epoch++; _inLevel = false; _combatWarm = false; _settled = false; _low = false; _pressure = false;
            _pendingSettlement = null; _ratingPending = false; _ratingAt = -1; _enemyNext.Clear(); _auras.Clear(); _next.Clear();
            foreach (var voice in _short) if (voice.gameplay) ResetVoice(voice);
            foreach (var voice in _loops) ResetVoice(voice);
            ResetVoice(_stinger);
            foreach (var pair in _definitions)
                if (pair.Value.gameplay || (pair.Key >= SoundCue.Victory && pair.Key <= SoundCue.Rating))
                    foreach (string key in pair.Value.logicalNames)
                    { _wanted.Remove(key); if (_clips.Remove(key)) ResLoader.Instance.Release(key); }
        }

        public void EnemyHit(BaseEnemy enemy)
        {
            if (!_ready || enemy == null) return;
            float next;
            if (_enemyNext.TryGetValue(enemy, out next) && next > Time.realtimeSinceStartup) return;
            _enemyNext[enemy] = Time.realtimeSinceStartup + _catalog.enemyHitCooldown;
            SoundCue cue; if (TryEnemyCue(enemy, out cue)) Play(cue, enemy);
        }

        private void OnEnemyKilled(BaseEnemy enemy, int reward)
        {
            if (!_ready || enemy == null) return;
            foreach (var voice in _short) if (voice.enemy == enemy) ResetVoice(voice);
            SoundCue cue; if (TryEnemyCue(enemy, out cue)) Play((SoundCue)((int)cue + 1));
            _enemyNext.Remove(enemy);
        }
        private void OnEnemyReset(BaseEnemy enemy)
        {
            if (enemy == null) return;
            _enemyNext.Remove(enemy);
            foreach (var voice in _short) if (voice.enemy == enemy) voice.enemy = null;
        }
        private bool TryEnemyCue(BaseEnemy enemy, out SoundCue cue)
        {
            cue = SoundCue.LightHit;
            if (enemy == null || enemy.Config == null) return false;
            string key = enemy.Config.ResName ?? "";
            if (_enemyGroups.TryGetValue(key, out cue)) return (int)cue >= 0;
            Warn("enemy:" + key, "Unknown audio family for " + key + "; light fallback."); _enemyGroups[key] = cue; return true;
        }
        private void BuildEnemyGroups()
        {
            for (int i = 0; i < MonsterCatalog.Count; i++)
            {
                string family = MonsterCatalog.Families[i]; SoundCue cue;
                switch (family)
                {
                    case "Bats": case "Birds": cue = SoundCue.WingHit; break;
                    case "Insects": case "Scorpions": case "Parasites": cue = SoundCue.InsectHit; break;
                    case "Cattle": case "Giants": case "Horses": case "Mounts": case "Dogs": case "Felines": case "Pigs": cue = SoundCue.HeavyHit; break;
                    case "Inanimate": cue = (SoundCue)(-1); Warn("family:Inanimate", "Inanimate family: biological voices disabled."); break;
                    case "Apes": case "Bunnies": case "Rats": cue = SoundCue.LightHit; break;
                    default: cue = SoundCue.LightHit; Warn("family:" + family, "Unknown family " + family + "; light fallback."); break;
                }
                _enemyGroups[MonsterCatalog.LogicalName(i)] = cue;
            }
        }

        public void FrostPulse(BaseTower tower)
        {
            if (!_ready || tower == null || !_inLevel || _settled) return;
            Aura aura = null;
            foreach (var a in _auras) if (a.tower == tower) { aura = a; break; }
            if (aura == null) { aura = new Aura { tower = tower }; _auras.Add(aura); }
            aura.lastActivity = Time.realtimeSinceStartup;
            if (aura.nextPulse <= aura.lastActivity)
            { aura.nextPulse = aura.lastActivity + _catalog.frostPulseCooldown; Play(SoundCue.FrostPulse); }
        }

        private void UpdateAuras()
        {
            if (_paused) return;
            for (int i = _auras.Count - 1; i >= 0; i--)
                if (_auras[i].tower == null || !_auras[i].tower.IsBuilt) _auras.RemoveAt(i);
            AudioCueDefinition def;
            if (!_definitions.TryGetValue(SoundCue.FrostLoop, out def)) return;
            foreach (var voice in _loops)
            {
                bool active = false;
                if (_inLevel && !_settled && _state == GameFlowState.RoundRunning)
                    foreach (var a in _auras)
                        if (a.tower == voice.owner && IsAuraActive(a)) { active = true; break; }
                if (!active || (!voice.paused && !voice.source.isPlaying)) ResetVoice(voice);
            }
            if (!_inLevel || _settled || _state != GameFlowState.RoundRunning || _paused) return;
            foreach (var aura in _auras)
            {
                if (!IsAuraActive(aura)) continue;
                Voice free = null; bool playing = false;
                foreach (var voice in _loops)
                {
                    if (voice.owner == aura.tower) playing = true;
                    if (voice.owner == null && free == null) free = voice;
                }
                if (playing || free == null) continue;
                AudioClip clip = PickClip(def); if (clip == null) continue;
                ResetVoice(free); free.owner = aura.tower; free.cue = SoundCue.FrostLoop;
                free.gameplay = true; free.gain = def.gain / Mathf.Sqrt(Mathf.Max(1, _loops.Length));
                free.source.clip = clip; free.source.loop = true; free.source.priority = 200; UpdateVoice(free); free.source.Play();
            }
        }

        private static bool IsAuraActive(Aura aura)
        {
            return aura.tower != null && aura.tower.Config != null &&
                Time.realtimeSinceStartup - aura.lastActivity < Mathf.Max(1, 2 * aura.tower.Config.CooldownSec / Mathf.Max(1, GameClock.Speed));
        }

        private void OnRoundStart(int round) { Play(SoundCue.RoundStart); }
        private void OnRoundClear(int round) { if (_ready) StartCoroutine(RoundClearLater(_epoch)); }
        private IEnumerator RoundClearLater(int epoch)
        {
            yield return new WaitForSecondsRealtime(.2f);
            if (epoch == _epoch && !_settled) Play(SoundCue.RoundClear);
        }
        private void OnLeak(BaseEnemy enemy, int damage) { Play(SoundCue.EnemyLeak); }
        private void OnHp(int hp, int delta)
        {
            if (!_ready || !_inLevel || _settled || hp <= 0) return;
            int max = PlayerDataManager.Instance.MaxHp; if (max <= 0) return;
            float ratio = (float)hp / max;
            if (ratio > _catalog.pressureExit) _low = false;
            if (delta < 0 && !_low && ratio <= _catalog.pressureEnter) { _low = true; Play(SoundCue.LowHp); }
        }

        private void OnGameOver(bool victory)
        {
            if (!_inLevel || _settled) return;
            if (!_ready) { _pendingSettlement = victory; return; }
            _settled = true; _ratingPending = false; _ratingAt = -1;
            foreach (var voice in _short) if (voice.gameplay) ResetVoice(voice);
            foreach (var voice in _loops) ResetVoice(voice);
            StartCoroutine(LoadStinger(victory ? SoundCue.Victory : SoundCue.Defeat, _epoch, victory));
        }
        private IEnumerator LoadStinger(SoundCue cue, int epoch, bool rating)
        {
            AudioCueDefinition def; if (!_definitions.TryGetValue(cue, out def)) yield break;
            string key = def.logicalNames[0]; _wanted.Add(key); EnsureClip(key);
            float until = Time.realtimeSinceStartup + 10;
            while (_loading.Contains(key) && Time.realtimeSinceStartup < until && epoch == _epoch) yield return null;
            if (epoch != _epoch || !_inLevel) yield break;
            while (Suspended && epoch == _epoch) yield return null;
            if (epoch != _epoch || !_inLevel) yield break;
            float length = StartStinger(cue);
            if (rating && _ratingAllowed && length > 0)
            {
                AudioCueDefinition ratingDef;
                if (_definitions.TryGetValue(SoundCue.Rating, out ratingDef))
                {
                    _wanted.Add(ratingDef.logicalNames[0]); EnsureClip(ratingDef.logicalNames[0]);
                    _ratingEpoch = epoch; _ratingPending = true; _ratingAt = -1;
                }
            }
        }
        private float StartStinger(SoundCue cue)
        {
            AudioCueDefinition def; if (!_definitions.TryGetValue(cue, out def)) return 0;
            AudioClip clip; if (!_clips.TryGetValue(def.logicalNames[0], out clip)) return 0;
            ResetVoice(_stinger); _stinger.cue = cue; _stinger.gain = def.gain;
            _stinger.source.clip = clip; _stinger.source.priority = 0; UpdateVoice(_stinger); _stinger.source.Play();
            return clip.length;
        }

        private void OnPause(bool paused) { SetGamePaused(paused, true); }
        private void SetGamePaused(bool paused, bool feedback)
        {
            bool changed = _paused != paused;
            if (changed && paused) _pauseStarted = Time.realtimeSinceStartup;
            if (changed && !paused)
                foreach (var aura in _auras) aura.lastActivity += Time.realtimeSinceStartup - _pauseStarted;
            _paused = paused;
            if (changed && feedback && _inLevel && !_settled && _state != GameFlowState.Loading)
                Play(paused ? SoundCue.Pause : SoundCue.Resume);
        }

        public void CancelRating()
        {
            _ratingAllowed = false; _ratingPending = false; _ratingAt = -1;
            if (_stinger != null && _stinger.cue == SoundCue.Rating) ResetVoice(_stinger);
        }

        public void ApplySettings()
        {
            _settings = AudioPreferences.Normalize(SaveManager.Instance.Settings.audio);
            _settingsDirty = true; _saveAt = Time.realtimeSinceStartup + .35f;
        }
        public void FlushSettings()
        {
            if (!_settingsDirty) return;
            if (SaveManager.Instance.SaveAudioSettings()) _settingsDirty = false;
            else _saveAt = Time.realtimeSinceStartup + 5;
        }
        private void OnApplicationPause(bool paused) { _background = paused; if (paused) FlushSettings(); RefreshSuspension(); }
        private void OnApplicationFocus(bool focused) { _focused = focused; if (!focused) FlushSettings(); RefreshSuspension(); }
        private void RefreshSuspension()
        {
            if (!_ready) return;
            foreach (var voice in _short) UpdateVoice(voice);
            foreach (var voice in _loops) UpdateVoice(voice);
            foreach (var voice in _music) UpdateVoice(voice);
            UpdateVoice(_stinger);
        }
        private void OnApplicationQuit() { Shutdown(); }
        private void OnDestroy() { Shutdown(); if (Current == this) Current = null; }
        public void Shutdown()
        {
            if (!_alive) return;
            FlushSettings(); _alive = false; StopAllCoroutines();
            UnityEngine.SceneManagement.SceneManager.sceneLoaded -= OnSceneLoaded;
            AudioSettings.OnAudioConfigurationChanged -= OnAudioConfigurationChanged;
            EventDispatcher.RemoveEventListener<BaseEnemy, int>(EventName.EnemyKilledEvent, OnEnemyKilled);
            EventDispatcher.RemoveEventListener<BaseEnemy, int>(EventName.EnemyReachedEndEvent, OnLeak);
            EventDispatcher.RemoveEventListener<BaseEnemy>(EventName.EnemyResetEvent, OnEnemyReset);
            EventDispatcher.RemoveEventListener<int, int>(EventName.PlayerHpChangeEvent, OnHp);
            EventDispatcher.RemoveEventListener<int>(EventName.RoundStartEvent, OnRoundStart);
            EventDispatcher.RemoveEventListener<int>(EventName.RoundClearEvent, OnRoundClear);
            EventDispatcher.RemoveEventListener<bool>(EventName.GameOverEvent, OnGameOver);
            EventDispatcher.RemoveEventListener<bool>(EventName.PauseStateChangedEvent, OnPause);
            foreach (var voice in _short) ResetVoice(voice);
            foreach (var voice in _loops) ResetVoice(voice);
            foreach (var voice in _music) ResetVoice(voice);
            ResetVoice(_stinger);
            foreach (var key in _clips.Keys) ResLoader.Instance.Release(key);
            _clips.Clear(); _wanted.Clear(); _enemyNext.Clear(); _auras.Clear();
            ResLoader.Instance.Release(AudioResourceMap.CatalogKey); ResLoader.Instance.Release(AudioResourceMap.MixerKey);
        }

        private void Warn(string key, string message) { if (_warnings.Add(key)) Debug.LogWarning("[Audio] " + message); }
        public string Diagnostics()
        {
            int active = 0; foreach (var voice in _short) if (voice.source.isPlaying || voice.paused) active++;
            return "ready=" + _ready + " clips=" + _clips.Count + " pending=" + _loading.Count + " short=" + active +
                "/" + _short.Length + " auras=" + _auras.Count + " desired=" + _desired + " epoch=" + _epoch;
        }
    }
}
