using System.Collections.Generic;
using cfg;

namespace FTProject
{
    /// <summary>
    /// 关卡配置视图（TBSceneInfo 的一行 = 一个关卡）。
    /// 注意：原 3D 时代的 CameraPosition / CameraRotration / MapPosition /
    /// EenemyPosition / PointScale 字段仍保留在表里，但 2D 固定视角下代码不再读取。
    /// </summary>
    public class LevelConfig
    {
        private readonly SceneInfo _s;

        public LevelConfig(SceneInfo s)
        {
            _s = s;
        }

        public SceneInfo Raw { get { return _s; } }

        public int Id { get { return _s.Id; } }
        public string Name { get { return _s.Name; } }

        /// <summary>本关卡包含的回合 id 列表 → TBRoundData</summary>
        public List<int> RoundIds { get { return _s.RoundList; } }

        /// <summary>棋盘布局 id → TBLevelMap</summary>
        public int MapId { get { return _s.MapId; } }

        public int InitialGold { get { return _s.InitialGold > 0 ? _s.InitialGold : 100; } }
        public int InitialHp { get { return _s.InitialHp > 0 ? _s.InitialHp : 10; } }

        /// <summary>回合之间的准备时间（秒）</summary>
        public float WaveIntervalSec
        {
            get { return (_s.WaveIntervalMs > 0 ? _s.WaveIntervalMs : 3000) / 1000f; }
        }

        /// <summary>难度标签 1~3（关卡选择界面展示用）</summary>
        public int Difficulty { get { return _s.Difficulty; } }

        public int RoundCount { get { return _s.RoundList != null ? _s.RoundList.Count : 0; } }

        public override string ToString()
        {
            return string.Format("LevelConfig(id={0}, name={1}, rounds={2}, map={3})",
                Id, Name, RoundCount, MapId);
        }
    }

    /// <summary>
    /// 棋盘布局配置视图（TBLevelMap）。
    /// 这是 v2.1 用配置表替代原 ASCII 地图文件（Map*.txt）的落地形式。
    ///
    /// 字符集：S 起点 / E 终点 / . 可建造地砖 / # 障碍 / X 空洞 / P 装饰地砖
    /// </summary>
    public class LevelMapConfig
    {
        private readonly LevelMap _m;

        public LevelMapConfig(LevelMap m)
        {
            _m = m;
        }

        public LevelMap Raw { get { return _m; } }

        public int Id { get { return _m.Id; } }
        public int LevelId { get { return _m.LevelId; } }
        public int Cols { get { return _m.Cols; } }
        public int Rows { get { return _m.Rows; } }

        /// <summary>每行一个字符串，长度应等于 Cols</summary>
        public List<string> Cells { get { return _m.Cells; } }

        public string Desc { get { return _m.Desc; } }

        /// <summary>取指定格子的字符；越界或行长度不足时返回 '.'（当空地处理）</summary>
        public char GetCell(int row, int col)
        {
            if (_m.Cells == null || row < 0 || row >= _m.Cells.Count)
            {
                return '.';
            }
            string line = _m.Cells[row];
            if (line == null || col < 0 || col >= line.Length)
            {
                return '.';
            }
            return line[col];
        }

        /// <summary>
        /// 自检：行长是否与 Cols 一致、行列数是否非 0。
        /// 返回空字符串表示通过，否则返回问题描述。
        /// </summary>
        public string Validate()
        {
            if (Cols <= 0 || Rows <= 0)
            {
                return string.Format("cols/rows 非法（{0}x{1}）", Cols, Rows);
            }
            if (Cells == null || Cells.Count != Rows)
            {
                return string.Format("行数不匹配：cells 有 {0} 行，rows 声明为 {1}",
                    Cells == null ? 0 : Cells.Count, Rows);
            }
            for (int r = 0; r < Cells.Count; r++)
            {
                if (Cells[r] == null || Cells[r].Length != Cols)
                {
                    return string.Format("第 {0} 行长度为 {1}，应为 {2}（每格一个字符）",
                        r, Cells[r] == null ? 0 : Cells[r].Length, Cols);
                }
            }
            return string.Empty;
        }

        public override string ToString()
        {
            return string.Format("LevelMapConfig(id={0}, level={1}, {2}x{3})", Id, LevelId, Cols, Rows);
        }
    }
}
