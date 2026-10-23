using System;
using UnityEngine;

namespace FTProject
{
    public enum EnemyFacing { Left, Right, Up, Down }

    /// <summary>Opt-in artwork for a monster. Original horizontal sprites remain on its prefab.</summary>
    [CreateAssetMenu(menuName = "FTProject/Enemy Directional Profile")]
    public sealed class EnemyDirectionalProfile : ScriptableObject
    {
        [Serializable]
        public sealed class Parts
        {
            public Sprite NormalHead;
            public Sprite AngryHead;
            public Sprite DeadHead;
            public Sprite Body;
            public Sprite Wing;
            public Sprite Leg;
            // False preserves the existing view; the example front torso covers its folded wings.
            public bool WingsBehindBody;

            public bool HasHeadAndBody { get { return NormalHead && AngryHead && DeadHead && Body; } }

            public bool IsComplete
            {
                get { return NormalHead && AngryHead && DeadHead && Body && Wing && Leg; }
            }

            public Sprite HeadAt(int index)
            {
                return index == 2 ? DeadHead : index == 1 ? AngryHead : NormalHead;
            }
        }

        // Optional complete per-view rigs for wings, quadrupeds and multi-legged enemies.
        // Existing six-part profiles retain their serialized behavior.
        public bool SeparateViewRigs;

        public Parts Up = new Parts();
        public Parts Down = new Parts();
        public RuntimeAnimatorController Controller;

        public bool IsComplete
        {
            get { return Up != null && Down != null && Controller && (SeparateViewRigs
                    ? Up.HasHeadAndBody && Down.HasHeadAndBody
                    : Up.IsComplete && Down.IsComplete); }
        }
    }
}
