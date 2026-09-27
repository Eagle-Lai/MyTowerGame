using System.Collections.Generic;
using AStar;
using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 怪物管理器（v2.1 的 2D 版）。
    ///
    /// 相对 v1.0 的关键改动：
    ///   - **修复池化字典键硬编码 Bug**：v1.0 无论真实类型如何都把敌人登记到
    ///     `EnemyType.NormalEnemy` 列表，导致类型错乱。现按**资源名**分池，天然正确。
    ///   - 数值全部来自 TBEnemyData（v1.0 血量硬编码 GlobalConst.EnemyHp=6）
    ///   - 统一使用通用 ObjectPool；回收时 CompleteReset 状态
    /// </summary>
    public class EnemyManager : BaseManager<EnemyManager>
    {
        public Transform EnemyParent { get; private set; }

        /// <summary>按资源名分池（每个 prefab 一个池）</summary>
        private readonly Dictionary<string, ObjectPool<BaseEnemy>> _pools =
            new Dictionary<string, ObjectPool<BaseEnemy>>();

        private readonly List<BaseEnemy> _all = new List<BaseEnemy>(256);

        public override void OnInit()
        {
            base.OnInit();
        }

        public override void OnDestroy()
        {
            base.OnDestroy();
            foreach (KeyValuePair<string, ObjectPool<BaseEnemy>> kv in _pools)
            {
                kv.Value.Clear(e =>
                {
                    if (e != null && e.gameObject != null)
                    {
                        Object.Destroy(e.gameObject);
                    }
                });
            }
            _pools.Clear();
            _all.Clear();
        }

        public void SetParent(Transform parent)
        {
            EnemyParent = parent;
        }

        /// <summary>
        /// 生成一只怪物。
        /// </summary>
        /// <param name="enemyId">TBEnemyData 的 id</param>
        /// <returns>生成失败返回 null</returns>
        public BaseEnemy Spawn(int enemyId)
        {
            EnemyConfig cfg = Configs.GetEnemy(enemyId);
            if (cfg == null)
            {
                Debug.LogWarning(string.Format("[Enemy] 生成失败：找不到怪物配置 id={0}", enemyId));
                return null;
            }
            if (string.IsNullOrEmpty(cfg.ResName))
            {
                Debug.LogWarning(string.Format("[Enemy] 生成失败：怪物 id={0} 未配置 resName", enemyId));
                return null;
            }

            // 同屏上限保护（低端机性能兜底）
            CombatSystem cs = CombatSystem.Instance;
            if (cs != null && Configs.Global != null && cs.AliveEnemyCount >= Configs.Global.MaxEnemyAlive)
            {
                Debug.LogWarning(string.Format(
                    "[Enemy] 同屏怪物已达上限 {0}，本次生成被跳过（可在 TBGlobal.maxEnemyAlive 调整）",
                    Configs.Global.MaxEnemyAlive));
                return null;
            }

            ObjectPool<BaseEnemy> pool = GetPool(cfg.ResName);
            BaseEnemy enemy = pool.Get();
            if (enemy == null)
            {
                Debug.LogError(string.Format(
                    "[Enemy] 创建失败：资源「{0}」不可用，请检查 ResTable 与预制体是否存在", cfg.ResName));
                return null;
            }

            List<Point> path = AStarManager.Instance.GetPath();
            if (path == null || path.Count == 0)
            {
                Debug.LogWarning("[Enemy] 当前无可用路径，生成被取消");
                pool.Release(enemy);
                return null;
            }

            if (EnemyParent != null)
            {
                enemy.transform.SetParent(EnemyParent, false);
            }

            // 出生点 = 路径第一格
            Vector2 spawn = path[0].Center;
            enemy.transform.position = new Vector3(spawn.x, spawn.y, 0f);

            enemy.Init(cfg, path);
            cs.RegisterEnemy(enemy);
            return enemy;
        }

        private ObjectPool<BaseEnemy> GetPool(string resName)
        {
            ObjectPool<BaseEnemy> pool;
            if (_pools.TryGetValue(resName, out pool))
            {
                return pool;
            }
            int prewarm = Configs.Global != null ? Mathf.Max(8, Configs.Global.EnemyPoolSize / 4) : 16;
            string captured = resName;
            pool = new ObjectPool<BaseEnemy>(
                create: () => CreateEnemy(captured),
                reset: e => e.OnRecycle(),
                maxSize: 512,
                prewarm: 0);
            _pools[resName] = pool;
            return pool;
        }

        private BaseEnemy CreateEnemy(string resName)
        {
            if (EnemyParent == null)
            {
                GameObject root = GameObject.Find("EnemyRoot");
                EnemyParent = root != null ? root.transform : null;
            }

            GameObject go = ResLoader.Instance.Instantiate(resName, EnemyParent);
            if (go == null)
            {
                return null;
            }
            BaseEnemy e = go.GetComponent<BaseEnemy>();
            if (e == null)
            {
                e = go.AddComponent<BaseEnemy>();
            }
            _all.Add(e);
            go.SetActive(false);
            return e;
        }

        /// <summary>回收（由 BaseEnemy 在死亡动画播完 / 漏怪时调用）</summary>
        public void RecycleEnemy(BaseEnemy e)
        {
            if (e == null)
            {
                return;
            }
            CombatSystem.Instance.UnregisterEnemy(e);
            if (Configs.Global != null && Configs.Global.ShowDebugLog && e.Config != null)
            {
                // 便于排查"怪物为何消失"
                // Debug.Log(string.Format("[Enemy] 回收 {0}", e.Config.Id));
            }
            string resName = e.Config != null ? e.Config.ResName : "Enemy_Rat";
            ObjectPool<BaseEnemy> pool = GetPool(resName);
            pool.Release(e);
        }

        /// <summary>清除全部怪物（关卡重置用）</summary>
        public void ClearAll()
        {
            for (int i = _all.Count - 1; i >= 0; i--)
            {
                BaseEnemy e = _all[i];
                if (e != null)
                {
                    CombatSystem.Instance.UnregisterEnemy(e);
                    e.OnRecycle();
                }
            }
        }

        public int PooledCount
        {
            get
            {
                int n = 0;
                foreach (KeyValuePair<string, ObjectPool<BaseEnemy>> kv in _pools)
                {
                    n += kv.Value.IdleCount;
                }
                return n;
            }
        }

        public int TotalCreated
        {
            get
            {
                int n = 0;
                foreach (KeyValuePair<string, ObjectPool<BaseEnemy>> kv in _pools)
                {
                    n += kv.Value.CreatedTotal;
                }
                return n;
            }
        }

        public string DumpDebugInfo()
        {
            return string.Format("[Enemy] 池数={0} 空闲={1} 累计创建={2} 存活={3}",
                _pools.Count, PooledCount, TotalCreated,
                CombatSystem.Instance != null ? CombatSystem.Instance.AliveEnemyCount : 0);
        }
    }
}
