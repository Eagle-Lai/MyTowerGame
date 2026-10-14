using UnityEngine;

namespace FTProject.Compat
{
    /// <summary>
    /// 【兼容占位】Poly Art 动物素材动画控制器所引用的 StateMachineBehaviour 占位实现。
    ///
    /// 背景：Assets/_UIAssets/Monsters 下 29 个动画控制器（Rat/Bear/Boar/…）自素材导入起
    /// 就引用两个从未随包进入本工程的脚本 GUID（408e227577c5a194ba246d63582e3419 /
    /// 57830dc1190df88479e9a6155ff52be7）。缺脚本的 StateMachineBehaviour 不属于任何
    /// GameObject，运行时每次加载敌人资源（进关卡会预加载全部敌人 prefab）都会报
    /// “The referenced script on this Behaviour (Game Object '<null>') is missing!”
    /// ——即模拟器截图中刷屏的那批警告（29 条 ≈ 29 个控制器/敌人资源）。
    ///
    /// 本类用**手工指定 meta guid** 的方式恢复这条引用的解析：
    ///   - GUID 与原引用一致（408e227577c5a194ba246d63582e3419，写在 .cs.meta 里）；
    ///   - 序列化字段与原数据一致（Name / Continuous / Active）；
    ///   - 行为为空实现 —— 与"脚本缺失时完全不被执行"等价，不改变任何现有表现，
    ///     消除警告是其唯一效果。
    ///
    /// 【将来若拿到素材原脚本】把本文件替换为原实现即可（GUID 不变，控制器引用自动生效）。
    /// </summary>
    public class CompatMonsterAnimNote : StateMachineBehaviour
    {
        public string Name;
        public bool Continuous;
        public bool Active;
    }
}
