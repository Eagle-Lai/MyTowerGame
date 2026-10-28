using NUnit.Framework;

namespace FTProject.Tests
{
    public class TowerCadenceTests
    {
        [TestCase(30, 1)]
        [TestCase(30, 3)]
        [TestCase(60, 1)]
        [TestCase(60, 3)]
        [TestCase(144, 3)]
        public void ConfiguredCooldownsKeepTheirRateAcrossFrameRatesAndSpeeds(int fps, int speed)
        {
            // 普通塔三档旧实现都会在30帧三倍速下被量化为0.5秒。
            foreach (float cooldown in new[] { 0.45f, 0.43f, 0.41f, 0.25f, 0.24f, 0.23f })
            {
                float remainder = 0f;
                int shots = 0;
                int frames = fps * 30;
                for (int i = 0; i < frames; i++)
                    shots += BaseTower.ConsumeCadence(ref remainder, (float)speed / fps, cooldown);

                double simulatedSeconds = 30d * speed;
                int expected = (int)System.Math.Floor((simulatedSeconds + 0.00001d) / cooldown);
                Assert.That(shots, Is.EqualTo(expected), "CD=" + cooldown);
                Assert.That(remainder, Is.GreaterThanOrEqualTo(0f).And.LessThan(cooldown));
                Assert.That(shots * (double)cooldown + remainder,
                    Is.EqualTo(simulatedSeconds).Within(0.0001d));
            }
        }

        [Test]
        public void LongFrameConsumesEveryElapsedCooldownAndCarriesRemainder()
        {
            float timer = 0.2f;
            Assert.That(BaseTower.ConsumeCadence(ref timer, 1f, 0.45f), Is.EqualTo(2));
            Assert.That(timer, Is.EqualTo(0.3f).Within(0.000001f));
            Assert.That(BaseTower.ConsumeCadence(ref timer, 0.15f, 0.45f), Is.EqualTo(1));
            Assert.That(timer, Is.EqualTo(0f).Within(0.000001f));
        }

        [Test]
        public void PauseDoesNotAdvanceOrConsumeRestoredTimer()
        {
            float timer = 0.6f;
            Assert.That(BaseTower.ConsumeCadence(ref timer, 0f, 0.45f), Is.Zero);
            Assert.That(timer, Is.EqualTo(0.6f));
        }
    }
}
