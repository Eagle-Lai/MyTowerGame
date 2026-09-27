"""
扫描 _UIAssets/Monsters 下的全部怪物，生成 Assets/Scripts/Data/MonsterCatalog.cs

为什么用"生成代码"而不是"运行时扫描"：
  ResTable 是资源寻址的唯一数据源，它需要在**运行时**就能枚举全部逻辑名
  （预加载、AB 引用计数、自检都要用），而运行时代码不能调 AssetDatabase。
  所以由工具在编辑期把清单生成成一份纯数据 C# 文件。
  新增/删除怪物后重跑本脚本（或 Unity 菜单「9. 导入全部怪物」）即可。

命名与归属规则（与 MonsterPrefabBuilder 共用，必须一致）：
  逻辑名   Enemy_<PrefabName>
  战斗预制体 Assets/Prefabs/Enemy/Enemy_<PrefabName>.prefab
  资源包    enemy_<familyLower>        ← 按家族分包，只加载本关用到的家族
  源 prefab Assets/_UIAssets/Monsters/<Family>/<Dir>/<PrefabName>.prefab
  图集     同目录 <PrefabName>.png（有则登记）
"""
import io, os, collections

ASSETS = r'D:\FreedomTower\Assets'
SRC_ROOT = os.path.join(ASSETS, '_UIAssets', 'Monsters')
OUT = os.path.join(ASSETS, 'Scripts', 'Data', 'MonsterCatalog.cs')


def scan():
    out = []
    for fam in sorted(os.listdir(SRC_ROOT)):
        fd = os.path.join(SRC_ROOT, fam)
        if not os.path.isdir(fd) or fam.startswith('_'):
            continue
        for sub in sorted(os.listdir(fd)):
            sd = os.path.join(fd, sub)
            if not os.path.isdir(sd):
                continue
            for fn in os.listdir(sd):
                if not fn.endswith('.prefab'):
                    continue
                name = os.path.splitext(fn)[0]
                atlas = os.path.join(sd, name + '.png')
                atlas_rel = os.path.relpath(atlas, os.path.dirname(ASSETS)).replace('\\', '/')
                if not os.path.exists(atlas):
                    atlas_rel = ''
                src_rel = os.path.relpath(os.path.join(sd, fn), os.path.dirname(ASSETS)).replace('\\', '/')
                out.append((fam, name, atlas_rel, src_rel))
    # 稳定排序：家族 -> 名称
    out.sort(key=lambda t: (t[0], t[1]))
    return out


def cs_str(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


def wrap(items, indent='            ', per_line=4):
    lines = []
    for i in range(0, len(items), per_line):
        lines.append(indent + ', '.join(items[i:i + per_line]) + ',')
    return '\n'.join(lines)


def main():
    mons = scan()
    assert mons, '没有扫描到任何怪物'
    names = [cs_str(n) for _, n, _, _ in mons]
    fams = [cs_str(f) for f, _, _, _ in mons]
    atlases = [cs_str(a) for _, _, a, _ in mons]
    sources = [cs_str(sp) for _, _, _, sp in mons]
    bundles = sorted(set('enemy_' + f.lower() for f, _, _, _ in mons))

    content = '''// =============================================================================
// 本文件由工具自动生成，请勿手改。
//   生成脚本：.workbuddy/tools/gen_monster_catalog.py
//   Unity 菜单：Tools ▸ 塔防 ▸ 9. 导入全部怪物（会同时生成战斗预制体）
//
// 数据来源：Assets/_UIAssets/Monsters/<家族>/<怪名>/<怪名>.prefab
// 共 %d 个怪物 / %d 个家族资源包
// =============================================================================

namespace FTProject
{
    /// <summary>
    /// 怪物清单（生成代码）。
    /// 三个数组下标一一对应：Names[i] 属于 Families[i]，图集是 AtlasPaths[i]（可能为空）。
    /// </summary>
    public static class MonsterCatalog
    {
        /// <summary>怪物 prefab 名（如 "Rat"）</summary>
        public static readonly string[] Names =
        {
%s
        };

        /// <summary>所属家族（如 "Rats"），同时决定资源包名</summary>
        public static readonly string[] Families =
        {
%s
        };

        /// <summary>源图集路径（相对工程根，空串表示该怪没有独立图集）</summary>
        public static readonly string[] AtlasPaths =
        {
%s
        };

        /// <summary>源 prefab 路径（相对工程根）。
        /// 必须记录而不能靠拼接：有 2 个怪物的目录名与 prefab 名不一致。</summary>
        public static readonly string[] SourcePaths =
        {
%s
        };

        /// <summary>全部家族资源包名（供 ResBundle / 打包脚本枚举）</summary>
        public static readonly string[] Bundles =
        {
%s
        };

        public static int Count { get { return Names.Length; } }

        /// <summary>逻辑名：Enemy_&lt;怪名&gt;</summary>
        public static string LogicalName(int i)
        {
            return "Enemy_" + Names[i];
        }

        /// <summary>战斗预制体路径（由 MonsterPrefabBuilder 生成）</summary>
        public static string PrefabPath(int i)
        {
            return "Assets/Prefabs/Enemy/Enemy_" + Names[i] + ".prefab";
        }

        /// <summary>所属资源包名：enemy_&lt;家族小写&gt;</summary>
        public static string BundleOf(int i)
        {
            return "enemy_" + Families[i].ToLowerInvariant();
        }
    }
}
''' % (len(mons), len(bundles), wrap(names), wrap(fams), wrap(atlases), wrap(sources), wrap([cs_str(b) for b in bundles]))

    io.open(OUT, 'w', encoding='utf-8-sig').write(content)
    print('已生成: %s' % OUT)
    print('  怪物 %d 个 / 资源包 %d 个' % (len(mons), len(bundles)))
    fam_cnt = collections.Counter(f for f, _, _, _ in mons)
    for f in sorted(fam_cnt):
        print('    %-12s %2d' % (f, fam_cnt[f]))


if __name__ == '__main__':
    main()
