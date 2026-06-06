"""
Chapter 1.1 — Patch Embedding
================================
A Vision Transformer divides an image into fixed-size patches,
then linearly projects each patch into a vector (the "token").

Example (ViT-Base):
  Image: 224×224×3
  Patch size: 16×16
  Number of patches: (224/16)² = 196
  Each patch: 16×16×3 = 768 raw values → projected to 768-dim embedding
"""

import torch
import torch.nn as nn


class PatchEmbedding(nn.Module):
    """
    Splits an image into non-overlapping patches and projects each to embed_dim.

    A single Conv2d with kernel_size=patch_size and stride=patch_size achieves
    both patch extraction and linear projection in one step.
    """

    def __init__(self, img_size: int = 224, patch_size: int = 16,
                 in_channels: int = 3, embed_dim: int = 768):
        super().__init__()
        assert img_size % patch_size == 0, \
            f"Image size {img_size} must be divisible by patch size {patch_size}"

        self.img_size = img_size
        self.patch_size = patch_size
        self.n_patches = (img_size // patch_size) ** 2

        # One Conv2d replaces: unfold + reshape + linear
        self.proj = nn.Conv2d(
            in_channels, embed_dim,
            kernel_size=patch_size, stride=patch_size
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (batch_size, in_channels, img_size, img_size)
        Returns:
            patches: (batch_size, n_patches, embed_dim)
        """
        # (B, C, H, W) → (B, embed_dim, H/P, W/P)
        x = self.proj(x)
        # (B, embed_dim, h, w) → (B, embed_dim, n_patches)
        x = x.flatten(2)
        # (B, embed_dim, n_patches) → (B, n_patches, embed_dim)
        x = x.transpose(1, 2)
        return x


class PositionalEmbedding(nn.Module):
    """
    Learnable 1-D positional embeddings added to patch tokens.

    ViT uses learned positional embeddings (not sinusoidal like the original
    Transformer), which works well for the fixed grid of image patches.

    The +1 accounts for the [CLS] token prepended before the patches.
    """

    def __init__(self, n_patches: int, embed_dim: int):
        super().__init__()
        # n_patches + 1 for [CLS] token
        self.pos_embed = nn.Parameter(
            torch.zeros(1, n_patches + 1, embed_dim)
        )
        # initialise with small random values (like original ViT paper)
        nn.init.trunc_normal_(self.pos_embed, std=0.02)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (batch_size, n_patches + 1, embed_dim)   (already has CLS token)
        Returns:
            x + positional embedding, same shape
        """
        return x + self.pos_embed
