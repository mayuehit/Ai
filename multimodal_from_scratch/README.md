# Build a Multimodal Model from Scratch

仿照《Build a Large Language Model from Scratch》(Sebastian Raschka)，
从零实现一个完整的视觉-语言模型 (VLM)。

## 整体架构

```
图像 → ViT 编码器 ──→ Projection MLP ──┐
                                        ├──→ GPT 解码器 ──→ 文本
文本 → Token 嵌入 ──────────────────────┘
```

## 章节目录

| 章节 | 主题 | 核心概念 |
|------|------|----------|
| Ch 01 | Vision Transformer (ViT) | Patch Embedding、双向注意力、[CLS] token |
| Ch 02 | GPT 文本解码器 | 因果注意力、自回归生成、权重绑定 |
| Ch 03 | CLIP 对比学习 | InfoNCE loss、零样本分类 |
| Ch 04 | Vision-Language Model | 投影 MLP、视觉前缀、两阶段训练 |
| Ch 05 | 预训练 & 微调 | 特征对齐、指令微调、检查点 |

## 快速开始

```bash
pip install -r requirements.txt
cd notebooks
jupyter notebook
```

## 文件结构

```
multimodal_from_scratch/
├── vision/
│   ├── patch_embedding.py   # Patch 提取 + 位置编码
│   ├── attention.py         # 双向多头自注意力
│   └── vit.py               # 完整 ViT 模型
├── language/
│   ├── attention.py         # 因果多头自注意力
│   ├── transformer.py       # Transformer 解码器块
│   └── gpt.py               # 完整 GPT 模型
├── multimodal/
│   ├── clip.py              # CLIP 双编码器
│   ├── projection.py        # 视觉→语言投影 MLP
│   └── vlm.py               # 完整 VLM (LLaVA 风格)
├── training/
│   ├── losses.py            # InfoNCE loss、LM loss
│   └── trainer.py           # CLIP 训练器、VLM 两阶段训练器
├── data/
│   ├── dataset.py           # ImageTextDataset、VQADataset
│   └── transforms.py        # 图像预处理
└── notebooks/
    ├── ch01_vision_transformer.ipynb
    ├── ch02_gpt_decoder.ipynb
    ├── ch03_clip.ipynb
    ├── ch04_vlm.ipynb
    └── ch05_training.ipynb
```

## 与 LLM from Scratch 的对比

| | LLM from Scratch | **Multimodal from Scratch** |
|--|--|--|
| 核心模型 | GPT | ViT + GPT + Projection |
| 模态 | 文本 | 图像 + 文本 |
| 预训练目标 | 下一词预测 | 对比学习 (CLIP) |
| 微调方式 | 指令微调 | 两阶段：对齐 → 视觉指令 |
| 代表模型 | GPT-2 | LLaVA-1.5 |

## 参考文献

- [An Image is Worth 16x16 Words](https://arxiv.org/abs/2010.11929) — ViT
- [Learning Transferable Visual Models From Natural Language Supervision](https://arxiv.org/abs/2103.00020) — CLIP
- [Visual Instruction Tuning](https://arxiv.org/abs/2304.08485) — LLaVA
- [Improved Baselines with Visual Instruction Tuning](https://arxiv.org/abs/2310.03744) — LLaVA-1.5
