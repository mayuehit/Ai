"""
Projection MLP — the semantic bridge between vision and language spaces.

A two-layer MLP with GELU activation maps ViT patch tokens (vision_dim)
into GPT token embedding space (language_dim).

Why two layers?
  A single linear layer can only rotate and rescale.  The hidden GELU layer
  allows non-linear remapping between the two feature manifolds.

In practice this tiny module (< 1% of total parameters) carries most of
the burden during Stage 1 training.
"""

import torch
import torch.nn as nn


class ProjectionMLP(nn.Module):
    """
    Two-layer MLP projecting visual patch tokens into language embedding space.

    Args:
        vision_dim   : output dimension of the ViT encoder
        language_dim : embedding dimension of the GPT decoder
    """

    def __init__(self, vision_dim: int, language_dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(vision_dim, language_dim),
            nn.GELU(),
            nn.Linear(language_dim, language_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, N_patches, vision_dim)  →  (B, N_patches, language_dim)
        return self.net(x)
