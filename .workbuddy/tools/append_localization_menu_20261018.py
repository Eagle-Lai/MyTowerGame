# -*- coding: utf-8 -*-
"""向 [家用D] 工程的 Luban 多语言表幂等追加 2026-10-18 的新词条（只加不改）。

背景：HUD 右上角 Btn_Intro 的职责从"游戏介绍"改成"暂停菜单"，文案随之改为 Menu；
      暂停菜单在未暂停状态下打开时，标题也用 Menu（暂停状态下仍是 Game Paused）。

用法：
    python .workbuddy/tools/append_localization_menu_20261018.py

【为什么直接改 xlsx 而不用 gen_localization_table.py 重新生成】
  那个脚本的 ROWS 已过期（168 条 vs 现表 351 条），重跑会**丢掉**后来追加的 180+ 条词条。
  所以沿用 20261014 的 append 口径：只往 sheetData 末尾追加行，其余 zip 条目原样保留（幂等）。

【格式口径】与表内既有行一致：数据行只写 B..F 五列（A 列是 Luban 的 ## 标记列），
  非 ASCII 字符写成 &#NNNN; 数字字符引用（表里既有行就是这么存的）。
跑完后必须在 Unity 里执行「Tools ▸ 塔防 ▸ 3. 导出配置表（Luban）」让词条进 json。
"""
import zipfile
import re
import shutil

XLSX = r'D:/FreedomTower_1/Luban/Config/Datas/Localization.xlsx'
BACKUP = XLSX + '.bak_20261018'

# (id/英文原文, zhHans, zhHant, comment)；id == en（英文原文即查找键）
NEW_ROWS = [
    ('Menu', '菜单', '選單', 'HUD 右上角暂停菜单按钮 / 暂停菜单（未暂停时）标题'),
]


def esc(s):
    out = []
    for ch in s:
        if ch == '&':
            out.append('&amp;')
        elif ch == '<':
            out.append('&lt;')
        elif ch == '>':
            out.append('&gt;')
        elif ord(ch) > 126:
            out.append('&#%d;' % ord(ch))
        else:
            out.append(ch)
    return ''.join(out)


def cell(ref, val):
    return '<c r="%s" t="inlineStr"><is><t xml:space="preserve">%s</t></is></c>' % (ref, esc(val))


def existing_ids(sheet_xml):
    ids = set()
    for row_m in re.finditer(r'<row r="(\d+)"[^>]*>(.*?)</row>', sheet_xml, re.S):
        m = re.search(r'<c r="B\d+"[^>]*><is><t[^>]*>(.*?)</t></is></c>', row_m.group(2), re.S)
        if m:
            ids.add(re.sub(r'&#(\d+);', lambda x: chr(int(x.group(1))), m.group(1)))
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
        print('[loc] 词条已存在，无需追加：%s' % ', '.join(r[0] for r in NEW_ROWS))
        return

    max_row = max(int(m.group(1)) for m in re.finditer(r'<row r="(\d+)"', sheet))
    print('[loc] 现有行数=%d（词条 %d 条）；待追加=%d' % (max_row, len(have), len(todo)))

    rows_xml = []
    ri = max_row
    for (key, zh_hans, zh_hant, comment) in todo:
        ri += 1
        full = (key, key, zh_hans, zh_hant, comment)   # B..F
        rows_xml.append('<row r="%d">' % ri + ''.join(
            cell(chr(66 + ci) + str(ri), v) for ci, v in enumerate(full)) + '</row>')
        print('  + %s（%s / %s）' % (key, zh_hans, zh_hant))

    sheet_new = sheet.replace('</sheetData>', ''.join(rows_xml) + '</sheetData>')
    if sheet_new == sheet:
        raise SystemExit('未找到 </sheetData>，表格式与预期不符，中止')

    # dimension 也要跟着扩，否则部分读取器会按旧范围截断新行
    sheet_new = re.sub(r'<dimension ref="A1:F(\d+)"/>', '<dimension ref="A1:F%d"/>' % ri, sheet_new, count=1)

    shutil.copyfile(XLSX, BACKUP)
    print('[loc] 已备份 →', BACKUP)

    data[sheet_name] = sheet_new.encode('utf-8')
    with zipfile.ZipFile(XLSX, 'w', zipfile.ZIP_DEFLATED) as z:
        for n in names:
            z.writestr(n, data[n])
    print('[loc] 写入完成：%s（+%d 行）' % (XLSX, len(todo)))


if __name__ == '__main__':
    main()
