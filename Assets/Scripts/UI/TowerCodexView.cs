using System.Collections.Generic;
using SuperScrollView;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace FTProject
{
    /// <summary>
    /// 防御塔图鉴（UI 补全 B2 / 效果图 19_TowerCodexView.svg）。
    ///
    /// 【它解决什么问题】5 种塔的定位、形态与三级数值在游戏里**没有任何地方能看到**，
    /// 玩家只能靠"造一座试试"。图鉴把配置表里的数值直接摊开。
    ///
    /// 【几何为什么照抄 SelectView】横向画廊的"精确居中 + 邻卡可见"是一组很脆的约束，
    /// 见 UIPrefabBuilder.SelectItemW 的注释（条目宽 ≡ 视口宽；视口比可视区窄；
    /// Viewport.pivot.x 必须预置 0；InitListView 只能调一次）。这里与那边**同一套参数与写法**，
    /// 改一处必须两处一起改。
    ///
    /// 【为什么不做点击态】图鉴是"看"的界面，点卡片没有下一层可去
    /// （详情已经在卡片上全部摊开），所以不做 onClick ——
    /// 顺带避开了 LoopListView2 "条目池化复用导致 onClick 重复挂"这个经典坑。
    /// </summary>
    public class TowerCodexView : MonoBehaviour
    {
        public const string LogicalName = "TowerCodexView";

        /// <summary>与 UIPrefabBuilder.TowerCodexItemPath 的资产名一致（LoopListView2 按名字取池）。</summary>
        private const string ItemPrefabName = "TowerCodexItem";

        /// <summary>必须与 UIPrefabBuilder 的 CodexItemW / CodexItemGap 一致（用于估算未实例化条目的位置）。</summary>
        private const float ItemWidth = 460f;
        private const float ItemGap = 70f;

        /// <summary>离视口中心一个步长就缩到最小/最暗（相邻那张落在最暗端）。</summary>
        private const float FocusFalloff = ItemWidth + ItemGap;

        private const float MinScale = 0.86f;
        private const float MinAlpha = 0.45f;

        private LoopListView2 _list;
        private Button _leftBtn;
        private Button _rightBtn;
        private Button _closeBtn;
        private TMP_Text _pageText;

        private List<TowerConfig> _towers;
        private bool _listInited;
        private int _pendingCenterIndex = -1;
        private int _centerIndex;

        private void Awake()
        {
            Transform listTr = transform.Find("Panel/List");
            _list = listTr != null ? listTr.GetComponent<LoopListView2>() : null;
            _leftBtn = FindButton("Panel/LeftBtn");
            _rightBtn = FindButton("Panel/RightBtn");
            _closeBtn = FindButton("Panel/CloseBtn");
            _pageText = FindText("Panel/PageText");

            if (_leftBtn != null) _leftBtn.onClick.AddListener(OnClickLeft);
            if (_rightBtn != null) _rightBtn.onClick.AddListener(OnClickRight);
            if (_closeBtn != null) _closeBtn.onClick.AddListener(OnClickClose);
        }

        private void OnEnable()
        {
            BuildList();
        }

        /// <summary>
        /// 取"每种塔的 1 级配置"作为图鉴数据源。
        /// 【为什么用 GetBaseTowers】它正是"建造栏上那 5 颗塔"的口径 ——
        /// 图鉴要与玩家实际能造的塔一一对应，用等级遍历会把 15 行都列出来（3 倍冗余）。
        /// </summary>
        private void BuildList()
        {
            if (_list == null)
            {
                Debug.LogWarning("[TowerCodex] 缺少 List 节点（LoopListView2），图鉴无法显示");
                return;
            }

            _towers = Configs.GetBaseTowers();
            if (_towers == null)
            {
                _towers = new List<TowerConfig>();
            }

            // 兜底：预制体里已经勾好，这里再确认一次（漏勾则"吸附居中"整个失效）
            _list.ItemSnapEnable = true;

            if (!_listInited)
            {
                _listInited = true;
                LoopListViewInitParam p = LoopListViewInitParam.CopyDefaultInitParam();
                p.mItemDefaultWithPaddingSize = ItemWidth + ItemGap;   // 用默认 20 会让初始定位被 clamp 回 0
                p.mSmoothDumpRate = 0.25f;
                _list.InitListView(_towers.Count, OnGetItemByIndex, p);
                _pendingCenterIndex = _towers.Count > 0 ? 0 : -1;
            }
            else if (_list.ItemTotalCount != _towers.Count)
            {
                _list.SetListItemCount(_towers.Count, false);
                _list.RefreshAllShownItem();
            }
            else
            {
                _list.RefreshAllShownItem();
            }

            RefreshFooter();
        }

        private LoopListViewItem2 OnGetItemByIndex(LoopListView2 listView, int index)
        {
            if (index < 0 || _towers == null || index >= _towers.Count)
            {
                return null;
            }

            LoopListViewItem2 item = listView.NewListViewItem(ItemPrefabName);
            if (item == null)
            {
                return null;
            }

            // 池化复用：数据每帧都要重灌，否则滚回来会看到上一张卡的内容
            item.UserIntData1 = index;
            TowerCodexItem card = item.GetComponent<TowerCodexItem>();
            if (card != null)
            {
                TowerConfig cfg = _towers[index];
                card.SetData(cfg, TowerCodexItem.RoleText(cfg.Type));
            }
            return item;
        }

        private void LateUpdate()
        {
            if (_list == null || !_listInited || _towers == null)
            {
                return;
            }

            // 【为什么首次定位拖到第一帧 LateUpdate】OnEnable 时 Canvas 还没排版，
            //   viewport / Content 的 rect 仍是 0，此时定位会被 clamp 回 0（永远停在第 1 张）。
            if (_pendingCenterIndex >= 0)
            {
                int idx = _pendingCenterIndex;
                _pendingCenterIndex = -1;
                _centerIndex = idx;
                _list.SetSnapTargetItemIndex(idx);
                _list.FinishSnapImmediately();
                RefreshFooter();
            }

            UpdateItemVisuals();
        }

        /// <summary>
        /// 按"离列表中心多远"缩放 + 淡化每张卡片。
        /// 【为什么不在卡片内部自己算】卡片不知道自己在视口里的位置；
        ///   而且 LoopListView2 的排布只有这里看得全。
        /// 【为什么改 Body 的缩放而不是卡片根节点】根节点 pivot=(0,0.5)，缩它会围绕左缘缩 → 偏心。
        /// </summary>
        private void UpdateItemVisuals()
        {
            float centerX = _list.transform.position.x;
            int count = _list.ShownItemCount;
            for (int i = 0; i < count; i++)
            {
                LoopListViewItem2 item = _list.GetShownItemByIndex(i);
                if (item == null)
                {
                    continue;
                }
                TowerCodexItem card = item.GetComponent<TowerCodexItem>();
                RectTransform body = card != null ? card.Body : null;
                if (body == null)
                {
                    continue;
                }

                float dist = Mathf.Abs(item.transform.position.x - centerX);
                float t = Mathf.Clamp01(dist / FocusFalloff);
                float scale = Mathf.Lerp(1f, MinScale, t);
                body.localScale = new Vector3(scale, scale, 1f);

                CanvasGroup cg = body.GetComponent<CanvasGroup>();
                if (cg != null)
                {
                    cg.alpha = Mathf.Lerp(1f, MinAlpha, t);
                }
            }
        }

        // ------------------------------------------------------------------
        // 交互
        // ------------------------------------------------------------------

        private void OnClickLeft()
        {
            MoveCenter(-1);
        }

        private void OnClickRight()
        {
            MoveCenter(1);
        }

        private void MoveCenter(int delta)
        {
            if (_towers == null || _towers.Count == 0)
            {
                return;
            }
            int target = Mathf.Clamp(_centerIndex + delta, 0, _towers.Count - 1);
            if (target == _centerIndex)
            {
                RefreshFooter();
                return;
            }
            _centerIndex = target;
            _list.SetSnapTargetItemIndex(target);
            RefreshFooter();
        }

        private void RefreshFooter()
        {
            int total = _towers != null ? _towers.Count : 0;
            if (_pageText != null)
            {
                _pageText.text = total > 0 ? string.Format("{0} / {1}", _centerIndex + 1, total) : "0 / 0";
            }
            // 到头置灰（只挪不进关，所以置灰比"循环回绕"更符合预期）
            if (_leftBtn != null) _leftBtn.interactable = _centerIndex > 0;
            if (_rightBtn != null) _rightBtn.interactable = _centerIndex < total - 1;
        }

        private void OnClickClose()
        {
            UIManager.Instance.Close(LogicalName);
            // 图鉴是从主菜单进来的整页界面，"返回"就该回到主菜单
            UIManager.Instance.Open<MainMenuView>("MainMenuView", UILayout.NormalPanel);
        }

        private TMP_Text FindText(string path)
        {
            Transform tr = transform.Find(path);
            if (tr == null)
            {
                Debug.LogWarning("[TowerCodex] 缺少文本节点「" + path + "」");
                return null;
            }
            return tr.GetComponent<TMP_Text>();
        }

        private Button FindButton(string path)
        {
            Transform tr = transform.Find(path);
            if (tr == null)
            {
                Debug.LogWarning("[TowerCodex] 缺少按钮节点「" + path + "」");
                return null;
            }
            return tr.GetComponent<Button>();
        }
    }
}
