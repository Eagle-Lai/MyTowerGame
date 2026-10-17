# 离线策略与对照证据

`normal`、`power`、`mixed` 为完整 480 条基线矩阵；`reference` 为八档各 20 关的 160 条合法零漏怪且战斗时间不超过 Par 的预测参考；`lower-star` 为 160 条完成 20 波且唯一 C# 评分为有效 1—4 星的通关对照；`mistake` 为 160 条明确失误的失败对照，共 960 条。每次操作按实时余额消费，不预支奖励。星数由 Unity 的唯一 C# LevelRatingEvaluator 回填，离线结果不认证真实五星。

`reference_index_160.json` 可直接定位每关的完整操作轨迹。初版高档结果已被显式后期 EHP 梯度校准替代，摘要见 `initial_high_profiles_superseded.json`；真实实测覆盖由 Reports 的 hash 匹配索引另列。

`matrix_all_960.json` 为完整聚合索引，`matrix_lower_160.json` 与 `lower_star_index_160.json` 专列有效低星对照。低星分布为 1 星 71、2 星 42、3 星 14、4 星 33；每档 20 关均覆盖。`lower_star_economy_audit.json` 核对 3200 波、5046 笔购买，逐波收支与实际塔价一致、最低余额为 0。`matrix_all_800.json` 保留原 480+160+160 范围，便于核对早期 C# 批评分；后续完整入口使用 960 索引。
