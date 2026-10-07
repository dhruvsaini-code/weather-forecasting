# 🌤️ Milestone 1 Synopsis Report: Delhi Urban Weather Analytics & Climatological Time-Series Exploration

**Course**: Time Series Analysis & Forecasting  
**Evaluation**: Milestone 1 (Synopsis Phase)  
**Team**: Team Lead & Group Members (Roll Nos.)  
**Evaluator**: Course Instructor & Project Evaluator  
**Date**: 07 October 2026  

---

## 1. Executive Summary & Problem Formulation
- **Target Domain**: Climate & Environmental Science / Urban Meteorology
- **Geographic Focus**: Delhi, India (Subtropical continental climate)
- **Time Horizon**: 01 Jan 1996 to 18 Mar 2026 (30 Continuous Years)
- **Core Problem**: Identifying longitudinal multi-decadal trends, recurring yearly seasonality, and extreme meteorological anomalies to scientifically formulate future forecasting architectures.

---

## 2. Dataset & Quality Audit
- **Source**: Kaggle - Indian Weather Dataset (1996–2026) (kaggle.com/datasets/sandeepgupta09/indian-weather-dataset-1996-2026)
- **Licence**: Open Data Commons Open Database License (ODbL) / CC BY-SA 4.0
- **Raw Observations**: 264,840 rows (Hourly (1-hr))
- **Daily Aggregated Points**: 11,035 days (far exceeding $\ge 500$ requirement)
- **Data Completeness**: >99.7% completeness across all meteorological attributes.

---

## 3. Key Exploratory Findings
1. **Thermal Dynamics**:
   - Overall Mean Temperature: **24.46 °C** (Std: **7.01 °C**)
   - Climatological Peak: **Jun** (Mean: **32.84 °C**)
   - Climatological Minimum: **Jan** (Mean: **13.07 °C**)
   - Annual Seasonal Swing: **19.77 °C**
2. **Time-Series Decomposition (STL)**:
   - Seasonal Strength ($F_s$): **0.934** (Dominant yearly periodicity)
   - Trend Strength ($F_t$): **0.083**
   - Residual Noise Std: **1.79 °C**
3. **Stationarity Diagnostics**:
   - Augmented Dickey-Fuller (ADF) Statistic: **-10.5964** ($p$-value: **6.3338e-19**)
   - KPSS Stationarity Statistic: **0.0158** ($p$-value: **0.1000**)
   - Autocorrelation Memory: $\text{Lag-1 ACF} = 0.989$, $\text{Lag-365 ACF} = 0.884$

---

## 4. Phase-Wise Project Roadmap
- **Milestone 1 (Current)**: Data Ingestion, Quality Auditing, Stationarity Diagnostics, STL Decomposition, and Synopsis Presentation. *(No forecasting models implemented)*.
- **Milestone 2 (Mid-Sem)**: Stationarity Differencing, Baseline Classical Models (ARIMA, SARIMA, Holt-Winters Exponential Smoothing), and Error Metric Formulations (RMSE, MAE, MAPE).
- **Milestone 3 (Final)**: Advanced Neural & Ensemble Models (LSTM/GRU, XGBoost with Lag Features, Facebook Prophet), Multi-Model Benchmarking, and Stakeholder Decision Frameworks.

---
