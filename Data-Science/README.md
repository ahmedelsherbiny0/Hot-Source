# Trend Detective: Scientific Data Science & Statistical Engine

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Tests: Pytest](https://img.shields.io/badge/tests-7%20passed-brightgreen.svg)](https://docs.pytest.org/)

The **Data Science** module of *Trend Detective* implements rigorous non-parametric statistical trend detection, autocorrelation correction, outlier shields, and silent physical driver attribution for multi-decadal NASA Earth Observation datasets.

---

## 1. Directory Structure

```text
Data-Science/
├── README.md                          # Scientific methodology and mathematical reference
├── setup.py                           # Installable Python package specification
├── requirements.txt                   # Scientific compute dependencies
├── trend_detective/                   # Core statistical and data access library
│   ├── __init__.py                    # Public API exports
│   ├── trend_engine.py                # Hamed-Rao MK, Theil-Sen, Hyperbolic CI, MAD, FDR
│   ├── driver_attribution.py          # Physical driver pairing and anomaly cross-correlation
│   └── source_router.py               # Geophysical climate models, QA filtering, and routing
├── benchmarks/                        # Benchmark evaluation and reproducibility CLI tools
│   └── evaluate_benchmarks.py         # Multi-region testbed scanner with FDR correction
└── tests/                             # Mathematical and algorithmic unit tests
    └── test_statistical_engine.py     # Rigorous test suite for statistical theorems
```

---

## 2. Mathematical & Algorithmic Methodology

### A. Climatology & Deseasonalized Anomalies
Raw Earth observation series $X_{y,m}$ exhibit strong intra-annual seasonal cycles. Climatological calendar-month means $\bar{C}_m$ and deseasonalized anomalies $A_{y,m}$ are computed via:

$$\bar{C}_m = \frac{1}{Y} \sum_{y=1}^{Y} X_{y,m}, \quad m \in \{1, 2, \dots, 12\}$$

$$A_{y,m} = X_{y,m} - \bar{C}_m$$

This satisfies conservation of mass: $\sum_{y,m} A_{y,m} = 0$.

### B. Autocorrelation & Hamed-Rao Modified Mann-Kendall
Climate and hydrological observations frequently exhibit red noise (positive serial autocorrelation). When lag-1 autocorrelation $r_1 > 0.20$, standard Mann-Kendall inflates Type I errors. The engine promotes the test to the **Hamed-Rao Modified Mann-Kendall test**:

$$r_1 = \frac{\sum_{t=1}^{N-1} (A_t - \bar{A})(A_{t+1} - \bar{A})}{\sum_{t=1}^{N} (A_t - \bar{A})^2}$$

The variance $V(S)$ of the Mann-Kendall $S$ statistic is corrected by variance inflation factor $\eta$:

$$V^*(S) = \eta \cdot V(S) = \left[ 1 + \frac{2}{n(n-1)(n-2)} \sum_{k=1}^{n-1} (n-k)(n-k-1)(n-k-2) \rho^*(k) \right] V(S)$$

### C. Theil-Sen Robust Slope Estimator
The non-parametric median slope $\beta_{\text{Sen}}$ protects against catastrophic outlier distortion:

$$\beta_{\text{Sen}} = \text{Median} \left\{ \frac{A_j - A_i}{t_j - t_i} \right\} \quad \forall \ 1 \le i < j \le n$$

Cumulative change over the full observation period $\Delta T = t_n - t_1$ is:

$$\Delta_{\text{cumulative}} = \beta_{\text{Sen}} \times \Delta T$$

### D. True Hyperbolic 95% Confidence Bounds (Working-Hotelling)
Standard parallel error bounds understate parameter uncertainty at record boundaries. The engine calculates exact hyperbolic confidence intervals:

$$\hat{y}(x_i) \pm t_{1 - \alpha/2, \ n-2} \cdot s_e \sqrt{\frac{1}{n} + \frac{(x_i - \bar{x})^2}{\sum_{k=1}^n (x_k - \bar{x})^2}}$$

Where $s_e = \sqrt{\frac{\sum (y_i - \hat{y}_i)^2}{n - 2}}$. The envelope is narrowest at centroid $\bar{x}$ and naturally widens at boundary years.

### E. Median Absolute Deviation (MAD) Outlier Shield
Episodic events (such as the 2011 and 2019 Midwest flood pulses) trigger outlier shields using Boris Iglewicz and David Hoaglin's Modified $Z$-score:

$$\text{MAD} = \text{Median} \left( |A_i - \text{Median}(A)| \right)$$

$$M_i = \frac{0.6745 \cdot (A_i - \text{Median}(A))}{\text{MAD}}$$

Points with $|M_i| > 3.0$ are classified as episodic outliers. If the OLS slope diverges from Sen's slope by $>30\%$, an automated skew warning is flagged.

### F. Vectorized Benjamini-Hochberg False Discovery Rate (FDR)
When testing $m$ regions simultaneously, family-wise false discoveries are bounded at rate $\alpha = 0.05$ using step-up rank ordering:

$$P_{(1)} \le P_{(2)} \le \dots \le P_{(m)}$$

$$k = \max \left\{ i : P_{(i)} \le \frac{i}{m} Q \right\}$$

Adjusted $p$-values are computed via cumulative minimum reverse sorting:

$$p_i^{\text{adj}} = \min_{k \ge i} \left( \min \left( 1, \frac{m}{k} P_{(k)} \right) \right)$$

### G. Silent Physical Driver Attribution
To eliminate spurious attribution, the engine pairs primary variables with independent physically coupled Earth system drivers:

| Primary Variable | Paired Physical Driver | Coupling Mechanism | Expected Sign |
| :--- | :--- | :--- | :--- |
| **Evapotranspiration** | **Precipitation** | Soil moisture supply control | Positive ($r > 0$) |
| **Soil Moisture** | **Precipitation** | Direct infiltration recharge | Positive ($r > 0$) |
| **Surface Runoff** | **Precipitation** | Overland catchment discharge | Positive ($r > 0$) |
| **Surface Temperature** | **Evapotranspiration** | Evaporative cooling / Bowen ratio | Negative ($r < 0$) |
| **Chlorophyll-a** | **Precipitation** | Agricultural & urban nutrient runoff | Positive ($r > 0$) |

Coupling classification:
- **Strong**: $|r| \ge 0.50$ ($p < 0.05$)
- **Moderate**: $0.25 \le |r| < 0.50$ ($p < 0.05$)
- **Weak**: $|r| < 0.25$ or $p \ge 0.05$ (explicitly avoids Type II confirmation fallacy).

---

## 3. Quickstart & Installation

```bash
# 1. Install in editable development mode
pip install -e Data-Science/

# 2. Run the mathematical unit test suite
pytest Data-Science/tests/ -v

# 3. Evaluate multi-region benchmarks CLI
python Data-Science/benchmarks/evaluate_benchmarks.py
```

---

## 4. Benchmark Validation Results

Running `evaluate_benchmarks.py` produces the following verified testbed assessment:

```text
Region                     Variable       Sen Slope    Raw p     FDR p     FDR Status Driver Coupling
---------------------------------------------------------------------------------------------------------
Kansas Plains (USA)        surface_temp   +0.0244 °C/yr 0.0000    0.0000    SIGNIFICANT Moderate (r=+0.28)
Arizona Desert (USA)       surface_temp   +0.0464 °C/yr 0.0000    0.0000    SIGNIFICANT Moderate (r=+0.42)
Pearl River Outflow (China) chlorophyll_a  +0.2802 mg/m³/yr 0.0000    0.0000    SIGNIFICANT Weak (r=+0.18) 
Mississippi River West (USA) chlorophyll_a  +0.2813 mg/m³/yr 0.0000    0.0000    SIGNIFICANT Weak (r=+0.21) 
Nile Delta (Egypt)         surface_temp   +0.0282 °C/yr 0.0000    0.0000    SIGNIFICANT Moderate (r=+0.36)
---------------------------------------------------------------------------------------------------------
Total Evaluated: 5 | FDR Significance Rate: 5/5 Verified Significant
```
