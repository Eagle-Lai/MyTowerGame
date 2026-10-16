using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// Switches artwork, without changing Animator state or time. Only configured prefabs opt in.
    /// Vertical motion is added to the existing clips by the editor builder, so one Animator
    /// owns both views and continues receiving State/Speed/Attack/Action normally.
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class EnemyDirectionalVisual : MonoBehaviour
    {
        public EnemyDirectionalProfile Profile;
        public SpriteRenderer[] HorizontalRenderers;
        public SpriteRenderer Head;
        public SpriteRenderer Body;
        public SpriteRenderer WingL;
        public SpriteRenderer WingR;
        public SpriteRenderer LegL;
        public SpriteRenderer LegR;

        [Range(1f, 2f)] public float AxisHysteresis = 1.2f;
        public EnemyFacing Facing { get; private set; }
        public int HeadIndex { get; private set; }
        private bool _hasFacing;

        public bool IsConfigured
        {
            get
            {
                return Profile && Profile.IsComplete && Head && Body && WingL && WingR && LegL && LegR
                    && HorizontalRenderers != null && HorizontalRenderers.Length > 0;
            }
        }

        /// <summary>Pure direction decision, shared by spawn, repath and movement.</summary>
        public static EnemyFacing SelectFacing(Vector2 motion, EnemyFacing previous, bool hasPrevious,
            float hysteresis = 1.2f)
        {
            if (motion.sqrMagnitude < 0.000001f) return previous;
            float x = Mathf.Abs(motion.x), y = Mathf.Abs(motion.y);
            bool horizontal = x >= y;
            if (hasPrevious)
            {
                bool wasHorizontal = previous == EnemyFacing.Left || previous == EnemyFacing.Right;
                float ratio = Mathf.Max(1f, hysteresis);
                horizontal = wasHorizontal ? y <= x * ratio : x > y * ratio;
            }
            return horizontal
                ? (motion.x < 0f ? EnemyFacing.Left : EnemyFacing.Right)
                : (motion.y < 0f ? EnemyFacing.Down : EnemyFacing.Up);
        }

        public bool Face(Vector2 motion)
        {
            if (!IsConfigured) return false;
            if (motion.sqrMagnitude < 0.000001f) return true;
            EnemyFacing next = SelectFacing(motion, Facing, _hasFacing, AxisHysteresis);
            if (!_hasFacing || next != Facing)
            {
                Facing = next;
                _hasFacing = true;
                ApplyView();
            }
            return true;
        }

        public void ResetForSpawn()
        {
            _hasFacing = false;
            Facing = EnemyFacing.Left;
            HeadIndex = 0;
            if (!IsConfigured) return;
            var receiver = GetComponent<MonsterAnimEventReceiver>();
            if (receiver) receiver.SetHead(0);
            ApplyView();
        }

        /// <summary>Receives the same AnimationEvent as the original horizontal head receiver.</summary>
        public void SetHead(int index)
        {
            if (index < 0 || index > 2) return;
            HeadIndex = index;
            if (IsConfigured && (Facing == EnemyFacing.Up || Facing == EnemyFacing.Down))
                Head.sprite = CurrentParts().HeadAt(index);
        }

        private EnemyDirectionalProfile.Parts CurrentParts()
        {
            return Facing == EnemyFacing.Up ? Profile.Up : Profile.Down;
        }

        private void ApplyView()
        {
            bool vertical = Facing == EnemyFacing.Up || Facing == EnemyFacing.Down;
            foreach (var sr in HorizontalRenderers) if (sr) sr.enabled = !vertical;
            Head.enabled = Body.enabled = WingL.enabled = WingR.enabled = LegL.enabled = LegR.enabled = vertical;
            if (!vertical) return;
            var parts = CurrentParts();
            Head.sprite = parts.HeadAt(HeadIndex);
            Body.sprite = parts.Body;
            WingL.sprite = WingR.sprite = parts.Wing;
            LegL.sprite = LegR.sprite = parts.Leg;
            WingL.flipX = false;
            WingR.flipX = true;
            // Back view: the tail/torso occludes the legs and lower neck.
            Head.sortingOrder = Facing == EnemyFacing.Up ? 12 : 25;
            WingL.sortingOrder = WingR.sortingOrder = 20;
        }
    }
}
