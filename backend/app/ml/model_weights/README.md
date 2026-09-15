# Model Weights & Local Checkpoints (`backend/app/ml/model_weights`)

## 1. Overview
The `model_weights` directory is reserved for storing local fine-tuned machine learning checkpoints, transformer weights, and tokenizer vocabularies.

In air-gapped sovereign environments (such as Indian refinery control networks and CPSE on-premise servers), models cannot make outbound HTTP calls to Hugging Face or public clouds. Storing weights locally guarantees zero external dependencies and air-gapped deployment readiness.

---

## 2. Expected Directory Structure

When custom models are trained using `train_biencoder.py` or `train_ner.py`, checkpoints are saved in this directory:

```
backend/app/ml/model_weights/
|-- bi_encoder/                  # Fine-tuned Sentence-Transformers checkpoint
|   |-- config.json              # Transformer architecture configuration
|   |-- model.safetensors        # Dense embedding neural weights
|   |-- tokenizer.json           # Fast tokenization dictionary
|   |-- tokenizer_config.json    # Special tokens and padding rules
|   `-- vocab.txt                # Vocabulary list
|-- ner_model/                   # Token classification checkpoint (if exported)
`-- README.md                    # This file
```

---

## 3. Fallback Behavior When Weights Are Not Downloaded

To ensure immediate, frictionless setup for new developers without requiring gigabytes of model downloads:
- `vector_search.py` detects if local weights are present.
- If no custom transformer weights are found in this directory, the system automatically uses **Fast Deterministic Feature Embeddings**.
- This fallback computes dense representations based on physical attribute tokens and standardized n-grams, executing searches in under 15ms with zero model download overhead.
