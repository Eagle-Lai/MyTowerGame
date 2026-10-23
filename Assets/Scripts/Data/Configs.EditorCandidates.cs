#if UNITY_EDITOR
using System;
using System.Collections.Generic;
using System.IO;
using cfg;
using SimpleJSON;
using UnityEngine;

namespace FTProject
{
    public static partial class Configs
    {
        /// <summary>Load a fully resolved candidate only in an explicitly isolated editor test session.</summary>
        public static bool LoadTestCandidate(string directory)
        {
            if (!SaveManager.IsTestStorage) throw new InvalidOperationException("An isolated balance-test save context is required");
            var flow = GameFlowManager.Instance;
            if (flow != null && (flow.State == GameFlowState.RoundRunning || flow.State == GameFlowState.Preparing || flow.State == GameFlowState.RoundComplete || flow.State == GameFlowState.Loading)) throw new InvalidOperationException("Teardown the active level before replacing candidate tables");
            var json = new Dictionary<string, string>();
            foreach (string key in ConfigKeys)
            {
                string path = Path.Combine(directory, key + ".json");
                if (File.Exists(path)) json[key] = File.ReadAllText(path).TrimStart('\uFEFF');
                else if (key == "tblocalization" && LoadedJson.ContainsKey(key)) json[key] = LoadedJson[key];
                else throw new FileNotFoundException("Candidate table is missing", path);
            }
            // Construction happens before touching any live table.
            var enemies = new TBEnemyData(JSONNode.Parse(json["tbenemydata"]));
            var towers = new TBTowerInfo(JSONNode.Parse(json["tbtowerinfo"]));
            var bullets = new TBBulletData(JSONNode.Parse(json["tbbulletdata"]));
            var groups = new TBEnemyList(JSONNode.Parse(json["tbenemylist"]));
            var rounds = new TBRoundData(JSONNode.Parse(json["tbrounddata"]));
            var levels = new TBSceneInfo(JSONNode.Parse(json["tbsceneinfo"]));
            var maps = new TBLevelMap(JSONNode.Parse(json["tblevelmap"]));
            var globals = new TBGlobal(JSONNode.Parse(json["tbglobal"]));
            var localization = new TBLocalization(JSONNode.Parse(json["tblocalization"]));
            JSONNode ratingJson = JSONNode.Parse(json["tblevelrating"]);
            foreach (JSONNode node in ratingJson.Children) node["runtimeContentHash"] = "";
            var rating = new TBLevelRating(ratingJson);
            string hash = CalculateRuntimeContentHash(json, rating.DataList);
            foreach (JSONNode node in ratingJson.Children) node["runtimeContentHash"] = hash;
            rating = new TBLevelRating(ratingJson);
            var global = globals.GetOrDefault(1);
            if (global == null) throw new InvalidDataException("Candidate global config is missing");

            var oldEnemies = EnemyTable; var oldTowers = TowerTable; var oldBullets = BulletTable; var oldGroups = WaveTable; var oldRounds = RoundTable; var oldLevels = LevelTable; var oldMaps = LevelMapTable; var oldGlobals = GlobalTable; var oldLocalization = LocalizationTable; var oldRating = RatingTable; var oldGlobal = Global;
            var oldJson = new Dictionary<string, string>(LoadedJson); bool oldVerified = RatingContentVerified; bool oldLoaded = IsLoaded;
            try
            {
                EnemyTable = enemies; TowerTable = towers; BulletTable = bullets; WaveTable = groups; RoundTable = rounds; LevelTable = levels; LevelMapTable = maps; GlobalTable = globals; LocalizationTable = localization; RatingTable = rating; Global = new GlobalConfig(global);
                LoadedJson.Clear(); foreach (var pair in json) LoadedJson[pair.Key] = pair.Value;
                if (!VerifyRatingContent()) throw new InvalidDataException("Candidate rating/content self-check failed");
                RatingContentVerified = true; IsLoaded = true;
                Debug.Log("[Rating] Isolated editor candidate loaded: " + Path.GetFullPath(directory) + " hash=" + hash);
                return true;
            }
            catch
            {
                EnemyTable = oldEnemies; TowerTable = oldTowers; BulletTable = oldBullets; WaveTable = oldGroups; RoundTable = oldRounds; LevelTable = oldLevels; LevelMapTable = oldMaps; GlobalTable = oldGlobals; LocalizationTable = oldLocalization; RatingTable = oldRating; Global = oldGlobal;
                LoadedJson.Clear(); foreach (var pair in oldJson) LoadedJson[pair.Key] = pair.Value;
                RatingContentVerified = oldVerified; IsLoaded = oldLoaded;
                throw;
            }
        }
    }
}
#endif
