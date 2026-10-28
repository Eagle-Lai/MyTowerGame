using UnityEngine;
using UnityEngine.EventSystems;

namespace FTProject
{
    /// <summary>Commit a user adjustment once; value synchronization never invokes this.</summary>
    public sealed class AudioSliderFeedback : MonoBehaviour, IPointerUpHandler, IEndDragHandler, IDeselectHandler
    {
        private bool _changed;
        public void MarkChanged() { _changed = true; }
        public void OnPointerUp(PointerEventData e) { Commit(); }
        public void OnEndDrag(PointerEventData e) { Commit(); }
        public void OnDeselect(BaseEventData e) { Commit(); }
        private void Commit()
        {
            if (!_changed) return;
            _changed = false;
            if (AudioRuntime.Current != null) AudioRuntime.Current.FlushSettings();
            GameAudio.Play(SoundCue.UiToggle);
        }
    }
}
