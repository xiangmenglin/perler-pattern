# 🎨 perler-pattern — 图片转拼豆图纸生成器

![Python](https://img.shields.io/badge/Python-3.7+-blue?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)
![Pillow](https://img.shields.io/badge/Pillow->=9.0-yellow)

将任意图片转换为拼豆（Perler Beads）网格图纸，支持真实品牌色板、控色和多种输出格式。

## 功能特性

- 🖼️ 支持 JPG / PNG / BMP / GIF / WebP 等常见图片格式
- 🎨 内置 **Artkal S**（199 色）、**Perler**（103 色）、**Hama**（92 色）、**MARD 221**（221 色）真实色卡
- 🔧 支持自定义颜色列表
- 🎛️ 可限制用色数量（`--max-colors`），避免大色板下颜色碎片化
- 📐 支持标准板型 (29×29)、2×2 (58×58)、4×4 (116×116) 等任意尺寸
- 📊 自动统计每种颜色用量
- 🖨️ 输出彩色预览 / 编号图纸 / 颜色图例，可选钉板分割线预览
- 🧭 预览图 / 编号图纸四周自带**行列计数标尺**（每 5 格标数字，可用 `--no-rulers` 关闭）
- 💾 支持 PNG 图片和 JSON 数据两种输出格式

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
python perler_pattern.py photo.jpg --palette mard      # MARD 221（国内主流）

# 使用自定义颜色
python perler_pattern.py photo.jpg --palette custom --colors "#FF0000,#00FF00,#0000FF,#FFFFFF,#000000"

# 控制用色数量（大色板下推荐，买豆更省事）
python perler_pattern.py photo.jpg -w 58 -p mard --max-colors 30

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

```bash
# 标尺每 10 格标一次（默认 5 格），或者关掉标尺
python perler_pattern.py photo.jpg -w 58 --ruler-step 10
python perler_pattern.py photo.jpg -w 58 --no-rulers
```

### 全部参数一览

| 参数 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| `image` | | 必填 | 输入图片路径 |
| `--width` | `-w` | 29 | 网格宽度 |
| `--height` | `-H` | 同宽度 | 网格高度 |
| `--aspect` | | off | 保持原始宽高比（省略 -H 时宽度固定，高度自动） |
| `--palette` | `-p` | artkal-s | 色板选择 |
| `--colors` | | — | 自定义颜色 (#RRGGBB / #RGB，逗号分隔) |
| `--cell` | `-c` | 10 | 预览格子像素大小 |
| `--max-colors` | | 0（不限） | 先把图片量化到 N 色以内再匹配色板 |
| `--output` | `-o` | 输入文件名 | 输出文件名前缀 |
| `--no-preview` | | off | 不生成彩色预览图 |
| `--no-pattern` | | off | 不生成编号图纸 |
| `--no-legend` | | off | 不生成颜色图例 |
| `--board-overlay` | | off | 生成钉板分割线预览 |
| `--no-rulers` | | off | 不添加行列计数标尺 |
| `--ruler-step` | | 5 | 标尺数字间隔（1 = 逐格标注） |
| `--format` | | png | 输出格式 (png/json/both) |
| `--quiet` | `-q` | off | 静默模式 |

## 输出文件说明

| 文件 | 说明 |
|------|------|
| `*_preview.png` | 彩色预览图，每格填充对应颜色 |
| `*_pattern.png` | 编号图纸，每格标色号（长编码自动缩字号），按号找豆 |
| `*_legend.png` | 颜色图例：色块 + 色号 + 官方名称 + 用量占比 |
| `*_board.png` | 钉板分割线预览（需 `--board-overlay`） |
| `*.json` | 完整数据（网格 + 元信息 + 每色 rgb / name / count） |

`_preview` / `_pattern` / `_board` 三张图默认四周带行列计数标尺：上下是列号、左右是行号，每 5 格标一个数字（首尾必标），每个格子边界都有小刻度，方便对着图纸数行数和列数。

## 支持的色板

色卡数据全部取自开源的**真实官方色卡**（官方色号；Artkal / Perler / Hama 另带官方颜色名，MARD 官方数据只有色号），照着图纸买豆不会买错色：

| 色板 | 色数 | 说明 |
|------|------|------|
| `artkal-s`（默认） | 199 | Artkal S 系列及珠光 / 夜光 / 闪粉 / 透明等变体，国内常见 |
| `perler` | 103 | Perler 官方 SKU 编码（如 `80-15179`） |
| `hama` | 92 | Hama 欧洲色卡（H01–H92） |
| `mard` | 221 | MARD 221（国内最主流、社区默认参考色卡） |
| `custom` | — | 完全自定义，用 `--colors` 传入逗号分隔的十六进制颜色值 |

数据来源（均为 MIT 许可）：

- Artkal S / Perler / Hama：[maxcleme/beadcolors](https://github.com/maxcleme/beadcolors)
- MARD 221：[HansBug/pindou-color-data](https://github.com/HansBug/pindou-color-data)

编号图纸里 Perler 的 8 位 SKU 会自动缩小字号；图例中同时显示色号与颜色名称（如 `S05  Tall Poppy`），MARD 只显示色号（如 `H16`）。

## 输出示例

运行后会得到：

```
photo_preview.png   ← 彩色预览，直观看到成品效果
photo_pattern.png   ← 编号图纸，每个格子标注色号
photo_legend.png    ← 图例：色块 + 色号 + 名称 + 用量
```

终端输出（58×58，MARD 221 色板，`--max-colors 30`）：

```
📐 网格尺寸: 58×58
🎨 色板: mard (221 色)
🎛️  颜色量化: 先压缩到 30 色以内
📦 总珠数: 3364（空位 0）
🎯 使用了 17 种颜色

✅ 彩色预览: photo_preview.png
✅ 编号图纸: photo_pattern.png
✅ 颜色图例: photo_legend.png

🎉 完成！共生成 3 个文件。

📊 用量排行 Top 10:
    H16:   499 颗 (14.8%)
     M3:   450 颗 (13.4%)
     H6:   329 颗 ( 9.8%)
    C29:   318 颗 ( 9.5%)
    C22:   299 颗 ( 8.9%)
    ...
```

## 性能

逐像素最近色匹配是大图的主要开销。脚本做了几层优化，**结果与全量扫描完全一致**（不是近似）：

- 调色板展平成数组，并按 G 通道排序建索引：加权距离里 G 的系数恒为 4（最大），所以按 G 距离由近到远扩展、一旦 `4·Δg² ≥ 当前最优` 就停（严格下界，不会漏掉更近的颜色）
- 半透明混白交给 Pillow 的 `alpha_composite` 一次算完，省掉逐像素浮点运算
- 按像素颜色去重缓存：缩放后的图有大量重复色，只对唯一色搜一次
- 色块图用 P 模式 + NEAREST 放大（C 层一次完成），网格线整图一次画完，色号文字每种只渲染一次再逐格粘贴
- 编号图纸输出 RGB（而非 RGBA），PNG 编码更快、文件更小

实测（Python 3.14 + Pillow 12，本地测试图，三张图全出）：

| 网格 | 优化前 | 优化后 |
|------|--------|--------|
| 58×58 | 0.90s | 0.58s |
| 116×116 | 1.95s | 0.80s |
| 200×200 | 4.65s | 1.29s |
| 300×300 | 9.74s | 2.12s |
| 500×500 | — | 4.37s |

加 `--max-colors 30` 还能再快一截（300×300 时 2.12s → 1.57s），因为最近色搜索的候选基本被去重吸收掉了。大图剩余开销主要是 PNG 编码本身。

## 拼豆小贴士

1. **选板型**：标准 29×29 板是最常见的，58×58（2×2）适合中等尺寸作品
2. **图片预处理**：建议先用图片编辑软件裁剪好主体，效果更好
3. **颜色太多？**：色板越大，逐像素匹配越容易把相近色打散（背景灰黑可能变成十几种灰）。加 `--max-colors 20`～`30` 先把图片量化到 N 色，选出的豆子种类会明显变少
4. **换更小的色卡**：`--palette perler`（103 色）或 `--palette hama`（92 色），或者 `--palette custom` 手动选色
5. **对细节不满意？**：增大网格尺寸（`-w 116`）会保留更多细节
6. **按图纸拼**：打印 `_pattern.png`，按色号找对应颜色的豆子；买豆时对照 `_legend.png` 里的色号清单
7. **数格子**：图纸四周有行列标尺，拼长排珠子时用它数到第几行、第几列，不容易串行

## 常见问题

**保存时报 `OSError: [Errno 22] Invalid argument`？**

目标 png 正被其它程序打开（Windows 照片、资源管理器预览窗格、部分看图软件会把图片映射进内存，映射中的文件无法被截断覆盖）。现在脚本先写临时文件再替换，替换失败会自动改存为 `xxx_pattern~1.png` 并在 stderr 提示，不会中断。关掉看图软件后重跑，就能拿回原本的文件名。

## License

MIT
