"""Update the marked live status and the complete next-owner instructions."""
from pathlib import Path
import re

H = Path(__file__).resolve().parents[1]
README = H.parent / "README.md"
PROMPT = H / "REMAINING_ENEMIES_EXECUTABLE_PROMPT_20261026.md"
NEXT = H / "NEXT_ENEMY_TASK.md"

live = (
    "2026-10-28 Turkey101已record，90/108，completed_pending_user_art_review、user_approved=false。"
    "Up/Down使用已保存raw，14透明分件；只修补封闭alpha孔1,004像素，已有非孔像素与raw不变，最终14片内部孔0。"
    "安装Verify通过；原Ready/Walk/Attack/Death水平曲线、事件、时长/loop及root/HP/pool检查通过，无C#改动。"
    "runtime_r01与runtime_updeath_r01各84/0、343帧，共168/0及686真实PNG；均回到Boot且场景clean。"
    "实审离线proof、四向图、runtime strip、选定原尺寸攻击/受击/死亡帧，以及12个GIF各5个采样点；Up无脸后视、Down表情/攻击清晰、受击闪白和死亡淡出可见，成对翅膀/腿和单尾转向连续；非逐GIF全帧审阅。"
    "AllGIF共1438，Turkey12源/归档SHA匹配。5,345基线→5,365当前、22路径变化、incremental unexpected=0；另有未修改ReporterEditor写入build_info时间戳。保护源其余5项与共享C#无漂移。"
    "旧global audit的291 unexpected/6历史语义失败不属于Turkey增量审计。最终Unity经8088核对E:/MyTowerGame/2022.3.62f3c1，console error=0，编译/更新/Play/review均idle，Boot单场景clean、ready_for_tools=true；external_changes_dirty=true，保留此现场标记。"
    "Turkey证据见Turkey/final_validation_20261028.json、version_binding_final_20261028.json、scope_incremental_final_20261028.json和conversation_handoffs/20261028_202757_Turkey_completed.md。"
    "下一唯一VolcanoParasite102为not_started，dispatch token为turkey-to-volcanoparasite-20261028-846ed4a4-803c-47fb-bd74-d1819f09a29c；Turkey仍待用户美术审核。"
)

for path, begin, end in [
    (README, "<!-- ENEMY_README_LIVE_BEGIN -->", "<!-- ENEMY_README_LIVE_END -->"),
    (PROMPT, "<!-- ENEMY_SERIAL_LIVE_STATE_BEGIN -->", "<!-- ENEMY_SERIAL_LIVE_STATE_END -->"),
]:
    text = path.read_text(encoding="utf-8")
    assert text.count(begin) == text.count(end) == 1, path
    text = re.sub(re.escape(begin) + r".*?" + re.escape(end), begin + "\n" + live + "\n" + end, text, flags=re.S)
    path.write_text(text, encoding="utf-8")

next_text = """# 下一唯一角色 VolcanoParasite(index 102)

工程 `E:/MyTowerGame`，Unity `2022.3.62f3c1`。父线程 `01a18233-1a0c-7653-9ac2-6ecd99754a92` 已完成 Turkey(index 101)，进度 90/108；Turkey 为 `completed_pending_user_art_review`、`user_approved=false`。

唯一 dispatch token：`turkey-to-volcanoparasite-20261028-846ed4a4-803c-47fb-bd74-d1819f09a29c`。

## 开工与所有权

先读取根 `AGENTS.md`、`ProjectSettings/ProjectVersion.txt`、`Docs/EnemyDirectionReview/README.md`、本目录的原执行 prompt/续接协议/图片中转恢复说明、本文件、`conversation_chain.json`、实时 `progress.json`、standing network recovery authorization、TreasureChest recovery application，以及以下交接和评估：

- `Docs/EnemyDirectionReview/Remaining_20261024/conversation_handoffs/20261028_202757_Turkey_completed.md`
- `Docs/EnemyDirectionReview/Remaining_20261024/VolcanoParasite/successor_assessment_20261028_202757.json`
- `Docs/EnemyDirectionReview/Remaining_20261024/VolcanoParasite/successor_prompt_20261028_202757.txt`

仅当实时 chain 为 `active`、owner 是本新线程、current character 为 VolcanoParasite 且 token 完全一致时开始生产/Unity/付费操作。处于 `handoff_ready` 时只读等待父登记，不依时间抢锁。只有一个角色所有者；禁止 fork、子代理、并行角色、定时器、模型或推理覆盖。

## VolcanoParasite 现场

实时进度为 index 102、`not_started`。角色目录目前只有 `reference/`，其中包含源 prefab、战斗 prefab、源图集、`source_structure.json` 和离线源预览；没有 anatomy、generation request/raw、staged art、install manifest 或 runtime 记录。当前需从磁盘重新确认：

- 战斗 prefab：`Assets/Prefabs/Enemy/Enemy_VolcanoParasite.prefab`
- 源 prefab：`Assets/_UIAssets/Monsters/Parasites/VolcanoParasite/VolcanoParasite.prefab`
- 源 atlas：`Assets/_UIAssets/Monsters/Parasites/VolcanoParasite/VolcanoParasite.png`

自行检查完整源图、prefab 层级、实际动画控制器/事件、战斗行为与对象池生命周期，再建立 VolcanoParasite 专属解剖方案和路径并集增量基线。不得照搬 Turkey、Troll 或其他角色的造型、层级或动作。

依原执行 prompt 完成：逐方向生成与实看 raw、保留请求/原图/拒绝稿、透明切片和 pivot/layout 审查、仅本角色的安装验证、两轮真实 Unity Play（每轮84项）、按1至2张分批审阅真实 PNG、记录准确视觉审阅范围、UTF-8 note/record、GIF归档及来源/归档hash核对、运行和版本绑定、路径并集审计。完成状态只能为 `completed_pending_user_art_review` 且 `user_approved=false`，除非用户亲自给出美术批准。

Turkey 已完成的事实只作交接上下文：两轮168/0、686 PNG；12个 GIF 每个抽看5点而非全帧审阅；Turkey 增量22路径变化、unexpected=0。其旧 global audit 的291 unexpected和6历史语义失败来自更早全局基线，不要当作新角色基线。Turkey 的 `Assets/StreamingAssets/build_info` 是未修改 ReporterEditor 的 Play 时间戳副作用。

## Unity 与安全

本任务链目标为 `E:/MyTowerGame`、Unity `2022.3.62f3c1`，桥接 `http://127.0.0.1:8088/mcp`，通过 `Remaining_20261024/mcp_call.py` 每次动态列 custom tools/instances、选择现场 MyTowerGame 实例并核对路径和版本。不要用8082或8080。通用根 AGENTS 中的旧 FreedomTower/D盘/8082配置不覆盖本项目的显式路由。断线重连或域重载后重新核验身份。

Turkey 最后状态为 Boot 单场景、Play停止、scene clean、无console error/编译/更新、`scriptCompilationFailed=false`、ready_for_tools=true；同时 Unity 标记 `assets.external_changes_dirty=true`。新线程须检查当前现场并保留真实状态。Turkey 没有 C# 改动；后续若改 C#，按本工程强制 Unity refresh/compile/state/error-log 闭环，编译期间不继续改代码。桌面控制操作前需要明确确认对话框；不得清空日志或强停其他任务。

图片请求只使用已授权的 AIHub 配置及原执行 prompt 规则；密钥只运行时解密，不写入项目。先核对已有 request/result，避免重复付费；不确定请求不得重发，不删安装清单绕保护。认证、余额、配额失败不盲目重试。PossessedWarg 的旧阻断及可能付费状态保持原样。

禁止改关卡/敌人数值表、`Assets/ConfigJson`、`Assets/Gen`、声音、其他角色和共享C#。禁止 Git pull/reset/commit、构建部署、并行任务或破坏性清理。用户此前已授权逐角色自动串行续接，无需逐角色再确认；完成 VolcanoParasite 后依协议总结、更新 prompt/NEXT/progress、释放 Unity，并创建唯一 fresh local 后继。"""
NEXT.write_text(next_text, encoding="utf-8")

print(f"Updated live status in README and prompt; wrote {NEXT}")
