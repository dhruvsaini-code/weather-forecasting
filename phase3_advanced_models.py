#!/usr/bin/env python3
"""
Phase 3 Extended: Deep Learning (Simple RNN, LSTM, GRU), Ensemble Models, & Meta Prophet
======================================================================================
Implements and benchmarks all remaining Phase 3 advanced models on the EXACT same
chronological split and post-split causal preprocessing as Phase 2 & Phase 3 XGBoost:
  - Training:     1996-01-01 to 2025-03-18 (10,670 days)
  - Test Holdout: 2025-03-19 to 2026-03-18 (365 days)

Models Implemented:
  1. Simple RNN (PyTorch 2-layer Elman RNN, 30-day lookback, Rolling 1-Step)
  2. LSTM (PyTorch 2-layer Long Short-Term Memory, 30-day lookback, Rolling 1-Step)
  3. GRU (PyTorch 2-layer Gated Recurrent Unit, 30-day lookback, Rolling 1-Step)
  4. ML Ensemble (XGBoost + RandomForest + HistGradientBoosting Weighted Blend, Rolling 1-Step)
  5. Hybrid 365d Ensemble (Holt-Winters Damped + XGBoost Direct Seasonal, Fixed 365-Day)
  6. Meta / Facebook Prophet (Additive Trend + Yearly Fourier Seasonality, Fixed 365-Day)

Outputs updated cleanly:
  - phase3_output/forecast_comparison.csv (adds columns for RNN, LSTM, GRU, Ensemble, Prophet)
  - phase3_output/model_comparison.csv (adds all new models with horizon regime labels)
  - phase3_output/metrics.json (merges into comparative_metrics & horizon_comparison)
  - phase3_output/figures/10_deep_learning_prophet_ensemble_comparison.png (200 DPI)

Team: Dhruv Saini (S24CSEU0818) & Aarush Saxena (S24CSEU1682)
"""

import os
import json
import time
import warnings
import numpy as np
import pandas as pd

os.environ.setdefault("MPLCONFIGDIR", "/tmp")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from xgboost import XGBRegressor
from prophet import Prophet

warnings.filterwarnings("ignore")

SEASONS = {
    12: "Winter", 1: "Winter", 2: "Winter",
    3: "Summer", 4: "Summer", 5: "Summer",
    6: "Monsoon", 7: "Monsoon", 8: "Monsoon", 9: "Monsoon",
    10: "Post-monsoon", 11: "Post-monsoon",
}


def compute_metrics(y_true, y_pred):
    y_t = np.asarray(y_true, dtype=float)
    y_p = np.asarray(y_pred, dtype=float)
    err = y_t - y_p
    rmse = float(np.sqrt(np.mean(err ** 2)))
    mae = float(np.mean(np.abs(err)))
    mape = float(np.mean(np.abs(err) / np.clip(np.abs(y_t), 1e-6, None)) * 100.0)
    ss_res = float(np.sum(err ** 2))
    ss_tot = float(np.sum((y_t - np.mean(y_t)) ** 2))
    r2 = float(1.0 - ss_res / ss_tot)
    max_err = float(np.max(np.abs(err)))
    bias = float(np.mean(err))
    return {
        "RMSE": round(rmse, 4),
        "MAE": round(mae, 4),
        "MAPE": round(mape, 3),
        "R2": round(r2, 4),
        "Max_Error": round(max_err, 3),
        "Bias": round(bias, 4),
    }


class SequenceForecastNet(nn.Module):
    """Unified PyTorch recurrent architecture supporting Simple RNN, LSTM, and GRU."""
    def __init__(self, cell_type, input_dim, hidden_dim=64, num_layers=2, dropout=0.15):
        super().__init__()
        rnn_cls = {"RNN": nn.RNN, "LSTM": nn.LSTM, "GRU": nn.GRU}[cell_type]
        self.rnn = rnn_cls(
            input_dim,
            hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.head = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
        )

    def forward(self, x):
        out, _ = self.rnn(x)
        return self.head(out[:, -1, :]).squeeze(-1)


def train_recurrent_model(
    cell_type,
    X_seq_train,
    y_seq_train,
    X_seq_val,
    y_seq_val,
    X_seq_test,
    hidden_dim=64,
    num_layers=2,
    epochs=28,
    batch_size=128,
    lr=1e-3,
    seed=42,
):
    torch.manual_seed(seed)
    np.random.seed(seed)
    device = torch.device("cpu")

    model = SequenceForecastNet(
        cell_type=cell_type,
        input_dim=X_seq_train.shape[2],
        hidden_dim=hidden_dim,
        num_layers=num_layers,
        dropout=0.15,
    ).to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=3)
    loss_fn = nn.MSELoss()

    train_ds = TensorDataset(torch.tensor(X_seq_train, dtype=torch.float32), torch.tensor(y_seq_train, dtype=torch.float32))
    train_dl = DataLoader(train_ds, batch_size=batch_size, shuffle=True)

    X_val_t = torch.tensor(X_seq_val, dtype=torch.float32, device=device)
    y_val_t = torch.tensor(y_seq_val, dtype=torch.float32, device=device)
    X_test_t = torch.tensor(X_seq_test, dtype=torch.float32, device=device)

    best_val_loss = float("inf")
    best_state = None
    for ep in range(epochs):
        model.train()
        for xb, yb in train_dl:
            optimizer.zero_grad()
            preds = model(xb)
            loss = loss_fn(preds, yb)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

        model.eval()
        with torch.no_grad():
            val_loss = float(loss_fn(model(X_val_t), y_val_t).item())
        scheduler.step(val_loss)
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_state = {k: v.clone() for k, v in model.state_dict().items()}

    if best_state is not None:
        model.load_state_dict(best_state)
    model.eval()
    with torch.no_grad():
        test_preds = model(X_test_t).cpu().numpy()
    return test_preds, float(np.sqrt(best_val_loss))


def run_extended_models():
    print("=" * 88)
    print("🧠 PHASE 3 EXTENDED: RNN, LSTM, GRU, ENSEMBLES & META PROPHET")
    print("=" * 88)

    daily = pd.read_csv(os.path.join("milestone1_output", "daily_series.csv"), parse_dates=["date"], index_col="date").sort_index()
    TEST_DAYS = 365
    train_raw = daily.iloc[:-TEST_DAYS].copy()
    test_raw = daily.iloc[-TEST_DAYS:].copy()

    # Strictly causal post-split forward-fill
    for c in ["tmean", "tmax", "tmin", "humidity"]:
        if pd.isna(train_raw[c].iloc[0]):
            train_raw.iloc[0, train_raw.columns.get_loc(c)] = float(train_raw[c].median())
        train_raw[c] = train_raw[c].ffill()
    train_raw["rain"] = train_raw["rain"].fillna(0.0)

    daily = pd.concat([train_raw, test_raw], axis=0)
    for c in ["tmean", "tmax", "tmin", "humidity"]:
        daily[c] = daily[c].ffill()
    daily["rain"] = daily["rain"].fillna(0.0)
    train_raw = daily.iloc[:-TEST_DAYS].copy()
    test_raw = daily.iloc[-TEST_DAYS:].copy()
    y_test = test_raw["tmean"].values

    fc_path = os.path.join("phase3_output", "forecast_comparison.csv")
    df_fc = pd.read_csv(fc_path, parse_dates=["date"], index_col="date").sort_index()
    with open(os.path.join("phase3_output", "metrics.json"), "r", encoding="utf-8") as f:
        metrics_json = json.load(f)

    # =====================================================================
    # 1. DEEP LEARNING SEQUENCE MODELS: Simple RNN, LSTM, GRU (30-Day Lookback)
    # =====================================================================
    print("\n[1/3] Training Deep Learning Sequence Models (Simple RNN, LSTM, GRU | 30-day lookback)...")
    seq_df = pd.DataFrame(index=daily.index)
    seq_df["tmean"] = daily["tmean"]
    seq_df["dtr"] = daily["tmax"] - daily["tmin"]
    seq_df["humidity"] = daily["humidity"]
    seq_df["rain"] = daily["rain"]
    doy = daily.index.dayofyear
    seq_df["sin_doy_1"] = np.sin(2.0 * np.pi * doy / 365.25)
    seq_df["cos_doy_1"] = np.cos(2.0 * np.pi * doy / 365.25)

    # Fit StandardScaler strictly on training rows (zero test leakage)
    scaler = StandardScaler()
    scaler.fit(seq_df.iloc[:-TEST_DAYS].values)
    scaled_all = scaler.transform(seq_df.values)

    LOOKBACK = 30
    X_seqs, y_seqs = [], []
    target_vals = daily["tmean"].values
    for i in range(LOOKBACK, len(daily)):
        X_seqs.append(scaled_all[i - LOOKBACK : i])  # strictly t-30 .. t-1
        y_seqs.append(target_vals[i])
    X_seqs = np.asarray(X_seqs, dtype=np.float32)
    y_seqs = np.asarray(y_seqs, dtype=np.float32)

    X_train_all = X_seqs[:-TEST_DAYS]
    y_train_all = y_seqs[:-TEST_DAYS]
    X_test_seq = X_seqs[-TEST_DAYS:]

    # Chronological validation tail (last 730 days of training set)
    VAL_LEN = 730
    X_tr_seq, y_tr_seq = X_train_all[:-VAL_LEN], y_train_all[:-VAL_LEN]
    X_va_seq, y_va_seq = X_train_all[-VAL_LEN:], y_train_all[-VAL_LEN:]

    dl_preds = {}
    dl_val_rmses = {}
    for cell, hdim, ep in [("RNN", 48, 28), ("LSTM", 64, 30), ("GRU", 64, 30)]:
        t0 = time.time()
        preds, v_rmse = train_recurrent_model(
            cell, X_tr_seq, y_tr_seq, X_va_seq, y_va_seq, X_test_seq,
            hidden_dim=hdim, num_layers=2, epochs=ep, batch_size=128, lr=1e-3, seed=42
        )
        dl_preds[cell] = preds
        dl_val_rmses[cell] = v_rmse
        met = compute_metrics(y_test, preds)
        print(f"      ✓ {cell:<4s} | Val RMSE={v_rmse:.3f}°C | Test RMSE={met['RMSE']:.3f}°C | MAE={met['MAE']:.3f}°C | R2={met['R2']:.4f} ({time.time()-t0:.1f}s)")

    # =====================================================================
    # 2. ENSEMBLE MODELS (Rolling 1-Step ML Stacking + Fixed 365d Hybrid)
    # =====================================================================
    print("\n[2/3] Training Ensemble Models (XGBoost+RF+HGB Stacking & Fixed-365d Hybrid)...")
    doy_clim_train = train_raw.groupby(train_raw.index.dayofyear)["tmean"].mean()
    feat_df = pd.DataFrame(index=daily.index)
    feat_df["tmean"] = daily["tmean"]
    for l in [1, 2, 3, 7, 14, 30, 365]:
        feat_df[f"lag_{l}"] = daily["tmean"].shift(l)
    sh = daily["tmean"].shift(1)
    for w in [7, 14, 30]:
        feat_df[f"roll_mean_{w}"] = sh.rolling(w, min_periods=w).mean()
        feat_df[f"roll_std_{w}"] = sh.rolling(w, min_periods=w).std()
    feat_df["month"] = daily.index.month
    feat_df["dayofyear"] = daily.index.dayofyear
    feat_df["sin_doy_1"] = np.sin(2.0 * np.pi * feat_df["dayofyear"] / 365.25)
    feat_df["cos_doy_1"] = np.cos(2.0 * np.pi * feat_df["dayofyear"] / 365.25)
    feat_df["sin_doy_2"] = np.sin(4.0 * np.pi * feat_df["dayofyear"] / 365.25)
    feat_df["cos_doy_2"] = np.cos(4.0 * np.pi * feat_df["dayofyear"] / 365.25)
    feat_df["clim_doy_mean"] = feat_df["dayofyear"].map(doy_clim_train).astype(float)
    feat_df["temp_momentum_1d"] = daily["tmean"].shift(1) - daily["tmean"].shift(2)
    feat_df["temp_anomaly_7d"] = daily["tmean"].shift(1) - feat_df["roll_mean_7"]
    feat_df["lag1_dtr"] = (daily["tmax"] - daily["tmin"]).shift(1)
    feat_df["lag1_humidity"] = daily["humidity"].shift(1)
    feat_df["lag1_rain"] = daily["rain"].shift(1)

    clean_f = feat_df.dropna().copy()
    fcols = [c for c in clean_f.columns if c != "tmean"]
    tr_f = clean_f.iloc[:-TEST_DAYS]
    te_f = clean_f.iloc[-TEST_DAYS:]

    bp = metrics_json["hyperparameter_tuning"]["best_params"]
    m_xgb = XGBRegressor(
        n_estimators=bp["n_estimators"], max_depth=bp["max_depth"],
        learning_rate=bp["learning_rate"], subsample=bp["subsample"],
        colsample_bytree=bp["colsample_bytree"], random_state=42, n_jobs=4
    )
    m_rf = RandomForestRegressor(n_estimators=180, max_depth=12, min_samples_leaf=4, random_state=42, n_jobs=4)
    m_hgb = HistGradientBoostingRegressor(max_iter=300, max_depth=5, learning_rate=0.04, random_state=42)

    # Fit base learners on training[:-365] to learn Ridge stacking weights strictly without test leakage
    tr_sub_X, tr_sub_y = tr_f[fcols].iloc[:-365], tr_f["tmean"].iloc[:-365]
    va_sub_X, va_sub_y = tr_f[fcols].iloc[-365:], tr_f["tmean"].iloc[-365:]
    m_xgb.fit(tr_sub_X, tr_sub_y)
    m_rf.fit(tr_sub_X, tr_sub_y)
    m_hgb.fit(tr_sub_X, tr_sub_y)
    meta_X_val = np.column_stack([m_xgb.predict(va_sub_X), m_rf.predict(va_sub_X), m_hgb.predict(va_sub_X)])
    meta_ridge = Ridge(alpha=1.0, positive=True).fit(meta_X_val, va_sub_y)
    stack_weights = meta_ridge.coef_ / np.sum(meta_ridge.coef_)

    # Refit all 3 base learners on full training set
    m_xgb.fit(tr_f[fcols], tr_f["tmean"])
    m_rf.fit(tr_f[fcols], tr_f["tmean"])
    m_hgb.fit(tr_f[fcols], tr_f["tmean"])
    pred_ens_1step = (
        stack_weights[0] * m_xgb.predict(te_f[fcols])
        + stack_weights[1] * m_rf.predict(te_f[fcols])
        + stack_weights[2] * m_hgb.predict(te_f[fcols])
    )
    met_ens1 = compute_metrics(y_test, pred_ens_1step)
    print(f"      ✓ Ensemble (XGB+RF+HGB Stacking, 1-Step) | Weights={[round(float(w),3) for w in stack_weights]} | Test RMSE={met_ens1['RMSE']:.3f}°C | R2={met_ens1['R2']:.4f}")

    # Hybrid Fixed-365d Ensemble: 0.65 * Holt-Winters Damped + 0.35 * XGBoost Direct Seasonal (zero test obs)
    pred_hybrid_365 = 0.65 * df_fc["pred_holt-winters_damped"].values + 0.35 * df_fc["pred_xgboost_seasonal_365d"].values
    met_hyb365 = compute_metrics(y_test, pred_hybrid_365)
    print(f"      ✓ Hybrid Ensemble (HW Damped + XGB Direct, 365d) | Test RMSE={met_hyb365['RMSE']:.3f}°C | R2={met_hyb365['R2']:.4f}")

    # =====================================================================
    # 3. FACEBOOK / META PROPHET (Fixed 365-Day Multi-Step)
    # =====================================================================
    print("\n[3/3] Training Meta / Facebook Prophet (Fixed 365-Day Horizon)...")
    prophet_train = pd.DataFrame({
        "ds": train_raw.index,
        "y": train_raw["tmean"].values,
    })
    m_prophet = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False,
        changepoint_prior_scale=0.05,
        seasonality_mode="additive",
    )
    m_prophet.fit(prophet_train)
    future_df = pd.DataFrame({"ds": test_raw.index})
    prophet_fc = m_prophet.predict(future_df)
    pred_prophet = prophet_fc["yhat"].values
    met_prophet = compute_metrics(y_test, pred_prophet)
    print(f"      ✓ Meta Prophet (Fixed 365d) | Test RMSE={met_prophet['RMSE']:.3f}°C | MAE={met_prophet['MAE']:.3f}°C | R2={met_prophet['R2']:.4f}")

    # =====================================================================
    # 4. SAVE UPDATED CSVs, METRICS.JSON, AND FIGURE 10
    # =====================================================================
    df_fc["pred_rnn_1step"] = np.round(dl_preds["RNN"], 4)
    df_fc["pred_lstm_1step"] = np.round(dl_preds["LSTM"], 4)
    df_fc["pred_gru_1step"] = np.round(dl_preds["GRU"], 4)
    df_fc["pred_ensemble_stacking_1step"] = np.round(pred_ens_1step, 4)
    df_fc["pred_ensemble_hybrid_365d"] = np.round(pred_hybrid_365, 4)
    df_fc["pred_prophet_365d"] = np.round(pred_prophet, 4)
    df_fc.to_csv(fc_path)

    new_metrics = {
        "Ensemble Stacking (XGB+RF+HGB, 1-Step)": met_ens1,
        "GRU (Deep Learning, Rolling 1-Step)": compute_metrics(y_test, dl_preds["GRU"]),
        "LSTM (Deep Learning, Rolling 1-Step)": compute_metrics(y_test, dl_preds["LSTM"]),
        "Simple RNN (Deep Learning, Rolling 1-Step)": compute_metrics(y_test, dl_preds["RNN"]),
        "Hybrid Ensemble (HW Damped + XGB Direct, 365d)": met_hyb365,
        "Meta Prophet (Fixed 365d)": met_prophet,
    }
    metrics_json["comparative_metrics_daily_365"].update(new_metrics)
    metrics_json["deep_learning_and_prophet_details"] = {
        "lookback_days": LOOKBACK,
        "dl_features": ["tmean", "dtr", "humidity", "rain", "sin_doy_1", "cos_doy_1"],
        "dl_validation_rmse": dl_val_rmses,
        "ensemble_stacking_weights": {
            "XGBoost_Tuned": round(float(stack_weights[0]), 4),
            "RandomForest": round(float(stack_weights[1]), 4),
            "HistGradientBoosting": round(float(stack_weights[2]), 4),
        },
        "hybrid_365d_weights": {"Holt_Winters_Damped": 0.65, "XGBoost_Direct_Seasonal": 0.35},
        "prophet_config": {"yearly_seasonality": True, "weekly_seasonality": False, "changepoint_prior_scale": 0.05},
    }
    metrics_json["horizon_comparison"]["rolling_1day_ahead"]["models"].update({
        "Ensemble Stacking (XGB+RF+HGB, 1-Step)": met_ens1,
        "GRU (Deep Learning, Rolling 1-Step)": new_metrics["GRU (Deep Learning, Rolling 1-Step)"],
        "LSTM (Deep Learning, Rolling 1-Step)": new_metrics["LSTM (Deep Learning, Rolling 1-Step)"],
        "Simple RNN (Deep Learning, Rolling 1-Step)": new_metrics["Simple RNN (Deep Learning, Rolling 1-Step)"],
    })
    metrics_json["horizon_comparison"]["fixed_365day_multistep"]["models"].update({
        "Hybrid Ensemble (HW Damped + XGB Direct, 365d)": met_hyb365,
        "Meta Prophet (Fixed 365d)": met_prophet,
    })

    with open(os.path.join("phase3_output", "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics_json, f, indent=2)

    # Update model_comparison.csv
    comp_rows = []
    for k, v in metrics_json["comparative_metrics_daily_365"].items():
        hz = "Rolling 1-Day-Ahead" if ("1-Step" in k or k.startswith("XGBoost (Tuned") or k.startswith("XGBoost (Untuned")) else "Fixed 365-Day Multi-Step"
        comp_rows.append({"Model": k, "Horizon_Regime": hz, **v})
    comp_df = pd.DataFrame(comp_rows).sort_values(["Horizon_Regime", "RMSE"])
    comp_df.to_csv(os.path.join("phase3_output", "model_comparison.csv"), index=False)

    # Generate Figure 10: Deep Learning (RNN, LSTM, GRU), Ensembles & Meta Prophet Comparison
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.4), dpi=200, facecolor="#F8FAFC")
    ax1, ax2 = axes
    ax1.plot(df_fc.index, y_test, color="#1B2320", lw=1.3, alpha=0.85, label="Actual Ground Truth")
    ax1.plot(df_fc.index, pred_ens_1step, color="#0D7A52", lw=1.4, label=f"Ensemble Stacking 1-Step ({met_ens1['RMSE']:.3f}°C)")
    ax1.plot(df_fc.index, dl_preds["GRU"], color="#2563EB", lw=1.1, alpha=0.85, label=f"GRU 1-Step ({new_metrics['GRU (Deep Learning, Rolling 1-Step)']['RMSE']:.3f}°C)")
    ax1.plot(df_fc.index, dl_preds["LSTM"], color="#7C3AED", lw=1.0, alpha=0.75, label=f"LSTM 1-Step ({new_metrics['LSTM (Deep Learning, Rolling 1-Step)']['RMSE']:.3f}°C)")
    ax1.plot(df_fc.index, pred_prophet, color="#E11D48", lw=1.3, ls="--", label=f"Meta Prophet 365d ({met_prophet['RMSE']:.3f}°C)")
    ax1.set_title("A. Deep Learning (GRU/LSTM), Ensemble & Meta Prophet vs. Actual (365d)", fontsize=10.5, fontweight="bold", color="#0B1F3A", loc="left")
    ax1.set_ylabel("Daily Mean Temp (°C)", fontsize=9, fontweight="bold")
    ax1.legend(loc="lower left", fontsize=7.5, frameon=True)
    ax1.grid(True, linestyle="--", alpha=0.35)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))

    bar_names = [
        "Ensemble Stack (1s)",
        "XGBoost Tuned (1s)",
        "GRU (1s)",
        "LSTM (1s)",
        "Simple RNN (1s)",
        "Hybrid Ens. (365d)",
        "HW Damped (365d)",
        "XGB Direct (365d)",
        "Meta Prophet (365d)",
    ][::-1]
    bar_vals = [
        met_ens1["RMSE"],
        metrics_json["comparative_metrics_daily_365"]["XGBoost (Tuned)"]["RMSE"],
        new_metrics["GRU (Deep Learning, Rolling 1-Step)"]["RMSE"],
        new_metrics["LSTM (Deep Learning, Rolling 1-Step)"]["RMSE"],
        new_metrics["Simple RNN (Deep Learning, Rolling 1-Step)"]["RMSE"],
        met_hyb365["RMSE"],
        metrics_json["comparative_metrics_daily_365"]["Holt-Winters Damped"]["RMSE"],
        metrics_json["comparative_metrics_daily_365"]["XGBoost (Seasonal No-Lag 365d)"]["RMSE"],
        met_prophet["RMSE"],
    ][::-1]
    bar_cols = ["#0D7A52", "#10B981", "#2563EB", "#7C3AED", "#64748B", "#D97706", "#F59E0B", "#8B5CF6", "#E11D48"][::-1]
    yp = np.arange(len(bar_names))
    bs = ax2.barh(yp, bar_vals, color=bar_cols, height=0.62)
    for b_item, v in zip(bs, bar_vals):
        ax2.text(v + 0.04, b_item.get_y() + b_item.get_height()/2, f"{v:.3f} °C", va="center", fontsize=8, fontweight="bold")
    ax2.set_yticks(yp)
    ax2.set_yticklabels(bar_names, fontsize=8.5)
    ax2.set_xlim(0, max(bar_vals) + 0.55)
    ax2.set_xlabel("Out-of-Sample RMSE (°C)", fontsize=9, fontweight="bold")
    ax2.set_title("B. Complete Phase 3 Advanced Model Family RMSE Comparison", fontsize=10.5, fontweight="bold", color="#0B1F3A", loc="left")
    ax2.grid(True, axis="x", linestyle="--", alpha=0.35)

    plt.tight_layout()
    fig10_path = os.path.join("phase3_output", "figures", "10_deep_learning_prophet_ensemble_comparison.png")
    fig.savefig(fig10_path, dpi=200)
    plt.close(fig)
    print(f"\n✓ Saved updated metrics, CSVs, and {fig10_path}")


if __name__ == "__main__":
    run_extended_models()

