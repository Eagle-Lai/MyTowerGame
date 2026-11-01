using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace FTProject
{
    /// <summary>
    /// 建造圆盘菜单（2026-11-01）：点击"可建造的空格"时，在该格弹出的径向菜单。
    /// 圆盘上三颗塔图标按钮（普通/火力/减速），点图标即在**该格**建造对应塔型
    /// —— 先选格子、再选塔型，与 HUD 建造栏"先选塔型再选格子"互为补充。
    ///
    /// 【视觉与定位复用 TowerActionMenu】
    ///   · 节点结构一致：TowerBuildMenu（零尺寸、中心 = 格子屏幕位置）+ Backdrop 装饰圆盘
    ///     （raycastTarget=false，按钮缝隙的点击仍落到棋盘）+ 三颗 124px 圆钮
    ///     （action-circle 贴图 + CircularRaycastFilter 圆形射线）；
    ///   · 屏幕边缘内收直接复用 TowerActionMenu.TryGetButtonPositions（几何同名：上/左下/右下）；
    ///   · 有模态弹窗时自动隐藏（HasModal 与 TowerActionMenu 同一张清单）。
    ///
    /// 【prefab 契约】节点由 Assets/Editor/TacticalForgePrefabBuilder.BuildTowerBuildMenu 生成：
    ///   TowerBuildMenu/{Backdrop, BuildBtn_Normal, BuildBtn_Power, BuildBtn_Retard}，
    ///   每颗按钮含 Icon（塔头像）/ Label（塔名）/ PriceText（价格）。改结构必须与该生成器成对修改。
    ///
    /// 【与放置态（ghost 跟手）的关系】HUD 塔按钮的两条旧路径（快速点按 = 经典放置态、
    ///   长按拖拽 = 拖拽建造）原样保留；本菜单是第三条建造入口。
    ///   落地统一走 TowerManager.TryBuild —— 可建/无塔/金币/不堵死路径的校验、扣费、
    ///   事件（BuildTowerSuccess / BuildTowerFail）与旧路径完全同源，不另写一份判定。
    ///
    /// 【事件驱动】开/关全部由事件驱动，不轮询游戏状态：
    ///   BuildCellChosenEvent（打开/平移/同格 toggle）→ TowerSelectedEvent / TowerDeselectedEvent（关闭）
    ///   → GoldChangeEvent / LanguageChangedEvent（刷新价格与塔名）。LateUpdate 只做"跟随格子"。
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class TowerBuildMenu : MonoBehaviour
    {
        [SerializeField] private RectTransform menu;
        [SerializeField] private Button normalButton;    // type=1 单体（BuildBtn_Normal）
        [SerializeField] private Button powerButton;     // type=2 火力（BuildBtn_Power）
        [SerializeField] private Button retardButton;    // type=3 减速（BuildBtn_Retard；节点名 Retard ↔ 枚举 Slow，映射口径见 HudView）

        /// <summary>三颗按钮对应的塔型（下标与 _buttons 对齐）。</summary>
        private static readonly int[] ButtonTypes = { 1, 2, 3 };

        /// <summary>价格文字颜色：可负担 = 暖白，买不起 = 红（与 TowerActionMenu 的价格配色一致）。</summary>
        private static readonly Color PriceColor = new Color(0.89f, 0.95f, 1f, 1f);
        private static readonly Color PriceBlockedColor = new Color(1f, 0.48f, 0.38f, 1f);

        private readonly Button[] _buttons = new Button[3];
        private readonly TMP_Text[] _nameLabels = new TMP_Text[3];
        private readonly TMP_Text[] _priceTexts = new TMP_Text[3];
        /// <summary>装饰圆盘（TowerBuildMenu/Backdrop），prefab 序列化引用；旧 prefab 缺失时 Awake 兜底 Find。</summary>
        [SerializeField] private RectTransform _backdrop;

        /// <summary>菜单当前锚定的格子；row &lt; 0 = 已收起。</summary>
        private int _row = -1;
        private int _col = -1;
        private RectTransform _root;
        private Canvas _canvas;
        private Camera _worldCamera;
        private int _lastActionFrame = -1;
        private Vector2 _lastAnchor;
        private Rect _lastBounds;
        private bool _hasPlacement;

        public void Configure(RectTransform actions, Button normal, Button power, Button retard)
        {
            menu = actions;
            _buttons[0] = normalButton = normal;
            _buttons[1] = powerButton = power;
            _buttons[2] = retardButton = retard;
            for (int i = 0; i < 3; i++)
            {
                if (_buttons[i] == null)
                {
                    continue;
                }
                Transform label = _buttons[i].transform.Find("Label");
                Transform price = _buttons[i].transform.Find("PriceText");
                _nameLabels[i] = label != null ? label.GetComponent<TMP_Text>() : null;
                _priceTexts[i] = price != null ? price.GetComponent<TMP_Text>() : null;
            }
            // 背景圆盘（生成器已在 Configure 前建好节点）；prefab 里直接序列化引用，运行时免 Find
            _backdrop = actions.Find("Backdrop") as RectTransform;
        }

        private void Awake()
        {
            _root = (RectTransform)transform;
            _canvas = GetComponentInParent<Canvas>();
            if (menu == null || normalButton == null || powerButton == null || retardButton == null)
            {
                Debug.LogError("[TowerBuildMenu] HUD 建造圆盘节点缺失；请运行「Tools/塔防/Tactical Forge/更新实际 UI（保留 GUID）」重建 HudView.prefab。");
                enabled = false;
                return;
            }
            // 旧 prefab 没序列化 backdrop 时兜底补一次 Find（新生成的 prefab 已带引用）
            if (_backdrop == null)
            {
                _backdrop = menu.Find("Backdrop") as RectTransform;
            }
            normalButton.onClick.AddListener(BuildNormal);
            powerButton.onClick.AddListener(BuildPower);
            retardButton.onClick.AddListener(BuildRetard);
            SetVisible(false);
        }

        private void OnEnable()
        {
            EventDispatcher.AddEventListener<int, int>(EventName.BuildCellChosenEvent, ShowAt);
            EventDispatcher.AddEventListener<BaseTower>(EventName.TowerSelectedEvent, OnTowerSelected);
            EventDispatcher.AddEventListener(EventName.TowerDeselectedEvent, Hide);
            EventDispatcher.AddEventListener<int, int>(EventName.GoldChangeEvent, OnGoldChanged);
            EventDispatcher.AddEventListener<int>(EventName.LanguageChangedEvent, OnLanguageChanged);
        }

        private void OnDisable()
        {
            EventDispatcher.RemoveEventListener<int, int>(EventName.BuildCellChosenEvent, ShowAt);
            EventDispatcher.RemoveEventListener<BaseTower>(EventName.TowerSelectedEvent, OnTowerSelected);
            EventDispatcher.RemoveEventListener(EventName.TowerDeselectedEvent, Hide);
            EventDispatcher.RemoveEventListener<int, int>(EventName.GoldChangeEvent, OnGoldChanged);
            EventDispatcher.RemoveEventListener<int>(EventName.LanguageChangedEvent, OnLanguageChanged);
            Hide();
        }

        private void OnDestroy()
        {
            if (normalButton != null) normalButton.onClick.RemoveListener(BuildNormal);
            if (powerButton != null) powerButton.onClick.RemoveListener(BuildPower);
            if (retardButton != null) retardButton.onClick.RemoveListener(BuildRetard);
        }

        // ------------------------------------------------------------------
        // 打开 / 关闭
        // ------------------------------------------------------------------

        /// <summary>
        /// 在指定格打开（或平移到）建造圆盘；同一格再点一次 = 收起（toggle）。
        /// 【发送方保证】TowerPlacement 只在"空且可建且不堵路"的格子上发事件，
        /// 这里不再重复可建判定 —— 格子状态在菜单开着期间可能变化，点击落地时仍会校验。
        /// </summary>
        private void ShowAt(int row, int col)
        {
            if (_row == row && _col == col && menu != null && menu.gameObject.activeSelf)
            {
                Hide();
                return;
            }
            _row = row;
            _col = col;
            _hasPlacement = false;
            RefreshButtons();
            GameAudio.Play(SoundCue.UiClick);
            SetVisible(true);
        }

        private void Hide()
        {
            _row = -1;
            _col = -1;
            _hasPlacement = false;
            SetVisible(false);
        }

        /// <summary>选中了某座塔 → 塔动作菜单接管，建造圆盘让位。</summary>
        private void OnTowerSelected(BaseTower tower)
        {
            Hide();
        }

        private void OnGoldChanged(int gold, int delta)
        {
            RefreshButtons();
        }

        private void OnLanguageChanged(int language)
        {
            RefreshButtons();
        }

        // ------------------------------------------------------------------
        // 每帧：跟随格子 + 屏幕边缘内收
        // ------------------------------------------------------------------

        private void LateUpdate()
        {
            bool visible = _row >= 0 && !HasModal();
            if (!visible)
            {
                SetVisible(false);
                return;
            }
            BoardView board = BoardView.Instance;
            if (board == null)
            {
                SetVisible(false);
                return;
            }
            if (_worldCamera == null)
            {
                _worldCamera = CameraController.Instance != null
                    ? CameraController.Instance.GetComponent<Camera>()
                    : Camera.main;
            }
            if (_worldCamera == null || _root == null)
            {
                SetVisible(false);
                return;
            }
            Vector2 world = board.CellCenter(_row, _col);
            Vector3 point = _worldCamera.WorldToScreenPoint(new Vector3(world.x, world.y, 0f));
            if (point.z <= 0)
            {
                SetVisible(false);
                return;
            }
            Camera uiCamera = _canvas != null && _canvas.renderMode != RenderMode.ScreenSpaceOverlay
                ? _canvas.worldCamera
                : null;
            Vector2 local;
            if (!RectTransformUtility.ScreenPointToLocalPointInRectangle(_root, point, uiCamera, out local))
            {
                return;
            }
            // 锚点始终钉在格子上；贴近屏幕边缘时三颗按钮整体内收（与塔动作菜单同一套几何）。
            if (!_hasPlacement || local != _lastAnchor || _root.rect != _lastBounds)
            {
                Vector2 first, second, third;
                if (!TowerActionMenu.TryGetButtonPositions(local, _root.rect, out first, out second, out third))
                {
                    SetVisible(false);
                    return;
                }
                menu.localPosition = new Vector3(local.x, local.y, 0);
                ((RectTransform)_buttons[0].transform).anchoredPosition = first - local;
                ((RectTransform)_buttons[1].transform).anchoredPosition = second - local;
                ((RectTransform)_buttons[2].transform).anchoredPosition = third - local;
                _lastAnchor = local;
                _lastBounds = _root.rect;
                _hasPlacement = true;
            }
            SetVisible(true);
        }

        // ------------------------------------------------------------------
        // 按钮
        // ------------------------------------------------------------------

        /// <summary>按当前金币与语言刷新三颗按钮（塔名 / 价格 / 可负担性）；表里没有的塔型直接隐藏。</summary>
        private void RefreshButtons()
        {
            PlayerDataManager pd = PlayerDataManager.Instance;
            for (int i = 0; i < 3; i++)
            {
                Button button = _buttons[i];
                if (button == null)
                {
                    continue;
                }
                TowerConfig cfg = Configs.GetTowerByTypeAndLevelSilent(ButtonTypes[i], 1);
                if (cfg == null)
                {
                    // 与 HUD 塔按钮同口径：表里没这个塔型就不留"点了没反应"的死按钮
                    if (button.gameObject.activeSelf)
                    {
                        button.gameObject.SetActive(false);
                    }
                    continue;
                }
                if (!button.gameObject.activeSelf)
                {
                    button.gameObject.SetActive(true);
                }
                bool affordable = pd != null && pd.Gold >= cfg.Prices;
                button.interactable = affordable;
                if (_nameLabels[i] != null)
                {
                    _nameLabels[i].text = cfg.DisplayName;
                }
                if (_priceTexts[i] != null)
                {
                    _priceTexts[i].text = cfg.Prices.ToString();
                    _priceTexts[i].color = affordable ? PriceColor : PriceBlockedColor;
                }
            }
        }

        private void BuildNormal() { Build(0); }
        private void BuildPower() { Build(1); }
        private void BuildRetard() { Build(2); }

        /// <summary>
        /// 点塔图标 → 在锚定格建造该塔型。
        /// 【校验只此一处】可建/无塔/金币/堵路全部由 TowerManager.TryBuild 负责
        /// （失败自带 Tips 与失败音效）；这里只做"格子状态在菜单开着期间是否已变"的轻量复查
        /// —— 变了就收起，不给玩家一个必假的按钮。
        /// </summary>
        private void Build(int index)
        {
            if (_row < 0 || _lastActionFrame == Time.frameCount || HasModal())
            {
                return;
            }
            _lastActionFrame = Time.frameCount;
            BoardView board = BoardView.Instance;
            if (board == null)
            {
                Hide();
                return;
            }
            CellData cell = board.GetCell(_row, _col);
            if (cell == null || !cell.IsBuildable || cell.HasTower)
            {
                Hide();
                return;
            }
            BaseTower tower = TowerManager.Instance.TryBuild(ButtonTypes[index], 1, _row, _col);
            if (tower != null)
            {
                // 建成即收起（想连建就再点下一格）；失败时 TryBuild 已给具体原因，圆盘保留可换塔型再试
                Hide();
            }
        }

        // ------------------------------------------------------------------
        // 工具
        // ------------------------------------------------------------------

        /// <summary>模态弹窗打开时圆盘让位（与 TowerActionMenu 同一张清单，新增弹窗两处都要补）。</summary>
        private static bool HasModal()
        {
            var ui = UIManager.Instance;
            return ui.IsOpen(TowerInfoView.LogicalName) || ui.IsOpen(SellConfirmView.LogicalName)
                || ui.IsOpen(PauseView.LogicalName) || ui.IsOpen(SettingView.LogicalName)
                || ui.IsOpen(GameIntroView.LogicalName) || ui.IsOpen(LevelClearView.LogicalName)
                || ui.IsOpen("ConfirmView");
        }

        private void SetVisible(bool value)
        {
            if (menu != null && menu.gameObject.activeSelf != value)
            {
                menu.gameObject.SetActive(value);
            }
        }
    }
}
