using System.Collections.Generic;
using SuperScrollView;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace FTProject
{
    /// <summary>
    /// 关卡选择界面（M3-4；整页全屏 + 横向画廊）。
    ///
    /// 【为什么这版换成 SuperScrollView 的 LoopListView2】
    ///   旧版是"运行时克隆模板按钮 + 手排 4 列网格"。关卡一多就整屏塞满，
    ///   既看不出"现在该打哪一关"，也没法扩展成章节/皮肤那种卡片式选关。
    ///   现在改用工程里已有的 SuperScrollView：条目池化复用、横向滑动、
    ///   **并且开启条目吸附（ItemSnap）让某一关始终停在屏幕正中**。
    ///
    /// 【交互约定（本版新增）】
    ///   · 居中的那一关 = "当前选中的关卡"，进入游戏**只认它**。
    ///   · 点居中的卡片 → 立刻进关。
    ///   · 点旁边没居中的卡片 → 先**动画滑到正中**，滑到位后再自动进关
    ///     （见 <see cref="OnClickItem"/> 与 <see cref="OnSnapItemFinished"/>）。
    ///   · 未解锁的卡片仍然只弹提示、不进关。
    ///   · 左右两颗箭头把"居中的关卡"前后挪一格（只挪，不进关）。
    ///
    /// 【为什么不把条目摆进 prefab，仍然由代码填内容】
    ///   与旧版同一理由：摆进 prefab 意味着"改关卡数量就要改 prefab"。
    ///   现在的分工是：`SelectLevelItem.prefab` 只描述**一张卡片长什么样**，
    ///   数量与内容仍由 TBSceneInfo 在运行时喂进去 —— 加关卡 = 加配置行。
    ///
    /// 【节点容错】与 TowerInfoView 同一口径：缺节点只警告、不阻断，
    ///   美术重排 prefab 时不会把功能一起弄坏。
    /// </summary>
    public class SelectView : MonoBehaviour
    {
        public const string LogicalName = "SelectView";

        /// <summary>
        /// 条目预制体名。
        /// 【必须与 UIPrefabBuilder 里登记进 LoopListView2 的名字一致】——
        ///   LoopListView2 是**按预制体名字**从对象池取条目的（见 NewListViewItem），
        ///   名字对不上只会 return null → 列表整片空白，**不报错**。
        /// </summary>
        private const string ItemPrefabName = "SelectLevelItem";

        /// <summary>
        /// 条目卡片宽度与间距（**必须与 UIPrefabBuilder 里的 SelectItemW / SelectItemGap 一致**）。
        /// 【为什么要在这里再写一份】LoopListView2 用 `mItemDefaultWithPaddingSize`
        ///   估算"还没实例化出来的条目"的位置。用它的默认值 20 会让内容总宽度被严重低估，
        ///   初始化定位时会被 clamp 回 0（表现为"要定位到第 N 关却永远停在第 1 关"）。
        /// </summary>
        private const float ItemWidth = 900f;
        private const float ItemGap = 56f;

        /// <summary>
        /// 条目中心离视口中心多远时缩到最小 / 最暗。
        /// 取"一个步长"，于是**相邻的那一张正好落在最暗端**，当前条目与邻居的对比一眼可见。
        /// </summary>
        private const float FocusFalloff = ItemWidth + ItemGap;

        /// <summary>最远端条目的缩放（居中条目恒为 1）</summary>
        private const float MinItemScale = 0.9f;

        /// <summary>最远端条目的不透明度（居中条目恒为 1）</summary>
        private const float MinItemAlpha = 0.5f;

        /// <summary>
        /// "滑到中间再进关"的兜底时限（秒）。
        /// 【为什么需要】吸附可能根本没跑起来（内容不满一屏、被拖拽打断……）。
        ///   没有这道兜底，一次失败的滑动就会让"点了却没反应"，玩家只能干等。
        /// 【为什么给到 2.5s】滑动本身约 0.5s 就把卡片送到位了，但插件要一直
        ///   微调到自己 0.01px 的完成阈值才罢休（实测还要再花 1s 以上）。
        ///   给得太紧会在动画尾巴上触发兜底、反而"啪"地跳一下。
        /// </summary>
        private const float SnapGuardSeconds = 2.5f;

        /// <summary>
        /// 判定"已经停在正中"的距离阈值（像素）。
        /// 【为什么不是 0.01】插件收尾是指数逼近，等它走完要 2 秒，玩家会觉得"点了半天没反应"。
        ///   4px 在 900 宽的卡片上肉眼不可辨，到了就直接进关，手感才跟得上。
        /// </summary>
        private const float CenteredEpsilon = 4f;

        private TMP_Text _title;
        private TMP_Text _summary;
        private LoopListView2 _list;
        private Button _closeBtn;
        private Button _leftBtn;
        private Button _rightBtn;

        private List<cfg.SceneInfo> _levels;

        /// <summary>InitListView 只允许调一次（再调 LoopListView2 会直接报错），用它守住</summary>
        private bool _listInited;

        /// <summary>待居中到第几个条目；&lt;0 表示无需处理（首次打开时用）</summary>
        private int _pendingCenterIndex = -1;

        /// <summary>当前"停在正中"的条目下标（每帧从到中心的距离推出来）；-1 = 尚未确定</summary>
        private int _centerIndex = -1;

        /// <summary>正在滑向哪一条；-1 = 没有进行中的滑动（箭头在此期间锁住，避免连点跳格）</summary>
        private int _targetCenterIndex = -1;

        /// <summary>点了没居中的卡片后，滑到位要进哪一关；&lt;=0 表示没有待进关</summary>
        private int _pendingEnterLevelId;

        /// <summary>滑动兜底倒计时（&lt;=0 表示没在等）</summary>
        private float _snapGuardTimer;

        private void Awake()
        {
            BindNodes();
        }

        private void OnEnable()
        {
            Build();
        }

        private void LateUpdate()
        {
            if (_list == null || !_listInited || _levels == null)
            {
                return;
            }

            // 【为什么首次定位要拖到第一帧 LateUpdate】
            //   OnEnable 那一刻 Canvas 还没排版，viewport / Content 的 rect 仍是 0，
            //   此时 MovePanelToItemIndex 会被 clamp 到 0 而"定位不过去"。
            if (_pendingCenterIndex >= 0)
            {
                int idx = _pendingCenterIndex;
                _pendingCenterIndex = -1;
                CenterOnIndexInstant(idx);
            }

            // 顺序有讲究：先把吸附距离刷新出来（UpdateFocusAndCenter 内部会做），
            // 再据此判断"滑到位了没有"
            UpdateFocusAndCenter();
            TickSliding();
            UpdateArrowInteractable();
        }

        // ------------------------------------------------------------------
        // 节点
        // ------------------------------------------------------------------

        private void BindNodes()
        {
            _title = FindText("Panel/Title");
            _summary = FindText("Panel/Summary");

            RectTransform listRect = FindRect("Panel/List");
            if (listRect != null)
            {
                _list = listRect.GetComponent<LoopListView2>();
                if (_list == null)
                {
                    Debug.LogWarning(
                        "[Select] Panel/List 上没有 LoopListView2 组件（prefab 可能还是旧版），关卡列表无法生成");
                }
            }

            _closeBtn = FindButton("Panel/CloseBtn");
            if (_closeBtn != null)
            {
                _closeBtn.onClick.AddListener(OnClickClose);
            }

            _leftBtn = FindButton("Panel/LeftBtn");
            if (_leftBtn != null)
            {
                _leftBtn.onClick.AddListener(delegate { OnClickStep(-1); });
            }
            _rightBtn = FindButton("Panel/RightBtn");
            if (_rightBtn != null)
            {
                _rightBtn.onClick.AddListener(delegate { OnClickStep(1); });
            }

            Button bg = FindButton("Bg");
            if (bg != null)
            {
                bg.onClick.AddListener(OnClickClose);
            }
        }

        // ------------------------------------------------------------------
        // 构建关卡列表
        // ------------------------------------------------------------------

        /// <summary>按 TBSceneInfo 重建关卡条目。可重复调用（界面是复用的，每次打开都会走一遍）。</summary>
        public void Build()
        {
            if (_list == null)
            {
                return;
            }
            if (Configs.LevelTable == null || Configs.LevelTable.DataList == null)
            {
                Debug.LogWarning("[Select] 配置表尚未加载，关卡列表为空");
                return;
            }

            _levels = Configs.LevelTable.DataList;

            // 兜底：预制体里已经勾好，这里再确认一次（漏勾则"吸附居中"整个失效）
            _list.ItemSnapEnable = true;

            if (!_listInited)
            {
                _listInited = true;
                LoopListViewInitParam p = LoopListViewInitParam.CopyDefaultInitParam();
                p.mItemDefaultWithPaddingSize = ItemWidth + ItemGap;
                // 默认 0.3 的平滑时长偏拖沓：卡片"肉眼到位"要 0.5s 以上，
                // 点一下要等这么久才进关会显得卡顿。0.25 约 0.4s，仍看得清是"滑过去"的。
                p.mSmoothDumpRate = 0.25f;
                _list.InitListView(_levels.Count, OnGetItemByIndex, p);

                // 初次打开：居中到"最靠前的未通关关卡"（通关后重进会自动停在下一关）。
                // 这一次用**瞬时**定位而不是动画 —— 刚打开界面就自己滑一段会很怪。
                _pendingCenterIndex = FirstUnclearedIndex();
            }
            else
            {
                // 重复打开：关卡数量一般不变，但星级 / 解锁态会变 → 整体重刷一遍内容
                if (_list.ItemTotalCount != _levels.Count)
                {
                    _list.SetListItemCount(_levels.Count, false);
                }
                _list.RefreshAllShownItem();
            }

            RefreshHeader(_levels.Count);
        }

        /// <summary>第一个"还没拿到星"的关卡下标；全通关则停在最后一关。空表返回 -1。</summary>
        private int FirstUnclearedIndex()
        {
            if (_levels == null || _levels.Count == 0)
            {
                return -1;
            }
            for (int i = 0; i < _levels.Count; i++)
            {
                cfg.SceneInfo s = _levels[i];
                if (s != null && SaveManager.Instance.GetStars(s.Id) == 0)
                {
                    return i;
                }
            }
            return _levels.Count - 1;
        }

        // ------------------------------------------------------------------
        // 居中 / 翻页 / 进关
        // ------------------------------------------------------------------

        /// <summary>
        /// 让第 index 个条目**立刻**停在正中（无动画）。
        /// 用于"刚打开界面时的初始定位"以及滑动兜底。
        /// </summary>
        private void CenterOnIndexInstant(int index)
        {
            if (!EnsureShown(index))
            {
                return;
            }
            _list.SetSnapTargetItemIndex(index);
            _list.FinishSnapImmediately();
            _targetCenterIndex = -1;
            _pendingEnterLevelId = 0;
            _snapGuardTimer = 0f;
        }

        /// <summary>
        /// 让第 index 个条目**动画滑动**到正中。
        /// 【为什么不用 FinishSnapImmediately】那一句是"瞬移"；这里要的是看得见的滑动，
        ///   所以只设吸附目标，交给 LoopListView2 自己用 SmoothDamp 滑过去。
        /// </summary>
        private bool RequestCenterOnIndex(int index)
        {
            if (!EnsureShown(index))
            {
                return false;
            }
            _list.SetSnapTargetItemIndex(index);
            _targetCenterIndex = index;
            _snapGuardTimer = SnapGuardSeconds;
            return true;
        }

        /// <summary>
        /// 保证第 index 个条目已经是"已显示条目"。
        /// 【为什么必须先保证】`SetSnapTargetItemIndex` 内部会去取"已显示条目"，
        ///   取不到就静默放弃（表现为"点了没反应"）。跨多格跳转时目标可能还在屏幕外，
        ///   所以先用 MovePanelToItemIndex 把它拉进来。
        /// </summary>
        private bool EnsureShown(int index)
        {
            if (_list == null || _list.ItemTotalCount <= 0)
            {
                return false;
            }
            index = Mathf.Clamp(index, 0, _list.ItemTotalCount - 1);
            if (_list.GetShownItemByItemIndex(index) == null)
            {
                _list.MovePanelToItemIndex(index, 0);
            }
            return true;
        }

        /// <summary>
        /// 滑动推进器：等目标条目真正落到正中，再决定要不要进关。
        ///
        /// 【为什么用"轮询距离"而不是插件的 mOnSnapItemFinished 回调】
        ///   实测那条回调并不可靠：它内部传的是 `mCurSnapNearestItemIndex`，
        ///   而这个值只在"容器位置变了"的那一帧才重算 —— 会出现"回调提前触发、
        ///   传回来的还不是我们要的那一条"的情况（表现为点击后下一帧就直接进关了，
        ///   滑动动画等于没播）。直接读目标条目到视口中心的距离，才是唯一可信的判据。
        /// </summary>
        private void TickSliding()
        {
            if (_targetCenterIndex < 0)
            {
                return;
            }

            _snapGuardTimer -= Time.unscaledDeltaTime;

            // 玩家中途自己拖了 → 视为改主意：取消这次"点哪进哪"，也不再自动进关
            bool dragging = _list.IsDraging;
            LoopListViewItem2 item = dragging ? null : _list.GetShownItemByItemIndex(_targetCenterIndex);
            bool centered = item != null &&
                            Mathf.Abs(item.DistanceWithViewPortSnapCenter) <= CenteredEpsilon;

            if (!centered && !dragging && _snapGuardTimer > 0f)
            {
                return;   // 还在滑，继续等
            }

            int enterId = dragging ? 0 : _pendingEnterLevelId;
            int index = _targetCenterIndex;
            _targetCenterIndex = -1;
            _pendingEnterLevelId = 0;
            _snapGuardTimer = 0f;

            if (enterId <= 0)
            {
                return;
            }
            if (!centered)
            {
                CenterOnIndexInstant(index);   // 兜底：滑动没跑起来就直接顶到正中
            }
            EnterLevel(enterId);
        }

        /// <summary>左右箭头：把"居中的那一关"前后挪一格。只挪，不进关。</summary>
        private void OnClickStep(int delta)
        {
            if (_list == null || !_listInited || _centerIndex < 0)
            {
                return;
            }
            if (_targetCenterIndex >= 0)
            {
                return;   // 正在滑，先让这一次走完（否则连点会跳格）
            }
            int target = _centerIndex + delta;
            if (target < 0 || target >= _list.ItemTotalCount)
            {
                return;
            }
            _pendingEnterLevelId = 0;
            RequestCenterOnIndex(target);
        }

        /// <summary>点条目：居中的直接进；没居中的先滑到中间，到位后再进。</summary>
        private void OnClickItem(LoopListViewItem2 item)
        {
            if (item == null)
            {
                return;
            }
            int index = item.ItemIndex;
            int levelId = item.UserIntData1;

            // 未解锁：给明确提示，不进关（与旧版一字不差的逻辑）
            if (item.UserIntData2 == 0)
            {
                EventDispatcher.TriggerEvent<string>(EventName.ShowTipEvent, "先通关上一关才能解锁");
                return;
            }

            // 已经停在正中、也没有滑动在跑 → 就是"点击居中关卡"，直接进
            if (index == _centerIndex && _targetCenterIndex < 0)
            {
                EnterLevel(levelId);
                return;
            }

            // 没居中 → 先动画滑到中间，滑到位后由 TickSliding 进关
            _pendingEnterLevelId = levelId;
            if (!RequestCenterOnIndex(index))
            {
                // 吸附起不来（例如内容不满一屏）→ 不能把玩家卡住，直接进
                _pendingEnterLevelId = 0;
                EnterLevel(levelId);
            }
        }

        private void EnterLevel(int levelId)
        {
            EventDispatcher.TriggerEvent<int>(EventName.SelectLevelRequestEvent, levelId);
        }

        /// <summary>
        /// 每帧刷新两件事：① 谁停在正中 ② 非居中卡片的缩小/压暗。
        /// 用一次遍历同时算出来（展示的条目只有几个，开销可忽略）。
        /// </summary>
        private void UpdateFocusAndCenter()
        {
            if (!_list.ItemSnapEnable)
            {
                return;
            }

            _list.UpdateAllShownItemSnapData();
            int count = _list.ShownItemCount;
            float bestDist = float.MaxValue;
            int bestIndex = -1;

            for (int i = 0; i < count; i++)
            {
                LoopListViewItem2 item = _list.GetShownItemByIndex(i);
                if (item == null)
                {
                    continue;
                }

                float dist = item.DistanceWithViewPortSnapCenter;
                float abs = Mathf.Abs(dist);

                // 拖拽中不做"谁是中心"的判定，否则箭头会在手指底下乱闪
                if (!_list.IsDraging && abs < bestDist)
                {
                    bestDist = abs;
                    bestIndex = item.ItemIndex;
                }

                // 缩放/淡化只动卡片的 Body 子节点（围绕卡片中心，左右对称），
                // 不碰条目根节点，因此不会干扰 LoopListView2 的排布算式。
                CanvasGroup body = item.UserObjectData as CanvasGroup;
                if (body == null)
                {
                    continue;
                }
                float t = Mathf.Clamp01(abs / FocusFalloff);
                float scale = Mathf.Lerp(1f, MinItemScale, t);
                body.transform.localScale = new Vector3(scale, scale, 1f);
                body.alpha = Mathf.Lerp(1f, MinItemAlpha, t);
            }

            if (bestIndex >= 0)
            {
                _centerIndex = bestIndex;
            }
        }

        /// <summary>到头了就把对应的箭头置灰，给出"没法再往那边翻"的反馈。</summary>
        private void UpdateArrowInteractable()
        {
            bool sliding = _targetCenterIndex >= 0;
            if (_leftBtn != null)
            {
                bool canPrev = !sliding && _centerIndex > 0;
                if (_leftBtn.interactable != canPrev)
                {
                    _leftBtn.interactable = canPrev;
                }
            }
            if (_rightBtn != null)
            {
                bool canNext = !sliding && _centerIndex >= 0 &&
                               _centerIndex < _list.ItemTotalCount - 1;
                if (_rightBtn.interactable != canNext)
                {
                    _rightBtn.interactable = canNext;
                }
            }
        }

        // ------------------------------------------------------------------
        // 条目回填
        // ------------------------------------------------------------------

        /// <summary>LoopListView2 的条目回调：池里取一张卡片，填上新内容。</summary>
        private LoopListViewItem2 OnGetItemByIndex(LoopListView2 listView, int index)
        {
            if (_levels == null || index < 0 || index >= _levels.Count)
            {
                return null;
            }
            cfg.SceneInfo raw = _levels[index];
            if (raw == null)
            {
                return null;
            }

            LoopListViewItem2 item = listView.NewListViewItem(ItemPrefabName);
            if (item == null)
            {
                Debug.LogWarning(
                    "[Select] LoopListView2 未登记条目预制体「" + ItemPrefabName + "」，关卡列表无法生成");
                return null;
            }

            int levelId = raw.Id;
            bool unlocked = SaveManager.Instance.IsUnlocked(levelId);
            int stars = SaveManager.Instance.GetStars(levelId);
            int diff = raw.Difficulty;

            // 【为什么点击回调只在首次初始化时挂】
            //   条目是**池化复用**的：每次回填都 AddListener 会让同一条目累积 N 个回调，
            //   横向滚一圈之后一次点击就会触发 N 次选关。回调里读的是条目的
            //   UserIntData1/2，所以复用时只要换数据，不必重挂。
            if (!item.IsInitHandlerCalled)
            {
                item.IsInitHandlerCalled = true;

                // 卡片的视觉层（缩放/淡化都作用在它身上）缓存一次，省掉每帧 GetComponent。
                // 取"第一个子节点"即可 —— 卡片预制体的结构由生成器固定为 Body 一个子节点。
                CanvasGroup body = item.transform.childCount > 0
                    ? item.transform.GetChild(0).GetComponent<CanvasGroup>()
                    : null;
                item.UserObjectData = body;

                Button btn = item.GetComponentInChildren<Button>(true);
                if (btn != null)
                {
                    btn.onClick.AddListener(delegate { OnClickItem(item); });
                }
            }
            item.UserIntData1 = levelId;
            item.UserIntData2 = unlocked ? 1 : 0;

            TMP_Text label = item.GetComponentInChildren<TMP_Text>(true);
            if (label != null)
            {
                // 【为什么要着色】效果图里实心星是金色、空心星与难度是暗蓝灰，
                //   全靠富文本在**一段文本内**分色，否则得拆成三个 TMP 节点。
                // 【字号为什么逐行给】卡片只有三行文案，名称/星级要压住难度，
                //   富文本标签即便失效，基础字号仍能保证三行落在卡片内。
                label.text = string.Format(
                    "<size=56><color=#E8F0FA>{0}</color></size>\n" +
                    "<size=56>{1}</size>\n" +
                    "<size=40>{2}</size>",
                    raw.Name,
                    StarRichText(stars),
                    unlocked
                        ? "<color=#7A8CA6>" + Difficulty(diff) + "</color>"
                        : "<color=#5A6B80>未解锁</color>");
            }

            return item;
        }

        private void RefreshHeader(int levelCount)
        {
            int cleared = SaveManager.Instance.ClearedCount;
            int stars = SaveManager.Instance.TotalStars;
            // 数字提亮、星级用金色（效果图 01 的 Summary 配色）
            SetText(_summary, string.Format(
                "已通关 <color=#E8F0FA>{0}/{1}</color>　<color=#FFC94D>★ {2}/{3}</color>",
                cleared, levelCount, stars, levelCount * 3));
            SetText(_title, "选择关卡");
        }

        /// <summary>星级字符串。用实心/空心星而不是数字，一眼能扫完所有关卡。</summary>
        public static string Stars(int n)
        {
            n = Mathf.Clamp(n, 0, 3);
            return new string('★', n) + new string('☆', 3 - n);
        }

        /// <summary>星级富文本：已得星金色、未得星暗蓝灰（效果图 01）。**公开**给结算界面复用，
        /// 否则"同一个星级在两处长得不一样"（与 Stars() 同样的理由）。</summary>
        public static string StarRichText(int n)
        {
            n = Mathf.Clamp(n, 0, 3);
            return "<color=#FFC94D>" + new string('★', n) + "</color>" +
                   "<color=#3F4E63>" + new string('☆', 3 - n) + "</color>";
        }

        public static string Difficulty(int d)
        {
            if (d <= 1) return "难度 Ⅰ";
            if (d == 2) return "难度 Ⅱ";
            return "难度 Ⅲ";
        }

        private void OnClickClose()
        {
            EventDispatcher.TriggerEvent(EventName.CloseSelectRequestEvent);
        }

        // ------------------------------------------------------------------
        // 节点查找（容错）
        // ------------------------------------------------------------------

        private TMP_Text FindText(string path)
        {
            Transform tr = transform.Find(path);
            if (tr == null)
            {
                Debug.LogWarning("[Select] 缺少文本节点「" + path + "」");
                return null;
            }
            return tr.GetComponent<TMP_Text>();
        }

        private Button FindButton(string path)
        {
            Transform tr = transform.Find(path);
            if (tr == null)
            {
                Debug.LogWarning("[Select] 缺少按钮节点「" + path + "」");
                return null;
            }
            return tr.GetComponent<Button>();
        }

        private RectTransform FindRect(string path)
        {
            Transform tr = transform.Find(path);
            if (tr == null)
            {
                Debug.LogWarning("[Select] 缺少容器节点「" + path + "」");
                return null;
            }
            return tr as RectTransform;
        }

        private static void SetText(TMP_Text t, string v)
        {
            if (t != null && t.text != v)
            {
                t.text = v;
            }
        }
    }
}
