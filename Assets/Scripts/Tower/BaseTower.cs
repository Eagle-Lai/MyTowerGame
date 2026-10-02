using System.Collections.Generic;
using AStar;
using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 塔型。编号与 TBTowerInfo.type 一一对应（设计文档 §8 M2 定案的五类）。
    ///
    /// 【命名与行为的偏差，只在这里解释一次】
    ///   · Power(2) 是美术名「强力塔」，其**行为**是范围伤害（AOE）—— 见 TBTowerInfo.effectType=3；
    ///   · Slow(3) 的行为是减速，而美术、节点名、资源目录一律叫 "Retard"
    ///     （映射表在 HudView.TowerTypeOf，别处不要再推导一遍）。
    /// </summary>
    public enum TowerType
    {
        None = 0,
        /// <summary>单体：普通塔</summary>
        Normal = 1,
        /// <summary>范围伤害：强力塔（美术名 Power，行为是 AOE）</summary>
        Aoe = 2,
        /// <summary>减速：美术名 Retard</summary>
        Slow = 3,
        /// <summary>穿透：一发子弹可连续命中多个敌人</summary>
        Pierce = 4,
        /// <summary>激光：瞬发命中（hitscan），不发射弹体</summary>
        Laser = 5,
    }

    /// <summary>
    /// 防御塔基类（v2.1 的 2D 版）。
    ///
    /// 相对 v1.0 的关键改动：
    ///   - 去掉 Renderer/GetComponentsInChildren 换色 → 改 SpriteRenderer.color
    ///   - **攻击逻辑抽出为 TickAttack(dt)，由 CombatSystem 集中驱动**（不再自行订阅 UpdateEvent）
    ///   - 索敌走 EnemyGrid 空间哈希 + 节流 + 目标锁定（不再用 SphereCollider / OnTriggerEnter）
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

        private BaseEnemy _target;
        private float _fireTimer;
        private float _searchTimer;
        private readonly List<BaseEnemy> _candidates = new List<BaseEnemy>(32);
        private Transform _barrel;
        private Transform _muzzle;
        private SpriteRenderer[] _renderers;
        private Vector2 _lastDir = Vector2.right;

        private const float MinRotateStep = 0.5f;

        // ---- 开火后坐（M4-3）----
        /// <summary>炮管后坐距离（世界单位）。要小到"几乎看不见但能感觉到"。</summary>
        private const float RecoilDistance = 0.07f;
        /// <summary>后坐回位时长（秒）</summary>
        private const float RecoilDurationSec = 0.09f;
        private float _recoilTimer;
        private Vector3 _barrelBasePos;
        private bool _barrelBaseCached;

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
        }

        public Vector2 Position
        {
            get { Vector2 p = transform.position; return p; }
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

            // ① 目标有效性检查：死亡/回收/走出射程 → 立即解除锁定
            if (_target != null && (!_target.IsAlive || !InRange(_target)))
            {
                _target = null;
            }

            // ② 节流索敌：已有锁定目标时不重复搜索
            _searchTimer += dt;
            if (_target == null && _searchTimer >= Config.SearchIntervalSec)
            {
                _searchTimer = 0f;
                _target = FindTarget();
            }

            if (_target == null)
            {
                return;   // ★ 无目标绝不开火
            }

            // ③ 塔头转向 + 后坐回位
            RotateBarrelTowards(_target.Position, dt);
            TickRecoil(dt);

            // ④ 冷却结束才开火
            _fireTimer += dt;
            if (_fireTimer < Config.CooldownSec)
            {
                return;
            }
            _fireTimer = 0f;
            Fire(_target);
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

        /// <summary>空间哈希取候选 → 精确过滤 → 按 targetMode 打分</summary>
        private BaseEnemy FindTarget()
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

            float r2 = Config.RadiusWorld * Config.RadiusWorld;
            Vector2 self = Position;
            BaseEnemy best = null;
            float bestScore = float.MinValue;

            for (int i = 0; i < _candidates.Count; i++)
            {
                BaseEnemy e = _candidates[i];
                if (e == null || !e.IsAlive)
                {
                    continue;
                }
                // 对空过滤：本塔打不到飞行单位时**直接跳过**，
                // 而不是"锁一个打不到的目标然后空放"——那会让无目标开火的自检计数器爆掉。
                if (e.Config != null && e.Config.IsFlying && !Config.CanAttackAir)
                {
                    continue;
                }
                float d2 = (e.Position - self).sqrMagnitude;
                if (d2 > r2)
                {
                    continue;   // 网格查询会带出范围外元素，这里精确过滤
                }

                float score;
                switch (Config.TargetMode)
                {
                    case TargetMode.Nearest:
                        score = -d2;
                        break;
                    case TargetMode.HighestHp:
                        score = e.CurrentHp;
                        break;
                    default:
                        score = e.PathProgress;   // 最危险优先
                        break;
                }
                if (score > bestScore)
                {
                    bestScore = score;
                    best = e;
                }
            }
            return best;
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

        private void Fire(BaseEnemy target)
        {
            _recoilTimer = RecoilDurationSec;   // M4-3：开火即后坐，回位在 TickRecoil 里推进

            // ---- 激光：瞬发命中（hitscan），不生成弹体 ----
            // 【为什么不做成"速度极高的子弹"】那会引入高速穿透漏判
            // （BulletConfig.IsSpeedSafeAtFps 就是为这个坑准备的自检），
            // 而且激光本来就该是"立即结算"，用弹体反而要额外处理寿命与回收。
            if (Config.IsLaser)
            {
                if (target == null || !target.IsAlive)
                {
                    return;   // ★ 无目标绝不开火（与普通塔同一条不变量）
                }
                Vector2 muzzle = MuzzlePosition;
                target.Hurt(Config.Power);
                LaserBeamView.Fire(muzzle, target.Position);
                if (AudioManager.Instance != null)
                {
                    AudioManager.Instance.PlayAt(AudioName.TowerFire(Config.Type), muzzle);
                }
                FireCount++;
                return;
            }

            if (!Config.FiresBullet)
            {
                return;
            }

            BulletConfig bulletCfg = Configs.GetBullet(Config.BulletId);
            if (bulletCfg == null)
            {
                return;
            }
            // 把塔的 effectValue 传下去：减速塔三级强度不同就靠它
            // （子弹自身 effectValue > 0 时会被塔的值覆盖，见 BaseBullet.Init）
            BulletManager.Instance.Fire(target, Config.Power, MuzzlePosition, bulletCfg, Config.EffectValue);
            if (AudioManager.Instance != null)
            {
                AudioManager.Instance.PlayAt(AudioName.TowerFire(Config.Type), MuzzlePosition);
            }
            FireCount++;
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
                Tips("该位置无法建造");
                return null;
            }
            if (!cell.IsBuildable)
            {
                board.SetHighlight(row, col, CellHighlight.Blocked);
                Tips("该位置不可建造");
                return null;
            }
            if (cell.HasTower)
            {
                Tips("该位置已有防御塔");
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
                Tips("该格上正有怪物，换个位置吧");
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
                Tips("不能完全阻断怪物路径");
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
                Tips("金币不足");
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
                Tips("防御塔资源加载失败");
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
            if (old == null || old.Config == null || !old.IsBuilt)
            {
                return null;
            }
            if (old.Config.IsMaxLevel)
            {
                Tips("该防御塔已满级");
                return null;
            }

            // 升级链：upgradeTo 指向"下一等级的 TBTowerInfo.id"，0 表示满级。
            // 走 Configs.GetNextLevel 而不是"type + level + 1"：口径只允许有一处。
            TowerConfig nextCfg = Configs.GetNextLevel(old.Config);
            if (nextCfg == null)
            {
                Tips("该防御塔暂无可升级的下一级配置");
                return null;
            }

            CellData cell = old.Cell;
            if (cell == null)
            {
                Tips("该防御塔不在格子上，无法升级");
                return null;
            }

            // ① 扣费（在一切破坏性操作之前，失败则完全无副作用）
            if (!PlayerDataManager.Instance.TrySpend(nextCfg.Prices))
            {
                Tips(string.Format("金币不足，升级需要 {0}", nextCfg.Prices));
                return null;
            }

            // ② **先实例化新塔**。此处失败必须做到"零损失"：
            //    金币退还、旧塔保持 IsBuilt、仍在 _towers、仍在 CombatSystem 注册、格子占用不变。
            GameObject go = ResLoader.Instance.Instantiate(nextCfg.ResName, TowerParent);
            if (go == null)
            {
                PlayerDataManager.Instance.AddGold(nextCfg.Prices);   // 退还
                Tips("升级失败：防御塔资源加载失败，已退还金币");
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
            Tips(string.Format("已升级为 {0} Lv.{1}", nextCfg.Name, nextCfg.Level));

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
            Tips(string.Format("已出售防御塔，返还 {0} 金币", refund));
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
                string resName = t.Config != null ? t.Config.ResName : "Tower_Normal";
                t.MarkDestroyed();
                CombatSystem.Instance.UnregisterTower(t);
                ResLoader.Instance.ReleaseInstance(resName, t.gameObject);
            }
            _towers.Clear();
            _clearBuf.Clear();
        }

        private static void Tips(string msg)
        {
            EventDispatcher.TriggerEvent<string>(EventName.ShowTipEvent, msg);
        }

        public int Count { get { return _towers.Count; } }
    }
}
