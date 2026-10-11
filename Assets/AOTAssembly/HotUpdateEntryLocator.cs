using System;
using System.Collections.Generic;
using System.Reflection;

namespace FTProject.AOT
{
    /// <summary>
    /// 在已加载程序集里查找 <see cref="IHotUpdateEntry"/> 的实现类并实例化。
    ///
    /// ==================================================================
    /// 【它解决的问题】
    ///   AOT 侧**不能 `new` 热更类型**（编译期符号依赖会让 IL2CPP 打包失败），
    ///   所以"接口"本身解决不了"谁来实例化"的问题 —— 这一步必须靠反射。
    ///
    ///   于是本类是**唯一**保留反射的地方，且职责收窄到一件事：
    ///   「找到实现者，并把它变成 IHotUpdateEntry」。
    ///   一旦拿到接口引用，后续所有调用都是**强类型**的（`entry.Start()`），
    ///   不再有字符串、不再有 MethodInfo。
    ///
    /// 【为什么用 `typeof(IHotUpdateEntry)` 而不是字符串】
    ///   `typeof` 走的是编译期类型系统 → 接口改名/挪程序集会**编译报错**（好）。
    ///   而旧方案用 `"FTProject.HotUpdateEntry"` 字符串 → 改名只在运行时炸（坏）。
    ///   这就是本次改造想要的核心收益。
    ///
    /// 【为什么不用 `Assembly.GetTypes()` 全扫】
    ///   `GetTypes()` 会把每个程序集的所有类型都反射构造一遍（含泛型构造、依赖解析），
    ///   在 IL2CPP 下开销明显，且某些程序集（如 Unity 内置）会抛 ReflectionTypeLoadException。
    ///   所以这里用 `GetType(name, false)` 只探**已知候选名**（快、稳）。
    ///   ⚠️ 候选名是**唯一**剩下的字符串契约（见 EntryTypeNames），
    ///      改热更侧类名必须同步这里。但它比旧方案健壮：
    ///      名字写错时会走 `CreateEntry` 的兜底扫描并给出明确错误。
    ///
    /// 【编辑器特例】
    ///   编辑器下热更 dll 已在 AppDomain，`GetType` 天然能找到。
    ///   真机上热更 dll 由 `HotUpdateAssembler` 先 `Assembly.Load` 进来，同样能找到。
    ///   两条路径对本类透明 —— 无需分支。
    /// ==================================================================
    /// </summary>
    public static class HotUpdateEntryLocator
    {
        /// <summary>
        /// 热更侧入口实现类的**候选全名**（按优先级）。
        ///
        /// ⚠️ 唯一剩下的字符串契约：热更侧改了类名，这里要同步。
        ///    加到这里的是"**预期**的名字"；名字不对时兜底扫描仍可能找到，
        ///    但会打 Warning 提示你同步（见 TryFallbackScan）。
        /// </summary>
        private static readonly string[] EntryTypeNames =
        {
            "FTProject.HotUpdateEntry",
        };

        /// <summary>
        /// 查找并实例化热更入口。失败时返回 null 并给出可读原因。
        /// </summary>
        /// <param name="error">失败原因（成功时为 null）</param>
        public static IHotUpdateEntry CreateEntry(out string error)
        {
            error = null;

            // ① 快路径：按候选全名精确找（常规情况走这里，零全扫开销）
            for (int i = 0; i < EntryTypeNames.Length; i++)
            {
                Type t = FindTypeByFullName(EntryTypeNames[i]);
                if (t == null)
                {
                    continue;
                }

                if (!TryInstantiate(t, out IHotUpdateEntry entry, out string reason))
                {
                    error = "找到入口类型「" + t.FullName + "」但不能实例化：" + reason;
                    return null;
                }
                return entry;
            }

            // ② 兜底：按接口扫描（候选名全部失效时用；会打 Warning）
            return TryFallbackScan(out error);
        }

        /// <summary>在所有已加载程序集中按全名查类型（不抛异常）。</summary>
        private static Type FindTypeByFullName(string fullName)
        {
            Assembly[] assemblies = AppDomain.CurrentDomain.GetAssemblies();
            for (int i = 0; i < assemblies.Length; i++)
            {
                Type found;
                try
                {
                    found = assemblies[i].GetType(fullName, false);
                }
                catch (Exception)
                {
                    continue; // 个别动态程序集取类型会抛，跳过
                }

                if (found != null)
                {
                    return found;
                }
            }
            return null;
        }

        /// <summary>
        /// 兜底扫描：遍历所有程序集找 `IHotUpdateEntry` 的实现类。
        /// 只在候选名失效时走，成功后打 Warning 提醒同步候选名。
        /// </summary>
        private static IHotUpdateEntry TryFallbackScan(out string error)
        {
            error = null;

            Type iface = typeof(IHotUpdateEntry);
            var candidates = new List<Type>();

            Assembly[] assemblies = AppDomain.CurrentDomain.GetAssemblies();
            for (int i = 0; i < assemblies.Length; i++)
            {
                Type[] types;
                try
                {
                    types = assemblies[i].GetTypes();
                }
                catch (ReflectionTypeLoadException e)
                {
                    // 部分类型加载失败也要拿能拿到的（Unity 内置程序集常这样）
                    types = e.Types;
                }
                catch (Exception)
                {
                    continue;
                }

                if (types == null)
                {
                    continue;
                }

                for (int j = 0; j < types.Length; j++)
                {
                    Type t = types[j];
                    if (t == null || t.IsAbstract || t.IsInterface)
                    {
                        continue;
                    }
                    if (iface.IsAssignableFrom(t))
                    {
                        candidates.Add(t);
                    }
                }
            }

            if (candidates.Count == 0)
            {
                error = "在所有已加载程序集中找不到任何 IHotUpdateEntry 的实现类。\n"
                    + "  请确认：① 热更 dll（FTProject.Runtime.dll）已成功加载；\n"
                    + "          ② 热更侧存在 `: IHotUpdateEntry` 的实现类（当前候选名："
                    + string.Join(" / ", EntryTypeNames) + "）。";
                return null;
            }

            if (candidates.Count > 1)
            {
                error = "找到多个 IHotUpdateEntry 实现类，无法确定用哪个："
                    + string.Join("、", candidates.ConvertAll(c => c.FullName).ToArray())
                    + "\n  请只保留一个实现类。";
                return null;
            }

            Type target = candidates[0];
            UnityEngine.Debug.LogWarning(
                "[HotUpdate] 候选名未命中，兜底扫描找到 IHotUpdateEntry 实现类：「"
                + target.FullName + "」。\n"
                + "  ⚠️ 请把它同步进 HotUpdateEntryLocator.EntryTypeNames，以走快路径、"
                + "并避免每次启动都全扫。");

            if (!TryInstantiate(target, out IHotUpdateEntry entry, out string reason))
            {
                error = "兜底找到入口类型「" + target.FullName + "」但不能实例化：" + reason;
                return null;
            }
            return entry;
        }

        /// <summary>实例化实现类（要求无参可构造）。</summary>
        private static bool TryInstantiate(Type t, out IHotUpdateEntry entry, out string error)
        {
            entry = null;
            error = null;

            try
            {
                object instance = Activator.CreateInstance(t);
                entry = instance as IHotUpdateEntry;
                if (entry == null)
                {
                    // 理论上不会发生（t 已由 IsAssignableFrom 校验过）
                    error = "实例化成功但类型转换失败（内部错误）";
                    return false;
                }
                return true;
            }
            catch (MissingMethodException)
            {
                error = "该类型没有 public 无参构造函数。"
                    + "IHotUpdateEntry 的实现类必须能被无参构造。";
                return false;
            }
            catch (Exception e)
            {
                error = e.ToString();
                return false;
            }
        }
    }
}
