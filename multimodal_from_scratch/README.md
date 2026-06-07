# Build a Multimodal Model from Scratch

A chapter-by-chapter guide to building multimodal AI systems from the ground up,
modeled after Sebastian Raschka's *Build a Large Language Model from Scratch*.

Every model component is implemented inside the notebook cells — no black
boxes, no pre-built libraries for the core algorithms.

---

## Prerequisites

This book assumes you have read *Build a Large Language Model from Scratch*
and are comfortable with Transformers, multi-head attention, and GPT-style
autoregressive generation.  Those concepts are not re-explained here.

---

## Chapters

### Part I — Vision & Cross-Modal Alignment

| Chapter | Topic | Key Concepts |
|---------|-------|--------------|
| **Ch 01** | Vision Transformer (ViT) | PatchEmbedding (Conv2d trick), bidirectional attention, [CLS] token, learnable positional embeddings |
| **Ch 02** | CLIP | InfoNCE contrastive loss, dual encoder, learnable temperature τ, zero-shot classification |
| **Ch 03** | VLM Architecture | ProjectionMLP (semantic gap bridge), visual prefix, hybrid attention mask, loss masking |
| **Ch 04** | Training & Evaluation | Two-stage training, feature alignment, instruction fine-tuning, BLEU, perplexity, ablation |

### Part II — Self-Supervised & Generative Vision

| Chapter | Topic | Key Concepts |
|---------|-------|--------------|
| **Ch 05** | Masked Autoencoder (MAE) | Masked patch reconstruction, asymmetric encoder-decoder, self-supervised pre-training |
| **Ch 06** | Image Tokenization (VQ-VAE) | Vector quantization, discrete codebook, straight-through estimator, latent image tokens |
| **Ch 07** | Diffusion Models (DDPM) | Forward/reverse process, noise schedule, ε-prediction, U-Net, classifier-free guidance |

### Part III — Beyond Images

| Chapter | Topic | Key Concepts |
|---------|-------|--------------|
| **Ch 08** | Audio Understanding | Mel spectrogram, audio patch embedding, Whisper-style encoder-decoder, speech recognition |
| **Ch 09** | Video Understanding | Spatio-temporal patches, factorized attention, video classification, temporal modeling |

### Part IV — Alignment & Reinforcement Learning

| Chapter | Topic | Key Concepts |
|---------|-------|--------------|
| **Ch 10** | Unified Multimodal Model | Image + audio + text capstone, multi-encoder VLM, two-stage assembly |
| **Ch 11** | Reward Modeling | Bradley-Terry preference model, pairwise ranking loss, reward distribution, RLHF pipeline |
| **Ch 12** | DPO & GRPO | Direct Preference Optimization, log-ratio loss, Group Relative Policy Optimization, verifier-based reward |

---

## Quick Start

```bash
pip install -r requirements.txt
cd notebooks
jupyter notebook
```

Each notebook is fully self-contained — figures are generated inline with
matplotlib, and all model classes are defined within the notebook cells.

---

## Repository Layout

```
multimodal_from_scratch/
├── notebooks/
│   ├── ch01_vision_transformer.ipynb
│   ├── ch02_clip.ipynb
│   ├── ch03_vlm_architecture.ipynb
│   ├── ch04_two_stage_training.ipynb
│   ├── ch05_mae.ipynb
│   ├── ch06_vqvae.ipynb
│   ├── ch07_diffusion.ipynb
│   ├── ch08_audio.ipynb
│   ├── ch09_video.ipynb
│   ├── ch10_capstone.ipynb
│   ├── ch11_reward_modeling.ipynb
│   └── ch12_dpo_grpo.ipynb
└── requirements.txt
```

---

## How It Relates to *LLMs from Scratch*

| | LLMs from Scratch | **Multimodal from Scratch** |
|--|--|--|
| Core model | GPT | ViT + ProjectionMLP + GPT |
| Modalities | Text only | Image, Audio, Video + Text |
| Pre-training | Next-token prediction | Contrastive (CLIP) + Reconstruction (MAE) |
| Generation | Autoregressive text | Diffusion (images) + VQ-VAE (discrete tokens) |
| Alignment | — | Reward Modeling + DPO + GRPO |
| Representative models | GPT-2 | LLaVA, Whisper, ViViT, DeepSeek-R1 |

---

## References

- [An Image is Worth 16×16 Words](https://arxiv.org/abs/2010.11929) — ViT
- [Learning Transferable Visual Models From Natural Language Supervision](https://arxiv.org/abs/2103.00020) — CLIP
- [Visual Instruction Tuning](https://arxiv.org/abs/2304.08485) — LLaVA
- [Masked Autoencoders Are Scalable Vision Learners](https://arxiv.org/abs/2111.06377) — MAE
- [Neural Discrete Representation Learning](https://arxiv.org/abs/1711.00937) — VQ-VAE
- [Denoising Diffusion Probabilistic Models](https://arxiv.org/abs/2006.11239) — DDPM
- [High-Resolution Image Synthesis with Latent Diffusion Models](https://arxiv.org/abs/2112.10752) — Stable Diffusion
- [Robust Speech Recognition via Large-Scale Weak Supervision](https://arxiv.org/abs/2212.04356) — Whisper
- [ViViT: A Video Vision Transformer](https://arxiv.org/abs/2103.15691) — Video ViT
- [Training Language Models to Follow Instructions with Human Feedback](https://arxiv.org/abs/2203.02155) — InstructGPT / RLHF
- [Direct Preference Optimization: Your Language Model is Secretly a Reward Model](https://arxiv.org/abs/2305.18290) — DPO
- [DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models](https://arxiv.org/abs/2402.03300) — GRPO
