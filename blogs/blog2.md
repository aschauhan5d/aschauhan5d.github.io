---
title: "LoRA Fine-Tuning: A Beginner's Guide"
date: "February 22, 2026"
excerpt: "Low-Rank Adaptation (LoRA) lets you fine-tune large models with very few trainable parameters. Here's how I applied it to medical imaging."
---

## What is LoRA?

Low-Rank Adaptation (LoRA) is a parameter-efficient fine-tuning technique. Instead of updating all model weights, it injects small trainable rank-decomposition matrices into each layer.

This means you can fine-tune a large model using a fraction of the compute and memory.

## Why I Used It

For my PhD research on 3D medical image segmentation, I needed to adapt a large pretrained ViT to MRI volumes — but with very limited GPU memory and labeled data.

LoRA was perfect: I kept the ViT backbone frozen and only trained the low-rank adapters.

```python
import loralib as lora

# Replace a linear layer with a LoRA-enabled one
layer = lora.Linear(768, 768, r=16)  # r = rank

# Only mark LoRA params as trainable
lora.mark_only_lora_as_trainable(model)

# Count trainable params
trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
print(f"Trainable parameters: {trainable:,}")
```

## Results

With rank r=16, I achieved comparable performance to full fine-tuning using only ~1% of the original trainable parameters.

## Conclusion

LoRA is an excellent choice when you have limited compute or data. Highly recommended for anyone working with large pretrained models.
