---
title: "PyTorch Deep Learning — Complete Tutorial"
date: "March 22, 2026"
excerpt: "Every concept from tensors to transformers — with working code, diagrams, formulas, and notes."
---

# 📘 PyTorch Deep Learning — Complete Tutorial

> Every concept from tensors to transformers — with working code, diagrams, formulas, and notes.

---

## 📑 Table of Contents

1. Tensors & Operations  
2. Autograd & Backpropagation  
3. nn.Module  
4. Optimizers  
5. Loss Functions  
6. Data Pipeline  

---

# 🧠 Chapter 1 — Tensors & Operations

## Creating Tensors

```python
import torch
import numpy as np

t1 = torch.tensor([1.0, 2.0, 3.0])

zeros = torch.zeros(3, 4)
ones  = torch.ones(2, 3)
rand  = torch.rand(2, 3)
randn = torch.randn(2, 3)

arr = np.array([1, 2, 3])
t2  = torch.from_numpy(arr)

t3 = torch.arange(0, 10, 2)
t4 = torch.linspace(0, 1, 5)
```

---

## Shape Manipulation

```python
x = torch.randn(2, 3, 4)
y = x.view(6, 4)
z = x.reshape(6, 4)
```

---

## Math Operations

```python
a = torch.tensor([[1.,2.],[3.,4.]])
b = torch.tensor([[5.,6.],[7.,8.]])

c = a + b
mm = torch.matmul(a, b)
```

---

# 🔁 Chapter 2 — Autograd

```python
import torch

x = torch.tensor([2.0], requires_grad=True)
y = torch.tensor([3.0], requires_grad=True)

z = x**2 + y * x
z.backward()

print(x.grad)
print(y.grad)
```

---

# 🧩 Chapter 3 — nn.Module

```python
import torch.nn as nn
import torch.nn.functional as F

class MLP(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(784, 256)
        self.fc2 = nn.Linear(256, 10)

    def forward(self, x):
        x = F.relu(self.fc1(x))
        return self.fc2(x)
```

---

# ⚙️ Chapter 4 — Optimizers

```python
import torch.optim as optim

optimizer = optim.Adam(model.parameters(), lr=1e-3)
```

---

# 📉 Chapter 5 — Loss Functions

```python
import torch.nn as nn

loss = nn.CrossEntropyLoss()
```

---

# 📦 Chapter 6 — Dataset

```python
from torch.utils.data import Dataset

class MyDataset(Dataset):
    def __init__(self, data):
        self.data = data

    def __getitem__(self, idx):
        return self.data[idx]
```

---

# 🎯 Notes

- PyTorch is dynamic and flexible
- Used in AI, CV, NLP
