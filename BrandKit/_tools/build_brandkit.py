# -*- coding: utf-8 -*-
"""
Freedom Tower / 自由人塔防 —— 品牌视觉资源生成器
--------------------------------------------------
设计取向：矢量几何标志（非 AI 生成位图）。
理由：① 必须与游戏内既有视觉令牌（UISkinArtGenerator 色板）零色差；
      ② 48x48 极小尺寸必须清晰 → 不能有细线/杂点；
      ③ 边缘无锯齿、无水印文字残留 → 4x 超采样 + LANCZOS 下采样；
      ④ 可自由缩放 → 同时导出 SVG 母版。

输出目录：<PROJ>/BrandKit/
"""
import math, os, random, json
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops
import numpy as np

# ============================ 路径 / 常量 ============================
PROJ   = r"D:\FreedomTower_1"
ROOT   = os.path.join(PROJ, "BrandKit")
FONT_CN   = os.path.join(PROJ, r"Assets\Font\SiYuanSongTi.ttf")
EN_FONTS  = [r"C:\Windows\Fonts\segoeuib.ttf", r"C:\Windows\Fonts\seguiemj.ttf",
             r"C:\Windows\Fonts\arialbd.ttf", os.path.join(PROJ, r"Assets\TextMesh Pro\Fonts\LiberationSans.ttf")]
MONO_FONTS= [r"C:\Windows\Fonts\consola.ttf", r"C:\Windows\Fonts\cour.ttf"]

# ---- 品牌色（源自游戏内视觉令牌，不得偏离）----
CYAN     = (0x35, 0xE0, 0xFF)   # 主色 · 科技青
CYAN_LT  = (0xDF, 0xFA, 0xFF)
CYAN_MD  = (0x5A, 0xE8, 0xFF)
CYAN_DK  = (0x0E, 0x6E, 0x93)
CYAN_DEEP= (0x07, 0x33, 0x47)
ICE      = (0x7D, 0xE8, 0xFF)
GOLD     = (0xFF, 0xC9, 0x4D)
GOLD_DK  = (0xB8, 0x84, 0x18)
RED      = (0xFF, 0x4D, 0x5E)
RED_DK   = (0x8E, 0x1F, 0x2C)
FIRE     = (0xFF, 0x7A, 0x29)
STEEL    = (0x9F, 0xB3, 0xC8)
STEEL_DK = (0x5E, 0x73, 0x96)
SLATE    = (0x1C, 0x25, 0x32)
SLATE_MD = (0x25, 0x2F, 0x40)
STROKE   = (0x3A, 0x4A, 0x63)
PANEL_T  = (0x2A, 0x34, 0x44)
PANEL_M  = (0x1B, 0x23, 0x30)
VOID     = (0x08, 0x0B, 0x12)
L0       = (0x0D, 0x11, 0x19)
TXT      = (0xE8, 0xF0, 0xFA)
INK      = (0x16, 0x20, 0x2E)

N = "自由人塔防"
EN= "FREEDOM TOWER"
TAG = "自由布防 · 塑路制胜"

# ============================ 几何（1000 单位坐标系）============================
CX = CY = 500.0
HEX_R      = 362.0
HEX_IN_R   = 300.0
BR_INSET   = 92.0
BR_ARM     = 172.0
BR_W       = 22.0
CRYSTAL    = [(432, 372), (568, 372), (624, 476), (500, 668), (376, 476)]
CRY_TABLE_L, CRY_TABLE_R = (432, 372), (568, 372)
CRY_GIRD_L,  CRY_GIRD_R  = (376, 476), (624, 476)
CRY_CULET                = (500, 668)
CHEV_L = [(286, 466), (334, 500), (286, 534)]
CHEV_R = [(714, 466), (666, 500), (714, 534)]
SPARK_C, SPARK_R, SPARK_R2 = (500, 140), 60.0, 16.0


def hexagon(cx, cy, r, rot=-90.0):
    return [(cx + r * math.cos(math.radians(rot + 60 * i)),
             cy + r * math.sin(math.radians(rot + 60 * i))) for i in range(6)]


def spark_pts(c, r1, r2):
    p = []
    for i in range(4):
        a = math.radians(90 * i - 90)
        p.append((c[0] + r1 * math.cos(a), c[1] + r1 * math.sin(a)))
        b = math.radians(90 * i - 45)
        p.append((c[0] + r2 * math.cos(b), c[1] + r2 * math.sin(b)))
    return p


# ============================ 通用绘图工具 ============================
def vgrad(w, h, stops, alpha=255):
    pos = np.array([s[0] for s in stops], float)
    cols = np.array([s[1] for s in stops], float)
    t = np.linspace(0, 1, h)
    arr = np.empty((h, w, 4), np.uint8)
    for i in range(3):
        arr[:, :, i] = np.interp(t, pos, cols[:, i])[:, None].astype(np.uint8)
    arr[:, :, 3] = alpha
    return Image.fromarray(arr, "RGBA")


def rgrad(w, h, cx, cy, rx, ry, stops):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    d = np.clip(np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2), 0, 1)
    pos = np.array([s[0] for s in stops], float)
    cols = np.array([s[1] for s in stops], float)
    al = np.array([s[2] for s in stops], float)
    arr = np.empty((h, w, 4), np.uint8)
    for i in range(3):
        arr[:, :, i] = np.interp(d, pos, cols[:, i]).astype(np.uint8)
    arr[:, :, 3] = np.interp(d, pos, al).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


def poly_mask(size, pts, ss=2):
    w, h = size
    m = Image.new("L", (w * ss, h * ss), 0)
    ImageDraw.Draw(m).polygon([(x * ss, y * ss) for x, y in pts], fill=255)
    return m.resize((w, h), Image.LANCZOS)


def grad_into(base, size, pts, stops, alpha=255):
    g = vgrad(size[0], size[1], stops, alpha)
    m = poly_mask(size, pts)
    g.putalpha(ImageChops.multiply(g.getchannel("A"), m))
    base.alpha_composite(g)


def glow_from(layer_size, pts, color, blur, alpha, ss=2):
    w, h = layer_size
    m = Image.new("L", (w * ss, h * ss), 0)
    ImageDraw.Draw(m).polygon([(x * ss, y * ss) for x, y in pts], fill=alpha)
    m = m.resize((w, h), Image.LANCZOS).filter(ImageFilter.GaussianBlur(blur))
    g = Image.new("RGBA", layer_size, color + (0,))
    g.putalpha(m)
    return g


def find_font(cands):
    for c in cands:
        if os.path.exists(c):
            return c
    return None


EN_PATH   = find_font(EN_FONTS)
MONO_PATH = find_font(MONO_FONTS)


def font(path, size):
    return ImageFont.truetype(path, int(size))


def text_w(f, s, spacing=0.0):
    if not s:
        return 0.0
    return sum(f.getlength(ch) for ch in s) + spacing * (len(s) - 1)


def draw_spaced(d, cx, cy, s, f, fill, spacing=0.0, stroke_w=0, stroke_fill=None, anchor="mm"):
    """按字距逐字绘制。anchor: 'mm' 以 cx 为水平中心；'left' 以 cx 为左起点。"""
    total = text_w(f, s, spacing)
    x = cx - total / 2.0 if anchor == "mm" else cx
    for ch in s:
        d.text((x, cy), ch, font=f, fill=fill, anchor="lm",
               stroke_width=stroke_w, stroke_fill=stroke_fill)
        x += f.getlength(ch) + spacing


def ensure(p):
    os.makedirs(p, exist_ok=True)
    return p


def save(img, folder, name):
    ensure(folder)
    p = os.path.join(folder, name)
    img.save(p)
    print("  +", os.path.relpath(p, ROOT))
    return p


# ============================ 标志绘制 ============================
def mark_layer(size, style="full", k_extra=1.0, show_brackets=None, show_chev=None,
               show_spark=None, light_plate=False, pad=0.0):
    """返回 (size,size) RGBA，标志居中，透明背景。style: full/symbol/mono_white/mono_dark"""
    ss = 4
    S = int(size * ss)
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    k = S / 1000.0 * k_extra
    off = (S - 1000.0 * k) / 2.0

    def T(pts):
        return [(x * k + off, y * k + off) for x, y in pts]

    def V(v):
        return v * k

    mono = style in ("mono_white", "mono_dark")
    mw = (255, 255, 255) if style == "mono_white" else (0x0D, 0x11, 0x19)

    def UW(base_units, min_px):
        """描边宽度单位换算：小尺寸下保证不小于 min_px 个输出像素，
        否则 48px 图标里六边形描边会细到 0.7px 而糊掉。"""
        return max(base_units, min_px * 1000.0 / max(1, size))
    if show_brackets is None:
        show_brackets = (style == "full")
    if show_chev is None:
        show_chev = False   # 汇聚箭头已弃用：形似 "< >" 文本符号，改用纯几何收束
    if show_spark is None:
        show_spark = style in ("full", "symbol")

    hexo = hexagon(CX, CY, HEX_R)
    hexi = hexagon(CX, CY, HEX_IN_R)

    # ---- 外发光 ----
    if not mono:
        gl = glow_from((S, S), T(hexo), CYAN, V(26), 150, ss=1)
        img.alpha_composite(gl)
        gl2 = glow_from((S, S), T([(x, y) for x, y in CRYSTAL]), CYAN_LT, V(34), 170, ss=1)
        img.alpha_composite(gl2)
    else:
        gl = glow_from((S, S), T(hexo), mw, V(16), 90, ss=1)
        img.alpha_composite(gl)

    # ---- 索敌框（四角）----
    if show_brackets:
        i0, a = BR_INSET, BR_ARM
        bw = V(BR_W)
        br_c = CYAN if not mono else mw
        corners = [((i0, i0), (1, 1)), ((1000 - i0, i0), (-1, 1)),
                   ((i0, 1000 - i0), (1, -1)), ((1000 - i0, 1000 - i0), (-1, -1))]
        for (cx0, cy0), (sx, sy) in corners:
            d.line(T([(cx0 + sx * a, cy0), (cx0, cy0), (cx0, cy0 + sy * a)]),
                   fill=br_c, width=int(bw), joint="curve")

    # ---- 六边形基座 ----
    if mono:
        d.polygon(T(hexo), outline=mw, width=int(V(UW(20, 2.2))))
        d.polygon(T(hexi), outline=mw, width=int(V(UW(6, 1.0))))
    else:
        if light_plate:
            plate = [(0.0, INK), (1.0, (0x0D, 0x14, 0x1E))]
        else:
            plate = [(0.0, PANEL_T), (0.52, PANEL_M), (1.0, (0x14, 0x1A, 0x24))]
        grad_into(img, (S, S), T(hexo), plate)
        d.line(T(hexo + [hexo[0]]), fill=CYAN, width=int(V(UW(15, 1.7))), joint="curve")
        d.line(T(hexi + [hexi[0]]), fill=STROKE, width=int(V(UW(6, 1.0))), joint="curve")
        # 内圈细青线（大尺寸细节）
        d.line(T(hexagon(CX, CY, HEX_IN_R - 26) + [hexagon(CX, CY, HEX_IN_R - 26)[0]]),
               fill=(0x35, 0xE0, 0xFF, 70), width=int(max(1, V(3))), joint="curve")

    # ---- 水晶核心 ----
    if mono:
        d.polygon(T(CRYSTAL), fill=mw)
    else:
        grad_into(img, (S, S), T(CRYSTAL),
                  [(0.0, CYAN_LT), (0.30, CYAN_MD), (0.62, CYAN), (1.0, CYAN_DK)])
        # 棱面线
        fl = (0x06, 0x1C, 0x26, 150)
        for seg in [[CRY_TABLE_L, CRY_GIRD_L], [CRY_TABLE_R, CRY_GIRD_R],
                    [CRY_GIRD_L, CRY_CULET], [CRY_GIRD_R, CRY_CULET],
                    [CRY_TABLE_L, CRY_CULET], [CRY_TABLE_R, CRY_CULET],
                    [CRY_GIRD_L, CRY_GIRD_R]]:
            d.line(T(seg), fill=fl, width=int(max(1, V(5))))
        # 台面高光
        d.line(T([(CRY_TABLE_L[0] + 6, CRY_TABLE_L[1] + 10), (CRY_TABLE_R[0] - 6, CRY_TABLE_R[1] + 10)]),
               fill=(255, 255, 255, 190), width=int(max(1, V(7))))
        d.line(T([CRYSTAL[0], CRYSTAL[1]]), fill=CYAN_LT, width=int(max(1, V(UW(9, 1.2)))), joint="curve")

    # ---- 汇聚箭头（路径塑形语义）----
    if show_chev:
        cc = CYAN if not mono else mw
        al = 255 if mono else 200
        for ch in (CHEV_L, CHEV_R):
            d.line(T(ch), fill=cc + (al,), width=int(V(16)), joint="curve")

    # ---- 金星（星级 / 荣耀）----
    if show_spark:
        col = GOLD if not mono else mw
        d.polygon(T(spark_pts(SPARK_C, SPARK_R, SPARK_R2)), fill=col + (255,))
        if not mono:
            d.line(T(spark_pts(SPARK_C, SPARK_R, SPARK_R2) + [spark_pts(SPARK_C, SPARK_R, SPARK_R2)[0]]),
                   fill=(255, 0xF2, 0xC0, 200), width=int(max(1, V(2))))

    return img.resize((size, size), Image.LANCZOS)


# ============================ 图标背景 ============================
def squircle_mask(size, n=4.6, ss=2):
    S = int(size * ss)
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float64)
    a = (S - 1) / 2.0
    d = (np.abs((xx - a) / a) ** n + np.abs((yy - a) / a) ** n)
    m = np.clip((1.0 - d) * 40 + 0.5, 0, 1) * 255
    return Image.fromarray(m.astype(np.uint8), "L").resize((size, size), Image.LANCZOS)


def round_mask(size, radius_ratio=0.225, ss=2, circle=False):
    S = int(size * ss)
    m = Image.new("L", (S, S), 0)
    dr = ImageDraw.Draw(m)
    if circle:
        dr.ellipse([0, 0, S - 1, S - 1], fill=255)
    else:
        dr.rounded_rectangle([0, 0, S - 1, S - 1], radius=int(S * radius_ratio), fill=255)
    return m.resize((size, size), Image.LANCZOS)


def hexgrid_layer(w, h, r, color, alpha, offset=(0, 0), ss=2):
    W, H = w * ss, h * ss
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    R = r * ss
    dx = math.sqrt(3) * R
    dy = 1.5 * R
    rows = int(H / dy) + 3
    cols = int(W / dx) + 3
    for j in range(-1, rows):
        for i in range(-1, cols):
            x = i * dx + (dx / 2 if j % 2 else 0) + offset[0] * ss
            y = j * dy + offset[1] * ss
            pts = hexagon(x, y, R)
            d.line(pts + [pts[0]], fill=color + (alpha,), width=max(1, int(1.6 * ss)), joint="curve")
    return lay.resize((w, h), Image.LANCZOS)


def starfield(w, h, count=260, seed=7, alpha_scale=1.0):
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    rnd = random.Random(seed)
    for _ in range(count):
        x = rnd.random() * w
        y = rnd.random() * h
        s = rnd.choice([0.8, 1.0, 1.2, 1.6, 2.2])
        a = int(rnd.uniform(40, 210) * alpha_scale)
        c = CYAN_LT if rnd.random() < 0.18 else TXT
        d.ellipse([x - s, y - s, x + s, y + s], fill=c + (a,))
    for _ in range(10):
        x = rnd.random() * w
        y = rnd.random() * h
        s = rnd.uniform(2.5, 4.5)
        g = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(g).ellipse([x - s, y - s, x + s, y + s], fill=CYAN + (200,))
        lay.alpha_composite(g.filter(ImageFilter.GaussianBlur(6)))
    return lay


def icon_bg(size, mask=None, seed=3):
    base = vgrad(size, size, [(0.0, (0x1A, 0x24, 0x34)), (0.5, (0x0E, 0x14, 0x1F)), (1.0, (0x06, 0x09, 0x0F))])
    base.alpha_composite(rgrad(size, size, size * 0.5, size * 0.36, size * 0.78, size * 0.78,
                               [(0.0, CYAN, 74), (0.55, CYAN, 20), (1.0, CYAN, 0)]))
    g = rgrad(size, size, size * 0.5, size * 0.5, size * 0.7, size * 0.7,
              [(0.0, CYAN, 0), (0.72, CYAN, 0), (1.0, (0x02, 0x04, 0x08), 190)])
    base.alpha_composite(g)
    base.alpha_composite(hexgrid_layer(size, size, size * 0.085, STEEL_DK, 34, (size * 0.02, size * 0.01)))
    base.alpha_composite(starfield(size, size, int(size * 0.55), seed=seed, alpha_scale=0.9))
    if mask is not None:
        base.putalpha(ImageChops.multiply(base.getchannel("A"), mask))
    return base


def fit_mark(size, style="symbol", fill=0.86, **kw):
    """渲染标记后按有效像素边界裁剪，再等比缩放到画布的 fill 比例并居中。
    保证不同变体在给定方框内占位一致、不被发光虚边撑开。"""
    base = int(min(1024, max(448, size * 1.4)))
    big = mark_layer(base, style, **kw)
    a = big.getchannel("A").point(lambda v: 255 if v > 22 else 0)
    bb = a.getbbox()
    crop = big.crop(bb)
    sc = fill * size / max(crop.width, crop.height)
    nw, nh = max(1, int(round(crop.width * sc))), max(1, int(round(crop.height * sc)))
    crop = crop.resize((nw, nh), Image.LANCZOS)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.alpha_composite(crop, ((size - nw) // 2, (size - nh) // 2))
    return out


def compose_icon(size, mask=None, inner_scale=0.80, seed=3):
    bg = icon_bg(size, None, seed=seed)
    m = fit_mark(size, "icon_core", fill=inner_scale,
                 show_brackets=False, show_chev=False, show_spark=True)
    bg.alpha_composite(m, (0, 0))
    if mask is not None:
        bg.putalpha(ImageChops.multiply(bg.getchannel("A"), mask))
    return bg


# ============================ 文字排版 ============================
def lockup_h(mark_px, gap_ratio=0.26, title_ratio=0.40, sub_ratio=0.135, on_light=False):
    W = int(mark_px * 3.55)
    H = mark_px
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    m = fit_mark(mark_px, "symbol", fill=1.0, show_spark=True, light_plate=on_light)
    img.alpha_composite(m, (0, 0))
    tx = mark_px + int(mark_px * gap_ratio)
    fcn = font(FONT_CN, mark_px * title_ratio)
    fen = font(EN_PATH, mark_px * sub_ratio) if EN_PATH else fcn
    title_col = INK if on_light else TXT
    sub_col   = (0x3A, 0x4A, 0x63) if on_light else CYAN
    cy1 = H * 0.42
    cy2 = H * 0.74
    total1 = text_w(fcn, N, mark_px * 0.02)
    draw_spaced(d, tx + total1 / 2 + 4, cy1, N, fcn, title_col, mark_px * 0.02,
                stroke_w=max(1, int(mark_px * 0.006)),
                stroke_fill=(0x00, 0x00, 0x00, 120) if not on_light else None)
    total2 = text_w(fen, EN, mark_px * 0.085)
    draw_spaced(d, tx + total2 / 2 + 4, cy2, EN, fen, sub_col, mark_px * 0.085)
    return img


def lockup_v(mark_px, title_ratio=0.30, sub_ratio=0.095, on_light=False, with_tag=False):
    W = int(mark_px * 2.35)
    H = int(mark_px * 1.90) if not with_tag else int(mark_px * 2.08)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    m = fit_mark(mark_px, "symbol", fill=1.0, show_spark=True, light_plate=on_light)
    img.alpha_composite(m, ((W - mark_px) // 2, 0))
    fcn = font(FONT_CN, mark_px * title_ratio)
    fen = font(EN_PATH, mark_px * sub_ratio) if EN_PATH else fcn
    title_col = INK if on_light else TXT
    sub_col   = (0x3A, 0x4A, 0x63) if on_light else CYAN
    y1 = mark_px + mark_px * 0.34
    draw_spaced(d, W / 2, y1, N, fcn, title_col, mark_px * 0.015,
                stroke_w=max(1, int(mark_px * 0.005)),
                stroke_fill=(0, 0, 0, 120) if not on_light else None)
    y2 = y1 + mark_px * 0.30
    draw_spaced(d, W / 2, y2, EN, fen, sub_col, mark_px * 0.095)
    if with_tag:
        ftg = font(FONT_CN, mark_px * 0.078)
        draw_spaced(d, W / 2, y2 + mark_px * 0.235, TAG, ftg,
                    (0x5E, 0x73, 0x96) if not on_light else (0x5E, 0x73, 0x96), mark_px * 0.03)
    return img


# ============================ SVG 母版 ============================
def _pstr(pts):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)


def svg_mark(style="full", size=1000):
    hexo, hexi = hexagon(CX, CY, HEX_R), hexagon(CX, CY, HEX_IN_R)
    hexi2 = hexagon(CX, CY, HEX_IN_R - 26)
    mono = style in ("mono_white", "mono_dark")
    mw = "#FFFFFF" if style == "mono_white" else "#0D1119"
    full = style == "full"
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000" width="{size}" height="{size}">']
    out.append('<defs>')
    out.append('<linearGradient id="plate" x1="0" y1="0" x2="0" y2="1">'
               '<stop offset="0" stop-color="#2A3444"/><stop offset="0.52" stop-color="#1B2330"/>'
               '<stop offset="1" stop-color="#141A24"/></linearGradient>')
    out.append('<linearGradient id="gem" x1="0" y1="0" x2="0" y2="1">'
               '<stop offset="0" stop-color="#DFFAFF"/><stop offset="0.30" stop-color="#5AE8FF"/>'
               '<stop offset="0.62" stop-color="#35E0FF"/><stop offset="1" stop-color="#0E6E93"/></linearGradient>')
    out.append('<filter id="glow" x="-60%" y="-60%" width="220%" height="220%">'
               '<feDropShadow dx="0" dy="0" stdDeviation="12" flood-color="#35E0FF" flood-opacity="0.85"/></filter>')
    out.append('</defs>')
    if mono:
        out.append(f'<polygon points="{_pstr(hexo)}" fill="none" stroke="{mw}" stroke-width="20"/>')
        out.append(f'<polygon points="{_pstr(hexi)}" fill="none" stroke="{mw}" stroke-width="6"/>')
        out.append(f'<polygon points="{_pstr(CRYSTAL)}" fill="{mw}"/>')
    else:
        out.append(f'<polygon points="{_pstr(hexo)}" fill="url(#plate)" stroke="#35E0FF" stroke-width="15"/>')
        out.append(f'<polygon points="{_pstr(hexi)}" fill="none" stroke="#3A4A63" stroke-width="6"/>')
        out.append(f'<polygon points="{_pstr(hexi2)}" fill="none" stroke="#35E0FF" stroke-opacity="0.28" stroke-width="3"/>')
        out.append(f'<polygon points="{_pstr(CRYSTAL)}" fill="url(#gem)" filter="url(#glow)"/>')
        for seg in [[CRY_TABLE_L, CRY_GIRD_L], [CRY_TABLE_R, CRY_GIRD_R],
                    [CRY_GIRD_L, CRY_CULET], [CRY_GIRD_R, CRY_CULET],
                    [CRY_TABLE_L, CRY_CULET], [CRY_TABLE_R, CRY_CULET], [CRY_GIRD_L, CRY_GIRD_R]]:
            out.append(f'<line x1="{seg[0][0]}" y1="{seg[0][1]}" x2="{seg[1][0]}" y2="{seg[1][1]}" stroke="#061C26" stroke-opacity="0.6" stroke-width="5"/>')
        out.append(f'<line x1="438" y1="382" x2="562" y2="382" stroke="#FFFFFF" stroke-opacity="0.75" stroke-width="7"/>')
    if full:
        i0, a = BR_INSET, BR_ARM
        for (cx0, cy0), (sx, sy) in [((i0, i0), (1, 1)), ((1000 - i0, i0), (-1, 1)),
                                     ((i0, 1000 - i0), (1, -1)), ((1000 - i0, 1000 - i0), (-1, -1))]:
            out.append(f'<path d="M{cx0+sx*a:.0f} {cy0:.0f} H{cx0:.0f} V{cy0+sy*a:.0f}" fill="none" stroke="{CYAN if not mono else mw}" stroke-width="22" stroke-linecap="round"/>')
        pass
    if style in ("full", "symbol"):
        out.append(f'<polygon points="{_pstr(spark_pts(SPARK_C, SPARK_R, SPARK_R2))}" fill="#FFC94D"/>')
    out.append('</svg>')
    return "\n".join(out)


# ============================ 主流程 ============================
def build():
    random.seed(11)
    APP   = os.path.join(ROOT, "01_AppIcon")
    KV    = os.path.join(ROOT, "02_KeyVisual")
    ING   = os.path.join(ROOT, "03_InGame")
    AUX   = os.path.join(ROOT, "04_Auxiliary")
    SVG   = os.path.join(ROOT, "05_Vector_SVG")
    GUIDE = os.path.join(ROOT, "00_Guidelines")
    for p in (APP, KV, ING, AUX, SVG, GUIDE):
        ensure(p)

    print("[1/6] APP 图标 ...")
    sq = squircle_mask(1024)
    master = compose_icon(1024, mask=None, inner_scale=0.80)
    save(master, APP, "Icon_Master_1024.png")
    save(master.resize((512, 512), Image.LANCZOS), APP, "Icon_Master_512.png")
    ios = compose_icon(1024, mask=sq, inner_scale=0.75)
    save(ios, APP, "Icon_iOS_1024_Squircle.png")
    save(compose_icon(512, mask=round_mask(512, circle=True), inner_scale=0.72), APP, "Icon_Android_Round_512.png")
    save(compose_icon(512, mask=round_mask(512, 0.225), inner_scale=0.77), APP, "Icon_Android_Square_512.png")
    # 自适应图标：前景为透明层（内容位于中央安全区）
    fg = fit_mark(432, "icon_core", fill=0.60, show_brackets=False, show_chev=False, show_spark=True)
    save(fg, APP, "Icon_Adaptive_Foreground_432.png")
    bgl = Image.new("RGBA", (432, 432), (0, 0, 0, 0))
    bgl.alpha_composite(icon_bg(432, None, seed=3))
    save(bgl, APP, "Icon_Adaptive_Background_432.png")
    mono_ic = fit_mark(432, "mono_white", fill=0.58, show_brackets=False, show_chev=False, show_spark=False)
    save(mono_ic, APP, "Icon_Adaptive_Monochrome_432.png")
    save(fit_mark(512, "symbol", fill=0.88, show_spark=True), APP, "Icon_Transparent_Symbol_512.png")

    SZ = ensure(os.path.join(APP, "Sizes"))
    for s in (180, 167, 152, 144, 120, 114):      # iOS
        save(master.resize((s, s), Image.LANCZOS), SZ, f"iOS_{s}.png")
    for s in (192, 144, 96, 72, 48):              # Android
        save(master.resize((s, s), Image.LANCZOS), SZ, f"Android_{s}.png")
    for s in (48, 32, 16):                        # Web / favicon
        save(master.resize((s, s), Image.LANCZOS), SZ, f"Web_{s}.png")
    # 极小尺寸验证：符号版
    save(fit_mark(48, "symbol", fill=0.92, show_spark=False), SZ, "Symbol_48_Transparent.png")

    print("[2/6] 主视觉 ...")
    for W, H, tag in ((1920, 1080, "1920x1080"), (1080, 1920, "1080x1920")):
        bg = kv_background(W, H, portrait=(H > W))
        save(bg, KV, f"KV_Splash_Background_Only_{tag}.png")
        save(kv_splash(W, H, bg, portrait=(H > W)), KV, f"KV_Splash_{tag}.png")
        save(kv_login(W, H, portrait=(H > W)), KV, f"KV_Login_{tag}.png")
        save(kv_loading(W, H, portrait=(H > W)), KV, f"KV_Loading_{tag}.png")

    print("[3/6] 游戏内图片 ...")
    save(ing_logo_plate(1400, 520), ING, "InGame_LogoPlate_1400x520.png")
    save(ing_logo_plate(700, 260), ING, "InGame_LogoPlate_700x260.png")
    save(ing_loading_emblem(512), ING, "InGame_LoadingEmblem_512.png")
    save(ing_divider(1600, 120, CYAN), ING, "InGame_Divider_Cyan_1600.png")
    save(ing_pause(1200, 900), ING, "InGame_PauseDecoration_1200x900.png")
    save(ing_result(1400, 420, win=True), ING, "InGame_Result_Win_1400x420.png")
    save(ing_result(1400, 420, win=False), ING, "InGame_Result_Lose_1400x420.png")
    save(ing_watermark(640, 200), ING, "InGame_Watermark_640x200.png")
    save(ing_corner_badge(320), ING, "InGame_CornerBadge_320.png")

    print("[4/6] 辅助资源 ...")
    save(lockup_h(360), AUX, "Logo_Horizontal_OnDark.png")
    save(lockup_h(360, on_light=True), AUX, "Logo_Horizontal_OnLight.png")
    save(lockup_v(360, with_tag=True), AUX, "Logo_Vertical_OnDark.png")
    save(lockup_v(360, with_tag=True, on_light=True), AUX, "Logo_Vertical_OnLight.png")
    save(logo_mono(900, "white"), AUX, "Logo_Monochrome_White.png")
    save(logo_mono(900, "black"), AUX, "Logo_Monochrome_Black.png")
    save(logo_with_bg_h(1920, 540), AUX, "Logo_Horizontal_OnDark_WithBg_1920x540.png")
    save(logo_with_bg_v(1080, 1080), AUX, "Logo_Vertical_OnDark_WithBg_1080.png")
    save(brand_palette(1920, 1200), AUX, "Brand_Palette_1920x1200.png")
    save(brand_typography(1920, 1200), AUX, "Brand_Typography_1920x1200.png")
    save(logo_clearspace(1400, 1000), AUX, "Logo_ClearSpace_MinSize_1400.png")
    save(fit_mark(1024, "symbol", fill=0.94, show_spark=True), AUX, "Logo_Symbol_Cyan_1024.png")

    print("[5/6] SVG 母版 ...")
    for style, fn in (("full", "logo_mark_full.svg"), ("symbol", "logo_mark_symbol.svg"),
                      ("mono_white", "logo_mark_monochrome_white.svg"),
                      ("mono_dark", "logo_mark_monochrome_black.svg")):
        p = os.path.join(SVG, fn)
        with open(p, "w", encoding="utf-8") as f:
            f.write(svg_mark(style))
        print("  +", os.path.relpath(p, ROOT))
    for fn, txt in (("logo_lockup_horizontal.svg", lockup_h_svg()), ("logo_lockup_vertical.svg", lockup_v_svg())):
        p = os.path.join(SVG, fn)
        with open(p, "w", encoding="utf-8") as f:
            f.write(txt)
        print("  +", os.path.relpath(p, ROOT))

    print("[6/6] 完成。")


# ---------- 主视觉绘制 ----------
def kv_background(W, H, portrait=False):
    base = vgrad(W, H, [(0.0, (0x09, 0x0D, 0x15)), (0.42, (0x06, 0x08, 0x0E)), (1.0, (0x03, 0x04, 0x07))])
    cy = H * (0.40 if not portrait else 0.34)
    base.alpha_composite(rgrad(W, H, W * 0.5, cy, W * 0.52, H * 0.52,
                               [(0.0, CYAN, 36), (0.5, CYAN, 11), (1.0, CYAN, 0)]))
    base.alpha_composite(hexgrid_layer(W, H, min(W, H) * 0.085, STEEL_DK, 17, (0, 0)))
    base.alpha_composite(starfield(W, H, int(W * H / 7000), seed=21, alpha_scale=1.0))
    base.alpha_composite(rgrad(W, H, W * 0.5, H * 0.5, W * 0.70, H * 0.70,
                               [(0.0, CYAN, 0), (0.55, CYAN, 0), (1.0, (0x02, 0x03, 0x05), 232)]))
    return base


def kv_splash(W, H, bg=None, portrait=False):
    img = (bg or kv_background(W, H, portrait)).copy()
    s = min(W, H)
    mark_px = int(s * (0.30 if not portrait else 0.42))
    m = fit_mark(mark_px, "full", fill=1.0)
    img.alpha_composite(m, ((W - mark_px) // 2, int(H * (0.13 if not portrait else 0.14))))
    d = ImageDraw.Draw(img)
    fcn = font(FONT_CN, s * (0.085 if not portrait else 0.105))
    y1 = H * (0.60 if not portrait else 0.60)
    draw_spaced(d, W / 2, y1, N, fcn, CYAN, s * 0.012, stroke_w=max(1, int(s * 0.0018)),
                stroke_fill=(0x03, 0x10, 0x16, 200))
    fen = font(EN_PATH, s * (0.026 if not portrait else 0.030)) if EN_PATH else fcn
    y2 = y1 + s * 0.085
    draw_spaced(d, W / 2, y2, EN, fen, STEEL, s * 0.011)
    ftg = font(FONT_CN, s * 0.024)
    draw_spaced(d, W / 2, y2 + s * 0.055, TAG, ftg, STEEL_DK, s * 0.012)
    # 版本号
    fv = font(MONO_PATH, s * 0.017) if MONO_PATH else fen
    if MONO_PATH:
        d.text((W - 44, H - 30), "v1.0.0", font=fv, fill=(0x5E, 0x73, 0x96), anchor="rs")
    return img


def kv_login(W, H, portrait=False):
    img = kv_background(W, H, portrait)
    s = min(W, H)
    mark_px = int(s * (0.20 if not portrait else 0.30))
    m = fit_mark(mark_px, "symbol", fill=1.0)
    mx, my = (W - mark_px) // 2, int(H * (0.13 if not portrait else 0.13))
    img.alpha_composite(m, (mx, my))
    d = ImageDraw.Draw(img)
    fcn = font(FONT_CN, s * (0.062 if not portrait else 0.082))
    y1 = my + mark_px + s * (0.075 if not portrait else 0.06)
    draw_spaced(d, W / 2, y1, N, fcn, TXT, s * 0.010, stroke_w=max(1, int(s * 0.0015)),
                stroke_fill=(0x03, 0x10, 0x16, 200))
    fen = font(EN_PATH, s * (0.021 if not portrait else 0.026)) if EN_PATH else fcn
    draw_spaced(d, W / 2, y1 + s * 0.062, EN, fen, CYAN, s * 0.010)
    draw_spaced(d, W / 2, y1 + s * 0.108, TAG, font(FONT_CN, s * 0.019), STEEL_DK, s * 0.012)
    # 底部战术棋盘装饰（两侧对称，不侵入文字区）
    bs = int(s * 0.34)
    board = tactical_board(bs, seed=5)
    by = int(H * (0.60 if not portrait else 0.64))
    if portrait:
        img.alpha_composite(board, (int(W * 0.30), by))
    else:
        img.alpha_composite(board, (int(W * 0.02), by))
        img.alpha_composite(board.transpose(Image.FLIP_LEFT_RIGHT), (int(W * 0.98) - bs, by))
    return img


def tactical_board(px, seed=5):
    """战术棋盘装饰：六边格 + 高亮路径 + 核心。"""
    img = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    img.alpha_composite(hexgrid_layer(px, px, px * 0.058, STEEL_DK, 46))
    r = px * 0.058
    dx = math.sqrt(3) * r
    dy = 1.5 * r
    path = [(3, 7), (4, 7), (4, 6), (5, 6), (5, 5), (6, 5), (6, 4), (7, 4), (7, 3), (8, 3), (8, 2)]
    d = ImageDraw.Draw(img)
    cells = []
    for (i, j) in path:
        x = px * 0.06 + i * dx + (dx / 2 if j % 2 else 0)
        y = px * 0.06 + j * dy
        cells.append((x, y))
        d.line(hexagon(x, y, r * 0.92) + [hexagon(x, y, r * 0.92)[0]],
               fill=CYAN + (150,), width=int(max(1, r * 0.11)), joint="curve")
    # 核心
    cx, cy = cells[0]
    d.line(hexagon(cx, cy, r * 0.90) + [hexagon(cx, cy, r * 0.90)[0]], fill=GOLD + (220,), width=int(max(1, r * 0.16)))
    for (x, y) in cells[1:int(len(cells) * 0.45)]:
        d.line(hexagon(x, y, r * 0.92) + [hexagon(x, y, r * 0.92)[0]], fill=FIRE + (170,), width=int(max(1, r * 0.12)))
    img = img.filter(ImageFilter.GaussianBlur(px * 0.0015))
    return img


def kv_loading(W, H, portrait=False):
    img = kv_background(W, H, portrait)
    s = min(W, H)
    mark_px = int(s * (0.13 if not portrait else 0.19))
    m = fit_mark(mark_px, "symbol", fill=1.0, show_spark=True)
    img.alpha_composite(m, ((W - mark_px) // 2, int(H * (0.30 if not portrait else 0.30))))
    d = ImageDraw.Draw(img)
    fen = font(EN_PATH, s * 0.020) if EN_PATH else font(FONT_CN, s * 0.02)
    draw_spaced(d, W / 2, H * (0.50 if not portrait else 0.52), EN, fen, STEEL, s * 0.010)
    return img


# ---------- 游戏内 ----------
def ing_logo_plate(W, H, show_zh=True):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # 底板
    plate = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    m = round_mask(min(W, H), 0.16, ss=3)
    pm = Image.new("L", (W, H), 0)
    ImageDraw.Draw(pm).rounded_rectangle([0, 0, W - 1, H - 1], radius=int(H * 0.14), fill=255)
    g = vgrad(W, H, [(0.0, (0x24, 0x2E, 0x3E)), (1.0, (0x11, 0x18, 0x22))])
    g.putalpha(ImageChops.multiply(g.getchannel("A"), pm))
    img.alpha_composite(g)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([1, 1, W - 2, H - 2], radius=int(H * 0.14), outline=CYAN + (170,), width=max(2, int(H * 0.008)))
    d.rounded_rectangle([int(H * 0.05), int(H * 0.05), W - int(H * 0.05), H - int(H * 0.05)],
                        radius=int(H * 0.09), outline=STROKE + (150,), width=max(1, int(H * 0.005)))
    d.rounded_rectangle([int(W * 0.16), 2, W - int(W * 0.16), int(H * 0.035)],
                        radius=int(H * 0.016), fill=CYAN + (235,))
    s = H
    mark_px = int(s * 0.60)
    mk = fit_mark(mark_px, "symbol", fill=1.0, show_spark=True)
    tx = int(W * 0.06)
    img.alpha_composite(mk, (tx, (H - mark_px) // 2))
    fcn = font(FONT_CN, s * 0.30)
    ax = tx + mark_px + int(s * 0.10)
    draw_spaced(d, ax + text_w(fcn, N, s * 0.02) / 2, H * 0.44, N, fcn, TXT, s * 0.02,
                stroke_w=max(1, int(s * 0.008)), stroke_fill=(0x02, 0x08, 0x0E, 220))
    fen = font(EN_PATH, s * 0.105) if EN_PATH else fcn
    draw_spaced(d, ax + text_w(fen, EN, s * 0.07) / 2, H * 0.74, EN, fen, CYAN, s * 0.07)
    return img


def ing_loading_emblem(px):
    img = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    r = px * 0.44
    d = ImageDraw.Draw(img)
    img.alpha_composite(glow_from((px, px), hexagon(px / 2, px / 2, r), CYAN, px * 0.03, 80, ss=1))
    for i in range(6):
        a0 = -90 + 60 * i + 6
        a1 = -90 + 60 * i + 54
        p0 = (px / 2 + r * math.cos(math.radians(a0)), px / 2 + r * math.sin(math.radians(a0)))
        p1 = (px / 2 + r * math.cos(math.radians(a1)), px / 2 + r * math.sin(math.radians(a1)))
        col = CYAN if i % 2 == 0 else STEEL_DK
        d.line([p0, p1], fill=col + (255,), width=int(px * 0.032))
    mk = fit_mark(int(px * 0.46), "symbol", fill=1.0, show_spark=False)
    img.alpha_composite(mk, ((px - mk.width) // 2, (px - mk.height) // 2))
    return img


def ing_divider(W, H, color=CYAN):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cy = H / 2
    for x0, x1, al in ((0, W * 0.42, 40), (W * 0.42, W * 0.44, 200), (W * 0.56, W * 0.58, 200), (W * 0.58, W, 40)):
        pass
    d.line([(W * 0.005, cy), (W * 0.415, cy)], fill=color + (55,), width=max(1, int(H * 0.05)))
    d.line([(W * 0.585, cy), (W * 0.995, cy)], fill=color + (55,), width=max(1, int(H * 0.05)))
    d.line([(W * 0.41, cy), (W * 0.455, cy)], fill=color + (230,), width=max(1, int(H * 0.09)))
    d.line([(W * 0.545, cy), (W * 0.59, cy)], fill=color + (230,), width=max(1, int(H * 0.09)))
    hx = H * 0.62
    for cxp, al in ((W * 0.5, 255),):
        hpts = hexagon(cxp, cy, hx * 0.62)
        d.polygon(hpts, fill=(0x11, 0x18, 0x22, 240))
        d.line(hpts + [hpts[0]], fill=color + (al,), width=max(2, int(H * 0.055)), joint="curve")
        g = [hexagon(cxp, cy, hx * 0.30)[k] for k in range(6)]
        d.polygon(g, fill=color + (235,))
    for sgn in (-1, 1):
        for t in (0.28, 0.62):
            x = W * 0.5 + sgn * W * 0.5 * 0 + (W * t * sgn)
            pass
    return img


def ing_pause(W, H):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # 顶部 / 底部装饰带
    for y, sgn in ((H * 0.06, 1), (H * 0.94, -1)):
        d.line([(W * 0.14, y), (W * 0.86, y)], fill=CYAN + (70,), width=2)
        for t in (0.14, 0.86):
            hpt = hexagon(W * t, y, H * 0.035)
            d.line(hpt + [hpt[0]], fill=CYAN + (180,), width=3, joint="curve")
    # 中央暂停符（品牌化：双六棱柱）
    bw, bh = W * 0.055, H * 0.30
    for sgn in (-1, 1):
        cx = W / 2 + sgn * W * 0.048
        pts = [(cx - bw / 2, H / 2 - bh / 2), (cx + bw / 2, H / 2 - bh / 2 + bh * 0.09),
               (cx + bw / 2, H / 2 + bh / 2 - bh * 0.09), (cx - bw / 2, H / 2 + bh / 2)]
        d.polygon(pts, fill=(0xDF, 0xFA, 0xFF, 235))
    # 四角索敌框
    i0, a = W * 0.045, W * 0.075
    for (cx0, cy0), (sx, sy) in [((i0, i0), (1, 1)), ((W - i0, i0), (-1, 1)),
                                 ((i0, H - i0), (1, -1)), ((W - i0, H - i0), (-1, -1))]:
        d.line([(cx0 + sx * a, cy0), (cx0, cy0), (cx0, cy0 + sy * a)], fill=CYAN + (120,), width=4, joint="curve")
    return img


def ing_result(W, H, win=True):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    col = GOLD if win else RED
    cy = H * 0.58
    y0, y1 = cy - H * 0.105, cy + H * 0.105
    x0, x1 = W * 0.17, W * 0.83
    nw = W * 0.035
    body = [(x0, y0), (x1, y0), (x1 - nw, cy), (x1, y1), (x0, y1), (x0 + nw, cy)]
    d.polygon(body, fill=(0x12, 0x18, 0x22, 235))
    d.line(body + [body[0]], fill=col + (200,), width=4, joint="curve")
    d.line([(x0 + nw, y0), (x1 - nw, y0)], fill=col + (255,), width=7)
    d.line([(x0 + nw, y1), (x1 - nw, y1)], fill=col + (140,), width=4)
    # 中央徽记
    r = H * 0.225
    hexp = hexagon(W / 2, cy, r)
    d.polygon(hexp, fill=(0x0B, 0x11, 0x19, 250))
    d.line(hexp + [hexp[0]], fill=col + (255,), width=6, joint="curve")
    m = fit_mark(int(r * 1.55), "symbol", fill=0.95, show_spark=False)
    img.alpha_composite(m, (int(W / 2 - m.width / 2), int(cy - m.height / 2)))
    # 星级（悬浮于徽记正上方）
    sy = cy - r - H * 0.115
    for i in range(3):
        sx = W * 0.5 + (i - 1) * W * 0.075
        sp = spark_pts((sx, sy), H * 0.05, H * 0.015)
        d.polygon(sp, fill=(GOLD if win else (0x3A, 0x4A, 0x63)) + (255,))
    return img


def ing_watermark(W, H):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    s = H
    mk = fit_mark(int(s * 0.80), "mono_white", fill=1.0, show_brackets=False, show_chev=False, show_spark=False)
    img.alpha_composite(mk, (0, int(H * 0.1)))
    fcn = font(FONT_CN, s * 0.34)
    draw_spaced(d, int(s * 0.95) + text_w(fcn, N, s * 0.02) / 2, H * 0.40, N, fcn, (255, 255, 255, 225), s * 0.02)
    fen = font(EN_PATH, s * 0.115) if EN_PATH else fcn
    draw_spaced(d, int(s * 0.95) + text_w(fen, EN, s * 0.08) / 2, H * 0.68, EN, fen, (255, 255, 255, 150), s * 0.08)
    a = img.getchannel("A").point(lambda v: int(v * 0.62))
    img.putalpha(a)
    return img


def ing_corner_badge(px):
    img = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = px * 0.46
    hx = hexagon(px / 2, px / 2, r)
    img.alpha_composite(glow_from((px, px), hx, CYAN, px * 0.035, 150, ss=1))
    d.polygon(hx, fill=(0x0E, 0x14, 0x1E, 245))
    d.line(hx + [hx[0]], fill=CYAN + (255,), width=int(px * 0.035), joint="curve")
    d.line(hexagon(px / 2, px / 2, r * 0.80) + [hexagon(px / 2, px / 2, r * 0.80)[0]],
           fill=STROKE + (200,), width=int(px * 0.016), joint="curve")
    mk = fit_mark(int(px * 0.44), "symbol", fill=1.0, show_spark=False)
    img.alpha_composite(mk, ((px - mk.width) // 2, (px - mk.height) // 2))
    return img


# ---------- 辅助 ----------
def logo_mono(px, tone):
    img = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    m = fit_mark(int(px * 0.52), "mono_white" if tone == "white" else "mono_dark", fill=1.0,
                  show_brackets=True, show_chev=False, show_spark=True)
    img.alpha_composite(m, (int(px * 0.03), (px - m.height) // 2))
    d = ImageDraw.Draw(img)
    c = (255, 255, 255) if tone == "white" else (0x0D, 0x11, 0x19)
    fcn = font(FONT_CN, px * 0.20)
    x0 = int(px * 0.03) + m.width + px * 0.05
    draw_spaced(d, x0 + text_w(fcn, N, px * 0.01) / 2, px * 0.42, N, fcn, c, px * 0.01)
    fen = font(EN_PATH, px * 0.072) if EN_PATH else fcn
    draw_spaced(d, x0 + text_w(fen, EN, px * 0.055) / 2, px * 0.70, EN, fen, c, px * 0.055)
    return img


def logo_with_bg_h(W, H):
    img = kv_background(W, H)
    lock = lockup_h(int(H * 0.46))
    img.alpha_composite(lock, ((W - lock.width) // 2, (H - lock.height) // 2))
    return img


def logo_with_bg_v(W, H):
    img = kv_background(W, H, True)
    lock = lockup_v(int(W * 0.44), with_tag=True)
    img.alpha_composite(lock, ((W - lock.width) // 2, (H - lock.height) // 2))
    return img


def brand_palette(W, H):
    img = Image.new("RGBA", (W, H), (0x0B, 0x0F, 0x16, 255))
    img.alpha_composite(hexgrid_layer(W, H, 46, STEEL_DK, 26))
    d = ImageDraw.Draw(img)
    ft = font(FONT_CN, 46)
    fs = font(MONO_PATH if MONO_PATH else EN_PATH, 26)
    draw_spaced(d, 70, 62, "品牌色板 · BRAND PALETTE", ft, TXT, 6, anchor="left")
    d.text((W - 70, 62), "Freedom Tower / 自由人塔防", font=font(FONT_CN, 26), fill=STEEL_DK, anchor="rm")
    groups = [
        ("主色 PRIMARY", [("Core Cyan", CYAN), ("Cyan Light", CYAN_LT), ("Cyan Deep", CYAN_DK), ("Core Dark", (0x0E, 0x14, 0x1E))]),
        ("辅助色 SECONDARY", [("Glory Gold", GOLD), ("Ice White", ICE), ("Steel", STEEL), ("Slate", SLATE)]),
        ("功能色 FUNCTIONAL", [("Alert Red", RED), ("Fire Orange", FIRE), ("Stroke", STROKE), ("Void", VOID)]),
    ]
    y0 = 160
    cw, chh, gap = 330, 190, 34
    for gi, (gname, items) in enumerate(groups):
        yy = y0 + gi * 290
        d.text((70, yy - 26), gname, font=font(MONO_PATH if MONO_PATH else EN_PATH, 24), fill=CYAN, anchor="ls")
        for ci, (nm, col) in enumerate(items):
            x = 70 + ci * (cw + gap)
            d.rounded_rectangle([x, yy, x + cw, yy + chh], radius=16, fill=col + (255,),
                                outline=(0x3A, 0x4A, 0x63, 200), width=2)
            hexs = "#%02X%02X%02X" % col
            txtc = (0x0D, 0x11, 0x19) if sum(col) > 420 else TXT
            d.text((x + 22, yy + chh - 62), nm, font=font(FONT_CN, 28), fill=txtc, anchor="ls")
            d.text((x + 22, yy + chh - 26), hexs, font=fs, fill=txtc, anchor="ls")
    return img


def brand_typography(W, H):
    img = Image.new("RGBA", (W, H), (0x0B, 0x0F, 0x16, 255))
    img.alpha_composite(hexgrid_layer(W, H, 46, STEEL_DK, 24))
    d = ImageDraw.Draw(img)
    draw_spaced(d, 70, 62, "字体规范 · TYPOGRAPHY", font(FONT_CN, 46), TXT, 6, anchor="left")
    y = 170
    rows = [
        ("中文标准字 · 思源宋体 Bold", N, FONT_CN, 92, CYAN, 12),
        ("英文标准字 · 几何无衬线 全大写宽字距", EN, EN_PATH, 54, TXT, 20),
        ("副标语", TAG, FONT_CN, 40, STEEL, 14),
        ("技术标号 / 版本号 · 等宽", "v1.0.0  BUILD 20261015", MONO_PATH, 34, STEEL_DK, 4),
        ("正文 · 思源宋体 Regular", "自由布塔，实时重算路径，用你的防线定义战场。", FONT_CN, 34, TXT, 2),
    ]
    for title, sample, path, size, col, sp in rows:
        d.text((70, y), title, font=font(FONT_CN, 24), fill=STEEL_DK, anchor="ls")
        if path:
            draw_spaced(d, W / 2, y + 84, sample, font(path, size), col, sp)
        y += 200
    return img


def logo_clearspace(W, H):
    img = Image.new("RGBA", (W, H), (0x0B, 0x0F, 0x16, 255))
    d = ImageDraw.Draw(img)
    lock = lockup_h(340)
    cx, cy = W / 2, H * 0.40
    x0 = int(cx - lock.width / 2)
    y0 = int(cy - lock.height / 2)
    # 清空区（= 水晶宽度 x 2）
    p = 62
    d.rectangle([x0 - p, y0 - p, x0 + lock.width + p, y0 + lock.height + p], outline=CYAN + (200,), width=3)
    for hx, hy in ((x0 - p, y0 - p), (x0 + lock.width + p, y0 - p), (x0 - p, y0 + lock.height + p), (x0 + lock.width + p, y0 + lock.height + p)):
        d.line([(hx - 18, hy), (hx, hy), (hx, hy - 18 if hy < cy else hy + 18)], fill=GOLD + (230,), width=5, joint="curve")
    img.alpha_composite(lock, (x0, y0))
    d.text((70, 60), "安全边距与最小尺寸 · CLEAR SPACE & MIN SIZE", font=font(FONT_CN, 40), fill=TXT, anchor="lm")
    d.text((70, 110), "安全边距 = 水晶核心宽度 (X)；标志四周必须留白 X，不得放置任何元素。", font=font(FONT_CN, 24), fill=STEEL, anchor="lm")
    y = H * 0.72
    d.text((70, y - 40), "最小尺寸 · MIN SIZE", font=font(FONT_CN, 28), fill=CYAN, anchor="lm")
    x = 90
    for px, label in ((160, "160px"), (96, "96px"), (48, "48px"), (32, "32px")):
        m = fit_mark(px, "symbol", fill=0.92, show_spark=(px >= 96))
        img.alpha_composite(m, (x, int(y)))
        d.text((x + px / 2, y + px + 34), label, font=font(MONO_PATH if MONO_PATH else EN_PATH, 24), fill=STEEL, anchor="mm")
        x += px + 90
    d.text((x + 10, y + 60), "→ 48px 为可用下限（简化符号版）；< 48px 仅用符号，禁用索敌框与文字。",
           font=font(FONT_CN, 24), fill=STEEL_DK, anchor="lm")
    return img


# ---------- 锁扣版 SVG ----------
def lockup_h_svg():
    hx = hexagon(0, 0, HEX_R)  # placeholder
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 360" width="1280" height="360">
  <g transform="translate(20,20) scale(0.32)">{svg_mark("symbol").split(">",1)[1].rsplit("</svg>",1)[0]}</g>
  <text x="410" y="170" font-family="'Source Han Serif SC','SiYuanSongTi',serif" font-size="130"
        font-weight="700" fill="#E8F0FA" letter-spacing="4">自由人塔防</text>
  <text x="412" y="252" font-family="'Rajdhani','Segoe UI',sans-serif" font-size="46"
        font-weight="600" fill="#35E0FF" letter-spacing="14">FREEDOM TOWER</text>
</svg>'''


def lockup_v_svg():
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 700" width="760" height="700">
  <g transform="translate(112,0) scale(0.536)">{svg_mark("symbol").split(">",1)[1].rsplit("</svg>",1)[0]}</g>
  <text x="380" y="620" font-family="'Source Han Serif SC','SiYuanSongTi',serif" font-size="108"
        font-weight="700" fill="#E8F0FA" text-anchor="middle" letter-spacing="3">自由人塔防</text>
  <text x="380" y="676" font-family="'Rajdhani','Segoe UI',sans-serif" font-size="38"
        font-weight="600" fill="#35E0FF" text-anchor="middle" letter-spacing="12">FREEDOM TOWER</text>
</svg>'''


if __name__ == "__main__":
    build()
