using UnityEngine;
using UnityEngine.EventSystems;

namespace FTProject
{
    /// <summary>
    /// 2D 正交相机控制（v2.1 重写）。
    ///
    /// 相对 v1.0 的改动：
    ///   - **删掉全部 Physics.Raycast / Touch 旋转逻辑**（需求 8：去物理化）
    ///   - 原实现用 `Physics.Raycast(..., 3)` 拾取塔，且引用已删除的 TowerInfoView，
    ///     还挂在 EventName.OperateDown/Up（这两个事件名已不存在）→ 无法编译
    ///   - 固定俯视 2D：相机永远看向 +Z，只在 XY 平面平移与缩放
    ///
    /// 【坐标换算约定】正交相机下 `ScreenToWorldPoint` 的 z 必须传
    /// `-camera.transform.position.z`，否则算出的世界坐标落在错误的深度平面。
    /// BoardView 与 TowerPlacement 都遵循这个约定。
    ///
    /// 【2026-11-06 真机手势】桌面端两条老路径（滚轮缩放 / 中键拖拽）**原样保留**，
    /// 另加两条触屏路径与之一一对应：双指捏合 = 滚轮、单指长按后拖动 = 中键。
    /// 两套输入互斥判定见 HandleTouchGestures 的注释（真机上滚轮恒 0、中键不存在，
    /// 所以两套同时挂着不会叠加）。
    /// </summary>
    [RequireComponent(typeof(Camera))]
    public class CameraController : MonoBehaviour
    {
        /// <summary>默认相机 z（正交下只影响裁剪与换算深度）</summary>
        public const float DefaultZ = -10f;

        [Header("缩放")]
        [Tooltip("滚轮缩放速度")]
        public float zoomSpeed = 2f;
        [Tooltip("相对自适应尺寸的最大放大倍数")]
        public float maxZoomInFactor = 2.5f;
        [Tooltip("相对自适应尺寸的最大缩小倍数")]
        public float maxZoomOutFactor = 2f;

        /// <summary>
        /// 全局唯一实例（供战斗侧触发"漏怪"震动）。
        /// 【为什么允许为 null 调用】场景没相机时不应该让"漏怪扣血"这种核心逻辑崩掉，
        /// 调用方统一写成 if (CameraController.Instance != null)。
        /// </summary>
        public static CameraController Instance { get; private set; }

        [Header("平移（M4-2）")]
        [Tooltip("中键拖拽的灵敏度（1 = 跟手）")]
        public float panDragFactor = 1f;
        [Tooltip("键盘（WASD / 方向键）平移速度系数，会按当前缩放折算")]
        public float panKeySpeed = 1.2f;
        [Tooltip("鼠标贴到屏幕边缘时自动平移。放置/选中塔时会自动禁用，避免误触")]
        public bool enableEdgeScroll = true;
        [Tooltip("边缘触发带宽度（像素）")]
        public float edgeBandPx = 18f;

        [Header("触屏手势（真机：双指缩放 ≈ 滚轮 / 长按拖动 ≈ 中键）")]
        [Tooltip("总开关。关掉后真机上就只剩键盘（等于完全无法操作视角）")]
        public bool enableTouchGestures = true;
        [Tooltip("双指捏合灵敏度：1 = 两指距离变化多少，视野就跟着变化多少")]
        public float pinchZoomSpeed = 1f;
        [Tooltip("单指按住多久后进入拖动视角（秒）。取 0.25 与 HUD 塔按钮长按拖拽保持一致")]
        public float longPressPanDelay = 0.25f;
        [Tooltip("长按成立前允许的手指抖动（像素）。超过即认为是指针拖动，本次不接管")]
        public float longPressPanSlopPx = 14f;

        [Header("棋盘取景留白（单位：格，2026-10-16 多分辨率适配）")]
        [Tooltip("棋盘底边留白（格）——为底部 HUD 建造栏/倍速按钮让位")]
        public float bottomMarginCells = 2f;
        [Tooltip("棋盘顶边留白（格）——为顶部 HUD 芯片让位")]
        public float topMarginCells = 1f;
        [Tooltip("棋盘左右留白（格）")]
        public float sideMarginCells = 1f;
        [Tooltip("是否把屏幕安全区（刘海/挖孔）内缩计入取景留白")]
        public bool fitSafeArea = true;

        private Camera _cam;
        private float _fitSize = 5f;
        private Vector2 _boardCenter = Vector2.zero;

        // ---- 多分辨率适配（2026-10-16）----
        /// <summary>最近一次 FitBoard 的棋盘参数（分辨率/安全区变化时重算用）</summary>
        private int _boardRows;
        private int _boardCols;
        private float _boardCellSize;
        /// <summary>取景归位点（含底边留白偏移后的相机位置；空格键/重算回位用）</summary>
        private Vector3 _homePos;
        /// <summary>平移夹取框（棋盘 + 四周留白；视口大于框时锁定框中心）</summary>
        private float _frameMinX, _frameMaxX, _frameMinY, _frameMaxY;
        private bool _hasFit;
        private int _lastPixW = -1, _lastPixH = -1;
        private Rect _lastSafeArea;
        private Rect _displayArea = new Rect(0f, 0f, 1f, 1f);
        private bool _centeredHudFit;

        /// <summary>UI content area in full-screen normalized coordinates; never changes the camera pixel rect.</summary>
        public void SetDisplayArea(Rect area, bool centeredHudFit = false)
        {
            area=Rect.MinMaxRect(Mathf.Clamp01(area.xMin),Mathf.Clamp01(area.yMin),Mathf.Clamp01(area.xMax),Mathf.Clamp01(area.yMax));
            if(area.width<.1f || area.height<.1f || (area==_displayArea && centeredHudFit==_centeredHudFit))return;
            _displayArea=area;
            _centeredHudFit=centeredHudFit;
            ApplyBoardFit();
        }

        // ---- 触屏视角手势（2026-11-06）----
        /// <summary>单指手势所处的阶段；双指缩放单独占一个阶段，任何阶段都能抢占。</summary>
        /// <remarks>名字不能叫 TouchPhase —— 会和 UnityEngine.TouchPhase 撞名，导致 switch 里比较失败。</remarks>
        private enum TouchGesturePhase
        {
            None,      // 空闲：等待下一次按下
            Pressing,  // 已按下，正在等长按计时成立
            Panning,   // 长按成立，手指移动即平移视角
            Pinching,  // 双指缩放中（独占，直到所有手指抬起）
            Locked     // 本序列已被普通点按/拖塔占用，本次不再接管
        }

        private TouchGesturePhase _touchPhase = TouchGesturePhase.None;
        /// <summary>正在跟踪的手指 id（多指时 GetTouch(0) 的下标会变，必须按 id 找）</summary>
        private int _touchFingerId = -1;
        private Vector2 _touchStartPos;
        private Vector2 _touchLastPos;
        private float _touchPressTime;
        /// <summary>进入拖动后累计移动的像素数（用于判断"真的动过镜头"）</summary>
        private float _touchPanMovedPx;
        /// <summary>上一帧两指间距（捏合缩放的基准）</summary>
        private float _pinchPrevDist;
        /// <summary>本次触摸序列是否已被视角手势实际占用（供 TowerPlacement 跳过点选）</summary>
        private bool _touchConsumed;

        /// <summary>拖动累计超过该像素数才认为"真的平移过视角"，松手就不再当点按。</summary>
        private const float TouchPanConsumePx = 4f;

        // ---- 屏幕震动（M2-W5）----
        private Vector3 _shakeOffset;
        private float _shakeTimer;
        private float _shakeAmplitude;
        private float _shakeDuration;

        private void Awake()
        {
            Instance = this;
            _cam = GetComponent<Camera>();
            _cam.orthographic = true;
            _cam.transform.position = new Vector3(0f, 0f, DefaultZ);
        }

        private void OnDestroy()
        {
            if (Instance == this)
            {
                Instance = null;
            }
        }

        /// <summary>
        /// 屏幕震动的**唯一**入口：怪物走到终点（漏怪）。
        ///
        /// 【2026-10-30 用户定规】关卡内只有"怪到达终点"允许让场景抖动，
        /// 其余任何事件（开火、爆炸、命中、失败结算……）一律不得震动。
        /// 因此这里不再保留通用的 <c>Shake</c> 接口：方法名本身就是白名单，
        /// 谁想加抖动都必须显式改这里的 API，避免又被顺手加回"打击反馈"。
        ///
        /// 【为什么不叠加而是取更强的一次】连续漏怪时如果每次都叠加，
        /// 相机振幅会迅速累积到看不清操作 —— 震动是反馈，不该变成惩罚。
        /// 【为什么在 LateUpdate 施加偏移】Update 里 FitBoard / 缩放改的是"真实位置"，
        /// 偏移必须最后叠加，否则会被它们覆盖掉（或者反过来污染真实位置）。
        /// </summary>
        public void ShakeOnEnemyLeak(float amplitude, float durationSec)
        {
            if (amplitude <= 0f || durationSec <= 0f)
            {
                return;
            }
            _shakeAmplitude = Mathf.Max(_shakeAmplitude, amplitude);
            _shakeDuration = Mathf.Max(_shakeDuration, durationSec);
            _shakeTimer = Mathf.Max(_shakeTimer, durationSec);
        }

        private void LateUpdate()
        {
            // 先把上一帧的偏移减掉，还原出"真实位置"
            Vector3 basePos = transform.position - _shakeOffset;

            if (_shakeTimer > 0f)
            {
                _shakeTimer -= Time.deltaTime;
                if (_shakeTimer <= 0f)
                {
                    _shakeTimer = 0f;
                    _shakeAmplitude = 0f;
                    _shakeDuration = 0f;
                    _shakeOffset = Vector3.zero;
                }
                else
                {
                    float k = _shakeDuration > 0.0001f ? _shakeTimer / _shakeDuration : 0f;
                    Vector2 r = Random.insideUnitCircle * (_shakeAmplitude * k);
                    _shakeOffset = new Vector3(r.x, r.y, 0f);
                }
            }
            else
            {
                _shakeOffset = Vector3.zero;
            }

            transform.position = basePos + _shakeOffset;
        }

        /// <summary>
        /// 让整块棋盘完整落入视野（含 HUD 避让与安全区留白，2026-10-16 重写）。
        ///
        /// 留白策略（单位 = 格）：
        ///   · 底边 bottomMarginCells（默认 2）——为底部 HUD（建造栏下缘 49 / 上缘 177 @1080 基准）让位；
        ///   · 顶边 topMarginCells（默认 1）——为顶部 HUD 芯片让位；
        ///   · 左右 sideMarginCells（默认 1）+（可选）屏幕安全区内缩。
        /// 相机不再居中于棋盘，而是**下移**若干，使底边留白恰好等于 bottomMarginCells。
        ///
        /// 【为什么底边要比顶边大】按 16:9 的"屏幕像素预算"算平：
        ///   顶部 HUD ≤86px、底部 HUD ≤177px（1080 设计基准）；
        ///   棋盘高 9 格 + 底 2 格 + 顶 1 格 = 12 格 ≈ 1080px（每格 90px）→ 底 180 / 顶 90，
        ///   正好包住两头 HUD 且不浪费视野（旧版四边各 1 格时，建造栏会压住棋盘底行约 80% 行高）。
        /// </summary>
        /// <param name="rows">行数</param>
        /// <param name="cols">列数</param>
        /// <param name="cellSize">格子边长（世界单位）</param>
        /// <param name="boardCenter">棋盘几何中心的世界坐标</param>
        public void FitBoard(int rows, int cols, float cellSize, Vector2 boardCenter)
        {
            if (_cam == null)
            {
                _cam = GetComponent<Camera>();
            }
            _boardRows = rows;
            _boardCols = cols;
            _boardCellSize = cellSize;
            _boardCenter = boardCenter;
            _hasFit = true;
            ApplyBoardFit();
        }

        /// <summary>按当前屏幕比例/安全区重算取景（FitBoard 与运行期分辨率变化共用）。</summary>
        private void ApplyBoardFit()
        {
            if (_cam == null || !_hasFit || _boardRows <= 0 || _boardCols <= 0)
            {
                return;
            }

            float halfHBoard = _boardRows * _boardCellSize * 0.5f;
            float halfWBoard = _boardCols * _boardCellSize * 0.5f;

            float padB = Mathf.Max(0f, bottomMarginCells) * _boardCellSize;
            float padT = Mathf.Max(0f, topMarginCells) * _boardCellSize;
            float padL = Mathf.Max(0f, sideMarginCells) * _boardCellSize;
            float padR = padL;
            // The compact HUD already reserves its pixel gutters. Do not count old cell margins twice.
            if (_centeredHudFit) padB=padT=padL=padR=_boardCellSize*.12f;

            float aspect = _cam.aspect > 0.0001f ? _cam.aspect : (16f / 9f);
            // 正交尺寸是"半高"，所以要同时满足高度与宽度（宽度需按宽高比折算）
            float ortho = Mathf.Max(halfHBoard + 0.5f * (padB + padT),
                                    (halfWBoard + Mathf.Max(padL, padR)) / aspect);

            // 安全区（刘海/挖孔）内缩换算成世界单位。像素↔世界换算依赖 ortho，
            // 先估一版再折算一次即可收敛（留白变化 → 视野变化很小，一遍足够）。
            bool useUiArea = _centeredHudFit || _displayArea != new Rect(0f, 0f, 1f, 1f);
            if (!useUiArea && fitSafeArea && Screen.width > 0 && Screen.height > 0 && _cam.pixelHeight > 0)
            {
                Rect sa = Screen.safeArea;
                float pxPerUnit = _cam.pixelHeight / (2f * ortho);
                if (pxPerUnit > 0.0001f)
                {
                    padL += sa.xMin / pxPerUnit;
                    padR += (Screen.width - sa.xMax) / pxPerUnit;
                    padB += sa.yMin / pxPerUnit;
                    padT += (Screen.height - sa.yMax) / pxPerUnit;
                    ortho = Mathf.Max(halfHBoard + 0.5f * (padB + padT),
                                      (halfWBoard + Mathf.Max(padL, padR)) / aspect);
                }
            }

            if(useUiArea)
                ortho=Mathf.Max((halfHBoard+.5f*(padB+padT))/_displayArea.height,
                    (halfWBoard+.5f*(padL+padR))/(aspect*_displayArea.width));
            _fitSize = ortho;
            _cam.orthographicSize = ortho;

            // 相机位置：底边留白精确 = padB（顶边余量 = 2·ortho − 棋盘高 − padB ≥ padT 恒成立）
            float camY = (_boardCenter.y - halfHBoard) - padB + ortho;
            _homePos = new Vector3(_boardCenter.x, camY, DefaultZ);
            if(useUiArea)
                _homePos=new Vector3(_boardCenter.x+.5f*(padR-padL)-(_displayArea.center.x-.5f)*2f*ortho*aspect,
                    _boardCenter.y+.5f*(padT-padB)-(_displayArea.center.y-.5f)*2f*ortho,DefaultZ);

            // 平移夹取框 = 棋盘 + 四周留白（取景归位时视口恰好贴合该框 → 锁定中心）
            _frameMinX = _boardCenter.x - halfWBoard - padL;
            _frameMaxX = _boardCenter.x + halfWBoard + padR;
            _frameMinY = (_boardCenter.y - halfHBoard) - padB;
            _frameMaxY = (_boardCenter.y + halfHBoard) + padT;
            if(useUiArea)
            {
                // Panning/home clamping uses the enlarged frame, including the UI reservation.
                _frameMinX=Mathf.Min(_frameMinX,_homePos.x-ortho*aspect);
                _frameMaxX=Mathf.Max(_frameMaxX,_homePos.x+ortho*aspect);
                _frameMinY=Mathf.Min(_frameMinY,_homePos.y-ortho);
                _frameMaxY=Mathf.Max(_frameMaxY,_homePos.y+ortho);
            }

            transform.position = _homePos;
            // 归位时清掉震动状态：否则上一关结束前触发的震动会带进新关卡，
            // 表现为"刚进关画面还在抖"。偏移必须清，计时与幅度也要清，
            // 不然 LateUpdate 会在下一帧按旧幅度重新生成偏移。
            _shakeOffset = Vector3.zero;
            _shakeTimer = 0f;
            _shakeAmplitude = 0f;
            _shakeDuration = 0f;

            _lastPixW = _cam.pixelWidth;
            _lastPixH = _cam.pixelHeight;
            _lastSafeArea = Screen.safeArea;
        }

        private void Update()
        {
            RefitOnScreenChange();
            // 触屏手势放在最前：真机上滚轮恒 0、中键不存在，下面两条鼠标路径自动空转，
            // 两套输入不会叠加；编辑器里 touchCount 恒 0，也不会被触屏逻辑干扰。
            HandleTouchGestures();
            HandleZoom();
            HandlePan();
        }

        /// <summary>
        /// 分辨率 / 安全区变化时重算取景（2026-10-16）：折叠屏展开、分屏、编辑器切 Game View
        /// 比例等场景下，旧实现只在建关时算一次，比例变了不会重算（棋盘按旧比例取景）。
        /// 只在数值变化时触发，常态零开销；重算会复位视图（缩放/平移回到自适应档）。
        /// </summary>
        private void RefitOnScreenChange()
        {
            if (_cam == null || !_hasFit)
            {
                return;
            }
            if (_cam.pixelWidth == _lastPixW && _cam.pixelHeight == _lastPixH
                && Screen.safeArea == _lastSafeArea)
            {
                return;
            }
            ApplyBoardFit();
            Debug.Log(string.Format(
                "[Camera] 屏幕/安全区变化（{0}×{1}），重算棋盘取景 ortho={2:F2}",
                _cam.pixelWidth, _cam.pixelHeight, _fitSize));
        }

        /// <summary>
        /// 平移：中键拖拽 / WASD·方向键 / 鼠标贴屏幕边缘。
        ///
        /// 【为什么用中键而不是右键】右键已经被 TowerPlacement 用作"取消放置 / 取消选中"。
        ///
        /// 【为什么速度要乘 orthographicSize】放大之后，同样的像素拖拽对应的世界距离更小。
        /// 按视口高度折算，才能做到"不管缩放多少，推起来手感一致"。
        /// </summary>
        private void HandlePan()
        {
            if (_cam == null || Time.timeScale <= 0f)
            {
                return;   // 暂停时不平移
            }

            float dt = Time.deltaTime;
            float speed = _cam.orthographicSize * panKeySpeed;
            Vector3 delta = Vector3.zero;

            // ① 键盘
            float h = Input.GetAxisRaw("Horizontal");
            float v = Input.GetAxisRaw("Vertical");
            if (Mathf.Abs(h) > 0.01f || Mathf.Abs(v) > 0.01f)
            {
                delta += new Vector3(h, v, 0f).normalized * (speed * dt);
            }

            // ② 中键拖拽
            if (Input.GetMouseButton(2))
            {
                delta += new Vector3(-Input.GetAxisRaw("Mouse X"), -Input.GetAxisRaw("Mouse Y"), 0f)
                         * (_cam.orthographicSize * 0.05f * panDragFactor);
            }

            // ③ 边缘自动平移（放置/选中塔时禁用，否则拖塔到边缘会把镜头一起带走）
            // 【2026-11-06】真机上 Input.mousePosition = 第一根手指的位置：
            // 手持时拇指本来就贴在屏幕边缘，边缘滚屏会一直偷偷推镜头，还会和长按拖动抢控制权。
            // 边缘滚屏是鼠标语义，触屏有手指拖动就够了 —— 有手指按着时整条关掉。
            if (enableEdgeScroll && Input.touchCount == 0 && !IsInteractingWithTower())
            {
                Vector3 m = Input.mousePosition;
                if (m.x >= 0f && m.x <= Screen.width && m.y >= 0f && m.y <= Screen.height)
                {
                    Vector2 dir = Vector2.zero;
                    if (m.x < edgeBandPx) dir.x -= 1f;
                    else if (m.x > Screen.width - edgeBandPx) dir.x += 1f;
                    if (m.y < edgeBandPx) dir.y -= 1f;
                    else if (m.y > Screen.height - edgeBandPx) dir.y += 1f;
                    if (dir.sqrMagnitude > 0.01f)
                    {
                        delta += (Vector3)(dir.normalized * (speed * dt));
                    }
                }
            }

            if (delta.sqrMagnitude <= 0f)
            {
                return;
            }
            transform.position = ClampToBoard(transform.position + delta);
        }

        private static bool IsInteractingWithTower()
        {
            TowerPlacement tp = TowerPlacement.Instance;
            return tp != null && (tp.IsPlacing || tp.SelectedTower != null);
        }

        // ------------------------------------------------------------------
        // 触屏视角手势（2026-11-06）
        // ------------------------------------------------------------------

        /// <summary>本次触摸序列是否已经被视角手势（双指缩放 / 长按拖动）占用。</summary>
        /// <remarks>
        /// 给 TowerPlacement 用：真机上"长按拖视角"和"点塔/点空地开建造圆盘"共用同一根手指，
        /// 没有这个标记的话，长按的第一帧就会顺手选中塔并弹出圆盘，然后镜头一拖菜单挂在原地。
        /// 只有**真的动过镜头**才算占用 —— 按久了不动再抬起，仍然算一次正常点按。
        /// </remarks>
        public bool IsTouchViewGestureConsumed
        {
            get { return _touchConsumed; }
        }

        /// <summary>
        /// 触屏手势主循环：双指捏合 = 滚轮缩放，单指长按后拖动 = 中键平移。
        ///
        /// 【为什么要单独一套】旧实现只有 `Input.GetAxis("Mouse ScrollWheel")` 和
        /// `Input.GetMouseButton(2)`：真机上滚轮恒为 0、中键根本不存在，等于完全没有视角操作。
        /// 桌面端两条老路径原样保留，本方法在编辑器里因 `touchCount == 0` 直接退出。
        ///
        /// 【互斥规则 —— 需求"两个操作不能相互影响"落在下面 4 条上】
        ///   ① 第二根手指落下 → 缩放独占：立刻放弃单指的长按/拖动，并把本次序列标记为已占用。
        ///      双指松开一根后，**剩下那根不接管**，必须等所有手指抬起才允许下一轮手势，
        ///      否则捏合结束时手指先后抬起的那一下会变成平移，镜头会窜一段。
        ///   ② 手指从 UI 上起手、或正处在放塔/拖塔状态 → 完全不接管（交给 UI 与建造逻辑），
        ///      避免"点 HUD 按钮顺手把镜头拖走"和"拖塔时镜头跟着跑"。
        ///   ③ 长按成立前手指已经移动超过 longPressPanSlopPx → 判定为普通点按/拖动，本序列锁死不接管。
        ///   ④ 单指长按成立后，手指位移按"屏幕像素 → 世界单位"折算后平移；速度随缩放变化，
        ///      放大后同样一段手指距离推得更少，手感与中键拖拽一致。
        /// </summary>
        private void HandleTouchGestures()
        {
            if (!enableTouchGestures)
            {
                // 运行中被关掉时不能留残留标记，否则 TowerPlacement 的点选会被一直吞掉
                _touchConsumed = false;
                return;
            }
            if (_cam == null)
            {
                return;
            }

            int count = Input.touchCount;
            if (count <= 0)
            {
                ResetTouchGesture();
                return;
            }

            // ---- 双指：独占缩放 ----
            if (count >= 2)
            {
                HandlePinchZoom();
                return;
            }

            if (Time.timeScale <= 0f)
            {
                return;   // 暂停（结算/设置弹窗）不接管单指，免得在面板上误长按把镜头拖走
            }

            Touch touch = Input.GetTouch(0);
            switch (_touchPhase)
            {
                case TouchGesturePhase.Pinching:
                case TouchGesturePhase.Locked:
                    // 双指松掉一根 / 本序列已交给别的交互：等全部抬起再重置
                    return;

                case TouchGesturePhase.Pressing:
                {
                    if (!TryGetTouch(_touchFingerId, out touch))
                    {
                        _touchPhase = TouchGesturePhase.Locked;   // 跟踪的那根手指已抬起
                        return;
                    }
                    Vector2 moved = touch.position - _touchStartPos;
                    if (moved.sqrMagnitude > longPressPanSlopPx * longPressPanSlopPx)
                    {
                        // 长按没成立就先划走了 → 这是一次拖动/滑动，不抢
                        _touchPhase = TouchGesturePhase.Locked;
                        return;
                    }
                    if (Time.unscaledTime - _touchPressTime < longPressPanDelay)
                    {
                        return;
                    }
                    // 【为什么长按成立时还要再查一次 UI / 放塔态】
                    //   ① EventSystem 处理这次触摸可能晚于本脚本：按下那一帧 IsPointerOverGameObject
                    //      还可能返回 false，等到 0.25s 后就已经可靠了；
                    //   ② HUD 塔按钮同样是 0.25s 长按进入拖拽建造，同帧竞态下 IsPlacing 可能刚被置真。
                    //   这两条任一命中都必须放弃，否则会出现"一边拖塔一边拖镜头"。
                    if (IsTouchOverUI(_touchFingerId) || IsPlacingTower())
                    {
                        _touchPhase = TouchGesturePhase.Locked;
                        return;
                    }
                    // 长按成立：以当前位置为拖动基准，避免把前面那点抖动一次性补成一段位移
                    _touchPhase = TouchGesturePhase.Panning;
                    _touchLastPos = touch.position;
                    _touchPanMovedPx = 0f;
                    return;
                }

                case TouchGesturePhase.Panning:
                {
                    if (!TryGetTouch(_touchFingerId, out touch))
                    {
                        _touchPhase = TouchGesturePhase.Locked;
                        return;
                    }
                    // 拖动途中若进入了放置态（HUD 长按抢先生效），立刻让出控制权，避免塔和镜头一起动
                    if (IsPlacingTower())
                    {
                        _touchPhase = TouchGesturePhase.Locked;
                        return;
                    }
                    Vector2 deltaPx = touch.position - _touchLastPos;
                    _touchLastPos = touch.position;
                    if (deltaPx.sqrMagnitude <= 0f)
                    {
                        return;
                    }
                    _touchPanMovedPx += deltaPx.magnitude;
                    if (!_touchConsumed && _touchPanMovedPx >= TouchPanConsumePx)
                    {
                        _touchConsumed = true;   // 确实动过镜头 → 松手不再当点按处理
                    }
                    // 像素 → 世界：视口高度（2×ortho）对应 pixelHeight 像素。
                    // 取负号 = 画面跟着手指走（手指往右上推，镜头往左下移），与中键拖拽同向。
                    float worldPerPx = 2f * _cam.orthographicSize / Mathf.Max(1f, _cam.pixelHeight);
                    Vector3 worldDelta = new Vector3(-deltaPx.x, -deltaPx.y, 0f) * worldPerPx;
                    // 减去震动偏移：LateUpdate 会把它重新叠回去，否则震动期间拖动会丢一截
                    transform.position = ClampToBoard(transform.position - _shakeOffset + worldDelta);
                    return;
                }

                default:
                {
                    // 只从"这一帧刚按下"起手接管。手指已经在屏上才被我们看到（例如从 UI 划出来）
                    // 时不接管 —— 那种手势的起点属于 UI。
                    if (touch.phase != UnityEngine.TouchPhase.Began)
                    {
                        return;
                    }
                    if (IsTouchOverUI(touch.fingerId) || IsPlacingTower())
                    {
                        _touchPhase = TouchGesturePhase.Locked;
                        return;
                    }
                    _touchConsumed = false;   // 新一轮触摸从"未被占用"开始
                    _touchPhase = TouchGesturePhase.Pressing;
                    _touchFingerId = touch.fingerId;
                    _touchStartPos = touch.position;
                    _touchPressTime = Time.unscaledTime;
                    return;
                }
            }
        }

        /// <summary>
        /// 双指捏合缩放（等价于滚轮）。手指张开 = 放大，与滚轮向前同向。
        /// 【为什么不做"以捏合中点为锚"】滚轮缩放同样以屏幕中心为锚，两者保持一致；
        /// 且以中点为锚会和平移夹取框互相拉扯（缩放后位置要重新夹，画面会漂）。
        /// </summary>
        private void HandlePinchZoom()
        {
            Touch a = Input.GetTouch(0);
            Touch b = Input.GetTouch(1);

            if (_touchPhase != TouchGesturePhase.Pinching)
            {
                // 任何阶段（包括正在长按拖动）被第二根手指抢占：停止平移，进入缩放独占
                _touchPhase = TouchGesturePhase.Pinching;
                _pinchPrevDist = 0f;
                _touchConsumed = true;   // 双指落下即视为视角操作，抬手后不再当点按
            }

            float dist = Vector2.Distance(a.position, b.position);
            if (dist < 1f)
            {
                return;
            }
            if (_pinchPrevDist < 1f)
            {
                _pinchPrevDist = dist;   // 第一帧只记基准，避免落下瞬间跳变
                return;
            }

            float ratio = dist / _pinchPrevDist;
            _pinchPrevDist = dist;
            if (ratio <= 0f || Mathf.Abs(ratio - 1f) < 0.0005f)
            {
                return;
            }

            float min = _fitSize / Mathf.Max(1.01f, maxZoomOutFactor);
            float max = _fitSize * Mathf.Max(1.01f, maxZoomInFactor);
            float next = Mathf.Clamp(
                _cam.orthographicSize / Mathf.Pow(ratio, Mathf.Max(0.05f, pinchZoomSpeed)), min, max);
            if (Mathf.Approximately(next, _cam.orthographicSize))
            {
                return;
            }
            _cam.orthographicSize = next;
            transform.position = ClampToBoard(transform.position - _shakeOffset);
        }

        private void ResetTouchGesture()
        {
            _touchPhase = TouchGesturePhase.None;
            _touchFingerId = -1;
            _pinchPrevDist = 0f;
            _touchPanMovedPx = 0f;
            // 注意：_touchConsumed 故意不在这里清 —— 抬手那一帧 TowerPlacement 还要读它，
            // 顺序上谁先 Update 不确定；改到下一次按下（TouchGesturePhase.None）时重置。
        }

        /// <summary>按 fingerId 取当前触摸（多指时下标会重排，不能直接信 GetTouch 的序号）。</summary>
        private static bool TryGetTouch(int fingerId, out Touch touch)
        {
            for (int i = 0; i < Input.touchCount; i++)
            {
                Touch t = Input.GetTouch(i);
                if (t.fingerId == fingerId)
                {
                    touch = t;
                    return true;
                }
            }
            touch = default(Touch);
            return false;
        }

        private static bool IsTouchOverUI(int fingerId)
        {
            EventSystem es = EventSystem.current;
            return es != null && es.IsPointerOverGameObject(fingerId);
        }

        /// <summary>放塔/拖塔期间禁止触屏平移（与边缘滚屏的禁用口径一致）。</summary>
        private static bool IsPlacingTower()
        {
            TowerPlacement tp = TowerPlacement.Instance;
            return tp != null && tp.IsPlacing;
        }

        /// <summary>
        /// 把相机位置夹在"棋盘 + 留白"的取景框内（框由 FitBoard/ApplyBoardFit 预算）。
        ///
        /// 【为什么不是简单夹到棋盘矩形】正交相机看到的是一个矩形视口：
        /// 当视野比取景框还大（缩到最远）时，"把中心夹进框内"反而会导致画面抖动。
        /// 正确做法是夹取半径 = 框半尺寸 − 视野半尺寸；差值为负时直接锁死在框中心
        /// （Mathf.Clamp 在 min &gt; max 时行为未定义，必须显式处理）。
        /// 2026-10-16：框取代了原来的"棋盘矩形"——含 HUD 避让与安全区留白。
        /// </summary>
        private Vector3 ClampToBoard(Vector3 pos)
        {
            if (_cam == null || !_hasFit)
            {
                return pos;
            }
            float halfH = _cam.orthographicSize;
            float halfW = halfH * _cam.aspect;

            float cx = (_frameMaxX - _frameMinX) > 2f * halfW
                ? Mathf.Clamp(pos.x, _frameMinX + halfW, _frameMaxX - halfW)
                : 0.5f * (_frameMinX + _frameMaxX);
            float cy = (_frameMaxY - _frameMinY) > 2f * halfH
                ? Mathf.Clamp(pos.y, _frameMinY + halfH, _frameMaxY - halfH)
                : 0.5f * (_frameMinY + _frameMaxY);
            return new Vector3(cx, cy, DefaultZ);
        }

        private void HandleZoom()
        {
            float scroll = Input.GetAxis("Mouse ScrollWheel");
            if (Mathf.Abs(scroll) < 0.0001f)
            {
                if (Input.GetKeyDown(KeyCode.Space))
                {
                    // 一键回到自适应视野（归位点 = FitBoard 算出的 _homePos，含底边留白偏移）
                    _cam.orthographicSize = _fitSize;
                    _shakeOffset = Vector3.zero;
                    transform.position = ClampToBoard(_homePos);
                }
                return;
            }

            float min = _fitSize / Mathf.Max(1.01f, maxZoomOutFactor);
            float max = _fitSize * Mathf.Max(1.01f, maxZoomInFactor);
            float next = Mathf.Clamp(_cam.orthographicSize - scroll * zoomSpeed, min, max);
            _cam.orthographicSize = next;
            // 缩放后视野变了，原来的位置可能已经越界 —— 立刻夹一次
            transform.position = ClampToBoard(transform.position - _shakeOffset);
        }

        /// <summary>屏幕坐标 → 世界坐标（z 取相机所在深度平面）</summary>
        public Vector3 ScreenToWorld(Vector2 screenPos)
        {
            return _cam.ScreenToWorldPoint(new Vector3(screenPos.x, screenPos.y, -transform.position.z));
        }

        /// <summary>世界坐标 → 屏幕坐标</summary>
        public Vector3 WorldToScreen(Vector3 world)
        {
            return _cam.WorldToScreenPoint(world);
        }
    }
}
