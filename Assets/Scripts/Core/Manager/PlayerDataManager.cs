using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 玩家数据（金币 / 生命 / 统计）。
    ///
    /// 【规则】所有金币变更**必须**走 TrySpend / AddGold，禁止直接改字段，
    /// 以保证事件与 UI 始终一致。
    ///
    /// 相对 v1.0 的补齐：
    ///   - v1.0 只有显示文本，建塔不扣费、击杀无奖励 → 经济循环不存在
    ///   - v1.0 漏怪直接回收不扣血、无失败判定 → 玩家永不失败
    /// </summary>
    public class PlayerDataManager : BaseManager<PlayerDataManager>
    {
        public int Gold { get; private set; }
        public int Hp { get; private set; }
        public int MaxHp { get; private set; }
        public int TotalKilled { get; private set; }
        public int TotalLeaked { get; private set; }
        public int CurrentLevelId { get; private set; }
        public bool IsGameOver { get; private set; }

        public override void OnInit()
        {
            base.OnInit();
            Gold = 0;
            Hp = 0;
            MaxHp = 0;
            IsGameOver = false;
        }

        /// <summary>按关卡配置初始化经济与生命</summary>
        public void InitFromLevel(LevelConfig level)
        {
            if (level == null)
            {
                Gold = 100;
                Hp = 10;
            }
            else
            {
                Gold = level.InitialGold;
                Hp = level.InitialHp;
                CurrentLevelId = level.Id;
            }
            MaxHp = Hp;
            TotalKilled = 0;
            TotalLeaked = 0;
            IsGameOver = false;

            EventDispatcher.TriggerEvent<int, int>(EventName.GoldChangeEvent, Gold, Gold);
            EventDispatcher.TriggerEvent<int, int>(EventName.PlayerHpChangeEvent, Hp, Hp);
            EventDispatcher.TriggerEvent(EventName.PlayerStateInitEvent);

            Debug.Log(string.Format("[Player] 关卡初始化：金币 {0}，生命 {1}", Gold, Hp));
        }

        /// <summary>
        /// 从局内快照恢复（M3-5）。
        /// 【为什么不复用 InitFromLevel】那个方法会把金币/生命重置成关卡初始值并清空统计，
        /// 而恢复的场景恰恰相反 —— 要**保留**玩家打到一半的状态。
        /// </summary>
        public void RestoreState(int levelId, int gold, int hp, int maxHp)
        {
            CurrentLevelId = levelId;
            Gold = Mathf.Max(0, gold);
            MaxHp = Mathf.Max(1, maxHp);
            Hp = Mathf.Clamp(hp, 0, MaxHp);
            IsGameOver = false;

            EventDispatcher.TriggerEvent<int, int>(EventName.GoldChangeEvent, Gold, 0);
            EventDispatcher.TriggerEvent<int, int>(EventName.PlayerHpChangeEvent, Hp, 0);
            EventDispatcher.TriggerEvent(EventName.PlayerStateInitEvent);

            Debug.Log(string.Format("[Player] 从快照恢复：金币 {0}，生命 {1}/{2}", Gold, Hp, MaxHp));
        }

        /// <summary>
        /// 只读检查余额是否够（不扣除）。
        /// 塔放置预览需要每帧判断能否建造，用这个而不是 TrySpend —— 后者会产生副作用。
        /// </summary>
        public bool TryPeek(int amount)
        {
            return amount <= 0 || Gold >= amount;
        }

        /// <summary>尝试消费；余额不足返回 false 且不扣除</summary>
        public bool TrySpend(int amount)
        {
            if (amount <= 0)
            {
                return true;
            }
            if (Gold < amount)
            {
                return false;
            }
            Gold -= amount;
            EventDispatcher.TriggerEvent<int, int>(EventName.GoldChangeEvent, Gold, -amount);
            return true;
        }

        public void AddGold(int amount)
        {
            if (amount <= 0)
            {
                return;
            }
            Gold += amount;
            EventDispatcher.TriggerEvent<int, int>(EventName.GoldChangeEvent, Gold, amount);
        }

        /// <summary>击杀敌人（由 BaseEnemy.Die 调用，奖励已在外部结算）</summary>
        public void OnEnemyKilled()
        {
            TotalKilled++;
        }

        /// <summary>漏怪扣血；归零则判定失败</summary>
        public void LoseHp(int amount)
        {
            if (amount <= 0 || IsGameOver)
            {
                return;
            }
            Hp = Mathf.Max(0, Hp - amount);
            TotalLeaked++;
            EventDispatcher.TriggerEvent<int, int>(EventName.PlayerHpChangeEvent, Hp, -amount);

            if (Hp <= 0)
            {
                IsGameOver = true;
                Debug.Log("[Player] 生命归零，判定失败");
                if (AudioManager.Instance != null)
                {
                    AudioManager.Instance.Play(AudioName.Defeat);
                }
                EventDispatcher.TriggerEvent<bool>(EventName.GameOverEvent, false);
            }
        }

        /// <summary>通关（由回合流程调用）</summary>
        public void Win()
        {
            if (IsGameOver)
            {
                return;
            }
            IsGameOver = true;
            Debug.Log("[Player] 全部回合完成，判定胜利");
            if (AudioManager.Instance != null)
            {
                AudioManager.Instance.Play(AudioName.Victory);
            }
            EventDispatcher.TriggerEvent<bool>(EventName.GameOverEvent, true);
        }

        public string DumpDebugInfo()
        {
            return string.Format("[Player] 金币={0} 生命={1}/{2} 击杀={3} 漏怪={4} 结束={5}",
                Gold, Hp, MaxHp, TotalKilled, TotalLeaked, IsGameOver);
        }
    }
}
