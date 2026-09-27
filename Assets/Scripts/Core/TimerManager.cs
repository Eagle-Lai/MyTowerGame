using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
namespace FTProject
{
    public class TimerManager : BaseManager<TimerManager>
    {
        class TimerItem
        {
            public int id;
            public float Interval
            {
                get { return _interval; }
                set { _interval = value; }
            }
            public int loopTimes;
            public float _interval;

            public float TempInterval;

            public UnityEngine.Object callbackObject;
            public object[] args;

            public Action callback;
            public Action<UnityEngine.Object> callbackObjectEvent;
            public Action<UnityEngine.Object, object[]> callbackObjAndArgs;
            public bool isNotLimtied;
            public bool isStop;
            public bool isFree;


            public TimerItem()
            {

            }
            public TimerItem(int id, float interval, int loopTimes, Action callback = null, Action<UnityEngine.Object> actionObject = null, Action<UnityEngine.Object, object[]> action = null, UnityEngine.Object obj = null, object[] args = null)
            {
                this.id = id;
                this._interval = interval;
                this.TempInterval = interval;
                this.loopTimes = loopTimes;
                this.callback = callback;
                this.callbackObjectEvent = actionObject;
                this.callbackObjAndArgs = action;
                this.callbackObject = obj;
                this.args = args;
                isStop = false;
                isNotLimtied = loopTimes == -1;
                isFree = true;
            }
            public void Reset()
            {
                this.loopTimes--;
                this._interval = TempInterval;
                isFree = loopTimes == 0;
            }
        }

        private Dictionary<int, TimerItem> _timerDicti;
        public int actionIndex;

        public float checkTimerInterval = 3f;

        public TimerManager()
        {
            _timerDicti = new Dictionary<int, TimerItem>();
            actionIndex = 0;
        }

        /// <summary>
        /// 
        /// </summary>
        /// <param name="interval">时间间隔</param>
        /// <param name="loopTimes">执行次数</param>
        /// <param name="callback">回调函数</param>
        /// /// /// <param name="isRun">是否立即执行</param>
        /// <param name="actionObject"></param>
        /// <param name="action"></param>
        /// <param name="obj"></param>
        /// <param name="args"></param>
        /// <returns></returns>
        public int AddTimer(float interval, int loopTimes, Action callback, bool isRun = false, Action<UnityEngine.Object> actionObject = null, Action<UnityEngine.Object, object[]> action = null, UnityEngine.Object obj = null, object[] args = null)
        {
            TimerItem item = GetTimerItem(interval, loopTimes, callback, actionObject, action, obj, args);
            if (isRun)
            {
                item.loopTimes--;
                if (callback != null)
                {
                    callback();
                }
                if (actionObject != null)
                {
                    actionObject(item.callbackObject);
                }
                if (action != null)
                {
                    action(item.callbackObject, item.args);
                }
            }
            return item.id;
        }


        public void Update(float intervalTime)
        {
            //CheckTimerItem();
            if (_timerDicti.Count > 0)
            {
                for (int i = 0; i < _timerDicti.Count; i++)
                {
                    KeyValuePair<int, TimerItem> item = _timerDicti.ElementAt(i);

                    if (!item.Value.isStop)
                    {
                        if (item.Value.isNotLimtied || item.Value.loopTimes > 0)
                        {
                            item.Value.Interval -= intervalTime;
                            if (item.Value.Interval <= 0)
                            {
                                if (item.Value.callback != null)
                                {
                                    item.Value.callback();
                                }
                                if (item.Value.callbackObjectEvent != null && item.Value.callbackObject != null)
                                {
                                    item.Value.callbackObjectEvent(item.Value.callbackObject);
                                }
                                if (item.Value.callbackObjAndArgs != null && item.Value.callbackObject != null && item.Value.args != null)
                                {
                                    item.Value.callbackObjAndArgs(item.Value.callbackObject, item.Value.args);
                                }
                                item.Value.Reset();
                            }
                        }
                    }
                }
            }
        }
        public void StopTimerById(int id, bool isStop = true)
        {
            if (_timerDicti.ContainsKey(id))
            {
                _timerDicti[id].isStop = isStop;
            }
        }

        public void RemoveTimerById(int id)
        {
            if (_timerDicti.ContainsKey(id))
            {
                _timerDicti[id].isFree = true;
                _timerDicti[id].isStop = true;
            }
        }

        private TimerItem GetTimerItem(float interval, int loopTimes, Action callback, Action<UnityEngine.Object> actionObject, Action<UnityEngine.Object, object[]> action = null, UnityEngine.Object obj = null, object[] args = null)
        {
            if (_timerDicti.Count > 0)
            {
                for (int i = 1; i < _timerDicti.Count; i++)
                {
                    KeyValuePair<int, TimerItem> item = _timerDicti.ElementAt(i);
                    if (item.Value.isFree)
                    {
                        item.Value.TempInterval = interval;
                        item.Value.Interval = interval;
                        item.Value.loopTimes = loopTimes;
                        item.Value.callback = callback;
                        item.Value.callbackObjectEvent = actionObject;
                        item.Value.callbackObjAndArgs = action;
                        item.Value.args = args;
                        item.Value.isFree = false;
                        item.Value.isStop = false;
                        return item.Value;
                    }
                }
            }
            actionIndex++;
            TimerItem item1 = new TimerItem(actionIndex, interval, loopTimes, callback, actionObject, action, obj, args);
            item1.isFree = false;
            item1.isStop = false; ;
            _timerDicti.Add(actionIndex, item1);
            return item1;
        }

        public override void OnDestroy()
        {
            base.OnDestroy();
            _timerDicti.Clear();
        }

        public void CheckTimerItem()
        {
            if(_timerDicti.Count > 5)
            {
                for (int i = _timerDicti.Count - 1; i > 0; i++)
                {
                    KeyValuePair<int, TimerItem> item = _timerDicti.ElementAt(i);
                    if (item.Value.isFree)
                    {
                        _timerDicti.Remove(item.Key);
                        if (_timerDicti.Count <= 5)
                        {
                            return;
                        }
                    }
                }
            }
        }

        public void ClearAll()
        {
            _timerDicti.Clear();
        }
    }
}