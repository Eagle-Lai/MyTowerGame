# BlueScorpion 背面参考尾巴修订 · 2026-10-23

本轮已接入并完成实际验证，等待用户美术审核。依据用户提供的背面蝎子参考，重做高拱尾巴，并按随后“尾巴弯曲再往中间靠一下”的反馈，将上端弯钩向身体中线收拢。保留原角色金棕配色、描边、甲节质感与后端尾根连接。最终状态和文件指纹见 progress.json。

两轮对最终安装资源的实际运行共 **168 PASS / 0 FAIL，589 帧**；覆盖上下行走、四方向切换、攻击、受击、朝上死亡、回收复用、实际暂停和 2/3 倍速。朝上行走、攻击及死亡阶段图均已人工查看，尾根连贯，弯钩靠近中线，未观察到尾针插入头部或画面裁切；死亡时尾部随身体共同淡出。程序结果不代表用户已接受尾巴造型。

当前实际动画：[行走](up_walk_fixed.gif)、[攻击](up_attack_fixed.gif)、[朝上死亡](up_death_fixed.gif)、[连续转向](continuous_turns.gif)；[四方向静态](four_directions.png)和[与旧版实际帧对照](tail_before_after.gif)。这些媒体仅对真实 Play 帧等比缩放、裁切和加标签，没有合成角色姿态。

## 方向与版本

- `generation/user_rear_reference.png` 为用户参考，仅使用尾部空间结构；不沿用其灰色材质、斜侧机位或文字水印。
- `layout_proposal.png` 是最初参考方案，12°；`layout_proposal_r02.png` 是本次收向中线后的离线布局，20°。这些图均为布局预演，不能替代实际运行证据。
- 后端尾根 `(0,0.65)` 保持固定，最终静态角度为 20°，尾部前景顺序为 25，宽高上限为 3.65 / 5.55，切片 pivot 为 `(0.46,0.07)`。保留原 245×344 切片矩形，图片等比缩放。
- 早先向右上伸展的方案已被否决，保留于兄弟目录 `BlueScorpionTailOut_20261023/`，其 `REJECTED_DO_NOT_APPLY.json` 明确禁止采用。此前内扣和朝下方案也保留历史身份，不表示通过。

## 图像来源与处理

沿用已读取的 imagegen 技能及工程用户明确授权的 AIHub Image API，通过项目授权的 Node fetch 编辑路径调用 `https://aihub.dog/v1/images/edits`。本轮只有一次请求，模型 gpt-image-2、medium、n=1，HTTP 200；实际返回 RGB PNG 1024×1536。

完整提示词为 `generation_prompt.txt`，四张输入、请求和结果记录、原始图片保存在 `generation/`。密钥仅在进程内存中读取，没有写入代码或交付物。后续收拢布局未再次调用生图。

处理后的图集仅 Up_Tail 矩形内 52,641 像素变化，矩形外变化为 0；所有其他切片像素保留。处理记录见 `processing_r02.json`，原始参考稿处理记录也予以保留。

## Unity 窗口与接入

准备阶段仅写 Docs，保留正在录制的 L02。录像于 10:37:50 正常结束，日志记录 `end ok=True frames=17931`。随后现场确认 Boot 场景干净、非播放、录像与方向审核验证器均停止；用户明确回复“已交回，继续接入并实测”后才应用资源，见 `unity_handoff.json`。

应用前对 39 份角色和方向代码文件复核指纹，无漂移。只调用 `EnemyDirectionalRigBuilder.Build("BlueScorpion")`，其 Verify 结果保存于 `installed.txt`；没有全量怪物重建。资源刷新和编译后重新发现实例并核对 E:/MyTowerGame / Unity 2022.3.62f3c1，错误日志为 0，scriptCompilationFailed=false，ready=true。

## 证据与审计入口

- `baseline.json`：本轮修改前 11,541 文件本地指纹；`source_snapshot.json` 为 C# 原文快照；`before/` 保留可恢复角色资源。既有 Balance 录像工具改动归为外部变化，不编辑或回滚。
- `runtime_input_identity.json`：两轮实际测试绑定的最终资源与代码身份。
- 实际原始帧输出到 `../Batch01_10/BlueScorpion/runtime_tailref_r02/` 和 `runtime_tailref_updeath_r02/`。第二轮用于朝上死亡；不把历史旧版 PASS 计入本轮。
- `scope_audit_final.json` 是最终范围审计；`scope_audit.json` 保留首次审计及其早先沿用的归属说明。最终说明已澄清 Balance 工具漂移发生在本轮基线之前，本轮没有修改 C#。
- 本轮共 10 份角色资源变化：图集、切片清单、布局、PNG 导入设置、4 份专用动作、专用控制器及战斗 prefab。其余 118 个战斗 prefab 与本轮修改前逐字节一致；原始图集、源 prefab、共享动画、GUID/Sprite ID 保留。4 份动作仅 Up/Tail 的位置和角度曲线变化，所有非美术原始组件语义保持一致。
- 两轮测试期间 11,541 份输入内容和集合不变；旧 Tail、TailUp、AnimationPolish、Batch 及被否决 TailOut 的身份指纹保留。
- `audit.py`、`build_focused_media.py` 为只读生产审计及真实帧裁切入口。精确变更前后 SHA256 见 `implementation_manifest.json`；最终全量指纹见 `final_fingerprints.json`。

结束状态见 `editor_validation.json`：Boot 场景干净，非播放，录像/审核验证器停止，manualSimulation=false，编译/重载/导入结束，scriptCompilationFailed=false，ready=true，当前错误和警告均为 0。Unity 已交回，不启动后续角色。

本轮不执行 APK/真机、发布包构建或回读、长期战斗和数值回归。程序检查通过不表示美术已获用户验收；交付最终实际动画后等待用户审核。
