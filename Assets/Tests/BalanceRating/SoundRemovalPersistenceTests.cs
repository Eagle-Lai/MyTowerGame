using System;
using System.IO;
using System.Linq;
using NUnit.Framework;

namespace FTProject.Tests
{
    public class SoundRemovalPersistenceTests
    {
        private string _directory;

        [SetUp]
        public void SetUp()
        {
            _directory = Path.Combine(Path.GetTempPath(), "FTProject-silent-" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(_directory);
        }

        [TearDown]
        public void TearDown()
        {
            Directory.Delete(_directory, true);
        }

        [Test]
        public void CurrentJsonIgnoresOldSoundFieldsAndPreservesLanguageAndProgress()
        {
            string path = Path.Combine(_directory, "freetower_save.json");
            File.WriteAllText(path, "{\"version\":2,\"settings\":{\"volume\":0.4,\"muted\":true,\"language\":\"zh-Hant\"},\"levels\":[{\"levelId\":1,\"stars\":4,\"clearCount\":7,\"ratingVersionKey\":\"original\"}],\"snapshot\":{\"valid\":true,\"formatVersion\":2,\"levelId\":1,\"roundCursor\":3}}");
            using (var storage = new JsonSaveStorage(null, _directory))
            {
                storage.Initialize();
                Assert.That(storage.LoadSettings().language, Is.EqualTo("zh-Hant"));
                Assert.That(storage.LoadLevels()[0].stars, Is.EqualTo(4));
                Assert.That(storage.LoadSnapshot().roundCursor, Is.EqualTo(3));
                Assert.That(storage.LoadSettings().audio.muted, Is.False);
                storage.SaveSettings(storage.LoadSettings());
                Assert.That(storage.LastError, Is.Null.Or.Empty);
            }
            string json = File.ReadAllText(path);
            Assert.That(json, Does.Not.Contain("\"volume\""));
            using (var storage = new JsonSaveStorage(null, _directory))
            {
                storage.Initialize();
                Assert.That(storage.LoadSettings().language, Is.EqualTo("zh-Hant"));
                Assert.That(storage.LoadLevels()[0].clearCount, Is.EqualTo(7));
                Assert.That(storage.LoadLevels()[0].stars, Is.EqualTo(4));
                Assert.That(storage.LoadSnapshot().valid, Is.True);
            }
        }

        [TestCase(false)]
        [TestCase(true)]
        public void SqliteSettingsWorkForNewAndLegacyDatabases(bool legacy)
        {
            SqliteDatabase db;
            string error;
            Assert.That(SqliteDatabase.TryOpen(Path.Combine(_directory, "test.db"), out db, out error), Is.True, error);
            using (db)
            {
                SaveSchema.Ensure(db);
                db.Execute("INSERT INTO kv_store(k,v,updated_at) VALUES('settings.language','zh-Hant',123)");
                db.Execute("INSERT INTO level_progress(level_id,stars,rating_payload) VALUES(1,'encrypted-score','rating-bytes')");
                db.Execute("INSERT INTO level_snapshot(id,valid,rating_payload) VALUES(1,1,'snapshot-bytes')");
                if (legacy)
                {
                    db.Execute("DROP TABLE game_settings");
                    db.Execute("CREATE TABLE game_settings(id INTEGER PRIMARY KEY CHECK(id=1), volume REAL, muted INTEGER, updated_at INTEGER)");
                    db.Execute("INSERT INTO game_settings VALUES(1,0.4,1,456)");
                    db.Execute("UPDATE meta SET v='3' WHERE k='schema_version'");
                }
                SaveSchema.Ensure(db);
                SaveSchema.Ensure(db);
                Assert.That(db.Query("PRAGMA table_info(game_settings)").Select(r => r.GetString("name")), Is.EquivalentTo(new[] { "id", "updated_at" }));
                Assert.That(db.QueryScalar<int>("SELECT v FROM meta WHERE k='schema_version'", 0), Is.EqualTo(SaveSchema.CurrentVersion));
                Assert.That(db.QueryScalar<string>("SELECT stars FROM level_progress WHERE level_id=1", null), Is.EqualTo("encrypted-score"));
                Assert.That(db.QueryScalar<string>("SELECT rating_payload FROM level_progress WHERE level_id=1", null), Is.EqualTo("rating-bytes"));
                Assert.That(db.QueryScalar<string>("SELECT rating_payload FROM level_snapshot WHERE id=1", null), Is.EqualTo("snapshot-bytes"));
                if (legacy) Assert.That(db.QueryScalar<long>("SELECT updated_at FROM game_settings WHERE id=1", 0), Is.EqualTo(456));
                using (var storage = new SqliteSaveStorage(db, null))
                {
                    storage.Initialize();
                    Assert.That(storage.LoadSettings().language, Is.EqualTo("zh-Hant"));
                    storage.SaveSettings(new GameSettings { language = "en" });
                    Assert.That(storage.LastError, Is.Null.Or.Empty);
                    Assert.That(storage.LoadSettings().language, Is.EqualTo("en"));
                    Assert.That(db.QueryScalar<string>("SELECT rating_payload FROM level_progress WHERE level_id=1", null), Is.EqualTo("rating-bytes"));
                }
            }
        }
    }
}
