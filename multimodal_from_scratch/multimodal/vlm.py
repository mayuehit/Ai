"""
Vision-Language Model (LLaVA-style) — Chapters 3 & 4.

Architecture:
    Image  →  ViT encoder  →  ProjectionMLP  →  visual prefix
    Text   →  GPT token embeddings
    [visual prefix | text embeddings]  →  GPT decoder  →  logits

Loss:
    Cross-entropy on text positions only.
    Visual token positions are labeled -100 so F.cross_entropy ignores them.

Two-stage training interface:
    model.set_stage1()  — freeze ViT + GPT, train only ProjectionMLP
    model.set_stage2()  — freeze ViT, train ProjectionMLP + GPT
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

from ..vision.vit import VisionTransformer
from ..language.gpt import GPTDecoder
from .projection import ProjectionMLP


class VisionLanguageModel(nn.Module):
    """
    LLaVA-style Vision-Language Model.

    Args:
        vit        : pretrained VisionTransformer instance
        projection : ProjectionMLP instance
        gpt        : GPTDecoder instance
    """

    def __init__(self, vit: VisionTransformer,
                 projection: ProjectionMLP,
                 gpt: GPTDecoder):
        super().__init__()
        self.vit        = vit
        self.projection = projection
        self.gpt        = gpt

    def forward(self, images: torch.Tensor, input_ids: torch.Tensor,
                labels: torch.Tensor | None = None):
        """
        Args:
            images    : (B, C, H, W)
            input_ids : (B, T) text token ids
            labels    : (B, T) targets for next-token prediction.
                        Set positions to -100 to exclude from loss
                        (e.g., instruction prefix, padding).

        Returns:
            logits : (B, N_visual + T, vocab_size)
            loss   : scalar or None
        """
        # 1. Image → patch tokens
        patch_tokens  = self.vit(images, return_all_tokens=True)  # (B, N, D_vit)
        # 2. Project to language space
        visual_prefix = self.projection(patch_tokens)              # (B, N, D_lang)
        # 3. GPT decoder
        logits, n_vis = self.gpt(input_ids, visual_prefix=visual_prefix)

        loss = None
        if labels is not None:
            # Predict each text token from its visual + prior text context
            text_logits  = logits[:, n_vis:-1, :]   # (B, T-1, vocab)
            text_targets = labels[:, 1:]             # (B, T-1)
            loss = F.cross_entropy(
                text_logits.reshape(-1, text_logits.size(-1)),
                text_targets.reshape(-1),
                ignore_index=-100,
            )
        return logits, loss

    # ── Stage control ─────────────────────────────────────────────────────────

    def set_stage1(self):
        """Freeze ViT and GPT; train only ProjectionMLP."""
        for p in self.vit.parameters():        p.requires_grad_(False)
        for p in self.gpt.parameters():        p.requires_grad_(False)
        for p in self.projection.parameters(): p.requires_grad_(True)

    def set_stage2(self):
        """Freeze ViT; train ProjectionMLP and GPT."""
        for p in self.vit.parameters():        p.requires_grad_(False)
        for p in self.projection.parameters(): p.requires_grad_(True)
        for p in self.gpt.parameters():        p.requires_grad_(True)

    def trainable_params(self) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad)

    def total_params(self) -> int:
        return sum(p.numel() for p in self.parameters())
