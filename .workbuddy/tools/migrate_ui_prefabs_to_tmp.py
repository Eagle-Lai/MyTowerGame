"""
把 UI 预制体里的 UGUI Text（以及 UGUI Outline）就地替换为 TextMeshProUGUI。

【为什么用脚本改 YAML 而不是只在 Unity 里跑编辑器工具】
  沙箱无法驱动 Unity，但用户要求"改到所有内容"。
  这里做的是**纯文本结构替换**：把每个 Text 的 MonoBehaviour 块换成 TMP 的块、
  删掉 Outline 块。TMP 块的字段模板严格取自工程里**已存在的** TMP 文本
  （Assets/Scenes/main.unity 内那个 TextMeshProUGUI），因此格式与 TMP 3.0.7 完全一致。

【保留的视觉属性】文本内容 / 字号 / 颜色 / 对齐 / raycastTarget / 粗斜体。
【字体】统一指向工程中文字体 Assets/Font/SiYuanSongTi SDF.asset
        （guid 68c477d3ad7f6e14baa3e8e1239d05de，TMP Settings 的默认字体）。

【幂等】已经是 TMP 的节点没有 UGUI Text 可换，重复执行安全。

用法：
    python .workbuddy/tools/migrate_ui_prefabs_to_tmp.py            # dry-run
    python .workbuddy/tools/migrate_ui_prefabs_to_tmp.py --apply    # 写入（自动备份）
"""
import io, os, re, sys, shutil, time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UI_DIR = os.path.join(ROOT, 'Assets', 'Prefabs', 'UI')

PREFABS = ['HudView', 'TipsView', 'TowerInfoView', 'SelectView', 'PauseView', 'SettingView']

UGUI_TEXT_GUID = '5f7201a12d95ffc409449d95f23cf332'   # UnityEngine.UI.Text
UGUI_OUTLINE_GUID = 'e19747de3f5aca642ab2be37e372fb86'  # UnityEngine.UI.Outline
TMP_GUID = 'f4688fdb7df04437aeb418b961361dc5'          # TMPro.TextMeshProUGUI
FONT_ASSET_GUID = '68c477d3ad7f6e14baa3e8e1239d05de'   # SiYuanSongTi SDF

# UGUI TextAnchor -> (HorizontalAlignmentOptions, VerticalAlignmentOptions)
#   Left=0x1 Center=0x2 Right=0x4 ; Top=0x100 Middle=0x200 Bottom=0x400
ALIGN_MAP = {
    0: (0x1, 0x100),   # UpperLeft
    1: (0x2, 0x100),   # UpperCenter
    2: (0x4, 0x100),   # UpperRight
    3: (0x1, 0x200),   # MiddleLeft
    4: (0x2, 0x200),   # MiddleCenter
    5: (0x4, 0x200),   # MiddleRight
    6: (0x1, 0x400),   # LowerLeft
    7: (0x2, 0x400),   # LowerCenter
    8: (0x4, 0x400),   # LowerRight
}


def split_blocks(text):
    """把 YAML 拆成 (header, [(doc_header, body), ...])，保留能否原样拼回。"""
    parts = re.split(r'(?m)^(?=--- !u!)', text)
    return parts


def find_block(parts, guid, cls='114'):
    for i, p in enumerate(parts):
        if p.startswith('--- !u!%s ' % cls) and ('guid: %s' % guid) in p:
            return i
    return -1


def parse_mb(body):
    """解析 UGUI Text / MonoBehaviour 的关键字段。"""

    def g(pat, default=None):
        m = re.search(pat, body)
        return m.group(1) if m else default

    out = {}
    out['gameObject'] = g(r'm_GameObject: \{fileID: (-?\d+)\}')
    out['color'] = g(r'\n  m_Color: (\{[^}]*\})')
    out['raycast'] = g(r'\n  m_RaycastTarget: (\d+)', '1')
    out['text'] = g(r'\n  m_Text: (.*)')          # 可能是空串
    # m_FontData 子字段
    fd_start = body.find('m_FontData:')
    fd = body[fd_start:] if fd_start >= 0 else ''

    def gf(pat, default='0'):
        m = re.search(pat, fd)
        return m.group(1) if m else default

    out['fontSize'] = gf(r'm_FontSize: (\d+)', '36')
    out['fontStyle'] = gf(r'm_FontStyle: (\d+)', '0')
    out['alignment'] = int(gf(r'm_Alignment: (\d+)', '4'))
    return out


def tmp_block(anchor, src):
    """生成 TextMeshProUGUI 的 MonoBehaviour 块（字段模板取自工程既有 TMP 文本）。"""
    h, v = ALIGN_MAP.get(src['alignment'], (0x2, 0x200))
    # UGUI HorizontalWrapMode: Wrap=0, Overflow=1 -> TMP enableWordWrapping 反之
    # 原生成器里所有文本都设了不换行（Overflow），这里统一给 0（不换行），
    # 需要换行的少数节点由迁移后的代码/生成器再打开。
    enable_wrap = 0
    font_style = src['fontStyle']
    return f"""--- !u!114 &{anchor}
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: {src['gameObject']}}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: {TMP_GUID}, type: 3}}
  m_Name: 
  m_EditorClassIdentifier: 
  m_Material: {{fileID: 0}}
  m_Color: {src['color']}
  m_RaycastTarget: {src['raycast']}
  m_RaycastPadding: {{x: 0, y: 0, z: 0, w: 0}}
  m_Maskable: 1
  m_OnCullStateChanged:
    m_PersistentCalls:
      m_Calls: []
  m_text: {src['text']}
  m_isRightToLeft: 0
  m_fontAsset: {{fileID: 11400000, guid: {FONT_ASSET_GUID}, type: 2}}
  m_sharedMaterial: {{fileID: 0}}
  m_fontSharedMaterials: []
  m_fontMaterial: {{fileID: 0}}
  m_fontMaterials: []
  m_fontColor32:
    serializedVersion: 2
    rgba: 4294967295
  m_fontColor: {src['color']}
  m_enableVertexGradient: 0
  m_colorMode: 3
  m_fontColorGradient:
    topLeft: {{r: 1, g: 1, b: 1, a: 1}}
    topRight: {{r: 1, g: 1, b: 1, a: 1}}
    bottomLeft: {{r: 1, g: 1, b: 1, a: 1}}
    bottomRight: {{r: 1, g: 1, b: 1, a: 1}}
  m_fontColorGradientPreset: {{fileID: 0}}
  m_spriteAsset: {{fileID: 0}}
  m_tintAllSprites: 0
  m_StyleSheet: {{fileID: 0}}
  m_TextStyleHashCode: -1183493901
  m_overrideHtmlColors: 0
  m_faceColor:
    serializedVersion: 2
    rgba: 4294967295
  m_fontSize: {src['fontSize']}
  m_fontSizeBase: {src['fontSize']}
  m_fontWeight: 400
  m_enableAutoSizing: 0
  m_fontSizeMin: 18
  m_fontSizeMax: 72
  m_fontStyle: {font_style}
  m_HorizontalAlignment: {h}
  m_VerticalAlignment: {v}
  m_textAlignment: 65535
  m_characterSpacing: 0
  m_wordSpacing: 0
  m_lineSpacing: 0
  m_lineSpacingMax: 0
  m_paragraphSpacing: 0
  m_charWidthMaxAdj: 0
  m_enableWordWrapping: {enable_wrap}
  m_wordWrappingRatios: 0.4
  m_overflowMode: 0
  m_linkedTextComponent: {{fileID: 0}}
  parentLinkedComponent: {{fileID: 0}}
  m_enableKerning: 1
  m_enableExtraPadding: 0
  checkPaddingRequired: 0
  m_isRichText: 1
  m_parseCtrlCharacters: 1
  m_isOrthographic: 1
  m_isCullingEnabled: 0
  m_horizontalMapping: 0
  m_verticalMapping: 0
  m_uvLineOffset: 0
  m_geometrySortingOrder: 0
  m_IsTextObjectScaleStatic: 0
  m_VertexBufferAutoSizeReduction: 0
  m_useMaxVisibleDescender: 1
  m_pageToDisplay: 1
  m_margin: {{x: 0, y: 0, z: 0, w: 0}}
  m_isUsingLegacyAnimationComponent: 0
  m_isVolumetricText: 0
  m_hasFontAssetChanged: 0
  m_baseMaterial: {{fileID: 0}}
  m_maskOffset: {{x: 0, y: 0, z: 0, w: 0}}
"""


def collect_outline_anchors(text):
    """先扫出所有 UGUI Outline 块的 fileID（anchor），供后续从 m_Component 里剔除。"""
    anchors = set()
    for m in re.finditer(r'--- !u!114 &(-?\d+)\n(.*?)(?=\n--- !u!|\Z)', text, re.S):
        if ('guid: %s' % UGUI_OUTLINE_GUID) in m.group(2):
            anchors.add(m.group(1))
    return anchors


def strip_component_refs(text, anchors):
    """从 GameObject 的 m_Component 列表里移除对这些 fileID 的引用。"""
    for a in anchors:
        text = re.sub(r'(?m)^  - component: \{fileID: %s\}\n' % re.escape(a), '', text)
    return text


def migrate_text(text):
    parts = split_blocks(text)
    changed_text = 0
    changed_outline = 0
    out = []
    for p in parts:
        if p.startswith('--- !u!114 ') and ('guid: %s' % UGUI_TEXT_GUID) in p:
            # 保留原 anchor（& 后面的 fileID）
            m = re.match(r'--- !u!114 &(-?\d+)', p)
            anchor = m.group(1) if m else '0'
            src = parse_mb(p)
            out.append(tmp_block(anchor, src))
            changed_text += 1
            continue
        if p.startswith('--- !u!114 ') and ('guid: %s' % UGUI_OUTLINE_GUID) in p:
            changed_outline += 1
            continue   # 丢弃 Outline 块
        out.append(p)
    return ''.join(out), changed_text, changed_outline


def main():
    apply = '--apply' in sys.argv
    total_t = total_o = 0
    for name in PREFABS:
        path = os.path.join(UI_DIR, name + '.prefab')
        if not os.path.exists(path):
            print('  [跳过] 不存在', path)
            continue
        s = io.open(path, encoding='utf-8').read()
        if UGUI_TEXT_GUID not in s:
            print('  [跳过] %s 已是 TMP 或无 UGUI Text' % name)
            continue
        outline_anchors = collect_outline_anchors(s)
        new, ct, co = migrate_text(s)
        new = strip_component_refs(new, outline_anchors)
        # 组件清单里的 Outline 组件引用也要一并去掉（否则 GameObject 指向已删块）
        print('  %s: Text %d 个 → TMP，删除 Outline %d 个' % (name, ct, co))
        total_t += ct
        total_o += co
        if apply:
            bak = path + '.bak_' + time.strftime('%Y%m%d_%H%M%S')
            shutil.copy2(path, bak)
            io.open(path, 'w', encoding='utf-8').write(new)
            print('        已写入（备份 %s）' % os.path.basename(bak))
    print('合计：%d 个 Text → TMP，%d 个 Outline 删除' % (total_t, total_o))
    if not apply:
        print('（dry-run，未写入。加 --apply 执行）')


if __name__ == '__main__':
    main()
