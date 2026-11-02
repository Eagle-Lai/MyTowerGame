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
                // 历史候选目录里没有新表的 json：回退到当前已加载的表，否则整批测试直接抛异常。
                // （tblocalization 同理：候选集只关心数值表，本地化沿用当前的。）
                else if ((key == "tblocalization" || key == "tbwavetuning") && LoadedJson.ContainsKey(key)) json[key] = LoadedJson[key];
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
            var rules = new TBLevelRules(JSONNode.Parse(json["tblevelrules"]));
            var localization = new TBLocalization(JSONNode.Parse(json["tblocalization"]));
            var waveTunings = new TBWaveTuning(JSONNode.Parse(json["tbwavetuning"]));
            var global = globals.GetOrDefault(1);
            if (global == null) throw new InvalidDataException("Candidate global config is missing");

            var oldEnemies = EnemyTable; var oldTowers = TowerTable; var oldBullets = BulletTable; var oldGroups = WaveTable; var oldRounds = RoundTable; var oldLevels = LevelTable; var oldMaps = LevelMapTable; var oldGlobals = GlobalTable; var oldRules = RulesTable; var oldLocalization = LocalizationTable; var oldWaveTunings = WaveTuningTable; var oldGlobal = Global; var oldGlobalRow = _globalRow;
            var oldJson = new Dictionary<string, string>(LoadedJson); bool oldLoaded = IsLoaded;
            try
            {
                EnemyTable = enemies; TowerTable = towers; BulletTable = bullets; WaveTable = groups; RoundTable = rounds; LevelTable = levels; LevelMapTable = maps; GlobalTable = globals; RulesTable = rules; LocalizationTable = localization;
                WaveTuningTable = waveTunings;
                BuildLevelIndexes();
                RebuildWaveTuningIndex();
                RulesByLevel.Clear(); foreach (LevelRules lr in rules.DataList) RulesByLevel[lr.Id] = lr;
                _globalRow = global; RebuildGlobalConfig();
                LoadedJson.Clear(); foreach (var pair in json) LoadedJson[pair.Key] = pair.Value;
                IsLoaded = true;
                Debug.Log("[Config] Isolated editor candidate loaded: " + Path.GetFullPath(directory));
                return true;
            }
            catch
            {
                EnemyTable = oldEnemies; TowerTable = oldTowers; BulletTable = oldBullets; WaveTable = oldGroups; RoundTable = oldRounds; LevelTable = oldLevels; LevelMapTable = oldMaps; GlobalTable = oldGlobals; RulesTable = oldRules; LocalizationTable = oldLocalization; _globalRow = oldGlobalRow; BuildLevelIndexes(); Global = oldGlobal;
                WaveTuningTable = oldWaveTunings;
                RebuildWaveTuningIndex();
                LoadedJson.Clear(); foreach (var pair in oldJson) LoadedJson[pair.Key] = pair.Value;
                IsLoaded = oldLoaded;
                throw;
            }
        }
    }
}
#endif
