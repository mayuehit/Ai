"""
Training utilities for CLIP and VLM — Chapter 4.

CLIPTrainer  : manages CLIP contrastive training loop
VLMTrainer   : manages two-stage VLM training with optional scheduler
"""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader


class CLIPTrainer:
    """
    Training loop for CLIP.

    Args:
        model     : CLIP instance
        optimizer : any torch optimizer
        device    : 'cpu' or 'cuda'
    """

    def __init__(self, model, optimizer, device="cpu"):
        self.model     = model
        self.optimizer = optimizer
        self.device    = device

    def train_epoch(self, loader: DataLoader) -> float:
        self.model.train()
        total = 0.0
        for images, token_ids, eos_positions, *_ in loader:
            images       = images.to(self.device)
            token_ids    = token_ids.to(self.device)
            eos_positions = eos_positions.to(self.device)
            out = self.model(images, token_ids, eos_positions)
            self.optimizer.zero_grad()
            out["loss"].backward()
            self.optimizer.step()
            total += out["loss"].item()
        return total / len(loader)

    def fit(self, loader: DataLoader, epochs: int,
            print_every: int = 1) -> list[float]:
        history = []
        for epoch in range(1, epochs + 1):
            loss = self.train_epoch(loader)
            history.append(loss)
            if epoch % print_every == 0:
                tau = (1.0 / self.model.logit_scale.exp()).item()
                print(f"Epoch {epoch:4d}/{epochs}  loss={loss:.4f}  tau={tau:.4f}")
        return history


class VLMTrainer:
    """
    Two-stage training loop for VisionLanguageModel.

    Stage 1: model.set_stage1() — trains only ProjectionMLP
    Stage 2: model.set_stage2() — trains ProjectionMLP + GPT

    Args:
        model     : VisionLanguageModel instance
        device    : 'cpu' or 'cuda'
    """

    def __init__(self, model, device="cpu"):
        self.model  = model
        self.device = device

    def _train_epoch(self, loader: DataLoader, optimizer) -> float:
        self.model.train()
        total = 0.0
        for images, input_ids, *rest in loader:
            images    = images.to(self.device)
            input_ids = input_ids.to(self.device)
            labels    = rest[0].to(self.device) if rest else input_ids
            _, loss   = self.model(images, input_ids, labels=labels)
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
            optimizer.step()
            total += loss.item()
        return total / len(loader)

    def stage1(self, loader: DataLoader, epochs: int,
               lr: float = 3e-3, print_every: int = 1) -> list[float]:
        self.model.set_stage1()
        optimizer = torch.optim.AdamW(
            filter(lambda p: p.requires_grad, self.model.parameters()), lr=lr
        )
        history = []
        for epoch in range(1, epochs + 1):
            loss = self._train_epoch(loader, optimizer)
            history.append(loss)
            if epoch % print_every == 0:
                print(f"[Stage 1] Epoch {epoch:4d}/{epochs}  loss={loss:.4f}")
        return history

    def stage2(self, loader: DataLoader, epochs: int,
               lr: float = 1e-3, print_every: int = 1) -> list[float]:
        self.model.set_stage2()
        optimizer = torch.optim.AdamW(
            filter(lambda p: p.requires_grad, self.model.parameters()), lr=lr
        )
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer, T_max=epochs, eta_min=lr / 10
        )
        history = []
        for epoch in range(1, epochs + 1):
            loss = self._train_epoch(loader, optimizer)
            scheduler.step()
            history.append(loss)
            if epoch % print_every == 0:
                cur_lr = optimizer.param_groups[0]["lr"]
                print(f"[Stage 2] Epoch {epoch:4d}/{epochs}  loss={loss:.4f}  lr={cur_lr:.2e}")
        return history
