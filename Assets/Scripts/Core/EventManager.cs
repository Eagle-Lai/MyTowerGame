using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace FTProject
{
    public class EventManager : BaseManager<EnemyManager>
    {

        public override void OnInit()
        {
            base.OnInit();
            
        }

        private Dictionary<string, Delegate> actionDictionary = new Dictionary<string, Delegate>();
        public void TriggerEvent(string name)
        {
            if (actionDictionary.TryGetValue(name, out Delegate action))
            {
                //action();
            }
        }

        public void AddListener(string name, Action action)
        {
            actionDictionary[name] = (Delegate)Delegate.Combine(actionDictionary[name], action);
        }

        public void AddListener<T>(string name, Action<T> action)
        {
            actionDictionary[name] = (Action<T>)Delegate.Combine((Action<T>)actionDictionary[name], action);
        }
        

        public void RemoveListener(string name, Action action = null)
        {
            if(action != null)
            {
                this.actionDictionary[name] = (Action)Delegate.Remove((Action)this.actionDictionary[name], action);
            }
            else
            {
                RemoveEventListener(name);
            }
        }
        public void RemoveListener<T>(string name, Action<T> action = null)
        {
            if (action != null)
            {
                this.actionDictionary[name] = (Action<T>)Delegate.Remove((Action<T>)this.actionDictionary[name], action);
            }
            else
            {
                RemoveEventListener(name);
            }
        }

        public void RemoveEventListener(string name)
        {
            if (actionDictionary.ContainsKey(name))
            {
                actionDictionary.Remove(name);
            }
        }

        public override void OnDestroy()
        {
            base.OnDestroy();
        }


    }
}