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
import bisect
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
# 标准拼豆色板定义（真实色卡数据）
# ─────────────────────────────────────────────
# 数据来源（均为 MIT 许可的开源色卡库）：
#   Artkal S / Perler / Hama —— github.com/maxcleme/beadcolors
#   MARD 221 —— github.com/HansBug/pindou-color-data
# 每个颜色：色号 -> (R, G, B, 名称)

# Artkal S 系列 (5mm) — 199 色
ARTKAL_S = {
    "S01": (234, 238, 243, "White"),
    "S02": (238, 146, 124, "Burning Sand"),
    "S03": (255, 166, 48, "Tangerine"),
    "S04": (235, 96, 39, "Orange"),
    "S05": (203, 53, 49, "Tall Poppy"),
    "S06": (239, 103, 178, "Raspberry Pink"),
    "S07": (149, 150, 152, "Gray"),
    "S08": (31, 196, 103, "Emerald"),
    "S09": (0, 104, 94, "Dark Green"),
    "S10": (46, 171, 216, "Baby Blue"),
    "S11": (0, 79, 164, "Dark Blue"),
    "S12": (145, 101, 178, "Pastel Lavender"),
    "S13": (41, 42, 43, "Black"),
    "S14": (225, 200, 53, "Sandstorm"),
    "S15": (154, 69, 65, "Redwood"),
    "S16": (101, 70, 61, "Brown"),
    "S17": (137, 93, 73, "Light Brown"),
    "S18": (220, 163, 132, "Sand"),
    "S19": (242, 191, 184, "Bubble Gun"),
    "S20": (0, 144, 83, "Green"),
    "S21": (139, 178, 58, "Pastel Green"),
    "S22": (72, 51, 126, "Purple"),
    "S23": (100, 79, 164, "Royal Purple"),
    "S24": (0, 120, 191, "True Blue"),
    "S25": (220, 81, 154, "Hot Pink"),
    "S26": (218, 67, 131, "Magenta"),
    "S27": (234, 193, 37, "Yellow"),
    "S28": (221, 161, 204, "Lily Pink"),
    "S29": (225, 211, 103, "Pastel Yellow"),
    "S30": (158, 201, 205, "Shadow Green"),
    "S31": (178, 215, 206, "Sea Mist"),
    "S32": (238, 211, 158, "Beeswax"),
    "S33": (192, 183, 215, "Maverick"),
    "S34": (182, 25, 39, "Red"),
    "S35": (225, 204, 210, "Mona Lisa"),
    "S36": (206, 109, 131, "Old Pink"),
    "S37": (96, 191, 203, "Blue-Green"),
    "S38": (163, 19, 74, "Burgundy"),
    "S39": (230, 135, 57, "Yellow Orange"),
    "S40": (225, 130, 176, "Carnation Pink"),
    "S41": (157, 91, 46, "Copper"),
    "S42": (103, 107, 115, "Silver"),
    "S43": (112, 117, 123, "Dark Gray"),
    "S44": (167, 205, 222, "Sky Blue"),
    "S45": (0, 165, 161, "Medium Turquoise"),
    "S46": (142, 195, 36, "Bright Green"),
    "S47": (178, 121, 56, "Marigold"),
    "S48": (236, 192, 61, "Corn"),
    "S49": (146, 30, 93, "Mulberry Wood"),
    "S50": (226, 164, 136, "Mandys Pink"),
    "S51": (223, 218, 189, "Spring Sun"),
    "S52": (234, 222, 127, "Picasso"),
    "S53": (85, 164, 217, "Turquoise"),
    "S54": (0, 132, 206, "Light Blue"),
    "S55": (151, 207, 135, "Pistachio"),
    "S56": (249, 111, 64, "Bright Carrot"),
    "S57": (179, 85, 64, "Buccaneer"),
    "S58": (177, 24, 54, "Paprika"),
    "S59": (79, 57, 137, "Butterfly Bush"),
    "S60": (138, 126, 194, "Lavender"),
    "S61": (205, 192, 63, "Key Lomen Pie"),
    "S62": (0, 118, 95, "Green Tea"),
    "S63": (105, 96, 70, "Metallic Gold"),
    "S64": (54, 56, 77, "Black Rock"),
    "S65": (226, 230, 93, "Canary"),
    "S66": (229, 83, 60, "Blaze Orange"),
    "S67": (233, 193, 166, "Vanilla"),
    "S68": (204, 155, 116, "Tan"),
    "S69": (56, 62, 68, "Mine Shaft"),
    "S70": (173, 173, 41, "Drark Algae"),
    "S71": (0, 125, 43, "Jade Green"),
    "S72": (104, 196, 210, "Light Sea Blue"),
    "S73": (90, 176, 191, "Steel Blue"),
    "S74": (0, 158, 194, "Azure"),
    "S75": (0, 132, 178, "Dark Steel Blue"),
    "S76": (0, 147, 169, "Sea Blue"),
    "S77": (212, 216, 211, "Ghost While"),
    "S78": (194, 196, 194, "Ash Grey"),
    "S79": (167, 172, 173, "Light Gray"),
    "S80": (143, 142, 60, "Dark Olive"),
    "S81": (191, 145, 104, "Deer"),
    "S82": (170, 116, 78, "Clay"),
    "S83": (187, 104, 51, "Sienna"),
    "S84": (190, 93, 101, "Deep Chestnut"),
    "S85": (153, 50, 58, "Red Wine"),
    "S86": (232, 174, 0, "Goldenrod"),
    "S87": (236, 98, 94, "Coral Red"),
    "S88": (214, 39, 121, "Dark Pink"),
    "S89": (86, 90, 94, "Charcoal Gray"),
    "S90": (217, 179, 94, "Pastel Orange"),
    "S91": (21, 56, 56, "Brunswick Green"),
    "S92": (206, 164, 51, "Dandelion"),
    "S93": (220, 183, 148, "Pale Skin"),
    "S94": (221, 146, 133, "Warm Blush"),
    "S95": (224, 123, 105, "Salmon"),
    "S96": (239, 127, 97, "Apricot"),
    "S97": (220, 119, 43, "Papaya"),
    "S98": (106, 174, 219, "Himalaya Blue"),
    "S99": (97, 187, 211, "Waterfall"),
    "S100": (39, 155, 190, "Lagoon"),
    "S101": (0, 167, 227, "Electric Blue"),
    "S102": (0, 119, 202, "Pool Blue"),
    "S103": (0, 90, 169, "Caribbian Blue"),
    "S104": (0, 127, 158, "Deep Water"),
    "S105": (0, 125, 145, "Petrol Blue"),
    "S106": (0, 100, 154, "Wegdewood Blue"),
    "S107": (0, 108, 159, "Pond Blue"),
    "S108": (207, 193, 121, "Seashell Beige"),
    "S109": (196, 174, 100, "Beige"),
    "S110": (171, 151, 69, "Beach Beige"),
    "S111": (151, 129, 56, "Caffe Latté"),
    "S112": (144, 124, 65, "Oaktree Brown"),
    "S113": (182, 174, 132, "Khaki"),
    "S114": (165, 159, 101, "Light Greengray"),
    "S115": (147, 141, 84, "Mossy Green"),
    "S116": (141, 139, 81, "Earth Green"),
    "S117": (127, 126, 73, "Sage Green"),
    "S118": (91, 110, 53, "Pinetree Green"),
    "S119": (138, 213, 201, "Frosty Blue"),
    "S120": (124, 210, 165, "Polar Mint"),
    "S121": (114, 172, 154, "Celadon Green"),
    "S122": (0, 178, 111, "Eucalyptus"),
    "S123": (62, 183, 36, "Clover Field"),
    "S124": (13, 117, 53, "Pooltable Felt"),
    "S125": (0, 125, 110, "Snake Green"),
    "S126": (0, 110, 105, "Dark Eucalyptus"),
    "S127": (223, 195, 225, "Marsmallow Rose"),
    "S128": (211, 142, 212, "Light Grape"),
    "S129": (213, 166, 186, "Rosebud Pink"),
    "S130": (214, 102, 142, "Fuschia"),
    "S131": (184, 170, 217, "Candy Violet"),
    "S132": (223, 72, 109, "Flamingo"),
    "S133": (188, 60, 166, "Pink Plum"),
    "S134": (128, 56, 151, "Amethyst"),
    "S135": (167, 186, 225, "Moonlight Blue"),
    "S136": (175, 184, 223, "Summer Rain"),
    "S137": (107, 154, 212, "Azur Blue"),
    "S138": (90, 137, 206, "Cornflower Blue"),
    "S139": (101, 138, 208, "Forget Me Not"),
    "S140": (86, 108, 189, "Indigo"),
    "S141": (77, 116, 198, "Horizon Blue"),
    "S142": (65, 109, 190, "Cobolt"),
    "S143": (48, 66, 158, "Royal Blue"),
    "S144": (2, 66, 136, "Marine"),
    "S145": (214, 202, 106, "Pale Yellow Moss"),
    "S146": (157, 26, 56, "Bloodrose Red"),
    "S147": (128, 183, 161, "Spearmint"),
    "S148": (122, 89, 79, "Mocha"),
    "S149": (239, 219, 161, "Creme"),
    "S150": (136, 132, 208, "Iris Violet"),
    "S151": (52, 86, 33, "Forrest Green"),
    "S152": (174, 173, 220, "Lilac"),
    "S153": (188, 195, 225, "Pale Lilac"),
    "S154": (227, 192, 154, "Sahara Sand"),
    "S155": (197, 139, 96, "Sunkissed Teint"),
    "S156": (90, 95, 101, "Steel Grey"),
    "S157": (76, 81, 86, "Iron Grey"),
    "S158": (58, 62, 66, "Pepper"),
    "S159": (130, 135, 139, "Oslo Gray"),
    "SE1": (241, 244, 250, "Moon"),
    "SE2": (162, 178, 211, "Raincloud"),
    "SE3": (131, 166, 220, "Winter"),
    "SE4": (112, 216, 237, "Tide"),
    "SE5": (105, 227, 213, "Aquamarine"),
    "SE6": (42, 99, 200, "Neptune"),
    "SE7": (213, 174, 201, "Rose Quartz"),
    "SE8": (175, 115, 154, "Mauve"),
    "SE9": (112, 75, 109, "Dark Mauve"),
    "SE10": (217, 119, 205, "Wild Berry"),
    "SE11": (182, 67, 172, "Sugar Plum"),
    "SE12": (222, 177, 129, "Desert"),
    "SE13": (188, 157, 119, "Peanut"),
    "SE14": (172, 127, 93, "Toffee"),
    "SE15": (163, 126, 102, "Bark"),
    "SG1": (198, 192, 180, "Glow Yellow"),
    "SG2": (223, 171, 188, "Glow Pink"),
    "SG3": (111, 173, 193, "Glow Blue"),
    "SL1": (54, 135, 178, "Glitter Blue"),
    "SL2": (17, 124, 82, "Glitter Green"),
    "SL3": (194, 41, 51, "Glitter Red"),
    "SL4": (205, 189, 0, "Glitter Yellow"),
    "SN1": (255, 116, 5, "Neon Orange"),
    "SN2": (1, 198, 62, "Neon Green"),
    "SN3": (242, 243, 60, "Neon Yellow"),
    "SN4": (255, 71, 122, "Neon Rose"),
    "SP1": (147, 202, 135, "Pearlescent Green"),
    "SP2": (254, 127, 84, "Pearlescent Tangerine"),
    "SP3": (240, 161, 73, "Pearlescent Orange"),
    "SP4": (220, 158, 169, "Pearlescent Pink"),
    "SP5": (214, 60, 83, "Pearlescent Red"),
    "SP6": (44, 78, 151, "Pearlescent Blue"),
    "SP7": (100, 66, 126, "Pearlescent Purple"),
    "SP8": (224, 219, 202, "Pearlescent White"),
    "ST1": (199, 188, 184, "Transparent"),
    "ST2": (249, 84, 152, "Transparent Pink"),
    "ST3": (255, 124, 69, "Transparent Tangering"),
    "ST4": (218, 223, 61, "Transparent Yellow"),
    "ST5": (15, 174, 88, "Transparent Green"),
    "ST6": (132, 119, 179, "Transparent Purple"),
}

# Perler — 103 色（官方 SKU 编码）
PERLER = {
    "80-15179": (48, 85, 69, "Evergreen"),
    "80-15181": (179, 186, 184, "Light Grey"),
    "80-15182": (175, 159, 206, "Lavender"),
    "80-15199": (0, 143, 83, "Shamrock"),
    "80-15200": (0, 101, 177, "Cobalt"),
    "80-15201": (47, 60, 85, "Midnight"),
    "80-15202": (169, 205, 213, "Robin's Egg"),
    "80-15203": (242, 175, 183, "Flamingo"),
    "80-15204": (225, 116, 122, "Salmon"),
    "80-15205": (201, 163, 133, "Fawn"),
    "80-15206": (148, 161, 157, "Pewter"),
    "80-15207": (79, 89, 90, "Charcoal"),
    "80-15208": (222, 218, 206, "Toasted Marshmallow"),
    "80-15210": (177, 98, 142, "Orchid"),
    "80-15211": (209, 67, 55, "Tomato"),
    "80-15212": (217, 89, 58, "Spice"),
    "80-15213": (245, 161, 104, "Apricot"),
    "80-15214": (216, 228, 124, "Sherbet"),
    "80-15215": (147, 176, 189, "Mist"),
    "80-15216": (74, 192, 216, "Sky"),
    "80-15217": (0, 164, 172, "Lagoon"),
    "80-15218": (4, 127, 138, "Teal"),
    "80-15219": (127, 151, 26, "Fern"),
    "80-15220": (105, 110, 49, "Olive"),
    "80-15961": (157, 43, 58, "Cherry"),
    "80-19001": (234, 239, 238, "White"),
    "80-19002": (225, 226, 187, "Creme"),
    "80-19003": (231, 206, 62, "Yellow"),
    "80-19004": (235, 123, 49, "Orange"),
    "80-19005": (176, 53, 60, "Red"),
    "80-19006": (216, 114, 154, "Bubblegum"),
    "80-19007": (104, 75, 134, "Purple"),
    "80-19008": (14, 80, 146, "Dark Blue"),
    "80-19009": (39, 140, 201, "Light Blue"),
    "80-19010": (0, 123, 78, "Dark Green"),
    "80-19011": (24, 199, 177, "Light Green"),
    "80-19012": (103, 76, 68, "Brown"),
    "80-19017": (144, 148, 151, "Grey"),
    "80-19018": (50, 50, 52, "Black"),
    "80-19020": (153, 80, 67, "Rust"),
    "80-19021": (147, 104, 72, "Light Brown"),
    "80-19033": (233, 191, 185, "Peach"),
    "80-19035": (197, 172, 144, "Tan"),
    "80-19038": (224, 66, 132, "Magenta"),
    "80-19052": (74, 156, 207, "Pastel Blue"),
    "80-19053": (109, 204, 148, "Pastel Green"),
    "80-19054": (147, 127, 191, "Pastel Lavender"),
    "80-19056": (233, 226, 144, "Pastel Yellow"),
    "80-19057": (251, 177, 70, "Cheddar"),
    "80-19058": (150, 209, 212, "Toothpaste"),
    "80-19059": (221, 89, 91, "Hot Coral"),
    "80-19060": (167, 93, 157, "Plum"),
    "80-19061": (105, 184, 69, "Kiwi Lime"),
    "80-19062": (0, 152, 197, "Turquoise"),
    "80-19063": (249, 146, 151, "Blush"),
    "80-19070": (102, 131, 183, "Periwinkle Blue"),
    "80-19079": (225, 188, 206, "Light Pink"),
    "80-19080": (77, 171, 100, "Green"),
    "80-19083": (212, 84, 150, "Pink"),
    "80-19088": (152, 56, 100, "Raspberry"),
    "80-19090": (218, 153, 100, "Butterscotch"),
    "80-19091": (0, 145, 136, "Parrot Green"),
    "80-19092": (88, 92, 97, "Dark Grey"),
    "80-19093": (133, 168, 227, "Blueberry Creme"),
    "80-19096": (132, 57, 71, "Cranapple"),
    "80-19097": (187, 201, 56, "Prickly Pear"),
    "80-19098": (229, 190, 158, "Sand"),
    "80-15240": (179, 238, 213, "Mint"),
    "80-15241": (163, 222, 111, "Sour Apple"),
    "80-15242": (244, 121, 176, "Cotton Candy"),
    "80-15243": (80, 59, 156, "Grape"),
    "80-15244": (210, 93, 114, "Rose"),
    "80-15245": (78, 86, 163, "Iris"),
    "80-15246": (253, 89, 24, "Tangerine"),
    "80-15247": (0, 93, 87, "Forest"),
    "80-15248": (111, 50, 85, "Eggplant"),
    "80-15249": (218, 140, 44, "Honey"),
    "80-15250": (126, 84, 70, "Gingerbread"),
    "80-15251": (140, 140, 167, "Thistle"),
    "80-15252": (94, 109, 123, "Slate Blue"),
    "80-15253": (76, 99, 136, "Denim"),
    "80-15254": (154, 169, 142, "Sage"),
    "80-15255": (239, 183, 155, "Orange Cream"),
    "80-15256": (202, 59, 101, "Fruit Punch"),
    "80-15257": (203, 89, 185, "Fuchsia"),
    "80-15258": (113, 72, 117, "Mulberry"),
    "80-15259": (200, 200, 92, "Slime"),
    "80-15260": (152, 140, 140, "Stone"),
    "80-15261": (20, 49, 59, "Dark Spruce"),
    "80-15262": (57, 41, 40, "Cocoa"),
    "80-15265": (198, 133, 177, "Twilight Plum"),
    "80-15266": (108, 200, 173, "Caribbean Sea"),
    "80-15267": (205, 183, 195, "Frosted Lilac"),
    "80-15273": (252, 149, 116, "Brick"),
    "80-15274": (246, 202, 105, "Rich Butter"),
    "80-15275": (0, 144, 172, "Peacock"),
    "80-15276": (248, 199, 201, "Carnation Pink"),
    "80-15089": (64, 106, 225, "Neon Blue"),
    "80-15268": (222, 186, 11, "Sunflower"),
    "80-15269": (246, 217, 1, "Lemon"),
    "80-15263": (190, 212, 166, "Celery"),
    "80-15239": (200, 182, 147, "Mocha"),
    "80-15272": (255, 154, 139, "Coral"),
}

# Hama — 92 色
HAMA = {
    "H01": (229, 236, 241, "White"),
    "H02": (228, 228, 197, "Cream"),
    "H03": (233, 199, 4, "Yellow"),
    "H04": (209, 72, 3, "Orange"),
    "H05": (180, 6, 14, "Red"),
    "H06": (234, 138, 165, "Pink"),
    "H07": (113, 34, 151, "Purple"),
    "H08": (2, 57, 163, "Blue"),
    "H09": (2, 91, 195, "Light Blue"),
    "H10": (2, 118, 67, "Green"),
    "H11": (25, 205, 167, "Light Green"),
    "H12": (62, 39, 26, "Brown"),
    "H13": (192, 36, 53, "Transparent Red"),
    "H14": (228, 170, 50, "Transparent Yellow"),
    "H16": (55, 184, 118, "Transparent Green"),
    "H17": (131, 143, 152, "Grey"),
    "H18": (20, 19, 21, "Black"),
    "H19": (216, 210, 206, "Clear"),
    "H20": (141, 42, 15, "Reddish Brown"),
    "H21": (190, 108, 33, "Light Brown"),
    "H22": (145, 2, 10, "Dark Red"),
    "H24": (104, 62, 154, "Translucent Purple"),
    "H25": (135, 89, 61, "Translucent Brown"),
    "H26": (232, 164, 152, "Matt Rose"),
    "H27": (220, 177, 142, "Beige"),
    "H28": (30, 44, 28, "Dark Green"),
    "H29": (191, 1, 66, "Claret"),
    "H30": (78, 12, 27, "Burgundy"),
    "H31": (72, 154, 185, "Turquoise"),
    "H32": (255, 32, 141, "Neon Fuchsia"),
    "H33": (255, 57, 86, "Cerise"),
    "H34": (229, 239, 19, "Neon Yellow"),
    "H35": (255, 40, 51, "Neon Red"),
    "H36": (35, 83, 176, "Neon Blue"),
    "H37": (6, 183, 60, "Neon Green"),
    "H38": (253, 134, 0, "Neon Orange"),
    "H39": (241, 242, 28, "Fluorescent Yellow"),
    "H40": (254, 99, 11, "Fluorescent Orange"),
    "H41": (38, 89, 178, "Fluorescent Blue"),
    "H42": (12, 189, 81, "Fluorescent Green"),
    "H43": (231, 228, 90, "Pastel Yellow"),
    "H44": (249, 97, 96, "Pastel Red"),
    "H45": (142, 105, 205, "Pastel Purple"),
    "H46": (81, 174, 228, "Pastel Blue"),
    "H47": (128, 223, 150, "Pastel Green"),
    "H48": (214, 122, 209, "Pastel Pink"),
    "H49": (15, 172, 209, "Azure"),
    "H60": (240, 152, 30, "Teddybear Brown"),
    "H70": (165, 179, 192, "Light Grey"),
    "H71": (68, 80, 89, "Dark Grey"),
    "H75": (183, 140, 109, "Tan"),
    "H76": (138, 89, 55, "Nougat"),
    "H77": (206, 209, 200, "Cloudy White"),
    "H78": (247, 193, 170, "Light Peach"),
    "H79": (248, 118, 51, "Apricot"),
    "H82": (145, 23, 90, "Plum"),
    "H83": (3, 122, 159, "Petrol Blue"),
    "H84": (104, 120, 54, "Olive Green"),
    "H95": (221, 155, 163, "Pastel Rose"),
    "H96": (180, 145, 173, "Pastel Lilac"),
    "H97": (138, 175, 194, "Pastel Ice Blue"),
    "H98": (148, 204, 164, "Pastel Mint"),
    "H15": (72, 126, 213, "Transparent Blue"),
    "H55": (250, 248, 237, "Green (Glow in the Dark)"),
    "H56": (237, 191, 159, "Red (Glow in the Dark)"),
    "H57": (196, 208, 227, "Blue (Glow in the Dark)"),
    "H61": (217, 147, 80, "Gold"),
    "H62": (72, 71, 74, "Silver"),
    "H63": (66, 49, 47, "Bronze"),
    "H64": (239, 235, 228, "Pearl"),
    "H72": (240, 151, 176, "Translucent Pink"),
    "H73": (89, 174, 245, "Translucent Aqua"),
    "H74": (91, 85, 189, "Translucent Lilac"),
    "H101": (169, 195, 155, "Eucalyptus"),
    "H102": (53, 107, 45, "Forest Green"),
    "H103": (255, 230, 96, "Light Yellow"),
    "H104": (188, 209, 34, "Lime"),
    "H105": (255, 172, 120, "Light Apricot"),
    "H106": (204, 197, 237, "Light Lavender"),
    "H107": (106, 135, 193, "Lavender"),
    "H108": (42, 37, 54, "Aubergine"),
    "H109": (138, 132, 127, "Cloudy Grey"),
    "H110": (131, 137, 86, "Matcha"),
    "H111": (131, 88, 84, "Dark Blush"),
    "H112": (173, 138, 130, "Blush"),
    "H113": (95, 136, 123, "Aqua"),
    "H114": (154, 44, 49, "Cherry Red"),
    "H115": (110, 151, 95, "Bright Green"),
    "H116": (34, 40, 56, "Midnight Blue"),
    "H117": (119, 113, 105, "Taupe Grey"),
    "H118": (97, 41, 50, "Maroon Red"),
    "H119": (65, 103, 180, "Sky Blue"),
}

# MARD 221 — 221 色（国内主流色卡）
MARD = {
    "A1": (250, 245, 205, ""),
    "A2": (252, 254, 214, ""),
    "A3": (252, 255, 146, ""),
    "A4": (247, 236, 92, ""),
    "A5": (255, 228, 75, ""),
    "A6": (253, 169, 81, ""),
    "A7": (250, 140, 79, ""),
    "A8": (249, 224, 69, ""),
    "A9": (249, 156, 95, ""),
    "A10": (244, 126, 54, ""),
    "A11": (254, 219, 153, ""),
    "A12": (253, 162, 118, ""),
    "A13": (254, 198, 103, ""),
    "A14": (248, 88, 66, ""),
    "A15": (251, 246, 94, ""),
    "A16": (254, 255, 151, ""),
    "A17": (253, 225, 115, ""),
    "A18": (252, 191, 128, ""),
    "A19": (253, 126, 119, ""),
    "A20": (249, 214, 110, ""),
    "A21": (250, 227, 147, ""),
    "A22": (237, 248, 120, ""),
    "A23": (225, 201, 189, ""),
    "A24": (243, 246, 169, ""),
    "A25": (255, 215, 133, ""),
    "A26": (254, 200, 50, ""),
    "B1": (223, 241, 57, ""),
    "B2": (100, 243, 67, ""),
    "B3": (159, 246, 133, ""),
    "B4": (95, 223, 52, ""),
    "B5": (57, 225, 88, ""),
    "B6": (100, 224, 164, ""),
    "B7": (63, 174, 124, ""),
    "B8": (29, 158, 84, ""),
    "B9": (42, 80, 55, ""),
    "B10": (154, 209, 186, ""),
    "B11": (98, 112, 50, ""),
    "B12": (26, 110, 61, ""),
    "B13": (200, 232, 125, ""),
    "B14": (172, 232, 76, ""),
    "B15": (48, 83, 53, ""),
    "B16": (192, 237, 156, ""),
    "B17": (158, 179, 62, ""),
    "B18": (230, 237, 79, ""),
    "B19": (38, 183, 142, ""),
    "B20": (202, 237, 207, ""),
    "B21": (23, 98, 104, ""),
    "B22": (10, 66, 65, ""),
    "B23": (52, 59, 26, ""),
    "B24": (232, 250, 166, ""),
    "B25": (78, 132, 109, ""),
    "B26": (144, 124, 53, ""),
    "B27": (208, 224, 175, ""),
    "B28": (158, 229, 187, ""),
    "B29": (198, 223, 95, ""),
    "B30": (227, 251, 177, ""),
    "B31": (178, 230, 148, ""),
    "B32": (146, 173, 96, ""),
    "C1": (232, 255, 231, ""),
    "C2": (171, 248, 254, ""),
    "C3": (158, 224, 248, ""),
    "C4": (68, 205, 251, ""),
    "C5": (6, 171, 227, ""),
    "C6": (84, 167, 233, ""),
    "C7": (57, 119, 204, ""),
    "C8": (15, 82, 189, ""),
    "C9": (51, 73, 195, ""),
    "C10": (61, 187, 227, ""),
    "C11": (42, 222, 211, ""),
    "C12": (30, 51, 78, ""),
    "C13": (205, 231, 254, ""),
    "C14": (214, 253, 252, ""),
    "C15": (33, 197, 196, ""),
    "C16": (24, 88, 162, ""),
    "C17": (2, 209, 243, ""),
    "C18": (33, 50, 68, ""),
    "C19": (24, 134, 144, ""),
    "C20": (26, 112, 169, ""),
    "C21": (190, 221, 252, ""),
    "C22": (107, 177, 187, ""),
    "C23": (200, 226, 249, ""),
    "C24": (126, 197, 249, ""),
    "C25": (169, 232, 224, ""),
    "C26": (66, 173, 209, ""),
    "C27": (208, 222, 239, ""),
    "C28": (189, 206, 237, ""),
    "C29": (54, 74, 137, ""),
    "D1": (172, 183, 239, ""),
    "D2": (134, 141, 211, ""),
    "D3": (54, 83, 175, ""),
    "D4": (22, 44, 126, ""),
    "D5": (179, 78, 198, ""),
    "D6": (179, 123, 220, ""),
    "D7": (135, 88, 169, ""),
    "D8": (227, 210, 254, ""),
    "D9": (214, 186, 245, ""),
    "D10": (48, 26, 73, ""),
    "D11": (188, 186, 226, ""),
    "D12": (220, 153, 206, ""),
    "D13": (181, 3, 143, ""),
    "D14": (136, 40, 147, ""),
    "D15": (47, 30, 142, ""),
    "D16": (226, 228, 240, ""),
    "D17": (199, 211, 249, ""),
    "D18": (154, 100, 184, ""),
    "D19": (216, 194, 217, ""),
    "D20": (156, 52, 173, ""),
    "D21": (148, 5, 149, ""),
    "D22": (56, 57, 149, ""),
    "D23": (250, 219, 248, ""),
    "D24": (118, 138, 225, ""),
    "D25": (73, 80, 194, ""),
    "D26": (214, 198, 235, ""),
    "E1": (246, 212, 203, ""),
    "E2": (252, 193, 221, ""),
    "E3": (246, 189, 232, ""),
    "E4": (233, 99, 158, ""),
    "E5": (241, 85, 159, ""),
    "E6": (236, 64, 114, ""),
    "E7": (198, 54, 116, ""),
    "E8": (253, 219, 233, ""),
    "E9": (229, 117, 199, ""),
    "E10": (211, 57, 151, ""),
    "E11": (247, 218, 212, ""),
    "E12": (248, 147, 191, ""),
    "E13": (181, 2, 106, ""),
    "E14": (250, 212, 191, ""),
    "E15": (245, 201, 202, ""),
    "E16": (251, 244, 236, ""),
    "E17": (247, 227, 236, ""),
    "E18": (251, 203, 219, ""),
    "E19": (246, 187, 209, ""),
    "E20": (215, 198, 206, ""),
    "E21": (192, 157, 164, ""),
    "E22": (181, 139, 159, ""),
    "E23": (147, 125, 138, ""),
    "E24": (222, 190, 229, ""),
    "F1": (255, 146, 128, ""),
    "F2": (247, 61, 72, ""),
    "F3": (239, 77, 62, ""),
    "F4": (249, 43, 64, ""),
    "F5": (227, 3, 40, ""),
    "F6": (145, 54, 53, ""),
    "F7": (145, 25, 50, ""),
    "F8": (187, 1, 38, ""),
    "F9": (224, 103, 122, ""),
    "F10": (135, 70, 40, ""),
    "F11": (111, 50, 29, ""),
    "F12": (248, 81, 109, ""),
    "F13": (244, 92, 69, ""),
    "F14": (252, 173, 178, ""),
    "F15": (213, 5, 39, ""),
    "F16": (248, 192, 169, ""),
    "F17": (232, 155, 125, ""),
    "F18": (208, 126, 74, ""),
    "F19": (190, 69, 74, ""),
    "F20": (198, 148, 149, ""),
    "F21": (242, 187, 198, ""),
    "F22": (247, 195, 208, ""),
    "F23": (236, 128, 109, ""),
    "F24": (224, 157, 175, ""),
    "F25": (232, 72, 84, ""),
    "G1": (255, 228, 211, ""),
    "G2": (252, 198, 172, ""),
    "G3": (241, 196, 165, ""),
    "G4": (220, 179, 135, ""),
    "G5": (231, 179, 78, ""),
    "G6": (243, 160, 20, ""),
    "G7": (152, 80, 58, ""),
    "G8": (75, 43, 28, ""),
    "G9": (228, 182, 133, ""),
    "G10": (218, 140, 66, ""),
    "G11": (218, 200, 152, ""),
    "G12": (254, 201, 147, ""),
    "G13": (178, 113, 75, ""),
    "G14": (139, 104, 76, ""),
    "G15": (252, 249, 224, ""),
    "G16": (242, 216, 193, ""),
    "G17": (121, 84, 78, ""),
    "G18": (255, 228, 214, ""),
    "G19": (221, 125, 65, ""),
    "G20": (165, 69, 47, ""),
    "G21": (179, 133, 97, ""),
    "H1": (251, 251, 251, ""),
    "H2": (255, 255, 255, ""),
    "H3": (180, 180, 180, ""),
    "H4": (135, 135, 135, ""),
    "H5": (70, 70, 72, ""),
    "H6": (44, 44, 44, ""),
    "H7": (1, 1, 1, ""),
    "H8": (231, 214, 220, ""),
    "H9": (239, 237, 238, ""),
    "H10": (236, 234, 235, ""),
    "H11": (205, 205, 205, ""),
    "H12": (253, 246, 238, ""),
    "H13": (244, 239, 209, ""),
    "H14": (206, 215, 212, ""),
    "H15": (152, 166, 166, ""),
    "H16": (27, 18, 19, ""),
    "H17": (240, 238, 239, ""),
    "H18": (252, 255, 248, ""),
    "H19": (242, 238, 229, ""),
    "H20": (150, 160, 159, ""),
    "H21": (255, 251, 225, ""),
    "H22": (202, 202, 218, ""),
    "H23": (155, 156, 148, ""),
    "M1": (187, 198, 182, ""),
    "M2": (144, 153, 148, ""),
    "M3": (105, 126, 128, ""),
    "M4": (224, 212, 188, ""),
    "M5": (208, 203, 174, ""),
    "M6": (176, 170, 134, ""),
    "M7": (176, 167, 150, ""),
    "M8": (174, 128, 130, ""),
    "M9": (168, 135, 100, ""),
    "M10": (198, 178, 187, ""),
    "M11": (157, 118, 147, ""),
    "M12": (100, 75, 81, ""),
    "M13": (199, 146, 102, ""),
    "M14": (195, 116, 99, ""),
    "M15": (116, 125, 122, ""),
}

PALETTES = {
    "artkal-s": ARTKAL_S,
    "perler": PERLER,
    "hama": HAMA,
    "mard": MARD,
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


_PALETTE_TABLES = {}


def _palette_index(palette):
    """
    预处理调色板：展平成 [(r,g,b,key)]，并按 G 通道排序建索引。

    加权距离里 G 的系数恒为 4（最大），所以"G 相差很远"的颜色不可能更近：
    从查询色的 G 位置向两侧由近到远扫，一旦 4*Δg² >= 当前最优距离就停。
    每次只算十几个候选，结果与全量扫描完全一致（剪枝下界是严格的）。
    """
    entry = _PALETTE_TABLES.get(id(palette))
    if entry is None or entry[0] is not palette:
        table = [(c[0], c[1], c[2], k) for k, c in palette.items()]
        by_g = sorted(table, key=lambda e: e[1])
        entry = (palette, table, by_g, [e[1] for e in by_g])
        _PALETTE_TABLES[id(palette)] = entry
    return entry


def _palette_table(palette):
    """展平表 [(r,g,b,key)]，按调色板对象缓存"""
    return _palette_index(palette)[1]


def _nearest_indexed(r, g, b, index):
    """精确最近色搜索：按 G 距离由近到远扩展 + 严格下界剪枝"""
    by_g = index[2]
    gvals = index[3]
    n = len(by_g)
    lo = bisect.bisect_left(gvals, g)
    hi = lo
    best = 1e18
    best_key = None
    while lo > 0 or hi < n:
        if hi >= n:
            i = lo - 1
            lo -= 1
        elif lo == 0:
            i = hi
            hi += 1
        else:
            gl = g - gvals[lo - 1]
            gh = gvals[hi] - g
            if gl <= gh:
                i = lo - 1
                lo -= 1
            else:
                i = hi
                hi += 1
        pr, pg, pb, key = by_g[i]
        dg = g - pg
        d0 = 4.0 * dg * dg
        if d0 >= best:
            # 剩下的 G 距离只会更大，不可能更近
            break
        dr = r - pr
        db = b - pb
        rm = (r + pr) * 0.5
        d = d0 + (2.0 + rm / 256.0) * dr * dr + (2.0 + (255.0 - rm) / 256.0) * db * db
        if d < best:
            best = d
            best_key = key
    return best_key


def find_nearest_color(pixel, palette):
    """找到调色板中最接近的颜色（保留原接口）"""
    return _nearest_indexed(pixel[0], pixel[1], pixel[2], _palette_index(palette))


def hex_to_rgb(h):
    """#RRGGBB / #RGB → (r, g, b)，非法值抛 ValueError"""
    s = h.strip().lstrip("#")
    if len(s) == 3:
        s = "".join(ch * 2 for ch in s)
    if len(s) != 6:
        raise ValueError(f"非法颜色值 {h!r}：应为 #RRGGBB 或 #RGB")
    try:
        return tuple(int(s[i:i+2], 16) for i in (0, 2, 4))
    except ValueError:
        raise ValueError(f"非法颜色值 {h!r}：应为 #RRGGBB 或 #RGB") from None


def build_custom_palette(color_list):
    """从颜色列表构建自定义调色板"""
    palette = {}
    for i, c in enumerate(color_list):
        palette[f"C{i+1:02d}"] = hex_to_rgb(c)
    return palette


def color_name(palette, code):
    """取颜色名称（真实色卡数据为 4 元组，第 4 位是名称；自定义色板无名）"""
    color = palette.get(code)
    return color[3] if color is not None and len(color) > 3 else ""


# ─────────────────────────────────────────────
# 图片处理核心
# ─────────────────────────────────────────────

def load_and_resize(image_path, width, height, keep_aspect=False):
    """加载图片并调整到目标网格尺寸"""
    img = Image.open(image_path).convert("RGBA")

    if keep_aspect:
        # 宽度固定；height 为 None 时高度按比例自动算，否则等比装入 W×H 框内
        ratio = width / img.width if height is None else min(width / img.width, height / img.height)
        new_w = max(1, round(img.width * ratio))
        new_h = max(1, round(img.height * ratio))
    else:
        new_w, new_h = width, height

    # 使用 LANCZOS 高质量缩放
    img = img.resize((new_w, new_h), Image.LANCZOS)
    return img


def quantize_image(img, palette):
    """
    将图片像素映射到调色板，返回：
    - grid: 二维列表，每个元素是调色板 key（None 表示空位）
    - stats: Counter 统计每种颜色用量

    大图上逐像素做最近色搜索是最慢的一步，这里做了两处优化：
    1) 半透明混白交给 PIL 的 alpha_composite 一次算完（C 级），省掉逐像素浮点混合；
    2) 按 RGB 去重缓存匹配结果——缩放后的图存在大量重复色，只对唯一色搜一次。
    """
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    width, height = img.size

    bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
    flat = Image.alpha_composite(bg, img).convert("RGB")
    alpha = img.getchannel("A").tobytes()
    flat_pixels = flat.load()

    index = _palette_index(palette)
    memo = {}
    grid = []
    stats = Counter()

    for y in range(height):
        row = []
        base = y * width
        for x in range(width):
            # 低透明度视为背景（空位）
            if alpha[base + x] < 60:
                row.append(None)
                continue
            rgb = flat_pixels[x, y]
            key = memo.get(rgb)
            if key is None:
                key = _nearest_indexed(rgb[0], rgb[1], rgb[2], index)
                memo[rgb] = key
            stats[key] += 1
            row.append(key)
        grid.append(row)

    return grid, stats


# ─────────────────────────────────────────────
# 字体加载
# ─────────────────────────────────────────────

# 优先选自带中文字形的字体，否则图例里的中文会渲染成豆腐块
_FONT_CANDIDATES = [
    "C:/Windows/Fonts/msyhbd.ttc",    # 微软雅黑 Bold
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/Dengb.ttf",     # 等线 Bold
    "C:/Windows/Fonts/Deng.ttf",
    "C:/Windows/Fonts/simhei.ttf",    # 黑体
    "C:/Windows/Fonts/simsun.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/Helvetica.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
]


def load_font(size):
    """加载支持中文的字体；全都找不到时退回 PIL 内置字体"""
    for path in _FONT_CANDIDATES:
        if not os.path.exists(path):
            continue
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


# ─────────────────────────────────────────────
# 图纸渲染
# ─────────────────────────────────────────────

def _indexed_base(grid, colors, cell_size, empty_rgb=(255, 255, 255)):
    """
    一次性把网格铺成色块图：P 模式 + NEAREST 放大，全部在 C 层完成。
    比逐格 draw.rectangle 快一个数量级。色数超过 256 时退回逐格绘制。
    """
    height = len(grid)
    width = len(grid[0]) if grid else 0
    index_of = {}
    data = []
    pal_bytes = []
    too_many = False
    for row in grid:
        for key in row:
            idx = index_of.get(key)
            if idx is None:
                if len(index_of) >= 256:
                    too_many = True
                    break
                idx = len(index_of)
                index_of[key] = idx
                rgb = empty_rgb if key is None else colors[key]
                pal_bytes.extend(rgb)
            data.append(idx)
        if too_many:
            break

    if not too_many:
        base = Image.new("P", (width, height))
        base.putdata(data)
        base.putpalette(pal_bytes + [0] * (768 - len(pal_bytes)))
        return base.convert("RGB").resize(
            (width * cell_size, height * cell_size), Image.NEAREST
        )

    # 兜底：色数 > 256 时逐格画
    img = Image.new("RGB", (width * cell_size, height * cell_size), empty_rgb)
    draw = ImageDraw.Draw(img)
    for y, row in enumerate(grid):
        for x, key in enumerate(row):
            if key is None:
                continue
            x0, y0 = x * cell_size, y * cell_size
            draw.rectangle(
                [x0, y0, x0 + cell_size - 1, y0 + cell_size - 1], fill=colors[key]
            )
    return img


def _draw_grid_lines(draw, width, height, cell_size, color):
    """整张图的网格线一次画完（横竖各 width+1 / height+1 条）"""
    w_px = max(1, width * cell_size - 1)
    h_px = max(1, height * cell_size - 1)
    for k in range(width + 1):
        x = min(k * cell_size, w_px)
        draw.line([(x, 0), (x, h_px)], fill=color)
    for k in range(height + 1):
        y = min(k * cell_size, h_px)
        draw.line([(0, y), (w_px, y)], fill=color)


def add_grid_rulers(img, width, height, cell_size, step=5):
    """
    在图像四周补上行列计数标尺：上下为列号，左右为行号。
    每 step 格标一个数字（总是包含两端），每个格子边界画短刻度。
    """
    if width <= 0 or height <= 0 or cell_size <= 0:
        return img
    step = max(1, step)
    margin = max(20, min(36, cell_size + 8))
    font = load_font(max(9, min(16, margin - 10)))

    w_px, h_px = img.size
    bg = (255, 255, 255) if img.mode == "RGB" else (255, 255, 255, 255)
    canvas = Image.new(img.mode, (w_px + margin * 2, h_px + margin * 2), bg)
    canvas.paste(img, (margin, margin))
    draw = ImageDraw.Draw(canvas)

    tick_color = (120, 120, 120)
    text_color = (50, 50, 50)
    pad = (margin - 6) / 2  # 刻度外剩余空间的中心

    def center_text(cx, cy, text):
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text((cx - tw / 2 - bbox[0], cy - th / 2 - bbox[1]), text, fill=text_color, font=font)

    # 外框
    draw.rectangle([margin, margin, margin + w_px - 1, margin + h_px - 1], outline=tick_color)

    # 列号：上下两边
    for i in range(width):
        x = margin + i * cell_size
        n = i + 1
        labeled = n % step == 0 or n == 1 or n == width
        length = 6 if labeled else 3
        draw.line([(x, margin - length), (x, margin)], fill=tick_color)
        draw.line([(x, margin + h_px), (x, margin + h_px + length)], fill=tick_color)
        if labeled:
            cx = x + cell_size / 2
            center_text(cx, margin - length - pad, str(n))
            center_text(cx, margin + h_px + length + pad, str(n))

    # 行号：左右两边
    for j in range(height):
        y = margin + j * cell_size
        n = j + 1
        labeled = n % step == 0 or n == 1 or n == height
        length = 6 if labeled else 3
        draw.line([(margin - length, y), (margin, y)], fill=tick_color)
        draw.line([(margin + w_px, y), (margin + w_px + length, y)], fill=tick_color)
        if labeled:
            cy = y + cell_size / 2
            center_text(margin - length - pad, cy, str(n))
            center_text(margin + w_px + length + pad, cy, str(n))

    return canvas


def render_color_preview(grid, palette, cell_size=10):
    """渲染彩色预览图（每个格子填色）"""
    height = len(grid)
    width = len(grid[0]) if grid else 0
    colors = {k: c[:3] for k, c in palette.items()}
    img = _indexed_base(grid, colors, cell_size, empty_rgb=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    _draw_grid_lines(draw, width, height, cell_size, (200, 200, 200))
    return img


def render_numbered_pattern(grid, palette, cell_size=24):
    """渲染带编号的图纸（每格显示颜色编号）"""
    height = len(grid)
    width = len(grid[0]) if grid else 0
    colors = {k: c[:3] for k, c in palette.items()}
    img = _indexed_base(grid, colors, cell_size, empty_rgb=(245, 245, 245)).convert("RGBA")

    font_size = max(8, cell_size // 3)
    font_cache = {}
    scratch = ImageDraw.Draw(Image.new("RGBA", (1, 1)))

    def fit_font(text):
        """长编码（如 Perler 的 80-15179）逐级缩小字号，塞进格子"""
        size = font_size
        while True:
            f = font_cache.get(size)
            if f is None:
                f = load_font(size)
                font_cache[size] = f
            if size <= 6 or scratch.textlength(text, font=f) <= cell_size - 4:
                return f
            size -= 1

    # 每种色号只渲染一次文字小图，之后逐格粘贴；比每格 draw.text 快数倍
    tiles = {}

    def label_tile(key):
        tile = tiles.get(key)
        if tile is not None:
            return tile
        r, g, b = palette[key][:3]
        luminance = 0.299 * r + 0.587 * g + 0.114 * b
        text_color = (0, 0, 0, 255) if luminance > 128 else (255, 255, 255, 255)
        tile = Image.new("RGBA", (cell_size, cell_size), (0, 0, 0, 0))
        tdraw = ImageDraw.Draw(tile)
        glyph_font = fit_font(key)
        bbox = tdraw.textbbox((0, 0), key, font=glyph_font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        tdraw.text(
            ((cell_size - tw) / 2 - bbox[0], (cell_size - th) / 2 - bbox[1]),
            key,
            fill=text_color,
            font=glyph_font,
        )
        tiles[key] = tile
        return tile

    for y, row in enumerate(grid):
        y0 = y * cell_size
        for x, key in enumerate(row):
            if key is None:
                continue
            tile = label_tile(key)
            img.paste(tile, (x * cell_size, y0), tile)

    draw = ImageDraw.Draw(img)
    _draw_grid_lines(draw, width, height, cell_size, (180, 180, 180))
    # 最终图没有透明区域，转 RGB 让 PNG 编码更快、文件更小
    return img.convert("RGB")


def render_legend(palette, stats, cell_size=30):
    """渲染颜色图例（含用量统计），列宽按实际文本宽度自适应"""
    if not stats:
        return Image.new("RGBA", (200, 50), (255, 255, 255, 255))

    # 按用量降序排列
    sorted_colors = stats.most_common()
    total_beads = sum(stats.values())
    row_height = max(28, cell_size)
    margin = 10

    title_font = load_font(16)
    body_font = load_font(13)
    scratch = ImageDraw.Draw(Image.new("RGBA", (1, 1)))

    # 先量好各列宽度，避免固定 label_w 造成的大片空白
    labels = []
    for code, _ in sorted_colors:
        name = color_name(palette, code)
        labels.append(f"{code}  {name}" if name else code)
    code_w = max(scratch.textlength(t, font=body_font) for t in labels)
    count_texts = [
        f"{count:>5d} 颗 ({count / total_beads * 100:4.1f}%)" if total_beads else "0 颗 (0.0%)"
        for _, count in sorted_colors
    ]
    count_w = max(scratch.textlength(t, font=body_font) for t in count_texts)
    title = f"颜色图例  |  共 {total_beads} 颗"
    title_w = scratch.textlength(title, font=title_font)

    label_x = margin + cell_size + 12
    count_x = label_x + int(code_w) + 24
    total_w = int(max(count_x + count_w + margin, margin + title_w + margin))
    total_h = (row_height + 6) * len(sorted_colors) + row_height + margin * 2 + 20

    img = Image.new("RGBA", (total_w, total_h), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)

    # 标题
    draw.text((margin, margin), title, fill=(30, 30, 30), font=title_font)

    y_offset = margin + row_height + 5
    for (code, count), count_text, label in zip(sorted_colors, count_texts, labels):
        color = palette[code]
        # 色块
        draw.rectangle(
            [margin, y_offset, margin + cell_size, y_offset + cell_size],
            fill=color[:3],
            outline=(100, 100, 100),
        )
        # 色号 + 名称
        draw.text(
            (label_x, y_offset + (cell_size - 14) // 2),
            label,
            fill=(30, 30, 30),
            font=body_font,
        )
        # 用量
        draw.text(
            (count_x, y_offset + (cell_size - 14) // 2),
            count_text,
            fill=(80, 80, 80),
            font=body_font,
        )
        y_offset += row_height + 6

    return img


def render_pegboard_overlay(grid, palette, cell_size=10, board_size=29):
    """渲染带钉板分割线的预览：画布与预览等大，只画板与板之间的缝"""
    height = len(grid)
    width = len(grid[0]) if grid else 0

    preview = render_color_preview(grid, palette, cell_size).convert("RGBA")
    w_px, h_px = preview.size

    overlay = Image.new("RGBA", (w_px, h_px), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    line_color = (220, 30, 30, 170)

    # 只画内部板缝（从 board_size 开始），避免第 0 行/列贴边被裁掉一半
    for bx in range(board_size, width, board_size):
        x = bx * cell_size
        draw.line([(x, 0), (x, h_px)], fill=line_color, width=2)
    for by in range(board_size, height, board_size):
        y = by * cell_size
        draw.line([(0, y), (w_px, y)], fill=line_color, width=2)

    # 外框
    draw.rectangle([0, 0, w_px - 1, h_px - 1], outline=(150, 150, 150), width=1)

    return Image.alpha_composite(preview, overlay)


# ─────────────────────────────────────────────
# CLI 主函数
# ─────────────────────────────────────────────

def _save_image(img, path):
    """保存 PNG；目标文件正被其它程序占用（Windows 上映射中的文件无法截断，报 Errno 22）时自动改名。"""
    tmp = f"{path}.part"
    img.save(tmp, format="PNG")
    try:
        os.replace(tmp, path)
        return path
    except OSError:
        pass
    base, ext = os.path.splitext(path)
    for i in range(1, 100):
        alt = f"{base}~{i}{ext}"
        try:
            os.replace(tmp, alt)
        except OSError:
            continue
        print(f"⚠️  {path} 正被其它程序占用，已改存为 {alt}", file=sys.stderr)
        return alt
    try:
        os.remove(tmp)
    except OSError:
        pass
    raise OSError(f"无法写入 {path}：文件正被其它程序占用")


def main():
    parser = argparse.ArgumentParser(
        description="🎨 perler-pattern — 图片转拼豆图纸生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
示例:
  %(prog)s photo.jpg                        # 默认 29×29，Artkal S 色板
  %(prog)s photo.jpg -w 58 -h 58            # 2×2 板（58×58）
  %(prog)s photo.jpg -w 116 --aspect        # 保持宽高比，宽度 116
  %(prog)s photo.jpg --palette perler       # 使用 Perler 色板
  %(prog)s photo.jpg --palette mard         # 使用 MARD 221 色板
  %(prog)s photo.jpg -w 58 --max-colors 20  # 限制用色数量（买豆更省事）
  %(prog)s photo.jpg --palette custom --colors "#FF0000,#00FF00,#0000FF,#FFFFFF,#000000"
  %(prog)s photo.jpg --cell 16 --no-legend  # 增大格子，不生成图例
  %(prog)s photo.jpg --format json          # 输出 JSON 数据

支持的色板:
  artkal-s    Artkal S 系列 (默认，{len(ARTKAL_S)} 色)
  perler      Perler 品牌 ({len(PERLER)} 色)
  hama        Hama 品牌 ({len(HAMA)} 色)
  mard        MARD 221 色（国内主流）({len(MARD)} 色)
  custom      自定义（需配合 --colors）
        """,
    )

    parser.add_argument("image", help="输入图片路径")
    parser.add_argument("-w", "--width", type=int, default=29, help="网格宽度（默认 29，标准钉板）")
    parser.add_argument("-H", "--height", type=int, default=None, help="网格高度（默认同宽度；配合 --aspect 省略则按比例自动）")
    parser.add_argument("--aspect", action="store_true", help="保持原始宽高比（宽度固定；省略 -H 时高度自动计算，指定 -H 时等比装入框内）")
    parser.add_argument("-p", "--palette", default="artkal-s", choices=list(PALETTES.keys()) + ["custom"],
                        help="色板选择（默认 artkal-s）")
    parser.add_argument("--colors", type=str, default=None,
                        help="自定义颜色列表，逗号分隔的 #RRGGBB 值（配合 --palette custom）")
    parser.add_argument("-c", "--cell", type=int, default=10, help="预览图格子像素大小（默认 10）")
    parser.add_argument("--max-colors", type=int, default=0,
                        help="先把图片压到 N 色以内再匹配色板（推荐 12–30，0=不限制）")
    parser.add_argument("-o", "--output", type=str, default=None, help="输出文件名前缀（默认同输入文件名）")
    parser.add_argument("--no-preview", action="store_true", help="不生成彩色预览图")
    parser.add_argument("--no-pattern", action="store_true", help="不生成编号图纸")
    parser.add_argument("--no-legend", action="store_true", help="不生成颜色图例")
    parser.add_argument("--board-overlay", action="store_true", help="生成钉板分割线预览")
    parser.add_argument("--no-rulers", action="store_true", help="不添加行列计数标尺")
    parser.add_argument("--ruler-step", type=int, default=5, help="标尺数字间隔（默认 5 格，1=逐格标注）")
    parser.add_argument("--format", choices=["png", "json", "both"], default="png", help="输出格式（默认 png）")
    parser.add_argument("-q", "--quiet", action="store_true", help="静默模式")

    args = parser.parse_args()

    # 参数验证
    if not os.path.isfile(args.image):
        print(f"错误：文件不存在 — {args.image}", file=sys.stderr)
        sys.exit(1)

    if args.height is None and not args.aspect:
        args.height = args.width

    # 加载调色板
    if args.palette == "custom":
        if not args.colors:
            print("错误：使用 custom 色板时需要指定 --colors", file=sys.stderr)
            sys.exit(1)
        color_list = [c.strip() for c in args.colors.split(",") if c.strip()]
        try:
            palette = build_custom_palette(color_list)
        except ValueError as e:
            print(f"错误：{e}", file=sys.stderr)
            sys.exit(1)
    else:
        palette = PALETTES[args.palette]

    # 输出文件名前缀
    if args.output:
        prefix = args.output
    else:
        prefix = Path(args.image).stem

    if not args.quiet:
        if args.height is None:
            print(f"📐 网格宽度: {args.width}（高度按原图比例自动）")
        else:
            print(f"📐 网格尺寸: {args.width}×{args.height}")
        print(f"🎨 色板: {args.palette} ({len(palette)} 色)")

    # 1. 加载并缩放图片
    img = load_and_resize(args.image, args.width, args.height, keep_aspect=args.aspect)
    actual_w, actual_h = img.size

    if not args.quiet and args.aspect:
        print(f"📐 实际尺寸（保持比例）: {actual_w}×{actual_h}")

    # 1.5 可选：先把颜色压到 N 色以内，避免大色板下颜色碎片化
    if args.max_colors > 0:
        alpha = img.getchannel("A") if img.mode == "RGBA" else None
        img = img.convert("RGB").quantize(
            colors=args.max_colors, method=Image.Quantize.MEDIANCUT
        ).convert("RGB")
        if alpha is not None:
            img = img.convert("RGBA")
            img.putalpha(alpha)
        if not args.quiet:
            print(f"🎛️  颜色量化: 先压缩到 {args.max_colors} 色以内")

    # 2. 量化颜色
    grid, stats = quantize_image(img, palette)

    if not args.quiet:
        total_beads = sum(stats.values())
        print(f"📦 总珠数: {total_beads}（空位 {actual_w * actual_h - total_beads}）")
        print(f"🎯 使用了 {len(stats)} 种颜色")
        print()

    # 3. 生成输出
    outputs = []

    def with_rulers(image, cell):
        if args.no_rulers:
            return image
        return add_grid_rulers(image, actual_w, actual_h, cell, step=args.ruler_step)

    # 彩色预览
    if not args.no_preview:
        preview = with_rulers(render_color_preview(grid, palette, cell_size=args.cell), args.cell)
        preview_path = _save_image(preview, f"{prefix}_preview.png")
        outputs.append(preview_path)
        if not args.quiet:
            print(f"✅ 彩色预览: {preview_path}")

    # 编号图纸
    if not args.no_pattern:
        longest = max((len(k) for row in grid for k in row if k), default=2)
        pattern_cell = max(args.cell + 12, 24, min(48, longest * 6))
        pattern = with_rulers(render_numbered_pattern(grid, palette, cell_size=pattern_cell), pattern_cell)
        pattern_path = _save_image(pattern, f"{prefix}_pattern.png")
        outputs.append(pattern_path)
        if not args.quiet:
            print(f"✅ 编号图纸: {pattern_path}")

    # 颜色图例
    if not args.no_legend:
        legend = render_legend(palette, stats)
        legend_path = _save_image(legend, f"{prefix}_legend.png")
        outputs.append(legend_path)
        if not args.quiet:
            print(f"✅ 颜色图例: {legend_path}")

    # 钉板分割线预览
    if args.board_overlay:
        overlay = with_rulers(
            render_pegboard_overlay(grid, palette, cell_size=args.cell, board_size=29), args.cell
        )
        overlay_path = _save_image(overlay, f"{prefix}_board.png")
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
                "total_beads": sum(stats.values()),
                "unique_colors": len(stats),
            },
            "colors": {code: {"rgb": list(palette[code][:3]),
                              "name": color_name(palette, code), "count": count}
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
