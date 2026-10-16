# -*- coding: utf-8 -*-
"""
为 AdvancedHen 派生"正面(朝下)/背面(朝上)"两向资源。

生成物（命名/规格与既有左右方向资源完全一致）：
  图集 meta   Assets/_UIAssets/Monsters/Birds/AdvancedHen/AdvancedHen_{Down,Up}.png.meta   (AB=enemy_birds)
  源预制体    Assets/_UIAssets/Monsters/Birds/AdvancedHen/AdvancedHen_{Down,Up}.prefab
  战斗预制体  Assets/Prefabs/Enemy/Enemy_AdvancedHen_{Down,Up}.prefab (+ .meta, AB=enemy_birds)

做法：整体复制既有文件，只替换"图集 guid"与根节点名。
  · 图集 slot 的顶点 rect / pivot 与主图集逐字相同 → 精灵 internalID 也相同
    （Unity 的 spriteID = name+rect 的哈希），所以预制体只需换 guid，其余字节不动。
  · 动画只驱动骨骼 Transform（Body/Head/Body/LegL…），不含任何精灵引用曲线，
    因此直接复用 _Common/Animations/Rooster/Controller.controller，不需要新动画。
"""
import os
import re
import uuid
import io

ROOT = r"D:/FreedomTower_1"
ART = os.path.join(ROOT, "Assets/_UIAssets/Monsters/Birds/AdvancedHen")
ENEMY = os.path.join(ROOT, "Assets/Prefabs/Enemy")

OLD_GUID = "b858ba88cc3e2dc42b51d53a94920c1e"   # AdvancedHen.png
OLD_SRC_PREFAB = os.path.join(ART, "AdvancedHen.prefab")
OLD_COMBAT_PREFAB = os.path.join(ENEMY, "Enemy_AdvancedHen.prefab")
OLD_PNG_META = os.path.join(ART, "AdvancedHen.png.meta")

# 两个方向：后缀 → 中文含义
DIRECTIONS = [("Down", "正面/朝下"), ("Up", "背面/朝上")]


def new_guid():
    return uuid.uuid4().hex


def read(p):
    """返回 (文本, 编码)。编码保留原文件的 BOM 有无。"""
    with open(p, "rb") as f:
        raw = f.read()
    sig = "utf-8-sig" if raw.startswith(b"\xef\xbb\xbf") else "utf-8"
    return raw.decode(sig), sig


def write_keep_sig(p, text, sig):
    """原文件带 BOM 的回写时保留 UTF-8 BOM（Unity 生成的 meta 无 BOM，源 prefab 有）。"""
    with io.open(p, "w", encoding=sig) as f:
        f.write(text)


def derive(text, old_atlas_guid, new_atlas_guid, old_root_name, new_root_name):
    if old_atlas_guid not in text:
        raise RuntimeError("源文件里找不到图集 guid：" + old_atlas_guid)
    out = text.replace(old_atlas_guid, new_atlas_guid)
    # 只改根节点名（缩进 2 空格的 m_Name），子节点名 Head/Body/Wing/Leg 必须保持原样
    out = out.replace("  m_Name: " + old_root_name + "\n", "  m_Name: " + new_root_name + "\n")
    return out


def main():
    src_prefab, sig_prefab = read(OLD_SRC_PREFAB)
    combat_prefab, sig_combat = read(OLD_COMBAT_PREFAB)
    png_meta, _ = read(OLD_PNG_META)

    rows = []
    for suffix, cn in DIRECTIONS:
        atlas_guid = new_guid()
        name = "AdvancedHen_" + suffix

        # 1) 图集 meta：仅换 guid，其余（切图 rect/pivot/AB 名）逐字保留
        meta_text = re.sub(r"^guid: [0-9a-f]{32}$", "guid: " + atlas_guid, png_meta, count=1, flags=re.M)
        mp = os.path.join(ART, name + ".png.meta")
        with io.open(mp, "w", encoding="utf-8", newline="\n") as f:
            f.write(meta_text)

        # 2) 源预制体
        sp = os.path.join(ART, name + ".prefab")
        write_keep_sig(sp, derive(src_prefab, OLD_GUID, atlas_guid, "AdvancedHen", name), sig_prefab)
        smp = os.path.join(ART, name + ".prefab.meta")
        with io.open(smp, "w", encoding="utf-8", newline="\n") as f:
            f.write("fileFormatVersion: 2\nguid: %s\nPrefabImporter:\n  externalObjects: {}\n"
                    "  userData: \n  assetBundleName: \n  assetBundleVariant: \n" % new_guid())

        # 3) 战斗预制体（含 HpBar / BaseEnemy / MonsterAnimEventReceiver）
        cp = os.path.join(ENEMY, "Enemy_" + name + ".prefab")
        write_keep_sig(cp,
                       derive(combat_prefab, OLD_GUID, atlas_guid, "Enemy_AdvancedHen", "Enemy_" + name),
                       sig_combat)
        cmp = os.path.join(ENEMY, "Enemy_" + name + ".prefab.meta")
        with io.open(cmp, "w", encoding="utf-8", newline="\n") as f:
            f.write("fileFormatVersion: 2\nguid: %s\nPrefabImporter:\n  externalObjects: {}\n"
                    "  userData: \n  assetBundleName: enemy_birds\n  assetBundleVariant: \n" % new_guid())

        rows.append((cn, name, atlas_guid, mp, sp, cp))

    for cn, name, g, mp, sp, cp in rows:
        print("【%s】" % cn)
        print("  图集 meta  guid=%s\n    %s" % (g, mp))
        print("  源预制体   %s" % sp)
        print("  战斗预制体 %s" % cp)


if __name__ == "__main__":
    main()
