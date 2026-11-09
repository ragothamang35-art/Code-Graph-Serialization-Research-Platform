# GraphTrust Reproducibility Guide

## Hardware & Environment Specifications
- **Python**: 3.10+
- **Inference Runtime**: llama-cpp-python or Gemini API server proxy
- **Base Model**: Gemma 4 E2B (4-bit quantized GGUF)
- **Decoding Configuration**: Temperature = 0.0, Top-p = 1.0, Repetition Penalty = 1.0

## Reproduction Commands

### 1. Inspect Dataset
```bash
python -m graphtrust.cli inspect --data-dir graphtrust/data/processed
```

### 2. Validate Controlled Invariants
```bash
python -m graphtrust.cli validate --data-dir graphtrust/data/processed
```

### 3. Run Pilot Smoke Test (3 tasks)
```bash
python -m graphtrust.cli run --data-dir graphtrust/data/processed --limit 3 --budget 2048
```

### 4. Run Full Primary Experiment
```bash
python -m graphtrust.cli run --data-dir graphtrust/data/processed --budget 2048
```

### 5. Run Ablation Suite
```bash
python -m graphtrust.cli ablate --data-dir graphtrust/data/processed
```

### 6. Run Unit Test Suite
```bash
python3 graphtrust/tests/test_all.py
```
