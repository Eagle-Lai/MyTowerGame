using FTProject;
using UnityEditor;
using UnityEngine;

namespace FTProject.EditorTools
{
    /// <summary>
    /// 敌人方向动画预览窗（编辑器内直接看"真实运行效果"）：
    /// 实例化战斗预制体 → 走真实代码路径（BaseEnemy.SetAnimState / EnemyDirectionalVisual.Face）
    /// 驱动动画与方向切换；播放开关用 Animator.Update 实时推进。
    /// 菜单：Tools/塔防/敌人方向示例/3. 方向动画预览窗。
    /// </summary>
    public sealed class EnemyDirectionPreviewWindow : EditorWindow
    {
        private EnemyDirectionSpec _spec;
        private GameObject _instance;
        private EnemyDirectionalVisual _visual;
        private Animator _animator;
        private bool _playing = true;
        private float _speed = 1f;
        private Vector2 _scroll;

        [MenuItem("Tools/塔防/敌人方向示例/3. 方向动画预览窗")]
        public static void Open()
        {
            var w = GetWindow<EnemyDirectionPreviewWindow>("方向预览");
            w.minSize = new Vector2(300f, 420f);
        }

        private static readonly string[] SpecNames = { "Monkey", "AdvancedHen" };
        private int _specIndex;

        private void OnEnable()
        {
            _specIndex = 0;
            _spec = EnemyDirectionPrefabBuilder.Monkey;
            EditorApplication.update += Tick;
        }

        private void OnDisable()
        {
            EditorApplication.update -= Tick;
            DestroyPreview();
        }

        private void Tick()
        {
            if (!_playing || _animator == null || Application.isPlaying) return;
            _animator.Update(0.016f * Mathf.Max(0.05f, _speed));
            Repaint();
        }

        private void OnGUI()
        {
            _scroll = EditorGUILayout.BeginScrollView(_scroll);
            EditorGUILayout.HelpBox(
                "编辑器内预览真实运行效果：实例 = 战斗预制体本体，按钮走真实代码路径\n" +
                "(BaseEnemy.SetAnimState / EnemyDirectionalVisual.Face → SetInteger(\"Dir\"))。\n" +
                "也可以把预制体拖进场景后直接进 Play 观察。", MessageType.Info);

            _specIndex = EditorGUILayout.Popup("规格", _specIndex, SpecNames);
            var picked = _specIndex == 1 ? EnemyDirectionPrefabBuilder.AdvancedHen : EnemyDirectionPrefabBuilder.Monkey;
            if (picked != _spec)
            {
                _spec = picked;
                DestroyPreview();
            }
            using (new EditorGUILayout.HorizontalScope())
            {
                if (GUILayout.Button("生成实例")) CreatePreview();
                if (GUILayout.Button("销毁实例")) DestroyPreview();
            }

            if (_instance == null)
            {
                EditorGUILayout.EndScrollView();
                return;
            }
            EditorGUILayout.LabelField("实例", _instance.name);
            EditorGUILayout.LabelField("朝向", _visual != null ? _visual.Facing.ToString() : "-");

            EditorGUILayout.Space();
            EditorGUILayout.LabelField("动画状态（BaseEnemy.SetAnimState）");
            using (new EditorGUILayout.HorizontalScope())
            {
                if (GUILayout.Button("待命")) SetState(EnemyAnimState.Idle);
                if (GUILayout.Button("准备")) SetState(EnemyAnimState.Ready);
                if (GUILayout.Button("行走")) SetState(EnemyAnimState.Walk);
            }
            using (new EditorGUILayout.HorizontalScope())
            {
                if (GUILayout.Button("奔跑")) SetState(EnemyAnimState.Run);
                if (GUILayout.Button("死亡")) SetState(EnemyAnimState.Death);
                if (GUILayout.Button("攻击"))
                {
                    SetState(EnemyAnimState.Walk);
                    if (_animator != null) _animator.SetTrigger("Attack");
                }
            }

            EditorGUILayout.Space();
            EditorGUILayout.LabelField("朝向（EnemyDirectionalVisual.Face）");
            using (new EditorGUILayout.HorizontalScope())
            {
                if (GUILayout.Button("← 左")) Face(Vector2.left);
                if (GUILayout.Button("→ 右")) Face(Vector2.right);
            }
            using (new EditorGUILayout.HorizontalScope())
            {
                if (GUILayout.Button("↑ 上")) Face(Vector2.up);
                if (GUILayout.Button("↓ 下")) Face(Vector2.down);
            }

            EditorGUILayout.Space();
            _playing = EditorGUILayout.Toggle(new GUIContent("播放（编辑器推进动画）"), _playing);
            _speed = EditorGUILayout.Slider(new GUIContent("速度倍率"), _speed, 0.1f, 3f);
            EditorGUILayout.EndScrollView();
        }

        private void CreatePreview()
        {
            DestroyPreview();
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(_spec.PrefabPath);
            if (prefab == null)
            {
                Debug.LogError("[DirectionPreview] 找不到预制体：" + _spec.PrefabPath);
                return;
            }
            _instance = (GameObject)PrefabUtility.InstantiatePrefab(prefab);
            _instance.name = "[" + _spec.Name + "DirectionPreview]";
            _visual = _instance.GetComponent<EnemyDirectionalVisual>();
            _animator = _instance.GetComponent<Animator>();
            Selection.activeGameObject = _instance;
            SceneView.lastActiveSceneView?.FrameSelected();
        }

        private void DestroyPreview()
        {
            if (_instance != null) DestroyImmediate(_instance);
            _instance = null;
            _visual = null;
            _animator = null;
        }

        private void SetState(EnemyAnimState state)
        {
            // 预览实例没走对象池 Init，BaseEnemy.SetAnimState 因 _anim 未缓存会静默返回，
            // 这里直接写与它完全相同的参数（State 整数 + Action 布尔）。
            if (_animator == null) return;
            _animator.SetBool(ActionHash, false);
            _animator.SetInteger(StateHash, (int)state);
            _animator.Update(0f);
        }

        private static readonly int StateHash = Animator.StringToHash("State");
        private static readonly int ActionHash = Animator.StringToHash("Action");

        private void Face(Vector2 dir)
        {
            if (_visual == null) return;
            _visual.Face(dir);
        }
    }
}
