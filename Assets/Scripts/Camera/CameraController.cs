using UnityEngine;

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
        /// 全局唯一实例（供战斗侧触发震动）。
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
        /// 触发一次屏幕震动。
        ///
        /// 【为什么不叠加而是取更强的一次】连续漏怪时如果每次都叠加，
        /// 相机振幅会迅速累积到看不清操作 —— 震动是反馈，不该变成惩罚。
        /// 【为什么在 LateUpdate 施加偏移】Update 里 FitBoard / 缩放改的是"真实位置"，
        /// 偏移必须最后叠加，否则会被它们覆盖掉（或者反过来污染真实位置）。
        /// </summary>
        public void Shake(float amplitude, float durationSec)
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

            float aspect = _cam.aspect > 0.0001f ? _cam.aspect : (16f / 9f);
            // 正交尺寸是"半高"，所以要同时满足高度与宽度（宽度需按宽高比折算）
            float ortho = Mathf.Max(halfHBoard + 0.5f * (padB + padT),
                                    (halfWBoard + Mathf.Max(padL, padR)) / aspect);

            // 安全区（刘海/挖孔）内缩换算成世界单位。像素↔世界换算依赖 ortho，
            // 先估一版再折算一次即可收敛（留白变化 → 视野变化很小，一遍足够）。
            if (fitSafeArea && Screen.width > 0 && Screen.height > 0 && _cam.pixelHeight > 0)
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

            _fitSize = ortho;
            _cam.orthographicSize = ortho;

            // 相机位置：底边留白精确 = padB（顶边余量 = 2·ortho − 棋盘高 − padB ≥ padT 恒成立）
            float camY = (_boardCenter.y - halfHBoard) - padB + ortho;
            _homePos = new Vector3(_boardCenter.x, camY, DefaultZ);

            // 平移夹取框 = 棋盘 + 四周留白（取景归位时视口恰好贴合该框 → 锁定中心）
            _frameMinX = _boardCenter.x - halfWBoard - padL;
            _frameMaxX = _boardCenter.x + halfWBoard + padR;
            _frameMinY = (_boardCenter.y - halfHBoard) - padB;
            _frameMaxY = (_boardCenter.y + halfHBoard) + padT;

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
            if (enableEdgeScroll && !IsInteractingWithTower())
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
