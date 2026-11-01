using System;
using System.Collections.Generic;
using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 一座塔在"通关阵型"里的最小记录：格位 + 塔型 + 等级。
    ///
    /// 【为什么要 type + level 而不是配置 id】恢复时要走 `Configs.GetTowerByTypeAndLevel`，
    ///   而塔表已按关拆分（每关一套 id）。存 id 会在换关/改表后指向别的行，
    ///   存 (type, level) 则是跨关稳定的语义坐标。
    /// 【为什么不存坐标/朝向/冷却】塔的位置完全由格子决定（`SnapToCell`），
    ///   冷却与炮管相位属于"打怪过程中的瞬时状态"，与布阵无关，存了反而制造假精确。
    /// </summary>
    [Serializable]
    public class TowerLayoutEntry
    {
        public int row;
        public int col;
        public int type;
        public int level;

        /// <summary>
        /// 这座塔**累计花了多少钱**（建造 + 历次升级）。
        ///
        /// 【为什么阵型里必须带钱（2026-11-01 追加）】
        ///   还原塔的出售返还走 `min(配置售价, 实际投入) × 比例`（见 `TowerManager.RefundOf`）。
        ///   不带这一项，还原出来的塔投入只能是 0，卖出去就是 +0 ——
        ///   同一座塔"退出前卖 22、重进后卖 0"，玩家看到的是返还凭空消失。
        ///   带上它，还原塔的投入与它离开时的真值一致，买卖口径跨会话闭合。
        /// 【为什么存"投入"而不是"售价"】售价是配置常数，投入才随升级累加；
        ///   若把售价存进来当上限，等于每次还原都把上限放宽到满售价，返还就不再受投入约束。
        /// 【老记录怎么读】JsonUtility 对缺失字段填 0；是否真的"存过"由
        ///   <see cref="hasInvested"/> 判断，不能拿 0 当哨兵（见下）。
        ///   本次不需要升 FormatVersion —— 升版本会把老玩家的阵型整本作废。
        /// </summary>
        public int investedGold;

        /// <summary>
        /// 这条记录是否带 <see cref="investedGold"/>。2026-11-01 之后写的一律为 true。
        ///
        /// 【为什么不用 investedGold == 0 当哨兵】"0 投入"和"不知道投入"是两件事：
        ///   前者理论上不存在（建塔必然花钱），但把语义压在一个数值上，
        ///   以后一旦出现合法 0（赠送塔、活动塔），"老档兜底"就会悄悄把赠送塔算成有投入。
        ///   显式开关与 `resourcesSaved` / `runSaved` 的老档兼容策略保持一致。
        /// 【false 时怎么算】老档没有投入信息，还原时用"本等级配置售价"兜底：
        ///   `min(售价, 售价) × 比例` = 售价 × 比例，与正常塔的返还额完全一致，
        ///   不会因为升级过而多发，也不会像写死 0 那样让返还凭空消失。
        /// </summary>
        public bool hasInvested;
    }

    /// <summary>单关的布阵与资源记录（一关只保留一份，后写整条覆盖前写）。</summary>
    [Serializable]
    public class LevelLayout
    {
        public int formatVersion = LevelLayoutStore.FormatVersion;
        public int levelId;
        /// <summary>写入时刻（UTC 秒）。排查"这是哪一次通关留下的阵型"时最有用。</summary>
        public long savedAtUnix;
        /// <summary>产生这份记录的那一局的 runId（只有整关通关那次才有，波次写传 null）。</summary>
        public string runId;
        /// <summary>冗余计数：读档时先做一次廉价校验，不必盲信列表长度。</summary>
        public int towerCount;
        public List<TowerLayoutEntry> towers = new List<TowerLayoutEntry>();

        /// <summary>
        /// 是否带了金币/生命（2026-10-31 追加）。
        /// 【为什么需要这个开关】老记录（只有塔阵）没有这三个字段，JsonUtility 会把它们读成 0；
        ///   不区分的话，老记录一还原就把金币和生命清零 —— 直接送玩家一个"0 血开局"。
        ///   所以资源必须显式声明"存过"才允许覆盖。
        /// </summary>
        public bool resourcesSaved;
        public int gold;
        public int hp;
        public int maxHp;

        /// <summary>
        /// 是否带"局内进度"（波次游标 + 运行统计）。2026-10-31 第二轮追加。
        ///
        /// 【为什么整份 LevelRunMetrics 都要存】只存游标是不够的：评级要核对
        ///   `completedWaveCount == expectedWaveCount`、`successfulSpawned == expectedEnemyCount`、
        ///   每波指标、计时……缺了任何一项，续玩通关会被判 "Incomplete waves / Spawn count mismatch"
        ///   → 星级不落库 → 下一关也解不开。所以必须把运行统计原样带过去，接着累加。
        /// 【为什么用开关而不是看游标是否为 0】游标 0 是合法值（第 1 波还没过），
        ///   不能拿它当"没存过"的哨兵。
        /// </summary>
        public bool runSaved;
        /// <summary>已通过的波数（= `GameFlowManager._roundCursor`）。</summary>
        public int roundCursor;
        /// <summary>存盘时本关计时是否在跑（见 `GameClock.RestoreTimers`）。</summary>
        public bool levelTimerStarted;
        /// <summary>整份运行统计（含每波明细），续玩时原样接着用。</summary>
        public LevelRunMetrics runMetrics;
    }

    /// <summary>
    /// 全部关卡的阵型册。
    ///
    /// 【为什么整本存一个 kv 键，而不是每关一个键】
    ///   1. 读取要么"全有"要么"全无"，不会出现"第 3 关解析成功、第 4 关坏了"的半截状态；
    ///   2. 覆盖写入天然是原子的（一次 INSERT OR REPLACE），不需要"先删旧再写新"两步；
    ///   3. 规模可控：30 关 × 最多几十座塔，整本 json 也就几十 KB，
    ///      相比多键枚举/前缀删除的实现成本，这点体积不值得优化。
    /// </summary>
    [Serializable]
    public class LevelLayoutBook
    {
        public int formatVersion = LevelLayoutStore.FormatVersion;
        public List<LevelLayout> levels = new List<LevelLayout>();

        public LevelLayout Find(int levelId)
        {
            if (levels == null)
            {
                return null;
            }
            for (int i = 0; i < levels.Count; i++)
            {
                LevelLayout l = levels[i];
                if (l != null && l.levelId == levelId)
                {
                    return l;
                }
            }
            return null;
        }

        /// <summary>
        /// 清旧写新：同一关只保留最新一份。
        /// 【语义】2026-10-31 用户口径 —— 每次通关都把该关旧阵型"清掉再写入本次阵型"，
        ///   所以这里不是"追加历史"，而是"替换当前值"。
        /// </summary>
        public void Upsert(LevelLayout layout)
        {
            if (layout == null)
            {
                return;
            }
            if (levels == null)
            {
                levels = new List<LevelLayout>();
            }
            for (int i = 0; i < levels.Count; i++)
            {
                if (levels[i] != null && levels[i].levelId == layout.levelId)
                {
                    levels[i] = layout;
                    return;
                }
            }
            levels.Add(layout);
        }
    }

    /// <summary>
    /// 关卡布阵 + 资源的落盘入口（业务门面之外的一个小仓库）。
    ///
    /// ==================================================================
    /// 【口径（2026-10-31 用户定案，逐步收敛）】
    ///   · **每通过一波就写**：`GameFlowManager.FinishRound` 在回合结算后调用
    ///     <see cref="SaveCurrentLevel"/>，同时记下**塔阵 + 金币 + 生命**。
    ///     （用户实测场景：打一波 → 回选关 → 再进，塔和资源都要还在。）
    ///   · **整关通关再写一次**：`CompleteVictory` 里 `RecordClear` 成功后写，带 runId，属权威覆盖。
    ///   · 每关一份，**后写整条替换前写**（清旧写新），不做历史累积。
    ///   · 进入某关时若存在记录：塔阵**免费还原**（不扣金币），金币/生命**直接覆盖**成记录值。
    ///   · 失败 / 中途退出 / 杀进程：不写（但那之前已通过的波次已经存过了）。
    ///
    /// 【和 10-30 停写的 level_snapshot 差在哪】
    ///   差在**波次游标**：本类不存"打到第几波"，重进一定从第 1 波开始。
    ///   所以金币/生命虽然是"打到一半"的数值，却不能用来跳波。
    ///   代价：重进后重打前面几波会再赚一遍钱，"退关 → 重进"仍能把金币滚大
    ///   （用户 2026-10-31 明确接受这个便利；要彻底闭合必须连波次游标一起存，
    ///   那等于把 10-30 废止的续玩快照恢复回来，需用户另行确认）。
    ///
    /// 【为什么免费还原不会变成刷金币】
    ///   塔的出售返还口径是 `min(配置售价, 实际投入) × 返还比例`
    ///   （见 `TowerManager.RefundOf`），而"实际投入"随阵型一起落盘
    ///   （<see cref="TowerLayoutEntry.investedGold"/>），所以：
    ///   · 还原塔卖出拿回的是"它当年投入的一部分"，含它自己；
    ///   · 返还额永远 ≤ 投入，卖塔本身不可能增殖；
    ///   · 关键在于**卖塔立刻再落盘一次**（`GameFlowManager.OnTowerSold`）：
    ///     塔从记录里消失、金币进记录，否则"卖完退出再进"会让塔带着投入额复活，
    ///     同一座塔可以被反复卖 —— 那才是真正的刷钱路径。
    ///   2026-11-01 之前这里是"还原塔投入 0 → 卖 0"，代价是同一座塔的返还
    ///   在退出重进前后不一致；按用户当次要求改成把投入一并存下来。
    ///
    /// 【异常策略】与存档层一致：读坏了当"没有记录"，写失败只记日志，绝不抛给玩法层。
    /// ==================================================================
    /// </summary>
    public static class LevelLayoutStore
    {
        /// <summary>
        /// 阵型记录的格式版本。字段语义一改就要 +1（旧档按"没有记录"处理）。
        ///
        /// 【2026-11-01 加了 investedGold 却故意不升版本】
        ///   这是"缺省值即旧行为"的纯增量字段：老档读出来是 0，还原塔投入 0、卖 0，
        ///   与改动前完全一致，不会算错钱。升到 2 反而会把所有老玩家的阵型整本作废
        ///   （`LoadBook` 直接返回空册），代价远大于收益。
        ///   判断标准：只有"老档的字段值会被新代码误读成另一个意思"时才必须升版本。
        /// </summary>
        public const int FormatVersion = 1;

        /// <summary>kv_store 里的唯一键。改它等于让老玩家的阵型记录全部失联。</summary>
        public const string StorageKey = "layout/campaign";

        /// <summary>
        /// 是否加密存放。阵型能换来"免费塔"，属于"改了能占便宜"的数据，
        /// 与星级/金币同级走密文（密钥不可用时数据层会自动退化为明文，不会阻断写入）。
        /// </summary>
        private const bool Sensitive = true;

        // ------------------------------------------------------------------
        // 读
        // ------------------------------------------------------------------

        /// <summary>
        /// 取某关的记录；没有 / 解析失败 / 版本不符 一律返回 false。
        ///
        /// 【为什么"全是空"的记录也算没有】2026-10-31 起记录里除了塔阵还带金币与生命，
        ///   所以判空不能只看塔数：玩家卖光塔再过一波时，塔数是 0 但金币/生命仍是有意义的存档。
        ///   只有"既没有塔、也没有资源"才说明这是一条空记录。
        /// </summary>
        public static bool TryGet(int levelId, out LevelLayout layout)
        {
            layout = null;
            if (levelId <= 0)
            {
                return false;
            }
            LevelLayoutBook book = LoadBook();
            LevelLayout found = book.Find(levelId);
            if (found == null)
            {
                return false;
            }
            bool hasTowers = found.towers != null && found.towers.Count > 0;
            bool hasResources = found.resourcesSaved && found.hp > 0 && found.maxHp > 0;
            if (!hasTowers && !hasResources)
            {
                return false;
            }
            if (found.formatVersion != FormatVersion)
            {
                Debug.LogWarning(string.Format(
                    "[Layout] 第 {0} 关阵型版本 {1} 与当前 {2} 不符，已忽略（按无记录处理）",
                    levelId, found.formatVersion, FormatVersion));
                return false;
            }
            layout = found;
            return true;
        }

        // ------------------------------------------------------------------
        // 写
        // ------------------------------------------------------------------

        /// <summary>
        /// 把**当前棋盘上的塔 + 金币/生命 + 波次进度**记成这一关的记录并落盘（同关旧记录整条替换）。
        ///
        /// 调用点与传参约定（重要）：
        ///   · `FinishRound`（每通过一波）：传 `roundCursor = _roundCursor`、`runMetrics = _run`、`runId = null`
        ///     —— 这样重进可以接着打，且评级能接着累加。
        ///   · `CompleteVictory` / `RetryPendingClearSave`（整关通关）：传 `roundCursor = 0`、`runMetrics = null`
        ///     —— 通关后再进这一关属于"重玩"，应该从第 1 波、全新评级开始，
        ///     否则一进关就 `_roundCursor >= _roundIds.Count` 立刻又判一次通关。
        /// </summary>
        public static bool SaveCurrentLevel(int levelId, int roundCursor, LevelRunMetrics runMetrics, string runId)
        {
            if (levelId <= 0)
            {
                return false;
            }
            TowerManager manager = TowerManager.Instance;
            if (manager == null)
            {
                Debug.LogWarning("[Layout] TowerManager 未就绪，本次记录未落盘");
                return false;
            }

            List<TowerLayoutEntry> entries = new List<TowerLayoutEntry>(manager.Count);
            IList<BaseTower> towers = manager.Towers;
            for (int i = 0; i < towers.Count; i++)
            {
                BaseTower tower = towers[i];
                // 只收"真正在格子上"的塔：正在被销毁/池化的实例 Cell 会被清空
                if (tower == null || !tower.IsBuilt || tower.Config == null || tower.Cell == null)
                {
                    continue;
                }
                entries.Add(new TowerLayoutEntry
                {
                    row = tower.Cell.Row,
                    col = tower.Cell.Col,
                    type = tower.Config.Type,
                    level = tower.Config.Level,
                    // 投入额一起存：还原时写回 InvestedGold，出售返还才不会因为
                    // "退出 → 重进"从"按投入算"退化成"+0"。
                    investedGold = tower.InvestedGold,
                    // 显式声明"这条记录带投入"：老档没有这个字段、读出来是 false，
                    // 还原时才知道该走"按配置售价兜底"而不是把 0 当真。
                    hasInvested = true,
                });
            }
            entries.Sort(CompareEntry);   // 固定顺序：同一套阵型每次序列化出来的字节一致，便于比对

            LevelLayout layout = new LevelLayout
            {
                levelId = levelId,
                savedAtUnix = SaveSchema.Now(),
                runId = runId,
                towerCount = entries.Count,
                towers = entries,
            };

            // 【2026-10-31 追加】金币与生命一起存。玩家数据管理器拿不到时（理论上不会发生）
            //   就不置 resourcesSaved —— 宁可只还原塔，也不能把金币/生命写成 0。
            PlayerDataManager player = PlayerDataManager.Instance;
            if (player != null)
            {
                layout.resourcesSaved = true;
                layout.gold = player.Gold;
                layout.hp = player.Hp;
                layout.maxHp = player.MaxHp;
            }

            // 【2026-10-31 第二轮】波次游标 + 整份运行统计。传 null 表示"这条记录是重玩起点"
            //   （通关时就是这么写的），不还原进度、评级从零开始。
            if (runMetrics != null)
            {
                layout.runSaved = true;
                layout.roundCursor = Mathf.Max(0, roundCursor);
                layout.levelTimerStarted = GameClock.IsLevelTimerRunning;
                layout.runMetrics = runMetrics.Clone();
            }

            LevelLayoutBook book = LoadBook();
            book.Upsert(layout);
            bool ok = WriteBook(book);
            if (ok)
            {
                Debug.Log(string.Format(
                    "[Layout] 第 {0} 关已落盘：{1} 座塔，金币 {2}，生命 {3}/{4}，波次 {5}（累计 {6} 关有记录）",
                    levelId, entries.Count, layout.gold, layout.hp, layout.maxHp,
                    layout.runSaved ? layout.roundCursor.ToString() : "从头", book.levels.Count));
            }
            return ok;
        }

        // ------------------------------------------------------------------
        // 还原
        // ------------------------------------------------------------------

        /// <summary>
        /// 把记录里的**金币 / 生命**覆盖到本局（先于塔阵还原调用）。
        ///
        /// 【为什么用 RestoreState 而不是直接改字段】`PlayerDataManager` 的金币/生命是私有 set，
        ///   且必须广播 `GoldChangeEvent` / `PlayerHpChangeEvent` / `PlayerStateInitEvent`，
        ///   否则 HUD 显示的还是初始值 —— 数据和界面就分叉了。
        /// 【老记录怎么办】没有 `resourcesSaved` 的记录（只有塔阵的旧档）**一律不动资源**，
        ///   否则 JsonUtility 会把缺省值 0 读进来，等于给玩家一个 0 血 0 金的开局。
        /// 【异常值】hp ≤ 0 或 maxHp ≤ 0 视为脏数据，直接跳过（宁可用关卡初始值）。
        /// </summary>
        public static bool RestoreResources(LevelLayout layout, int killed = 0, int leaked = 0)
        {
            if (layout == null || !layout.resourcesSaved)
            {
                return false;
            }
            if (layout.hp <= 0 || layout.maxHp <= 0)
            {
                Debug.LogWarning(string.Format(
                    "[Layout] 第 {0} 关记录里的生命数据无效（{1}/{2}），保留关卡初始值",
                    layout.levelId, layout.hp, layout.maxHp));
                return false;
            }
            PlayerDataManager player = PlayerDataManager.Instance;
            if (player == null)
            {
                return false;
            }
            // killed / leaked 传进来是为了让本局统计接着累加：
            //   续玩后结算要报"击杀 N / 漏怪 M"，从 0 开始会把前面几波的数据抹掉。
            player.RestoreState(layout.levelId, layout.gold, layout.hp, layout.maxHp, killed, leaked);
            Debug.Log(string.Format("[Layout] 第 {0} 关资源已还原：金币 {1}，生命 {2}/{3}",
                layout.levelId, layout.gold, layout.hp, layout.maxHp));
            return true;
        }

        /// <summary>
        /// 把记录里的阵型免费摆回棋盘，返回成功摆出的塔数（不碰金币/生命）。
        ///
        /// 【为什么免费】用户 2026-10-31 明确要"重进时免费还原"：这是给重打老关的便利，
        ///   不是本局经济的一部分 —— 所以走 `TowerManager.RestoreTower`（不扣钱）。
        ///   金币/生命由 <see cref="RestoreResources"/> 单独覆盖，两边互不抵扣。
        /// 【"免费摆"和"卖得出钱"不矛盾】免费指的是**摆回来不扣钱**；塔的
        ///   <see cref="BaseTower.InvestedGold"/> 仍是它当年的累计投入（随记录带回来），
        ///   所以卖出去的返还额与退出前一致。两个口径分别对应"进场"和"离场"，
        ///   都不允许凭空生钱：摆回来不扣、卖出去也不超过投入。
        /// 【为什么整批还原】批量期间不发 `BuildTowerSuccess`、不逐塔重算路径，
        ///   否则 HUD 会被 N 次"建塔成功"刷一遍、A* 也会被 N 次改道请求打满。
        /// 【失败怎么办】某座塔摆不下（地图改过 / 该格现在不可建）就跳过并记警告，
        ///   其余照常还原 —— 绝不能因为一条脏记录让整关进不去。
        /// </summary>
        public static int RestoreTowers(LevelLayout layout)
        {
            if (layout == null || layout.towers == null || layout.towers.Count == 0)
            {
                return 0;
            }
            TowerManager manager = TowerManager.Instance;
            if (manager == null)
            {
                Debug.LogWarning("[Layout] TowerManager 未就绪，跳过阵型还原");
                return 0;
            }

            int restored = 0;
            int skipped = 0;
            manager.BeginRestoreBatch();
            try
            {
                for (int i = 0; i < layout.towers.Count; i++)
                {
                    TowerLayoutEntry entry = layout.towers[i];
                    if (entry == null)
                    {
                        continue;
                    }
                    // 投入额：新记录直接用存档值；老记录（hasInvested=false）没有这项信息，
                    // 走"本等级配置售价"兜底 —— 算出来的返还额与正常塔完全一致
                    //（min(售价, 售价) × 比例），既不因为升级过而多发，也不是写死 0。
                    // Mathf.Max 兜底脏数据，别让负数把 RefundOf 的 min 拉成负值。
                    int invested = entry.hasInvested
                        ? Mathf.Max(0, entry.investedGold)
                        : FallbackInvested(entry.type, entry.level);
                    BaseTower tower = manager.RestoreTower(
                        entry.type, entry.level, entry.row, entry.col, invested);
                    if (tower != null)
                    {
                        restored++;
                    }
                    else
                    {
                        skipped++;
                    }
                }
            }
            finally
            {
                manager.EndRestoreBatch();
            }

            Debug.Log(string.Format(
                "[Layout] 第 {0} 关阵型已免费还原：{1} 座（跳过 {2} 座，来源 runId={3}）",
                layout.levelId, restored, skipped, string.IsNullOrEmpty(layout.runId) ? "-" : layout.runId));
            return restored;
        }

        /// <summary>
        /// 老记录（没有 `investedGold`）的投入兜底：取本等级的配置售价。
        ///
        /// 【为什么是售价】售价在数值设计上就是"累计投入的约七成"，
        ///   以它为上限算出来的返还额，与新记录里"投入 ≥ 售价"的正常塔完全一致 ——
        ///   老档玩家不会因为这次改动而少拿或多拿。
        /// 【配置缺失怎么办】改表删了行 / 类型越界时返回 0：宁可少给，不可凭空造钱。
        /// </summary>
        private static int FallbackInvested(int type, int level)
        {
            TowerConfig cfg = Configs.GetTowerByTypeAndLevel(type, level);
            return cfg != null ? Mathf.Max(0, cfg.SellPrice) : 0;
        }

        // ------------------------------------------------------------------
        // 内部：序列化
        // ------------------------------------------------------------------

        private static LevelLayoutBook LoadBook()
        {
            string json;
            LevelLayoutBook book = null;
            if (SaveManager.Instance.TryGetUserValue(StorageKey, out json) && !string.IsNullOrEmpty(json))
            {
                try
                {
                    book = JsonUtility.FromJson<LevelLayoutBook>(json);
                }
                catch (Exception ex)
                {
                    // 解不出来就按"没有记录"走，绝不让一段坏 json 把进关流程卡死
                    Debug.LogWarning("[Layout] 阵型存档解析失败，按无记录处理：" + ex.Message);
                    book = null;
                }
            }
            if (book == null)
            {
                book = new LevelLayoutBook();
            }
            if (book.levels == null)
            {
                book.levels = new List<LevelLayout>();
            }
            if (book.formatVersion != FormatVersion)
            {
                // 版本不符：不猜旧字段语义，直接当空册（阵型丢了只是要重新布防，代价可接受）
                Debug.LogWarning(string.Format(
                    "[Layout] 阵型册版本 {0} 与当前 {1} 不符，按空册处理", book.formatVersion, FormatVersion));
                return new LevelLayoutBook();
            }
            return book;
        }

        private static bool WriteBook(LevelLayoutBook book)
        {
            if (book == null)
            {
                return false;
            }
            // 存档后端没起来（首次启动失败会退化成一局内存档）时不要假装写成功：
            // 调用方（通关流程）虽然不回滚什么，但日志里必须能看出"这次没落盘"。
            if (string.IsNullOrEmpty(SaveManager.Instance.StorageLocation))
            {
                Debug.LogWarning("[Layout] 存档后端不可用，阵型未落盘");
                return false;
            }
            try
            {
                string json = JsonUtility.ToJson(book);
                SaveManager.Instance.SetUserValue(StorageKey, json, Sensitive);
                return true;
            }
            catch (Exception ex)
            {
                Debug.LogWarning("[Layout] 阵型落盘失败：" + ex.Message);
                return false;
            }
        }

        private static int CompareEntry(TowerLayoutEntry a, TowerLayoutEntry b)
        {
            if (ReferenceEquals(a, b)) return 0;
            if (a == null) return -1;
            if (b == null) return 1;
            int byRow = a.row.CompareTo(b.row);
            return byRow != 0 ? byRow : a.col.CompareTo(b.col);
        }
    }
}
