"""
Chapter 5.2 — Training Loops
==============================
Simple, readable training loops for CLIP and VLM.
These are intentionally minimal — no distributed training, no AMP,
no gradient accumulation — so you can follow every step.

For production training, see the original repositories:
  CLIP:  https://github.com/openai/CLIP
  LLaVA: https://github.com/haotian-liu/LLaVA
"""

import time
from typing import Callable

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR


class CLIPTrainer:
    """
    Trains a CLIP model (Chapter 3).

    The training loop:
      for each batch (images, input_ids, eos_positions):
        1. Forward pass → compute contrastive loss
        2. Backward pass → gradients
        3. Gradient clipping (important for stability)
        4. Optimiser step
        5. Log metrics
    """

    def __init__(
        self,
        model: nn.Module,
        train_loader: DataLoader,
        val_loader: DataLoader | None = None,
        lr: float = 5e-4,
        weight_decay: float = 0.1,
        max_epochs: int = 30,
        grad_clip: float = 1.0,
        device: str = "cuda",
        log_every: int = 50,
    ):
        self.model = model.to(device)
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.device = device
        self.grad_clip = grad_clip
        self.log_every = log_every
        self.max_epochs = max_epochs

        self.optimizer = AdamW(
            model.parameters(), lr=lr, weight_decay=weight_decay,
            betas=(0.9, 0.98), eps=1e-6,
        )
        total_steps = max_epochs * len(train_loader)
        self.scheduler = CosineAnnealingLR(self.optimizer, T_max=total_steps)

    def train(self):
        self.model.train()
        for epoch in range(self.max_epochs):
            epoch_loss = 0.0
            t0 = time.time()

            for step, batch in enumerate(self.train_loader):
                images = batch["images"].to(self.device)
                input_ids = batch["input_ids"].to(self.device)
                eos_positions = batch["eos_positions"].to(self.device)

                out = self.model(images, input_ids, eos_positions)
                loss = out["loss"]

                self.optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(self.model.parameters(), self.grad_clip)
                self.optimizer.step()
                self.scheduler.step()

                epoch_loss += loss.item()

                if (step + 1) % self.log_every == 0:
                    avg = epoch_loss / (step + 1)
                    lr = self.scheduler.get_last_lr()[0]
                    print(f"Epoch {epoch+1} | Step {step+1} | "
                          f"loss={avg:.4f} | lr={lr:.2e}")

            elapsed = time.time() - t0
            print(f"Epoch {epoch+1} done in {elapsed:.1f}s | "
                  f"avg loss={epoch_loss/len(self.train_loader):.4f}")

            if self.val_loader is not None:
                val_loss = self._validate()
                print(f"  → val loss={val_loss:.4f}")

    @torch.no_grad()
    def _validate(self) -> float:
        self.model.eval()
        total_loss = 0.0
        for batch in self.val_loader:
            images = batch["images"].to(self.device)
            input_ids = batch["input_ids"].to(self.device)
            eos_positions = batch["eos_positions"].to(self.device)
            out = self.model(images, input_ids, eos_positions)
            total_loss += out["loss"].item()
        self.model.train()
        return total_loss / len(self.val_loader)


class VLMTrainer:
    """
    Two-stage VLM training (Chapter 5).

    Stage 1 — feature alignment:
      Freeze ViT + LLM, train only ProjectionMLP.
      Dataset: image-caption pairs.

    Stage 2 — instruction tuning:
      Freeze ViT, train ProjectionMLP + LLM.
      Dataset: visual instruction-following data (image, question, answer).
    """

    def __init__(
        self,
        model: nn.Module,
        device: str = "cuda",
        lr_stage1: float = 1e-3,
        lr_stage2: float = 2e-5,
        weight_decay: float = 0.0,
        grad_clip: float = 1.0,
        log_every: int = 50,
    ):
        self.model = model.to(device)
        self.device = device
        self.lr_stage1 = lr_stage1
        self.lr_stage2 = lr_stage2
        self.weight_decay = weight_decay
        self.grad_clip = grad_clip
        self.log_every = log_every

    def run_stage(
        self,
        stage: int,
        loader: DataLoader,
        epochs: int,
    ):
        """
        Run one training stage.

        Args:
            stage:  1 (alignment) or 2 (instruction tuning)
            loader: DataLoader yielding dicts with 'images', 'input_ids', 'labels'
            epochs: number of epochs
        """
        if stage == 1:
            print("=== Stage 1: Feature Alignment ===")
            self.model.set_stage1()
            lr = self.lr_stage1
        else:
            print("=== Stage 2: Instruction Tuning ===")
            self.model.set_stage2()
            lr = self.lr_stage2

        trainable_params = [p for p in self.model.parameters() if p.requires_grad]
        optimizer = AdamW(trainable_params, lr=lr, weight_decay=self.weight_decay)
        scheduler = CosineAnnealingLR(optimizer, T_max=epochs * len(loader))

        for epoch in range(epochs):
            epoch_loss = 0.0
            t0 = time.time()

            for step, batch in enumerate(loader):
                images = batch["images"].to(self.device)
                input_ids = batch["input_ids"].to(self.device)
                labels = batch["labels"].to(self.device)

                out = self.model(images, input_ids, labels)
                loss = out["loss"]

                optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(
                    [p for p in self.model.parameters() if p.requires_grad],
                    self.grad_clip
                )
                optimizer.step()
                scheduler.step()

                epoch_loss += loss.item()

                if (step + 1) % self.log_every == 0:
                    avg = epoch_loss / (step + 1)
                    print(f"  Stage {stage} | Epoch {epoch+1} | Step {step+1} | "
                          f"loss={avg:.4f}")

            elapsed = time.time() - t0
            print(f"  Stage {stage} Epoch {epoch+1} done in {elapsed:.1f}s | "
                  f"avg loss={epoch_loss/len(loader):.4f}")

    def train(
        self,
        stage1_loader: DataLoader,
        stage2_loader: DataLoader,
        stage1_epochs: int = 1,
        stage2_epochs: int = 3,
    ):
        """Full two-stage training pipeline."""
        self.run_stage(1, stage1_loader, stage1_epochs)
        self.run_stage(2, stage2_loader, stage2_epochs)
        print("Training complete.")
