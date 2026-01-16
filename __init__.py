# -*- coding: utf-8 -*-
"""
ComfyUI 自定义节点：自适应TTP分块（零参数，最少分块 + 尽量均分）
- 输入：
  - image: IMAGE（必需）
  - target_tile_pixels_wan: FLOAT（可选，单位：万像素，0或空表示自动模式）
- 输出：width_factor（int）, height_factor（int）, overlap_rate（float 0~1）
- 模式说明：
  * 自动模式（target_tile_pixels_wan = 0）：最少分块优先，满足单块短/长边上限（2048/2304像素）
  * 指定模式（target_tile_pixels_wan > 0）：按最接近期望单块像素数计算，不应用边长硬性约束
- 通用规则（两种模式都适用）：
  1) 禁止 1×1（沿长边拆 2×1 或 1×2）；
  2) 近似正方图（长宽比在 0.85–1.18）且得到 2×1/1×2 时，强制改为 2×2，保证"均分"；
  3) 均匀性兜底：若最后一列/行明显过窄（<80%），仅在必要时对应方向 +1；
  4) 重叠率随单块短边与块数自适应（质量取向）。
"""

import math
import torch

class AdaptiveTTPTilePlannerMinimal:
    CATEGORY = "图像/分块·TTP"
    FUNCTION = "plan"
    RETURN_TYPES = ("INT", "INT", "FLOAT")
    RETURN_NAMES = ("width_factor", "height_factor", "overlap_rate")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
            },
            "optional": {
                "target_tile_pixels_wan": ("FLOAT", {
                    "default": 0.0,
                    "min": 0.0,
                    "max": 1000.0,
                    "step": 1.0,
                    "display": "number"
                }),
            }
        }

    # 固定内部常量
    _S_HARD_MAX = 2048    # 单块短边硬上限
    _L_HARD_MAX = 2304    # 单块长边硬上限
    _TOL        = 128     # 容忍像素（利于更少块）
    _FORBID_1x1 = True    # 禁止 1×1
    _UNIFORMITY_MIN_RATIO = 0.80  # 最后一列/行与常规宽/高比的阈值
    _NEAR_SQUARE_LOW  = 0.85      # 近似正方的下限长宽比
    _NEAR_SQUARE_HIGH = 1.18      # 近似正方的上限长宽比

    # 工具
    def _get_wh(self, image: torch.Tensor):
        if image is None or not isinstance(image, torch.Tensor):
            raise ValueError("image 不能为空")
        if image.ndim < 3:
            raise ValueError("image 维度异常，期望至少为 [*, H, W, *]")
        H = int(image.shape[-3])
        W = int(image.shape[-2])
        return W, H

    @staticmethod
    def _clamp(v, lo, hi): return max(lo, min(hi, v))

    def _uniformity_ratio_1d(self, total, n):
        if n <= 1:
            return 1.0, total, total
        t = math.ceil(total / n)        # 常规列宽/行高
        last = total - t * (n - 1)      # 最后一列/行
        last = max(1, last)
        ratio = float(last) / float(t)  # 越接近 1 越均匀
        return ratio, t, last

    def _overlap_rate(self, s, N, uniform_ratio):
        # 质量向：块越大/越少，重叠率偏高
        if s >= 1800 or N <= 4:
            p0 = 0.05
        elif s >= 1400:
            p0 = 0.045
        else:
            p0 = 0.04
        if uniform_ratio < 0.9:
            p0 += 0.005  # 均匀性差一点时，略增重叠帮助融合
        return self._clamp(p0, 0.03, 0.06)

    def plan(self, image, target_tile_pixels_wan=0.0):
        W, H = self._get_wh(image)
        aspect = (W / H) if H > 0 else 1.0
        total_pixels = W * H

        # 如果用户指定了期望单块像素数（单位：万），则基于此计算（不应用边长硬性约束）
        if target_tile_pixels_wan and target_tile_pixels_wan > 0:
            target_tile_pixels = target_tile_pixels_wan * 10000  # 转换为实际像素数
            # 计算期望总块数
            target_total_tiles = total_pixels / target_tile_pixels
            
            # 根据长宽比分配 n_x 和 n_y，使分块接近正方形
            # n_x * n_y ≈ target_total_tiles
            # n_x / n_y ≈ W / H
            # 解得：n_x ≈ sqrt(target_total_tiles * W / H), n_y ≈ sqrt(target_total_tiles * H / W)
            if aspect >= 1.0:  # 横向或正方形
                n_x = max(1, round(math.sqrt(target_total_tiles * aspect)))
                n_y = max(1, round(target_total_tiles / n_x))
            else:  # 纵向
                n_y = max(1, round(math.sqrt(target_total_tiles / aspect)))
                n_x = max(1, round(target_total_tiles / n_y))
            
            # 确保至少是1×1（后续会处理禁止1×1的情况）
            n_x = max(1, n_x)
            n_y = max(1, n_y)
            
            # 计算当前分块的尺寸
            tile_w = math.ceil(W / n_x)
            tile_h = math.ceil(H / n_y)
            
            # 用户指定模式下，不应用边长硬性约束，直接进入后续规则处理
        else:
            # 自动模式：最少分块（以短边上限+容忍为分母）
            denom = self._S_HARD_MAX + self._TOL
            n_x = max(1, math.ceil(W / max(1, denom)))
            n_y = max(1, math.ceil(H / max(1, denom)))
            tile_w = math.ceil(W / n_x)
            tile_h = math.ceil(H / n_y)

            # 自动模式：长边约束
            long_cap = self._L_HARD_MAX + self._TOL
            while tile_w > long_cap:
                n_x += 1
                tile_w = math.ceil(W / n_x)
            while tile_h > long_cap:
                n_y += 1
                tile_h = math.ceil(H / n_y)

        # 3) 禁止 1×1：沿长边拆
        if self._FORBID_1x1 and n_x == 1 and n_y == 1:
            if W >= H:
                n_x = 2
            else:
                n_y = 2
            tile_w = math.ceil(W / n_x)
            tile_h = math.ceil(H / n_y)

        # 3.5) 近似正方时的“均分覆盖”：2×1/1×2 -> 2×2
        if (n_x == 2 and n_y == 1) or (n_x == 1 and n_y == 2):
            if self._NEAR_SQUARE_LOW <= aspect <= self._NEAR_SQUARE_HIGH:
                n_x, n_y = 2, 2
                tile_w = math.ceil(W / n_x)
                tile_h = math.ceil(H / n_y)

        # 4) 均分兜底：避免最后一列/行过窄
        ratio_w, _, _ = self._uniformity_ratio_1d(W, n_x)
        if ratio_w < self._UNIFORMITY_MIN_RATIO:
            n_x += 1
            tile_w = math.ceil(W / n_x)
            ratio_w, _, _ = self._uniformity_ratio_1d(W, n_x)

        ratio_h, _, _ = self._uniformity_ratio_1d(H, n_y)
        if ratio_h < self._UNIFORMITY_MIN_RATIO:
            n_y += 1
            tile_h = math.ceil(H / n_y)
            ratio_h, _, _ = self._uniformity_ratio_1d(H, n_y)

        # 5) 重叠率（质量取向 + 均匀性微调）
        s = min(tile_w, tile_h)
        N = n_x * n_y
        uniform_ratio = min(ratio_w, ratio_h)
        overlap_rate = self._overlap_rate(s, N, uniform_ratio)

        return int(n_x), int(n_y), float(overlap_rate)


# 正确注册
NODE_CLASS_MAPPINGS = {
    "AdaptiveTTPTilePlannerMinimal": AdaptiveTTPTilePlannerMinimal,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "AdaptiveTTPTilePlannerMinimal": "自适应TTP分块",
}
