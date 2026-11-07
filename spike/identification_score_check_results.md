# Identification Strength next to the DiD's actual bias

From `spike/identification_score_check.py`: 200 worlds per row, default design, true effect -0.50.

| Scenario | Mean score | Share of worlds at 80 or more | Mean bias | Bias as a share of the effect |
|---|---|---|---|---|
| no threat | 91.5 | 96% | +0.001 | 0% |
| diverging pre-trends, low | 89.7 | 92% | +0.241 | 48% |
| diverging pre-trends, medium | 84.1 | 86% | +0.561 | 112% |
| confounding, high | 91.7 | 92% | +0.106 | 21% |
| confounding, severe | 91.8 | 96% | +0.239 | 48% |
| diverging pre-trends, severe | 72.5 | 66% | +1.601 | 320% |
