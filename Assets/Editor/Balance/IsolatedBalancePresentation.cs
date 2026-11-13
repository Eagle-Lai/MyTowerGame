using System;
using System.Collections.Generic;
using System.Reflection;
using UnityEngine;

namespace FTProject.EditorTools
{
    // Suppress presentation only inside an isolated, non-rendered numerical replay.
    // HP, speed, damage, cooldowns, targets, paths, transactions and game clocks are untouched.
    public static class IsolatedBalancePresentation
    {
        private const BindingFlags PrivateInstance = BindingFlags.Instance | BindingFlags.NonPublic;
        private static readonly FieldInfo EnemyList = typeof(CombatSystem).GetField("_enemies",PrivateInstance);
        private static readonly HashSet<long> Seen = new HashSet<long>();
        private static readonly HashSet<int> Towers = new HashSet<int>();
        private static bool Initialized;
        private static string RunId;
        private static void Set(object target,string name,object value)
        {
            FieldInfo field=null;
            for(var type=target.GetType();type!=null && field==null;type=type.BaseType)
                field=type.GetField(name,PrivateInstance);
            if(field==null) throw new MissingFieldException(target.GetType().Name,name);
            field.SetValue(target,value);
        }
        public static void Prepare()
        {
            if(!SaveManager.IsTestStorage) throw new InvalidOperationException("Presentation suppression requires isolated test storage.");
            string runId=GameFlowManager.Instance.RunMetrics.runId;
            if(!Initialized || RunId!=runId)
            {
                RunId=runId;
                Initialized=true; Seen.Clear(); Towers.Clear();
                foreach(string name in new[]{"_muzzleNormal","_muzzlePower","_blast"})
                    typeof(TowerFireFx).GetField(name,BindingFlags.NonPublic|BindingFlags.Static).SetValue(null,new Sprite[0]);
                typeof(AudioRuntime).GetProperty("Current").SetValue(null,null,null);
                foreach(var camera in Camera.allCameras) camera.enabled=false;
                foreach(var canvas in UnityEngine.Object.FindObjectsOfType<Canvas>()) canvas.enabled=false;
            }
            var global=Configs.Global;
            if(global!=null)
            {
                var rule=global.GetType().GetField("_r",PrivateInstance).GetValue(global);
                var row=global.GetType().GetField("_g",PrivateInstance).GetValue(global);
                if(rule!=null)rule.GetType().GetProperty("ShowDamageText").SetValue(rule,0,null);
                if(row!=null)row.GetType().GetProperty("ShowDebugLog").SetValue(row,0,null);
            }
            if(CombatSystem.Instance==null) return;
            var enemies=EnemyList.GetValue(CombatSystem.Instance) as List<BaseEnemy>;
            foreach(var e in enemies)
            {
                if(e==null || !e.IsAlive || !Seen.Add(e.EvidenceSpawnSerial)) continue;
                Set(e,"_bodyRenderers",new SpriteRenderer[0]);Set(e,"_anim",null);
                Set(e,"_directionalVisual",null);Set(e,"_hpBarReady",false);
                foreach(var renderer in e.GetComponentsInChildren<Renderer>(true)) renderer.enabled=false;
            }
            foreach(var t in TowerManager.Instance.Towers)
            {
                if(t==null || !Towers.Add(t.GetInstanceID()))continue;
                Set(t,"_barrel",null);Set(t,"_muzzleFx",null);Set(t,"_auraView",null);
                foreach(var renderer in t.GetComponentsInChildren<Renderer>(true)) renderer.enabled=false;
            }
        }
    }
}
