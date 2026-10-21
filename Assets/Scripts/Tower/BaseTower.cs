using System.Collections.Generic;
using AStar;
using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 塔型。编号与 TBTowerInfo.type 一一对应（2026-10-14 收敛定案的**三类**）。
    ///
    /// 【命名与行为的偏差，只在这里解释一次】
    ///   · Aoe(2) 是美术名「Power/强力塔」（火力塔），其**行为**是范围伤害 —— 见 TBTowerInfo.effectType=3；
    ///   · Slow(3) 的行为是**范围减速光环**（进入射程的怪持续被减速，不发射子弹），
    ///     而美术、节点名、资源目录一律叫 "Retard"
    ///     （映射表在 HudView.TowerTypeOf，别处不要再推导一遍）。
    ///
    /// 【2026-10-14 三塔型收敛】原 Pierce(4)/Laser(5) 已整体删除
    /// （表行、子弹、音效、图标、文档同步清理）；塔型若要扩展，从配置表加行开始。
    /// </summary>
    public enum TowerType
    {
        None = 0,
        /// <summary>单体：普通塔。可攻击**飞行与行走**两类怪物（canAttackAir=1）</summary>
        Normal = 1,
        /// <summary>范围伤害：火力塔（美术名 Power，行为是 AOE）。**仅能攻击行走怪物**（canAttackAir=0）</summary>
        Aoe = 2,
        /// <summary>减速：美术名 Retard。**行为是范围光环**（见 SlowAuraView），不发射子弹；飞行与行走都覆盖（canAttackAir=1）</summary>
        Slow = 3,
    }

    /// <summary>
    /// 防御塔基类（v2.1 的 2D 版）。
    ///
    /// 相对 v1.0 的关键改动：
    ///   - 去掉 Renderer/GetComponentsInChildren 换色 → 改 SpriteRenderer.color
    ///   - **攻击逻辑抽出为 TickAttack(dt)，由 CombatSystem 集中驱动**（不再自行订阅 UpdateEvent）
    ///   - 索敌走 EnemyGrid 空间哈希 + 节流 + 目标锁定（不再用 SphereCollider / OnTriggerEnter）
    ///   - **对空优先**：能打飞行单位的塔，射程内有飞行怪就先打飞行怪，没有才打地面（2026-10-21）
    ///   - **无目标绝不开火**（v1.0 是每 0.2s 无条件空放）
    ///   - 塔头转向目标；数值全部来自 TBTowerInfo
    /// </summary>
    public class BaseTower : MonoBehaviour
    {
        public TowerConfig Config { get; private set; }
        public CellData Cell { get; private set; }
        public bool IsBuilt { get; private set; }

        /// <summary>自检计数（CombatSystem 汇总，用于验证"空放为 0"）</summary>
        public int SearchCount { get; set; }
        public int FireCount { get; set; }
#if UNITY_EDITOR
        // Evidence counters never participate in combat or rating decisions.
        public double EvidenceDamage, EvidenceOverkill;
        public int EvidenceHits, EvidenceSlowApplications, EvidenceAirHits;
        public static bool EvidenceTrackReentry;
        public int EvidenceRepeatedEnemyEffects;
        private struct RangeEvidence { public bool inside; public int entry, affectedEntry; }
        private Dictionary<long, RangeEvidence> _rangeEvidence = new Dictionary<long, RangeEvidence>();
        private HashSet<long> _repeatedEvidence = new HashSet<long>();

        internal void CopyRangeEvidenceFrom(BaseTower old)
        {
            EvidenceRepeatedEnemyEffects = old.EvidenceRepeatedEnemyEffects;
            _rangeEvidence = new Dictionary<long, RangeEvidence>(old._rangeEvidence);
            _repeatedEvidence = new HashSet<long>(old._repeatedEvidence);
        }

        public void ObserveEvidenceRange(BaseEnemy enemy)
        {
            if (!enemy.IsAlive) return;
            RangeEvidence state;
            _rangeEvidence.TryGetValue(enemy.EvidenceSpawnSerial, out state);
            bool inside = InRange(enemy);
            if (inside && !state.inside) state.entry++;
            state.inside = inside;
            _rangeEvidence[enemy.EvidenceSpawnSerial] = state;
        }

        private void RecordEvidenceEffect(BaseEnemy enemy)
        {
            if (!EvidenceTrackReentry) return;
            RangeEvidence state;
            if (!_rangeEvidence.TryGetValue(enemy.EvidenceSpawnSerial, out state)) return;
            if (state.affectedEntry > 0 && state.entry > state.affectedEntry && _repeatedEvidence.Add(enemy.EvidenceSpawnSerial))
                EvidenceRepeatedEnemyEffects++;
            state.affectedEntry = state.entry;
            _rangeEvidence[enemy.EvidenceSpawnSerial] = state;
        }
#endif

        private BaseEnemy _target;
        private float _fireTimer;
        private float _searchTimer;
        private readonly List<BaseEnemy> _candidates = new List<BaseEnemy>(32);
        private Transform _barrel;
        private Transform _muzzle;
        private SpriteRenderer[] _renderers;
        private Vector2 _lastDir = Vector2.right;

        private const float MinRotateStep = 0.5f;

        // ---- 减速光环（Slow / 美术名 Retard）----
        /// <summary>
        /// 减速时长的额外余量（秒）：实际时长 = 塔的冷却间隔 + 本值。
        /// 取 0.1s，刷新周期之外只保留短暂的离场缓冲，
        /// 又不至于让玩家觉得"明明出圈了还慢"。
        /// </summary>
        private const float SlowAuraLingerSec = 0.1f;

        /// <summary>光环命中时的视觉脉冲时长（秒），每次结算触发一次。</summary>
        private const float AuraPulseSec = 0.15f;
        private float _auraPulseTimer;
        private SlowAuraView _auraView;

        // ---- 开火后坐（M4-3）----
        /// <summary>炮管后坐距离（世界单位）。要小到"几乎看不见但能感觉到"。</summary>
        private const float RecoilDistance = 0.07f;
        /// <summary>后坐回位时长（秒）</summary>
        private const float RecoilDurationSec = 0.09f;
        private float _recoilTimer;
        private Vector3 _barrelBasePos;
        private bool _barrelBaseCached;

        // ---- 开火序列帧（2026-10-17 表现改版）----
        /// <summary>
        /// 枪口焰播放器（挂在炮管下的子物体，随炮管旋转）。
        /// 普通塔/火力塔开火时重放一遍；减速光环塔不挂（永不开火）。
        /// </summary>
        private TowerFireFx _muzzleFx;

        /// <summary>
        /// 炮管贴图**自身画朝哪个方向**（Unity 角度，0°=右、90°=上）。
        ///
        /// 【为什么需要这个偏移】`Atan2(y,x)` 算出的角是"0°=右"，
        /// 而旋转是作用在贴图上的 —— 两者之间差一个"贴图原生朝向"。
        /// 本工程的炮管贴图（turret_barrel_128.png）是**竖着画**的：上窄下宽、枪口朝上，
        /// 即原生朝向 90°。所以实际要转的角度 = 目标角 - 90°。
        ///
        /// 【怎么量出来的】把贴图降采样成 ASCII 图看形状：枪口（窄端）在图像顶部。
        /// 这类美术事实从代码/节点名推不出来，必须看图。
        /// 换炮管美术时若朝向不对，改这一个常数即可。
        /// </summary>
        private const float BarrelNativeAngle = 90f;

        // ------------------------------------------------------------------
        // 初始化
        // ------------------------------------------------------------------

        public void Init(TowerConfig cfg, CellData cell)
        {
            Config = cfg;
            Cell = cell;
            IsBuilt = true;
            _fireTimer = 0f;
            _searchTimer = 0f;
            _target = null;
            SearchCount = 0;
            FireCount = 0;
#if UNITY_EDITOR
            EvidenceDamage = EvidenceOverkill = 0;
            EvidenceHits = EvidenceSlowApplications = EvidenceAirHits = 0;
            EvidenceRepeatedEnemyEffects = 0; _rangeEvidence.Clear(); _repeatedEvidence.Clear();
#endif

            if (_renderers == null)
            {
                _renderers = GetComponentsInChildren<SpriteRenderer>(true);
                for (int i = 0; i < _renderers.Length; i++)
                {
                    // 保留 prefab 里排好的相对层次（炮座 300 / 炮管 301），
                    // 只把"画在棋盘底下"的那些抬到塔层，不做无差别覆盖
                    if (_renderers[i] != null && _renderers[i].sortingOrder < BoardSorting.Tower)
                    {
                        _renderers[i].sortingOrder = BoardSorting.Tower;
                    }
                }
            }
            if (_barrel == null)
            {
                _barrel = transform.Find("barbette/Img_gun");
                if (_barrel == null)
                {
                    _barrel = transform.Find("Img_gun");
                }
            }
            if (_muzzle == null && _barrel != null)
            {
                _muzzle = _barrel.Find("BarrelPoint");
            }
            SetTint(Color.white);

            // 非光环塔挂枪口焰播放器（幂等：已挂则复用；光环塔不索敌不开火，不挂）
            if (!cfg.IsSlowAura && _barrel != null)
            {
                _muzzleFx = TowerFireFx.AttachMuzzle(_barrel, _muzzle);
            }

            // 减速塔：挂一个光环表现（射程圈 + 命中脉冲），并常亮显示射程
            if (cfg.IsSlowAura)
            {
                if (_auraView == null)
                {
                    _auraView = SlowAuraView.Attach(transform, cfg.RadiusWorld);
                }
                else
                {
                    _auraView.SetRadius(cfg.RadiusWorld);
                }
                if (_auraView != null)
                {
                    _auraView.SetVisible(true);
                }
            }
            else if (_auraView != null)
            {
                _auraView.SetVisible(false);
            }
            _auraPulseTimer = 0f;
        }

        public Vector2 Position
        {
            get { Vector2 p = transform.position; return p; }
        }

        /// <summary>Capture combat phases as well as the layout at an enemy-free boundary.</summary>
        public void CaptureCheckpointState(TowerSnapshot snapshot)
        {
            snapshot.runtimeStateSaved = true;
            snapshot.fireTimer = _fireTimer; snapshot.searchTimer = _searchTimer;
            snapshot.recoilTimer = _recoilTimer; snapshot.auraPulseTimer = _auraPulseTimer;
            snapshot.lastDirection = _lastDir;
            snapshot.barrelPoseSaved = _barrel != null;
            snapshot.barrelBaseCached = _barrel != null && _barrelBaseCached;
            if (_barrel != null)
            {
                snapshot.barrelLocalPosition = _barrel.localPosition;
                snapshot.barrelLocalRotation = _barrel.localRotation;
                snapshot.barrelBasePosition = _barrelBasePos;
            }
        }

        public bool RestoreCheckpointState(TowerSnapshot snapshot)
        {
            if (snapshot == null || !snapshot.HasValidRuntimeState() || snapshot.barrelPoseSaved != (_barrel != null)) return false;
            _fireTimer = snapshot.fireTimer; _searchTimer = snapshot.searchTimer;
            _recoilTimer = snapshot.recoilTimer; _auraPulseTimer = snapshot.auraPulseTimer;
            _lastDir = snapshot.lastDirection; _target = null; _candidates.Clear();
            _barrelBaseCached = snapshot.barrelBaseCached; _barrelBasePos = snapshot.barrelBasePosition;
            if (_barrel != null) { _barrel.localPosition = snapshot.barrelLocalPosition; _barrel.localRotation = snapshot.barrelLocalRotation; }
            return true;
        }

        private Vector2 MuzzlePosition
        {
            get
            {
                if (_muzzle != null)
                {
                    Vector2 m = _muzzle.position;
                    return m;
                }
                return Position;
            }
        }

        // ------------------------------------------------------------------
        // 每帧（由 CombatSystem 驱动）
        // ------------------------------------------------------------------

        public void TickAttack(float dt)
        {
            if (!IsBuilt || Config == null)
            {
                return;
            }

            // ① 光环塔（减速）：逻辑与普通塔完全不同 —— 不索敌、不转向、不开火，
            //    只是把射程内的**所有**敌人持续施加减速。单独一条支路，避免
            //    在下面那条"锁定单目标"的流程里塞 if，两者语义本就不同。
            if (Config.IsSlowAura)
            {
                TickSlowAura(dt);
                return;
            }

            // ② 目标有效性检查：死亡/回收/走出射程 → 立即解除锁定
            if (_target != null && (!_target.IsAlive || !InRange(_target)))
            {
                _target = null;
            }

            // ③ 节流索敌
            //    · 无锁定 → 整圈找：飞行单位优先，没有飞行单位才选地面；
            //    · 已锁定**地面**目标 → 每个节拍复查一次，只要圈里有飞行单位就立刻抢断
            //      （否则塔会一直咬着地面怪，飞行怪整队从头顶溜过去 —— 这正是本次需求的由来）。
            //    · 已锁定飞行目标 → 不再复查，保持地面目标原有的"锁定不抖动"手感。
            _searchTimer += dt;
            if (_searchTimer >= Config.SearchIntervalSec)
            {
                _searchTimer = 0f;
                if (_target == null)
                {
                    _target = FindTarget();
                }
                else if (Config.CanAttackAir && !IsFlying(_target))
                {
                    BaseEnemy air = FindAirTarget();
                    if (air != null)
                    {
                        _target = air;
                    }
                }
            }

            if (_target == null)
            {
                return;   // ★ 无目标绝不开火
            }

            // ④ 塔头转向 + 后坐回位
            RotateBarrelTowards(_target.Position, dt);
            TickRecoil(dt);

            // ⑤ 冷却结束才开火
            _fireTimer += dt;
            if (_fireTimer < Config.CooldownSec)
            {
                return;
            }
            _fireTimer = 0f;
            Fire(_target);
        }

        /// <summary>
        /// 减速光环：把射程内全部存活敌人施加/刷新减速。
        ///
        /// 【为什么按冷却间隔结算，而不是每帧刷】每帧调用 ApplySlow 会把怪的
        /// _slowTimer 一直顶在满值，那么"离开光环后该多久恢复"就取决于帧率 ——
        /// 用冷却间隔（CD）作为**施加节拍**，时长取 CD + 一个固定余量，
        /// 于是"站在光环里 = 一直被减速，走出去 0.x 秒后恢复"这件事是确定的。
        ///
        /// 【为什么不做目标列表缓存】减速塔射程内的怪随时进出，缓存要维护增删，
        /// 而空间哈希查询本身就是常数级 —— 直接查更简单也更不容易出错。
        ///
        /// 【对空规则与普通塔同一口径（2026-10-14 三塔型收敛）】
        /// 飞行单位是否吃光环，同样由塔表 canAttackAir 决定（减速塔填 1，行为不变）。
        /// 这样"这座塔能不能打到飞行怪"在代码里**只有一条判定**（FindTarget 与此处相同），
        /// 不会出现塔型分支各说各话。目标模式不在此过滤 —— 那是"选哪个目标打"的概念，
        /// 光环没有选择行为，范围内一律结算。
        ///
        /// 【不参与"对空优先"（2026-10-21 确认）】光环没有单目标，射程内的飞行与地面
        /// 一律同时结算，"优先打飞行"在这里没有落点。**不要**为了对齐而加
        /// "圈里有飞行就跳过地面"的分支 —— 那会白白削掉地面减速，属于改坏而不是改好。
        /// </summary>
        private void TickSlowAura(float dt)
        {
            _fireTimer += dt;
            if (_fireTimer < Config.CooldownSec)
            {
                return;
            }
            _fireTimer = 0f;

            CombatSystem cs = CombatSystem.Instance;
            if (cs == null || cs.Grid == null)
            {
                return;
            }

            float radius = Config.RadiusWorld;
            _candidates.Clear();
            cs.Grid.QueryCircle(Position, radius, _candidates);
            if (_candidates.Count == 0)
            {
                return;
            }

            float r2 = radius * radius;
            Vector2 self = Position;
            float ratio = Config.EffectValue;          // 配置中的减速比例
            float duration = Config.CooldownSec + SlowAuraLingerSec;
            int applied = 0;
            for (int i = 0; i < _candidates.Count; i++)
            {
                BaseEnemy e = _candidates[i];
                if (e == null || !e.IsAlive)
                {
                    continue;
                }
                // 对空过滤：与 FindTarget 同一条口径 —— 本塔打不到飞行单位时直接跳过
                if (e.Config != null && e.Config.IsFlying && !Config.CanAttackAir)
                {
                    continue;
                }
                // 网格查询会带出圆形包围盒外的元素，这里精确过滤成圆形射程
                if ((e.Position - self).sqrMagnitude > r2)
                {
                    continue;
                }
                e.ApplySlow(ratio, duration);
#if UNITY_EDITOR
                EvidenceSlowApplications++;
                RecordEvidenceEffect(e);
#endif
                applied++;
            }

            // 有怪被减速才算"开火"，供自检区分"空放"与"有效作用"
            if (applied > 0)
            {
                FireCount++;
                _auraPulseTimer = AuraPulseSec;   // 触发一次视觉脉冲
            }
        }

        /// <summary>
        /// 光环表现的每帧推进（脉冲渐隐）。**独立于结算节拍** ——
        /// 结算每 CD 才跑一次，而渐隐必须每帧推进，否则脉冲会"跳"没。
        /// 由 CombatSystem 的 TickTowers 每帧调用（与 TickAttack 并列）。
        /// </summary>
        public void TickVisual(float dt)
        {
            if (_auraView == null)
            {
                return;
            }
            if (_auraPulseTimer > 0f)
            {
                _auraPulseTimer -= dt;
                if (_auraPulseTimer < 0f)
                {
                    _auraPulseTimer = 0f;
                }
            }
            _auraView.SetPulse(_auraPulseTimer / AuraPulseSec);
        }

        /// <summary>
        /// 开火后坐：炮管沿自身"向后"退一点再回位。
        ///
        /// 【为什么要乘 localRotation】炮管是跟着目标转的，直接改 localPosition.y
        /// 在后坐方向上就错了（转 90° 时变成横着平移）。
        /// 正确做法是把"本地朝下"这个方向用炮管自身的旋转转换到父空间
        /// —— 炮管贴图原生朝上（见 BarrelNativeAngle），所以本地 -Y 就是"向后"。
        /// </summary>
        private void TickRecoil(float dt)
        {
            if (_barrel == null)
            {
                return;
            }
            if (!_barrelBaseCached)
            {
                _barrelBasePos = _barrel.localPosition;
                _barrelBaseCached = true;
            }
            if (_recoilTimer <= 0f)
            {
                return;
            }

            _recoilTimer -= dt;
            if (_recoilTimer <= 0f)
            {
                _recoilTimer = 0f;
                _barrel.localPosition = _barrelBasePos;
                return;
            }
            float k = Mathf.Clamp01(_recoilTimer / RecoilDurationSec);
            Vector3 back = _barrel.localRotation * Vector3.down;
            _barrel.localPosition = _barrelBasePos + back * (RecoilDistance * k);
        }

        private bool InRange(BaseEnemy e)
        {
            float r = Config.RadiusWorld;
            return (e.Position - Position).sqrMagnitude <= r * r;
        }

        /// <summary>本怪是否飞行（Config 缺失时按地面处理，与原对空过滤口径一致）</summary>
        private static bool IsFlying(BaseEnemy e)
        {
            return e != null && e.Config != null && e.Config.IsFlying;
        }

        /// <summary>空间哈希取候选 → 精确过滤 → 按 targetMode 打分 → 对空优先分层</summary>
        private BaseEnemy FindTarget()
        {
            return SelectBest(false);
        }

        /// <summary>只挑飞行单位（用于抢断已锁定的地面目标）</summary>
        private BaseEnemy FindAirTarget()
        {
            return SelectBest(true);
        }

        /// <summary>
        /// 选敌核心。
        ///
        /// 【对空优先（2026-10-21）】飞行单位与地面单位分成两层各自打分：
        /// 只要圈内存在本塔打得到的飞行单位，就在飞行层里按 targetMode 选，
        /// 地面层彻底不参与；没有飞行单位时才回落到地面层。
        /// 分层的意义：targetMode=0 的"最靠前"是按地面路径算的，
        /// 飞行怪走直线、没有 PathProgress，混在一起比分会把飞行怪永久压在地面怪后面。
        ///
        /// 【为什么按层而不是给分数加常数】加常数要挑一个"足够大"的值，
        /// 而 PathProgress / CurrentHp / 距离的量纲各不相同，迟早会被某个极端值穿透；
        /// 两个候选变量互不干扰，也不存在溢出与比较误差。
        /// </summary>
        /// <param name="flyingOnly">true = 只考虑飞行单位（抢断检查用）</param>
        private BaseEnemy SelectBest(bool flyingOnly)
        {
            CombatSystem cs = CombatSystem.Instance;
            if (cs == null || cs.Grid == null)
            {
                return null;
            }

            SearchCount++;
            cs.AddSearchCount(1);

            _candidates.Clear();
            cs.Grid.QueryCircle(Position, Config.RadiusWorld, _candidates);
            if (_candidates.Count == 0)
            {
                return null;   // ★ 空列表直接返回，杜绝 v1.0 的 IndexOutOfRange
            }

            float radius = Config.RadiusWorld;
            return PickBestTarget(_candidates, Position, radius * radius,
                Config.TargetMode, Config.CanAttackAir, flyingOnly);
        }

        /// <summary>
        /// 选敌策略本体：**纯函数**（不查场景、不读全局表），EditMode 可直接验证。
        /// 规则只有两条，按顺序生效：
        ///   ① 能否攻击飞行单位（塔表 canAttackAir）→ 打不到就直接剔除；
        ///   ② 对空优先 → 有可打的飞行单位就绝不选地面，层内再按 targetMode 打分。
        /// </summary>
        internal static BaseEnemy PickBestTarget(IList<BaseEnemy> candidates, Vector2 self, float radiusSqr,
            TargetMode targetMode, bool canAttackAir, bool flyingOnly)
        {
            if (candidates == null)
            {
                return null;
            }

            BaseEnemy bestAir = null;
            BaseEnemy bestGround = null;
            float bestAirScore = float.MinValue;
            float bestGroundScore = float.MinValue;

            for (int i = 0; i < candidates.Count; i++)
            {
                BaseEnemy e = candidates[i];
                if (e == null || !e.IsAlive)
                {
                    continue;
                }
                bool flying = IsFlying(e);
                // 对空过滤：本塔打不到飞行单位时**直接跳过**，
                // 而不是"锁一个打不到的目标然后空放"——那会让无目标开火的自检计数器爆掉。
                if (flying && !canAttackAir)
                {
                    continue;
                }
                if (flyingOnly && !flying)
                {
                    continue;
                }
                float d2 = (e.Position - self).sqrMagnitude;
                if (d2 > radiusSqr)
                {
                    continue;   // 网格查询会带出范围外元素，这里精确过滤
                }

                float score = ScoreCandidate(e, d2, targetMode);
                if (flying)
                {
                    if (score > bestAirScore)
                    {
                        bestAirScore = score;
                        bestAir = e;
                    }
                }
                else if (score > bestGroundScore)
                {
                    bestGroundScore = score;
                    bestGround = e;
                }
            }

            // ★ 对空优先：有能打的飞行单位就不选地面
            return bestAir != null ? bestAir : bestGround;
        }

        /// <summary>按塔表 targetMode 打分（口径与改造前完全一致，只是不再跨层比较）</summary>
        private static float ScoreCandidate(BaseEnemy e, float d2, TargetMode mode)
        {
            switch (mode)
            {
                case TargetMode.Nearest:
                    return -d2;
                case TargetMode.HighestHp:
                    return e.CurrentHp;
                default:
                    return e.PathProgress;   // 最危险优先
            }
        }

        private void RotateBarrelTowards(Vector2 targetPos, float dt)
        {
            Vector2 d = targetPos - Position;
            if (d.sqrMagnitude >= 0.000001f)
            {
                _lastDir = d.normalized;
            }
            if (_barrel == null)
            {
                return;
            }
            Vector2 bd = targetPos - (Vector2)_barrel.position;
            if (bd.sqrMagnitude < 0.000001f)
            {
                return;
            }
            float targetAngle = Mathf.Atan2(bd.y, bd.x) * Mathf.Rad2Deg - BarrelNativeAngle;
            Vector3 e = _barrel.localEulerAngles;
            float cur = e.z;
            float next = Mathf.MoveTowardsAngle(cur, targetAngle, Config.RotateSpeed * dt);
            if (Mathf.Abs(Mathf.DeltaAngle(cur, next)) >= MinRotateStep)
            {
                _barrel.localEulerAngles = new Vector3(e.x, e.y, next);
            }
        }

        /// <summary>
        /// 开火（冷却到点、有目标时由 TickAttack 调用）。
        ///
        /// 【2026-10-17 表现改版：移除真实子弹，《坚守阵地》式即时命中】
        ///   开火瞬间直接结算伤害，塔上只重放一段枪口焰序列帧（TowerFireFx）；
        ///   火力塔在落点补播爆炸序列帧。攻击节奏完全不变：
        ///   冷却间隔（CooldownSec）、索敌/锁定、伤害值（Power）、音效、后坐、震动全部照旧。
        ///   唯一的判定差异是"伤害不再等弹体飞行"——即时命中本来就是去掉真实子弹后的题中之义。
        ///
        /// 【为什么数值仍从子弹表取】aoeRadius / effectType / effectValue 的权威来源
        ///   依旧是 TBBulletData（见 BulletConfig 注释），这里只是把"弹体飞到落点才结算"
        ///   换成"开火瞬间在落点结算"，表驱动的方式没有变。
        /// </summary>
        private void Fire(BaseEnemy target)
        {
            _recoilTimer = RecoilDurationSec;   // M4-3：开火即后坐，回位在 TickRecoil 里推进

            // 屏幕震动（UI 补全 C3）：满级塔开火给一点"重火力"的手感。
            // 系数 0.15 —— 满级塔攻速不低，震感必须轻到"感觉得到但不烦人"。
            if (Config.Level >= 2 && CameraController.Instance != null && Configs.Global != null)
            {
                CameraController.Instance.Shake(
                    Configs.Global.ShakeAmplitude * 0.15f, Configs.Global.ShakeDurationSec);
            }

            // 减速光环塔走 TickSlowAura，永远不会到这里（与原 FiresBullet 口径一致的防御分支）
            if (!Config.FiresBullet)
            {
                return;
            }

            BulletConfig bulletCfg = Configs.GetBullet(Config.BulletId);
            if (bulletCfg == null)
            {
                return;
            }

            if (Config.IsAoe)
            {
                // 火力塔：落点 = 发射瞬间锁定的目标位置（与原"落点弹"锁定时机一致），
                // 对落点 aoeRadius（格）内全部存活敌人造成同等伤害 + 命中效果。
                Vector2 center = target.Position;
                DetonateAt(center, bulletCfg.AoeRadius, Config.Power, bulletCfg);
                // 爆炸的分量感：与原 BaseBullet.Explode 同系数 0.3（爆炸很频繁，晃多了没法玩）
                if (CameraController.Instance != null && Configs.Global != null)
                {
                    CameraController.Instance.Shake(
                        Configs.Global.ShakeAmplitude * 0.3f, Configs.Global.ShakeDurationSec);
                }
                TowerFireFx.PlayBlastAt(center);
            }
            else
            {
                // 普通塔：单体即时命中（原为追踪弹命中才结算，此处只去掉飞行环节）
                HurtEnemy(target, Config.Power, bulletCfg);
            }

            // 枪口焰序列帧（普通塔黄白细焰 / 火力塔橙红重焰）
            if (_muzzleFx != null)
            {
                _muzzleFx.PlayMuzzle(TowerFireFx.GetMuzzleFrames(Config.IsAoe));
            }
            if (AudioManager.Instance != null)
            {
                AudioManager.Instance.PlayAt(AudioName.TowerFire(Config.Type), MuzzlePosition);
            }
            FireCount++;
        }

        /// <summary>
        /// 对单个敌人结算一次伤害 + 命中效果（效果语义与 BaseBullet.ApplyEffect 同口径）。
        /// </summary>
        private void HurtEnemy(BaseEnemy e, float damage, BulletConfig bulletCfg)
        {
            if (e == null || !e.IsAlive)
            {
                return;
            }
#if UNITY_EDITOR
            float effective = damage * (1f - e.Config.Armor);
            EvidenceDamage += Mathf.Min(e.CurrentHp, effective);
            EvidenceOverkill += Mathf.Max(0, effective - e.CurrentHp);
            EvidenceHits++;
            RecordEvidenceEffect(e);
            if (e.Config.IsFlying) EvidenceAirHits++;
#endif
            e.Hurt(damage);
            CombatSystem.Instance.AddHitCount(1);
            ApplyHitEffect(e, bulletCfg.Effect,
                Config.EffectValue > 0f ? Config.EffectValue : bulletCfg.EffectValue);
        }

        /// <summary>
        /// 在落点引爆：对半径内可攻击的存活敌人造成伤害并施加效果。
        /// 与原 BaseBullet.Explode 同口径：范围从落点算，与落点上是否站怪无关。
        /// </summary>
        private void DetonateAt(Vector2 center, float radius, float damage, BulletConfig bulletCfg)
        {
            if (radius <= 0f)
            {
                return;
            }
            CombatSystem cs = CombatSystem.Instance;
            if (cs == null || cs.Grid == null)
            {
                return;
            }
            _candidates.Clear();
            cs.Grid.QueryCircle(center, radius, _candidates);
            float r2 = radius * radius;
            for (int i = 0; i < _candidates.Count; i++)
            {
                BaseEnemy e = _candidates[i];
                if (e == null || !e.IsAlive)
                {
                    continue;
                }
                // 命中集合与索敌使用同一对空规则，避免地面爆炸误伤贴近的飞行怪。
                if (e.Config == null || (e.Config.IsFlying && !Config.CanAttackAir))
                {
                    continue;
                }
                // 网格查询会带出范围外元素，精确过滤成圆形落点范围（与原实现一致）
                if ((e.Position - center).sqrMagnitude > r2)
                {
                    continue;
                }
                HurtEnemy(e, damage, bulletCfg);
            }
        }

        /// <summary>命中效果。与 BaseBullet.ApplyEffect 共用同一组时长常数（那里是唯一权威）。</summary>
        private void ApplyHitEffect(BaseEnemy e, EffectType effect, float effectValue)
        {
            switch (effect)
            {
                case EffectType.Slow:
                    e.ApplySlow(effectValue, BaseBullet.SlowDurationSec);
                    break;
                case EffectType.Dot:
                    e.ApplyDot(effectValue, BaseBullet.DotDurationSec);
                    break;
                default:
                    break;
            }
        }

        // ------------------------------------------------------------------
        // 表现
        // ------------------------------------------------------------------

        public void SetTint(Color c)
        {
            if (_renderers == null)
            {
                return;
            }
            for (int i = 0; i < _renderers.Length; i++)
            {
                if (_renderers[i] != null)
                {
                    _renderers[i].color = c;
                }
            }
        }

        public void SetPreviewAlpha(float a)
        {
            if (_renderers == null)
            {
                return;
            }
            for (int i = 0; i < _renderers.Length; i++)
            {
                if (_renderers[i] != null)
                {
                    Color c = _renderers[i].color;
                    c.a = a;
                    _renderers[i].color = c;
                }
            }
        }

        /// <summary>吸附到格子中心</summary>
        public void SnapToCell(CellData cell)
        {
            Cell = cell;
            transform.position = new Vector3(cell.Center.x, cell.Center.y, 0f);
        }

        public void MarkDestroyed()
        {
            IsBuilt = false;
            _target = null;
            // 枪口焰是挂在**炮管下**的子物体，随塔一起销毁；这里只清引用
            _muzzleFx = null;
            // 光环表现是挂在**塔自己**的 transform 上的子物体，随塔一起销毁；
            // 这里只把引用清掉，避免持有已销毁对象
            _auraView = null;
            _auraPulseTimer = 0f;
        }
    }

    /// <summary>
    /// 防御塔管理器：建塔（含路径校验与扣费）、出售、按格查询。
    /// v1.0 的 `GetTower&lt;T&gt;() where T : new()` 对 MonoBehaviour 是反模式，已废弃。
    ///
    /// 【注意】本类不是 MonoBehaviour（继承 BaseManager），可以与本文件共存；
    /// 而 NormalTower 是 MonoBehaviour，Unity 要求它与文件名一致，故放在 NormalTower.cs。
    /// </summary>
    public class TowerManager : BaseManager<TowerManager>
    {
        public Transform TowerParent { get; private set; }

        private readonly List<BaseTower> _towers = new List<BaseTower>(64);
        /// <summary>ClearAll 的复用缓冲（避免每次切关都分配一个 List）</summary>
        private readonly List<BaseTower> _clearBuf = new List<BaseTower>(64);

        public IList<BaseTower> Towers { get { return _towers; } }

        public void SetParent(Transform parent)
        {
            TowerParent = parent;
        }

        /// <summary>
        /// 尝试在指定格建塔。
        /// 顺序：占位校验 → 临时设墙跑 A*（堵死则回滚）→ 扣费 → 实例化。
        /// 任何一步失败都完整回滚，不会出现"扣了钱又建不成"。
        /// </summary>
        public BaseTower TryBuild(int type, int level, int row, int col)
        {
            return TryBuildInternal(type, level, row, col, true);
        }

        /// <summary>
        /// 按快照恢复一座塔（M3-5）：与 TryBuild 走**同一套**实例化/注册流程，
        /// 唯一区别是**不扣钱**（钱已经在上次游戏时扣过了）。
        ///
        /// 【为什么复用 TryBuildInternal 而不是另写一份】
        /// "建塔"这件事牵扯格子占用、A* 墙标记、战斗注册、对象池取出，
        /// 复制一份出来迟早会分叉 —— 而分叉点往往在某个不常走的分支上，很难发现。
        /// </summary>
        public BaseTower RestoreTower(int type, int level, int row, int col)
        {
            return TryBuildInternal(type, level, row, col, false);
        }

        private BaseTower TryBuildInternal(int type, int level, int row, int col, bool charge)
        {
            BoardView board = BoardView.Instance;
            if (board == null)
            {
                Debug.LogError("[Tower] BoardView 未初始化");
                return null;
            }

            CellData cell = board.GetCell(row, col);
            if (cell == null)
            {
                Tips(Localization.Get("No Tile Here") ?? "该位置无法建造");
                return null;
            }
            if (!cell.IsBuildable)
            {
                board.SetHighlight(row, col, CellHighlight.Blocked);
                Tips(Localization.Get("Not Buildable Here") ?? "该位置不可建造");
                return null;
            }
            if (cell.HasTower)
            {
                Tips(Localization.Get("Tower already there") ?? "该位置已有防御塔");
                return null;
            }

            TowerConfig cfg = Configs.GetTowerByTypeAndLevel(type, level);
            if (cfg == null)
            {
                return null;
            }

            // 怪物脚下的格子不允许建塔：否则怪物会瞬间被墙包住，视觉上像卡死
            CombatSystem combat = CombatSystem.Instance;
            if (combat != null && combat.HasAliveEnemyNear(cell.Center, board.CellSize * 0.5f))
            {
                Tips(Localization.Get("An enemy is on this tile, try another spot") ?? "该格上正有怪物，换个位置吧");
                return null;
            }

            AStarManager astar = AStarManager.Instance;
            Point point = astar.GetPoint(row, col);
            bool oldWall = point != null && point.IsWall;

            // ① 临时占位，校验不会把路完全堵死
            if (point != null)
            {
                point.IsWall = true;
            }
            if (!astar.IsFindPath())
            {
                if (point != null)
                {
                    point.IsWall = oldWall;
                }
                board.SetHighlight(row, col, CellHighlight.Blocked);
                Tips(Localization.Get("Cannot fully block the path") ?? "不能完全阻断怪物路径");
                return null;
            }

            // ② 扣费（放在路径校验之后，避免扣了钱建不成）
            //    charge=false 是"按快照恢复"路径：钱在上次游戏时已经扣过，不能再扣一次。
            if (charge && !PlayerDataManager.Instance.TrySpend(cfg.Prices))
            {
                if (point != null)
                {
                    point.IsWall = oldWall;
                }
                Tips(Localization.Get("Not enough gold") ?? "金币不足");
                return null;
            }

            // ③ 实例化
            GameObject go = ResLoader.Instance.Instantiate(cfg.ResName, TowerParent);
            if (go == null)
            {
                if (point != null)
                {
                    point.IsWall = oldWall;
                }
                if (charge)
                {
                    PlayerDataManager.Instance.AddGold(cfg.Prices);   // 退还（恢复路径没扣过，自然也不用退）
                }
                Tips(Localization.Get("Failed to load tower asset") ?? "防御塔资源加载失败");
                Debug.LogError("[Tower] 建塔失败：无法加载 " + cfg.ResName);
                return null;
            }

            BaseTower tower = go.GetComponent<BaseTower>();
            if (tower == null)
            {
                tower = go.AddComponent<NormalTower>();
            }
            tower.Init(cfg, cell);
            tower.SnapToCell(cell);

            cell.Tower = tower;
            cell.Point = point;
            _towers.Add(tower);

            CombatSystem.Instance.RegisterTower(tower);
            EventDispatcher.TriggerEvent<BaseTower>(EventName.BuildTowerSuccess, tower);
            if (AudioManager.Instance != null)
            {
                AudioManager.Instance.PlayAt(AudioName.TowerBuild, cell.Center);
            }
            astar.RequestRefresh();      // 节流重算，敌人改道

            return tower;
        }

        /// <summary>
        /// 升级一座已建造的塔（M2「换实例」方案）。
        ///
        /// 【为什么是"换实例"而不是"就地改数值"】
        ///   1. 塔的等级差异不止数值，还有外观（炮座/炮管贴图、后续可能加特效），
        ///      就地改数值无法换皮，"换实例"一步到位。
        ///   2. 不同塔型会挂不同子类组件（NormalTower / PowerTower / RetardTower），
        ///      AddComponent 覆盖旧组件会留下脏数据；换实例最干净。
        ///   3. 升级后等级/射程/伤害/攻速全部由新行的 TBTowerInfo 驱动，
        ///      不用在代码里维护任何"等级 → 数值"映射表。
        ///
        /// 【顺序很重要，且顺序本身就是正确性的一部分】
        ///   读旧状态 → 校验升级链 → 扣费（失败即返回，无副作用）
        ///   → **先实例化新塔**（失败则退还金币、旧塔原样保留）
        ///   → 摘旧塔的战斗注册与列表引用 → 新塔 Init + SnapToCell
        ///   → 写回格子 → 注册新塔 → 释放旧实例 → 广播事件（★ 全程不触发路径重算）
        ///
        /// 【为什么必须"先建后拆"】
        ///   如果先拆旧塔再实例化，一旦新塔资源加载失败，旧塔已经被 MarkDestroyed
        ///   并归还对象池 —— 玩家花了钱，格子上却什么都不剩。
        ///   先建后拆才能做到"失败时原样保留原塔"，与 TryBuild 的回滚风格一致。
        ///
        /// 【注册顺序】必须先 UnregisterTower(old) 再 RegisterTower(new)，
        ///   否则会出现短暂的双份 tick（同一格被两座塔各开一次火）。
        ///
        /// 【为什么不 RequestRefresh 路径】
        ///   换塔前后格子始终是"有塔"状态，地图阻挡关系没变，路径无需重算。
        ///   若重算反而会让怪物在升级瞬间抖动改道。
        /// </summary>
        public BaseTower TryUpgrade(BaseTower old)
        {
            // 【真机诊断埋点】升级请求进入执行层
            if (old != null)
            {
                Debug.Log("[Tower] TryUpgrade: " + old.name
                    + " (Lv." + (old.Config != null ? old.Config.Level : -1) + ")");
            }
            if (old == null || old.Config == null || !old.IsBuilt)
            {
                // 【真机诊断埋点】塔句柄无效（空/未建成）——"升级没反应"时先看这条
                Debug.LogWarning(string.Format("[Tower] TryUpgrade 失败：old={0} config={1} isBuilt={2}",
                    old == null ? "null" : old.name,
                    old == null || old.Config == null ? "null" : old.Config.Name,
                    old != null && old.IsBuilt));
                return null;
            }
            if (old.Config.IsMaxLevel)
            {
                // 【真机诊断埋点】满级拦截（按钮此时本应置灰，若用户仍点到这里说明按钮状态不同步）
                Debug.Log(string.Format("[Tower] TryUpgrade 失败：{0} 已是满级 Lv.{1}", old.Config.Name, old.Config.Level));
                Tips(Localization.Get("Tower is already at max level") ?? "该防御塔已满级");
                return null;
            }

            // 升级链：upgradeTo 指向"下一等级的 TBTowerInfo.id"，0 表示满级。
            // 走 Configs.GetNextLevel 而不是"type + level + 1"：口径只允许有一处。
            TowerConfig nextCfg = Configs.GetNextLevel(old.Config);
            if (nextCfg == null)
            {
                // 【真机诊断埋点】升级链断了（配置问题）——"升级没反应"时看这条
                Debug.LogWarning(string.Format("[Tower] TryUpgrade 失败：{0} Lv.{1} 找不到下一级配置（upgradeTo={2}）",
                    old.Config.Name, old.Config.Level, old.Config.UpgradeTo));
                Tips(Localization.Get("No next-level config available") ?? "该防御塔暂无可升级的下一级配置");
                return null;
            }

            CellData cell = old.Cell;
            if (cell == null)
            {
                // 【真机诊断埋点】塔不在格子上（数据不一致）
                Debug.LogWarning("[Tower] TryUpgrade 失败：塔不在格子上（cell=null）");
                Tips(Localization.Get("Tower is not on a tile, cannot upgrade") ?? "该防御塔不在格子上，无法升级");
                return null;
            }

            // ① 扣费（在一切破坏性操作之前，失败则完全无副作用）
            if (!PlayerDataManager.Instance.TrySpend(nextCfg.Prices))
            {
                // 【真机诊断埋点】金币不足（按钮置灰时本不该触发；若触发说明 HUD 状态不同步）
                Debug.Log(string.Format("[Tower] TryUpgrade 失败：金币不足（升级需要 {0}，现有 {1}）",
                    nextCfg.Prices, PlayerDataManager.Instance.Gold));
                Tips(Localization.Get("Not enough gold, upgrade needs {0}", nextCfg.Prices)
                    ?? string.Format("金币不足，升级需要 {0}", nextCfg.Prices));
                return null;
            }

            // ② **先实例化新塔**。此处失败必须做到"零损失"：
            //    金币退还、旧塔保持 IsBuilt、仍在 _towers、仍在 CombatSystem 注册、格子占用不变。
            GameObject go = ResLoader.Instance.Instantiate(nextCfg.ResName, TowerParent);
            if (go == null)
            {
                PlayerDataManager.Instance.AddGold(nextCfg.Prices);   // 退还
                Tips(Localization.Get("Upgrade failed: tower asset missing, gold refunded") ?? "升级失败：防御塔资源加载失败，已退还金币");
                Debug.LogError("[Tower] 升级失败：无法加载 " + nextCfg.ResName + "（原塔保持不变）");
                return null;
            }

            BaseTower tower = go.GetComponent<BaseTower>();
            if (tower == null)
            {
                tower = go.AddComponent<NormalTower>();
            }

            string oldResName = old.Config.ResName;

            // ③ 新塔已就位，才拆旧塔：只摘战斗注册与列表引用，**不动格子阻挡与路径**。
            //    顺序不变量：先 Unregister 旧的，再 Register 新的（避免双份 tick）。
            old.MarkDestroyed();
            _towers.Remove(old);
            CombatSystem.Instance.UnregisterTower(old);

            tower.Init(nextCfg, cell);
#if UNITY_EDITOR
            tower.EvidenceDamage = old.EvidenceDamage; tower.EvidenceOverkill = old.EvidenceOverkill;
            tower.EvidenceHits = old.EvidenceHits; tower.EvidenceSlowApplications = old.EvidenceSlowApplications;
            tower.EvidenceAirHits = old.EvidenceAirHits;
            tower.CopyRangeEvidenceFrom(old);
#endif
            tower.SnapToCell(cell);

            cell.Tower = tower;
            _towers.Add(tower);
            CombatSystem.Instance.RegisterTower(tower);

            // ④ 释放旧实例（放在新塔注册之后：即使释放过程出问题，战斗注册也已一致）
            ResLoader.Instance.ReleaseInstance(oldResName, old.gameObject);

            // 升级后选中态要指向"新实例"，否则面板还拿着已被销毁的旧塔
            if (TowerPlacement.Instance != null)
            {
                TowerPlacement.Instance.ReselectAfterSwap(old, tower);
            }

            // 【为什么不用 BuildTowerSuccess】它的语义是"新建了一座塔"，
            // HudView 收到会退出放置态并复位按钮 —— 升级时发它会把 HUD 状态搅乱。
            EventDispatcher.TriggerEvent<BaseTower>(EventName.TowerUpgradeSuccess, tower);
            if (AudioManager.Instance != null)
            {
                AudioManager.Instance.PlayAt(AudioName.TowerUpgrade, tower.Position);
            }
            Tips(Localization.Get("Upgraded to {0} Lv.{1}", nextCfg.DisplayName, nextCfg.Level)
                ?? string.Format("已升级为 {0} Lv.{1}", nextCfg.DisplayName, nextCfg.Level));

            return tower;
        }

        /// <summary>出售：返还金币 + 释放格子 + 请求重算路径</summary>
        public bool Sell(BaseTower tower)
        {
            if (tower == null || tower.Config == null || !tower.IsBuilt)
            {
                return false;
            }
            // 返还金额 = 配置的 sellPrice × 常数表的返还比例
            // （比例做成常数是为了以后能加"卖塔折损"的经济压力，而不用改代码）
            float rate = Configs.Global != null ? Configs.Global.SellRefundRate : 1f;
            int refund = Mathf.Max(0, Mathf.RoundToInt(tower.Config.SellPrice * rate));
            string resName = tower.Config.ResName;

            if (tower.Cell != null)
            {
                tower.Cell.Tower = null;
                if (tower.Cell.Point != null)
                {
                    tower.Cell.Point.IsWall = false;
                }
            }
            tower.MarkDestroyed();
            _towers.Remove(tower);
            CombatSystem.Instance.UnregisterTower(tower);

            PlayerDataManager.Instance.AddGold(refund);
            EventDispatcher.TriggerEvent<BaseTower>(EventName.DestroyTower, tower);
            if (AudioManager.Instance != null)
            {
                AudioManager.Instance.PlayAt(AudioName.TowerSell, tower.Position);
            }
            ResLoader.Instance.ReleaseInstance(resName, tower.gameObject);
            AStarManager.Instance.RequestRefresh();
            Tips(Localization.Get("Tower sold, refunded {0} gold", refund)
                ?? string.Format("已出售防御塔，返还 {0} 金币", refund));
            return true;
        }

        /// <summary>
        /// 清除全部防御塔（切关 / 重开用）。**不返还金币** ——
        /// 这是关卡重置，不是玩家卖塔，返还会让"重开"变成刷钱手段。
        ///
        /// 【为什么用 CombatSystem 的快照而不是遍历 _towers】
        /// ReleaseInstance 会销毁 GameObject，可能连带触发回调；
        /// 拿一份快照再逐个清理，遍历期间就不受这些副作用影响。
        /// </summary>
        public void ClearAll()
        {
            _clearBuf.Clear();
            if (CombatSystem.Instance != null)
            {
                CombatSystem.Instance.CopyTowers(_clearBuf);
            }
            for (int i = _clearBuf.Count - 1; i >= 0; i--)
            {
                BaseTower t = _clearBuf[i];
                if (t == null)
                {
                    continue;
                }
                CellData cell = t.Cell;
                if (cell != null)
                {
                    cell.Tower = null;
                    if (cell.Point != null)
                    {
                        cell.Point.IsWall = false;
                    }
                }
                string resName = t.Config != null ? t.Config.ResName : "Tower_Normal0";
                t.MarkDestroyed();
                CombatSystem.Instance.UnregisterTower(t);
                ResLoader.Instance.ReleaseInstance(resName, t.gameObject);
            }
            _towers.Clear();
            _clearBuf.Clear();
            // 落点爆炸序列帧的池与帧缓存随关卡一起清（枪口焰随塔销毁，无需处理）
            TowerFireFx.ClearPool();
        }

        private static void Tips(string msg)
        {
            EventDispatcher.TriggerEvent<string>(EventName.ShowTipEvent, msg);
        }

        public int Count { get { return _towers.Count; } }
    }
}
