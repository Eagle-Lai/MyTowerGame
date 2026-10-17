using System.Collections.Generic;
using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 塔开火序列帧播放器（2026-10-17 攻击表现改版）。
    ///
    /// 【背景】普通塔(1)/火力塔(2) 移除真实子弹，改为《坚守阵地》式表现：
    ///   开火只在炮口播一段枪口焰序列帧，伤害在开火瞬间即时结算（见 BaseTower.Fire）；
    ///   火力塔另在落点播一段爆炸序列帧。本组件就是这两段序列帧的播放器。
    ///
    /// 【两种形态】
    ///   1. 枪口焰：Attach 到炮管（Img_gun）下作为子物体 —— 跟随炮管旋转，
    ///      localPosition 对齐炮口（BarrelPoint）。帧内火焰**朝上画**（与炮管贴图
    ///      原生朝向一致，见 BaseTower.BarrelNativeAngle 的说明），因此无需再转。
    ///   2. 落点爆炸：PlayBlastAt(worldPos) 从静态池取一个一次性实例播放，
    ///      播完自动归池。池化是因为火力塔攻速不低，逐次 Instantiate 会产生 GC 尖峰。
    ///
    /// 【帧数据】来自 ResTable 登记的散帧（Tower_Muzzle_* / Tower_Blast_*），
    ///   懒加载一次后缓存到静态字段 —— 所有塔共享，切关后随域重载自然清空。
    ///
    /// 【节拍】帧率固定 MuzzleFps/BlastFps，用 Time.deltaTime 推进：
    ///   暂停时 timeScale=0，序列自然冻结，与攻击节奏保持一致。
    /// </summary>
    public class TowerFireFx : MonoBehaviour
    {
        private const float MuzzleFps = 20f;
        private const float BlastFps = 16f;

        private SpriteRenderer _sr;
        private Sprite[] _frames;
        private float _frameSec;
        private float _timer;
        private int _index;
        private bool _playing;
        /// <summary>播完是否隐藏（枪口焰 true；爆炸实例回池时统一 SetActive(false)）</summary>
        private bool _hideWhenDone;

        // ---- 静态帧缓存（全塔共享）----
        private static Sprite[] _muzzleNormal;
        private static Sprite[] _muzzlePower;
        private static Sprite[] _blast;

        // ---- 落点爆炸的静态池 ----
        private static readonly List<TowerFireFx> _blastIdle = new List<TowerFireFx>(8);
        private static Transform _blastRoot;

        // ------------------------------------------------------------------
        // 枪口焰
        // ------------------------------------------------------------------

        /// <summary>
        /// 在炮管下挂一个枪口焰子物体（每塔一个，随炮管旋转）。
        /// localPosition 取炮口标记 BarrelPoint（没有就顶在炮管上沿）。
        /// </summary>
        public static TowerFireFx AttachMuzzle(Transform barrel, Transform muzzleTip)
        {
            if (barrel == null)
            {
                return null;
            }
            Transform t = barrel.Find("FireFx_Muzzle");
            GameObject go;
            if (t == null)
            {
                go = new GameObject("FireFx_Muzzle");
                go.transform.SetParent(barrel, false);
                if (muzzleTip != null)
                {
                    go.transform.localPosition = muzzleTip.localPosition;
                }
                else
                {
                    go.transform.localPosition = new Vector3(0f, 0.5f, 0f);
                }
                go.transform.localScale = Vector3.one * 0.9f;
                SpriteRenderer sr = go.AddComponent<SpriteRenderer>();
                // 塔层之上、子弹层之下：焰要盖住炮管，但不得盖住飞行中的弹体/爆炸
                sr.sortingOrder = BoardSorting.Tower + 2;
            }
            else
            {
                go = t.gameObject;
            }
            TowerFireFx fx = go.GetComponent<TowerFireFx>();
            if (fx == null)
            {
                fx = go.AddComponent<TowerFireFx>();
            }
            fx._sr = go.GetComponent<SpriteRenderer>();
            fx._hideWhenDone = true;
            fx._playing = false;
            if (fx._sr != null)
            {
                fx._sr.enabled = false;
            }
            return fx;
        }

        /// <summary>按塔型取枪口焰帧序列（懒加载）。</summary>
        public static Sprite[] GetMuzzleFrames(bool isPower)
        {
            if (isPower)
            {
                if (_muzzlePower == null)
                {
                    _muzzlePower = LoadFrames("Tower_Muzzle_Power_", 5);
                }
                return _muzzlePower;
            }
            if (_muzzleNormal == null)
            {
                _muzzleNormal = LoadFrames("Tower_Muzzle_Normal_", 4);
            }
            return _muzzleNormal;
        }

        /// <summary>重放一遍枪口焰（正在播时从头打断重放 —— 攻速快时表现为持续喷吐）。</summary>
        public void PlayMuzzle(Sprite[] frames)
        {
            if (frames == null || frames.Length == 0 || _sr == null)
            {
                return;
            }
            _frames = frames;
            _frameSec = 1f / MuzzleFps;
            _index = 0;
            _timer = 0f;
            _playing = true;
            _sr.sprite = frames[0];
            _sr.enabled = true;
        }

        // ------------------------------------------------------------------
        // 落点爆炸
        // ------------------------------------------------------------------

        /// <summary>在落点播一次爆炸序列帧（池化）。</summary>
        public static void PlayBlastAt(Vector2 worldPos)
        {
            if (_blast == null)
            {
                _blast = LoadFrames("Tower_Blast_", 6);
            }
            if (_blast == null || _blast.Length == 0)
            {
                return;
            }
            TowerFireFx fx = null;
            // 从池里找一个空闲实例
            while (_blastIdle.Count > 0 && fx == null)
            {
                int last = _blastIdle.Count - 1;
                fx = _blastIdle[last];
                _blastIdle.RemoveAt(last);
                if (fx == null)
                {
                    continue;   // 池里残留了已销毁实例（切关），跳过
                }
            }
            if (fx == null)
            {
                fx = CreateBlastInstance();
            }
            if (fx == null)
            {
                return;
            }
            fx.transform.position = new Vector3(worldPos.x, worldPos.y, 0f);
            fx.gameObject.SetActive(true);
            fx._frames = _blast;
            fx._frameSec = 1f / BlastFps;
            fx._index = 0;
            fx._timer = 0f;
            fx._playing = true;
            fx._hideWhenDone = false;
            fx._sr.sprite = _blast[0];
            fx._sr.enabled = true;
        }

        private static TowerFireFx CreateBlastInstance()
        {
            if (_blastRoot == null)
            {
                GameObject root = GameObject.Find("TowerFireFxRoot");
                if (root == null)
                {
                    root = new GameObject("TowerFireFxRoot");
                }
                _blastRoot = root.transform;
            }
            GameObject go = new GameObject("FireFx_Blast");
            go.transform.SetParent(_blastRoot, false);
            go.transform.localScale = Vector3.one;
            SpriteRenderer sr = go.AddComponent<SpriteRenderer>();
            sr.sortingOrder = BoardSorting.Bullet + 1;
            TowerFireFx fx = go.AddComponent<TowerFireFx>();
            fx._sr = sr;
            return fx;
        }

        private void ReturnToPool()
        {
            _playing = false;
            if (_sr != null)
            {
                _sr.enabled = false;
                _sr.sprite = null;
            }
            if (!_blastIdle.Contains(this))
            {
                _blastIdle.Add(this);
            }
            gameObject.SetActive(false);
        }

        // ------------------------------------------------------------------
        // 帧推进
        // ------------------------------------------------------------------

        private void Update()
        {
            if (!_playing)
            {
                return;
            }
            _timer += Time.deltaTime;
            while (_timer >= _frameSec)
            {
                _timer -= _frameSec;
                _index++;
                if (_index >= _frames.Length)
                {
                    // 播完：枪口焰隐藏待命，爆炸实例回池
                    if (_hideWhenDone)
                    {
                        _playing = false;
                        _sr.enabled = false;
                    }
                    else
                    {
                        ReturnToPool();
                    }
                    return;
                }
                _sr.sprite = _frames[_index];
            }
        }

        /// <summary>切关清理：清空爆炸池与帧缓存（塔本体随场景销毁，枪口焰无需处理）。</summary>
        public static void ClearPool()
        {
            for (int i = 0; i < _blastIdle.Count; i++)
            {
                TowerFireFx fx = _blastIdle[i];
                if (fx != null)
                {
                    Object.Destroy(fx.gameObject);
                }
            }
            _blastIdle.Clear();
            _blastRoot = null;
            _muzzleNormal = null;
            _muzzlePower = null;
            _blast = null;
        }

        /// <summary>按逻辑名前缀加载一串散帧；缺失按 0 帧处理（自检日志会提示）。</summary>
        private static Sprite[] LoadFrames(string prefix, int count)
        {
            List<Sprite> list = new List<Sprite>(count);
            for (int i = 0; i < count; i++)
            {
                Sprite s = ResLoader.Instance.Load<Sprite>(prefix + i);
                if (s != null)
                {
                    list.Add(s);
                }
                else
                {
                    Debug.LogWarning("[TowerFireFx] 缺序列帧 " + prefix + i + "，请检查 ResTable 与 AB 包");
                }
            }
            return list.ToArray();
        }
    }
}
