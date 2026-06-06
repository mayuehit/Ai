"""
Chapter 1.3 — Vision Transformer (ViT)
========================================
Reference: "An Image is Worth 16x16 Words" (Dosovitskiy et al., 2020)

Full pipeline:
  1. Split image into patches → PatchEmbedding → (B, N, D)
  2. Prepend [CLS] token        → (B, N+1, D)
  3. Add positional embeddings
  4. Pass through L Transformer encoder blocks
  5. Take [CLS] token output as image representation

Configurations shipped:
  ViT-Tiny  : embed_dim=192,  depth=12, heads=3
  ViT-Small : embed_dim=384,  depth=12, heads=6
  ViT-Base  : embed_dim=768,  depth=12, heads=12
  ViT-Large : embed_dim=1024, depth=24, heads=16
"""

from dataclasses import dataclass
import torch
import torch.nn as nn

from .patch_embedding import PatchEmbedding, PositionalEmbedding
from .attention import MultiHeadSelfAttention


@dataclass
class ViTConfig:
    img_size: int = 224
    patch_size: int = 16
    in_channels: int = 3
    embed_dim: int = 768
    depth: int = 12          # number of Transformer blocks
    num_heads: int = 12
    mlp_ratio: float = 4.0   # hidden dim of FFN = embed_dim * mlp_ratio
    dropout: float = 0.0
    emb_dropout: float = 0.0

    @property
    def n_patches(self) -> int:
        return (self.img_size // self.patch_size) ** 2

    @classmethod
    def vit_tiny(cls) -> "ViTConfig":
        return cls(embed_dim=192, depth=12, num_heads=3)

    @classmethod
    def vit_small(cls) -> "ViTConfig":
        return cls(embed_dim=384, depth=12, num_heads=6)

    @classmethod
    def vit_base(cls) -> "ViTConfig":
        return cls(embed_dim=768, depth=12, num_heads=12)

    @classmethod
    def vit_large(cls) -> "ViTConfig":
        return cls(embed_dim=1024, depth=24, num_heads=16)


class MLP(nn.Module):
    """Feed-forward network used inside each Transformer block (the 'FFN')."""

    def __init__(self, embed_dim: int, mlp_ratio: float = 4.0, dropout: float = 0.0):
        super().__init__()
        hidden_dim = int(embed_dim * mlp_ratio)
        self.net = nn.Sequential(
            nn.Linear(embed_dim, hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, embed_dim),
            nn.Dropout(dropout),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class ViTBlock(nn.Module):
    """
    One Transformer encoder block:
        x = x + Attention(LayerNorm(x))
        x = x + MLP(LayerNorm(x))

    Note: ViT uses Pre-LayerNorm (before attention/FFN), unlike the original
    Transformer paper which used Post-LayerNorm.
    """

    def __init__(self, cfg: ViTConfig):
        super().__init__()
        self.norm1 = nn.LayerNorm(cfg.embed_dim)
        self.attn = MultiHeadSelfAttention(cfg.embed_dim, cfg.num_heads, cfg.dropout)
        self.norm2 = nn.LayerNorm(cfg.embed_dim)
        self.mlp = MLP(cfg.embed_dim, cfg.mlp_ratio, cfg.dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Residual connection around attention
        x = x + self.attn(self.norm1(x))
        # Residual connection around FFN
        x = x + self.mlp(self.norm2(x))
        return x


class VisionTransformer(nn.Module):
    """
    Full Vision Transformer (ViT) encoder.

    Returns the [CLS] token embedding, which serves as a global image
    representation — this is what we hand off to the language model.
    """

    def __init__(self, cfg: ViTConfig):
        super().__init__()
        self.cfg = cfg

        self.patch_embed = PatchEmbedding(
            cfg.img_size, cfg.patch_size, cfg.in_channels, cfg.embed_dim
        )
        # [CLS] token: a learnable vector prepended to the patch sequence
        self.cls_token = nn.Parameter(torch.zeros(1, 1, cfg.embed_dim))
        self.pos_embed = PositionalEmbedding(cfg.n_patches, cfg.embed_dim)
        self.emb_drop = nn.Dropout(cfg.emb_dropout)

        self.blocks = nn.Sequential(*[ViTBlock(cfg) for _ in range(cfg.depth)])
        self.norm = nn.LayerNorm(cfg.embed_dim)

        self._init_weights()

    def _init_weights(self):
        nn.init.trunc_normal_(self.cls_token, std=0.02)
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.trunc_normal_(m.weight, std=0.02)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
            elif isinstance(m, nn.LayerNorm):
                nn.init.ones_(m.weight)
                nn.init.zeros_(m.bias)

    def forward(self, x: torch.Tensor) -> dict:
        """
        Args:
            x: (batch_size, in_channels, img_size, img_size)
        Returns:
            dict with:
              'cls':    (batch_size, embed_dim)   — global image feature
              'tokens': (batch_size, n_patches, embed_dim)  — per-patch features
              'all':    (batch_size, n_patches+1, embed_dim) — cls + patches
        """
        B = x.shape[0]

        # 1. Patch embeddings: (B, n_patches, D)
        x = self.patch_embed(x)

        # 2. Prepend [CLS] token: (B, 1, D) → (B, n_patches+1, D)
        cls = self.cls_token.expand(B, -1, -1)
        x = torch.cat([cls, x], dim=1)

        # 3. Add positional embeddings
        x = self.pos_embed(x)
        x = self.emb_drop(x)

        # 4. Transformer encoder blocks
        x = self.blocks(x)
        x = self.norm(x)

        return {
            "cls": x[:, 0],        # [CLS] token → global image representation
            "tokens": x[:, 1:],   # patch tokens → spatial features
            "all": x,             # everything
        }

    def count_parameters(self) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
