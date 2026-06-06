"""
Chapter 2.3 — GPT-style Autoregressive Language Model
=======================================================
This is a standalone GPT decoder — identical to what you'd find in
"Build a Large Language Model from Scratch" Ch 4/5.

In Chapter 4 we will extend this by injecting visual tokens from ViT
into the token sequence before decoding (the LLaVA approach).

Architecture:
  TokenEmbedding + PositionalEmbedding
  → N × TransformerBlock
  → LayerNorm
  → Linear head (vocab_size)

During training we predict the NEXT token at every position:
  Loss = CrossEntropy(logits[:, :-1], targets[:, 1:])
"""

from dataclasses import dataclass
import torch
import torch.nn as nn
from .transformer import TransformerBlock


@dataclass
class GPTConfig:
    vocab_size: int = 50257    # GPT-2 BPE vocabulary
    context_len: int = 1024    # maximum sequence length
    embed_dim: int = 768
    depth: int = 12            # number of Transformer blocks
    num_heads: int = 12
    ffn_multiplier: int = 4    # ffn_dim = embed_dim * ffn_multiplier
    dropout: float = 0.1
    emb_dropout: float = 0.1

    @property
    def ffn_dim(self) -> int:
        return self.embed_dim * self.ffn_multiplier

    # Preset sizes matching GPT-2 paper
    @classmethod
    def gpt2_small(cls) -> "GPTConfig":
        return cls(embed_dim=768, depth=12, num_heads=12)

    @classmethod
    def gpt2_medium(cls) -> "GPTConfig":
        return cls(embed_dim=1024, depth=24, num_heads=16)

    @classmethod
    def gpt2_large(cls) -> "GPTConfig":
        return cls(embed_dim=1280, depth=36, num_heads=20)

    @classmethod
    def gpt2_xl(cls) -> "GPTConfig":
        return cls(embed_dim=1600, depth=48, num_heads=25)


class GPT(nn.Module):
    """
    GPT: autoregressive language model.

    Accepts optional `visual_prefix` — a sequence of visual tokens
    (from ViT + projection) that are prepended to the text tokens.
    This is the hook used in Chapter 4 to build the VLM.
    """

    def __init__(self, cfg: GPTConfig):
        super().__init__()
        self.cfg = cfg

        self.token_embed = nn.Embedding(cfg.vocab_size, cfg.embed_dim)
        self.pos_embed = nn.Embedding(cfg.context_len, cfg.embed_dim)
        self.emb_drop = nn.Dropout(cfg.emb_dropout)

        self.blocks = nn.ModuleList([
            TransformerBlock(
                cfg.embed_dim, cfg.num_heads, cfg.ffn_dim,
                cfg.context_len, cfg.dropout
            )
            for _ in range(cfg.depth)
        ])
        self.norm = nn.LayerNorm(cfg.embed_dim)
        # Weight-tied output projection (same matrix as token embedding)
        self.lm_head = nn.Linear(cfg.embed_dim, cfg.vocab_size, bias=False)
        self.lm_head.weight = self.token_embed.weight  # weight tying

        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, mean=0.0, std=0.02)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
            elif isinstance(m, nn.Embedding):
                nn.init.normal_(m.weight, mean=0.0, std=0.02)

    def forward(
        self,
        input_ids: torch.Tensor,
        visual_prefix: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """
        Args:
            input_ids:     (batch_size, seq_len)  token indices
            visual_prefix: (batch_size, n_img_tokens, embed_dim)  optional
        Returns:
            logits: (batch_size, total_len, vocab_size)
        """
        B, T = input_ids.shape
        device = input_ids.device

        # Token + positional embeddings
        pos = torch.arange(T, device=device).unsqueeze(0)
        x = self.token_embed(input_ids) + self.pos_embed(pos)

        # Prepend visual tokens if provided (Chapter 4 hook)
        if visual_prefix is not None:
            x = torch.cat([visual_prefix, x], dim=1)

        x = self.emb_drop(x)

        for block in self.blocks:
            x = block(x)

        x = self.norm(x)
        logits = self.lm_head(x)
        return logits

    @torch.no_grad()
    def generate(
        self,
        input_ids: torch.Tensor,
        max_new_tokens: int = 50,
        temperature: float = 1.0,
        top_k: int | None = None,
        visual_prefix: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """
        Autoregressive generation via greedy / top-k sampling.

        Args:
            input_ids:      (1, seq_len)  starting token ids (prompt)
            max_new_tokens: number of tokens to generate
            temperature:    > 1 = more random, < 1 = sharper, 1 = unchanged
            top_k:          if set, only sample from the top-k logits
            visual_prefix:  optional visual context (only used for first pass)
        Returns:
            (1, seq_len + max_new_tokens)
        """
        for i in range(max_new_tokens):
            # Truncate if sequence exceeds context length
            ids_cond = input_ids[:, -self.cfg.context_len:]

            # Only attach visual prefix on the very first pass
            vp = visual_prefix if i == 0 else None
            logits = self(ids_cond, visual_prefix=vp)

            # Take logits at the last position
            logits = logits[:, -1, :] / temperature

            if top_k is not None:
                # Zero out all logits below the k-th largest
                v, _ = torch.topk(logits, top_k)
                logits[logits < v[:, [-1]]] = float("-inf")

            probs = torch.softmax(logits, dim=-1)
            next_id = torch.multinomial(probs, num_samples=1)
            input_ids = torch.cat([input_ids, next_id], dim=1)

        return input_ids

    def count_parameters(self) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
