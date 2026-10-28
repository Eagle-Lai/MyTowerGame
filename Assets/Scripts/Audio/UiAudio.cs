using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace FTProject
{
    /// <summary>Pointer/submit feedback only; programmatic onClick and value synchronization stay silent.</summary>
    public sealed class UiAudio : MonoBehaviour, IPointerClickHandler, ISubmitHandler
    {
        public bool silent;
        public SoundCue cue = SoundCue.UiClick;
        private Button _button;
        private int _lastFrame = -1;

        private void Awake() { _button = GetComponent<Button>(); }
        public void OnPointerClick(PointerEventData data)
        {
            if (data.button == PointerEventData.InputButton.Left && !data.dragging) Feedback();
        }
        public void OnSubmit(BaseEventData data) { Feedback(); }
        private void Feedback()
        {
            if (silent || _button == null || !_button.IsInteractable() || _lastFrame == Time.frameCount) return;
            _lastFrame = Time.frameCount;
            GameAudio.Play(cue);
        }

        public static void Bind(GameObject root)
        {
            if (root == null || root.name == "HotUpdateView") return;
            foreach (var button in root.GetComponentsInChildren<Button>(true)) BindButton(button);
        }

        public static void BindButton(Button button)
        {
            if (button == null || button.GetComponent<UiAudio>() != null) return;
            var audio = button.gameObject.AddComponent<UiAudio>();
            string n = button.name.ToLowerInvariant();
            // These actions have result-dependent business feedback. A click must not claim success.
            audio.silent = n.Contains("upgrade") || n.Contains("build") || n.Contains("tower_") ||
                n.Contains("speed") || n.Contains("pause") || n.Contains("resume") ||
                (button.GetComponentInParent<HudView>() != null && (n == "startbutton" || n == "btn_intro")) ||
                (rootName(button.transform) == "SellConfirmView" && n.Contains("confirm"));
            if (n == "bg" || n.Contains("back") || n.Contains("close") || n.Contains("cancel")) audio.cue = SoundCue.UiBack;
            else if (n.Contains("confirm") || n.Contains("ok")) audio.cue = SoundCue.UiConfirm;
        }

        private static string rootName(Transform node)
        {
            while (node != null) { if (node.GetComponent<SellConfirmView>() != null) return "SellConfirmView"; node = node.parent; }
            return "";
        }
    }
}
