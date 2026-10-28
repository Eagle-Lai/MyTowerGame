# Freedom Tower 原创音频资源

本目录包含 93 个原创音频 WAV 母版，均为 48 kHz / 24-bit PCM。

- BGM：4 首循环背景音乐（立体声）。
- Stingers：3 段胜利、失败及评级音乐短句（立体声）。
- SFX/UI：12 个界面音效。
- SFX/Tower：34 个防御塔及建造操作音效。
- SFX/Enemy：24 个敌人受击、死亡音效。
- SFX/Feedback：16 个回合与状态提示音效。

asset_manifest.csv 记录文件内容、变体、循环样本帧范围及技术测量结果；循环末端为不包含的样本帧。

2026-10-27 已将全部 93 个 WAV 接入游戏声音服务：包含菜单/准备/战斗/高压音乐、结算短曲、UI、塔操作、战斗、敌人与流程提示。运行配置位于 `Assets/Audio/Runtime/`，语义与地址由 `Assets/Scripts/Audio/AudioResourceMap.cs` 登记并接入 ResTable；不恢复旧 Luban 声音表。

导入策略为 BGM 流式 Vorbis，短音效及 Stinger 为 PCM 解压加载；默认与 Android 覆盖均已配置。母版 WAV 和 GUID 保留不变。README、清单、预览与制作源码不进入正式声音收集目录。

架构、完整资源映射、声音设置/旧档兼容、重建入口、已执行检查和运行验收清单见[声音接入实施记录](../../../Docs/AudioIntegration_Implementation_2026-10-27.md)。编辑器编译与隔离存档测试已通过，游戏播放及 Android 设备表现尚待用户验收。
完整制作源文件、MIDI、试听预览、质量报告及来源说明位于工程根目录的 AudioProduction/OriginalPack_20261023/。
人工听感仍待确认；已有自动技术检查不能替代听感验收。
