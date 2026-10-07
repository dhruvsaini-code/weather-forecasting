# 🌤️ Delhi Urban Weather Dynamics (1996–2026): Exploratory Time-Series Analysis

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Milestone](https://img.shields.io/badge/Project%20Phase-Milestone%201%20(Synopsis)-success.svg)]()

A rigorous, end-to-end **Time-Series Analysis & Exploratory Data Analysis (EDA)** project investigating 30 years of meteorological observations in **Delhi, India (1996–2026)**.

---

## 📌 1. Project Overview & Domain Context

- **Domain**: Climate & Environmental Science / Urban Meteorology
- **Course**: Time Series Analysis & Forecasting
- **Milestone 1 Scope**: Problem domain identification, dataset curation, quality auditing, exploratory time-series visualization (trend, seasonality, decomposition, extremes), and future methodology formulation.
- **Strict Compliance**: *No forecasting models or predictions are executed in Milestone 1 (per course evaluation rubrics).*

### 🎯 Problem Statement
> *How do temperature, precipitation, humidity, and atmospheric dynamics evolve over a 30-year span in Delhi across seasonal and multi-decadal scales, and what do these empirical properties imply for the design and selection of statistical, machine-learning, and deep-learning forecasting models in subsequent phases?*

### 👥 Stakeholders & Impact
1. **Power & Energy Utilities**: Quantifying summer heatwave intensity and temperature swings to plan peak load capacity and prevent grid failures.
2. **Urban & Disaster Management Agencies**: Identifying extreme monsoon precipitation anomalies for urban drainage and flood mitigation.
3. **Agriculture & Agronomy**: Tracking seasonal onset, monsoon duration, and temperature anomalies affecting crop cycles in northern India.
4. **Public Health Authorities**: Formulating early health advisories for extreme heatwaves and severe winter cold waves.

---

## 📊 2. Dataset Description

The analysis uses historical weather observations from the Kaggle repository:
- **Source**: Kaggle Indian Weather Dataset (1996–2026)
- **Geographical Scope**: Delhi, India
- **Temporal Index**: Timestamped (`datetime` UTC / IST), regular frequency
- **Time Period**: `1996-01-01` to `2026-03-31` (30 full years)
- **Observations**: >260,000 hourly observations aggregated to ~11,048 daily records (far exceeding the ≥500 observation threshold)

### Data Dictionary

| Variable | Column Name | Unit | Type | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Timestamp** | `datetime` | ISO-8601 | Datetime | Observation time index |
| **Temperature** | `temperature_C` | °C | Float | Ambient air temperature at 2m height |
| **Precipitation** | `precip_mm` | mm | Float | Cumulative rainfall |
| **Relative Humidity**| `humidity_pct` | % | Float | Atmospheric moisture content |
| **Pressure** | `pressure_hPa` | hPa | Float | Barometric air pressure at sea level |
| **Wind Speed** | `wind_speed_ms` | m/s | Float | Horizontal wind velocity |

---

## 🔍 3. Milestone 1 Exploratory Visualizations & Findings

All figures are automatically generated at high resolution in `milestone1_output/figures/`:

1. **Trend & 30-Day Moving Average (`01_trend_ma.png`)**: Visualizes multi-decadal temperature fluctuations and baseline warming trends smoothed with a 30-day centered moving average.
2. **Data Quality & Missingness Audit (`02_missing.png`)**: Quantifies timestamp gaps, duplicate records, and monthly data coverage across 30 years.
3. **Climate Fingerprint (`03_fingerprint.png`)**: Monthly envelope showing mean, daily max, and daily min temperatures alongside mean monthly rainfall.
4. **Year × Month Heatmap (`04_heatmap.png`)**: Two-dimensional thermal matrix highlighting recurring annual seasonality and inter-annual shifts.
5. **STL Decomposition (`05_decomposition.png`)**: Loess-based additive/multiplicative decomposition isolating **Observed = Trend + Seasonal + Residual** ($Period = 365\text{ days}$).
6. **Seasonal Boxplots (`06_boxplot.png`)**: Empirical temperature distributions across Winter, Summer, Monsoon, and Post-Monsoon seasons.
7. **Temperature vs. Rainfall (`07_temp_vs_rain.png`)**: Scatter plots comparing raw Spearman correlation vs. de-seasonalised temperature anomalies.

---

## 🚀 4. Proposed Multi-Phase Roadmap

```mermaid
graph LR
    A[Milestone 1: Synopsis & EDA] --> B[Milestone 2: Classical Models]
    B --> C[Milestone 3: Advanced ML/DL & Comparative Insights]
    
    subgraph Milestone 1 (Current)
        A1[Data Quality Audit]
        A2[Component Analysis]
        A3[STL Decomposition]
        A4[Feasibility Review]
    end
    
    subgraph Milestone 2 (Mid-Sem)
        B1[Stationarity & Differencing]
        B2[ARIMA & SARIMA]
        B3[Holt-Winters Exponential Smoothing]
        B4[Initial Error Metrics: RMSE, MAE, MAPE]
    end
    
    subgraph Milestone 3 (Final)
        C1[XGBoost with Lag Features]
        C2[LSTM / GRU Neural Networks]
        C3[Facebook Prophet]
        C4[Stakeholder Decision Framework]
    end
```

### Model Selection Justification (Based on Milestone 1 EDA)
- **SARIMA & Holt-Winters**: Justified by strong, recurring annual seasonality ($F_s > 0.85$).
- **XGBoost Regressor**: Justified by zero-heavy, highly skewed precipitation distributions requiring non-linear tree-based splits on lag features.
- **LSTM / Deep Learning**: Justified by long-range temporal dependencies and non-linear interactions across multivariable features (temperature, pressure, humidity).

---

## 🛠️ 5. Quickstart & Execution

### 1. Clone & Setup Environment
```bash
git clone https://github.com/<your-username>/delhi-weather-time-series.git
cd delhi-weather-time-series

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Complete Milestone 1 Pipeline
```bash
python milestone1_pipeline.py
```

### 3. Generated Artifacts
Executing the pipeline produces:
- `milestone1_output/Milestone1_Synopsis.pptx` (Presentation slide deck with speaker notes)
- `milestone1_output/figures/*.png` (All high-resolution EDA plots)
- `milestone1_output/stats.json` (Exact statistics calculated for the presentation)
- `milestone1_output/daily_series.csv` (Aggregated daily time-series)

---

## 📚 6. Academic References & Literature

1. **Hyndman, R. J., & Athanasopoulos, G.** (2021). *Forecasting: Principles and Practice* (3rd ed.). OTexts.
2. **Box, G. E. P., Jenkins, G. M., Reinsel, G. C., & Ljung, G. M.** (2015). *Time Series Analysis: Forecasting and Control* (5th ed.). John Wiley & Sons.
3. **Cleveland, R. B., Cleveland, W. S., McRae, J. E., & Terpenning, I.** (1990). *STL: A Seasonal-Trend Decomposition Procedure Based on Loess*. Journal of Official Statistics, 6(1), 3–73.
4. **Taylor, S. J., & Letham, B.** (2018). *Forecasting at Scale*. The American Statistician, 72(1), 37–45.
5. **Hochreiter, S., & Schmidhuber, J.** (1997). *Long Short-Term Memory*. Neural Computation, 9(8), 1735–1780.
6. **Chen, T., & Guestrin, C.** (2016). *XGBoost: A Scalable Tree Boosting System*. In Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining (pp. 785–794).
7. **Bauer, P., Thorpe, A., & Brunet, G.** (2015). *The Quiet Revolution of Numerical Weather Prediction*. Nature, 525(7567), 47–55.
8. **Rasp, S., Dueben, P. D., Scher, S., Weyn, J. A., Mouatadid, S., & Thuerey, N.** (2020). *WeatherBench: A Benchmark Data Set for Data-Driven Weather Forecasting*. Journal of Advances in Modeling Earth Systems, 12(11), e2020MS002203.
9. **Kaggle Dataset**: *Indian Weather Dataset (1996–2026)*. Available at Kaggle.
