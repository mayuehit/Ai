"""
Chapter 3 — CLIP: Contrastive Language-Image Pre-training
===========================================================
Reference: "Learning Transferable Visual Models From Natural Language
           Supervision" (Radford et al., OpenAI 2021)

Core idea:
  Given a batch of N (image, caption) pairs, train:
    - A vision encoder  fv(image)  → image embedding
    - A text encoder    ft(text)   → text embedding

  Maximise similarity of N matching pairs,
  minimise similarity of N²-N non-matching pairs.

  This is called InfoNCE (Noise-Contrastive Estimation) loss.

  Loss = (CrossEntropy(logits, targets, dim=0)      # image-to-text
        + CrossEntropy(logits, targets, dim=1)) / 2 # text-to-image

After training, CLIP can do zero-shot image classification by comparing
image embeddings to text embeddings of class descriptions like
"a photo of a {dog}".
"""

from dataclasses import dataclass
import torch
import torch.nn as nn
import torch.nn.functional as F

from ..vision.vit import VisionTransformer, ViTConfig
from ..language.transformer import TransformerBlock


# ---------------------------------------------------------------------------
# Lightweight text encoder for CLIP (bidirectional, not causal)
# ---------------------------------------------------------------------------

class CLIPTextEncoder(nn.Module):
    """
    Bidirectional Transformer text encoder.

    Unlike GPT (which is causal/decoder-only), CLIP's text encoder is
    encoder-only and uses the [EOS] token's representation as the output.
    Here we reuse ViT's bidirectional attention blocks — the only difference
    from ViT is that the input is tokens (not patches).
    """

    def __init__(self, vocab_size: int, context_len: int,
                 embed_dim: int, depth: int, num_heads: int,
                 dropout: float = 0.0):
        super().__init__()
        self.token_embed = nn.Embedding(vocab_size, embed_dim)
        self.pos_embed = nn.Embedding(context_len, embed_dim)
        self.drop = nn.Dropout(dropout)

        # Re-use ViT blocks (bidirectional attention) for the text side
        from ..vision.attention import MultiHeadSelfAttention

        class BidirectionalBlock(nn.Module):
            def __init__(self):
                super().__init__()
                self.norm1 = nn.LayerNorm(embed_dim)
                self.attn = MultiHeadSelfAttention(embed_dim, num_heads, dropout)
                self.norm2 = nn.LayerNorm(embed_dim)
                hidden = int(embed_dim * 4)
                self.ffn = nn.Sequential(
                    nn.Linear(embed_dim, hidden),
                    nn.GELU(),
                    nn.Linear(hidden, embed_dim),
                    nn.Dropout(dropout),
                )

            def forward(self, x):
                x = x + self.attn(self.norm1(x))
                x = x + self.ffn(self.norm2(x))
                return x

        self.blocks = nn.Sequential(*[BidirectionalBlock() for _ in range(depth)])
        self.norm = nn.LayerNorm(embed_dim)

    def forward(self, input_ids: torch.Tensor, eos_positions: torch.Tensor) -> torch.Tensor:
        """
        Args:
            input_ids:     (B, T)  token ids (padded to same length)
            eos_positions: (B,)    index of [EOS] token in each sequence
        Returns:
            text_features: (B, embed_dim)
        """
        B, T = input_ids.shape
        pos = torch.arange(T, device=input_ids.device).unsqueeze(0)
        x = self.token_embed(input_ids) + self.pos_embed(pos)
        x = self.drop(x)
        x = self.blocks(x)
        x = self.norm(x)

        # Take the [EOS] token representation as the text embedding
        text_features = x[torch.arange(B), eos_positions]
        return text_features


# ---------------------------------------------------------------------------
# CLIP model
# ---------------------------------------------------------------------------

@dataclass
class CLIPConfig:
    # Vision tower
    img_size: int = 224
    patch_size: int = 16
    vision_embed_dim: int = 768
    vision_depth: int = 12
    vision_heads: int = 12

    # Text tower
    vocab_size: int = 49408   # CLIP's BPE vocab
    context_len: int = 77     # CLIP's max text length
    text_embed_dim: int = 512
    text_depth: int = 12
    text_heads: int = 8

    # Shared projection dimension
    embed_dim: int = 512

    dropout: float = 0.0


class CLIP(nn.Module):
    """
    CLIP model: dual encoder with contrastive training.

    After training:
      image_features = model.encode_image(images)   # (B, embed_dim)
      text_features  = model.encode_text(texts, eos) # (B, embed_dim)
      similarity     = image_features @ text_features.T
    """

    def __init__(self, cfg: CLIPConfig):
        super().__init__()
        self.cfg = cfg

        # Vision encoder
        vit_cfg = ViTConfig(
            img_size=cfg.img_size,
            patch_size=cfg.patch_size,
            embed_dim=cfg.vision_embed_dim,
            depth=cfg.vision_depth,
            num_heads=cfg.vision_heads,
        )
        self.vision_encoder = VisionTransformer(vit_cfg)
        self.vision_proj = nn.Linear(cfg.vision_embed_dim, cfg.embed_dim, bias=False)

        # Text encoder
        self.text_encoder = CLIPTextEncoder(
            cfg.vocab_size, cfg.context_len,
            cfg.text_embed_dim, cfg.text_depth,
            cfg.text_heads, cfg.dropout,
        )
        self.text_proj = nn.Linear(cfg.text_embed_dim, cfg.embed_dim, bias=False)

        # Learnable temperature parameter (log scale for numerical stability)
        # Initialised to log(1/0.07) ≈ 2.66 as in the original CLIP paper
        self.logit_scale = nn.Parameter(torch.ones([]) * 2.6592)

    def encode_image(self, images: torch.Tensor) -> torch.Tensor:
        """
        Args:  images: (B, 3, H, W)
        Returns: L2-normalised image embeddings (B, embed_dim)
        """
        feats = self.vision_encoder(images)["cls"]  # (B, vision_embed_dim)
        feats = self.vision_proj(feats)             # (B, embed_dim)
        return F.normalize(feats, dim=-1)

    def encode_text(self, input_ids: torch.Tensor,
                    eos_positions: torch.Tensor) -> torch.Tensor:
        """
        Args:
            input_ids:     (B, T)
            eos_positions: (B,)  index of [EOS] token per sample
        Returns: L2-normalised text embeddings (B, embed_dim)
        """
        feats = self.text_encoder(input_ids, eos_positions)  # (B, text_embed_dim)
        feats = self.text_proj(feats)                        # (B, embed_dim)
        return F.normalize(feats, dim=-1)

    def forward(
        self,
        images: torch.Tensor,
        input_ids: torch.Tensor,
        eos_positions: torch.Tensor,
    ) -> dict:
        """
        Args:
            images:        (B, 3, H, W)
            input_ids:     (B, T)
            eos_positions: (B,)
        Returns:
            dict with 'loss', 'logits_per_image', 'logits_per_text'
        """
        img_emb = self.encode_image(images)    # (B, D)
        txt_emb = self.encode_text(input_ids, eos_positions)  # (B, D)

        # Temperature-scaled cosine similarity matrix
        scale = self.logit_scale.exp()
        logits_per_image = scale * img_emb @ txt_emb.T  # (B, B)
        logits_per_text  = logits_per_image.T            # (B, B)

        # Symmetric InfoNCE loss
        # Diagonal = positive pairs; off-diagonal = negatives
        labels = torch.arange(img_emb.shape[0], device=img_emb.device)
        loss_i = F.cross_entropy(logits_per_image, labels)  # image→text
        loss_t = F.cross_entropy(logits_per_text, labels)   # text→image
        loss = (loss_i + loss_t) / 2

        return {
            "loss": loss,
            "logits_per_image": logits_per_image,
            "logits_per_text": logits_per_text,
        }
