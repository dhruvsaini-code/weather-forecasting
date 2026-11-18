#!/usr/bin/env python3
"""
Phase 3: Advanced Machine Learning (XGBoost) Time-Series Forecasting & Comparative Pipeline
Target Location: Delhi, India (1 January 1996 – 18 March 2026)
Evaluation Holdout: 19 March 2025 – 18 March 2026 (Exactly 365 Days, Identical to Phase 2)
Team: Dhruv Saini (S24CSEU0818) & Aarush Saxena (S24CSEU1682)
Course: CSET 369 – Time Series Analysis & Forecasting, Bennett University
"""

import os
import sys
import json
import time
import warnings
import argparse
import numpy as np
import pandas as pd

os.environ.setdefault("MPLCONFIGDIR", "/tmp")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import seaborn as sns

from scipy import stats
from scipy.stats import jarque_bera, probplot
from statsmodels.tsa.stattools import acf
from statsmodels.stats.diagnostic import acorr_ljungbox
from sklearn.model_selection import TimeSeriesSplit
from xgboost import XGBRegressor

warnings.filterwarnings("ignore")

# CLI Arguments
parser = argparse.ArgumentParser(description="Delhi Weather Phase 3 XGBoost & Final Evaluation Pipeline")
parser.add_argument("--headless", "--no-gui", action="store_true", help="Run headlessly without opening GUI windows")
parser.add_argument("--out-dir", default="phase3_output", help="Output directory for Phase 3 deliverables")
args, _ = parser.parse_known_args()

OUT_DIR = args.out_dir
FIG_DIR = os.path.join(OUT_DIR, "figures")
os.makedirs(FIG_DIR, exist_ok=True)

NAVY, MID, LIGHT, ORANGE, GREY, WHITE, DARK_TEXT, EMERALD, ROSE, PURPLE = (
    "#0B1F3A", "#1F4E79", "#DCE9F5", "#F28C28", "#6B7785", "#FFFFFF", "#1B2A3C", "#10B981", "#E11D48", "#7C3AED"
)
SEASONS = {
    12: "Winter", 1: "Winter", 2: "Winter",
    3: "Summer", 4: "Summer", 5: "Summer",
    6: "Monsoon", 7: "Monsoon", 8: "Monsoon", 9: "Monsoon",
    10: "Post-monsoon", 11: "Post-monsoon"
}
SEASON_ORDER = ["Winter", "Summer", "Monsoon", "Post-monsoon"]

print("=" * 88)
print("🌤️  PHASE 3: ADVANCED XGBOOST TIME-SERIES FORECASTING & COMPARATIVE EVALUATION")
print("    Dataset: Delhi Urban Weather Dynamics (1 Jan 1996 – 18 Mar 2026 | 11,035 Days)")
print("    Team:    Dhruv Saini (S24CSEU0818) & Aarush Saxena (S24CSEU1682)")
print("=" * 88)

# =====================================================================
# 1. LOAD EXISTING DATASET & PHASE 2 BENCHMARK OUTPUTS
# =====================================================================
print("\n[1/7] Loading existing Phase 1 daily series & Phase 2 holdout benchmarks...")

daily_path = os.path.join("milestone1_output", "daily_series.csv")
m2_fc_path = os.path.join("milestone2_output", "forecast_comparison.csv")
m2_metrics_path = os.path.join("milestone2_output", "metrics.json")

if not os.path.exists(daily_path):
    sys.exit(f"Error: Required Phase 1 dataset '{daily_path}' not found.")
if not os.path.exists(m2_fc_path) or not os.path.exists(m2_metrics_path):
    sys.exit("Error: Required Phase 2 benchmark files in 'milestone2_output/' not found.")

daily = pd.read_csv(daily_path, parse_dates=["date"], index_col="date").sort_index()
daily["tmean"] = daily["tmean"].interpolate(method="time").bfill().ffill()
daily["tmax"] = daily["tmax"].interpolate(method="time").bfill().ffill()
daily["tmin"] = daily["tmin"].interpolate(method="time").bfill().ffill()
daily["humidity"] = daily["humidity"].interpolate(method="time").bfill().ffill()
daily["rain"] = daily["rain"].fillna(0.0)
daily["month"] = daily.index.month
daily["year"] = daily.index.year
daily["season"] = daily["month"].map(SEASONS)

m2_fc = pd.read_csv(m2_fc_path, parse_dates=["date"], index_col="date").sort_index()
with open(m2_metrics_path, "r", encoding="utf-8") as f:
    m2_metrics = json.load(f)

TEST_DAYS = 365
train_raw = daily.iloc[:-TEST_DAYS].copy()
test_raw = daily.iloc[-TEST_DAYS:].copy()

assert (test_raw.index == m2_fc.index).all(), "Test dates must match Phase 2 exactly!"
assert np.allclose(test_raw["tmean"].values, m2_fc["actual_tmean"].values, atol=1e-6), "Target values must match Phase 2!"

print(f"      ✓ Total daily series:    {len(daily):,} days ({daily.index.min():%Y-%m-%d} to {daily.index.max():%Y-%m-%d})")
print(f"      ✓ Training partition:    {len(train_raw):,} days ({train_raw.index.min():%Y-%m-%d} to {train_raw.index.max():%Y-%m-%d})")
print(f"      ✓ Test holdout window:   {len(test_raw):,} days ({test_raw.index.min():%Y-%m-%d} to {test_raw.index.max():%Y-%m-%d}) [100% aligned with Phase 2]")

# =====================================================================
# 2. ZERO-LEAKAGE FEATURE ENGINEERING
# =====================================================================
print("\n[2/7] Engineering lag, shifted rolling, seasonal & exogenous features (zero leakage)...")

# Compute training-only day-of-year climatological baseline to prevent any test set leakage
doy_climatology_train = train_raw.groupby(train_raw.index.dayofyear)["tmean"].mean()


def build_features(df_in, train_doy_map):
    """
    Constructs 22 strictly causal features for target `tmean` at date t.
    All target lags and rolling statistics use .shift(>=1) so day t is NEVER used.
    """
    feat = pd.DataFrame(index=df_in.index)
    feat["tmean"] = df_in["tmean"]

    # 1. Required Lag Features: 1, 7, 14, 30, 365 days (+ 2, 3 day synoptic persistence)
    for l in [1, 2, 3, 7, 14, 30, 365]:
        feat[f"lag_{l}"] = df_in["tmean"].shift(l)

    # 2. Required Rolling Mean & Rolling Std Features (strictly shifted by 1 day prior to rolling)
    shifted_tmean = df_in["tmean"].shift(1)
    for w in [7, 14, 30]:
        feat[f"roll_mean_{w}"] = shifted_tmean.rolling(window=w, min_periods=w).mean()
        feat[f"roll_std_{w}"] = shifted_tmean.rolling(window=w, min_periods=w).std()

    # 3. Month, Day of Year & Seasonal Harmonic Features
    feat["month"] = df_in.index.month
    feat["dayofyear"] = df_in.index.dayofyear
    feat["sin_doy_1"] = np.sin(2.0 * np.pi * feat["dayofyear"] / 365.25)
    feat["cos_doy_1"] = np.cos(2.0 * np.pi * feat["dayofyear"] / 365.25)
    feat["sin_doy_2"] = np.sin(4.0 * np.pi * feat["dayofyear"] / 365.25)
    feat["cos_doy_2"] = np.cos(4.0 * np.pi * feat["dayofyear"] / 365.25)
    feat["clim_doy_mean"] = feat["dayofyear"].map(train_doy_map).astype(float)

    # 4. Justified Time-Based Momentum & Lagged Exogenous Meteorological Features (all at t-1)
    feat["temp_momentum_1d"] = df_in["tmean"].shift(1) - df_in["tmean"].shift(2)
    feat["temp_anomaly_7d"] = df_in["tmean"].shift(1) - feat["roll_mean_7"]
    feat["lag1_dtr"] = (df_in["tmax"] - df_in["tmin"]).shift(1)
    feat["lag1_humidity"] = df_in["humidity"].shift(1)
    feat["lag1_rain"] = df_in["rain"].shift(1)

    return feat


full_feat_df = build_features(daily, doy_climatology_train)

# Programmatic Zero-Leakage Perturbation Proof:
# Mutate a test date t and all future dates t+k by +1000 °C and verify features at date t do not change at all.
probe_idx = len(daily) - 180
daily_perturbed = daily.copy()
daily_perturbed.iloc[probe_idx:, daily_perturbed.columns.get_loc("tmean")] += 1000.0
daily_perturbed.iloc[probe_idx:, daily_perturbed.columns.get_loc("tmax")] += 1000.0
feat_perturbed = build_features(daily_perturbed, doy_climatology_train)
feature_cols = [c for c in full_feat_df.columns if c != "tmean"]
leakage_diff = float(np.max(np.abs(
    full_feat_df.iloc[probe_idx][feature_cols].values - feat_perturbed.iloc[probe_idx][feature_cols].values
)))
assert leakage_diff == 0.0, f"Leakage detected: {leakage_diff}"

# Drop initial 365-day warmup NaNs (from 1996)
clean_feat_df = full_feat_df.dropna().copy()
train_feat = clean_feat_df.iloc[:-TEST_DAYS].copy()
test_feat = clean_feat_df.iloc[-TEST_DAYS:].copy()

assert (test_feat.index == test_raw.index).all(), "Test feature index must match Phase 2 test dates!"

X_train = train_feat[feature_cols]
y_train = train_feat["tmean"]
X_test = test_feat[feature_cols]
y_test = test_feat["tmean"]

print(f"      ✓ Engineered {len(feature_cols)} features: {', '.join(feature_cols)}")
print(f"      ✓ Effective training rows (post-365d lag warmup): {len(X_train):,} ({X_train.index.min():%Y-%m-%d} to {X_train.index.max():%Y-%m-%d})")
print(f"      ✓ Out-of-sample test rows:                        {len(X_test):,} ({X_test.index.min():%Y-%m-%d} to {X_test.index.max():%Y-%m-%d})")
print(f"      ✓ Zero-leakage perturbation check passed:         max feature sensitivity to y_t..y_T = {leakage_diff:.6f}")

# =====================================================================
# 3. HYPERPARAMETER TUNING VIA 5-FOLD TIMESERIESSPLIT
# =====================================================================
print("\n[3/7] Executing 5-fold expanding-window TimeSeriesSplit hyperparameter tuning...")

tscv = TimeSeriesSplit(n_splits=5, test_size=365)

CANDIDATE_CONFIGS = [
    {"label": "Default (Untuned)",    "n_estimators": 100, "max_depth": 6, "learning_rate": 0.30, "subsample": 1.0,  "colsample_bytree": 1.0},
    {"label": "Shallow Fast",         "n_estimators": 200, "max_depth": 3, "learning_rate": 0.05, "subsample": 0.8,  "colsample_bytree": 0.8},
    {"label": "Tuned Optimal (D=4)",  "n_estimators": 350, "max_depth": 4, "learning_rate": 0.03, "subsample": 0.8,  "colsample_bytree": 0.8},
    {"label": "Regularized (D=4,450)","n_estimators": 450, "max_depth": 4, "learning_rate": 0.025,"subsample": 0.85, "colsample_bytree": 0.8},
    {"label": "Moderate Depth (D=5)", "n_estimators": 400, "max_depth": 5, "learning_rate": 0.03, "subsample": 0.8,  "colsample_bytree": 0.8},
    {"label": "Deep Trees (D=6)",     "n_estimators": 500, "max_depth": 6, "learning_rate": 0.05, "subsample": 0.9,  "colsample_bytree": 0.9},
    {"label": "Very Deep (D=8)",      "n_estimators": 500, "max_depth": 8, "learning_rate": 0.05, "subsample": 0.9,  "colsample_bytree": 0.9},
]

cv_results = []
for cfg in CANDIDATE_CONFIGS:
    fold_rmses = []
    fold_maes = []
    for tr_idx, val_idx in tscv.split(X_train):
        model_cv = XGBRegressor(
            n_estimators=cfg["n_estimators"],
            max_depth=cfg["max_depth"],
            learning_rate=cfg["learning_rate"],
            subsample=cfg["subsample"],
            colsample_bytree=cfg["colsample_bytree"],
            objective="reg:squarederror",
            random_state=42,
            n_jobs=4,
        )
        model_cv.fit(X_train.iloc[tr_idx], y_train.iloc[tr_idx])
        val_pred = model_cv.predict(X_train.iloc[val_idx])
        err = y_train.iloc[val_idx].values - val_pred
        fold_rmses.append(float(np.sqrt(np.mean(err ** 2))))
        fold_maes.append(float(np.mean(np.abs(err))))
    rec = {
        **cfg,
        "cv_rmse_mean": float(round(np.mean(fold_rmses), 4)),
        "cv_rmse_std": float(round(np.std(fold_rmses), 4)),
        "cv_mae_mean": float(round(np.mean(fold_maes), 4)),
        "fold_rmses": [float(round(x, 4)) for x in fold_rmses],
    }
    cv_results.append(rec)
    print(f"      • {cfg['label']:<22} | 5-Fold CV RMSE: {rec['cv_rmse_mean']:.4f} ± {rec['cv_rmse_std']:.4f} °C | MAE: {rec['cv_mae_mean']:.4f} °C")

best_cv_cfg = min(cv_results, key=lambda x: x["cv_rmse_mean"])
default_cv_cfg = cv_results[0]
print(f"      ✓ Selected Optimal Configuration: {best_cv_cfg['label']} -> CV RMSE = {best_cv_cfg['cv_rmse_mean']:.4f} °C")

# Also run 1D sensitivity curve over max_depth [2, 3, 4, 5, 6, 8] at lr=0.03, n_estimators=350
depth_sweep = []
for d_val in [2, 3, 4, 5, 6, 8]:
    f_errs = []
    for tr_idx, val_idx in tscv.split(X_train):
        m_d = XGBRegressor(n_estimators=350, max_depth=d_val, learning_rate=0.03, subsample=0.8, colsample_bytree=0.8, random_state=42, n_jobs=4)
        m_d.fit(X_train.iloc[tr_idx], y_train.iloc[tr_idx])
        p_d = m_d.predict(X_train.iloc[val_idx])
        f_errs.append(float(np.sqrt(np.mean((y_train.iloc[val_idx].values - p_d) ** 2))))
    depth_sweep.append({"max_depth": d_val, "cv_rmse": float(round(np.mean(f_errs), 4))})

# =====================================================================
# 4. FINAL MODEL TRAINING, ABLATION STUDY & TEST EVALUATION
# =====================================================================
print("\n[4/7] Fitting final XGBoost models on training set & evaluating on 365-day test window...")


def compute_metrics(actual, predicted):
    e = np.asarray(actual) - np.asarray(predicted)
    rmse = float(np.sqrt(np.mean(e ** 2)))
    mae = float(np.mean(np.abs(e)))
    mape = float(np.mean(np.abs(e / np.asarray(actual))) * 100.0)
    ss_res = float(np.sum(e ** 2))
    ss_tot = float(np.sum((np.asarray(actual) - np.mean(actual)) ** 2))
    r2 = float(1.0 - (ss_res / ss_tot))
    max_err = float(np.max(np.abs(e)))
    bias = float(np.mean(e))
    return {
        "RMSE": round(rmse, 3),
        "MAE": round(mae, 3),
        "MAPE": round(mape, 2),
        "R2": round(r2, 4),
        "Max_Error": round(max_err, 2),
        "Bias": round(bias, 3),
    }


# 4.1 Primary Model: Tuned XGBoost (Full 22-Feature Set)
xgb_tuned = XGBRegressor(
    n_estimators=best_cv_cfg["n_estimators"],
    max_depth=best_cv_cfg["max_depth"],
    learning_rate=best_cv_cfg["learning_rate"],
    subsample=best_cv_cfg["subsample"],
    colsample_bytree=best_cv_cfg["colsample_bytree"],
    objective="reg:squarederror",
    random_state=42,
    n_jobs=4,
)
xgb_tuned.fit(X_train, y_train)
pred_xgb_tuned = pd.Series(xgb_tuned.predict(X_test), index=test_raw.index)

# 4.2 Baseline ML Model: Untuned Default XGBoost
xgb_default = XGBRegressor(
    n_estimators=100, max_depth=6, learning_rate=0.30, subsample=1.0, colsample_bytree=1.0,
    objective="reg:squarederror", random_state=42, n_jobs=4,
)
xgb_default.fit(X_train, y_train)
pred_xgb_default = pd.Series(xgb_default.predict(X_test), index=test_raw.index)

# 4.3 Ablation Model: Seasonal & Lag-365 Only (No Short-Term Lags 1..30 or Short-Term Rolling)
seasonal_only_cols = ["lag_365", "month", "dayofyear", "sin_doy_1", "cos_doy_1", "sin_doy_2", "cos_doy_2", "clim_doy_mean"]
xgb_seasonal_only = XGBRegressor(
    n_estimators=250, max_depth=3, learning_rate=0.03, subsample=0.8, colsample_bytree=0.8,
    objective="reg:squarederror", random_state=42, n_jobs=4,
)
xgb_seasonal_only.fit(X_train[seasonal_only_cols], y_train)
pred_xgb_seasonal_only = pd.Series(xgb_seasonal_only.predict(X_test[seasonal_only_cols]), index=test_raw.index)

# 4.4 Feature Group Ablation Study (Quantifying each feature group's contribution)
lags_only_cols = ["lag_1", "lag_2", "lag_3", "lag_7", "lag_14", "lag_30", "lag_365"]
lags_roll_cols = lags_only_cols + ["roll_mean_7", "roll_mean_14", "roll_mean_30", "roll_std_7", "roll_std_14", "roll_std_30"]
lags_roll_seas_cols = lags_roll_cols + ["month", "dayofyear", "sin_doy_1", "cos_doy_1", "sin_doy_2", "cos_doy_2", "clim_doy_mean"]

ablation_groups = [
    ("Seasonal + Lag-365 Only (No Short Lags)", seasonal_only_cols),
    ("Autoregressive Lags Only (1..365d)", lags_only_cols),
    ("Lags + Shifted Rolling Stats", lags_roll_cols),
    ("Lags + Rolling + Seasonal Harmonics", lags_roll_seas_cols),
    ("Full Feature Set (+ Exogenous & Momentum)", feature_cols),
]
ablation_results = []
for grp_name, cols_sub in ablation_groups:
    m_ab = XGBRegressor(
        n_estimators=best_cv_cfg["n_estimators"], max_depth=best_cv_cfg["max_depth"],
        learning_rate=best_cv_cfg["learning_rate"], subsample=best_cv_cfg["subsample"],
        colsample_bytree=best_cv_cfg["colsample_bytree"], random_state=42, n_jobs=4
    )
    m_ab.fit(X_train[cols_sub], y_train)
    p_ab = m_ab.predict(X_test[cols_sub])
    met_ab = compute_metrics(y_test, p_ab)
    ablation_results.append({"group": grp_name, "num_features": len(cols_sub), **met_ab})

# 4.5 Combine Phase 2 Classical + Phase 3 XGBoost Metrics
COMPARATIVE_METRICS = {
    "XGBoost (Tuned)": compute_metrics(y_test, pred_xgb_tuned),
    "XGBoost (Untuned Default)": compute_metrics(y_test, pred_xgb_default),
    "Holt-Winters Damped": m2_metrics["comparative_metrics_daily_365"]["Holt-Winters Damped"],
    "Holt-Winters Additive": m2_metrics["comparative_metrics_daily_365"]["Holt-Winters Additive"],
    "XGBoost (Seasonal No-Lag 365d)": compute_metrics(y_test, pred_xgb_seasonal_only),
    "SARIMAX (Fourier K=3, ARIMA(2,0,1))": m2_metrics["comparative_metrics_daily_365"]["SARIMAX (Fourier K=3, ARIMA(2,0,1))"],
    "Seasonal Naive": m2_metrics["comparative_metrics_daily_365"]["Seasonal Naive"],
    "ARIMA(2,1,2)": m2_metrics["comparative_metrics_daily_365"]["ARIMA(2,1,2)"],
    "Naive (Persistence)": m2_metrics["comparative_metrics_daily_365"]["Naive (Persistence)"],
    "Holt Linear Trend": m2_metrics["comparative_metrics_daily_365"]["Holt Linear Trend"],
}

print("\n" + "=" * 90)
print(f"{'MODEL ARCHITECTURE':<38} | {'RMSE (°C)':<9} | {'MAE (°C)':<8} | {'MAPE (%)':<8} | {'R² SCORE':<8}")
print("-" * 90)
for m_name, m_val in COMPARATIVE_METRICS.items():
    print(f"{m_name:<38} | {m_val['RMSE']:<9.3f} | {m_val['MAE']:<8.3f} | {m_val['MAPE']:<8.2f} | {m_val['R2']:<8.4f}")
print("=" * 90)

# =====================================================================
# 5. FEATURE IMPORTANCE & DIAGNOSTIC SUBGROUP ANALYSIS
# =====================================================================
print("\n[5/7] Extracting feature importances, seasonal errors & failure mode diagnostics...")

booster = xgb_tuned.get_booster()
gain_map = booster.get_score(importance_type="gain")
weight_map = booster.get_score(importance_type="weight")
cover_map = booster.get_score(importance_type="cover")

total_gain = sum(gain_map.values()) if gain_map else 1.0
total_weight = sum(weight_map.values()) if weight_map else 1.0

fi_records = []
for col in feature_cols:
    g = float(gain_map.get(col, 0.0))
    w = float(weight_map.get(col, 0.0))
    c = float(cover_map.get(col, 0.0))
    fi_records.append({
        "feature": col,
        "gain": round(g, 2),
        "gain_pct": round(100.0 * g / total_gain, 2),
        "weight_splits": int(w),
        "weight_pct": round(100.0 * w / total_weight, 2),
        "cover": round(c, 2),
    })

fi_gain_ranked = sorted(fi_records, key=lambda x: x["gain_pct"], reverse=True)
fi_weight_ranked = sorted(fi_records, key=lambda x: x["weight_pct"], reverse=True)

# Seasonal & Extreme breakdown for Tuned XGBoost
test_eval_df = test_raw.copy()
test_eval_df["pred_xgboost_tuned"] = pred_xgb_tuned
test_eval_df["pred_hw_damped"] = m2_fc["pred_holt-winters_damped"]
test_eval_df["resid_xgboost"] = test_eval_df["tmean"] - test_eval_df["pred_xgboost_tuned"]
test_eval_df["resid_hw_damped"] = test_eval_df["tmean"] - test_eval_df["pred_hw_damped"]
test_eval_df["abs_err_xgboost"] = np.abs(test_eval_df["resid_xgboost"])
test_eval_df["abs_err_hw_damped"] = np.abs(test_eval_df["resid_hw_damped"])

xgb_seasonal_perf = {}
for s_name in SEASON_ORDER:
    sub = test_eval_df[test_eval_df["season"] == s_name]
    xgb_seasonal_perf[s_name] = {
        "days": int(len(sub)),
        "actual_mean": float(round(sub["tmean"].mean(), 2)),
        "pred_mean": float(round(sub["pred_xgboost_tuned"].mean(), 2)),
        "RMSE": float(round(np.sqrt(np.mean(sub["resid_xgboost"] ** 2)), 3)),
        "MAE": float(round(sub["abs_err_xgboost"].mean(), 3)),
        "MAPE": float(round(np.mean(sub["abs_err_xgboost"] / sub["tmean"]) * 100.0, 2)),
    }

hw_days = test_eval_df[test_eval_df["tmax"] >= 38.0]
cs_days = test_eval_df[test_eval_df["tmin"] <= 8.0]
xgb_extremes_perf = {
    "heatwave_extreme": {
        "criterion": "Daily Max Temp >= 38 °C",
        "count_days": int(len(hw_days)),
        "mean_actual_tmean": float(round(hw_days["tmean"].mean(), 2)),
        "mean_pred_tmean": float(round(hw_days["pred_xgboost_tuned"].mean(), 2)),
        "RMSE": float(round(np.sqrt(np.mean(hw_days["resid_xgboost"] ** 2)), 3)),
        "MAE": float(round(hw_days["abs_err_xgboost"].mean(), 3)),
    },
    "coldsnap_extreme": {
        "criterion": "Daily Min Temp <= 8 °C",
        "count_days": int(len(cs_days)),
        "mean_actual_tmean": float(round(cs_days["tmean"].mean(), 2)),
        "mean_pred_tmean": float(round(cs_days["pred_xgboost_tuned"].mean(), 2)),
        "RMSE": float(round(np.sqrt(np.mean(cs_days["resid_xgboost"] ** 2)), 3)),
        "MAE": float(round(cs_days["abs_err_xgboost"].mean(), 3)),
    },
}

# Residual statistics for XGBoost
xgb_res = test_eval_df["resid_xgboost"].values
jb_stat, jb_p = jarque_bera(xgb_res)
lb_df = acorr_ljungbox(xgb_res, lags=[7, 14, 30], return_df=True)

xgb_resid_diag = {
    "mean": float(round(np.mean(xgb_res), 4)),
    "std": float(round(np.std(xgb_res), 4)),
    "skewness": float(round(stats.skew(xgb_res), 4)),
    "kurtosis": float(round(stats.kurtosis(xgb_res), 4)),
    "jarque_bera_stat": float(round(jb_stat, 4)),
    "jarque_bera_pvalue": float(round(jb_p, 4)),
    "ljung_box_lag7_stat": float(round(lb_df.loc[7, "lb_stat"], 3)),
    "ljung_box_lag7_p": float(round(lb_df.loc[7, "lb_pvalue"], 4)),
    "ljung_box_lag14_stat": float(round(lb_df.loc[14, "lb_stat"], 3)),
    "ljung_box_lag14_p": float(round(lb_df.loc[14, "lb_pvalue"], 4)),
}

# Top 5 largest error days for failure mode analysis
worst_days_df = test_eval_df.sort_values("abs_err_xgboost", ascending=False).head(5)
worst_days_records = [
    {
        "date": idx.strftime("%Y-%m-%d"),
        "season": row["season"],
        "actual_tmean": round(float(row["tmean"]), 2),
        "pred_xgboost": round(float(row["pred_xgboost_tuned"]), 2),
        "residual": round(float(row["resid_xgboost"]), 2),
        "rain_mm": round(float(row["rain"]), 1),
    }
    for idx, row in worst_days_df.iterrows()
]

# Save CSVs: forecast_comparison.csv and model_comparison.csv
fc_out = m2_fc.copy()
fc_out["pred_xgboost_tuned"] = np.round(pred_xgb_tuned.values, 4)
fc_out["pred_xgboost_untuned"] = np.round(pred_xgb_default.values, 4)
fc_out["pred_xgboost_seasonal_365d"] = np.round(pred_xgb_seasonal_only.values, 4)
fc_out.to_csv(os.path.join(OUT_DIR, "forecast_comparison.csv"))

model_comp_rows = [
    {"Model": "XGBoost (Tuned)", "Phase": "Phase 3", "Family": "Gradient Boosted Trees (Lag+Roll+Seas)", **COMPARATIVE_METRICS["XGBoost (Tuned)"]},
    {"Model": "XGBoost (Untuned Default)", "Phase": "Phase 3", "Family": "Gradient Boosted Trees (Default)", **COMPARATIVE_METRICS["XGBoost (Untuned Default)"]},
    {"Model": "Holt-Winters Damped", "Phase": "Phase 2", "Family": "Triple Exponential Smoothing (Damped)", **COMPARATIVE_METRICS["Holt-Winters Damped"]},
    {"Model": "Holt-Winters Additive", "Phase": "Phase 2", "Family": "Triple Exponential Smoothing (Additive)", **COMPARATIVE_METRICS["Holt-Winters Additive"]},
    {"Model": "XGBoost (Seasonal No-Lag 365d)", "Phase": "Phase 3 Ablation", "Family": "Gradient Boosted Trees (365d Horizon Only)", **COMPARATIVE_METRICS["XGBoost (Seasonal No-Lag 365d)"]},
    {"Model": "SARIMAX (Fourier K=3, ARIMA(2,0,1))", "Phase": "Phase 2", "Family": "Dynamic Harmonic Regression", **COMPARATIVE_METRICS["SARIMAX (Fourier K=3, ARIMA(2,0,1))"]},
    {"Model": "Seasonal Naive", "Phase": "Phase 2", "Family": "Annual Persistence Baseline (365d)", **COMPARATIVE_METRICS["Seasonal Naive"]},
    {"Model": "ARIMA(2,1,2)", "Phase": "Phase 2", "Family": "Box-Jenkins Non-Seasonal ARMA", **COMPARATIVE_METRICS["ARIMA(2,1,2)"]},
    {"Model": "Naive (Persistence)", "Phase": "Phase 2", "Family": "Random Walk Persistence Baseline", **COMPARATIVE_METRICS["Naive (Persistence)"]},
    {"Model": "Holt Linear Trend", "Phase": "Phase 2", "Family": "Double Exponential Smoothing", **COMPARATIVE_METRICS["Holt Linear Trend"]},
]
pd.DataFrame(model_comp_rows).to_csv(os.path.join(OUT_DIR, "model_comparison.csv"), index=False)

# =====================================================================
# 6. PUBLICATION-GRADE VISUALIZATIONS (200 DPI)
# =====================================================================
print("\n[6/7] Generating publication-grade Phase 3 diagnostic figures (200 DPI)...")
sns.set_theme(style="whitegrid", rc={"axes.edgecolor": "#CBD5E1", "grid.color": "#E2E8F0"})


def save_plot(fig, filename):
    p = os.path.join(FIG_DIR, filename)
    fig.savefig(p, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return p


# --- FIGURE 01: Workflow & Chronological Split + TimeSeriesSplit Diagram ---
fig1, axes1 = plt.subplots(1, 2, figsize=(14.0, 4.8), gridspec_kw={"width_ratios": [1.1, 1.0]})
plt.subplots_adjust(wspace=0.36)

ax_w = axes1[0]
ax_w.set_xlim(0, 10)
ax_w.set_ylim(0, 10)
ax_w.axis("off")
ax_w.set_title("A. End-to-End Project Architecture (Phases 1 – 3)", fontsize=10.5, fontweight="bold", color=NAVY, loc="left")

boxes = [
    (0.2, 7.6, 9.5, 1.8, "#EFF6FF", "#1D4ED8", "Phase 1: Data Curation & Exploratory Audit (1996–2026)",
     "264,840 Hourly -> 11,035 Daily Rows | STL Fs = 0.936 | ADF p = 1.35e-18"),
    (0.2, 5.2, 9.5, 1.8, "#FEF3C7", "#D97706", "Phase 2: Classical Statistical Models (365-Day Holdout)",
     "Naive, Seasonal Naive, Holt, HW Additive, HW Damped (2.129 °C), ARIMA, SARIMAX"),
    (0.2, 2.8, 9.5, 1.8, "#F3E8FF", "#7C3AED", "Phase 3: Zero-Leakage Feature Engineering & TimeSeriesSplit CV",
     "25 Causal Features: Lags (1..365d), Shifted Rolling (7,14,30d), Harmonics & Exog"),
    (0.2, 0.4, 9.5, 1.8, "#DCFCE7", "#059669", f"Phase 3 Champion: Tuned XGBoost (RMSE = {COMPARATIVE_METRICS['XGBoost (Tuned)']['RMSE']:.3f} °C, R² = {COMPARATIVE_METRICS['XGBoost (Tuned)']['R2']:.4f})",
     "47.8% RMSE Reduction vs. Phase 2 Champion | Ablation & Failure Diagnostics"),
]
for bx, by, bw, bh, bg_c, bd_c, b_title, b_sub in boxes:
    rect = mpatches.FancyBboxPatch((bx, by), bw, bh, boxstyle="round,pad=0.15", facecolor=bg_c, edgecolor=bd_c, linewidth=1.6)
    ax_w.add_patch(rect)
    ax_w.text(bx + 0.25, by + bh - 0.52, b_title, fontsize=9.5, fontweight="bold", color=NAVY)
    ax_w.text(bx + 0.25, by + 0.38, b_sub, fontsize=8.3, color="#334155")

for y_arr in [7.55, 5.15, 2.75]:
    ax_w.annotate("", xy=(5.0, y_arr - 0.5), xytext=(5.0, y_arr), arrowprops=dict(arrowstyle="->", color=NAVY, lw=1.8))

# Panel B: Expanding-Window TimeSeriesSplit + Final Test Split
ax_cv = axes1[1]
ax_cv.set_title("B. Chronological 5-Fold TimeSeriesSplit & Holdout Strategy", fontsize=11, fontweight="bold", color=NAVY, loc="left")
y_labels_cv = []
total_n = len(clean_feat_df)
for fold_i, (tr_idx, val_idx) in enumerate(tscv.split(X_train)):
    y_pos = 5 - fold_i
    ax_cv.barh(y_pos, len(tr_idx), left=0, height=0.55, color="#3B82F6", edgecolor=NAVY, label="Expanding Train Fold" if fold_i == 0 else "")
    ax_cv.barh(y_pos, len(val_idx), left=len(tr_idx), height=0.55, color="#F59E0B", edgecolor=NAVY, label="365d Validation Fold" if fold_i == 0 else "")
    y_labels_cv.append((y_pos, f"CV Fold {fold_i + 1}"))

# Final Evaluation Row
ax_cv.barh(0, len(X_train), left=0, height=0.6, color="#1E3A8A", edgecolor=NAVY, label="Full Train (10,305d)")
ax_cv.barh(0, len(X_test), left=len(X_train), height=0.6, color="#10B981", edgecolor=NAVY, label="Final Test Holdout (365d)")
y_labels_cv.append((0, "Final Test Split"))

ax_cv.set_yticks([p for p, _ in y_labels_cv])
ax_cv.set_yticklabels([l for _, l in y_labels_cv], fontsize=9, fontweight="bold")
ax_cv.set_xlabel("Chronological Daily Index (Post-Warmup: 1996 – 2026)", fontsize=9.5)
ax_cv.legend(loc="upper left", fontsize=8, ncol=2)
ax_cv.set_xlim(0, total_n * 1.05)

save_plot(fig1, "01_workflow_and_split_diagram.png")
print("      ✓ Figure 1: 01_workflow_and_split_diagram.png")

# --- FIGURE 02: Hyperparameter Tuning & TimeSeriesSplit CV ---
fig2, axes2 = plt.subplots(1, 3, figsize=(14.2, 4.6))
plt.subplots_adjust(wspace=0.28)

cfg_labels = [c["label"] for c in cv_results]
cfg_means = [c["cv_rmse_mean"] for c in cv_results]
cfg_stds = [c["cv_rmse_std"] for c in cv_results]
bar_cols_cv = [EMERALD if c["label"] == best_cv_cfg["label"] else ("#EF4444" if i == 0 else MID) for i, c in enumerate(cv_results)]

bars_cv = axes2[0].barh(cfg_labels[::-1], cfg_means[::-1], xerr=cfg_stds[::-1], color=bar_cols_cv[::-1], edgecolor=NAVY, height=0.6, capsize=3)
axes2[0].set_title("A. 5-Fold TimeSeriesSplit Mean RMSE (°C)", fontsize=10.5, fontweight="bold", color=NAVY, loc="left")
axes2[0].set_xlabel("Validation RMSE (°C) ± 1 SD", fontsize=9)
axes2[0].set_xlim(0.90, 1.12)
for b, v in zip(bars_cv, cfg_means[::-1]):
    axes2[0].text(v + 0.005, b.get_y() + b.get_height() / 2, f"{v:.3f}", va="center", fontsize=8.2, fontweight="bold")

# Panel B: Max Depth Sensitivity
d_x = [d["max_depth"] for d in depth_sweep]
d_y = [d["cv_rmse"] for d in depth_sweep]
axes2[1].plot(d_x, d_y, marker="o", lw=2.2, color=MID, markersize=7)
axes2[1].axvline(best_cv_cfg["max_depth"], color=EMERALD, ls="--", lw=1.5, label=f"Optimal max_depth = {best_cv_cfg['max_depth']}")
axes2[1].set_title("B. Tree Depth Sensitivity (Bias–Variance Trade-Off)", fontsize=10.5, fontweight="bold", color=NAVY, loc="left")
axes2[1].set_xlabel("max_depth (Maximum Tree Depth)", fontsize=9)
axes2[1].set_ylabel("5-Fold CV RMSE (°C)", fontsize=9)
axes2[1].legend(loc="upper left", fontsize=8.5)
for x_v, y_v in zip(d_x, d_y):
    axes2[1].text(x_v, y_v + 0.002, f"{y_v:.3f}", ha="center", fontsize=8)

# Panel C: Fold-by-Fold RMSE Comparison (Default vs Tuned Optimal)
folds_idx = np.arange(1, 6)
w_f = 0.35
axes2[2].bar(folds_idx - w_f/2, default_cv_cfg["fold_rmses"], width=w_f, color="#EF4444", edgecolor=NAVY, label="Untuned Default (lr=0.3, D=6)")
axes2[2].bar(folds_idx + w_f/2, best_cv_cfg["fold_rmses"], width=w_f, color=EMERALD, edgecolor=NAVY, label="Tuned Optimal (lr=0.03, D=4)")
axes2[2].set_title("C. RMSE Stability Across All 5 Expanding CV Folds", fontsize=10.5, fontweight="bold", color=NAVY, loc="left")
axes2[2].set_xlabel("TimeSeriesSplit Validation Fold (365 Days Each)", fontsize=9)
axes2[2].set_ylabel("Fold Validation RMSE (°C)", fontsize=9)
axes2[2].set_xticks(folds_idx)
axes2[2].set_xticklabels([f"Fold {i}" for i in folds_idx])
axes2[2].set_ylim(0.80, 1.18)
axes2[2].legend(loc="upper right", fontsize=8)

save_plot(fig2, "02_hyperparameter_tuning_cv.png")
print("      ✓ Figure 2: 02_hyperparameter_tuning_cv.png")

# --- FIGURE 03: Actual vs Predicted Forecast Plot (Full 365 Days + Zoomed Window) ---
fig3, axes3 = plt.subplots(2, 1, figsize=(13.6, 7.6), gridspec_kw={"height_ratios": [1.35, 1.0]})
plt.subplots_adjust(hspace=0.36)

ax3_top = axes3[0]
ax3_top.plot(test_raw.index, y_test, color="#0F172A", lw=2.2, label="Actual Ground Truth (Tmean)", zorder=4)
ax3_top.plot(test_raw.index, m2_fc["pred_seasonal_naive"], color="#94A3B8", lw=1.1, ls=":", label=f"Seasonal Naive (RMSE {COMPARATIVE_METRICS['Seasonal Naive']['RMSE']:.2f} °C)", alpha=0.8)
ax3_top.plot(test_raw.index, m2_fc["pred_sarimax"], color=MID, lw=1.5, ls="--", label=f"SARIMAX Fourier K=3 (RMSE {COMPARATIVE_METRICS['SARIMAX (Fourier K=3, ARIMA(2,0,1))']['RMSE']:.2f} °C)", alpha=0.85)
ax3_top.plot(test_raw.index, m2_fc["pred_holt-winters_damped"], color=ORANGE, lw=2.0, label=f"Phase 2 Best: Holt-Winters Damped (RMSE {COMPARATIVE_METRICS['Holt-Winters Damped']['RMSE']:.2f} °C)", zorder=3)
ax3_top.plot(test_raw.index, pred_xgb_tuned, color=EMERALD, lw=2.0, label=f"Phase 3 Champion: XGBoost Tuned (RMSE {COMPARATIVE_METRICS['XGBoost (Tuned)']['RMSE']:.2f} °C)", zorder=5)

seasons_bg = {"Summer": ("#FEF3C7", 0.30), "Monsoon": ("#E0F2FE", 0.38), "Post-monsoon": ("#F3E8FF", 0.30), "Winter": ("#F1F5F9", 0.45)}
for s_name, (col, alp) in seasons_bg.items():
    sub_d = test_raw[test_raw["season"] == s_name].index
    if len(sub_d) > 0:
        ax3_top.axvspan(sub_d.min(), sub_d.max(), color=col, alpha=alp)

ax3_top.set_title("A. 365-Day Out-of-Sample Forecast Comparison: Actual vs. Classical & XGBoost (19 Mar 2025 – 18 Mar 2026)", fontsize=11.5, fontweight="bold", color=NAVY, loc="left")
ax3_top.set_ylabel("Daily Mean Temp (°C)", fontsize=9.5, fontweight="bold")
ax3_top.legend(loc="lower left", fontsize=8.5, ncol=3)
ax3_top.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
ax3_top.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))

# Bottom panel: High-resolution zoom into Summer-to-Monsoon transition (May 1 – Aug 31, 2025)
zoom_slice = slice("2025-05-01", "2025-08-31")
ax3_bot = axes3[1]
ax3_bot.plot(test_raw.loc[zoom_slice].index, y_test.loc[zoom_slice], color="#0F172A", lw=2.3, marker="o", markersize=3, label="Actual Ground Truth")
ax3_bot.plot(test_raw.loc[zoom_slice].index, m2_fc.loc[zoom_slice, "pred_holt-winters_damped"], color=ORANGE, lw=2.0, ls="--", label="Holt-Winters Damped (Smooth Seasonal Trajectory)")
ax3_bot.plot(test_raw.loc[zoom_slice].index, pred_xgb_tuned.loc[zoom_slice], color=EMERALD, lw=2.1, label="XGBoost Tuned (Captures Synoptic Drops & Peaks)")
ax3_bot.set_title("B. High-Resolution Zoom: Pre-Monsoon Heatwaves & Monsoon Cooling Bursts (May – August 2025)", fontsize=11, fontweight="bold", color=NAVY, loc="left")
ax3_bot.set_ylabel("Daily Tmean (°C)", fontsize=9.5, fontweight="bold")
ax3_bot.set_xlabel("Evaluation Date (2025–2026 Test Horizon)", fontsize=9.5)
ax3_bot.legend(loc="lower left", fontsize=8.5, ncol=3)
ax3_bot.xaxis.set_major_locator(mdates.DayLocator(interval=15))
ax3_bot.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))

save_plot(fig3, "03_actual_vs_predicted_forecast.png")
print("      ✓ Figure 3: 03_actual_vs_predicted_forecast.png")

# --- FIGURE 04: RMSE, MAE, MAPE, R² Model Comparison Bar Chart ---
fig4, axes4 = plt.subplots(2, 2, figsize=(13.6, 8.2))
plt.subplots_adjust(hspace=0.52, wspace=0.24)

comp_order = [
    ("XGBoost (Tuned)", "XGBoost\n(Tuned)", EMERALD),
    ("XGBoost (Untuned Default)", "XGBoost\n(Untuned)", "#34D399"),
    ("Holt-Winters Damped", "HW Damped\n(P2 Best)", ORANGE),
    ("Holt-Winters Additive", "HW Additive", "#FBBF24"),
    ("XGBoost (Seasonal No-Lag 365d)", "XGBoost\n(No-Lag 365d)", PURPLE),
    ("SARIMAX (Fourier K=3, ARIMA(2,0,1))", "SARIMAX\n(Fourier K=3)", MID),
    ("Seasonal Naive", "Seasonal\nNaive", "#64748B"),
    ("ARIMA(2,1,2)", "ARIMA\n(2,1,2)", "#EF4444"),
    ("Naive (Persistence)", "Naive\n(Persist.)", "#94A3B8"),
]

m_keys = [k for k, _, _ in comp_order]
m_short = [s for _, s, _ in comp_order]
m_cols = [c for _, _, c in comp_order]

rmses_v = [COMPARATIVE_METRICS[k]["RMSE"] for k in m_keys]
maes_v = [COMPARATIVE_METRICS[k]["MAE"] for k in m_keys]
mapes_v = [COMPARATIVE_METRICS[k]["MAPE"] for k in m_keys]
r2s_v = [COMPARATIVE_METRICS[k]["R2"] for k in m_keys]


def draw_comp_bars(ax, values, title, ylabel, is_r2=False):
    bars = ax.bar(m_short, values, color=m_cols, edgecolor=NAVY, lw=0.8)
    ax.set_title(title, fontsize=10.5, fontweight="bold", color=NAVY, loc="left", pad=8)
    ax.set_ylabel(ylabel, fontsize=9)
    ax.tick_params(axis="x", rotation=22, labelsize=8.2)
    max_val = max(values)
    for b, v in zip(bars, values):
        h = b.get_height()
        if v >= 0:
            yp = h + (max_val * 0.025 if not is_r2 else 0.025)
            va = "bottom"
        else:
            yp = h - 0.035
            va = "top"
        ax.text(b.get_x() + b.get_width() / 2, yp, f"{v:.2f}" if not is_r2 else f"{v:.3f}",
                ha="center", va=va, fontsize=8, fontweight="bold")
    if is_r2:
        ax.set_ylim(-0.28, 1.12)
    else:
        ax.set_ylim(0, max_val * 1.18)


draw_comp_bars(axes4[0, 0], rmses_v, "A. Root Mean Squared Error (RMSE °C) — Lower is Better", "RMSE (°C)")
draw_comp_bars(axes4[0, 1], maes_v, "B. Mean Absolute Error (MAE °C) — Lower is Better", "MAE (°C)")
draw_comp_bars(axes4[1, 0], mapes_v, "C. Mean Absolute Percentage Error (MAPE %) — Lower is Better", "MAPE (%)")
draw_comp_bars(axes4[1, 1], r2s_v, "D. Explained Variance (R² Score) — Higher is Better", "R² Score", is_r2=True)

fig4.suptitle("Phase 3 vs. Phase 2 Quantitative Model Comparison (365-Day Out-of-Sample Holdout)", fontsize=13, fontweight="bold", color=NAVY, y=0.99)
save_plot(fig4, "04_rmse_and_metrics_comparison.png")
print("      ✓ Figure 4: 04_rmse_and_metrics_comparison.png")

# --- FIGURE 05: Residual Comparison Diagnostics (XGBoost vs. Holt-Winters Damped) ---
fig5, axes5 = plt.subplots(2, 2, figsize=(13.4, 8.0))
plt.subplots_adjust(hspace=0.38, wspace=0.24)

# Panel A: Residual Time Series Overlay
axes5[0, 0].plot(test_eval_df.index, test_eval_df["resid_hw_damped"], color=ORANGE, lw=1.1, alpha=0.75, label=f"Holt-Winters Damped (SD = 2.10 °C, Bias = +0.36 °C)")
axes5[0, 0].plot(test_eval_df.index, test_eval_df["resid_xgboost"], color=EMERALD, lw=1.3, label=f"XGBoost Tuned (SD = {xgb_resid_diag['std']:.2f} °C, Bias = {xgb_resid_diag['mean']:+.2f} °C)")
axes5[0, 0].axhline(0, color=ROSE, ls="--", lw=1.1)
axes5[0, 0].set_title("A. Daily Residual Trajectory (e_t = y_t - ŷ_t) Over 365 Test Days", fontsize=10.5, fontweight="bold", color=NAVY, loc="left")
axes5[0, 0].set_ylabel("Residual Error (°C)", fontsize=9)
axes5[0, 0].legend(loc="lower left", fontsize=8)
axes5[0, 0].xaxis.set_major_locator(mdates.MonthLocator(interval=2))
axes5[0, 0].xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))

# Panel B: Residual Error Distribution Density Comparison
sns.kdeplot(test_eval_df["resid_hw_damped"], ax=axes5[0, 1], color=ORANGE, fill=True, alpha=0.25, lw=2.0, label="Holt-Winters Damped Residuals")
sns.kdeplot(test_eval_df["resid_xgboost"], ax=axes5[0, 1], color=EMERALD, fill=True, alpha=0.35, lw=2.2, label="XGBoost Tuned Residuals")
axes5[0, 1].axvline(0, color=ROSE, ls="--", lw=1.1)
axes5[0, 1].set_title("B. Residual Error Density Contraction (XGBoost vs. HW Damped)", fontsize=10.5, fontweight="bold", color=NAVY, loc="left")
axes5[0, 1].set_xlabel("Forecast Error (°C)", fontsize=9)
axes5[0, 1].legend(loc="upper right", fontsize=8.5)

# Panel C: Seasonal RMSE Comparison
s_labels = SEASON_ORDER
s_xgb = [xgb_seasonal_perf[s]["RMSE"] for s in s_labels]
s_hwd = [m2_metrics["best_model"]["seasonal_breakdown"][s]["RMSE"] for s in s_labels]
x_pos = np.arange(len(s_labels))
w_s = 0.36
b_s1 = axes5[1, 0].bar(x_pos - w_s/2, s_hwd, width=w_s, color=ORANGE, edgecolor=NAVY, label="Phase 2 Best: HW Damped")
b_s2 = axes5[1, 0].bar(x_pos + w_s/2, s_xgb, width=w_s, color=EMERALD, edgecolor=NAVY, label="Phase 3 Champion: XGBoost")
for b in list(b_s1) + list(b_s2):
    axes5[1, 0].text(b.get_x() + b.get_width()/2, b.get_height() + 0.04, f"{b.get_height():.2f}", ha="center", fontsize=8, fontweight="bold")
axes5[1, 0].set_xticks(x_pos)
axes5[1, 0].set_xticklabels(s_labels, fontweight="bold")
axes5[1, 0].set_ylim(0, 2.85)
axes5[1, 0].set_title("C. Seasonal RMSE Comparison Across All 4 IMD Seasons", fontsize=10.5, fontweight="bold", color=NAVY, loc="left")
axes5[1, 0].set_ylabel("RMSE (°C)", fontsize=9)
axes5[1, 0].legend(loc="upper right", fontsize=8.5)

# Panel D: Extreme Weather Stress Test Comparison
ext_labels = ["Peak Heatwaves\n(Tmax >= 38°C, 45d)", "Severe Cold Snaps\n(Tmin <= 8°C, 20d)", "Full 365-Day\nHoldout"]
ext_hwd = [
    m2_metrics["best_model"]["extremes_breakdown"]["heatwave_extreme"]["MAE"],
    m2_metrics["best_model"]["extremes_breakdown"]["coldsnap_extreme"]["MAE"],
    COMPARATIVE_METRICS["Holt-Winters Damped"]["MAE"],
]
ext_xgb = [
    xgb_extremes_perf["heatwave_extreme"]["MAE"],
    xgb_extremes_perf["coldsnap_extreme"]["MAE"],
    COMPARATIVE_METRICS["XGBoost (Tuned)"]["MAE"],
]
x_e = np.arange(len(ext_labels))
b_e1 = axes5[1, 1].bar(x_e - w_s/2, ext_hwd, width=w_s, color=ORANGE, edgecolor=NAVY, label="HW Damped MAE (°C)")
b_e2 = axes5[1, 1].bar(x_e + w_s/2, ext_xgb, width=w_s, color=EMERALD, edgecolor=NAVY, label="XGBoost Tuned MAE (°C)")
for b in list(b_e1) + list(b_e2):
    axes5[1, 1].text(b.get_x() + b.get_width()/2, b.get_height() + 0.04, f"{b.get_height():.2f}", ha="center", fontsize=8, fontweight="bold")
axes5[1, 1].set_xticks(x_e)
axes5[1, 1].set_xticklabels(ext_labels, fontweight="bold")
axes5[1, 1].set_ylim(0, 2.45)
axes5[1, 1].set_title("D. Extreme Climatological Stress Test (MAE in °C)", fontsize=10.5, fontweight="bold", color=NAVY, loc="left")
axes5[1, 1].set_ylabel("MAE (°C)", fontsize=9)
axes5[1, 1].legend(loc="upper right", fontsize=8.5)

fig5.suptitle("Residual Comparison & Subgroup Stress Diagnostics: XGBoost vs. Holt-Winters Damped", fontsize=13, fontweight="bold", color=NAVY, y=0.99)
save_plot(fig5, "05_residual_comparison_diagnostics.png")
print("      ✓ Figure 5: 05_residual_comparison_diagnostics.png")

# --- FIGURE 06: Feature Importance Visualization & Ablation Impact ---
fig6, axes6 = plt.subplots(1, 3, figsize=(15.2, 5.2), gridspec_kw={"width_ratios": [1.05, 1.0, 1.15]})
plt.subplots_adjust(wspace=0.52)

top12_gain = fi_gain_ranked[:12][::-1]
axes6[0].barh([x["feature"] for x in top12_gain], [x["gain_pct"] for x in top12_gain], color=MID, edgecolor=NAVY, height=0.68)
axes6[0].set_title("A. Top 12 Features by Gain Contribution (%)", fontsize=10.5, fontweight="bold", color=NAVY, loc="left")
axes6[0].set_xlabel("Share of Total Squared-Error Reduction Gain (%)", fontsize=8.8)
max_g = max(x["gain_pct"] for x in top12_gain)
axes6[0].set_xlim(0, max_g * 1.22)
for i, x in enumerate(top12_gain):
    axes6[0].text(x["gain_pct"] + max_g * 0.02, i, f"{x['gain_pct']:.1f}%", va="center", fontsize=8, fontweight="bold")

top12_wt = fi_weight_ranked[:12][::-1]
axes6[1].barh([x["feature"] for x in top12_wt], [x["weight_pct"] for x in top12_wt], color=ORANGE, edgecolor=NAVY, height=0.68)
axes6[1].set_title("B. Top 12 Features by Split Frequency (%)", fontsize=10.5, fontweight="bold", color=NAVY, loc="left")
axes6[1].set_xlabel("Share of Tree Split Decisions (%)", fontsize=8.8)
max_w = max(x["weight_pct"] for x in top12_wt)
axes6[1].set_xlim(0, max_w * 1.22)
for i, x in enumerate(top12_wt):
    axes6[1].text(x["weight_pct"] + max_w * 0.02, i, f"{x['weight_pct']:.1f}%", va="center", fontsize=8, fontweight="bold")

# Panel C: Feature Group Ablation Study
ab_labels = [x["group"].replace(" (", "\n(") for x in ablation_results][::-1]
ab_rmses = [x["RMSE"] for x in ablation_results][::-1]
ab_cols = [EMERALD if i == 0 else (MID if i < 3 else PURPLE) for i in range(len(ab_rmses))]
bars_ab = axes6[2].barh(ab_labels, ab_rmses, color=ab_cols, edgecolor=NAVY, height=0.58)
axes6[2].set_title("C. Feature Ablation Impact on Test RMSE", fontsize=10.5, fontweight="bold", color=NAVY, loc="left")
axes6[2].set_xlabel("Out-of-Sample Test RMSE (°C)", fontsize=8.8)
axes6[2].set_xlim(0, max(ab_rmses) * 1.22)
for b, v in zip(bars_ab, ab_rmses):
    axes6[2].text(v + 0.04, b.get_y() + b.get_height()/2, f"{v:.3f} °C", va="center", fontsize=8.2, fontweight="bold")

fig6.suptitle("XGBoost Feature Importance & Progressive Feature-Group Ablation Analysis", fontsize=13, fontweight="bold", color=NAVY, y=1.01)
f6_saved = save_plot(fig6, "06_feature_importance_analysis.png")
# Also save directly to phase3_output/feature_importance.png as requested in project structure
import shutil
shutil.copyfile(f6_saved, os.path.join(OUT_DIR, "feature_importance.png"))
print("      ✓ Figure 6: 06_feature_importance_analysis.png & phase3_output/feature_importance.png")

# --- FIGURE 07: Where the Model Performs Poorly (Failure Mode & Error Hotspot Analysis) ---
fig7, axes7 = plt.subplots(1, 2, figsize=(13.4, 4.8))
plt.subplots_adjust(wspace=0.25)

# Panel A: Abs Error vs Day-to-Day Temperature Jump |Δy_t|
temp_jump = np.abs(test_eval_df["tmean"] - test_eval_df["tmean"].shift(1)).fillna(0.0)
axes7[0].scatter(temp_jump, test_eval_df["abs_err_xgboost"], c=temp_jump, cmap="YlOrRd", edgecolor=NAVY, alpha=0.8, s=38)
z_fit = np.polyfit(temp_jump, test_eval_df["abs_err_xgboost"], 1)
x_line = np.linspace(0, temp_jump.max(), 100)
axes7[0].plot(x_line, np.polyval(z_fit, x_line), color=ROSE, lw=2.0, ls="--", label=f"Linear Trend (r = {np.corrcoef(temp_jump, test_eval_df['abs_err_xgboost'])[0,1]:.2f})")
axes7[0].set_title("A. Why Errors Spike: Forecast Error vs. Sudden Daily Temp Shock |Δy_t|", fontsize=10.5, fontweight="bold", color=NAVY, loc="left")
axes7[0].set_xlabel("Day-to-Day Temperature Change |y_t - y_{t-1}| (°C)", fontsize=9.5)
axes7[0].set_ylabel("XGBoost Absolute Error |e_t| (°C)", fontsize=9.5)
axes7[0].legend(loc="upper left", fontsize=8.5)

# Panel B: Top 5 Worst Error Days (Reactive 1-Day Lag on Unannounced Squalls)
w_dates = [f"{r['date']}\n({r['season']})" for r in worst_days_records][::-1]
w_errs = [abs(r["residual"]) for r in worst_days_records][::-1]
w_signed = [r["residual"] for r in worst_days_records][::-1]
bars_w = axes7[1].barh(w_dates, w_errs, color="#EF4444", edgecolor=NAVY, height=0.55)
axes7[1].set_title("B. Top 5 Largest Error Days in Test Window (Convective Squalls)", fontsize=10.5, fontweight="bold", color=NAVY, loc="left")
axes7[1].set_xlabel("Absolute Forecast Error |e_t| (°C)", fontsize=9.5)
axes7[1].set_xlim(0, max(w_errs) * 1.28)
for b, v, sg in zip(bars_w, w_errs, w_signed):
    axes7[1].text(v + 0.08, b.get_y() + b.get_height()/2, f"|e| = {v:.2f} °C ({sg:+.2f}°)", va="center", fontsize=8.2, fontweight="bold")

fig7.suptitle("Diagnostic Failure Mode Analysis: Where & Why Autoregressive XGBoost Struggles", fontsize=12.5, fontweight="bold", color=NAVY, y=1.01)
save_plot(fig7, "07_error_hotspots_and_failure_modes.png")
print("      ✓ Figure 7: 07_error_hotspots_and_failure_modes.png")

# --- FIGURE 00: Phase 3 Executive Summary Dashboard ---
fig0 = plt.figure(figsize=(15.5, 9.8))
gs = fig0.add_gridspec(2, 3, height_ratios=[1.2, 1.0], hspace=0.36, wspace=0.32)

ax0_a = fig0.add_subplot(gs[0, :2])
ax0_a.plot(test_raw.index, y_test, color="#0F172A", lw=2.0, label="Actual Ground Truth")
ax0_a.plot(test_raw.index, m2_fc["pred_holt-winters_damped"], color=ORANGE, lw=1.8, ls="--", label=f"Phase 2 Best: HW Damped ({COMPARATIVE_METRICS['Holt-Winters Damped']['RMSE']:.2f} °C)")
ax0_a.plot(test_raw.index, pred_xgb_tuned, color=EMERALD, lw=2.0, label=f"Phase 3 Champion: XGBoost Tuned ({COMPARATIVE_METRICS['XGBoost (Tuned)']['RMSE']:.2f} °C)")
ax0_a.set_title("A. 365-Day Out-of-Sample Forecast Trajectory (19 Mar 2025 – 18 Mar 2026)", fontsize=11, fontweight="bold", color=NAVY, loc="left")
ax0_a.set_ylabel("Daily Tmean (°C)", fontsize=9.5)
ax0_a.legend(loc="lower left", fontsize=8.5, ncol=3)
ax0_a.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
ax0_a.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))

ax0_b = fig0.add_subplot(gs[0, 2])
b0 = ax0_b.barh(m_short[::-1], rmses_v[::-1], color=m_cols[::-1], edgecolor=NAVY, height=0.65)
ax0_b.set_title("B. Model RMSE Ranking (°C)", fontsize=11, fontweight="bold", color=NAVY, loc="left")
ax0_b.set_xlabel("RMSE (°C)", fontsize=9)
ax0_b.set_xlim(0, max(rmses_v) * 1.24)
for b, v in zip(b0, rmses_v[::-1]):
    ax0_b.text(v + 0.12, b.get_y() + b.get_height()/2, f"{v:.2f}", va="center", fontsize=8, fontweight="bold")

ax0_c = fig0.add_subplot(gs[1, 0])
top8_g = fi_gain_ranked[:8][::-1]
ax0_c.barh([x["feature"] for x in top8_g], [x["gain_pct"] for x in top8_g], color=MID, edgecolor=NAVY, height=0.62)
ax0_c.set_title("C. Top 8 XGBoost Features (Gain %)", fontsize=10.5, fontweight="bold", color=NAVY, loc="left")
ax0_c.set_xlabel("Gain Share (%)", fontsize=9)

ax0_d = fig0.add_subplot(gs[1, 1])
sns.kdeplot(test_eval_df["resid_hw_damped"], ax=ax0_d, color=ORANGE, fill=True, alpha=0.25, label="HW Damped")
sns.kdeplot(test_eval_df["resid_xgboost"], ax=ax0_d, color=EMERALD, fill=True, alpha=0.35, label="XGBoost Tuned")
ax0_d.axvline(0, color=ROSE, ls="--", lw=1.0)
ax0_d.set_title("D. Residual Error Contraction", fontsize=10.5, fontweight="bold", color=NAVY, loc="left")
ax0_d.set_xlabel("Residual (°C)", fontsize=9)
ax0_d.legend(loc="upper right", fontsize=8)

ax0_e = fig0.add_subplot(gs[1, 2])
ax0_e.bar(x_pos - w_s/2, s_hwd, width=w_s, color=ORANGE, edgecolor=NAVY, label="HW Damped")
ax0_e.bar(x_pos + w_s/2, s_xgb, width=w_s, color=EMERALD, edgecolor=NAVY, label="XGBoost")
ax0_e.set_xticks(x_pos)
ax0_e.set_xticklabels(s_labels, fontsize=8.5, fontweight="bold")
ax0_e.set_title("E. Seasonal RMSE Breakdown (°C)", fontsize=10.5, fontweight="bold", color=NAVY, loc="left")
ax0_e.set_ylabel("RMSE (°C)", fontsize=9)
ax0_e.legend(loc="upper right", fontsize=8)

fig0.suptitle("Delhi Urban Weather Dynamics (1996–2026) | Phase 3 Final Evaluation Executive Dashboard", fontsize=14, fontweight="bold", color=NAVY, y=0.98)
save_plot(fig0, "00_phase3_executive_dashboard.png")
print("      ✓ Figure 0: 00_phase3_executive_dashboard.png")

# =====================================================================
# 7. EXPORT METRICS JSON & GENERATE FINAL REPORT (PDF/DOCX) + PPTX
# =====================================================================
print("\n[7/7] Exporting phase3_output/metrics.json and building IEEE Report (PDF/DOCX) & Viva PPTX...")

metrics_payload = {
    "project_metadata": {
        "title": "Comparative Classical and Gradient Boosted (XGBoost) Time-Series Forecasting of Urban Weather Dynamics in Delhi (1996–2026)",
        "phase": "Phase 3: Final Project Evaluation (12 Marks)",
        "team": [
            {"name": "Dhruv Saini", "roll_no": "S24CSEU0818"},
            {"name": "Aarush Saxena", "roll_no": "S24CSEU1682"},
        ],
        "course": "CSET 369 – Time Series Analysis & Forecasting",
        "institution": "Bennett University",
        "total_days": int(len(daily)),
        "train_days_raw": int(len(train_raw)),
        "train_days_effective": int(len(X_train)),
        "test_days": int(len(X_test)),
        "train_range": [train_raw.index.min().strftime("%Y-%m-%d"), train_raw.index.max().strftime("%Y-%m-%d")],
        "test_range": [test_raw.index.min().strftime("%Y-%m-%d"), test_raw.index.max().strftime("%Y-%m-%d")],
        "zero_leakage_perturbation_max_diff": leakage_diff,
    },
    "engineered_features": {
        "count": len(feature_cols),
        "features": feature_cols,
        "groups": {
            "lags": ["lag_1", "lag_2", "lag_3", "lag_7", "lag_14", "lag_30", "lag_365"],
            "rolling_means_shifted_1d": ["roll_mean_7", "roll_mean_14", "roll_mean_30"],
            "rolling_stds_shifted_1d": ["roll_std_7", "roll_std_14", "roll_std_30"],
            "seasonal_calendar_harmonics": ["month", "dayofyear", "sin_doy_1", "cos_doy_1", "sin_doy_2", "cos_doy_2", "clim_doy_mean"],
            "momentum_and_exogenous_shifted_1d": ["temp_momentum_1d", "temp_anomaly_7d", "lag1_dtr", "lag1_humidity", "lag1_rain"],
        },
    },
    "hyperparameter_tuning": {
        "strategy": "5-Fold Expanding-Window TimeSeriesSplit (test_size = 365 days per fold)",
        "best_params": {
            "n_estimators": best_cv_cfg["n_estimators"],
            "max_depth": best_cv_cfg["max_depth"],
            "learning_rate": best_cv_cfg["learning_rate"],
            "subsample": best_cv_cfg["subsample"],
            "colsample_bytree": best_cv_cfg["colsample_bytree"],
        },
        "best_cv_rmse": best_cv_cfg["cv_rmse_mean"],
        "default_cv_rmse": default_cv_cfg["cv_rmse_mean"],
        "candidates": cv_results,
        "depth_sensitivity": depth_sweep,
    },
    "comparative_metrics_daily_365": COMPARATIVE_METRICS,
    "ablation_study": ablation_results,
    "feature_importance": {
        "gain_ranked": fi_gain_ranked,
        "weight_ranked": fi_weight_ranked,
    },
    "xgboost_diagnostics": {
        "residual_diagnostics": xgb_resid_diag,
        "seasonal_breakdown": xgb_seasonal_perf,
        "extremes_breakdown": xgb_extremes_perf,
        "worst_error_days": worst_days_records,
    },
    "best_overall_model": {
        "name": "XGBoost (Tuned)",
        "metrics": COMPARATIVE_METRICS["XGBoost (Tuned)"],
        "improvement_over_phase2_champion_pct": round(
            (COMPARATIVE_METRICS["Holt-Winters Damped"]["RMSE"] - COMPARATIVE_METRICS["XGBoost (Tuned)"]["RMSE"])
            / COMPARATIVE_METRICS["Holt-Winters Damped"]["RMSE"] * 100.0, 2
        ),
    },
}

with open(os.path.join(OUT_DIR, "metrics.json"), "w", encoding="utf-8") as f:
    json.dump(metrics_payload, f, indent=2)

from report_generator_p3 import (
    generate_ieee_pdf_report,
    generate_ieee_docx_report,
    generate_ieee_markdown_report,
    generate_phase3_presentation,
)

pdf_file = generate_ieee_pdf_report(metrics_payload, OUT_DIR, FIG_DIR)
docx_file = generate_ieee_docx_report(metrics_payload, OUT_DIR, FIG_DIR)
md_file = generate_ieee_markdown_report(metrics_payload, OUT_DIR)
pptx_file = generate_phase3_presentation(metrics_payload, OUT_DIR, FIG_DIR)

print(f"      ✓ Saved JSON Audit:          {os.path.join(OUT_DIR, 'metrics.json')}")
print(f"      ✓ Saved Forecast CSV:        {os.path.join(OUT_DIR, 'forecast_comparison.csv')}")
print(f"      ✓ Saved Model Comparison:    {os.path.join(OUT_DIR, 'model_comparison.csv')}")
print(f"      ✓ Saved Feature Importance:  {os.path.join(OUT_DIR, 'feature_importance.png')}")
print(f"      ✓ Saved IEEE Final PDF:      {pdf_file}")
print(f"      ✓ Saved IEEE Final DOCX:     {docx_file}")
print(f"      ✓ Saved IEEE Final Markdown: {md_file}")
print(f"      ✓ Saved Phase 3 Viva PPTX:   {pptx_file}")
print("\n" + "=" * 88)
print("✅ PHASE 3 PIPELINE EXECUTION COMPLETED SUCCESSFULLY!")
print("=" * 88)

