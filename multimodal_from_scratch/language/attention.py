"""
Chapter 2.1 — Causal Multi-Head Self-Attention
================================================
Language models generate text left-to-right. To prevent the model from
"peeking" at future tokens during training, we apply a causal (triangular)
mask that zeros out all attention weights above the diagonal.

Comparison with Vision attention (Ch 1.2):
  Vision: bidirectional (every patch sees every patch)
  Language: causal / unidirectional (each token only sees past tokens)
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F


class CausalMultiHeadAttention(nn.Module):
    """
    Causal (masked) multi-head self-attention for autoregressive language models.
    """

    def __init__(self, embed_dim: int, num_heads: int,
                 context_len: int, dropout: float = 0.0):
        super().__init__()
        assert embed_dim % num_heads == 0

        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        self.scale = self.head_dim ** -0.5

        self.qkv = nn.Linear(embed_dim, 3 * embed_dim, bias=False)
        self.out_proj = nn.Linear(embed_dim, embed_dim, bias=False)
        self.attn_drop = nn.Dropout(dropout)
        self.resid_drop = nn.Dropout(dropout)

        # Causal mask: upper triangle = -inf so softmax → 0 for future tokens
        # Registered as buffer so it moves with .to(device) but isn't a parameter
        self.register_buffer(
            "causal_mask",
            torch.triu(torch.ones(context_len, context_len), diagonal=1).bool()
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (batch_size, seq_len, embed_dim)
        Returns:
            out: (batch_size, seq_len, embed_dim)
        """
        B, T, C = x.shape

        qkv = self.qkv(x).reshape(B, T, 3, self.num_heads, self.head_dim)
        qkv = qkv.permute(2, 0, 3, 1, 4)
        q, k, v = qkv.unbind(0)  # each: (B, heads, T, head_dim)

        # Attention scores
        attn = (q @ k.transpose(-2, -1)) * self.scale  # (B, heads, T, T)

        # Apply causal mask: block attention to future positions
        attn = attn.masked_fill(self.causal_mask[:T, :T], float("-inf"))

        attn = F.softmax(attn, dim=-1)
        attn = self.attn_drop(attn)

        out = (attn @ v).transpose(1, 2).reshape(B, T, C)
        out = self.out_proj(out)
        out = self.resid_drop(out)
        return out
