using UnityEngine;
using cfg;

namespace FTProject
{
    /// <summary>
    /// 音效配置视图（TBAudio 的一行）。
    /// 与其它 Config 包装类一样：字段缺失时给安全的默认值，不抛异常。
    /// </summary>
    public class AudioConfig
    {
        private readonly AudioData _a;

        public AudioConfig(AudioData a)
        {
            _a = a;
        }

        public int Id { get { return _a.Id; } }

        public string Name { get { return _a.Name; } }

        /// <summary>逻辑名。与 Assets/Audio/ 下的文件名一致（ResTable 里是 "Audio_" + 它）</summary>
        public string LogicalName { get { return _a.LogicalName; } }

        /// <summary>音量 0~1（缺省 1）</summary>
        public float Volume { get { return _a.Volume > 0f ? Mathf.Clamp01(_a.Volume) : 1f; } }

        /// <summary>音高（缺省 1 = 原速）</summary>
        public float Pitch { get { return _a.Pitch > 0f ? _a.Pitch : 1f; } }

        public bool Loop { get { return _a.Loop != 0; } }

        /// <summary>是否 3D 音效（0 = 2D 全局音，1 = 按世界坐标衰减）</summary>
        public bool Is3d { get { return _a.Is3d != 0; } }

        public string Desc { get { return _a.Desc; } }

        public override string ToString()
        {
            return string.Format("AudioConfig({0}, vol={1}, pitch={2})", LogicalName, Volume, Pitch);
        }
    }
}
