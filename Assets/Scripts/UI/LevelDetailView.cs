using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace FTProject
{
    /// <summary>
    /// 关卡详情（UI 补全 B4 / 效果图 21_LevelDetailView.svg）。
    ///
    /// 【它解决什么问题】改造前点选关卡片**直接进关**，玩家看不到"几回合、多少波、
    /// 什么难度、历史最好多久"，进关才发现不是自己想要的，只能退出来。
    ///
    /// 【为什么走 SelectLevelRequestEvent 而不是直接 StartLevel】
    ///   选关界面与结算界面本来都在用这条事件，详情窗口再插一条新链路就会出现
    ///   "从详情进关"与"从卡片进关"两套入口，将来改建关流程必然漏改一处。
    /// </summary>
    public class LevelDetailView : MonoBehaviour
    {
        public const string LogicalName = "LevelDetailView";

        /// <summary>怪物名字最多显示几个（效果图 21 的图标行一屏放得下 7 个）。</summary>
        private const int MaxEnemyNames = 7;

        private static readonly Color Gold = new Color(1f, 0.788f, 0.302f, 1f);           // #FFC94D
        private static readonly Color StarOff = new Color(0.22f, 0.27f, 0.35f, 1f);       // 未获得的星
        private static readonly Color TextPrimary = new Color(0.910f, 0.941f, 0.980f, 1f);
        private static readonly Color TextSecondary = new Color(0.624f, 0.702f, 0.784f, 1f);

        private TMP_Text _title;
        private TMP_Text _levelName;
        private TMP_Text _bestStarText;
        private TMP_Text _enemyLabel;
        private TMP_Text _enemyIcons;
        private readonly Image[] _stars = new Image[3];
        private readonly TMP_Text[] _info = new TMP_Text[6];
        private Button _playBtn;
        private Button _replayBtn;
        private Button _closeBtn;
        private TMP_Text _playLabel;

        private int _levelId;

        /// <summary>打开并展示某一关的详情。levelId 非法时直接不显示（不弹空窗）。</summary>
        public static void Show(int levelId)
        {
            LevelConfig lv = Configs.GetLevel(levelId);
            if (lv == null)
            {
                Debug.LogWarning("[LevelDetail] 关卡 " + levelId + " 不存在，无法显示详情");
                return;
            }
            LevelDetailView view = UIManager.Instance.Open<LevelDetailView>(LogicalName, UILayout.NormalPanel);
            if (view == null)
            {
                Debug.LogError("[LevelDetail] LevelDetailView 打开失败（prefab 可能还没生成）");
                return;
            }
            view.Fill(levelId);
        }

        private void Awake()
        {
            _title = FindText("Panel/DetailTitle");
            _levelName = FindText("Panel/LevelName");
            _bestStarText = FindText("Panel/BestStarText");
            _enemyLabel = FindText("Panel/EnemyLabel");
            _enemyIcons = FindText("Panel/EnemyIcons");
            _playBtn = FindButton("Panel/PlayBtn");
            _replayBtn = FindButton("Panel/ReplayBtn");
            _closeBtn = FindButton("Panel/CloseBtn");
            _playLabel = FindText("Panel/PlayBtn/Label");

            // ⚠️ 逐个写开而不是循环：`transform.Find("Panel/Star" + i)` 这种拼接写法会让
            //   节点契约校验脚本只取到字面量前缀（"Panel/Star"），从而误报"生成器不产出该节点"。
            _stars[0] = FindImage("Panel/Star1");
            _stars[1] = FindImage("Panel/Star2");
            _stars[2] = FindImage("Panel/Star3");

            _info[0] = FindText("Panel/Info1");
            _info[1] = FindText("Panel/Info2");
            _info[2] = FindText("Panel/Info3");
            _info[3] = FindText("Panel/Info4");
            _info[4] = FindText("Panel/Info5");
            _info[5] = FindText("Panel/Info6");

            if (_playBtn != null) _playBtn.onClick.AddListener(OnClickPlay);
            if (_replayBtn != null) _replayBtn.onClick.AddListener(OnClickPlay);
            if (_closeBtn != null) _closeBtn.onClick.AddListener(OnClickClose);
            Button bg = FindButton("Bg");
            if (bg != null) bg.onClick.AddListener(OnClickClose);

            if (_title != null) _title.color = TextPrimary;
            if (_levelName != null) _levelName.color = TextSecondary;
            if (_bestStarText != null) _bestStarText.color = TextSecondary;
            if (_enemyLabel != null) _enemyLabel.color = TextSecondary;
            if (_enemyIcons != null) _enemyIcons.color = TextPrimary;
            for (int i = 0; i < _info.Length; i++)
            {
                if (_info[i] != null) _info[i].color = TextPrimary;
            }
        }

        private void Fill(int levelId)
        {
            _levelId = levelId;
            LevelConfig lv = Configs.GetLevel(levelId);
            if (lv == null)
            {
                return;
            }

            SetText(_title, string.Format("第 {0} 关", levelId));
            SetText(_levelName, string.IsNullOrEmpty(lv.Name) ? string.Empty : lv.Name);

            SaveManager sm = SaveManager.Instance;
            int stars = sm != null ? sm.GetStars(levelId) : 0;
            bool unlocked = sm == null || sm.IsUnlocked(levelId);

            for (int i = 0; i < 3; i++)
            {
                if (_stars[i] != null)
                {
                    _stars[i].color = i < stars ? Gold : StarOff;
                }
            }
            // 【为什么先算出字符串再赋值】把三元表达式拆成独立语句：
            // 多行调用会让参数个数的静态校验脚本误判（它按行解析）。
            string bestText = stars > 0 ? string.Format("历史最佳 {0} 星", stars) : "尚未通关";
            SetText(_bestStarText, bestText);

            // 波次总数 = 各回合的 WaveCount 之和（回合数 ≠ 波数，分开显示）
            List<int> roundIds = lv.RoundIds;
            int totalWaves = 0;
            HashSet<int> enemyIds = new HashSet<int>();
            if (roundIds != null)
            {
                for (int i = 0; i < roundIds.Count; i++)
                {
                    RoundConfig round = Configs.GetRound(roundIds[i]);
                    if (round == null)
                    {
                        continue;
                    }
                    totalWaves += round.WaveCount;
                    List<int> waveIds = round.WaveIds;
                    if (waveIds == null)
                    {
                        continue;
                    }
                    for (int w = 0; w < waveIds.Count; w++)
                    {
                        WaveGroupConfig group = Configs.GetWaveGroup(waveIds[w]);
                        List<int> ids = group != null ? group.EnemyIds : null;
                        if (ids == null)
                        {
                            continue;
                        }
                        for (int e = 0; e < ids.Count; e++)
                        {
                            enemyIds.Add(ids[e]);
                        }
                    }
                }
            }

            string diff = lv.Difficulty >= 3 ? "★★★" : (lv.Difficulty == 2 ? "★★☆" : "★☆☆");
            int bestTimeMs = sm != null ? sm.GetBestTimeMs(levelId) : 0;

            SetText(_info[0], string.Format("回合数　{0}", lv.RoundCount));
            SetText(_info[1], string.Format("波次　　{0}", totalWaves));
            SetText(_info[2], string.Format("初始金币　{0}", lv.InitialGold));
            SetText(_info[3], string.Format("初始生命　{0}", lv.InitialHp));
            SetText(_info[4], string.Format("难度　　{0}", diff));
            // 【最佳用时】0 显示成 --:--（SaveManager.FormatTime 统一口径）——
            // "没有记录"与"0 秒通关"必须一眼分得开
            SetText(_info[5], string.Format("最佳用时　{0}", SaveManager.FormatTime(bestTimeMs)));

            SetText(_enemyLabel, "本关出现怪物");
            SetText(_enemyIcons, BuildEnemySummary(enemyIds));

            // 未解锁的关卡不给"开始挑战"，只留"返回"（效果图 21 的既定行为）
            if (_playBtn != null && _playBtn.gameObject.activeSelf != unlocked)
            {
                _playBtn.gameObject.SetActive(unlocked);
            }
            if (_playLabel != null)
            {
                _playLabel.text = stars > 0 ? "再次挑战" : "开始挑战";
            }
            if (_replayBtn != null && _replayBtn.gameObject.activeSelf != unlocked)
            {
                _replayBtn.gameObject.SetActive(unlocked);
            }
        }

        /// <summary>
        /// 怪物一览。当前用**名字串**而不是图标：怪物图标是图集（`Atlas_&lt;怪名&gt;`），
        /// 要做成图标行得先给每个怪生成一个 Image 节点并运行时按怪名取图集 ——
        /// 那是"图鉴界面（B2/B3）"的活。这里先用真实数据把"有哪些怪"讲清楚，
        /// 不编造图标，也不写死数量。
        /// </summary>
        private string BuildEnemySummary(HashSet<int> enemyIds)
        {
            if (enemyIds.Count == 0)
            {
                return "—";
            }
            List<int> sorted = new List<int>(enemyIds);
            sorted.Sort();
            System.Text.StringBuilder sb = new System.Text.StringBuilder();
            int shown = 0;
            for (int i = 0; i < sorted.Count && shown < MaxEnemyNames; i++)
            {
                EnemyConfig cfg = Configs.GetEnemy(sorted[i]);
                if (cfg == null)
                {
                    continue;
                }
                if (shown > 0)
                {
                    sb.Append("　");
                }
                sb.Append(string.IsNullOrEmpty(cfg.Name) ? ("#" + sorted[i]) : cfg.Name);
                shown++;
            }
            if (sorted.Count > shown)
            {
                sb.Append(string.Format("　等 {0} 种", sorted.Count));
            }
            return sb.ToString();
        }

        private void OnClickPlay()
        {
            int id = _levelId;
            UIManager.Instance.Close(LogicalName);
            // 复用既有入口：选关界面与结算界面都发这个事件
            EventDispatcher.TriggerEvent<int>(EventName.SelectLevelRequestEvent, id);
        }

        private void OnClickClose()
        {
            UIManager.Instance.Close(LogicalName);
        }

        private static void SetText(TMP_Text t, string v)
        {
            if (t != null && t.text != v)
            {
                t.text = v;
            }
        }

        private TMP_Text FindText(string path)
        {
            Transform tr = transform.Find(path);
            if (tr == null)
            {
                Debug.LogWarning("[LevelDetail] 缺少文本节点「" + path + "」");
                return null;
            }
            return tr.GetComponent<TMP_Text>();
        }

        private Button FindButton(string path)
        {
            Transform tr = transform.Find(path);
            if (tr == null)
            {
                Debug.LogWarning("[LevelDetail] 缺少按钮节点「" + path + "」");
                return null;
            }
            return tr.GetComponent<Button>();
        }

        private Image FindImage(string path)
        {
            Transform tr = transform.Find(path);
            if (tr == null)
            {
                Debug.LogWarning("[LevelDetail] 缺少图片节点「" + path + "」");
                return null;
            }
            return tr.GetComponent<Image>();
        }
    }
}
