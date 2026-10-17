using System.Collections.Generic;
using System.Reflection;
using NUnit.Framework;
using UnityEngine;

namespace FTProject.Tests
{
    /// <summary>直接调用真实命中和状态逻辑，避免用镜像算法替代战斗验证。</summary>
    public class CombatTargetingAndSlowTests
    {
        private readonly List<GameObject> _objects = new List<GameObject>();
        private EnemyGrid _originalGrid;

        [SetUp]
        public void SetUp()
        {
            _originalGrid = CombatSystem.Instance.Grid;
            SetProperty(CombatSystem.Instance, "Grid", new EnemyGrid(2f, 256));
        }

        [TearDown]
        public void TearDown()
        {
            CombatSystem.Instance.Grid.Clear();
            SetProperty(CombatSystem.Instance, "Grid", _originalGrid);
            foreach (GameObject go in _objects) Object.DestroyImmediate(go);
            _objects.Clear();
        }

        [Test]
        public void GroundExplosionCannotDamageNearbyFlyingEnemy()
        {
            BaseEnemy ground = Enemy(false, new Vector2(0f, 0f));
            BaseEnemy flying = Enemy(true, new Vector2(0.1f, 0f));
            Explode(Tower(false), Vector2.zero);
            Assert.That(ground.CurrentHp, Is.EqualTo(99.5f).Within(0.0001f));
            Assert.That(flying.CurrentHp, Is.EqualTo(100f));
        }

        [Test]
        public void GroundExplosionAgainstPureAirHitsNothing()
        {
            BaseEnemy flying = Enemy(true, Vector2.zero);
            Explode(Tower(false), Vector2.zero);
            Assert.That(flying.CurrentHp, Is.EqualTo(100f));
        }

        [Test]
        public void AirCapableExplosionRespectsCapabilityAndRadius()
        {
            BaseEnemy flying = Enemy(true, Vector2.zero);
            BaseEnemy outside = Enemy(false, new Vector2(1.21f, 0f));
            Explode(Tower(true), Vector2.zero);
            Assert.That(flying.CurrentHp, Is.EqualTo(99.5f).Within(0.0001f));
            Assert.That(outside.CurrentHp, Is.EqualTo(100f));
        }

        [Test]
        public void WeakAuraCannotExtendStrongEffectAndReappliesOnNextPulse()
        {
            BaseEnemy enemy = Enemy(false, Vector2.zero);
            enemy.ApplySlow(0.45f, 0.7f);
            TickEffects(enemy, 0.4f);
            enemy.ApplySlow(0.25f, 0.7f);
            TickEffects(enemy, 0.301f);
            Assert.That(Speed(enemy), Is.EqualTo(1f).Within(0.0001f), "弱光环不能续高级减速");
            // 下次400ms脉冲前的空档不超过一个刷新周期。
            TickEffects(enemy, 0.099f);
            enemy.ApplySlow(0.25f, 0.7f);
            Assert.That(Speed(enemy), Is.EqualTo(0.75f).Within(0.0001f));
            TickEffects(enemy, 0.701f);
            Assert.That(Speed(enemy), Is.EqualTo(1f).Within(0.0001f), "完全离场必须恢复配置速度");
        }

        [Test]
        public void EqualAuraRefreshesAndStrongerEffectHasItsOwnDuration()
        {
            BaseEnemy enemy = Enemy(false, Vector2.zero);
            enemy.ApplySlow(0.25f, 5f);
            enemy.ApplySlow(0.45f, 0.7f);
            TickEffects(enemy, 0.4f);
            enemy.ApplySlow(0.45f, 0.7f);
            TickEffects(enemy, 0.4f);
            Assert.That(Speed(enemy), Is.EqualTo(0.55f).Within(0.0001f));
            TickEffects(enemy, 0.301f);
            Assert.That(Speed(enemy), Is.EqualTo(1f).Within(0.0001f), "强效果不得继承弱效果的5秒计时");
        }

        [Test]
        public void RecycledEnemyDoesNotRetainSlowOrDot()
        {
            BaseEnemy enemy = Enemy(false, Vector2.zero);
            enemy.ApplySlow(0.45f, 3f);
            enemy.ApplyDot(4f, 3f);
            enemy.OnRecycle();
            enemy.Init(EnemyConfig(false), null);
            TickEffects(enemy, 0.5f);
            Assert.That(Speed(enemy), Is.EqualTo(1f).Within(0.0001f));
            Assert.That(enemy.CurrentHp, Is.EqualTo(100f));
            Assert.That(enemy.IsAlive, Is.True);
        }

        [TestCase(-1, "☆☆☆☆☆")]
        [TestCase(0, "☆☆☆☆☆")]
        [TestCase(3, "★★★☆☆")]
        [TestCase(4, "★★★★☆")]
        [TestCase(5, "★★★★★")]
        [TestCase(8, "★★★★★")]
        public void EveryAchievementUsesFiveSlots(int stars, string expected)
        {
            Assert.That(SelectView.Stars(stars), Is.EqualTo(expected));
        }

        private BaseEnemy Enemy(bool flying, Vector2 position)
        {
            GameObject go = new GameObject("RatingCombatTestEnemy");
            _objects.Add(go);
            go.transform.position = position;
            BaseEnemy enemy = go.AddComponent<BaseEnemy>();
            enemy.Init(EnemyConfig(flying), null);
            CombatSystem.Instance.Grid.Update(enemy, position);
            return enemy;
        }

        private static EnemyConfig EnemyConfig(bool flying)
        {
            return new EnemyConfig(new cfg.EnemyData(100000, 1f, 100f, "Test", flying ? 4 : 1,
                0, "Test", 0f, 1, 1, 1f, 0.2f, flying ? 1 : 0, string.Empty, string.Empty));
        }

        private BaseTower Tower(bool canAttackAir)
        {
            GameObject go = new GameObject("RatingCombatTestTower");
            _objects.Add(go);
            BaseTower tower = go.AddComponent<BaseTower>();
            SetProperty(tower, "Config", new TowerConfig(new cfg.TowerInfo(4, 2, "Test", "Test", 1,
                3, 14, 1000f, 45, 2, 0, 100, 360f, 0, 31, 3, 0f, string.Empty, canAttackAir ? 1 : 0)));
            return tower;
        }

        private static void Explode(BaseTower tower, Vector2 center)
        {
            BulletConfig bullet = new BulletConfig(new cfg.BulletData(2, "Test", "Test", 1f,
                0.2f, 3000, 1.2f, 0, 0f, 1f, string.Empty));
            typeof(BaseTower).GetMethod("DetonateAt", BindingFlags.Instance | BindingFlags.NonPublic)
                .Invoke(tower, new object[] { center, 1.2f, 0.5f, bullet });
        }

        private static void TickEffects(BaseEnemy enemy, float dt)
        {
            typeof(BaseEnemy).GetMethod("TickEffects", BindingFlags.Instance | BindingFlags.NonPublic)
                .Invoke(enemy, new object[] { dt });
        }

        private static float Speed(BaseEnemy enemy)
        {
            return (float)typeof(BaseEnemy).GetField("_speed", BindingFlags.Instance | BindingFlags.NonPublic).GetValue(enemy);
        }

        private static void SetProperty(object instance, string name, object value)
        {
            instance.GetType().GetProperty(name, BindingFlags.Instance | BindingFlags.Public)
                .GetSetMethod(true).Invoke(instance, new[] { value });
        }
    }
}
