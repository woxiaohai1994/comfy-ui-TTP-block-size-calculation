# 🖼️ ComfyUI Adaptive TTP Tile Planner
## 自适应TTP分块 (零参数智能图像分块)

> 🚀 **一键智能分块** - 自动计算最优的图像分块方案，适合大图AI处理

### ✨ 核心功能
- 🎯 **零参数优化**：自动模式下智能计算最少分块数
- 📐 **均分优先**：确保分块均匀，避免最后一列/行过窄
- 🔄 **自适应重叠**：根据块大小自动调整重叠率保证质量
- ⚙️ **双模式支持**：自动模式 + 自定义像素模式
- 🚫 **智能约束**：禁止1×1分块，强制近似正方形比例

### 🎨 解决什么问题？
处理超大图像时，AI模型（如Stable Diffusion）需要将图像分成小块处理。这个节点**自动计算最佳分块方案**，让你无需手动调整参数。

| 输入 | 输出 | 效果 |
|------|------|------|
| 🖼️ 大图 (4096×4096) | 📊 4×4网格 + 5%重叠 | ✅ 最少分块，质量保证 |
| 🎯 指定像素大小 | 📐 精确控制单块大小 | ✅ 自定义优化 |

### 📋 功能特点

| English | 中文 |
|---------|------|
| 🔄 **Zero-parameter optimization**<br/>Automatic mode prioritizes minimal tiling | 🔄 **零参数优化**<br/>自动模式优先最少分块 |
| 🎛️ **Flexible input modes**<br/>Auto or custom pixel count | 🎛️ **灵活输入模式**<br/>自动或自定义像素数 |
| 🧠 **Smart constraints**<br/>Prevents 1×1, ensures uniformity | 🧠 **智能约束**<br/>禁止1×1，保证均匀性 |
| 📏 **Adaptive overlap**<br/>Quality-based overlap calculation | 📏 **自适应重叠**<br/>质量导向重叠率计算 |
| 📏 **Hard limits**<br/>2048px short / 2304px long edge | 📏 **硬性限制**<br/>2048短边/2304长边约束 |

## 🔌 接口说明

### 📥 输入参数
| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| 🖼️ **image** | IMAGE | ✅ 必需 | 输入图像张量 |
| 🎯 **target_tile_pixels_wan** | FLOAT | ❌ 可选 | 单块目标像素数(万)，0=自动模式 |

### 📤 输出参数
| 输出 | 类型 | 说明 |
|------|------|------|
| 📐 **width_factor** | INT | 宽度方向分块数 |
| 📏 **height_factor** | INT | 高度方向分块数 |
| 🔗 **overlap_rate** | FLOAT | 自适应重叠率(0-1) |

## 🎮 使用模式

### 🤖 自动模式 (推荐)
> 当 `target_tile_pixels_wan = 0` 时

- 🎯 **最少分块优先**：智能计算最小分块数
- 📏 **尺寸约束**：单块不超过2048×2304像素
- ⚡ **容忍优化**：128像素容忍度，更少分块

### 🎨 自定义模式
> 当 `target_tile_pixels_wan > 0` 时

- 🎯 **精确控制**：按指定像素数分块
- 🔓 **无硬约束**：不受尺寸限制
- 📏 **自定义优化**：按目标大小优化

## 🧠 智能规则

| 规则 | 图标 | 说明 |
|------|------|------|
| **1. 禁止1×1** | 🚫 | 强制沿长边拆分为2×1或1×2 |
| **2. 近似正方** | ⬜ | 长宽比0.85-1.18时，2×1/1×2→2×2 |
| **3. 均匀性兜底** | ⚖️ | 最后一列/行<80%时，增加分块数 |
| **4. 质量导向重叠** | 🔗 | 大块/少块时重叠率更高 |

## 🚀 快速开始

### 📦 安装步骤
1. **下载节点** 📥
   ```bash
   # 将此文件夹复制到 ComfyUI 的 custom_nodes 目录
   cp -r zishiy-TTP /path/to/ComfyUI/custom_nodes/
   ```

2. **重启ComfyUI** 🔄
   - 关闭并重新启动 ComfyUI
   - 或在界面中点击 "Refresh" 按钮

3. **使用节点** 🎯
   - 在节点菜单中找到 **"图像/分块·TTP"** 分类
   - 拖入 **"自适应TTP分块"** 节点

### 💡 使用示例
```
输入: 4096×4096 大图
设置: target_tile_pixels_wan = 0 (自动模式)
输出: width_factor=3, height_factor=3, overlap_rate=0.045
结果: 9块均匀分布，质量最优
```

### 🔧 目录结构
```
zishiy TTP/
├── __init__.py          # 节点实现
├── README.md           # 项目说明
└── __pycache__/        # Python缓存
```

## 📄 许可证

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

<div align="center">

**Made with ❤️ for ComfyUI Community**

⭐ 如果这个节点对你有帮助，请给项目点个星！

</div>
