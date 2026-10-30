using UnityEngine;

namespace FTProject
{
    /// <summary>Restores this character's authored side-body pose between pooled lives.</summary>
    [DisallowMultipleComponent]
    public sealed class PigSpawnPose : MonoBehaviour
    {
        [SerializeField] private Transform horizontalBody;
        [SerializeField] private Quaternion spawnRotation = Quaternion.identity;

        private void OnEnable()
        {
            RestorePose();
        }

        private void OnDisable()
        {
            // Rebind reads default values from transforms on the next pooled Init.
            // Restore after the completed death, before that rebind can capture its half-turn.
            RestorePose();
        }

        private void RestorePose()
        {
            if (horizontalBody) horizontalBody.localRotation = spawnRotation;
        }
    }
}
