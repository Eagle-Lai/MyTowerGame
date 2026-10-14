# -*- coding: utf-8 -*-
"""向公司E工程的 Luban 多语言表幂等追加 2026-10-14 需求的新词条。

用法：
    C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe \
        E:/MyTowerGame/.workbuddy/tools/append_localization_rows_20261014.py

做了什么：
  1. 读取 E:/MyTowerGame/Luban/Config/Datas/Localization.xlsx（裸 zip/XML，与
     gen_localization_table.py 的产出格式一致）。
  2. 提取已有 id（列 B = 英文原文主键），跳过已存在的行（幂等）。
  3. 把 NEW_ROWS 追加到 sheetData 末尾并重写 zip（其余 zip 条目原样保留）。
  4. 跑完后必须在 Unity 里执行「Tools ▸ 塔防 ▸ 3. 导出配置表（Luban）」让词条生效
     （本工程由 FT_FeatureBuild 流水线自动完成这一步）。

权威源仍是 gen_localization_table.py 的 ROWS —— 本脚本与其保持同一份新词条。
"""
import re
import shutil
import zipfile

XLSX = r'E:/MyTowerGame/Luban/Config/Datas/Localization.xlsx'
BACKUP = XLSX + '.bak_20261014'

HEAD = ['id', 'en', 'zhHans', 'zhHant', 'comment']

# 与 gen_localization_table.py ROWS 末尾新增的 8 条保持一致
NEW_ROWS = [
    ('Pause', '暂停', '暫停', 'HUD 右上角暂停按钮'),
    ('Game Intro', '游戏介绍', '遊戲介紹', 'HUD 右上角介绍按钮/弹窗标题'),
    ('Back to Level Select', '回到选关', '回到選關', '介绍弹窗「回到选关」按钮'),
    ('{0}: drag onto a buildable tile and release to place',
     '{0}：拖到可建造格上松手放置，拖回按钮取消', '{0}：拖到可建造格上鬆手放置，拖回按鈕取消',
     '拖拽建造提示（占位符 {0} 保留）'),
    ('Stop the monsters before they reach your base: build towers on the open tiles beside the path.',
     '在怪物途经的路边空地建造防御塔，阻止它们抵达你的基地。',
     '在怪物途經的路邊空地建造防禦塔，阻止它們抵達你的基地。', '介绍弹窗正文 1'),
    ('Long-press a tower button, drag it onto the board, then release to build.',
     '长按建造栏的塔按钮，拖到棋盘格子上松手即可建造（金币在落地成功后扣除）。',
     '長按建造欄的塔按鈕，拖到棋盤格子上鬆手即可建造（金幣在落地成功後扣除）。', '介绍弹窗正文 2'),
    ('You may slow the monsters down, but never fully block their path.',
     '你可以拖慢怪物的脚步，但不能把它们的路完全堵死。',
     '你可以拖慢怪物的腳步，但不能把它們的路完全堵死。', '介绍弹窗正文 3'),
    ('Survive every round to win the level.',
     '撑过全部回合即通关。', '撐過全部回合即通關。', '介绍弹窗正文 4'),
]


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def col_letter(i):
    s = ''
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


def cell(ref, val):
    return '<c r="%s" t="inlineStr"><is><t xml:space="preserve">%s</t></is></c>' % (ref, esc(val))


def existing_ids(sheet_xml):
    """提取每行列 B 的文本值（= id 主键）。"""
    ids = set()
    for row_m in re.finditer(r'<row r="(\d+)"[^>]*>(.*?)</row>', sheet_xml, re.S):
        body = row_m.group(2)
        m = re.search(r'<c r="B\d+"[^>]*><is><t[^>]*>(.*?)</t></is></c>', body, re.S)
        if m:
            ids.add(m.group(1).replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>'))
    return ids


def main():
    with zipfile.ZipFile(XLSX, 'r') as z:
        names = z.namelist()
        data = {n: z.read(n) for n in names}

    sheet_name = 'xl/worksheets/sheet1.xml'
    sheet = data[sheet_name].decode('utf-8')

    have = existing_ids(sheet)
    todo = [r for r in NEW_ROWS if r[0] not in have]
    if not todo:
        print('所有新词条均已存在，无需追加')
        return

    # 现有最大行号
    max_row = 0
    for m in re.finditer(r'<row r="(\d+)"', sheet):
        max_row = max(max_row, int(m.group(1)))
    print('当前最大行号:', max_row, '；已有词条:', len(have), '；待追加:', len(todo))

    rows_xml = []
    ri = max_row
    for (key, zh_hans, zh_hant, comment) in todo:
        ri += 1
        full = (key, key, zh_hans, zh_hant, comment)  # id == en（英文原文即主键）
        rows_xml.append('<row r="%d">' % ri + ''.join(
            cell(col_letter(ci + 1) + str(ri), v) for ci, v in enumerate(full)) + '</row>')
        print('  +', key)

    sheet_new = sheet.replace('</sheetData>', ''.join(rows_xml) + '</sheetData>')
    if sheet_new == sheet:
        raise SystemExit('未找到 </sheetData>，表格式与预期不符，中止')

    shutil.copyfile(XLSX, BACKUP)
    print('已备份原表 →', BACKUP)

    data[sheet_name] = sheet_new.encode('utf-8')
    with zipfile.ZipFile(XLSX, 'w', zipfile.ZIP_DEFLATED) as z:
        for n in names:
            z.writestr(n, data[n])
    print('written', XLSX, '新增行数:', len(todo))


if __name__ == '__main__':
    main()
