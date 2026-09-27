using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using UnityEngine;

namespace FTProject
{
    /// <summary>
    /// 管理器单例基类。
    ///
    /// 【访问约定】**只能通过 `XxxManager.Instance` 访问，绝不要 `new`。**
    ///
    /// 为什么要把这条写进注释并加运行时检测：`Instance` 是**懒创建**的，
    /// 一旦某处 `new` 了一个管理器，就会同时存在两份实例 ——
    /// 一份被注册进主循环（被 tick），另一份承载数据（被各处写入）。
    /// 症状极具迷惑性：**没有报错，逻辑就是不生效**。
    /// 本项目真实踩过：`Launcher` 用 `new` 创建管理器，于是
    /// "怪物生成了但不会移动、也不计入存活数、回合空转完成"。
    ///
    /// 所以下面的构造函数会统计创建次数，出现第二份就报 Error。
    /// </summary>
    public class BaseManager<T> : IManagerInterface where T : class, new()
    {
        /// <summary>
        /// 标记"当前正在由 Instance 的 getter 构造单例"。
        /// 唯一的合法构造路径就是 getter，所以构造时这个标记必须是 true。
        /// </summary>
        private static bool s_creatingSingleton;

        /// <summary>单例是否已创建（仅用于日志措辞，不影响逻辑）</summary>
        private static bool s_singletonCreated;

        public BaseManager()
        {
            if (s_creatingSingleton)
            {
                s_singletonCreated = true;
                return;
            }

            // 走到这里说明有人直接 `new` 了一个管理器。
            // 这是**真问题**：随后 .Instance 还会再建一个，两份实例分别承担
            // "被 tick" 与 "承载数据"，逻辑会静默失效且不报错。
            Debug.LogError(string.Format(
                "[Manager] 检测到直接 new {0}()。\n" +
                "  管理器必须统一通过 {0}.Instance 访问 —— 出现两份实例会导致" +
                "「一处写数据、另一处被 tick」的静默故障（例如怪物生成了却不移动）。\n" +
                "  请把 `new {0}()` 改成 `{0}.Instance`。",
                typeof(T).Name));
        }

        public virtual void OnInit()
        {
            //Debug.LogError("##################");
        }

        public virtual void OnDestroy()
        {

        }

        private static T instance;
        public static T Instance
        {
            get
            {
                if (instance == null)
                {
                    s_creatingSingleton = true;
                    try
                    {
                        instance = new T();
                    }
                    finally
                    {
                        s_creatingSingleton = false;
                    }
                }

                return instance;
            }
        }
    }
}
