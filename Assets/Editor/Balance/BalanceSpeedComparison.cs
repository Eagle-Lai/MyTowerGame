using System.Collections.Generic;
using System.Linq;
using SimpleJSON;
using UnityEngine;

namespace FTProject.EditorTools
{
    /// <summary>
    /// 倍速一致性比对（2026-10-30 由 BalanceCheckpointVerifier 收缩而来）。
    ///
    /// 【为什么只剩这一步】局内的塔阵 / 金币 / 生命不再落盘，"退出后继续"与"失败续局"
    /// 整条链路已经下线（见 SaveManager / GameFlowManager 的 2026-10-30 说明）。
    /// 原先的 boundary_resume / half_wave_rollback / terminal_duplicate 场景随之删除 ——
    /// 它们验证的是已被移除的续玩行为，留着只会变成永远跑不到的死代码。
    ///
    /// 【还留下什么】同一串合法操作在 ×1 / ×2 / ×3 下重放，最终评级证据（星级、判定、
    /// 全部原始时间与波次统计）、结束金币、终局塔阵必须逐字段一致。
    /// 这是"倍速只影响观看、不影响结算"的唯一自动化证据。
    /// </summary>
    public static class BalanceSpeedComparison
    {
        /// <summary>
        /// Compare completed run entries. The caller must use the same operationsPath and
        /// normalized simulation step (baseStep / speed) at 1x, 2x and 3x.
        /// runId and wall time intentionally differ; all gameplay evidence must agree.
        /// </summary>
        public static JSONNode Compare(IEnumerable<JSONNode> results)
        {
            var array = results.ToList();
            var report = new JSONObject();
            report["method"] = "Same operation replay and fixed simulation step; unscaled input step is divided by speed";
            report["comparisons"] = new JSONArray();

            var groups = array.Where(r => !string.IsNullOrEmpty(r["speedComparisonGroup"].Value))
                              .GroupBy(r => r["speedComparisonGroup"].Value);
            foreach (var group in groups)
            {
                var runs = group.OrderBy(r => r["speed"].AsFloat).ToList();
                var entry = new JSONObject(); entry["group"] = group.Key;
                bool complete = runs.Count == 3 && runs.Select(r => r["speed"].AsInt).SequenceEqual(new[] { 1, 2, 3 });
                entry["complete"] = complete;
                bool same = complete;
                if (complete)
                {
                    string first = ComparisonSignature(runs[0]);
                    foreach (var run in runs.Skip(1)) same &= ComparisonSignature(run) == first;
                }
                entry["passed"] = same;
                entry["comparison"] = "Stars, validity, every raw clock, wave evidence, kills/leaks, final gold and final tower layout; runId normalized";
                report["comparisons"].Add(entry);
            }

            bool anyGroup = report["comparisons"].Count > 0;
            report["passed"] = anyGroup && report["comparisons"].Children.All(n => n["passed"].AsBool);
            return report;
        }

        private static string ComparisonSignature(JSONNode entry)
        {
            LevelRatingResult result = JsonUtility.FromJson<LevelRatingResult>(entry.ToString());
            if (result == null || result.metrics == null) return "missing evidence";
            result.metrics.runId = "same replay";
            // End times and economy in every wave remain in the comparison.
            return result.stars + "|" + result.valid + "|" + JsonUtility.ToJson(result.metrics) + "|"
                + entry["finalGold"].Value + "|" + entry["finalTowerSignature"].Value;
        }
    }
}
