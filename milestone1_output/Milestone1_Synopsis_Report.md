# 🌤️ Milestone 1 Synopsis Report: Delhi Urban Weather Analytics & Climatological Time-Series Exploration

**Course**: Time Series Analysis & Forecasting  
**Evaluation**: Milestone 1 (Synopsis Phase - Completed)  
**Target Location**: Delhi, India (Subtropical continental climate)  
**Time Horizon**: 1 January 1996 to 18 March 2026 (Over 30 Continuous Years)  
**Source Dataset**: Kaggle — `sandeepgupta09/indian-weather-dataset-1996-2026`  
**License**: CC0: Public Domain (Verified on Kaggle)  
**Evaluator**: Course Instructor & Project Evaluator  

---

## 📌 1. Executive Summary & Problem Formulation

### 1.1 Problem Statement
> *How do ambient air temperature, precipitation, and coupled atmospheric variables in Delhi evolve across seasonal, annual, and multi-decadal horizons (1996–2026), and what empirical time-series properties govern the formulation and choice of predictive forecasting models in subsequent phases?*

### 1.2 Target Stakeholders & Decisions Supported
1. **Power & Utility Operators**: Projecting heatwave duration and peak summer load requirements to avoid electrical grid failures.
2. **Municipal Disaster & Stormwater Authorities**: Planning flood prevention infrastructure and urban drainage capacity based on concentrated monsoon precipitation.
3. **Agronomy & Regional Food Systems**: Monitoring shifting thermal boundaries and monsoon onset dates for Northern Indian crop scheduling.
4. **Public Health Agencies**: Formulating early warning advisories and vulnerability mitigation for extreme heat and winter cold snaps.

### 1.3 Evaluation Rule Compliance
In strict compliance with the Milestone 1 Synopsis evaluation rubric, **no predictive forecasting models are executed during this phase**. The scope is strictly delimited to problem formulation, data curation, quality auditing, exploratory visual analytics, stationarity diagnostics, and technical feasibility verification.

---

## 🔍 2. Dataset Architecture & Quality Audit

The dataset consists of longitudinal hourly observations over 30 years recorded at Delhi, India:

| Metric | Raw Ingestion | Daily Aggregation | Evaluation Threshold | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Observation Count** | 264,840 rows | 11,035 days | $\ge 500$ observations | **PASS (Exceeds by 22x)** |
| **Duplicate Timestamps**| 0 duplicates | 0 duplicates | 0 duplicates | **PASS (100% Unique)** |
| **Temporal Gaps** | 0 missing slots | 0 missing days | Continuous grid | **PASS (100% Continuity)** |
| **Variable Missingness**| 0.00% across all cols | 0.00% across all cols| $<5\%$ threshold | **PASS (Complete)** |
| **Frequency** | Hourly (Regular) | Daily ($N=11,035$) | Uniform interval | **PASS** |

### Data Dictionary & Variable Schema
- **`datetime`**: Regular hourly observation timestamp index (ISO-8601).
- **`temperature_C`**: Ambient air temperature at 2-meter elevation (°C).
- **`precip_mm`**: Cumulative precipitation / liquid rainfall (mm).
- **`humidity_pct`**: Atmospheric relative humidity percentage (%).
- **`wind_speed_ms`**: Horizontal wind velocity (m/s).
- **`pressure_hPa`**: Barometric air pressure at sea level (hPa).

---

## 📊 3. Stationarity & Time-Series Diagnostic Tests

Before selecting any forecasting architectures for subsequent phases, rigorous exploratory stationarity and memory tests were conducted on the daily temperature time series ($N=11,035$):

### 3.1 Unit-Root & Level Stationarity Tests
1. **Augmented Dickey-Fuller (ADF) Test**:
   - **Test Statistic**: **-10.6033**
   - **Critical Value (1%)**: **-3.4310**
   - **Critical Value (5%)**: **-2.8618**
   - **$p$-value**: **$6.09 \times 10^{-19}$**
   - *Inference*: Rejects the null hypothesis of a stochastic unit root with overwhelming statistical confidence ($p \ll 0.001$). The series does not exhibit an explosive random walk.
2. **Kwiatkowski-Phillips-Schmidt-Shin (KPSS) Test**:
   - **Test Statistic**: **0.0185**
   - **Critical Value (5%)**: **0.4630**
   - **Critical Value (1%)**: **0.7390**
   - **$p$-value**: **$\ge 0.1000$**
   - *Inference*: Fails to reject the null hypothesis of level stationarity. Confirms the series fluctuates around a stable climatological mean.

### 3.2 Autocorrelation Function (ACF) Memory
- **Lag 1 (1 Day)**: $\rho = 0.989$ (Intense short-term thermal inertia)
- **Lag 7 (1 Week)**: $\rho = 0.932$ (Strong synoptic-scale persistence)
- **Lag 30 (1 Month)**: $\rho = 0.771$ (Orderly intra-seasonal transition)
- **Lag 365 (1 Year)**: $\rho = 0.886$ (Exceptionally strong deterministic annual cyclic recurrence)

---

## 📈 4. Key Exploratory Findings & Climatological Insights

### 4.1 Thermal Dynamics & Seasonal Envelope
- **Overall Mean Temperature**: **24.39 °C**
- **Climatological Peak**: **June** (Mean: **32.85 °C**)
- **Climatological Minimum**: **January** (Mean: **12.90 °C**)
- **Annual Climatological Swing**: **19.94 °C**
- **Empirical Seasonality**:
  - **Summer (Mar–May)**: Median 28.5°C, high positive skewness, frequent heatwaves.
  - **Monsoon (Jun–Sep)**: High sustained temperatures coupled with elevated humidity.
  - **Post-Monsoon (Oct–Nov)**: Rapid thermal drop, temperature variance widens.
  - **Winter (Dec–Feb)**: Median 14.1°C, frequent dense radiation fog episodes.

### 4.2 LOESS STL Decomposition ($Period = 365\text{ days}$)
The additive structural decomposition ($Y_t = T_t + S_t + R_t$) reveals:
- **Seasonal Strength ($F_s$)**: **0.936** (Overwhelming dominant annual periodicity)
- **Trend Strength ($F_t$)**: **0.082** (Minor long-term secular drift compared to solar cycles)
- **Residual Noise Std. Dev. ($\sigma_R$)**: **1.79 °C**
- *Model Implication*: The high ratio $F_s \gg F_t$ directly motivates the implementation of **Seasonal ARIMA (SARIMA)** and **Holt-Winters Exponential Smoothing** models in Phase 2.

### 4.3 Precipitation Coupling & Monsoonal Concentration
- **Monsoon Concentration**: **78.2%** of Delhi's 30-year cumulative precipitation occurs strictly during the 4-month monsoon window (June through September).
- **Raw Correlation vs. Deseasonalized Anomaly**:
  - Raw Spearman Correlation: $\rho_{\text{raw}} = +0.25$ (Spurious positive association caused by both heat and rainfall peaking in summer/monsoon).
  - Deseasonalized Temperature Anomaly Correlation: $\rho_{\text{anom}} = -0.21$ (Statistically significant negative association reflecting physical evaporative cooling and cloud shading).

### 4.4 Top Historical Extreme Temperature Events
#### Top 5 Hottest Days (Daily Maximum Temperature)
1. **26 May 1998**: **46.9 °C**
2. **30 May 2024**: **46.2 °C**
3. **28 May 1998**: **46.2 °C**
4. **29 May 2024**: **46.1 °C**
5. **24 May 1998**: **46.0 °C**

#### Top 5 Coldest Days (Daily Minimum Temperature)
1. **31 Dec 2019**: **1.3 °C**
2. **06 Jan 2013**: **1.9 °C**
3. **01 Jan 2020**: **1.9 °C**
4. **28 Dec 2019**: **2.0 °C**
5. **30 Dec 2019**: **2.2 °C**

---

## 🔬 5. Review of Existing Systems & Feasibility Analysis

| Forecasting Paradigm | Key Characteristics | Technical Limitations | Project Direction |
| :--- | :--- | :--- | :--- |
| **Numerical Weather Prediction (NWP)** | Numerical fluid dynamics & atmospheric physics | Heavy supercomputer overhead; physical grid tuning | Contextual benchmark; out of scope for pure time series |
| **Classical Statistical (ARIMA / SARIMA)** | Autoregressive moving average on stationary series | Assumes linearity; limited non-linear multivariable flexibility | **Planned Phase 2 baseline models** |
| **Holt-Winters Exponential Smoothing** | Triple recursive smoothing (level, trend, seasonality) | Fixed linear parameters; cumulative multi-step drift | **Planned Phase 2 baseline comparison** |
| **LOESS STL Decomposition** | Non-parametric locally weighted polynomial regression | Purely descriptive; requires secondary model for forecast | **Phase 1 exploratory framework (Completed)** |
| **Machine Learning (XGBoost)** | Gradient boosted decision trees on engineered lags | Requires manual feature engineering; sensitive to extrapolation | **Planned Phase 3 ensemble benchmark** |
| **Deep Learning (LSTM) & Prophet** | Recurrent neural sequence modeling & additive Fourier models| Higher training compute; sensitive to hyperparameter tuning | **Planned Phase 3 advanced comparison** |

### Feasibility Confirmation
- **Sample Size**: 11,035 daily points far exceeds the required $\ge 500$ sample size.
- **Compute Stack**: Clean standard Python stack (`pandas`, `numpy`, `matplotlib`, `seaborn`, `statsmodels`, `scipy`).
- **Phasing**: Clear division across Milestone 1 (EDA/Synopsis), Milestone 2 (Classical Baselines), and Milestone 3 (Advanced ML/DL Benchmarks).

---

## 🚀 6. Multi-Phase Roadmap & Evaluation Protocol

```mermaid
graph LR
    A[Milestone 1: Synopsis & EDA] --> B[Milestone 2: Classical Models]
    B --> C[Milestone 3: Advanced ML/DL & Evaluation]
    
    subgraph Milestone 1 (Completed)
        A1[Data Quality & Continuity Audit]
        A2[Climatological Envelope & Extremes]
        A3[LOESS STL Decomposition]
        A4[Stationarity & Diagnostics: ADF/KPSS]
    end
    
    subgraph Milestone 2 (Mid-Sem)
        B1[Stationarity Differencing & ACF/PACF]
        B2[ARIMA, SARIMA & Holt-Winters Models]
        B3[Baseline Error Metrics: RMSE, MAE, MAPE]
        B4[Residual Diagnostics: Ljung-Box Test]
    end
    
    subgraph Milestone 3 (Final)
        C1[XGBoost with Lag Features]
        C2[LSTM Recurrent Neural Networks]
        C3[Facebook Prophet Additive Modeling]
        C4[Comparative Benchmark & Decision Framework]
    end
```

### Evaluation Protocol
- **Data Splitting**: Strict chronological chronological split (e.g. 70% Train, 15% Validation, 15% Test). **No random shuffling** to maintain temporal dependency.
- **Evaluation Metrics**:
  - **Root Mean Squared Error (RMSE)**: Penalizes severe anomalous prediction errors.
  - **Mean Absolute Error (MAE)**: Measures average absolute magnitude of forecasting error.
  - **Mean Absolute Percentage Error (MAPE)**: Relative scale-independent error metric.

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
