"""
Chapter 5.1 — Loss Functions
==============================
Two loss functions power multimodal training:

1. Contrastive (InfoNCE) loss  — used in CLIP pre-training
2. Language modelling (CE) loss — used in VLM instruction tuning
"""

import torch
import torch.nn.functional as F


def contrastive_loss(
    image_embeddings: torch.Tensor,
    text_embeddings: torch.Tensor,
    temperature: float = 0.07,
) -> torch.Tensor:
    """
    Symmetric InfoNCE loss for a batch of (image, text) pairs.

    For a batch of size N:
      - N pairs are "positive" (matching image-text)
      - N*(N-1) pairs are "negative" (mismatched)

    Args:
        image_embeddings: (B, D)  L2-normalised
        text_embeddings:  (B, D)  L2-normalised
        temperature:      scaling factor (lower = sharper distribution)
    Returns:
        scalar loss
    """
    B = image_embeddings.shape[0]
    logits = image_embeddings @ text_embeddings.T / temperature  # (B, B)
    labels = torch.arange(B, device=image_embeddings.device)

    loss_i2t = F.cross_entropy(logits, labels)        # image → text
    loss_t2i = F.cross_entropy(logits.T, labels)      # text → image
    return (loss_i2t + loss_t2i) / 2


def language_modeling_loss(
    logits: torch.Tensor,
    targets: torch.Tensor,
    ignore_index: int = -100,
) -> torch.Tensor:
    """
    Standard cross-entropy next-token prediction loss.

    Args:
        logits:  (B, T, vocab_size)  — model output
        targets: (B, T)              — shifted token ids (-100 = ignore)
    Returns:
        scalar mean loss over non-ignored positions
    """
    B, T, V = logits.shape
    return F.cross_entropy(
        logits.reshape(B * T, V),
        targets.reshape(B * T),
        ignore_index=ignore_index,
    )
