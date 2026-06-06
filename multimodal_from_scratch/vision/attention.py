"""
Chapter 1.2 — Multi-Head Self-Attention (Vision)
==================================================
This is the same scaled dot-product attention as in GPT, but WITHOUT
a causal mask — every image patch can attend to every other patch.

Scaled Dot-Product Attention:
    Attention(Q, K, V) = softmax(QKᵀ / √d_k) · V

Multi-head allows the model to jointly attend to information from
different representation subspaces at different positions.
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F


class MultiHeadSelfAttention(nn.Module):
    """
    Bidirectional multi-head self-attention (no causal mask).
    Used in the Vision Transformer encoder.
    """

    def __init__(self, embed_dim: int, num_heads: int, dropout: float = 0.0):
        super().__init__()
        assert embed_dim % num_heads == 0, \
            f"embed_dim ({embed_dim}) must be divisible by num_heads ({num_heads})"

        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        self.scale = self.head_dim ** -0.5  # 1/√d_k

        # Project input to queries, keys, values in one shot
        self.qkv = nn.Linear(embed_dim, 3 * embed_dim, bias=True)
        self.out_proj = nn.Linear(embed_dim, embed_dim)
        self.attn_drop = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (batch_size, seq_len, embed_dim)
        Returns:
            out: (batch_size, seq_len, embed_dim)
        """
        B, N, C = x.shape

        # Compute Q, K, V and split into heads
        # (B, N, 3*C) → (B, N, 3, num_heads, head_dim) → (3, B, num_heads, N, head_dim)
        qkv = self.qkv(x).reshape(B, N, 3, self.num_heads, self.head_dim)
        qkv = qkv.permute(2, 0, 3, 1, 4)
        q, k, v = qkv.unbind(0)  # each: (B, num_heads, N, head_dim)

        # Scaled dot-product attention
        attn = (q @ k.transpose(-2, -1)) * self.scale  # (B, num_heads, N, N)
        attn = F.softmax(attn, dim=-1)
        attn = self.attn_drop(attn)

        # Weighted sum of values
        out = (attn @ v)  # (B, num_heads, N, head_dim)
        # Merge heads: (B, num_heads, N, head_dim) → (B, N, C)
        out = out.transpose(1, 2).reshape(B, N, C)
        out = self.out_proj(out)
        return out
