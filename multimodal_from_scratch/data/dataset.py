"""
Chapter 5.3 — Datasets
========================
Two dataset classes:

1. ImageTextDataset  — (image, caption) pairs for CLIP pre-training
2. VQADataset        — (image, question, answer) for VLM instruction tuning

Format expected on disk:
  data/
    images/
      img_000001.jpg
      img_000002.jpg
      ...
    annotations.jsonl   ← one JSON object per line

  JSONL format for CLIP:
    {"image": "img_000001.jpg", "caption": "a cat sitting on a mat"}

  JSONL format for VQA:
    {"image": "img_000001.jpg",
     "conversations": [
       {"role": "user",    "content": "<image>\nWhat is the cat doing?"},
       {"role": "assistant","content": "The cat is sitting on a mat."}
     ]}
"""

import json
from pathlib import Path
from PIL import Image

import torch
from torch.utils.data import Dataset


class ImageTextDataset(Dataset):
    """
    Flat image-caption dataset for CLIP contrastive pre-training.
    Returns: {'images': tensor, 'input_ids': tensor, 'eos_positions': tensor}
    """

    def __init__(self, data_dir: str, tokenizer, transform=None, max_len: int = 77):
        self.data_dir = Path(data_dir)
        self.tokenizer = tokenizer
        self.transform = transform
        self.max_len = max_len

        with open(self.data_dir / "annotations.jsonl") as f:
            self.samples = [json.loads(line) for line in f]

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> dict:
        sample = self.samples[idx]

        # Load and preprocess image
        img_path = self.data_dir / "images" / sample["image"]
        image = Image.open(img_path).convert("RGB")
        if self.transform is not None:
            image = self.transform(image)

        # Tokenise caption
        tokens = self.tokenizer.encode(sample["caption"])
        tokens = tokens[:self.max_len]
        eos_pos = len(tokens) - 1

        # Pad to max_len
        padded = tokens + [0] * (self.max_len - len(tokens))

        return {
            "images": image,
            "input_ids": torch.tensor(padded, dtype=torch.long),
            "eos_positions": torch.tensor(eos_pos, dtype=torch.long),
        }


class VQADataset(Dataset):
    """
    Visual instruction-following dataset for VLM fine-tuning (Stage 2).

    Formats conversations as:
      USER: <image>\n{question}  ASSISTANT: {answer}

    The loss is computed only on the ASSISTANT part (labels for USER = -100).
    """

    def __init__(self, data_dir: str, tokenizer, transform=None,
                 max_len: int = 512,
                 user_token: str = "USER:",
                 asst_token: str = "ASSISTANT:"):
        self.data_dir = Path(data_dir)
        self.tokenizer = tokenizer
        self.transform = transform
        self.max_len = max_len
        self.user_token = user_token
        self.asst_token = asst_token

        with open(self.data_dir / "annotations.jsonl") as f:
            self.samples = [json.loads(line) for line in f]

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> dict:
        sample = self.samples[idx]

        # Load image
        img_path = self.data_dir / "images" / sample["image"]
        image = Image.open(img_path).convert("RGB")
        if self.transform is not None:
            image = self.transform(image)

        # Build conversation text and labels
        input_ids = []
        labels = []

        for turn in sample["conversations"]:
            text = turn["content"]
            tokens = self.tokenizer.encode(text)

            if turn["role"] == "user":
                # Ignore user tokens in loss
                input_ids.extend(tokens)
                labels.extend([-100] * len(tokens))
            else:
                # Compute loss on assistant tokens
                input_ids.extend(tokens)
                labels.extend(tokens)

        # Truncate
        input_ids = input_ids[:self.max_len]
        labels = labels[:self.max_len]

        # Pad
        pad_len = self.max_len - len(input_ids)
        input_ids = input_ids + [0] * pad_len
        labels = labels + [-100] * pad_len

        return {
            "images": image,
            "input_ids": torch.tensor(input_ids, dtype=torch.long),
            "labels": torch.tensor(labels, dtype=torch.long),
        }


def collate_fn(batch: list) -> dict:
    """Stack a list of sample dicts into a batched dict of tensors."""
    keys = batch[0].keys()
    return {k: torch.stack([s[k] for s in batch]) for k in keys}
