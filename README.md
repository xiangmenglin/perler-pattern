# 🎨 perler-pattern — 图片转拼豆图纸生成器

将任意图片转换为拼豆（Perler Beads）网格图纸，支持多种品牌色板和输出格式。

## 功能特性

- 🖼️ 支持 JPG / PNG / BMP / GIF / WebP 等常见图片格式
- 🎨 内置 **Artkal S**、**Perler**、**Hama** 三大品牌色板
- 🔧 支持自定义颜色列表
- 📐 支持标准板型 (29×29)、2×2 (58×58)、4×4 (116×116) 等任意尺寸
- 📊 自动统计每种颜色用量
- 🖨️ 输出三种图纸：彩色预览 / 编号图纸 / 颜色图例
- 💾 支持 PNG 图片和 JSON 数据两种输出格式
- 🎯 钉板分割线预览，方便拼装定位

## 安装

```bash
pip install Pillow
```

Python 3.7+ 即可，唯一的依赖是 [Pillow](https://pillow.readthedocs.io/)。

## 使用方法

### 基础用法

```bash
python perler_pattern.py photo.jpg
```

生成 `photo_preview.png`、`photo_pattern.png`、`photo_legend.png` 三个文件。

### 常用参数

```bash
# 指定网格尺寸 (58×58 = 2×2 标准板)
python perler_pattern.py photo.jpg -w 58 -H 58

# 保持原始宽高比（宽度固定为 116，高度自动计算）
python perler_pattern.py photo.jpg -w 116 --aspect

# 切换色板
python perler_pattern.py photo.jpg --palette perler
python perler_pattern.py photo.jpg --palette hama

# 使用自定义颜色
python perler_pattern.py photo.jpg --palette custom --colors "#FF0000,#00FF00,#0000FF,#FFFFFF,#000000"

# 增大预览格子尺寸
python perler_pattern.py photo.jpg --cell 16

# 生成钉板分割线预览
python perler_pattern.py photo.jpg --board-overlay

# 同时输出 JSON 数据
python perler_pattern.py photo.jpg --format both

# 只输出编号图纸，不生成预览和图例
python perler_pattern.py photo.jpg --no-preview --no-legend

# 指定输出文件名前缀
python perler_pattern.py photo.jpg -o my_design
```

### 全部参数一览

| 参数 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| `image` | | 必填 | 输入图片路径 |
| `--width` | `-w` | 29 | 网格宽度 |
| `--height` | `-H` | 同宽度 | 网格高度 |
| `--aspect` | | off | 保持原始宽高比 |
| `--palette` | `-p` | artkal-s | 色板选择 |
| `--colors` | | — | 自定义颜色 (#RRGGBB,逗号分隔) |
| `--cell` | `-c` | 10 | 预览格子像素大小 |
| `--output` | `-o` | 输入文件名 | 输出文件名前缀 |
| `--no-preview` | | off | 不生成彩色预览图 |
| `--no-pattern` | | off | 不生成编号图纸 |
| `--no-legend` | | off | 不生成颜色图例 |
| `--board-overlay` | | off | 生成钉板分割线预览 |
| `--format` | | png | 输出格式 (png/json/both) |
| `--quiet` | `-q` | off | 静默模式 |

## 输出文件说明

| 文件 | 说明 |
|------|------|
| `*_preview.png` | 彩色预览图，每个格子填充对应颜色 |
| `*_pattern.png` | 编号图纸，每格显示色板编号，方便按号找豆 |
| `*_legend.png` | 颜色图例，显示色块 + 编号 + 用量统计 |
| `*_board.png` | 钉板分割线预览（需 `--board-overlay`） |
| `*.json` | 完整数据（网格 + 元信息 + 颜色统计） |

## 支持的色板

### artkal-s（默认）
Artkal S 系列 5mm 拼豆，约 60 色，颜色丰富，推荐使用。

### perler
Perler 品牌，经典拼豆，约 29 色。

### hama
Hama 品牌，欧洲常用，约 23 色。

### custom
完全自定义色板，用 `--colors` 参数传入逗号分隔的十六进制颜色值。

## 输出示例

运行后会得到：

```
photo_preview.png   ← 彩色预览，直观看到成品效果
photo_pattern.png   ← 编号图纸，每个格子标注色号
photo_legend.png    ← 图例：每种颜色对应编号和用量
```

终端输出：

```
📐 网格尺寸: 58×58
🎨 色板: artkal-s (60 色)
📦 总珠数: 3364
🎯 使用了 12 种颜色

✅ 彩色预览: photo_preview.png
✅ 编号图纸: photo_pattern.png
✅ 颜色图例: photo_legend.png

🎉 完成！共生成 3 个文件。

📊 用量排行 Top 10:
    S05:   420 颗 (12.5%)
    S01:   380 颗 (11.3%)
    S57:   210 颗 ( 6.2%)
    ...
```

## 拼豆小贴士

1. **选板型**：标准 29×29 板是最常见的，58×58（2×2）适合中等尺寸作品
2. **图片预处理**：建议先用图片编辑软件裁剪好主体，效果更好
3. **颜色太多？**：用 `--palette perler` 减少到 29 色，或者 `--palette custom` 手动选色
4. **对细节不满意？**：增大网格尺寸（`-w 116`）会保留更多细节
5. **按图纸拼**：打印 `_pattern.png`，按编号找对应颜色的豆子

## License

MIT
