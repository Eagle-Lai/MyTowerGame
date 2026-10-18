# -*- coding: utf-8 -*-
"""
gen_tower_fire_frames.py — 生成塔开火序列帧（2026-10-17 攻击表现改版）

背景：普通塔(1)/火力塔(2) 移除真实子弹，改为《坚守阵地》式表现——
开火只播枪口焰序列帧 + 即时伤害判定；火力塔在落点补一段爆炸序列帧。

产物（Assets/_UIAssets/Tower/FireFx/）：
  Tower_Muzzle_Normal_0..3.png  128x128  普通塔枪口焰（黄白、朝上，轴点=焰底）
  Tower_Muzzle_Power_0..4.png   160x160  火力塔枪口焰（橙红、更大，朝上，轴点=焰底）
  Tower_Blast_0..5.png          256x256  落点爆炸（中心引爆：闪光→火球→冲击环→烟雾）

朝向与轴点约定（★2026-10-17 修正）：
  炮管贴图原生朝上（BaseTower.BarrelNativeAngle=90°），枪口焰挂在炮口节点
  BarrelPoint 下、跟随炮管旋转，因此**帧内火焰朝上画**。
  轴点必须**正好落在焰底**（白热核心中心），这样精灵位置 = BarrelPoint 位置时，
  焰根就落在枪口上；焰底以下那圈回喷光晕留在炮管上，是想要的自然过渡。
  → base_y = h*(1-BASE_MARGIN)，meta 用 **alignment: 9（Custom）+ spritePivot y=BASE_MARGIN**。
  ★别再写 alignment: 1 —— Unity 的 SpriteAlignment 枚举是 0=Center,1=TopLeft,…,7=BottomCenter,9=Custom，
    1 是"左上角"，会把整张贴图挂到炮口右下方（曾因此枪口焰整个跑偏）。

确定性：固定随机种子，重复运行产物逐字节一致（便于 diff 复核）。
运行：C:/Users/Administrator/.workbuddy/binaries/python/envs/default/Scripts/python.exe 本脚本
"""
import math
import os
import random
import uuid

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
OUT_DIR = os.path.normpath(os.path.join(ROOT, "Assets", "_UIAssets", "Tower", "FireFx"))
SS = 2  # 超采样倍数（抗锯齿）

# 枪口焰：焰底距画布底边的留白比例（= meta 里的轴点 y）。
# 留白只给"焰底以下那圈回喷光晕"用，焰底本身正好落在轴点上 → 轴点即枪口。
MUZZLE_BASE_MARGIN = 0.20

random.seed(20261017)


def new_canvas(w, h):
    """加色累积缓冲（RGB float）+ alpha 累积，最后合成 RGBA。"""
    return [[0.0, 0.0, 0.0, 0.0] for _ in range(w * h)]  # r,g,b,a


def add_px(buf, w, h, x, y, r, g, b, a):
    x, y = int(x), int(y)
    if 0 <= x < w and 0 <= y < h:
        i = y * w + x
        p = buf[i]
        p[0] += r
        p[1] += g
        p[2] += b
        p[3] = max(p[3], a)


def glow_circle(buf, w, h, cx, cy, radius, color, intensity):
    """径向衰减光斑：fall = (1-d)^2。"""
    r2 = radius * radius
    x0, x1 = int(cx - radius - 1), int(cx + radius + 2)
    y0, y1 = int(cy - radius - 1), int(cy + radius + 2)
    for py in range(max(0, y0), min(h, y1)):
        dy2 = (py - cy) ** 2
        for px in range(max(0, x0), min(w, x1)):
            d2 = (px - cx) ** 2 + dy2
            if d2 > r2:
                continue
            fall = 1.0 - math.sqrt(d2) / radius
            fall *= fall
            a = intensity * fall
            add_px(buf, w, h, px, py, color[0] * a, color[1] * a, color[2] * a, a)


def disc(buf, w, h, cx, cy, radius, color, intensity):
    """实心圆盘：内部基本不衰减，只在边缘 20% 内快速收边（火球主体用）。"""
    r2 = radius * radius
    x0, x1 = int(cx - radius - 1), int(cx + radius + 2)
    y0, y1 = int(cy - radius - 1), int(cy + radius + 2)
    for py in range(max(0, y0), min(h, y1)):
        dy2 = (py - cy) ** 2
        for px in range(max(0, x0), min(w, x1)):
            d2 = (px - cx) ** 2 + dy2
            if d2 > r2:
                continue
            d = math.sqrt(d2) / radius
            fall = 1.0 if d < 0.8 else (1.0 - d) / 0.2
            a = intensity * max(0.0, fall)
            add_px(buf, w, h, px, py, color[0] * a, color[1] * a, color[2] * a, a)


def flame(buf, w, h, base_x, base_y, length, width, color_hot, color_cool, intensity, lean=0.0):
    """朝上的火舌：y 从 base_y 向上 length 像素，宽度随高度收窄，颜色由热到冷。"""
    for k in range(int(length)):
        t = k / max(1.0, length)          # 0=底部 1=顶端
        y = base_y - k
        half_w = width * (1.0 - t) ** 0.85 + 0.6
        cx = base_x + lean * t * t * width
        row_i = intensity * (1.0 - 0.55 * t)
        x0, x1 = int(cx - half_w - 1), int(cx + half_w + 2)
        for px in range(max(0, x0), min(w, x1)):
            # 横向柔和衰减 + 轻微噪声锯齿边
            edge = 1.0 - abs(px - cx) / max(0.5, half_w)
            edge = max(0.0, edge)
            edge *= edge
            n = 1.0 - 0.25 * random.random()
            a = row_i * edge * n
            r = color_hot[0] + (color_cool[0] - color_hot[0]) * t
            g = color_hot[1] + (color_cool[1] - color_hot[1]) * t
            b = color_hot[2] + (color_cool[2] - color_hot[2]) * t
            add_px(buf, w, h, px, y, r * a, g * a, b * a, a)


def ring(buf, w, h, cx, cy, radius, thickness, color, intensity):
    """圆环描边（冲击波）。"""
    r_in = radius - thickness * 0.5
    r_out = radius + thickness * 0.5
    r_in2, r_out2 = r_in * r_in, r_out * r_out
    x0, x1 = int(cx - r_out - 1), int(cx + r_out + 2)
    y0, y1 = int(cy - r_out - 1), int(cy + r_out + 2)
    for py in range(max(0, y0), min(h, y1)):
        dy2 = (py - cy) ** 2
        for px in range(max(0, x0), min(w, x1)):
            d2 = (px - cx) ** 2 + dy2
            if d2 < r_in2 or d2 > r_out2:
                continue
            d = math.sqrt(d2)
            k = 1.0 - abs(d - radius) / max(0.5, thickness * 0.5)
            a = intensity * max(0.0, k) ** 1.5
            add_px(buf, w, h, px, py, color[0] * a, color[1] * a, color[2] * a, a)


def spark(buf, w, h, x, y, angle_deg, length, color, intensity):
    """线状火星。"""
    rad = math.radians(angle_deg)
    dx, dy = math.cos(rad), -math.sin(rad)
    steps = max(2, int(length))
    for k in range(steps):
        t = k / float(steps)
        px, py = x + dx * k, y + dy * k
        a = intensity * (1.0 - t)
        # 沿线做 2px 粗
        for oy in (0, 1):
            for ox in (0, 1):
                add_px(buf, w, h, int(px) + ox, int(py) + oy, color[0] * a, color[1] * a, color[2] * a, a)


def finalize(buf, w, h, out_w):
    """加色缓冲 → RGBA（alpha 取亮度包络），柔化后缩放到 out_w。"""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    pix = img.load()
    for i, p in enumerate(buf):
        x, y = i % w, i // w
        r = min(255.0, p[0])
        g = min(255.0, p[1])
        b = min(255.0, p[2])
        lum = (0.3 * r + 0.5 * g + 0.2 * b) / 255.0
        a = min(1.0, max(p[3], lum * 1.15))
        pix[x, y] = (int(r), int(g), int(b), int(a * 255))
    img = img.filter(ImageFilter.GaussianBlur(1.2 * SS))
    return img.resize((out_w, out_w), Image.LANCZOS)


# ---------------------------------------------------------------------------
# 枪口焰（朝上；焰底 = 轴点 = BarrelPoint；焰底以下 CIRCLE 半径内的回喷光晕留白）
# ---------------------------------------------------------------------------

def gen_muzzle(size, frames, hot, cool, base_len, base_w, heavy):
    """heavy=True 时加左右横向爆光（火力塔的重炮感）。"""
    imgs = []
    for f in range(frames):
        t = f / float(frames - 1)             # 0→1 时间进度
        # 强度包络：f0 起火 → 第1帧峰值 → 渐熄
        peak = 1.0 if frames <= 4 else 1.0
        env = [0.62, 1.0, 0.72, 0.34, 0.16][min(f, 4)]
        w = h = size * SS
        buf = new_canvas(w, h)
        # ★焰底位置必须与 meta 的 spritePivot.y 一致（都是 MUZZLE_BASE_MARGIN）
        cx, base_y = w * 0.5, h * (1.0 - MUZZLE_BASE_MARGIN)
        inten = env * peak
        length = base_len * SS * (0.45 + 0.75 * env)
        width = base_w * SS * (0.5 + 0.7 * env)
        # 火舌主体（热芯→冷缘）
        flame(buf, w, h, cx, base_y, length, width * 0.55, hot, cool, inten)
        flame(buf, w, h, cx, base_y, length * 0.62, width, cool, cool, inten * 0.55,
              lean=random.choice((-0.18, 0.18)))
        # 白热内核（贴枪口）
        glow_circle(buf, w, h, cx, base_y - 2 * SS, width * (0.9 + 0.5 * env),
                    (255, 250, 230), inten * 1.15)
        glow_circle(buf, w, h, cx, base_y, width * 0.55, (255, 255, 255), inten)
        # 重炮：左右横向爆光
        if heavy and f <= 2:
            for sgn in (-1, 1):
                flame(buf, w, h, cx + sgn * width * 0.4, base_y - width * 0.5,
                      length * 0.3 * (1.0 - 0.4 * f), width * 0.35, hot, cool, inten * 0.5,
                      lean=sgn * 1.6)
        # 火星：前两帧多、向外上飞
        n_spark = max(0, 5 - 2 * f)
        for s in range(n_spark):
            ang = random.uniform(45, 135)
            spark(buf, w, h, cx, base_y - length * 0.55, ang,
                  random.uniform(8, 20) * SS * (1.0 + f * 0.25),
                  cool, inten * 0.8)
        imgs.append(finalize(buf, w, h, size))
    return imgs


# ---------------------------------------------------------------------------
# 落点爆炸（居中）
# ---------------------------------------------------------------------------

def gen_blast(size, frames):
    imgs = []
    cx = cy = size * SS * 0.5
    for f in range(frames):
        t = f / float(frames - 1)
        w = h = size * SS
        buf = new_canvas(w, h)
        env = [0.55, 1.0, 0.9, 0.62, 0.38, 0.18][min(f, 5)]
        inten = env
        # 火球：先白黄核后转橙红、半径先涨后稳（实心主体 + 光晕包边）
        r_fire = size * SS * (0.13 + 0.30 * min(1.0, f / 1.5))
        hot = (255, 244, 200) if f <= 1 else (255, 170, 60)
        cool = (255, 120, 40) if f <= 2 else (200, 80, 30)
        disc(buf, w, h, cx, cy, r_fire, cool, inten * 0.9)
        disc(buf, w, h, cx, cy, r_fire * 0.72, hot, inten * 0.9)
        glow_circle(buf, w, h, cx, cy, r_fire * 1.5, hot, inten * 0.55)
        glow_circle(buf, w, h, cx, cy, r_fire * 0.5, (255, 255, 240),
                    inten * (1.0 if f <= 1 else 0.7))
        # 放射火刺（前 3 帧）：楔形粗刺，用短火舌画
        if f <= 3:
            n = 9 - 2 * f
            for s in range(n):
                ang = 360.0 * s / n + random.uniform(-12, 12)
                ln = r_fire * random.uniform(1.1, 1.8)
                rad = math.radians(ang)
                sx = cx + math.cos(rad) * r_fire * 0.5
                sy = cy - math.sin(rad) * r_fire * 0.5
                # 沿刺方向铺 3 段渐细圆斑
                for seg in range(3):
                    k = seg / 3.0
                    glow_circle(buf, w, h,
                                sx + math.cos(rad) * ln * k,
                                sy - math.sin(rad) * ln * k,
                                r_fire * 0.22 * (1.0 - 0.6 * k),
                                cool, inten * (0.8 - 0.2 * seg))
        # 冲击环：第 2 帧出现，逐帧外扩变淡
        if f >= 2:
            ring_r = size * SS * (0.16 + 0.26 * (f - 1))
            thick = max(1.0, size * SS * (0.05 - 0.007 * f))
            ring(buf, w, h, cx, cy, ring_r, thick, (255, 210, 140), inten * (1.0 - 0.12 * f))
        # 烟雾（后 3 帧）：灰橙、下沉
        if f >= 3:
            for s in range(5):
                a_ang = random.uniform(0, 6.283)
                dist = r_fire * random.uniform(0.4, 1.1)
                sx, sy = cx + math.cos(a_ang) * dist, cy + math.sin(a_ang) * dist - f * 1.5
                glow_circle(buf, w, h, sx, sy, size * SS * 0.14, (120, 100, 90), inten * 0.35)
        imgs.append(finalize(buf, w, h, size))
    return imgs


# ---------------------------------------------------------------------------
# meta 写出（模板对齐 Assets/Art/Generated/Bullet_Dot.png.meta：
# Sprite / PPU100 / bilinear / 无 mipmap / alphaIsTransparency / 指定 AB 包名）
# ---------------------------------------------------------------------------

META_TMPL = """fileFormatVersion: 2
guid: {guid}
TextureImporter:
  internalIDToNameTable: []
  externalObjects: {{}}
  serializedVersion: 13
  mipmaps:
    mipMapMode: 0
    enableMipMap: 0
    sRGBTexture: 1
    linearTexture: 0
    fadeOut: 0
    borderMipMap: 0
    mipMapsPreserveCoverage: 0
    alphaTestReferenceValue: 0.5
    mipMapFadeDistanceStart: 1
    mipMapFadeDistanceEnd: 3
  bumpmap:
    convertToNormalMap: 0
    externalNormalMap: 0
    heightScale: 0.25
    normalMapFilter: 0
    flipGreenChannel: 0
  isReadable: 0
  streamingMipmaps: 0
  streamingMipmapsPriority: 0
  vTOnly: 0
  ignoreMipmapLimit: 0
  grayScaleToAlpha: 0
  generateCubemap: 6
  cubemapConvolution: 0
  seamlessCubemap: 0
  textureFormat: 1
  maxTextureSize: 2048
  textureSettings:
    serializedVersion: 2
    filterMode: 1
    aniso: 1
    mipBias: 0
    wrapU: 1
    wrapV: 1
    wrapW: 1
  nPOTScale: 0
  lightmap: 0
  compressionQuality: 50
  spriteMode: 1
  spriteExtrude: 1
  spriteMeshType: 1
  alignment: {alignment}
  spritePivot: {{x: 0.5, y: {pivot_y}}}
  spritePixelsToUnits: 100
  spriteBorder: {{x: 0, y: 0, z: 0, w: 0}}
  spriteGenerateFallbackPhysicsShape: 1
  alphaUsage: 1
  alphaIsTransparency: 1
  spriteTessellationDetail: -1
  textureType: 8
  textureShape: 1
  singleChannelComponent: 0
  flipbookRows: 1
  flipbookColumns: 1
  maxTextureSizeSet: 0
  compressionQualitySet: 0
  textureFormatSet: 0
  ignorePngGamma: 0
  applyGammaDecoding: 0
  swizzle: 50462976
  cookieLightType: 0
  platformSettings:
  - serializedVersion: 3
    buildTarget: DefaultTexturePlatform
    maxTextureSize: 2048
    resizeAlgorithm: 0
    textureFormat: -1
    textureCompression: 0
    compressionQuality: 50
    crunchedCompression: 0
    allowsAlphaSplitting: 0
    overridden: 0
    ignorePlatformSupport: 0
    androidETC2FallbackOverride: 0
    forceMaximumCompressionQuality_BC6H_BC7: 0
  - serializedVersion: 3
    buildTarget: Standalone
    maxTextureSize: 2048
    resizeAlgorithm: 0
    textureFormat: -1
    textureCompression: 1
    compressionQuality: 50
    crunchedCompression: 0
    allowsAlphaSplitting: 0
    overridden: 0
    ignorePlatformSupport: 0
    androidETC2FallbackOverride: 0
    forceMaximumCompressionQuality_BC6H_BC7: 0
  - serializedVersion: 3
    buildTarget: Android
    maxTextureSize: 2048
    resizeAlgorithm: 0
    textureFormat: -1
    textureCompression: 1
    compressionQuality: 50
    crunchedCompression: 0
    allowsAlphaSplitting: 0
    overridden: 0
    ignorePlatformSupport: 0
    androidETC2FallbackOverride: 0
    forceMaximumCompressionQuality_BC6H_BC7: 0
  spriteSheet:
    serializedVersion: 2
    sprites: []
    outline: []
    physicsShape: []
    bones: []
    spriteID: 5e97eb03825dee720800000000000000
    internalID: 0
    vertices: []
    indices: 
    edges: []
    weights: []
    secondaryTextures: []
    nameFileIdTable: {{}}
  mipmapLimitGroupName: 
  pSDRemoveMatte: 0
  userData: 
  assetBundleName: {bundle}
  assetBundleVariant: 
"""


def existing_guid(meta_path):
    """沿用同名 .meta 里已有的 guid —— 重跑脚本不能换 GUID（否则引用/AB 全抖）。"""
    try:
        with open(meta_path, "r", encoding="utf-8") as fp:
            for line in fp:
                if line.startswith("guid: "):
                    return line[6:].strip()
    except OSError:
        pass
    return None


def write_group(imgs, prefix, bundle, alignment, pivot_y):
    """alignment 走 Unity SpriteAlignment 枚举：0=Center，9=Custom（此时以 spritePivot 为准）。"""
    os.makedirs(OUT_DIR, exist_ok=True)
    for i, img in enumerate(imgs):
        name = "%s_%d" % (prefix, i)
        png = os.path.join(OUT_DIR, name + ".png")
        meta = os.path.join(OUT_DIR, name + ".png.meta")
        img.save(png)
        guid = existing_guid(meta) or uuid.uuid4().hex
        with open(meta, "w", encoding="utf-8", newline="\n") as fp:
            fp.write(META_TMPL.format(
                guid=guid, alignment=alignment, pivot_y=pivot_y, bundle=bundle))
        print("write", png)


def main():
    # 普通塔枪口焰：黄白、细长（机枪点射感）
    normal = gen_muzzle(128, 4,
                        hot=(255, 240, 180), cool=(255, 190, 80),
                        base_len=64, base_w=16, heavy=False)
    write_group(normal, "Tower_Muzzle_Normal", "tower_normal",
                alignment=9, pivot_y=MUZZLE_BASE_MARGIN)

    # 火力塔枪口焰：橙红、宽厚（重炮感）
    power = gen_muzzle(160, 5,
                       hot=(255, 220, 150), cool=(255, 130, 50),
                       base_len=84, base_w=26, heavy=True)
    write_group(power, "Tower_Muzzle_Power", "tower_power",
                alignment=9, pivot_y=MUZZLE_BASE_MARGIN)

    # 落点爆炸：居中锚点（引爆点在中心，位置由 PlayBlastAt 的落点决定）
    blast = gen_blast(256, 6)
    write_group(blast, "Tower_Blast", "tower_power",
                alignment=0, pivot_y=0.5)

    print("done ->", OUT_DIR)


if __name__ == "__main__":
    main()
