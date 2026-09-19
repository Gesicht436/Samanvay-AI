# Neural Reranking & Subvector Explainability (`ml/ranking/`)

This directory implements the multi-stage reranking and feature attribution pipeline that refines vector search candidates and explains matching confidence to human users.

---

## 1. File-by-File Breakdown

### `ranker.py` — Cross-Encoder Neural Reranker
- **Purpose:** Computes all-to-all cross-attention scores between requisition query and top-K vector search candidates.
- **Key Classes:**
  - `CompatibilityRanker`:
    - `rank_candidates(query_text: str, candidate_texts: List[str]) -> List[Tuple[int, float]]`: Takes query and top-K candidate descriptions, passes them through a Cross-Encoder transformer (`cross-encoder/ms-marco-MiniLM-L-6-v2`), and outputs softmax matching probabilities.
    - Fixes false positives from vector cosine similarity (e.g. distinguishing `150#` from `1500#` which embed close in vector space).

### `feature_extract.py` — Physical Subvector Decomposition
- **Purpose:** Decomposes overall similarity into 4 orthogonal engineering vectors for interpretable scoring.
- **Key Functions:**
  - `build_dimensional_vector(attrs)`: One-hot and scalar representation of diameter, wall thickness, length, and bore.
  - `build_metallurgy_vector(attrs)`: Material family, carbon content, corrosion resistance, and heat treatment.
  - `build_pressure_temp_vector(attrs)`: Working pressure, test pressure, min/max design temperatures.
  - `build_standards_vector(attrs)`: ASME, ASTM, API, ISO, and NACE compliance flags.
  - `compute_subvector_cosines(query_attrs, candidate_attrs) -> Dict[str, float]`: Computes individual cosine similarities across each domain:
    - `sim_dimensions`
    - `sim_metallurgy`
    - `sim_pressure_temp`
    - `sim_standards`

### `explainer.py` — SHAP-Style Feature Attribution
- **Purpose:** Generates human-understandable visual explanations for why an item was ranked first.
- **Key Classes:**
  - `ShapExplainer`:
    - `explain_prediction(features_dict) -> Dict[str, float]`: Uses Kernel SHAP to compute Shapley values $\phi_i$ indicating the positive or negative contribution of each physical feature to the final match score.

---

## 2. Theory: Cooperative Game Theory & Shapley Values

Shapley values originate from cooperative game theory. In the context of Samanvay-AI:
$$\phi_i = \sum_{S \subseteq F \setminus \{i\}} \frac{|S|!(|F| - |S| - 1)!}{|F|!} \left[ f(S \cup \{i\}) - f(S) \right]$$
- $F$ is the set of all physical attributes (size, class, metallurgy, facing, trim).
- $\phi_i$ measures the marginal contribution of attribute $i$ across all possible feature coalitions.
- If an item scores $92\%$ overall, the explainer can state:
  - *Size match contributed $+35\%$*
  - *Metallurgy match contributed $+30\%$*
  - *Pressure class upgrade contributed $+20\%$*
  - *Trim minor difference contributed $-3\%$*

---

## 3. Code Example

```python
from ml.ranking.ranker import CompatibilityRanker
from ml.ranking.feature_extract import compute_subvector_cosines
from ml.ranking.explainer import ShapExplainer

query = "PIPE 6 INCH SCH 40 ASTM A106 GR B SEAMLESS"
candidates = [
    "PIPE 6 INCH SCH 80 ASTM A106 GR B SEAMLESS",
    "VALVE GATE 6 INCH 150# ASTM A216 WCB"
]

# 1. Neural Cross-Encoder Reranking
ranker = CompatibilityRanker()
ranked = ranker.rank_candidates(query, candidates)
print("Top match index:", ranked[0][0], "Score:", ranked[0][1])

# 2. Subvector breakdown
cosines = compute_subvector_cosines(
    query_attrs={"size": "6 INCH", "schedule": "SCH 40", "material": "A106-B"},
    candidate_attrs={"size": "6 INCH", "schedule": "SCH 80", "material": "A106-B"}
)
print("Subvector Cosines:", cosines)
```
