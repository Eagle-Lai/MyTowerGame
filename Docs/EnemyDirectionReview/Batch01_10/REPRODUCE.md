# 单角色复现

Unity 2022.3.62f3c1，工程 `E:/MyTowerGame`。先协调并取得编辑器安全窗口，保存当前场景，确认未在 Play、编译中或运行 BalancePlayModeVerifier。

本批只接受 Bat、BattlePanther、Bear、BearMounted、BlackBear、BlackBoar、BlackWolf、BlueScorpion、Boar、BoarMounted。不得执行全目录重建。

1. 如需重复接入，在 Project 选中一个表中角色的战斗 prefab，再执行 `Tools/塔防/敌人方向批次/接入选中的单个战斗预制体`。也可通过本工程 MCP 执行 `FTProject.EditorTools.EnemyDirectionalRigBuilder.Build("Bat");`，只替换成一个已授权名称。原始图集和源 prefab 不修改。
2. 检查 `EnemyDirectionalRigBuilder.Verify(spec, out report)`。该检查含两个临时克隆的重建钩子、无重复 DirectionVisual、无 Shadow、根/血条/事件引用、Missing 脚本、依赖和现有收集覆盖。克隆不落盘。
3. 执行 `FTProject.EditorTools.EnemyDirectionBatchReview.Start("Bat", "runtime_manual_01");`。证据版本目录必须全新；工具拒绝覆盖。该调用会进入本任务隔离 Play，约 20 秒后退出并恢复调用前已保存场景。
4. 检查对应目录 `actual_runtime_checks.txt` 的 84 PASS，以及 `exception.txt` 是否不存在；检查原始帧与 `actual_frames.jsonl` 的真实帧号、状态、方向和动作相位。
5. 使用 `build_runtime_media.py Bat runtime_manual_01` 合成四向/行走/转向/攻击死亡复用/暂停倍速媒体。该脚本拒绝失败版本，不生成或重采样角色姿态。画面仍需人工检查。

AdvancedHen 回归只调用通用审核工具，不重新构建其 prefab。不要复用原 AdvancedHenDirectionReview 中“Bat 未配置”的历史断言；本批使用完全未接入的 BugQueen 临时实例抽查旧分支，不改 BugQueen 资源。

验证路径/实例须遵守项目 AGENTS.md：发现当前 MyTowerGame 完整实例 ID、明确选定、确认 projectRoot/version；代码修改后通过 unityMCP/8082 完成刷新、编译、状态和控制台闭环。

审核工具仅在内存创建配置，不改表、ConfigJson/Gen、项目场景或战斗相机。资源收集覆盖不等于发布包回读；APK/真机与长期战斗未在本批执行。
