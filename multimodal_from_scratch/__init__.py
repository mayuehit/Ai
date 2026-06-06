"""
Build a Multimodal Model from Scratch
======================================
A step-by-step implementation of a Vision-Language Model (VLM),
inspired by "Build a Large Language Model from Scratch" by Sebastian Raschka.

Architecture overview:
  Image → PatchEmbedding → ViT Encoder ──┐
                                          ├─→ Projection → VLM Decoder → Text
  Text  → TokenEmbedding → GPT Decoder ──┘

Chapters:
  Ch01: Vision Transformer (ViT)
  Ch02: GPT-style Text Decoder
  Ch03: CLIP (Contrastive Language-Image Pre-training)
  Ch04: Vision-Language Model (VLM)
  Ch05: Pre-training & Fine-tuning
"""
