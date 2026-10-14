using UnityEngine;
using UnityEngine.Events;

namespace FTProject.Compat
{
    /// <summary>
    /// 【兼容占位】Poly Art 动物素材动画控制器所引用的“状态事件桥”占位实现
    /// （背景与方案详见 CompatMonsterAnimNote.cs 的类注释）。
    ///
    /// 该行为挂在 Death / Run / Attack 等动画状态上（m_StateMachineBehaviours 列表），
    /// 按字段名推断原脚本用途是“状态进入/更新/退出时触发 UnityEvent”。本工程所有控制器里
    /// 这些事件列表均为空（m_Calls: []），因此空实现与“原脚本”在本工程内的可观测行为一致，
    /// 也与“脚本缺失”等价。序列化字段与原数据一一对应
    /// （Name / StateEnterEvent / StateUpdateEvent / StateExit）。
    /// </summary>
    public class CompatMonsterAnimStateEvent : StateMachineBehaviour
    {
        public string Name;
        public UnityEvent StateEnterEvent = new UnityEvent();
        public UnityEvent StateUpdateEvent = new UnityEvent();
        public UnityEvent StateExit = new UnityEvent();
    }
}
