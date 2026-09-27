using System;
using System.Collections.Generic;
using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 通用对象池。
    ///
    /// 设计要点：
    ///   1. 用「生产工厂 + 归还清理」委托把池与具体业务解耦
    ///   2. 归还时执行 reset 委托，解决"池化对象带着上次状态复用"这一经典 Bug
    ///   3. 不依赖 GameObject.SetActive 的实现细节，隐藏方式由业务决定
    ///
    /// 用法：
    ///   var pool = new ObjectPool&lt;BaseEnemy&gt;(
    ///       create: () =&gt; { ... return enemy; },
    ///       reset:  e  =&gt; e.OnRecycle(),   // 必须清空目标/计时/位置等状态
    ///       maxSize: 64);
    ///   var e = pool.Get();
    ///   pool.Release(e);
    /// </summary>
    public class ObjectPool<T> where T : class
    {
        private readonly Func<T> _create;
        private readonly Action<T> _reset;
        private readonly int _maxSize;
        private readonly Stack<T> _idle;

        /// <summary>池内空闲数量</summary>
        public int IdleCount { get { return _idle.Count; } }

        /// <summary>历史创建总数（含已销毁，用于诊断）</summary>
        public int CreatedTotal { get; private set; }

        public ObjectPool(Func<T> create, Action<T> reset = null, int maxSize = 128, int prewarm = 0)
        {
            if (create == null)
            {
                throw new ArgumentNullException("create");
            }
            _create = create;
            _reset = reset;
            _maxSize = maxSize > 0 ? maxSize : 128;
            _idle = new Stack<T>(64);

            for (int i = 0; i < prewarm; i++)
            {
                T item = _create();
                CreatedTotal++;
                if (item != null)
                {
                    _idle.Push(item);
                }
            }
        }

        /// <summary>取一个对象；池空则新建</summary>
        public T Get()
        {
            while (_idle.Count > 0)
            {
                T item = _idle.Pop();
                if (item != null)
                {
                    return item;
                }
            }
            CreatedTotal++;
            return _create();
        }

        /// <summary>归还一个对象；超出上限则丢弃（由调用方销毁或交给 GC）</summary>
        public void Release(T item)
        {
            if (item == null)
            {
                return;
            }
            if (_reset != null)
            {
                _reset(item);
            }
            if (_idle.Count < _maxSize)
            {
                _idle.Push(item);
            }
        }

        /// <summary>清空池（切关卡时调用）；onDiscard 用于销毁被丢弃的对象</summary>
        public void Clear(Action<T> onDiscard = null)
        {
            while (_idle.Count > 0)
            {
                T item = _idle.Pop();
                if (item != null && onDiscard != null)
                {
                    onDiscard(item);
                }
            }
        }

        public string DumpDebugInfo()
        {
            return string.Format("ObjectPool<{0}>: idle={1}, created={2}, max={3}",
                typeof(T).Name, _idle.Count, CreatedTotal, _maxSize);
        }
    }
}
