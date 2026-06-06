"""
Vision Transformer (ViT) — Chapter 1.

Architecture mirrors GPT exactly, with one critical difference:
  ViT uses BIDIRECTIONAL attention (no causal mask).
  GPT uses CAUSAL attention (upper-triangle mask).

Images have no temporal order, so every patch should attend to every other.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

from .patch_embedding import PatchEmbedding, PositionalEmbedding


class MultiHeadSelfAttention(nn.Module):
    """Bidirectional multi-head self-attention (no causal mask)."""

    def __init__(self, embed_dim: int, n_heads: int, dropout: float = 0.0):
        super().__init__()
        assert embed_dim % n_heads == 0
        self.n_heads  = n_heads
        self.head_dim = embed_dim // n_heads
        self.scale    = self.head_dim ** -0.5
        self.qkv      = nn.Linear(embed_dim, 3 * embed_dim)
        self.out_proj = nn.Linear(embed_dim, embed_dim)
        self.drop     = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B, N, C = x.shape
        qkv = self.qkv(x).reshape(B, N, 3, self.n_heads, self.head_dim)
        q, k, v = qkv.permute(2, 0, 3, 1, 4).unbind(0)
        # No masked_fill — full bidirectional attention
        attn = F.softmax((q @ k.transpose(-2, -1)) * self.scale, dim=-1)
        attn = self.drop(attn)
        return self.out_proj((attn @ v).transpose(1, 2).reshape(B, N, C))


class ViTBlock(nn.Module):
    """
    Transformer encoder block with Pre-LayerNorm.

        x = x + Attention(LayerNorm(x))
        x = x + FFN(LayerNorm(x))
    """

    def __init__(self, embed_dim: int, n_heads: int,
                 mlp_ratio: float = 4.0, dropout: float = 0.0):
        super().__init__()
        self.norm1 = nn.LayerNorm(embed_dim)
        self.attn  = MultiHeadSelfAttention(embed_dim, n_heads, dropout)
        self.norm2 = nn.LayerNorm(embed_dim)
        hidden     = int(embed_dim * mlp_ratio)
        self.ffn   = nn.Sequential(
            nn.Linear(embed_dim, hidden), nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden, embed_dim), nn.Dropout(dropout),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.attn(self.norm1(x))
        return x + self.ffn(self.norm2(x))


class VisionTransformer(nn.Module):
    """
    Vision Transformer (ViT-B/16 style).

    Forward pass returns the [CLS] token embedding by default, which
    serves as the global image representation.

    Args:
        img_size    : input image size
        patch_size  : patch size
        in_channels : image channels
        embed_dim   : token embedding dimension
        depth       : number of transformer blocks
        n_heads     : attention heads
        dropout     : dropout probability
    """

    def __init__(self, img_size=224, patch_size=16, in_channels=3,
                 embed_dim=768, depth=12, n_heads=12, dropout=0.1):
        super().__init__()
        self.patch_embed = PatchEmbedding(img_size, patch_size, in_channels, embed_dim)
        n_patches = self.patch_embed.n_patches

        self.cls_token = nn.Parameter(torch.zeros(1, 1, embed_dim))
        self.pos_embed = PositionalEmbedding(n_patches, embed_dim)
        self.blocks    = nn.ModuleList(
            [ViTBlock(embed_dim, n_heads, dropout=dropout) for _ in range(depth)]
        )
        self.norm = nn.LayerNorm(embed_dim)

        nn.init.trunc_normal_(self.cls_token, std=0.02)

    def forward(self, x: torch.Tensor,
                return_all_tokens: bool = False) -> torch.Tensor:
        B = x.shape[0]
        tokens = self.patch_embed(x)
        cls    = self.cls_token.expand(B, -1, -1)
        tokens = torch.cat([cls, tokens], dim=1)
        tokens = self.pos_embed(tokens)
        for blk in self.blocks:
            tokens = blk(tokens)
        tokens = self.norm(tokens)
        if return_all_tokens:
            return tokens                    # (B, N+1, D)
        return tokens[:, 0, :]              # CLS only  (B, D)
