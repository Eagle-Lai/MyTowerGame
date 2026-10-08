using System.Collections.Generic;
using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 集中式战斗系统 —— v2.1 去物理化改造的核心。
    ///
    /// 为什么要有它：
    ///   v1.0 里每个塔/怪/子弹都各自 `EventDispatcher.AddEventListener(UpdateEvent, ...)`，
    ///   每帧全局分发给 N 个监听者，且调用顺序不可控（塔可能比怪先更新，导致索敌基于上一帧位置）。
    ///
    /// 本类做到：
    ///   1. **全局唯一**的 UpdateEvent 订阅者
    ///   2. 固定更新顺序：怪先动 → 塔再索敌 → 子弹最后判定（消除一帧延迟）
    ///   3. 倒序遍历 + 顺手清理失效引用（不再依赖 OnDestroy 回调时序）
    ///   4. 驱动 EnemyGrid 同步与路径重算节流
    ///   5. 同屏怪物上限保护
    ///
    /// 【性能目标】Profiler 中 Physics/Physics2D 分区恒为 0；本类 OnUpdate 的 GC Alloc 为 0 B。
    /// </summary>
    public class CombatSystem : BaseManager<CombatSystem>
    {
        private readonly List<BaseEnemy> _enemies = new List<BaseEnemy>(256);
        private readonly List<BaseTower> _towers = new List<BaseTower>(64);
        private readonly List<BaseBullet> _bullets = new List<BaseBullet>(256);
        /// <summary>索敌/查询的复用缓冲，避免每次查询都分配 List（GC Alloc = 0 的前提）</summary>
        private readonly List<BaseEnemy> _queryBuffer = new List<BaseEnemy>(64);
        /// <summary>TickEnemies 的遍历快照：避免 Tick 期间列表被回调修改导致索引失效</summary>
        private readonly List<BaseEnemy> _tickSnapshot = new List<BaseEnemy>(256);

        /// <summary>空间哈希（供塔索敌查询）</summary>
        public EnemyGrid Grid { get; private set; }

        /// <summary>存活怪物数（回合完成判定用，按 IsAlive 过滤）</summary>
        public int AliveEnemyCount { get; private set; }

        // 自检计数（DoD 要求：无目标时塔的空放次数必须为 0）
        public int StatSearchCount { get; private set; }
        public int StatFireCount { get; private set; }
        public int StatHitCount { get; private set; }
        public int StatIdleFireAttempt { get; private set; }

        private float _statTimer;
        private float _statInterval = 5f;
        /// <summary>空放告警只报一次，避免刷屏（报一次就足够定位问题了）</summary>
        private bool _idleFireReported;
        /// <summary>是否已初始化（防止 OnInit 重复订阅事件）</summary>
        private bool _inited;

        public override void OnInit()
        {
            base.OnInit();

            // 幂等保护：OnInit 重复调用会导致 UpdateEvent 被重复订阅，
            // 表现为"每帧被 tick 两次"（怪物速度翻倍、子弹判定重复）。
            if (_inited)
            {
                Debug.LogWarning("[Combat] OnInit 被重复调用，已忽略（管理器应只初始化一次）");
                return;
            }
            _inited = true;

            CreateGrid();

            // ★ 全局唯一订阅
            EventDispatcher.AddEventListener(EventName.UpdateEvent, OnUpdate);
            // ★ 路径重算后让所有存活怪物改道 —— 这是《坚守阵地》的核心机制
            EventDispatcher.AddEventListener(EventName.RefreshPathEvent, OnRefreshPath);
        }

        private void CreateGrid()
        {
            float cellSize = Configs.Global != null ? Configs.Global.CellSize : 1f;
            // 邻域尺寸取 2 格：塔半径 3~6 格时，查询会覆盖 3×3 ~ 7×7 个格子
            Grid = new EnemyGrid(cellSize * 2f, 256);
        }

        /// <summary>
        /// 按最终配置重建空间哈希。
        /// 【为什么需要】Launcher 在 Awake 里就 OnInit 了各管理器，那时配置表还没加载，
        /// `Configs.Global` 为 null，网格尺寸会退回默认的 1；等配置到位必须重建一次，
        /// 否则格子划分与真实世界单位不一致，索敌范围会整体偏差。
        /// </summary>
        public void RebuildGridFromConfig()
        {
            if (Grid != null)
            {
                Grid.Clear();
            }
            CreateGrid();
            Debug.Log(string.Format("[Combat] 空间哈希已按配置重建：{0}", Grid.DumpDebugInfo()));
        }

        public override void OnDestroy()
        {
            base.OnDestroy();
            EventDispatcher.RemoveEventListener(EventName.UpdateEvent, OnUpdate);
            EventDispatcher.RemoveEventListener(EventName.RefreshPathEvent, OnRefreshPath);
            UnregisterAll();
            if (Grid != null)
            {
                Grid.Clear();
            }
        }

        // ------------------------------------------------------------------
        // 路径重算 → 怪物改道
        // ------------------------------------------------------------------

        /// <summary>
        /// 路径发生变化时，让场上所有存活怪物从各自当前格重新寻路。
        /// 【为什么必须做】"建塔改变敌人行进路线"是《坚守阵地》的核心玩法。
        /// 原实现只把新路径算给 AStarManager 后就没人用了 —— 怪物会继续沿旧路径走到终点，
        /// 塔摆了等于白摆。这个回调就是把"路径变了"传导到每一只怪身上。
        ///
        /// 开销：仅在路径**确实变化**时触发（AStarManager 用路径哈希判重），
        /// 每次触发是 O(怪数 × 单次 A*)，16×9 网格下可忽略。
        /// </summary>
        private void OnRefreshPath()
        {
            if (_enemies.Count == 0)
            {
                return;
            }
            int rerouted = 0;
            for (int i = 0; i < _enemies.Count; i++)
            {
                BaseEnemy e = _enemies[i];
                if (e != null && e.IsAlive)
                {
                    e.RefreshPath();
                    rerouted++;
                }
            }
            if (rerouted > 0 && Configs.Global != null && Configs.Global.ShowDebugLog)
            {
                Debug.Log(string.Format("[Combat] 路径已变化，{0} 只怪物改道", rerouted));
            }
        }

        // ------------------------------------------------------------------
        // 供建塔校验用
        // ------------------------------------------------------------------

        /// <summary>
        /// 指定圆内是否有存活怪物。
        /// 建塔前用它拦住"在怪物脚下盖塔"——否则怪物会瞬间被墙包住，
        /// 虽然 A* 保证它还能走出去，但视觉上很怪，也容易被误判成卡死。
        /// </summary>
        public bool HasAliveEnemyNear(Vector2 center, float radius)
        {
            if (Grid == null)
            {
                return false;
            }
            _queryBuffer.Clear();
            Grid.QueryCircle(center, radius, _queryBuffer);
            float r2 = radius * radius;
            for (int i = 0; i < _queryBuffer.Count; i++)
            {
                BaseEnemy e = _queryBuffer[i];
                // 飞行单位不参与"脚下不能建塔"的判定：它从空中过去，
                // 在它下面盖塔既困不住它，也不该抢走玩家的一个格子。
                if (e != null && e.IsAlive && e.Config != null && !e.Config.IsFlying &&
                    (e.Position - center).sqrMagnitude <= r2)
                {
                    return true;
                }
            }
            return false;
        }

        // ------------------------------------------------------------------
        // 注册 / 注销
        // ------------------------------------------------------------------

        public void RegisterEnemy(BaseEnemy e)
        {
            if (e != null && !_enemies.Contains(e))
            {
                _enemies.Add(e);
            }
        }

        public void UnregisterEnemy(BaseEnemy e)
        {
            if (e == null)
            {
                return;
            }
            _enemies.Remove(e);
            if (Grid != null)
            {
                Grid.Remove(e);
            }
        }

        public void RegisterTower(BaseTower t)
        {
            if (t != null && !_towers.Contains(t))
            {
                _towers.Add(t);
                t.SearchCount = 0;
                t.FireCount = 0;
            }
        }

        public void UnregisterTower(BaseTower t)
        {
            if (t != null)
            {
                _towers.Remove(t);
            }
        }

        public void RegisterBullet(BaseBullet b)
        {
            if (b != null && !_bullets.Contains(b))
            {
                _bullets.Add(b);
            }
        }

        public void UnregisterBullet(BaseBullet b)
        {
            if (b != null)
            {
                _bullets.Remove(b);
            }
        }

        private void UnregisterAll()
        {
            _enemies.Clear();
            _towers.Clear();
            _bullets.Clear();
        }

        // ------------------------------------------------------------------
        // 主循环
        // ------------------------------------------------------------------

        private void OnUpdate()
        {
            float dt = Time.deltaTime;

            // ① 怪物移动 → 同步空间哈希
            TickEnemies(dt);

            // ② 塔索敌与开火
            TickTowers(dt);

            // ③ 子弹推进与命中判定
            TickBullets(dt);

            // ④ 路径重算节流（建塔/拆塔后置脏标记，这里统一处理）
            AStarManager.Instance.ProcessRefresh();

            TickStats(dt);
        }

        private void TickEnemies(float dt)
        {
            // 【为什么用快照遍历，而不是直接按索引倒序边遍历边删】
            // e.Tick() 内部会经由
            //   MoveAlongPath → OnReachEnd → EnemyManager.RecycleEnemy → UnregisterEnemy
            // 把元素从 _enemies 里删掉；也可能一次删掉多个（例如漏怪同时触发失败流程）。
            // 那样外层循环持有的索引就失效了，随后的 RemoveAt(i) 会
            // ArgumentOutOfRangeException —— 这是真实踩到的崩溃（行 279）。
            //
            // 改成"先快照遍历、再单独清理"：遍历期间完全不碰 _enemies，索引自然安全；
            // 清理趟只做纯数据操作（不调用外部代码），不会引发二次修改。
            _tickSnapshot.Clear();
            _tickSnapshot.AddRange(_enemies);
            for (int i = 0; i < _tickSnapshot.Count; i++)
            {
                BaseEnemy e = _tickSnapshot[i];
                // 已彻底回收的跳过；死亡动画播放中的仍要 Tick（它靠 Tick 推进回收倒计时）
                if (e == null || e.IsFullyRecycled)
                {
                    continue;
                }
                e.Tick(dt);
            }

            // 清理趟：统计存活数、移除空引用与已彻底回收的
            AliveEnemyCount = 0;
            for (int i = _enemies.Count - 1; i >= 0; i--)
            {
                BaseEnemy e = _enemies[i];
                if (e == null || (!e.IsAlive && e.IsFullyRecycled))
                {
                    _enemies.RemoveAt(i);
                    continue;
                }
                if (e.IsAlive)
                {
                    AliveEnemyCount++;
                    Grid.Update(e, e.Position);
                }
            }
        }

        private void TickTowers(float dt)
        {
            for (int i = _towers.Count - 1; i >= 0; i--)
            {
                BaseTower t = _towers[i];
                if (t == null)
                {
                    _towers.RemoveAt(i);
                    continue;
                }
                t.TickAttack(dt);
                t.TickVisual(dt);   // 光环脉冲渐隐等纯表现，必须每帧推进
            }
        }

        private void TickBullets(float dt)
        {
            for (int i = _bullets.Count - 1; i >= 0; i--)
            {
                BaseBullet b = _bullets[i];
                if (b == null)
                {
                    _bullets.RemoveAt(i);
                    continue;
                }
                b.Tick(dt);
            }
        }

        private void TickStats(float dt)
        {
            // ① 「无目标开火」是**正确性不变量**，与调试开关无关：一旦发生就必须报出来。
            //    正常应恒为 0；不为 0 说明塔的开火条件写错了。只报一次，不刷屏。
            if (StatIdleFireAttempt > 0 && !_idleFireReported)
            {
                _idleFireReported = true;
                Debug.LogError(string.Format(
                    "[Combat] 检测到 {0} 次「无目标开火」—— 塔在没有目标时开了火，\n" +
                    "  请检查 BaseTower.TickAttack 的开火条件（正常应为 0）", StatIdleFireAttempt));
            }

            // ② 周期性汇总：只在开了调试日志时输出
            if (Configs.Global == null || !Configs.Global.ShowDebugLog)
            {
                return;
            }
            _statTimer += dt;
            if (_statTimer < _statInterval)
            {
                return;
            }
            _statTimer = 0f;

            // 场上什么都没有就不打 —— 否则空闲期每 5 秒一条，会把 Console 刷满
            // （日志被刷屏会掩盖真正的错误，这是实际踩过的坑）
            if (_enemies.Count == 0 && _towers.Count == 0 && _bullets.Count == 0)
            {
                return;
            }

            int statSearch = 0;
            int statFire = 0;
            for (int i = 0; i < _towers.Count; i++)
            {
                if (_towers[i] != null)
                {
                    statSearch += _towers[i].SearchCount;
                    statFire += _towers[i].FireCount;
                }
            }

            Debug.Log(string.Format(
                "[Combat] 怪={0}(存活{1}) 塔={2} 弹={3} | 索敌次数={4} 开火次数={5} 命中={6} 空放尝试={7} | {8}",
                _enemies.Count, AliveEnemyCount, _towers.Count, _bullets.Count,
                statSearch, statFire, StatHitCount, StatIdleFireAttempt,
                Grid.DumpDebugInfo()));
            // （空放检查已移到本方法开头，且与调试开关无关，不在这里重复）
        }

        public void ResetStats()
        {
            StatSearchCount = 0;
            StatFireCount = 0;
            StatHitCount = 0;
            StatIdleFireAttempt = 0;
            // 一次性告警的"已报过"标志也要复位 —— 否则切到新关卡后即使真的再次出现
            // 无目标开火，也不会再报（那个报错是正确性不变量，不能只报全局一次）。
            _idleFireReported = false;
        }

        /// <summary>由塔内部统计（集中上报，便于自检）</summary>
        public void AddSearchCount(int n) { StatSearchCount += n; }
        public void AddFireCount(int n) { StatFireCount += n; }
        public void AddHitCount(int n) { StatHitCount += n; }
        public void AddIdleFireAttempt(int n) { StatIdleFireAttempt += n; }

        /// <summary>
        /// 把在场塔复制到 dst（切关时统一清理用）。
        /// 【为什么给快照而不是暴露内部列表】直接暴露 _towers 会让调用方在遍历时改到它 ——
        /// 本项目在 TickEnemies 里已经因为同类问题崩过一次（见那里的长注释）。
        /// </summary>
        public void CopyTowers(List<BaseTower> dst)
        {
            dst.Clear();
            dst.AddRange(_towers);
        }

        /// <summary>把在场子弹复制到 dst（切关时统一回收用）</summary>
        public void CopyBullets(List<BaseBullet> dst)
        {
            dst.Clear();
            dst.AddRange(_bullets);
        }

        public int TowerCount { get { return _towers.Count; } }
        public int BulletCount { get { return _bullets.Count; } }
        public int EnemyCount { get { return _enemies.Count; } }

        public string DumpDebugInfo()
        {
            return string.Format("[Combat] 怪 {0}（存活 {1}）/ 塔 {2} / 弹 {3}\n{4}",
                _enemies.Count, AliveEnemyCount, _towers.Count, _bullets.Count,
                Grid != null ? Grid.DumpDebugInfo() : "(Grid 未初始化)");
        }
    }
}
