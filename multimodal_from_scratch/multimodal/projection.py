"""
Chapter 4.1 — Vision-to-Language Projection Layer
===================================================
The vision encoder (ViT) outputs vectors in "vision space" (e.g. 768-dim),
while the language model works in "language space" (e.g. 768-dim with a
different semantic meaning).

We need a small learnable network to translate between these spaces.

LLaVA uses a two-layer MLP:
    vision_dim → hidden_dim → language_dim
with GELU activation.

This is sometimes called the "connector" or "adapter" in the literature.

Why not just a single linear layer?
  The MLP gives the model capacity to perform a non-linear mapping,
  which empirically helps align the feature spaces.
"""

import torch
import torch.nn as nn


class ProjectionMLP(nn.Module):
    """
    Two-layer MLP that projects vision features into language model space.

    Used to convert ViT patch tokens (or [CLS] token) into "visual tokens"
    that the language decoder can process alongside text tokens.
    """

    def __init__(self, vision_dim: int, language_dim: int,
                 hidden_dim: int | None = None):
        super().__init__()
        if hidden_dim is None:
            hidden_dim = language_dim  # sensible default

        self.net = nn.Sequential(
            nn.Linear(vision_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, language_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (batch_size, n_tokens, vision_dim)  — patch tokens from ViT
        Returns:
            (batch_size, n_tokens, language_dim)   — ready to concat with text
        """
        return self.net(x)


class LinearProjection(nn.Module):
    """Single linear projection (simpler baseline, used in early LLaVA v1)."""

    def __init__(self, vision_dim: int, language_dim: int):
        super().__init__()
        self.proj = nn.Linear(vision_dim, language_dim, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.proj(x)
