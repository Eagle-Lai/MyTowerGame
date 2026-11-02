#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
L02关卡配置生成脚本 - 方案2（中等增长）
- 初始金币: 100 (固定)
- 总经济: 2500金
- 怪物数量: ×1.5
- 怪物HP: ×1.05
- 波次奖励: 1900金
"""

import openpyxl
from openpyxl import Workbook
from copy import copy
import os
import sys

# ==================== 配置参数 ====================
HP_SCALE = 1.05
GOLD_DROP_SCALE = 1.05
ENEMY_COUNT_SCALE = 1.5
L02_ENEMY_ID_BASE = 6000000
L02_WAVE_ID_OFFSET = 2000

# 波次奖励（手工计算好的25个值）
L02_WAVE_REWARDS = [
    52, 52, 52, 52, 122,  # W1-5
    63, 63, 63, 63, 127,  # W6-10
    66, 66, 66, 66, 131,  # W11-15
    68, 68, 68, 68, 135,  # W16-20
    71, 71, 71, 71, 103   # W21-25
]

L01_DIR = 'Luban/Config/Datas/Levels/L01'
L02_DIR = 'Luban/Config/Datas/Levels/L02'

# ==================== 工具函数 ====================
def copy_cell_style(src_cell, dst_cell):
    """复制单元格样式"""
    if src_cell.has_style:
        dst_cell.font = copy(src_cell.font)
        dst_cell.border = copy(src_cell.border)
        dst_cell.fill = copy(src_cell.fill)
        dst_cell.number_format = copy(src_cell.number_format)
        dst_cell.protection = copy(src_cell.protection)
        dst_cell.alignment = copy(src_cell.alignment)

def backup_file(filepath):
    """备份文件"""
    if os.path.exists(filepath):
        backup_path = filepath + '.bak_20261102_before_script'
        if not os.path.exists(backup_path):
            import shutil
            shutil.copy2(filepath, backup_path)
            print(f"  [Backup] {os.path.basename(filepath)} -> {os.path.basename(backup_path)}")

# ==================== RoundData 生成 ====================
def generate_rounddata():
    print("\n[1/4] Generating RoundData.xlsx...")

    src_path = f'{L01_DIR}/RoundData.xlsx'
    dst_path = f'{L02_DIR}/RoundData.xlsx'

    backup_file(dst_path)

    src_wb = openpyxl.load_workbook(src_path)
    src_ws = src_wb.active

    dst_wb = Workbook()
    dst_ws = dst_wb.active

    wave_idx = 0
    for row_idx, row in enumerate(src_ws.iter_rows(), 1):
        for col_idx, cell in enumerate(row, 1):
            dst_cell = dst_ws.cell(row=row_idx, column=col_idx)
            value = cell.value

            # 跳过前3行表头
            if row_idx > 3:
                # id列 (第2列)
                if col_idx == 2 and isinstance(value, (int, float)):
                    value = int(value) + L02_WAVE_ID_OFFSET

                # EnemyIndexs列 (第3列)
                elif col_idx == 3:
                    if isinstance(value, str):
                        ids = [int(x.strip()) for x in value.split(',') if x.strip()]
                        new_ids = [id + L02_WAVE_ID_OFFSET for id in ids]
                        value = ','.join(map(str, new_ids))
                    elif isinstance(value, (int, float)):
                        value = int(value) + L02_WAVE_ID_OFFSET

                # rewardGold列 (第6列)
                elif col_idx == 6 and isinstance(value, (int, float)):
                    if wave_idx < len(L02_WAVE_REWARDS):
                        value = L02_WAVE_REWARDS[wave_idx]
                        wave_idx += 1

            dst_cell.value = value
            copy_cell_style(cell, dst_cell)

    # 复制列宽和行高
    for col_letter, col_dim in src_ws.column_dimensions.items():
        dst_ws.column_dimensions[col_letter].width = col_dim.width
    for row_num, row_dim in src_ws.row_dimensions.items():
        dst_ws.row_dimensions[row_num].height = row_dim.height

    dst_wb.save(dst_path)
    print(f"  [OK] Saved: {dst_path}")
    print(f"  [Check] Wave rewards sum: {sum(L02_WAVE_REWARDS)} (target: 1900)")

# ==================== EnemyData 生成 ====================
def generate_enemydata():
    print("\n[2/4] Generating EnemyData.xlsx...")

    src_path = f'{L01_DIR}/EnemyData.xlsx'
    dst_path = f'{L02_DIR}/EnemyData.xlsx'

    backup_file(dst_path)

    src_wb = openpyxl.load_workbook(src_path)
    src_ws = src_wb.active

    # 找到列索引
    headers = [cell.value for cell in list(src_ws.iter_rows())[0]]
    hp_col = headers.index('hp') + 1 if 'hp' in headers else None
    gold_col = headers.index('goldDrop') + 1 if 'goldDrop' in headers else None
    desc_col = headers.index('desc') + 1 if 'desc' in headers else None

    dst_wb = Workbook()
    dst_ws = dst_wb.active

    for row_idx, row in enumerate(src_ws.iter_rows(), 1):
        for col_idx, cell in enumerate(row, 1):
            dst_cell = dst_ws.cell(row=row_idx, column=col_idx)
            value = cell.value

            if row_idx > 3:  # 跳过表头
                # enemyId列 (第2列)
                if col_idx == 2 and isinstance(value, (int, float)):
                    old_id = int(value)
                    if old_id >= 5000000:
                        value = L02_ENEMY_ID_BASE + (old_id - 5000000)
                    else:
                        value = L02_ENEMY_ID_BASE + old_id

                # hp列
                elif col_idx == hp_col and isinstance(value, (int, float)):
                    value = round(value * HP_SCALE, 6)

                # goldDrop列
                elif col_idx == gold_col and isinstance(value, (int, float)):
                    value = round(value * GOLD_DROP_SCALE, 6)

                # desc列
                elif col_idx == desc_col and isinstance(value, str):
                    value = str(value) + f" | L02-scale-20261102: hp×{HP_SCALE}, gold×{GOLD_DROP_SCALE}, count×{ENEMY_COUNT_SCALE}"

            dst_cell.value = value
            copy_cell_style(cell, dst_cell)

    # 复制列宽和行高
    for col_letter, col_dim in src_ws.column_dimensions.items():
        dst_ws.column_dimensions[col_letter].width = col_dim.width
    for row_num, row_dim in src_ws.row_dimensions.items():
        dst_ws.row_dimensions[row_num].height = row_dim.height

    dst_wb.save(dst_path)
    print(f"  [OK] Saved: {dst_path}")
    print(f"  [Check] HP scale: {HP_SCALE}x, Gold scale: {GOLD_DROP_SCALE}x")

# ==================== EnemyList 生成 ====================
def generate_enemylist():
    print("\n[3/4] Generating EnemyList.xlsx...")

    src_path = f'{L01_DIR}/EnemyList.xlsx'
    dst_path = f'{L02_DIR}/EnemyList.xlsx'

    backup_file(dst_path)

    src_wb = openpyxl.load_workbook(src_path)
    src_ws = src_wb.active

    dst_wb = Workbook()
    dst_ws = dst_wb.active

    for row_idx, row in enumerate(src_ws.iter_rows(), 1):
        for col_idx, cell in enumerate(row, 1):
            dst_cell = dst_ws.cell(row=row_idx, column=col_idx)
            value = cell.value

            if row_idx > 3:  # 跳过表头
                # id列 (第2列)
                if col_idx == 2 and isinstance(value, (int, float)):
                    value = int(value) + L02_WAVE_ID_OFFSET

                # EnemyIndexs列 (第3列)
                elif col_idx == 3 and isinstance(value, str):
                    # 解析ID列表
                    ids = [int(x.strip()) for x in value.split(',') if x.strip()]

                    # 转换ID并扩展数量
                    new_ids = []
                    for old_id in ids:
                        if old_id >= 5000000:
                            new_id = L02_ENEMY_ID_BASE + (old_id - 5000000)
                        else:
                            new_id = L02_ENEMY_ID_BASE + old_id
                        new_ids.append(new_id)

                    # 扩展到1.5倍数量
                    target_count = int(len(new_ids) * ENEMY_COUNT_SCALE)
                    if target_count > len(new_ids):
                        # 循环复制直到达到目标数量
                        expanded_ids = []
                        for i in range(target_count):
                            expanded_ids.append(new_ids[i % len(new_ids)])
                        new_ids = expanded_ids

                    value = ','.join(map(str, new_ids))

            dst_cell.value = value
            copy_cell_style(cell, dst_cell)

    # 复制列宽和行高
    for col_letter, col_dim in src_ws.column_dimensions.items():
        dst_ws.column_dimensions[col_letter].width = col_dim.width
    for row_num, row_dim in src_ws.row_dimensions.items():
        dst_ws.row_dimensions[row_num].height = row_dim.height

    dst_wb.save(dst_path)
    print(f"  [OK] Saved: {dst_path}")
    print(f"  [Check] Enemy count scale: {ENEMY_COUNT_SCALE}x")

# ==================== SceneInfo 生成 ====================
def generate_sceneinfo():
    print("\n[4/4] Generating SceneInfo.xlsx...")

    src_path = f'{L01_DIR}/SceneInfo.xlsx'
    dst_path = f'{L02_DIR}/SceneInfo.xlsx'

    backup_file(dst_path)

    src_wb = openpyxl.load_workbook(src_path)
    src_ws = src_wb.active

    dst_wb = Workbook()
    dst_ws = dst_wb.active

    for row_idx, row in enumerate(src_ws.iter_rows(), 1):
        for col_idx, cell in enumerate(row, 1):
            dst_cell = dst_ws.cell(row=row_idx, column=col_idx)
            value = cell.value

            if row_idx > 3:  # 跳过表头
                # id列 (第2列)
                if col_idx == 2 and isinstance(value, (int, float)):
                    value = 2

                # RoundList列 (第3列)
                elif col_idx == 3 and isinstance(value, str):
                    ids = [int(x.strip()) for x in value.split(',') if x.strip()]
                    new_ids = [id + L02_WAVE_ID_OFFSET for id in ids]
                    value = ','.join(map(str, new_ids))

                # name列 (假设第11列)
                elif col_idx == 11 and isinstance(value, str) and "关卡" in str(value):
                    value = "关卡 2"

                # mapId列 (假设第12列)
                elif col_idx == 12 and isinstance(value, (int, float)):
                    value = 2

                # initialGold - 保持100不变
                # initialHp - 保持L02原有值

            dst_cell.value = value
            copy_cell_style(cell, dst_cell)

    # 复制列宽和行高
    for col_letter, col_dim in src_ws.column_dimensions.items():
        dst_ws.column_dimensions[col_letter].width = col_dim.width
    for row_num, row_dim in src_ws.row_dimensions.items():
        dst_ws.row_dimensions[row_num].height = row_dim.height

    dst_wb.save(dst_path)
    print(f"  [OK] Saved: {dst_path}")
    print(f"  [Check] initialGold should remain 100")

# ==================== 主函数 ====================
def main():
    print("=" * 70)
    print("L02 Configuration Generator - Final Version")
    print("=" * 70)
    print("\nConfiguration:")
    print(f"  HP Scale: {HP_SCALE}x")
    print(f"  Gold Drop Scale: {GOLD_DROP_SCALE}x")
    print(f"  Enemy Count Scale: {ENEMY_COUNT_SCALE}x")
    print(f"  Total Wave Rewards: {sum(L02_WAVE_REWARDS)} gold")
    print(f"  Initial Gold: 100 (unchanged)")
    print(f"  Target Total Economy: ~2500 gold")

    try:
        generate_rounddata()
        generate_enemydata()
        generate_enemylist()
        generate_sceneinfo()

        print("\n" + "=" * 70)
        print("Configuration Complete!")
        print("=" * 70)
        print("\nGenerated files:")
        print(f"  - {L02_DIR}/RoundData.xlsx")
        print(f"  - {L02_DIR}/EnemyData.xlsx")
        print(f"  - {L02_DIR}/EnemyList.xlsx")
        print(f"  - {L02_DIR}/SceneInfo.xlsx")
        print("\nBackup files created with suffix: .bak_20261102_before_script")
        print("\nNext steps:")
        print("  1. Review the generated files")
        print("  2. Run Luban export: cd Luban/Config && gen_code_json.bat")
        print("  3. Verify in Unity: refresh and compile")
        print("  4. Test in Play Mode")

        return 0

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
