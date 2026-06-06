"""
Patch extraction and positional embedding for Vision Transformer.

Key insight: Conv2d with kernel_size=stride=patch_size is mathematically
identical to extracting patches in a loop and applying a linear projection —
but fully vectorized and GPU-friendly.
"""

import torch
import torch.nn as nn


class PatchEmbedding(nn.Module):
    """
    Split image into non-overlapping patches and project each to embed_dim.

    Args:
        img_size    : input image size (assumed square)
        patch_size  : patch size (assumed square)
        in_channels : number of image channels
        embed_dim   : output embedding dimension per patch
    """

    def __init__(self, img_size=224, patch_size=16, in_channels=3, embed_dim=768):
        super().__init__()
        assert img_size % patch_size == 0, "img_size must be divisible by patch_size"
        self.n_patches = (img_size // patch_size) ** 2
        self.proj = nn.Conv2d(
            in_channels, embed_dim, kernel_size=patch_size, stride=patch_size
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, C, H, W)  →  (B, N_patches, embed_dim)
        return self.proj(x).flatten(2).transpose(1, 2)


class PositionalEmbedding(nn.Module):
    """
    Learnable positional embedding added to patch tokens + CLS token.

    Shape: (1, n_patches + 1, embed_dim) — broadcast over batch.
    Initialized with small values (trunc_normal, std=0.02).
    """

    def __init__(self, n_patches: int, embed_dim: int):
        super().__init__()
        self.pos_embed = nn.Parameter(torch.zeros(1, n_patches + 1, embed_dim))
        nn.init.trunc_normal_(self.pos_embed, std=0.02)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.pos_embed
