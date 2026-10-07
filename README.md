# 🌤️ Delhi Urban Weather Dynamics (1996–2026): Time-Series Analysis

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: CC0](https://img.shields.io/badge/License-CC0-lightgrey.svg)](https://creativecommons.org/publicdomain/zero/1.0/)
[![Milestone](https://img.shields.io/badge/Phase-Milestone%201%20(Synopsis)-success.svg)]()

A comprehensive **Time-Series Analysis & Exploratory Data Analysis (EDA)** project investigating meteorological dynamics in **Delhi, India (1 January 1996 to 18 March 2026)**.

---

## 📌 1. Project Overview & Domain Context

- **Domain**: Climate & Environmental Science / Urban Meteorology
- **Course**: Time Series Analysis & Forecasting
- **Milestone 1 Scope**: Problem formulation, dataset curation, quality audit, and exploratory analysis (trend, annual seasonality, and LOESS STL decomposition).
- **Evaluation Rule Compliance**: *No forecasting models are implemented during the Synopsis (Phase 1) evaluation.*

### 🎯 Problem Statement
> *How do temperature, precipitation, and atmospheric variables in Delhi evolve across seasonal and multi-decadal horizons (1996–2026), and what empirical properties govern the choice of future forecasting models in subsequent phases?*

### 👥 Target Stakeholders & Decisions Supported
1. **Power Utilities**: Quantifying summer heatwave intensity to plan peak electricity grid resourcing.
2. **Municipal & Disaster Planners**: Analyzing concentrated monsoon precipitation for urban stormwater and drainage planning.
3. **Agronomy & Agriculture**: Tracking seasonal onset and temperature patterns affecting Northern Indian crop cycles.
4. **Public Health Authorities**: Formulating early warning advisories for extreme heatwaves and severe winter cold snaps.

---

## 📊 2. Dataset Description

- **Source**: Kaggle Indian Weather Dataset 1996–2026 (`sandeepgupta09/indian-weather-dataset-1996-2026`)
- **License**: CC0: Public Domain (verified on Kaggle dataset page)
- **Coverage**: Over 30 years of historical observations, from 1 January 1996 to 18 March 2026
- **Frequency**: Regular hourly observations
- **Volume**: 264,840 hourly observations aggregated to 11,035 daily points (far exceeding the $\ge 500$ requirement)
- **Data Quality**: 0 duplicate timestamps, 0 missing timestamps, 100% temporal continuity

### Data Dictionary

| Variable | Column Name | Unit | Type | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Timestamp** | `datetime` | ISO-8601 | Datetime | Regular hourly observation time index |
| **Temperature** | `temperature_C` | °C | Float | Ambient air temperature at 2m height |
| **Precipitation** | `precip_mm` | mm | Float | Cumulative rainfall |
| **Relative Humidity**| `humidity_pct` | % | Float | Atmospheric relative moisture percentage |
| **Pressure** | `pressure_hPa` | hPa | Float | Barometric air pressure at sea level |
| **Wind Speed** | `wind_speed_ms` | m/s | Float | Horizontal wind velocity |

---

## 🔍 3. Milestone 1 Exploratory Visualizations & Findings

All figures are generated in `milestone1_output/figures/`:

1. **Trend & 30-Day Moving Average (`01_trend_ma.png`)**: Multi-decadal temperature fluctuations with a 30-day centered moving average (exploratory visual smoothing aid only; no prediction).
2. **Data Quality & Coverage Audit (`02_missing_audit.png`)**: Full audit verifying 264,840 hourly points, 0 duplicate timestamps, and complete monthly coverage over time.
3. **Climate Fingerprint Envelope (`03_climate_fingerprint.png`)**: Monthly thermal envelope (mean, max, min) with monthly rainfall profile. Hottest month: **June (32.8°C)**, Coldest month: **January (12.9°C)**, Annual swing: **~19.9°C**.
4. **Year × Month Thermal Matrix (`04_thermal_heatmap.png`)**: Two-dimensional heatmap demonstrating stable annual seasonality across all years.
5. **LOESS STL Decomposition (`05_stl_decomposition.png`)**: Additive component separation ($Period = 365\text{ days}$) isolating seasonal strength ($F_s = 0.936$), trend strength ($F_t = 0.082$), and residual variation ($\sigma_R = 1.79^\circ\text{C}$).
6. **Seasonal Boxplots (`06_seasonal_boxplot.png`)**: Empirical temperature distributions across Winter, Summer, Monsoon, and Post-Monsoon.
7. **Temperature vs. Precipitation (`07_temp_vs_rain.png`)**: Scatter plots contrasting raw association vs. deseasonalized temperature anomaly ($\rho = -0.21$).

---

## 🔬 4. Review of Existing Systems & Feasibility (Rubric Criterion)

| Approach | Key Characteristics | Typical Limitations | Project Direction |
| :--- | :--- | :--- | :--- |
| **Numerical Weather Prediction (NWP)** | Physics-based fluid dynamics | Heavy supercomputing overhead; physical grid tuning | Benchmark context; out of scope for time series |
| **Classical Statistical (ARIMA / SARIMA)** | Linear autoregressive modeling | Assumes linearity; limited with complex non-linear patterns | Planned Phase 2 baseline models |
| **Holt-Winters Exponential Smoothing** | Triple exponential smoothing | Fixed linear smoothing parameters | Planned Phase 2 baseline comparison |
| **LOESS Seasonal Decomposition (STL)** | Non-parametric loess smoothing | Descriptive; requires separate forecasting mechanism | Phase 1 exploratory tool |
| **Machine Learning (XGBoost)** | Gradient boosted decision trees | Requires extensive manual lag/rolling feature engineering | Planned Phase 3 ensemble benchmark |
| **Deep Learning (LSTM) & Prophet** | Recurrent sequence & additive models | Heavier training compute; sequence length sensitivity | Planned Phase 3 advanced comparison |

### Technical Feasibility
- **Data Volume**: 11,035 daily points ($\ge 500$ requirement satisfied).
- **Tooling**: Pure Python stack using `pandas`, `matplotlib`, `seaborn`, and `statsmodels`.
- **Phase Alignment**: Feasible 3-phase execution matching course milestones.

---

## 🚀 5. Proposed Multi-Phase Roadmap

```mermaid
graph LR
    A[Milestone 1: Synopsis & EDA] --> B[Milestone 2: Classical Models]
    B --> C[Milestone 3: Advanced ML/DL & Evaluation]
    
    subgraph Milestone 1 (Completed)
        A1[Data Quality & Continuity Audit]
        A2[Climatological Envelope & Extremes]
        A3[LOESS STL Decomposition]
        A4[Existing Systems Review & Feasibility]
    end
    
    subgraph Milestone 2 (Mid-Sem)
        B1[Stationarity Checks: ADF & KPSS Tests]
        B2[ACF / PACF Parameter Diagnostics]
        B3[ARIMA, SARIMA & Holt-Winters Models]
        B4[Baseline Error Metrics: RMSE, MAE, MAPE]
    end
    
    subgraph Milestone 3 (Final)
        C1[XGBoost with Lag Features]
        C2[LSTM Neural Network]
        C3[Facebook Prophet]
        C4[Comparative Benchmark & Stakeholder Framework]
    end
```

### Model Selection Justification (Based on Phase 1 EDA)
- **Seasonal Models (SARIMA, Holt-Winters)**: Motivated by the strong annual seasonal pattern ($F_s = 0.936$).
- **XGBoost on Lag Features**: Motivated by zero-heavy, skewed monsoon precipitation distributions.
- **LSTM Networks**: Motivated by multivariable non-linear interactions across temperature, pressure, and humidity.

---

## 🛠️ 6. Quickstart & Execution

```bash
# 1. Clone & install dependencies
git clone https://github.com/dhruvsaini-code/weather-forecasting.git
cd weather-forecasting
pip install -r requirements.txt

# 2. Run the Milestone 1 Pipeline
python milestone1_pipeline.py
```

### Deliverables Generated
- `milestone1_output/Milestone1_Synopsis.pptx` (Exact 12-slide presentation with speaker notes)
- `milestone1_output/figures/*.png` (7 publication-grade EDA figures)
- `milestone1_output/stats.json` (Exact data-audit & EDA statistics)
- `milestone1_output/daily_series.csv` (Aggregated daily time series)

---

## 📚 7. Academic References

1. **Hyndman, R. J., & Athanasopoulos, G.** (2021). *Forecasting: Principles and Practice* (3rd ed.). OTexts.
2. **Box, G. E. P., Jenkins, G. M., Reinsel, G. C., & Ljung, G. M.** (2015). *Time Series Analysis: Forecasting and Control* (5th ed.). John Wiley & Sons.
3. **Cleveland, R. B., Cleveland, W. S., McRae, J. E., & Terpenning, I.** (1990). *STL: A Seasonal-Trend Decomposition Procedure Based on Loess*. Journal of Official Statistics, 6(1), 3–73.
4. **Taylor, S. J., & Letham, B.** (2018). *Forecasting at Scale*. The American Statistician, 72(1), 37–45.
5. **Hochreiter, S., & Schmidhuber, J.** (1997). *Long Short-Term Memory*. Neural Computation, 9(8), 1735–1780.
6. **Chen, T., & Guestrin, C.** (2016). *XGBoost: A Scalable Tree Boosting System*. ACM SIGKDD, 785–794.
7. **Bauer, P., Thorpe, A., & Brunet, G.** (2015). *The Quiet Revolution of Numerical Weather Prediction*. Nature, 525(7567), 47–55.
8. **Rasp, S. et al.** (2020). *WeatherBench: A Benchmark Data Set for Data-Driven Weather Forecasting*. JAMES, 12(11), e2020MS002203.
9. **Kaggle Dataset**: *Indian Weather Dataset (1996–2026)*, sandeepgupta09. License: CC0: Public Domain.
