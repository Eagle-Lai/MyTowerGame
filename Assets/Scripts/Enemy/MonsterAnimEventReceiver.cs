using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 怪物动画事件的接收者。
    ///
    /// 【为什么需要它】怪物美术包的动画里内置了 AnimationEvent，但**没有随包提供接收脚本**，
    /// 于是运行时 Console 会刷：
    /// `'Enemy_Bat' AnimationEvent 'SetHead' on animation 'Death' has no receiver!`
    /// 事件的语义从参数可以直接读出来（见 `_Common/Animations/*/Attack.anim`、`Death.anim`）：
    ///   · `SetHead(int)`：0=正常头、1=愤怒头、2=死亡头
    ///     （对应图集里的 `HeadNormal` / `HeadAngry` / `HeadDead` 三个精灵）
    ///     攻击动画里按 0→1→0 来回切，死亡动画里切成 2。
    ///   · `Event(string)`：形如 "Attack" 的通用事件钩子（原包用作音效/特效触发点）。
    ///
    /// 【挂在哪】Unity 把 AnimationEvent 发给**播放动画的 Animator 所在的那个 GameObject**，
    /// 所以本组件必须挂在 Animator 的 GameObject 上（生成预制体时由工具负责）。
    ///
    /// 【头部引用为什么由工具预填】运行期没法从一张 Sprite 反查同一图集里的其它精灵
    /// （Sprite 不暴露图集内的兄弟精灵），所以由 MonsterPrefabBuilder 在编辑期
    /// 用 AssetDatabase 枚举图集把三个头填进 HeadSprites。
    /// </summary>
    public class MonsterAnimEventReceiver : MonoBehaviour
    {
        /// <summary>头部渲染器（由生成工具预填；为空则 SetHead 自动查找一次）</summary>
        public SpriteRenderer HeadRenderer;

        /// <summary>
        /// 头部贴图，按 [正常, 愤怒, 死亡] 排列（由生成工具从图集里解析后预填）。
        /// 个别美术包缺某个状态（例如只有 Normal/Dead），缺失项为 null，SetHead 会自动回退。
        /// </summary>
        public Sprite[] HeadSprites;

        private bool _headSearched;

        private void Awake()
        {
            EnsureHeadRenderer();
        }

        /// <summary>
        /// 切换头部贴图。由 Attack / Death 动画的 AnimationEvent 调用。
        /// </summary>
        public void SetHead(int index)
        {
            EnsureHeadRenderer();
            if (HeadRenderer == null || HeadSprites == null || HeadSprites.Length == 0)
            {
                return;
            }
            if (index < 0 || index >= HeadSprites.Length)
            {
                return;
            }
            Sprite s = HeadSprites[index];
            if (s == null)
            {
                // 该美术包没有这个状态（例如只有 Normal/Dead），保持当前贴图不动
                return;
            }
            if (HeadRenderer.sprite != s)
            {
                HeadRenderer.sprite = s;
            }
        }

        /// <summary>
        /// 通用事件钩子（原包在攻击动画的关键帧发出，参数形如 "Attack"）。
        /// M0 不接音效/特效，所以这里是空实现 —— 它**必须存在**，
        /// 否则 Unity 会报 "has no receiver"。M2 接音效时在这里分发即可。
        /// </summary>
        public void Event(string name)
        {
            // 预留给 M2：按 name 播放音效 / 生成受击特效
        }

        /// <summary>兜底查找：从本组件的父级往上找到怪物根节点，再往下找名字含 Head 的渲染器</summary>
        private void EnsureHeadRenderer()
        {
            if (HeadRenderer != null || _headSearched)
            {
                return;
            }
            _headSearched = true;

            // 从最近的 BaseEnemy 所在节点往下找（避免找到别的怪物）
            BaseEnemy owner = GetComponentInParent<BaseEnemy>();
            Transform root = owner != null ? owner.transform : transform;
            SpriteRenderer[] rs = root.GetComponentsInChildren<SpriteRenderer>(true);
            for (int i = 0; i < rs.Length; i++)
            {
                if (rs[i] != null && rs[i].name.IndexOf("head", System.StringComparison.OrdinalIgnoreCase) >= 0)
                {
                    HeadRenderer = rs[i];
                    return;
                }
            }
        }
    }
}
