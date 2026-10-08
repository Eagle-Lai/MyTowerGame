using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

namespace FTProject
{
    /// <summary>
    /// 界面级"全局点击音"（M4-W7）。
    ///
    /// 【为什么挂在界面上，而不是在每个 View 的 onClick 里手动 Play】
    ///   本项目有 7 个界面、几十个按钮，且不少按钮是**运行时创建**的
    ///   （例如 SelectView 每次显示都会 Instantiate 一批关卡按钮）。
    ///   逐个去写 `AudioManager.Play(AudioName.UiClick)` 的后果是：
    ///   ① 一定会漏；② 新加按钮的人不知道该写；
    ///   ③ 想换点击音要全局搜字符串。
    ///   挂在界面根节点上统一代管，就只需要在 `UIManager.Open` 里加一行。
    ///
    /// 【为什么要周期性重扫】
    ///   按钮是运行时创建的（关卡按钮、以后可能有的动态列表），
    ///   OnEnable 那一刻它们可能还不存在；SelectView 还会在每次 OnEnable 时
    ///   **销毁并重建**按钮，旧引用随之作废。
    ///   与其在每个 View 里加"通知钩子"，不如让本组件低频重扫：
    ///   代价是每个界面每 0.4 秒一次 `GetComponentsInChildren`（几十个节点，可忽略），
    ///   换来的是"谁建的按钮都能自动有声音"。
    ///
    /// 【为什么用未缩放时间】暂停界面在 timeScale=0 下打开，用缩放时间会让重扫停摆。
    /// </summary>
    public class UiClickSfx : MonoBehaviour
    {
        /// <summary>重扫间隔（秒）。太密没必要，太疏会让"新出现的按钮"短时间没声音。</summary>
        private const float RescanInterval = 0.4f;

        private readonly List<Button> _hooked = new List<Button>();
        private float _nextRescan;

        private void OnEnable()
        {
            // 立刻扫一次，避免刚打开的界面在第一次间隔内点了没声
            _nextRescan = 0f;
            HookAll();
        }

        private void OnDisable()
        {
            // 【必须解绑】界面会被 SetActive(false) 后复用（UIManager.Open 对已存在实例直接返回），
            // 不解绑会让同一个按钮累积多个监听 → 一次点击播多次（音量翻倍）。
            for (int i = 0; i < _hooked.Count; i++)
            {
                if (_hooked[i] != null)
                {
                    _hooked[i].onClick.RemoveListener(OnAnyClick);
                }
            }
            _hooked.Clear();
            _nextRescan = 0f;
        }

        private void Update()
        {
            if (Time.unscaledTime < _nextRescan)
            {
                return;
            }
            _nextRescan = Time.unscaledTime + RescanInterval;
            HookAll();
        }

        /// <summary>把本界面下所有 Button（含未激活的）都挂上点击音。可重复调用，幂等。</summary>
        private void HookAll()
        {
            // ① 先剔除已被销毁的引用（SelectView 重建按钮后，旧引用会变成"假 null"）
            for (int i = _hooked.Count - 1; i >= 0; i--)
            {
                if (_hooked[i] == null)
                {
                    _hooked.RemoveAt(i);
                }
            }

            // ② 再补齐新出现的按钮
            Button[] all = GetComponentsInChildren<Button>(true);
            for (int i = 0; i < all.Length; i++)
            {
                Button b = all[i];
                if (b == null || IsHooked(b))
                {
                    continue;
                }
                b.onClick.AddListener(OnAnyClick);
                _hooked.Add(b);
            }
        }

        /// <summary>
        /// 用 `==` 比较（UnityEngine.Object 重载了它，能正确处理"已销毁对象"）。
        /// 注意不要用 List.Contains —— 它走 EqualityComparer，语义与 Unity 的 == 不同。
        /// </summary>
        private bool IsHooked(Button b)
        {
            for (int i = 0; i < _hooked.Count; i++)
            {
                if (_hooked[i] == b)
                {
                    return true;
                }
            }
            return false;
        }

        private void OnAnyClick()
        {
            if (AudioManager.Instance != null)
            {
                AudioManager.Instance.Play(AudioName.UiClick);
            }
        }
    }
}
