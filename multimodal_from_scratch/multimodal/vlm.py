"""
Chapter 4.2 — Vision-Language Model (VLM)
==========================================
Reference architecture: LLaVA-1.5 (Liu et al., 2023)

Full pipeline:
  Image  → ViT → patch tokens (B, N_img, D_v)
                → ProjectionMLP → visual tokens (B, N_img, D_l)
                                                        ↓
  Text   → TokenEmbedding                  → text tokens (B, T, D_l)
                                                        ↓
                    Concat: [visual tokens | text tokens] (B, N_img+T, D_l)
                                                        ↓
                              GPT decoder blocks
                                                        ↓
                              Language model head → logits

During training:
  - Visual tokens are NOT supervised (loss masked to -100)
  - Only text tokens contribute to the language modelling loss
  - This matches how LLaVA and InstructBLIP work

Training stages (matching LLaVA):
  Stage 1 (feature alignment):
    - Freeze ViT + LLM, train ONLY ProjectionMLP
    - Teaches projection to map vision → language space

  Stage 2 (instruction tuning):
    - Freeze ViT, train ProjectionMLP + LLM together
    - Teaches the model to follow visual instructions
"""

from dataclasses import dataclass
import torch
import torch.nn as nn
import torch.nn.functional as F

from ..vision.vit import VisionTransformer, ViTConfig
from ..language.gpt import GPT, GPTConfig
from .projection import ProjectionMLP


@dataclass
class VLMConfig:
    # Vision tower config
    vit: ViTConfig = None

    # Language model config
    gpt: GPTConfig = None

    # Projection MLP hidden dim (None → same as language embed_dim)
    proj_hidden_dim: int | None = None

    # Number of image tokens passed to the LLM
    # 'all'  → use all N_patches patch tokens (more detail)
    # 'cls'  → use only 1 [CLS] token (cheaper)
    image_token_mode: str = "all"   # "all" | "cls"

    def __post_init__(self):
        if self.vit is None:
            self.vit = ViTConfig()
        if self.gpt is None:
            self.gpt = GPTConfig()


class VisionLanguageModel(nn.Module):
    """
    Minimal LLaVA-style Vision-Language Model.

    The image is encoded by ViT, projected into language space, and
    prepended to the token sequence before the GPT decoder.
    """

    def __init__(self, cfg: VLMConfig):
        super().__init__()
        self.cfg = cfg

        # --- Vision encoder ---
        self.vision_encoder = VisionTransformer(cfg.vit)

        # --- Projection MLP ---
        self.projection = ProjectionMLP(
            vision_dim=cfg.vit.embed_dim,
            language_dim=cfg.gpt.embed_dim,
            hidden_dim=cfg.proj_hidden_dim,
        )

        # --- Language model ---
        self.language_model = GPT(cfg.gpt)

    # ------------------------------------------------------------------
    # Training stage helpers
    # ------------------------------------------------------------------

    def freeze_vision_encoder(self):
        """Freeze all ViT parameters."""
        for p in self.vision_encoder.parameters():
            p.requires_grad = False

    def freeze_language_model(self):
        """Freeze all GPT parameters."""
        for p in self.language_model.parameters():
            p.requires_grad = False

    def unfreeze_language_model(self):
        for p in self.language_model.parameters():
            p.requires_grad = True

    def set_stage1(self):
        """
        Stage 1 (feature alignment): only train the projection MLP.
        ViT and LLM are frozen.
        """
        self.freeze_vision_encoder()
        self.freeze_language_model()
        for p in self.projection.parameters():
            p.requires_grad = True

    def set_stage2(self):
        """
        Stage 2 (instruction tuning): train projection + LLM.
        ViT stays frozen.
        """
        self.freeze_vision_encoder()
        self.unfreeze_language_model()
        for p in self.projection.parameters():
            p.requires_grad = True

    # ------------------------------------------------------------------
    # Core forward pass
    # ------------------------------------------------------------------

    def encode_image(self, images: torch.Tensor) -> torch.Tensor:
        """
        Encode images to visual token embeddings in language space.

        Args:
            images: (B, 3, H, W)
        Returns:
            visual_tokens: (B, n_img_tokens, language_embed_dim)
        """
        out = self.vision_encoder(images)

        if self.cfg.image_token_mode == "cls":
            # Use only [CLS] token: (B, 1, D_v)
            feats = out["cls"].unsqueeze(1)
        else:
            # Use all patch tokens: (B, n_patches, D_v)
            feats = out["tokens"]

        # Project to language space
        visual_tokens = self.projection(feats)  # (B, n_img_tokens, D_l)
        return visual_tokens

    def forward(
        self,
        images: torch.Tensor,
        input_ids: torch.Tensor,
        labels: torch.Tensor | None = None,
    ) -> dict:
        """
        Args:
            images:    (B, 3, H, W)
            input_ids: (B, T)   text token ids
            labels:    (B, T)   targets for LM loss; -100 means ignore
                                (typically: image region = -100, text = token_id)
        Returns:
            dict with 'logits' and optionally 'loss'
        """
        # 1. Encode image to visual tokens
        visual_tokens = self.encode_image(images)  # (B, n_img, D_l)
        n_img = visual_tokens.shape[1]

        # 2. Forward through GPT with visual prefix
        logits = self.language_model(input_ids, visual_prefix=visual_tokens)
        # logits shape: (B, n_img + T, vocab_size)

        result = {"logits": logits}

        if labels is not None:
            # Shift for next-token prediction
            # logits for text tokens start at position n_img
            text_logits = logits[:, n_img:-1, :]   # (B, T-1, V)
            text_labels = labels[:, 1:]             # (B, T-1)

            loss = F.cross_entropy(
                text_logits.reshape(-1, text_logits.shape[-1]),
                text_labels.reshape(-1),
                ignore_index=-100,
            )
            result["loss"] = loss

        return result

    @torch.no_grad()
    def generate(
        self,
        images: torch.Tensor,
        input_ids: torch.Tensor,
        max_new_tokens: int = 128,
        temperature: float = 1.0,
        top_k: int | None = 50,
    ) -> torch.Tensor:
        """
        Generate text conditioned on an image.

        Args:
            images:         (1, 3, H, W)
            input_ids:      (1, T)   text prompt tokens
            max_new_tokens: how many tokens to generate
        Returns:
            (1, T + max_new_tokens)  generated token ids
        """
        visual_tokens = self.encode_image(images)  # (1, n_img, D_l)
        return self.language_model.generate(
            input_ids=input_ids,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_k=top_k,
            visual_prefix=visual_tokens,
        )

    def count_parameters(self, trainable_only: bool = True) -> dict:
        def _count(module):
            if trainable_only:
                return sum(p.numel() for p in module.parameters() if p.requires_grad)
            return sum(p.numel() for p in module.parameters())

        return {
            "vision_encoder": _count(self.vision_encoder),
            "projection":     _count(self.projection),
            "language_model": _count(self.language_model),
            "total":          _count(self),
        }
