"""
Chapter 2.2 — Transformer Decoder Block
=========================================
Each GPT-style block consists of:
  1. Causal self-attention (so each token predicts the next)
  2. Feed-forward network (position-wise MLP)
  Both wrapped in residual connections and LayerNorm.
"""

import torch
import torch.nn as nn
from .attention import CausalMultiHeadAttention


class FeedForward(nn.Module):
    """
    Position-wise FFN: Linear → GELU → Linear
    Hidden dimension is typically 4× the embedding dimension.
    """

    def __init__(self, embed_dim: int, ffn_dim: int, dropout: float = 0.0):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(embed_dim, ffn_dim),
            nn.GELU(),
            nn.Linear(ffn_dim, embed_dim),
            nn.Dropout(dropout),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class TransformerBlock(nn.Module):
    """
    GPT-style Transformer block with Pre-LayerNorm:

        x = x + Attention(LayerNorm(x))
        x = x + FFN(LayerNorm(x))
    """

    def __init__(self, embed_dim: int, num_heads: int, ffn_dim: int,
                 context_len: int, dropout: float = 0.0):
        super().__init__()
        self.norm1 = nn.LayerNorm(embed_dim)
        self.attn = CausalMultiHeadAttention(embed_dim, num_heads, context_len, dropout)
        self.norm2 = nn.LayerNorm(embed_dim)
        self.ffn = FeedForward(embed_dim, ffn_dim, dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.attn(self.norm1(x))
        x = x + self.ffn(self.norm2(x))
        return x
