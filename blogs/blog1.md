---
title: "Getting Started with Vision Transformers in PyTorch"
date: "March 10, 2026"
excerpt: "A practical introduction to ViT architecture and how to implement it from scratch using PyTorch, with examples on image classification tasks."
---

## Introduction

Vision Transformers (ViT) have revolutionized computer vision by applying the transformer architecture — originally designed for NLP — directly to image patches.

In this post, I'll walk through building a simple ViT from scratch in PyTorch.

## What is a Vision Transformer?

A ViT splits an image into fixed-size patches, linearly embeds each patch, adds positional encodings, and feeds the sequence into a standard transformer encoder.

```python
import torch
import torch.nn as nn

class PatchEmbedding(nn.Module):
    def __init__(self, img_size=224, patch_size=16, in_channels=3, embed_dim=768):
        super().__init__()
        self.proj = nn.Conv2d(in_channels, embed_dim, 
                              kernel_size=patch_size, stride=patch_size)
    
    def forward(self, x):
        x = self.proj(x)           # (B, embed_dim, H/P, W/P)
        x = x.flatten(2)           # (B, embed_dim, N)
        x = x.transpose(1, 2)      # (B, N, embed_dim)
        return x
```

## Training Tips

- Use a pretrained backbone when possible (ViT-B/16 from ImageNet)
- Warmup the learning rate for the first few epochs
- Data augmentation is crucial — RandAugment works well

## Conclusion

ViTs are powerful but data-hungry. For small datasets, consider adapter fine-tuning rather than full training.
