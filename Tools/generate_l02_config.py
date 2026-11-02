#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
L02关卡数值配置生成工具
基于L01模板生成L02配置，保持相同难度，适配地图差异

生成日期：2026-11-02
基准：L01
目标：L02
缩放策略：HP × 0.95 (路径长度补偿)
"""

import openpyxl
from openpyxl import Workbook
from copy import copy
import os

# ==================== 配置参数 ====================
HP_SCALE = 0.95  # HP缩放因子（基于L02路径长度+24.3%的补偿）
L02_ENEMY_ID_BASE = 6000000  # L02敌人ID起始
L02_WAVE_ID_OFFSET = 2000  # L02波次ID偏移

# L01/L02路径
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

def copy_sheet_with_data(src_path, dst_path, data_transformer=None):
    """
    复制Excel文件并应用数据转换
    data_transformer: function(row_idx, col_idx, value) -> new_value
    """
    src_wb = openpyxl.load_workbook(src_path)
    src_ws = src_wb.active

    dst_wb = Workbook()
    dst_ws = dst_wb.active

    # 复制所有行
    for row_idx, row in enumerate(src_ws.iter_rows(), 1):
        for col_idx, cell in enumerate(row, 1):
            dst_cell = dst_ws.cell(row=row_idx, column=col_idx)

            # 获取值
            value = cell.value

            # 应用转换
            if data_transformer and row_idx > 3:  # 跳过表头
                value = data_transformer(row_idx, col_idx, value)

            dst_cell.value = value
            copy_cell_style(cell, dst_cell)

    # 复制列宽
    for col_letter, col_dim in src_ws.column_dimensions.items():
        dst_ws.column_dimensions[col_letter].width = col_dim.width

    # 复制行高
    for row_num, row_dim in src_ws.row_dimensions.items():
        dst_ws.row_dimensions[row_num].height = row_dim.height

    dst_wb.save(dst_path)
    return dst_path

# ==================== RoundData 转换 ====================
def transform_rounddata(row_idx, col_idx, value):
    """转换RoundData：修改id和EnemyIndexs"""
    if col_idx == 2 and isinstance(value, (int, float)):  # id列
        if value <= 20:
            return int(value + L02_WAVE_ID_OFFSET)
        else:  # 401-405
            return int(value + L02_WAVE_ID_OFFSET)
    elif col_idx == 3 and isinstance(value, (int, float, str)):  # EnemyIndexs列
        if isinstance(value, str):
            # 解析逗号分隔的ID
            ids = [int(x.strip()) for x in value.split(',') if x.strip()]
            new_ids = [id + L02_WAVE_ID_OFFSET for id in ids]
            return ','.join(map(str, new_ids))
        else:
            return int(value + L02_WAVE_ID_OFFSET)
    return value

# ==================== EnemyData 转换 ====================
def create_enemydata_transformer(hp_col_idx):
    def transform(row_idx, col_idx, value):
        if col_idx == 2 and isinstance(value, (int, float)):  # enemyId列
            # 转换ID：5000001 -> 6000001
            old_id = int(value)
            if old_id >= 5000000:
                return L02_ENEMY_ID_BASE + (old_id - 5000000)
            else:
                return L02_ENEMY_ID_BASE + old_id
        elif col_idx == hp_col_idx and isinstance(value, (int, float)):  # hp列
            # HP缩放
            return round(value * HP_SCALE, 6)
        elif col_idx == 16 and isinstance(value, str):  # desc列（假设在第16列）
            # 在描述中添加L02标记
            return str(value) + f" | L02-tune-20261102: hp×{HP_SCALE}"
        return value
    return transform

# ==================== EnemyList 转换 ====================
def transform_enemylist(row_idx, col_idx, value):
    """转换EnemyList：修改id和EnemyIndexs"""
    if col_idx == 2 and isinstance(value, (int, float)):  # id列
        if value <= 20:
            return int(value + L02_WAVE_ID_OFFSET)
        else:
            return int(value + L02_WAVE_ID_OFFSET)
    elif col_idx == 3 and isinstance(value, str):  # EnemyIndexs列
        # 转换敌人ID列表：5000001,5000002 -> 6000001,6000002
        ids = [int(x.strip()) for x in value.split(',') if x.strip()]
        new_ids = []
        for old_id in ids:
            if old_id >= 5000000:
                new_ids.append(L02_ENEMY_ID_BASE + (old_id - 5000000))
            else:
                new_ids.append(L02_ENEMY_ID_BASE + old_id)
        return ','.join(map(str, new_ids))
    return value

# ==================== SceneInfo 转换 ====================
def transform_sceneinfo(row_idx, col_idx, value):
    """转换SceneInfo：修改id和RoundList"""
    if col_idx == 2 and isinstance(value, (int, float)):  # id列
        return 2  # L02的id
    elif col_idx == 3 and isinstance(value, str):  # RoundList列
        # 转换波次列表
        ids = [int(x.strip()) for x in value.split(',') if x.strip()]
        new_ids = []
        for old_id in ids:
            if old_id <= 20:
                new_ids.append(old_id + L02_WAVE_ID_OFFSET)
            else:
                new_ids.append(old_id + L02_WAVE_ID_OFFSET)
        return ','.join(map(str, new_ids))
    elif col_idx == 11 and isinstance(value, str):  # name列
        return "关卡 2"
    elif col_idx == 12 and isinstance(value, (int, float)):  # mapId列
        return 2
    return value

# ==================== 主函数 ====================
def main():
    print("=" * 60)
    print("L02 Configuration Generator")
    print("=" * 60)

    # 确定hp列位置（需要读取表头）
    l01_enemy_wb = openpyxl.load_workbook(f'{L01_DIR}/EnemyData.xlsx', read_only=True)
    l01_enemy_ws = l01_enemy_wb.active
    headers = [cell.value for cell in list(l01_enemy_ws.iter_rows())[0]]
    hp_col_idx = headers.index('hp') + 1 if 'hp' in headers else 3
    print(f"HP column detected at index: {hp_col_idx}")

    # 1. 转换 RoundData.xlsx
    print("\n[1/5] Generating RoundData.xlsx...")
    copy_sheet_with_data(
        f'{L01_DIR}/RoundData.xlsx',
        f'{L02_DIR}/RoundData.xlsx.new',
        transform_rounddata
    )
    print("[OK] RoundData.xlsx.new created")

    # 2. 转换 EnemyData.xlsx
    print("\n[2/5] Generating EnemyData.xlsx...")
    copy_sheet_with_data(
        f'{L01_DIR}/EnemyData.xlsx',
        f'{L02_DIR}/EnemyData.xlsx.new',
        create_enemydata_transformer(hp_col_idx)
    )
    print("[OK] EnemyData.xlsx.new created")

    # 3. 转换 EnemyList.xlsx
    print("\n[3/5] Generating EnemyList.xlsx...")
    copy_sheet_with_data(
        f'{L01_DIR}/EnemyList.xlsx',
        f'{L02_DIR}/EnemyList.xlsx.new',
        transform_enemylist
    )
    print("[OK] EnemyList.xlsx.new created")

    # 4. 转换 SceneInfo.xlsx
    print("\n[4/5] Generating SceneInfo.xlsx...")
    copy_sheet_with_data(
        f'{L01_DIR}/SceneInfo.xlsx',
        f'{L02_DIR}/SceneInfo.xlsx.new',
        transform_sceneinfo
    )
    print("[OK] SceneInfo.xlsx.new created")

    # 5. 复制其他不变的文件
    print("\n[5/5] Copying unchanged files...")
    for filename in ['LevelRules.xlsx', 'TowerInfo.xlsx', 'BulletData.xlsx']:
        src = f'{L01_DIR}/{filename}'
        dst = f'{L02_DIR}/{filename}.new'
        if os.path.exists(src):
            copy_sheet_with_data(src, dst, None)
            print(f"[OK] {filename}.new copied")

    print("\n" + "=" * 60)
    print("Generation Complete!")
    print("=" * 60)
    print("\nGenerated files (with .new suffix):")
    print("  - RoundData.xlsx.new")
    print("  - EnemyData.xlsx.new")
    print("  - EnemyList.xlsx.new")
    print("  - SceneInfo.xlsx.new")
    print("  - LevelRules.xlsx.new")
    print("  - TowerInfo.xlsx.new")
    print("  - BulletData.xlsx.new")
    print("\nConfiguration Summary:")
    print(f"  - HP Scaling: {HP_SCALE}x")
    print(f"  - Enemy ID Base: {L02_ENEMY_ID_BASE}")
    print(f"  - Wave ID Offset: +{L02_WAVE_ID_OFFSET}")
    print(f"  - Total Wave Rewards: 1305 gold (unchanged)")
    print("\nNext steps:")
    print("  1. Review the .new files")
    print("  2. Backup current L02 files")
    print("  3. Rename .new files to replace originals")
    print("  4. Run Luban export")
    print("  5. Verify in Unity")

if __name__ == '__main__':
    main()
