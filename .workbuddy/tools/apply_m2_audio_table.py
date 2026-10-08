# -*- coding: utf-8 -*-
"""
M2 音效系统（W6-1）：新建 TBAudio 表并在 __tables__.xlsx 登记。

【为什么先建表、却没有音频文件】
  工程内目前 **0 个音频文件**（已按 .mp3/.wav/.ogg/.aiff 全盘扫描确认）。
  按设计文档 §3.5「功能缺失不应阻塞」，音效这一轮交付的是
  **系统 + 配置 + 调用点**：表里先把逻辑名与参数定下来，
  美术/音效给文件后只需丢进 Assets/Audio/ 并跑一次目录生成器，
  **不需要改任何代码**（与"面板换皮""塔换外观"同一个口径）。

【幂等性】按 id 与表名定位，重复执行结果一致。
"""
import os
import shutil
import sys
import datetime

import openpyxl

sys.stdout.reconfigure(encoding="utf-8")

# 【为什么按 __file__ 推导】本脚本位于 <工程根>/.workbuddy/tools/ 下，
# 硬编码 "D:/FreedomTower_1" 会在换机器 / 换盘符时静默扫到错误目录（历史上踩过：
# 四个静态检查脚本曾因路径写错而"扫 0 文件却一律 PASS"）。三级 dirname 回到工程根。
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATAS = os.path.join(ROOT, "Luban/Config/Datas")
BACKUP_ROOT = os.path.join(ROOT, ".workbuddy/backup")

AUDIO_FILE = "AudioData.xlsx"
TABLE_NAME = "TBAudio"
BEAN_NAME = "AudioData"

# 表头三行，格式与既有表完全一致
AUDIO_HEADER = [
    ["##", "id", "name", "logicalName", "volume", "pitch", "loop", "is3d", "desc"],
    ["##type", "int", "string", "string", "float", "float", "int", "int", "string"],
    ["##", "主键", "展示名", "逻辑名（对应 ResTable 的 Audio_<logicalName>）",
     "音量 0~1", "音高（1=原速）", "是否循环 0否/1是", "是否 3D 音效 0否/1是", "备注"],
]

# (id, name, logicalName, volume, pitch, loop, is3d, desc)
AUDIO_ROWS = [
    (1, "普通塔开火", "sfx_tower_fire_normal", 0.55, 1.0, 0, 0, "单体塔开火"),
    (2, "强力塔开火", "sfx_tower_fire_power", 0.65, 0.95, 0, 0, "AOE 塔开火，低频更重"),
    (3, "减速塔开火", "sfx_tower_fire_retard", 0.5, 1.1, 0, 0, "减速塔开火"),
    (4, "穿透塔开火", "sfx_tower_fire_pierce", 0.5, 1.15, 0, 0, "穿透塔开火，偏清脆"),
    (5, "激光塔开火", "sfx_tower_fire_laser", 0.55, 1.2, 0, 0, "激光 hitscan"),
    (6, "怪物受击", "sfx_enemy_hit", 0.35, 1.0, 0, 0, "命中非致命"),
    (7, "怪物死亡", "sfx_enemy_death", 0.6, 1.0, 0, 0, "击杀"),
    (8, "建造防御塔", "sfx_tower_build", 0.7, 1.0, 0, 0, "建塔成功"),
    (9, "升级防御塔", "sfx_tower_upgrade", 0.7, 1.05, 0, 0, "升级成功"),
    (10, "出售防御塔", "sfx_tower_sell", 0.6, 0.95, 0, 0, "出售返还"),
    (11, "回合开始", "sfx_round_start", 0.8, 1.0, 0, 0, "回合开始"),
    (12, "回合完成", "sfx_round_clear", 0.8, 1.0, 0, 0, "回合清空"),
    (13, "漏怪", "sfx_enemy_leak", 0.85, 0.9, 0, 0, "怪物走到终点，负面反馈"),
    (14, "通关", "sfx_victory", 0.9, 1.0, 0, 0, "全部回合完成"),
    (15, "失败", "sfx_defeat", 0.9, 0.85, 0, 0, "生命归零"),
    (16, "按钮点击", "sfx_ui_click", 0.4, 1.0, 0, 0, "通用 UI 点击"),
    # —— BGM（M4-W7 追加）：循环播放，AudioManager 用独立通道处理，见 PlayBgm。——
    (17, "选关BGM", "bgm_select", 0.5, 1.0, 1, 0, "选关界面循环"),
    (18, "战斗BGM", "bgm_battle", 0.4, 1.0, 1, 0, "战斗循环"),
]


def backup():
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = os.path.join(BACKUP_ROOT, stamp, "Config", "Datas")
    os.makedirs(dst, exist_ok=True)
    for name in (AUDIO_FILE, "__tables__.xlsx"):
        src = os.path.join(DATAS, name)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(dst, name))
    return dst


def build_audio_table():
    path = os.path.join(DATAS, AUDIO_FILE)
    if os.path.exists(path):
        wb = openpyxl.load_workbook(path)
        ws = wb.active
    else:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Sheet1"

    for r, row in enumerate(AUDIO_HEADER, start=1):
        for c, v in enumerate(row, start=1):
            ws.cell(row=r, column=c).value = v

    for i, spec in enumerate(AUDIO_ROWS):
        r = 4 + i
        # 【易错点】A 列是 Luban 的 "##" 标记列，**数据从 B 列（第 2 列）开始**。
        # 之前用 start=1 把 id 写进了 A 列，Luban 便在 B 列读到了"普通塔开火"当 id。
        # 其余各表也都是"A 列留空、数据从 B 列起"，这里必须对齐。
        for c, v in enumerate(spec, start=2):
            ws.cell(row=r, column=c).value = v
        ws.cell(row=r, column=1).value = None

    wb.save(path)
    return "已写出 %s（%d 行）" % (AUDIO_FILE, len(AUDIO_ROWS))


def register_table():
    path = os.path.join(DATAS, "__tables__.xlsx")
    wb = openpyxl.load_workbook(path)
    ws = wb.active

    # 幂等：已登记就不再追加
    for r in range(4, ws.max_row + 1):
        if str(ws.cell(row=r, column=2).value or "").strip() == TABLE_NAME:
            return "__tables__.xlsx 已登记 %s，跳过" % TABLE_NAME

    r = ws.max_row + 1
    if ws.cell(row=r - 1, column=2).value is None and r > 4:
        r = r - 1
    ws.cell(row=r, column=1).value = "音效表"
    ws.cell(row=r, column=2).value = TABLE_NAME      # full_name
    ws.cell(row=r, column=3).value = BEAN_NAME       # value_type
    ws.cell(row=r, column=4).value = True            # define_from_file
    ws.cell(row=r, column=5).value = AUDIO_FILE      # input

    wb.save(path)
    return "__tables__.xlsx 新增一行：%s → %s" % (TABLE_NAME, AUDIO_FILE)


if __name__ == "__main__":
    print("已备份到:", backup())
    print(build_audio_table())
    print(register_table())
    print("OK")
