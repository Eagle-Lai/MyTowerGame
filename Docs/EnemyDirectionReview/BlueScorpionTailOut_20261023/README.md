# BlueScorpion 尾梢外弯方案 · 2026-10-23

当前状态：**仅在 Docs 中完成美术与待应用资源，尚未接入生产工程，尚未做本版运行验证。**

用户指出上一轮尾巴扣向头部、背甲，要求向身体外侧弯曲。本轮重新制作 Up_Tail 分件：尾根接腹部后端，尾杆上扬，尾梢向画面右上外侧展开，远离头部和背甲。[离线前后对照](layout_proposal.png)左侧为上轮内扣，右侧为本轮外展。最终仍需用户核对其意图，不能把此图当作已批准或实际运行效果。

## 已完成

- 读取现有布局、切片、构建器和本地资源；建立 11541 文件基线、C# 原文快照和完整角色方向资源备份。
- 上一轮最终身份之后的两份 Balance 工具漂移均记录为既有外部变更，没有回滚或覆盖。
- 已查询、查看网络参考；来源与适用边界见 [references.md](references.md)。本轮按用户的美术要求选择外展姿态，不把防御姿态的照片当作唯一规范。
- 使用 imagegen 技能指导和项目已授权的 AIHub `gpt-image-2` 编辑接口，仅调用一次，n=1、quality=medium；HTTP 200。实际返回 PNG / RGB / 1254×1254，与请求 1024×1024 不同，按实际尺寸处理。提示词见 generation_prompt.txt，输入、请求、原始输出和结果留在 generation/。generate.mjs 是项目授权的 Node fetch 调用，密钥仅存在进程内存，未写入交付物。
- 清除白底后等比缩放到原 Up_Tail 切片 245×344，保持原矩形和其他切片。仅该矩形内 57594 像素变化，矩形外逐像素差异为 0，详见 processing.json。
- 三份待应用资源位于 staged/：Directions.png、Directions.sprites.json、Directions.layout.json。原 PNG、源 prefab、生产图集和所有其他生产资源目前未被本任务改动；staged_manifest.json 保存待应用指纹。
- Up/Tail 最终待应用布局 x=0.25、y=0.65、width=3.05、height=4.9、angle=0、order=15；pivot=(0.17,0.12)。Down 和其他分件不变。

## 接入窗口待交接

准备期间现场发现 Unity Main.unity 正由另一任务运行 BalancePlayModeVerifier / Library/BalanceWorkbench/Video-Batch，录制 L02。遵守原始任务第一节第 5 条，保持生产文件、刷新、编译和播放状态不动。与原数值报告 chat 协调后，对方确认不是录像持有者，详见 coordination.md；不能以该 chat 的回复代替实际持有者交接。

已向用户请求：核对右侧外展方向；安排录像在当前关完成后交回 Unity，或明确授权立即停止此次录像。等待答复期间没有应用 staged 资源，没有中断录制。

## 收到窗口后的继续步骤

1. 重新发现 unityMCP 实例，明确选择并核对 E:/MyTowerGame / 2022.3.62f3c1；确认录像与实测结束、编辑器 idle、场景已保存。
2. 运行 apply_staged.py 前核对本轮方向反馈。脚本再次核对所有将覆盖的角色文件及方向相关代码指纹，只安装三份待应用文件，发现漂移会拒绝覆盖。
3. force/all/request 刷新与编译，等待完整 ready，再用单例 EnemyDirectionalRigBuilder.Build("BlueScorpion") 接入。保留 GUID 和 Sprite ID，执行 Verify 并存 installed.txt。
4. 以全新 runtime_tailout_r01 / runtime_tailout_updeath_r01 分别完成原生审核和 Up 死亡补测；build_focused_media.py / audit.py 已准备，尚未执行。检查尾根连接、向外摆动、攻击、死亡和完整裁切，再交付实际媒体。
5. 保存本轮精确前后 SHA256、范围/语义审计、最终编辑器状态和指纹，保留所有旧版本身份；本轮美术审核前不处理后续角色。

当前没有本版 PASS 数量，也没有将旧版运行结果用于证明本版完成。没有 APK/真机、发布包或长期战斗结果。
