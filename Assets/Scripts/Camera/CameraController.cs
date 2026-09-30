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

        private Camera _cam;
        private float _fitSize = 5f;
        private Vector2 _boardCenter = Vector2.zero;

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
        /// 让整块棋盘完整落入视野（含留白）。
        /// 由 GameFlowManager 在棋盘建成后调用。
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

            float margin = cellSize;   // 四周各留一格
            float halfH = rows * cellSize * 0.5f + margin;
            float halfW = cols * cellSize * 0.5f + margin;

            float aspect = _cam.aspect > 0.0001f ? _cam.aspect : (16f / 9f);
            // 正交尺寸是"半高"，所以要同时满足高度与宽度（宽度需按宽高比折算）
            _fitSize = Mathf.Max(halfH, halfW / aspect);

            _boardCenter = boardCenter;
            _cam.orthographicSize = _fitSize;
            // 归位时清掉震动偏移：否则 LateUpdate 会把"上一帧的偏移"从新位置里减掉，导致对不准
            _shakeOffset = Vector3.zero;
            transform.position = new Vector3(boardCenter.x, boardCenter.y, DefaultZ);
        }

        private void Update()
        {
            HandleZoom();
        }

        private void HandleZoom()
        {
            float scroll = Input.GetAxis("Mouse ScrollWheel");
            if (Mathf.Abs(scroll) < 0.0001f)
            {
                if (Input.GetKeyDown(KeyCode.Space))
                {
                    // 一键回到自适应视野
                    _cam.orthographicSize = _fitSize;
                    _shakeOffset = Vector3.zero;
                    transform.position = new Vector3(_boardCenter.x, _boardCenter.y, DefaultZ);
                }
                return;
            }

            float min = _fitSize / Mathf.Max(1.01f, maxZoomOutFactor);
            float max = _fitSize * Mathf.Max(1.01f, maxZoomInFactor);
            float next = Mathf.Clamp(_cam.orthographicSize - scroll * zoomSpeed, min, max);
            _cam.orthographicSize = next;
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
