namespace FTProject
{
    /// <summary>
    /// 一局结算的数据快照（通关与失败共用同一份结构）。
    ///
    /// 【为什么要单独抽一个类，而不是给 Show() 传十来个参数】
    ///   结算界面要同时用到：本次星级、**结算前的历史最高星级**、是否刷新记录、
    ///   关卡名、下一关 id、战绩三项……十几个参数挤在一个签名里，
    ///   调用点与实现点稍有出入就会错位（本项目已真实踩过一次"实参个数不匹配"的坑）。
    ///   用对象传递后，字段名即文档，增删字段也不会牵动调用签名。
    ///
    /// 【数据从哪来】
    ///   由 <see cref="GameFlowManager"/> 在回合全部结束、调用 RecordClear **之前**组装：
    ///   因为 RecordClear 会把星级"只升不降"地合并进存档，一旦先写再读，
    ///   就再也拿不到"这一局之前玩家最好打到几星"了 —— 而那正是"是否刷新记录"的依据。
    /// </summary>
    public class LevelClearInfo
    {
        /// <summary>true = 通关；false = 防御失败</summary>
        public bool victory;

        /// <summary>本关 id</summary>
        public int levelId;

        /// <summary>关卡展示名（取自配置表，失败时也可能为空）</summary>
        public string levelName;

        /// <summary>本次获得的星级 0~3（失败恒为 0）</summary>
        public int stars;

        /// <summary>本局**之前**的历史最高星级，用于对比展示</summary>
        public int previousBest;

        /// <summary>本局是否刷新了历史最高星级</summary>
        public bool newRecord;

        /// <summary>本局结束时的剩余生命</summary>
        public int hp;

        /// <summary>本关最大生命</summary>
        public int maxHp;

        /// <summary>本局击杀数</summary>
        public int killed;

        /// <summary>本局漏怪数</summary>
        public int leaked;

        /// <summary>下一关 id；0 表示没有下一关（已是最后一关）</summary>
        public int nextLevelId;

        /// <summary>下一关展示名（可为空 —— 调用方拿不到配置时就不显示名字）</summary>
        public string nextLevelName;

        /// <summary>是否存在下一关（决定「下一关」按钮是否可点）</summary>
        public bool hasNext;
    }
}
