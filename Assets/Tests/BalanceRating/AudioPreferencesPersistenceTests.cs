using System;
using System.Globalization;
using System.IO;
using System.Text.RegularExpressions;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools;

namespace FTProject.Tests
{
    public sealed class AudioPreferencesPersistenceTests
    {
        private string _directory;
        [SetUp] public void Setup() { _directory = Path.Combine(Path.GetTempPath(), "FT-audio-" + Guid.NewGuid().ToString("N")); Directory.CreateDirectory(_directory); }
        [TearDown] public void Cleanup() { Directory.Delete(_directory, true); }

        [Test]
        public void NormalizationPreservesZeroMuteAndHandlesNonFiniteValues()
        {
            var a = AudioPreferences.Normalize(new AudioPreferences { version = 1, master = 0, music = float.NaN, sfx = float.PositiveInfinity, muted = true });
            Assert.That(a.master, Is.Zero); Assert.That(a.muted, Is.True);
            Assert.That(a.music, Is.EqualTo(.65f)); Assert.That(a.sfx, Is.EqualTo(.8f));
            Assert.That(AudioPreferences.Normalize(null).master, Is.EqualTo(.8f));
            Assert.That(AudioPreferences.Normalize(new AudioPreferences()).master, Is.EqualTo(.8f));
            a = AudioPreferences.Normalize(new AudioPreferences { version = 1, master = -3, music = 4 });
            Assert.That(a.master, Is.Zero); Assert.That(a.music, Is.EqualTo(1));
        }

        [TestCase(false)] [TestCase(true)]
        public void JsonLegacyAndNewSaveRoundTripWithoutChangingProgress(bool legacy)
        {
            string path = Path.Combine(_directory, "freetower_save.json");
            if (legacy) File.WriteAllText(path, "{\"version\":2,\"settings\":{\"language\":\"zh-Hant\",\"volume\":0.2,\"muted\":true},\"levels\":[{\"levelId\":2,\"stars\":4,\"ratingVersionKey\":\"keep\"}],\"snapshot\":{\"valid\":true,\"formatVersion\":2,\"levelId\":2,\"roundCursor\":3}}");
            using (var storage = new JsonSaveStorage(null, _directory))
            {
                storage.Initialize(); var settings = storage.LoadSettings();
                Assert.That(settings.audio.master, Is.EqualTo(.8f)); Assert.That(settings.audio.muted, Is.False);
                settings.audio = new AudioPreferences { version = 1, master = 0, music = .25f, sfx = 0, muted = true };
                storage.SaveSettings(settings); Assert.That(storage.LastError, Is.Null.Or.Empty);
            }
            using (var storage = new JsonSaveStorage(null, _directory))
            {
                storage.Initialize(); var settings = storage.LoadSettings();
                Assert.That(settings.audio.master, Is.Zero); Assert.That(settings.audio.music, Is.EqualTo(.25f)); Assert.That(settings.audio.sfx, Is.Zero); Assert.That(settings.audio.muted, Is.True);
                if (legacy) { Assert.That(settings.language, Is.EqualTo("zh-Hant")); Assert.That(storage.LoadLevels()[0].ratingVersionKey, Is.EqualTo("keep")); Assert.That(storage.LoadSnapshot().roundCursor, Is.EqualTo(3)); }
                storage.SaveSettings(settings); Assert.That(storage.LastError, Is.Null.Or.Empty);
            }
        }

        [Test]
        public void SqliteUsesInvariantValuesAndAtomicRollback()
        {
            SqliteDatabase db; string error;
            Assert.That(SqliteDatabase.TryOpen(Path.Combine(_directory, "audio.db"), out db, out error), Is.True, error);
            var culture = CultureInfo.CurrentCulture;
            try
            {
                CultureInfo.CurrentCulture = CultureInfo.GetCultureInfo("fr-FR");
                using (var storage = new SqliteSaveStorage(db, null))
                {
                    storage.Initialize();
                    var settings = new GameSettings { language = "zh-Hant", audio = new AudioPreferences { version = 1, master = 0, music = .25f, sfx = .5f, muted = true } };
                    storage.SaveSettings(settings); Assert.That(storage.LastError, Is.Null.Or.Empty);
                    Assert.That(db.QueryScalar<string>("SELECT v FROM kv_store WHERE k='settings.audio.music'", ""), Is.EqualTo("0.25"));
                    var read = storage.LoadSettings(); Assert.That(read.audio.master, Is.Zero); Assert.That(read.audio.muted, Is.True);
                    db.Execute("CREATE TRIGGER audio_abort BEFORE INSERT ON kv_store WHEN NEW.k='settings.audio.sfx' BEGIN SELECT RAISE(ABORT,'audio-test-write-failure'); END");
                    settings.language = "en"; settings.audio.master = .9f; settings.audio.muted = false;
                    LogAssert.Expect(LogType.Warning, new Regex(".*写入会话设置失败.*", RegexOptions.Singleline));
                    storage.SaveSettings(settings); Assert.That(storage.LastError, Is.Not.Empty);
                    read = storage.LoadSettings(); Assert.That(read.language, Is.EqualTo("zh-Hant")); Assert.That(read.audio.master, Is.Zero); Assert.That(read.audio.muted, Is.True);
                    db.Execute("DROP TRIGGER audio_abort"); storage.SaveSettings(settings); Assert.That(storage.LastError, Is.Null.Or.Empty);
                    Assert.That(storage.LoadSettings().audio.master, Is.EqualTo(.9f));
                    db.Execute("UPDATE kv_store SET v='NaN' WHERE k='settings.audio.music'");
                    Assert.That(storage.LoadSettings().audio.music, Is.EqualTo(.65f));
                }
            }
            finally { CultureInfo.CurrentCulture = culture; }
        }
    }
}
