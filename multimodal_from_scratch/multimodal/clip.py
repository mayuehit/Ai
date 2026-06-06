"""
CLIP — Contrastive Language-Image Pre-training — Chapter 2.

Trains a shared embedding space for images and text using InfoNCE loss.
After training, cosine similarity between image and text embeddings reflects
semantic alignment, enabling zero-shot classification.
"""

import math

import torch
import torch.nn as nn
import torch.nn.functional as F

from ..vision.patch_embedding import PatchEmbedding, PositionalEmbedding


# ── Shared transformer block (bidirectional) ──────────────────────────────────

class _BidirectionalAttention(nn.Module):
    def __init__(self, embed_dim: int, n_heads: int, dropout: float = 0.0):
        super().__init__()
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
        attn = F.softmax((q @ k.transpose(-2, -1)) * self.scale, dim=-1)
        return self.out_proj((self.drop(attn) @ v).transpose(1, 2).reshape(B, N, C))


class _TransformerBlock(nn.Module):
    def __init__(self, embed_dim: int, n_heads: int,
                 mlp_ratio: float = 4.0, dropout: float = 0.0):
        super().__init__()
        self.norm1 = nn.LayerNorm(embed_dim)
        self.attn  = _BidirectionalAttention(embed_dim, n_heads, dropout)
        self.norm2 = nn.LayerNorm(embed_dim)
        h          = int(embed_dim * mlp_ratio)
        self.ffn   = nn.Sequential(
            nn.Linear(embed_dim, h), nn.GELU(),
            nn.Linear(h, embed_dim), nn.Dropout(dropout),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.attn(self.norm1(x))
        return x + self.ffn(self.norm2(x))


# ── InfoNCE loss ──────────────────────────────────────────────────────────────

def infonce_loss(img_emb: torch.Tensor, txt_emb: torch.Tensor,
                 temperature: float = 0.07) -> torch.Tensor:
    """
    Symmetric InfoNCE / NT-Xent contrastive loss.

    Args:
        img_emb     : (B, D) L2-normalised image embeddings
        txt_emb     : (B, D) L2-normalised text embeddings
        temperature : softmax temperature (lower = sharper)

    Returns:
        Scalar loss.  Random baseline = ln(B).
    """
    B      = img_emb.shape[0]
    sim    = img_emb @ txt_emb.T / temperature   # (B, B)
    labels = torch.arange(B, device=img_emb.device)
    return (F.cross_entropy(sim, labels) + F.cross_entropy(sim.T, labels)) / 2


# ── Encoders ──────────────────────────────────────────────────────────────────

class CLIPImageEncoder(nn.Module):
    """
    ViT-based image encoder.
    Output: L2-normalised vector of shape (B, proj_dim).
    """

    def __init__(self, img_size=224, patch_size=16, in_channels=3,
                 embed_dim=768, depth=12, n_heads=12, proj_dim=512):
        super().__init__()
        self.patch_embed = PatchEmbedding(img_size, patch_size, in_channels, embed_dim)
        n_patches = self.patch_embed.n_patches
        self.cls_token = nn.Parameter(torch.zeros(1, 1, embed_dim))
        self.pos_embed = PositionalEmbedding(n_patches, embed_dim)
        self.blocks    = nn.ModuleList(
            [_TransformerBlock(embed_dim, n_heads) for _ in range(depth)]
        )
        self.norm = nn.LayerNorm(embed_dim)
        self.proj = nn.Linear(embed_dim, proj_dim, bias=False)
        nn.init.trunc_normal_(self.cls_token, std=0.02)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B = x.shape[0]
        t = torch.cat([self.cls_token.expand(B, -1, -1), self.patch_embed(x)], dim=1)
        t = self.pos_embed(t)
        for blk in self.blocks:
            t = blk(t)
        return F.normalize(self.proj(self.norm(t)[:, 0, :]), dim=-1)


class CLIPTextEncoder(nn.Module):
    """
    Bidirectional Transformer text encoder.

    Uses the embedding at the EOS token position, giving the model full
    bidirectional context over the caption before projecting.
    Output: L2-normalised vector of shape (B, proj_dim).
    """

    def __init__(self, vocab_size=49408, context_len=77,
                 embed_dim=512, depth=12, n_heads=8, proj_dim=512):
        super().__init__()
        self.tok_embed = nn.Embedding(vocab_size, embed_dim)
        self.pos_embed = nn.Embedding(context_len, embed_dim)
        self.blocks    = nn.ModuleList(
            [_TransformerBlock(embed_dim, n_heads) for _ in range(depth)]
        )
        self.norm = nn.LayerNorm(embed_dim)
        self.proj = nn.Linear(embed_dim, proj_dim, bias=False)

    def forward(self, token_ids: torch.Tensor,
                eos_positions: torch.Tensor) -> torch.Tensor:
        B, T   = token_ids.shape
        device = token_ids.device
        x = (self.tok_embed(token_ids)
             + self.pos_embed(torch.arange(T, device=device)).unsqueeze(0))
        for blk in self.blocks:
            x = blk(x)
        x = self.norm(x)
        eos_out = x[torch.arange(B, device=device), eos_positions]
        return F.normalize(self.proj(eos_out), dim=-1)


# ── Full CLIP model ───────────────────────────────────────────────────────────

class CLIP(nn.Module):
    """
    CLIP dual-encoder model.

    The learnable logit_scale stores log(1/τ) for numerical stability.
    Initial value log(1/0.07) ≈ 2.66 corresponds to τ = 0.07.
    """

    def __init__(self, img_size=224, patch_size=16, vocab_size=49408,
                 context_len=77, embed_dim=512, depth=12, n_heads=8,
                 proj_dim=512):
        super().__init__()
        self.image_encoder = CLIPImageEncoder(
            img_size, patch_size, 3, embed_dim, depth, n_heads, proj_dim
        )
        self.text_encoder = CLIPTextEncoder(
            vocab_size, context_len, embed_dim, depth, n_heads, proj_dim
        )
        self.logit_scale = nn.Parameter(torch.tensor(math.log(1.0 / 0.07)))

    def encode_image(self, images: torch.Tensor) -> torch.Tensor:
        return self.image_encoder(images)

    def encode_text(self, token_ids: torch.Tensor,
                    eos_positions: torch.Tensor) -> torch.Tensor:
        return self.text_encoder(token_ids, eos_positions)

    def forward(self, images: torch.Tensor, token_ids: torch.Tensor,
                eos_positions: torch.Tensor) -> dict:
        img_emb = self.encode_image(images)
        txt_emb = self.encode_text(token_ids, eos_positions)
        tau     = (1.0 / self.logit_scale.exp().clamp(min=1e-8)).item()
        loss    = infonce_loss(img_emb, txt_emb, temperature=tau)
        return {
            "loss":    loss,
            "sim":     img_emb @ txt_emb.T,
            "img_emb": img_emb,
            "txt_emb": txt_emb,
        }
