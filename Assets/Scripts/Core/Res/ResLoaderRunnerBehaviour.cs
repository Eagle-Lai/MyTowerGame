using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 协程宿主组件（无逻辑，只为 StartCoroutine 提供一个常驻 MonoBehaviour）。
    ///
    /// 【为什么单独成文件】Unity 要求 MonoBehaviour 的类名与文件名一致，
    /// 否则该组件拿不到 MonoScript，AddComponent 会失败、"script class cannot be found"。
    ///
    /// 本组件由 ResLoaderRunner 在首次使用时动态创建，并标记 DontDestroyOnLoad +
    /// HideAndDontSave（不出现在 Hierarchy、不随场景卸载）。
    /// </summary>
    public class ResLoaderRunnerBehaviour : MonoBehaviour
    {
    }
}
