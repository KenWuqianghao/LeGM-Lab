---
paths:
  - "models/**"
  - "training/**"
  - "experiments/**"
  - "data/**"
  - "**/train*.py"
  - "**/eval*.py"
  - "**/dataset*.py"
---

# ML Rules

- Always set random seeds (random, numpy, torch, CUDA) at the top of training scripts.
- Log all hyperparameters to W&B or MLflow before training starts.
- Save model checkpoints with optimizer state and epoch number.
- Use `model.eval()` + `torch.no_grad()` for all inference/evaluation code.
- Handle device placement explicitly — never assume CUDA is available.
- Use mixed precision (`torch.autocast` + `GradScaler`) for training when possible.
- Data splits: split BEFORE any preprocessing. Use fixed random seed for splits.
- HuggingFace: always set `tokenizer.pad_token` if model doesn't have one.
- Never evaluate on training data. Keep test set for final evaluation only.
- Config files (YAML/JSON) for all experiment hyperparameters — no magic numbers in code.
