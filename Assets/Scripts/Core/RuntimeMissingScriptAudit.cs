using System.Collections;
using System.Collections.Generic;
using System.Text;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace FTProject
{
    /// <summary>
    /// 【真机诊断】运行时"缺失脚本（missing script）"扫描器。
    ///
    /// 背景：AB 资源里的脚本引用（GUID）若在运行时无法解析，Unity 会逐条打
    /// “The referenced script on this Behaviour (Game Object '…') is missing!”。
    /// 海量警告里很难看出"到底哪个对象挂了 missing"，尤其 GameObject 显示为 '&lt;null&gt;'
    /// 时（StateMachineBehaviour 等不属于任何 GameObject 的行为）。
    /// 本扫描器在关卡初始化完成后延时扫一遍场景对象树，把结果**汇总成一条日志**：
    ///   - 无缺失 → “[Audit] 缺失脚本扫描：0”；
    ///   - 有缺失 → 列出 对象完整路径 + 缺失槽位数（路径可直接在 Hierarchy 里定位）。
    ///
    /// 检测原理：GameObject.GetComponents&lt;Component&gt;() 返回的数组里，
    /// 缺失脚本的槽位为 null —— 出现 null 即该对象上有 missing script。
    ///
    /// 【为什么延时扫描】关卡初始化（UI 打开 / 资源实例化 / 快照恢复）是分帧完成的，
    /// 立即扫描会漏掉当帧之后才实例化的对象；默认延迟 1 秒覆盖整个启动窗口。
    ///
    /// 【开销】每关一次、数百对象 × GetComponents，毫秒级；无缺失时只打一行 OK。
    /// </summary>
    public static class RuntimeMissingScriptAudit
    {
        /// <summary>延时扫描入口（host 用 GameFlowManager 自身即可）。</summary>
        public static void RunDeferred(MonoBehaviour host, float delaySec = 1f)
        {
            if (host == null)
            {
                return;
            }
            host.StartCoroutine(RunCo(delaySec));
        }

        private static IEnumerator RunCo(float delaySec)
        {
            yield return new WaitForSecondsRealtime(delaySec);

            int missingObjects = 0;
            int missingSlots = 0;
            StringBuilder detail = null;

            // 场景根对象树（含 DontDestroyOnLoad 场景——SceneManager 会一并列出）
            List<GameObject> roots = new List<GameObject>(64);
            for (int s = 0; s < SceneManager.sceneCount; s++)
            {
                Scene scene = SceneManager.GetSceneAt(s);
                if (!scene.isLoaded)
                {
                    continue;
                }
                scene.GetRootGameObjects(roots);
            }

            for (int i = 0; i < roots.Count; i++)
            {
                Walk(roots[i], ref missingObjects, ref missingSlots, ref detail);
            }

            if (missingSlots > 0)
            {
                Debug.LogWarning(string.Format(
                    "[Audit] 缺失脚本（missing script）扫描：{0} 个对象 / {1} 个槽位。明细：\n{2}",
                    missingObjects, missingSlots, detail));
            }
            else
            {
                Debug.Log("[Audit] 缺失脚本扫描：0（全部脚本引用解析正常）");
            }
        }

        private static void Walk(GameObject go, ref int missingObjects, ref int missingSlots, ref StringBuilder detail)
        {
            Component[] comps = go.GetComponents<Component>();
            int nullCount = 0;
            for (int i = 0; i < comps.Length; i++)
            {
                if (comps[i] == null)
                {
                    nullCount++;
                }
            }
            if (nullCount > 0)
            {
                missingObjects++;
                missingSlots += nullCount;
                if (detail == null)
                {
                    detail = new StringBuilder(512);
                }
                detail.Append("  - ").Append(GetPath(go.transform))
                      .Append("（缺失 ").Append(nullCount).Append(" 个脚本槽位）\n");
            }

            Transform t = go.transform;
            for (int i = 0; i < t.childCount; i++)
            {
                Walk(t.GetChild(i).gameObject, ref missingObjects, ref missingSlots, ref detail);
            }
        }

        private static string GetPath(Transform t)
        {
            StringBuilder sb = new StringBuilder(128);
            while (t != null)
            {
                if (sb.Length > 0)
                {
                    sb.Insert(0, '/');
                }
                sb.Insert(0, t.name);
                t = t.parent;
            }
            return sb.ToString();
        }
    }
}
