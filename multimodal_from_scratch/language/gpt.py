"""
GPT Decoder with optional visual prefix support — Chapter 3.

Extends the standard causal GPT with a visual_prefix parameter.
When provided, visual tokens are prepended and receive bidirectional
attention; text tokens remain causal.

Attention mask layout (n_visual=3, T=4):
          V1  V2  V3  t1  t2  t3  t4
    V1  [ OK  OK  OK   X   X   X   X ]
    V2  [ OK  OK  OK   X   X   X   X ]
    V3  [ OK  OK  OK   X   X   X   X ]
    t1  [ OK  OK  OK  OK   X   X   X ]
    t2  [ OK  OK  OK  OK  OK   X   X ]
    t3  [ OK  OK  OK  OK  OK  OK   X ]
    t4  [ OK  OK  OK  OK  OK  OK  OK ]
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class GPTBlock(nn.Module):
    """Transformer decoder block with combined causal + visual attention mask."""

    def __init__(self, embed_dim: int, n_heads: int):
        super().__init__()
        self.norm1 = nn.LayerNorm(embed_dim)
        self.norm2 = nn.LayerNorm(embed_dim)
        self.attn  = nn.MultiheadAttention(embed_dim, n_heads, batch_first=True)
        self.ffn   = nn.Sequential(
            nn.Linear(embed_dim, embed_dim * 4), nn.GELU(),
            nn.Linear(embed_dim * 4, embed_dim),
        )

    def _build_mask(self, T: int, n_visual: int, device: torch.device) -> torch.Tensor:
        # Start with a full causal mask
        mask = torch.triu(torch.ones(T, T, device=device), diagonal=1).bool()
        if n_visual > 0:
            # Visual rows: no restriction (bidirectional among themselves)
            mask[:n_visual, :]       = False
            # Text rows: can attend to all visual positions
            mask[n_visual:, :n_visual] = False
        return mask

    def forward(self, x: torch.Tensor, n_visual: int = 0) -> torch.Tensor:
        T    = x.shape[1]
        mask = self._build_mask(T, n_visual, x.device)
        h    = self.norm1(x)
        out, _ = self.attn(h, h, h, attn_mask=mask)
        x    = x + out
        return x + self.ffn(self.norm2(x))


class GPTDecoder(nn.Module):
    """
    GPT-style autoregressive decoder with optional visual prefix.

    Args:
        vocab_size : vocabulary size
        embed_dim  : token embedding dimension
        depth      : number of transformer blocks
        n_heads    : attention heads
        max_seq    : maximum sequence length (text tokens only)
    """

    def __init__(self, vocab_size: int, embed_dim: int = 768,
                 depth: int = 12, n_heads: int = 12, max_seq: int = 1024):
        super().__init__()
        self.token_embed = nn.Embedding(vocab_size, embed_dim)
        self.pos_embed   = nn.Embedding(max_seq, embed_dim)
        self.blocks      = nn.ModuleList(
            [GPTBlock(embed_dim, n_heads) for _ in range(depth)]
        )
        self.norm    = nn.LayerNorm(embed_dim)
        self.lm_head = nn.Linear(embed_dim, vocab_size, bias=False)
        # Weight tying: share parameters between input embedding and output projection
        self.lm_head.weight = self.token_embed.weight
        self.max_seq = max_seq

    def forward(self, input_ids: torch.Tensor,
                visual_prefix: torch.Tensor | None = None):
        """
        Args:
            input_ids     : (B, T) token ids
            visual_prefix : (B, N_img, embed_dim) projected visual tokens, or None

        Returns:
            logits   : (B, N_img + T, vocab_size)
            n_visual : number of visual token positions (0 if no prefix)
        """
        B, T   = input_ids.shape
        device = input_ids.device
        n_visual = 0

        if visual_prefix is not None:
            n_visual = visual_prefix.shape[1]
            vpos = self.pos_embed(torch.arange(n_visual, device=device)).unsqueeze(0)
            tpos = self.pos_embed(
                torch.arange(n_visual, n_visual + T, device=device)
            ).unsqueeze(0)
            x = torch.cat(
                [visual_prefix + vpos, self.token_embed(input_ids) + tpos], dim=1
            )
        else:
            pos = self.pos_embed(torch.arange(T, device=device)).unsqueeze(0)
            x   = self.token_embed(input_ids) + pos

        for blk in self.blocks:
            x = blk(x, n_visual=n_visual)
        x = self.norm(x)
        return self.lm_head(x), n_visual
