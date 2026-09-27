using System.Collections.Generic;
using cfg;

namespace FTProject
{
    /// <summary>
    /// 回合配置视图（TBRoundData 的一行 = 一个回合）。
    /// 一个关卡由若干个回合组成（SceneInfo.RoundList）。
    /// </summary>
    public class RoundConfig
    {
        private readonly RoundData _r;

        public RoundConfig(RoundData r)
        {
            _r = r;
        }

        public RoundData Raw { get { return _r; } }

        public int Id { get { return _r.Id; } }
        public string Name { get { return _r.Name; } }

        /// <summary>本回合包含的波次 id 列表 → TBEnemyList</summary>
        public List<int> WaveIds { get { return _r.EnemyIndexs; } }

        /// <summary>本回合开始前的准备时间（毫秒）</summary>
        public int StartDelayMs { get { return _r.Interval; } }

        /// <summary>本回合通关奖励金币</summary>
        public int RewardGold { get { return _r.RewardGold; } }

        public int WaveCount { get { return _r.EnemyIndexs != null ? _r.EnemyIndexs.Count : 0; } }

        public override string ToString()
        {
            return string.Format("RoundConfig(id={0}, waves={1})", Id, WaveCount);
        }
    }

    /// <summary>
    /// 波次编组配置视图（TBEnemyList 的一行 = 一波敌人的编组）。
    /// </summary>
    public class WaveGroupConfig
    {
        private readonly EnemyList _w;

        public WaveGroupConfig(EnemyList w)
        {
            _w = w;
        }

        public EnemyList Raw { get { return _w; } }

        public int Id { get { return _w.Id; } }

        /// <summary>本波出现的怪物 id 列表（按顺序生成）→ TBEnemyData</summary>
        public List<int> EnemyIds { get { return _w.EnemyIndexs; } }

        /// <summary>本波相对回合开始的延迟（毫秒）</summary>
        public int StartDelayMs { get { return _w.Interval; } }

        /// <summary>波内相邻两只怪的生成间隔（毫秒）</summary>
        public float SpawnIntervalMs { get { return _w.EnemyInterval; } }

        /// <summary>波内生成间隔（秒）</summary>
        public float SpawnIntervalSec
        {
            get { return (_w.EnemyInterval > 0f ? _w.EnemyInterval : 200f) / 1000f; }
        }

        public string Desc { get { return _w.Desc; } }

        public int EnemyCount { get { return _w.EnemyIndexs != null ? _w.EnemyIndexs.Count : 0; } }

        public override string ToString()
        {
            return string.Format("WaveGroupConfig(id={0}, enemies={1}, gap={2}ms)",
                Id, EnemyCount, SpawnIntervalMs);
        }
    }
}
