#!/usr/bin/env python3
"""
perler-pattern — 图片转拼豆图纸生成器

将任意图片转换为拼豆（Perler Beads）网格图纸，支持：
- 自动调色到标准拼豆色板（Artkal / Hama / Perler）
- 自定义网格尺寸与多种板型（29×29 标准板、大板等）
- 输出彩色预览图 + 编号图纸 + 颜色图例（含用量统计）
- 支持透明背景处理
- 纯 Python，仅依赖 Pillow

用法：
    python perler_pattern.py photo.jpg
    python perler_pattern.py photo.jpg -w 58 -h 58 --palette artkal-s
    python perler_pattern.py photo.jpg -w 116 --palette custom --colors "#FF0000,#00FF00,#0000FF"
"""

import argparse
import json
import math
import os
import sys
from collections import Counter
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("错误：需要 Pillow 库。运行: pip install Pillow", file=sys.stderr)
    sys.exit(1)


# ─────────────────────────────────────────────
# 标准拼豆色板定义
# ─────────────────────────────────────────────

# Artkal S 系列 (5mm) — 最常用的色板，约 80+ 色
ARTKAL_S = {
    "S01": (255, 255, 255),   # White
    "S02": (228, 228, 228),   # Light Grey
    "S03": (160, 160, 160),   # Grey
    "S04": (100, 100, 100),   # Dark Grey
    "S05": (0, 0, 0),         # Black
    "S06": (255, 210, 220),   # Blush
    "S07": (255, 155, 175),   # Light Pink
    "S08": (255, 90, 130),    # Pink
    "S09": (230, 50, 100),    # Dark Pink
    "S10": (180, 20, 60),     # Raspberry
    "S11": (255, 175, 155),   # Peach
    "S12": (255, 130, 80),    # Light Orange
    "S13": (255, 100, 30),    # Orange
    "S14": (230, 70, 0),      # Dark Orange
    "S15": (200, 50, 0),      # Rust
    "S16": (255, 240, 100),   # Light Yellow
    "S17": (255, 220, 0),     # Yellow
    "S18": (230, 190, 0),     # Dark Yellow
    "S19": (200, 160, 0),     # Gold
    "S20": (180, 140, 0),     # Dark Gold
    "S21": (180, 230, 130),   # Light Green
    "S22": (100, 200, 60),    # Green
    "S23": (50, 170, 30),     # Medium Green
    "S24": (20, 130, 20),     # Dark Green
    "S25": (0, 90, 10),       # Forest Green
    "S26": (150, 230, 210),   # Mint
    "S27": (60, 200, 180),    # Teal
    "S28": (0, 160, 140),     # Dark Teal
    "S29": (0, 120, 110),     # Deep Teal
    "S30": (0, 80, 80),       # Darkest Teal
    "S31": (170, 210, 255),   # Light Blue
    "S32": (100, 170, 255),   # Sky Blue
    "S33": (50, 120, 230),    # Blue
    "S34": (20, 70, 200),     # Medium Blue
    "S35": (0, 30, 160),      # Dark Blue
    "S36": (170, 150, 255),   # Lavender
    "S37": (120, 90, 220),    # Purple
    "S38": (80, 40, 180),     # Dark Purple
    "S39": (50, 20, 130),     # Deep Purple
    "S40": (30, 0, 80),       # Darkest Purple
    "S41": (255, 180, 200),   # Light Rose
    "S42": (230, 130, 160),   # Rose
    "S43": (200, 80, 120),    # Dark Rose
    "S44": (160, 50, 80),     # Wine
    "S45": (120, 30, 50),     # Burgundy
    "S46": (255, 200, 150),   # Light Tan
    "S47": (220, 160, 100),   # Tan
    "S48": (180, 120, 60),    # Brown
    "S49": (140, 80, 30),     # Dark Brown
    "S50": (90, 50, 10),      # Chocolate
    "S51": (60, 30, 0),       # Espresso
    "S52": (255, 255, 200),   # Cream
    "S53": (230, 210, 170),   # Light Sand
    "S54": (190, 170, 130),   # Sand
    "S55": (150, 130, 90),    # Khaki
    "S56": (255, 100, 100),   # Light Red
    "S57": (220, 30, 30),     # Red
    "S58": (170, 0, 0),       # Dark Red
    "S59": (130, 0, 0),       # Crimson
    "S60": (100, 0, 0),       # Maroon
    "S99": (0, 0, 0, 0),      # Transparent (special)
}

# Perler 品牌常用色板
PERLER = {
    "01": (255, 255, 255),    # White
    "02": (200, 200, 200),    # Light Grey
    "03": (120, 120, 120),    # Grey
    "04": (0, 0, 0),          # Black
    "05": (255, 200, 200),    # Blush
    "06": (255, 120, 150),    # Light Pink
    "07": (255, 50, 100),     # Hot Pink
    "08": (200, 0, 50),       # Red
    "09": (255, 180, 130),    # Peach
    "10": (255, 150, 50),     # Orange
    "11": (255, 230, 80),     # Yellow
    "12": (200, 180, 0),      # Cheddar
    "13": (180, 230, 100),    # Light Green
    "14": (50, 180, 50),      # Green
    "15": (0, 120, 0),        # Dark Green
    "16": (100, 200, 180),    # Pastel Green
    "17": (0, 180, 160),      # Teal
    "18": (130, 200, 255),    # Light Blue
    "19": (50, 120, 255),     # Blue
    "20": (0, 50, 180),       # Dark Blue
    "21": (150, 130, 255),    # Purple
    "22": (100, 50, 200),     # Dark Purple
    "23": (200, 100, 200),    # Pastel Lavender
    "24": (150, 50, 100),     # Plum
    "25": (200, 150, 100),    # Tan
    "26": (150, 100, 50),     # Brown
    "27": (100, 50, 0),       # Dark Brown
    "28": (255, 200, 150),    # Cream
    "29": (180, 140, 80),     # Sand
}

# Hama 品牌色板
HAMA = {
    "01": (255, 255, 255),    # White
    "02": (220, 220, 220),    # Light Grey
    "03": (140, 140, 140),    # Grey
    "04": (60, 60, 60),       # Dark Grey
    "05": (0, 0, 0),          # Black
    "06": (255, 180, 180),    # Light Pink
    "07": (255, 80, 120),     # Pink
    "08": (200, 0, 40),       # Red
    "09": (255, 160, 80),     # Orange
    "10": (255, 220, 0),      # Yellow
    "11": (180, 220, 60),     # Light Green
    "12": (50, 170, 50),      # Green
    "13": (0, 100, 0),        # Dark Green
    "14": (0, 160, 150),      # Turquoise
    "15": (80, 160, 255),     # Light Blue
    "16": (0, 80, 200),       # Blue
    "17": (0, 30, 150),       # Dark Blue
    "18": (120, 80, 200),     # Purple
    "19": (180, 60, 120),     # Violet
    "20": (200, 140, 80),     # Brown
    "21": (130, 70, 30),      # Dark Brown
    "22": (255, 220, 180),    # Peach
    "23": (200, 160, 100),    # Sand
}

PALETTES = {
    "artkal-s": ARTKAL_S,
    "perler": PERLER,
    "hama": HAMA,
}


# ─────────────────────────────────────────────
# 颜色匹配算法
# ─────────────────────────────────────────────

def color_distance(c1, c2):
    """加权欧氏距离（感知优化），人眼对绿色最敏感，蓝色最不敏感"""
    r1, g1, b1 = c1[:3]
    r2, g2, b2 = c2[:3]
    dr, dg, db = r1 - r2, g1 - g2, b1 - b2
    r_mean = (r1 + r2) / 2.0
    # 略微感知加权
    return math.sqrt(
        (2 + r_mean / 256) * dr * dr +
        4 * dg * dg +
        (2 + (255 - r_mean) / 256) * db * db
    )


def find_nearest_color(pixel, palette):
    """找到调色板中最接近的颜色"""
    min_dist = float("inf")
    best_key = None
    for key, color in palette.items():
        if len(color) == 4 and color[3] == 0:
            continue  # 跳过透明色
        dist = color_distance(pixel, color)
        if dist < min_dist:
            min_dist = dist
            best_key = key
    return best_key


def hex_to_rgb(h):
    """#RRGGBB → (r, g, b)"""
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def build_custom_palette(color_list):
    """从颜色列表构建自定义调色板"""
    palette = {}
    for i, c in enumerate(color_list):
        palette[f"C{i+1:02d}"] = hex_to_rgb(c)
    return palette


# ─────────────────────────────────────────────
# 图片处理核心
# ─────────────────────────────────────────────

def load_and_resize(image_path, width, height, keep_aspect=False):
    """加载图片并调整到目标网格尺寸"""
    img = Image.open(image_path).convert("RGBA")

    if keep_aspect:
        # 保持宽高比，计算目标尺寸
        ratio = min(width / img.width, height / img.height)
        new_w = int(img.width * ratio)
        new_h = int(img.height * ratio)
    else:
        new_w, new_h = width, height

    # 使用 LANCZOS 高质量缩放
    img = img.resize((new_w, new_h), Image.LANCZOS)
    return img


def quantize_image(img, palette):
    """
    将图片像素映射到调色板，返回：
    - grid: 二维列表，每个元素是调色板 key
    - stats: Counter 统计每种颜色用量
    """
    width, height = img.size
    pixels = img.load()
    grid = []
    stats = Counter()

    # 背景色（白色）
    bg_color = (255, 255, 255, 255)

    for y in range(height):
        row = []
        for x in range(width):
            r, g, b, a = pixels[x, y]
            # 低透明度视为背景
            if a < 60:
                key = None  # 空位/透明
            else:
                # 混合到白色背景上（模拟不透明效果）
                if a < 255:
                    alpha = a / 255.0
                    r = int(r * alpha + bg_color[0] * (1 - alpha))
                    g = int(g * alpha + bg_color[1] * (1 - alpha))
                    b = int(b * alpha + bg_color[2] * (1 - alpha))
                key = find_nearest_color((r, g, b), palette)
                stats[key] += 1
            row.append(key)
        grid.append(row)

    return grid, stats


# ─────────────────────────────────────────────
# 图纸渲染
# ─────────────────────────────────────────────

def render_color_preview(grid, palette, cell_size=10):
    """渲染彩色预览图（每个格子填色）"""
    height = len(grid)
    width = len(grid[0]) if grid else 0
    img = Image.new("RGBA", (width * cell_size, height * cell_size), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)

    for y, row in enumerate(grid):
        for x, key in enumerate(row):
            if key is None:
                continue
            color = palette[key]
            x0, y0 = x * cell_size, y * cell_size
            draw.rectangle(
                [x0, y0, x0 + cell_size - 1, y0 + cell_size - 1],
                fill=color[:3],
                outline=(200, 200, 200),
            )

    return img


def render_numbered_pattern(grid, palette, cell_size=24):
    """渲染带编号的图纸（每格显示颜色编号）"""
    height = len(grid)
    width = len(grid[0]) if grid else 0
    img = Image.new("RGBA", (width * cell_size, height * cell_size), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)

    # 尝试加载字体
    font = None
    font_size = max(8, cell_size // 3)
    for font_path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:/Windows/Fonts/arialbd.ttf",
    ]:
        if os.path.exists(font_path):
            try:
                font = ImageFont.truetype(font_path, font_size)
            except Exception:
                pass
            break
    if font is None:
        font = ImageFont.load_default()

    for y, row in enumerate(grid):
        for x, key in enumerate(row):
            x0, y0 = x * cell_size, y * cell_size
            if key is None:
                # 空格用浅灰虚线
                draw.rectangle(
                    [x0, y0, x0 + cell_size - 1, y0 + cell_size - 1],
                    fill=(245, 245, 245),
                    outline=(200, 200, 200),
                )
                continue

            color = palette[key]
            # 计算亮度决定文字颜色
            r, g, b = color[:3]
            luminance = 0.299 * r + 0.587 * g + 0.114 * b
            text_color = (0, 0, 0) if luminance > 128 else (255, 255, 255)

            draw.rectangle(
                [x0, y0, x0 + cell_size - 1, y0 + cell_size - 1],
                fill=color[:3],
                outline=(180, 180, 180),
            )

            # 居中绘制编号
            text = key
            bbox = draw.textbbox((0, 0), text, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            tx = x0 + (cell_size - tw) / 2
            ty = y0 + (cell_size - th) / 2
            draw.text((tx, ty), text, fill=text_color, font=font)

    return img


def render_legend(palette, stats, cell_size=30):
    """渲染颜色图例（含用量统计）"""
    if not stats:
        return Image.new("RGBA", (200, 50), (255, 255, 255, 255))

    # 按用量降序排列
    sorted_colors = stats.most_common()
    total_beads = sum(stats.values())
    row_height = max(28, cell_size)
    margin = 10
    label_w = 280
    count_w = 100
    total_w = cell_size + 20 + label_w + count_w + margin * 2
    total_h = (row_height + 6) * len(sorted_colors) + row_height + margin * 2 + 20

    img = Image.new("RGBA", (total_w, total_h), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)

    # 标题字体
    title_font = None
    body_font = None
    for fp in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:/Windows/Fonts/arialbd.ttf",
    ]:
        if os.path.exists(fp):
            try:
                title_font = ImageFont.truetype(fp, 16)
                body_font = ImageFont.truetype(fp, 13)
            except Exception:
                pass
            break
    if title_font is None:
        title_font = ImageFont.load_default()
        body_font = title_font

    # 标题
    draw.text(
        (margin, margin),
        f"颜色图例  |  共 {total_beads} 颗",
        fill=(30, 30, 30),
        font=title_font,
    )

    y_offset = margin + row_height + 5
    for code, count in sorted_colors:
        color = palette[code]
        # 色块
        cx = margin
        cy = y_offset
        draw.rectangle(
            [cx, cy, cx + cell_size, cy + cell_size],
            fill=color[:3],
            outline=(100, 100, 100),
        )
        # 编号 + 颜色名
        name = f"{code}"
        draw.text(
            (cx + cell_size + 12, cy + (cell_size - 14) // 2),
            name,
            fill=(30, 30, 30),
            font=body_font,
        )
        # 用量
        pct = count / total_beads * 100 if total_beads > 0 else 0
        count_text = f"{count:>5d} 颗 ({pct:4.1f}%)"
        draw.text(
            (cx + cell_size + 20 + label_w, cy + (cell_size - 14) // 2),
            count_text,
            fill=(80, 80, 80),
            font=body_font,
        )
        y_offset += row_height + 6

    return img


def render_pegboard_overlay(grid, palette, cell_size=10, board_size=29):
    """渲染带钉板网格线的预览（可选）"""
    height = len(grid)
    width = len(grid[0]) if grid else 0
    total_w = width * cell_size + (width // board_size) * 2
    total_h = height * cell_size + (height // board_size) * 2

    # 先画彩色预览
    preview = render_color_preview(grid, palette, cell_size)
    result = Image.new("RGBA", (total_w, total_h), (240, 240, 240, 255))

    # 粘贴预览图
    result.paste(preview, (0, 0))

    draw = ImageDraw.Draw(result)
    # 画钉板边界线
    for by in range(0, height, board_size):
        y_line = by * cell_size
        draw.line([(0, y_line), (total_w, y_line)], fill=(200, 0, 0, 120), width=2)
    for bx in range(0, width, board_size):
        x_line = bx * cell_size
        draw.line([(x_line, 0), (x_line, total_h)], fill=(200, 0, 0, 120), width=2)

    return result


# ─────────────────────────────────────────────
# CLI 主函数
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="🎨 perler-pattern — 图片转拼豆图纸生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s photo.jpg                        # 默认 29×29，Artkal S 色板
  %(prog)s photo.jpg -w 58 -h 58            # 2×2 板（58×58）
  %(prog)s photo.jpg -w 116 --aspect        # 保持宽高比，宽度 116
  %(prog)s photo.jpg --palette perler       # 使用 Perler 色板
  %(prog)s photo.jpg --palette custom --colors "#FF0000,#00FF00,#0000FF,#FFFFFF,#000000"
  %(prog)s photo.jpg --cell 16 --no-legend  # 增大格子，不生成图例
  %(prog)s photo.jpg --format json          # 输出 JSON 数据

支持的色板:
  artkal-s    Artkal S 系列 (默认，约 60 色)
  perler      Perler 品牌 (约 29 色)
  hama        Hama 品牌 (约 23 色)
  custom      自定义（需配合 --colors）
        """,
    )

    parser.add_argument("image", help="输入图片路径")
    parser.add_argument("-w", "--width", type=int, default=29, help="网格宽度（默认 29，标准钉板）")
    parser.add_argument("-H", "--height", type=int, default=None, help="网格高度（默认同宽度）")
    parser.add_argument("--aspect", action="store_true", help="保持原始宽高比（宽度固定，高度自动计算）")
    parser.add_argument("-p", "--palette", default="artkal-s", choices=list(PALETTES.keys()) + ["custom"],
                        help="色板选择（默认 artkal-s）")
    parser.add_argument("--colors", type=str, default=None,
                        help="自定义颜色列表，逗号分隔的 #RRGGBB 值（配合 --palette custom）")
    parser.add_argument("-c", "--cell", type=int, default=10, help="预览图格子像素大小（默认 10）")
    parser.add_argument("-o", "--output", type=str, default=None, help="输出文件名前缀（默认同输入文件名）")
    parser.add_argument("--no-preview", action="store_true", help="不生成彩色预览图")
    parser.add_argument("--no-pattern", action="store_true", help="不生成编号图纸")
    parser.add_argument("--no-legend", action="store_true", help="不生成颜色图例")
    parser.add_argument("--board-overlay", action="store_true", help="生成钉板分割线预览")
    parser.add_argument("--format", choices=["png", "json", "both"], default="png", help="输出格式（默认 png）")
    parser.add_argument("-q", "--quiet", action="store_true", help="静默模式")

    args = parser.parse_args()

    # 参数验证
    if not os.path.isfile(args.image):
        print(f"错误：文件不存在 — {args.image}", file=sys.stderr)
        sys.exit(1)

    if args.height is None:
        args.height = args.width

    # 加载调色板
    if args.palette == "custom":
        if not args.colors:
            print("错误：使用 custom 色板时需要指定 --colors", file=sys.stderr)
            sys.exit(1)
        color_list = [c.strip() for c in args.colors.split(",")]
        palette = build_custom_palette(color_list)
    else:
        palette = PALETTES[args.palette]

    # 输出文件名前缀
    if args.output:
        prefix = args.output
    else:
        prefix = Path(args.image).stem

    if not args.quiet:
        print(f"📐 网格尺寸: {args.width}×{args.height}")
        print(f"🎨 色板: {args.palette} ({len(palette)} 色)")

    # 1. 加载并缩放图片
    img = load_and_resize(args.image, args.width, args.height, keep_aspect=args.aspect)
    actual_w, actual_h = img.size

    if not args.quiet:
        if args.aspect:
            print(f"📐 实际尺寸（保持比例）: {actual_w}×{actual_h}")
        print(f"📦 总珠数: {actual_w * actual_h}")

    # 2. 量化颜色
    grid, stats = quantize_image(img, palette)

    if not args.quiet:
        print(f"🎯 使用了 {len(stats)} 种颜色")
        print()

    # 3. 生成输出
    outputs = []

    # 彩色预览
    if not args.no_preview:
        preview = render_color_preview(grid, palette, cell_size=args.cell)
        preview_path = f"{prefix}_preview.png"
        preview.save(preview_path)
        outputs.append(preview_path)
        if not args.quiet:
            print(f"✅ 彩色预览: {preview_path}")

    # 编号图纸
    if not args.no_pattern:
        pattern_cell = max(args.cell + 12, 24)
        pattern = render_numbered_pattern(grid, palette, cell_size=pattern_cell)
        pattern_path = f"{prefix}_pattern.png"
        pattern.save(pattern_path)
        outputs.append(pattern_path)
        if not args.quiet:
            print(f"✅ 编号图纸: {pattern_path}")

    # 颜色图例
    if not args.no_legend:
        legend = render_legend(palette, stats)
        legend_path = f"{prefix}_legend.png"
        legend.save(legend_path)
        outputs.append(legend_path)
        if not args.quiet:
            print(f"✅ 颜色图例: {legend_path}")

    # 钉板分割线预览
    if args.board_overlay:
        overlay = render_pegboard_overlay(grid, palette, cell_size=args.cell, board_size=29)
        overlay_path = f"{prefix}_board.png"
        overlay.save(overlay_path)
        outputs.append(overlay_path)
        if not args.quiet:
            print(f"✅ 钉板预览: {overlay_path}")

    # JSON 输出
    if args.format in ("json", "both"):
        json_data = {
            "meta": {
                "source": args.image,
                "palette": args.palette,
                "width": actual_w,
                "height": actual_h,
                "total_beads": actual_w * actual_h,
                "unique_colors": len(stats),
            },
            "colors": {code: {"rgb": list(palette[code][:3]), "count": count}
                       for code, count in stats.most_common()},
            "grid": grid,
        }
        json_path = f"{prefix}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        outputs.append(json_path)
        if not args.quiet:
            print(f"✅ JSON 数据: {json_path}")

    if not args.quiet:
        print(f"\n🎉 完成！共生成 {len(outputs)} 个文件。")

        # 打印用量排行 Top 10
        if stats:
            print("\n📊 用量排行 Top 10:")
            for code, count in stats.most_common(10):
                pct = count / sum(stats.values()) * 100
                print(f"   {code:>4s}: {count:>5d} 颗 ({pct:4.1f}%)")


if __name__ == "__main__":
    main()
