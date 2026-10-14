using UnityEngine;
using UnityEngine.EventSystems;

namespace FTProject
{
    /// <summary>
    /// 塔按钮的"按压/松开"中继组件（长按拖拽建造 · 2026-10-14）。
    ///
    /// 【为什么需要单独一个组件，而不能只靠 Button.onClick】
    ///   拖拽建造（对标《坚守阵地》）需要区分两种手势：
    ///     · 快速点按（按下→松开都在按钮上、时间短、没怎么动）→ 经典放置态（点击落子）；
    ///     · 长按 / 按住后移动 → 立即生成拖拽实例跟手，松手落子。
    ///   Button 只会给 onClick（松手时才判定），拿不到"按住了多久、挪了多远"，
    ///   所以必须监听 IPointerDownHandler / IPointerUpHandler。
    ///   本组件只做"转发"，手势判定（长按时长/位移阈值）全部在 HudView 里 ——
    ///   保持"HUD 一个脑子"的既有结构，避免判定逻辑散进 prefab 组件。
    ///
    /// 【为什么不进 prefab】由 HudView.Awake 对每个塔按钮 AddComponent（实例级），
    ///   不动 HudView.prefab 资产 —— prefab 里少一个脚本引用，就少一类
    ///   "prefab 与程序集版本错位"的 missing-script 风险。
    ///
    /// 【OnPointerUp 一定收得到吗】UGUI 会把 pointerUp 路由给"按下时捕获"的
    ///   pointerPress 对象，即使手指已经挪出按钮也会送达 —— 所以松手回调可靠；
    ///   而 onClick 只有"松手仍在按钮上"才触发，天然区分"原地松手/拖走松手"。
    /// </summary>
    public class TowerDragButton : MonoBehaviour, IPointerDownHandler, IPointerUpHandler
    {
        /// <summary>按下回调（HudView 记录按下时间/位置，开始长按计时）。</summary>
        public System.Action OnPressed;

        /// <summary>松开回调（HudView 判定这次按压最终算"拖拽"还是"点按"）。</summary>
        public System.Action OnReleased;

        public void OnPointerDown(PointerEventData eventData)
        {
            if (OnPressed != null)
            {
                OnPressed();
            }
        }

        public void OnPointerUp(PointerEventData eventData)
        {
            if (OnReleased != null)
            {
                OnReleased();
            }
        }
    }
}
