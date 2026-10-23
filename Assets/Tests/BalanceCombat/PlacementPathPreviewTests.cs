using System.Collections.Generic;
using System.Reflection;
using AStar;
using NUnit.Framework;
using UnityEngine;

namespace FTProject.Tests
{
    /// <summary>
    /// 放置防御塔两条规则（2026-10-22）的回归测试。
    ///
    /// 规则①：玩家滑动时算出的路径只是**预览** ——
    ///   不得改写 CurrentPathWorld、不得广播 RefreshPathEvent（怪物因此不会改道）、
    ///   临时置上的墙必须原样还原。
    /// 规则②：预览路径必须**逐点等于**松手落地后的真实路径 ——
    ///   两边是同一张网格、同一套 A*、同一对起终点，唯一差别是"算完墙标记留不留"。
    /// 规则③：会堵死起点→终点的格子必须判为不可建（预览返回 null）。
    /// 另外校验"怪物脚下建塔"的补丁：站/将踏入新墙格的怪能被挑出来改道。
    /// </summary>
    public class PlacementPathPreviewTests
    {
        private object _oldWidth;
        private object _oldHeight;
        private object _oldMap;
        private object _oldStart;
        private object _oldTarget;
        private object _oldCurrent;
        private object _oldPreview;

        [SetUp]
        public void SetUp()
        {
            AStarManager a = AStarManager.Instance;
            _oldWidth = a.MapWidth;
            _oldHeight = a.MapHeight;
            _oldMap = a.Map;
            _oldStart = a.StartPoint;
            _oldTarget = a.TargetPoint;
            _oldCurrent = a.CurrentPathWorld;
            _oldPreview = a.PreviewPathWorld;
        }

        [TearDown]
        public void TearDown()
        {
            AStarManager a = AStarManager.Instance;
            SetProperty(a, "MapWidth", _oldWidth);
            SetProperty(a, "MapHeight", _oldHeight);
            SetProperty(a, "Map", _oldMap);
            SetProperty(a, "StartPoint", _oldStart);
            SetProperty(a, "TargetPoint", _oldTarget);
            SetProperty(a, "CurrentPathWorld", _oldCurrent);
            SetProperty(a, "PreviewPathWorld", _oldPreview);
        }

        [Test]
        public void PreviewDoesNotTouchAppliedPathOrBroadcastRefresh()
        {
            AStarManager a = AStarManager.Instance;
            a.BuildGrid(DoubleRouteMap(), 1f, Vector2.zero);

            int refreshHits = 0;
            System.Action onRefresh = delegate { refreshHits++; };
            EventDispatcher.AddEventListener(EventName.RefreshPathEvent, onRefresh);
            try
            {
                Vector3[] before = a.CurrentPathWorld;
                Vector3[] preview = a.ComputePathWithExtraWall(2, 0);
                a.ShowPreviewPath(preview);

                Assert.That(preview, Is.Not.Null, "双走廊图上 (2,0) 不应堵死");
                Assert.That(refreshHits, Is.EqualTo(0), "预览期间不得广播 RefreshPathEvent（否则怪物会改道）");
                Assert.That(a.CurrentPathWorld, Is.SameAs(before), "预览不得改写已生效路径");
                Assert.That(a.GetPoint(2, 0).IsWall, Is.False, "预览用的临时墙必须还原");
                Assert.That(a.PreviewPathWorld, Is.SameAs(preview), "预览应只挂到预览槽位");
            }
            finally
            {
                EventDispatcher.RemoveEventListener(EventName.RefreshPathEvent, onRefresh);
                a.ClearPreviewPath();
            }
        }

        [Test]
        public void PreviewPathEqualsPathAppliedAfterBuilding()
        {
            AStarManager a = AStarManager.Instance;
            a.BuildGrid(DoubleRouteMap(), 1f, Vector2.zero);

            // 悬停阶段：只推演
            Vector3[] before = a.CurrentPathWorld;
            Vector3[] preview = a.ComputePathWithExtraWall(2, 0);
            Assert.That(preview, Is.Not.Null);

            // 松手落地：与 TowerManager.TryBuildInternal 相同的三步（置墙 → 请求 → 下一帧重算）
            a.SetWall(2, 0, true);
            a.RequestRefresh();
            a.ProcessRefresh();

            Vector3[] applied = a.CurrentPathWorld;
            Assert.That(applied, Is.Not.Null, "落地后必须存在生效路径");
            Assert.That(applied.Length, Is.EqualTo(preview.Length), "预览与实际路径格数不一致");
            for (int i = 0; i < preview.Length; i++)
            {
                Assert.That((applied[i] - preview[i]).sqrMagnitude, Is.LessThan(0.0001f),
                    "预览与实际路径在第 " + i + " 个点上分叉");
            }

            // 双走廊图：封掉左列后路径必须真的改道（而不是原地不动）
            bool rerouted = applied.Length != before.Length;
            if (!rerouted)
            {
                for (int i = 0; i < applied.Length; i++)
                {
                    if ((applied[i] - before[i]).sqrMagnitude > 0.0001f)
                    {
                        rerouted = true;
                        break;
                    }
                }
            }
            Assert.That(rerouted, Is.True, "封掉 (2,0) 后实际路径必须改道");
        }

        [Test]
        public void ExtraWallThatSealsTheOnlyRouteIsRejectedAndRolledBack()
        {
            AStarManager a = AStarManager.Instance;
            a.BuildGrid(SingleRouteMap(), 1f, Vector2.zero);
            Vector3[] before = a.CurrentPathWorld;

            Vector3[] preview = a.ComputePathWithExtraWall(2, 0);

            Assert.That(preview, Is.Null, "堵死唯一通路的格子必须判为不可建");
            Assert.That(a.GetPoint(2, 0).IsWall, Is.False, "判定结束后临时墙必须还原");
            Assert.That(a.CurrentPathWorld, Is.SameAs(before), "判定失败不得改写已生效路径");
        }

        [Test]
        public void RemainingPathTouchesReportsOnlyCellsNotYetPassed()
        {
            GameObject go = new GameObject("PlacementProbeEnemy");
            try
            {
                BaseEnemy enemy = go.AddComponent<BaseEnemy>();
                List<Point> path = new List<Point>(4);
                for (int row = 0; row < 4; row++)
                {
                    path.Add(new Point(0, row));
                }
                enemy.SetPath(path);

                Assert.That(enemy.RemainingPathTouches(3, 0), Is.True, "终点格应在剩余路径里");
                Assert.That(enemy.RemainingPathTouches(1, 0), Is.True);

                SetField(enemy, "_pathIndex", 2);   // 前两格已走过
                Assert.That(enemy.RemainingPathTouches(1, 0), Is.False, "已走过的格子不该再触发改道");
                Assert.That(enemy.RemainingPathTouches(2, 0), Is.True);
            }
            finally
            {
                Object.DestroyImmediate(go);
            }
        }

        // ------------------------------------------------------------------
        // 测试地图
        // ------------------------------------------------------------------

        /// <summary>上下两条通路的 5×5 图：封住左列中段只能改走右侧。</summary>
        private static LevelMapConfig DoubleRouteMap()
        {
            List<string> cells = new List<string>(5)
            {
                "S....",
                ".###.",
                ".###.",
                ".###.",
                "....E",
            };
            return new LevelMapConfig(new cfg.LevelMap(9001, 1, 5, 5, cells, "preview-double-route"));
        }

        /// <summary>只有一条 L 形通路的 3×5 图：中段任一格都是"堵死点"。</summary>
        private static LevelMapConfig SingleRouteMap()
        {
            List<string> cells = new List<string>(5)
            {
                "S##",
                ".##",
                ".##",
                ".##",
                "..E",
            };
            return new LevelMapConfig(new cfg.LevelMap(9002, 1, 3, 5, cells, "preview-single-route"));
        }

        private static void SetProperty(object instance, string name, object value)
        {
            instance.GetType().GetProperty(name, BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic)
                .GetSetMethod(true).Invoke(instance, new[] { value });
        }

        private static void SetField(object instance, string name, object value)
        {
            instance.GetType().GetField(name, BindingFlags.Instance | BindingFlags.NonPublic)
                .SetValue(instance, value);
        }
    }
}
