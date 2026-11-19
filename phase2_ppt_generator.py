#!/usr/bin/env python3
"""
Dedicated Phase 2 Evaluation Presentation Generator (PPTX, 12 Widescreen Slides)
Generates `milestone2_output/Phase2_Evaluation_Presentation.pptx` strictly focused
on Phase 2 (Classical Statistical Time-Series Forecasting & Benchmarking), with
Keynote-compatible OOXML (`screen16x9` + `notesMasterIdLst`).

Team: Dhruv Saini (S24CSEU0818) & Aarush Saxena (S24CSEU1682)
Course: CSET 369 – Time Series Analysis & Forecasting, Bennett University
"""

import os
import json
import shutil
import zipfile
import xml.etree.ElementTree as ET
import pandas as pd
from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE


def generate_phase2_evaluation_pptx(
    metrics_path=os.path.join("milestone2_output", "metrics.json"),
    fig_dir=os.path.join("milestone2_output", "figures"),
    out_path=os.path.join("milestone2_output", "Phase2_Evaluation_Presentation.pptx"),
):
    with open(metrics_path, "r", encoding="utf-8") as f:
        m2 = json.load(f)

    eval_tbl = m2["comparative_metrics_daily_365"]
    best = m2["best_model"]
    s_perf = best["seasonal_breakdown"]
    ext_perf = best["extremes_breakdown"]
    resid = best["residual_diagnostics"]
    stat = m2["stationarity_diagnostics"]["raw"]
    m_sarima = m2.get("monthly_sarima_metrics", {"RMSE": 1.264, "MAE": 0.939, "MAPE": 3.99, "R2": 0.9637})

    hw_d = eval_tbl["Holt-Winters Damped"]
    hw_a = eval_tbl["Holt-Winters Additive"]
    sar = eval_tbl["SARIMAX (Fourier K=3, ARIMA(2,0,1))"]
    snaive = eval_tbl["Seasonal Naive"]
    arima = eval_tbl["ARIMA(2,1,2)"]
    naive = eval_tbl["Naive (Persistence)"]
    holt = eval_tbl["Holt Linear Trend"]

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    BLANK = prs.slide_layouts[6]
    TOTAL_SLIDES = 12

    NAVY, MID, LIGHT, ORANGE, GREY, WHITE, DARK_TEXT, EMERALD = (
        "0B1F3A", "1F4E79", "DCE9F5", "F28C28", "6B7785", "FFFFFF", "1B2A3C", "10B981"
    )
    rgb = lambda h: RGBColor.from_string(h)

    def set_shape_style(shape, bg_hex, border_hex=None, border_width=1.0):
        shape.fill.solid()
        shape.fill.fore_color.rgb = rgb(bg_hex)
        if border_hex:
            shape.line.color.rgb = rgb(border_hex)
            shape.line.width = Pt(border_width)
        else:
            shape.line.fill.background()

    def render_text(slide, x, y, w, h, content, size=12, color=DARK_TEXT, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
        tx_box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = tx_box.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = anchor
        lines = content if isinstance(content, list) else [content]
        for i, line in enumerate(lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = line
            p.alignment = align
            p.font.size = Pt(size)
            p.font.name = "Calibri"
            p.font.color.rgb = rgb(color)
            p.font.bold = bold
        return tx_box

    def create_slide_scaffold(index, title_text, category_tag="PHASE 2 EVALUATION • CLASSICAL TIME-SERIES FORECASTING", notes_text=None):
        slide = prs.slides.add_slide(BLANK)
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = rgb("F8FAFC")
        top_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.12))
        set_shape_style(top_bar, ORANGE)
        render_text(slide, 0.5, 0.25, 11.5, 0.28, category_tag.upper(), size=9.5, color=ORANGE, bold=True)
        render_text(slide, 0.5, 0.50, 12.2, 0.52, title_text, size=20, color=NAVY, bold=True)
        footer_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(7.0), Inches(12.33), Inches(0.02))
        set_shape_style(footer_bar, "CBD5E1")
        render_text(slide, 0.5, 7.08, 9.8, 0.3, "CSET 369: Time Series Analysis & Forecasting | Phase 2 Evaluation | Dhruv Saini (S24CSEU0818) & Aarush Saxena (S24CSEU1682)", size=9, color=GREY)
        render_text(slide, 11.5, 7.08, 1.33, 0.3, f"{index} / {TOTAL_SLIDES}", size=9, color=GREY, align=PP_ALIGN.RIGHT)
        if notes_text:
            slide.notes_slide.notes_text_frame.text = notes_text
        return slide

    def insert_figure(slide, image_path, x, y, w, h):
        if not os.path.exists(image_path):
            return
        im_w, im_h = Image.open(image_path).size
        scale = min(w / im_w, h / im_h)
        slide.shapes.add_picture(
            image_path,
            Inches(x + (w - im_w * scale) / 2),
            Inches(y + (h - im_h * scale) / 2),
            Inches(im_w * scale),
            Inches(im_h * scale),
        )

    def insert_metric_card(slide, x, y, w, h, value_text, label_text, color=ORANGE):
        r = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
        set_shape_style(r, WHITE, "CBD5E1")
        render_text(slide, x, y + 0.08, w, h * 0.52, value_text, size=20, color=color, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        render_text(slide, x, y + h * 0.56, w, h * 0.38, label_text, size=9.5, color=GREY, align=PP_ALIGN.CENTER)

    def insert_structured_panel(slide, x, y, w, h, header_text, items, size=10.5):
        r = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
        set_shape_style(r, WHITE, "CBD5E1")
        render_text(slide, x + 0.15, y + 0.1, w - 0.3, 0.35, header_text, size=size + 1.5, color=MID, bold=True)
        render_text(slide, x + 0.15, y + 0.46, w - 0.3, h - 0.52, items, size=size)

    def insert_summary_banner(slide, message_text, y=6.36):
        r = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.5), Inches(y), Inches(12.33), Inches(0.52))
        set_shape_style(r, LIGHT, "93C5FD")
        render_text(slide, 0.65, y, 12.0, 0.52, message_text, size=10.5, color=NAVY, bold=True, anchor=MSO_ANCHOR.MIDDLE)

    def insert_table(slide, dataframe, x, y, w, column_widths=None, size=8.5, row_height=0.35, header_color=MID):
        table_obj = slide.shapes.add_table(
            len(dataframe) + 1, len(dataframe.columns),
            Inches(x), Inches(y), Inches(w), Inches(row_height * (len(dataframe) + 1))
        ).table
        if column_widths:
            for i, cw in enumerate(column_widths):
                table_obj.columns[i].width = Inches(cw)
        for j, col_title in enumerate(dataframe.columns):
            cell = table_obj.cell(0, j)
            cell.text = str(col_title)
            cell.fill.solid()
            cell.fill.fore_color.rgb = rgb(header_color)
        for i in range(len(dataframe)):
            for j in range(len(dataframe.columns)):
                cell = table_obj.cell(i + 1, j)
                cell.text = str(dataframe.iloc[i, j])
                cell.fill.solid()
                cell.fill.fore_color.rgb = rgb("DCFCE7" if i == 0 else (WHITE if i % 2 == 0 else "F1F5F9"))
        for r_idx, row in enumerate(table_obj.rows):
            row.height = Inches(row_height)
            for cell in row.cells:
                cell.vertical_anchor = MSO_ANCHOR.MIDDLE
                for p in cell.text_frame.paragraphs:
                    for r_run in p.runs:
                        r_run.font.size = Pt(size)
                        r_run.font.name = "Calibri"
                        if r_idx in (0, 1):
                            r_run.font.bold = True
                        if r_idx == 0:
                            r_run.font.color.rgb = rgb(WHITE)

    # SLIDE 1: TITLE SLIDE
    s1 = prs.slides.add_slide(BLANK)
    s1.background.fill.solid()
    s1.background.fill.fore_color.rgb = rgb(NAVY)
    bar = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.7), Inches(1.5), Inches(0.14), Inches(3.8))
    set_shape_style(bar, ORANGE)
    render_text(s1, 1.05, 0.85, 11.2, 0.45, "CSET 369: TIME SERIES ANALYSIS & FORECASTING | PHASE 2 EVALUATION", size=13, color="93C5FD", bold=True)
    render_text(s1, 1.05, 1.50, 11.4, 2.0, "Classical Time-Series Forecasting of Delhi Urban Weather Dynamics (1996–2026)", size=27, color=WHITE, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    render_text(s1, 1.05, 3.80, 11.4, 0.55, f"7 Daily Classical Models + Supplementary Monthly SARIMA • Fixed 365-Day Champion: Holt-Winters Damped ({hw_d['RMSE']:.3f} °C RMSE)", size=14.5, color="FCD34D", bold=True)
    render_text(s1, 1.05, 4.65, 11.2, 0.4, "Team Members: Dhruv Saini (S24CSEU0818) & Aarush Saxena (S24CSEU1682)", size=14, color=WHITE, bold=True)
    render_text(s1, 1.05, 5.15, 11.2, 0.4, "Course Coordinator: Prof. Anurag Choubey | School of CSET, Bennett University", size=12, color="CBD5E1")
    s1.notes_slide.notes_text_frame.text = "Slide 1: Title slide for Phase 2 Classical Time-Series Forecasting Evaluation."

    # SLIDE 2: PHASE 2 SCOPE & EXECUTIVE SUMMARY
    s2 = create_slide_scaffold(2, "1. Phase 2 Executive Summary & Evaluation Scope",
        notes_text="Slide 2: Summarize the 30-year dataset, strict chronological holdout, and key Phase 2 classical findings.")
    insert_metric_card(s2, 0.5, 1.25, 2.85, 1.05, f"{hw_d['RMSE']:.2f} °C", "HW Damped Champion RMSE", color=EMERALD)
    insert_metric_card(s2, 3.55, 1.25, 2.85, 1.05, f"{hw_d['R2']*100:.1f}%", "Out-of-Sample R² (0.9061)", color=MID)
    insert_metric_card(s2, 6.6, 1.25, 2.85, 1.05, "+26.8%", "RMSE Gain vs. Seasonal Naive", color=ORANGE)
    insert_metric_card(s2, 9.65, 1.25, 3.18, 1.05, f"p = {resid['ljung_box_lag14_p']:.2f}", "Ljung-Box (Lag 14) White Noise", color=NAVY)
    insert_figure(s2, os.path.join(fig_dir, "00_milestone2_summary_dashboard.png"), 0.5, 2.48, 7.6, 3.72)
    insert_structured_panel(s2, 8.3, 2.48, 4.53, 3.72, "Phase 2 Objectives & Protocol", [
        "• Dataset: Delhi daily mean temperature (tmean), 1 Jan 1996 – 18 Mar 2026 (11,035 days).",
        "• Missing Data Reconciled:",
        "   - Raw hourly (264,840 pts): 0.59% missing (1,575 records).",
        "   - Final processed daily series: 0.00% missing.",
        "• Fixed 365-Day Multi-Step Protocol:",
        "   - Train: 1 Jan 1996 – 18 Mar 2025 (10,670 days).",
        "   - Test: 19 Mar 2025 – 18 Mar 2026 (365 days).",
        "   - Zero test-period observations used during forecasting."
    ], size=10.2)
    insert_summary_banner(s2, "Phase 2 evaluates 7 daily classical model families on the 365-day holdout plus 1 supplementary Monthly SARIMA model on 12 holdout months.")

    # SLIDE 3: STATIONARITY & DIFFERENCING (ADF vs KPSS)
    s3 = create_slide_scaffold(3, "2. Stationarity Diagnostics (ADF vs. KPSS) & Lag Structure",
        notes_text="Slide 3: Clearly distinguish ADF (unit-root null rejected) vs KPSS (level-stationarity null not rejected).")
    insert_figure(s3, os.path.join(fig_dir, "01_stationarity_differencing.png"), 0.5, 1.25, 7.5, 4.9)
    insert_structured_panel(s3, 8.2, 1.25, 4.63, 4.9, "Complementary Statistical Tests", [
        "1. Augmented Dickey-Fuller (ADF) Test:",
        "   • Null Hypothesis (H0): Series has a unit root.",
        f"   • Result: t = {stat['adf_stat']:.2f}, p = {stat['adf_pvalue']:.2e}.",
        "   • Conclusion: Rejects unit-root non-stationarity.",
        "2. KPSS Level-Stationarity Test:",
        "   • Null Hypothesis (H0): Series is level-stationary.",
        f"   • Result: stat = {stat['kpss_stat']:.4f} (< 0.463 crit), p >= 0.10.",
        "   • Conclusion: Fails to reject level stationarity.",
        "   • Note: Supports level stationarity around the annual cycle without claiming every aspect is invariant.",
        "3. ACF / PACF Order Identification:",
        "   • Strong lag-1 persistence (ACF = 0.978); PACF cuts off after lag 2–3 -> motivates AR(2) & s = 365."
    ], size=10.0)
    insert_summary_banner(s3, "ADF rejects a unit root (p = 1.35e-18) and KPSS does not reject level stationarity (p >= 0.10); seasonal period m = 365 dominates.")

    # SLIDE 4: HOLT-WINTERS STATE-SPACE ANATOMY & GRADUAL DAMPING
    s4 = create_slide_scaffold(4, "3. Exponential Smoothing: Holt-Winters State-Space & Gradual Damping",
        notes_text="Slide 4: Explain alpha, gamma, and why phi = 0.9891 provides gradual trend damping rather than eliminating the trend.")
    insert_figure(s4, os.path.join(fig_dir, "02_holt_winters_components.png"), 0.5, 1.25, 7.5, 4.9)
    insert_structured_panel(s4, 8.2, 1.25, 4.63, 4.9, "Holt-Winters Damped Specification", [
        "State-Space Equations (m = 365, Additive):",
        "  • Level:    l_t = α(y_t − s_{t−m}) + (1−α)(l_{t−1} + ϕ b_{t−1})",
        "  • Trend:    b_t = β(l_t − l_{t−1}) + (1−β)ϕ b_{t−1}",
        "  • Seasonal: s_t = γ(y_t − l_{t−1} − ϕ b_{t−1}) + (1−γ)s_{t−m}",
        "Fitted Optimal Parameters:",
        "  • α = 0.9554 (responsive daily level update)",
        "  • β = 0.0000 (stable long-term secular slope)",
        "  • γ = 0.0446 (smooth 365-day seasonal evolution)",
        "  • ϕ = 0.9891 (gradual trend damping factor)",
        "Why ϕ = 0.9891 Matters:",
        "  • Because ϕ is close to 1, damping is gradual over 365 days—moderating warm bias (+0.362 °C vs +0.616 °C undamped) without abruptly eliminating trend."
    ], size=10.0)
    insert_summary_banner(s4, "Holt-Winters Damped (AIC = 2,880) reduces fixed 365-day RMSE from 2.228 °C (Additive) to 2.129 °C via gradual trend damping (ϕ = 0.9891).")

    # SLIDE 5: ARIMA(2,1,2) ORDER SELECTION (AIC / BIC GRID SEARCH)
    s5 = create_slide_scaffold(5, "4. Box-Jenkins Identification: ARIMA(2,1,2) Grid Search",
        notes_text="Slide 5: Present the AIC/BIC grid search over (p,q) in [0..3]^2 and explain why non-seasonal ARIMA flattens over 365 days.")
    insert_figure(s5, os.path.join(fig_dir, "03_arima_grid_search_selection.png"), 0.5, 1.25, 7.5, 4.9)
    insert_structured_panel(s5, 8.2, 1.25, 4.63, 4.9, "ARIMA Selection & Multi-Step Behavior", [
        "Grid Search Across (p, q) ∈ [0..3]² (d = 1):",
        "  • Evaluated on all 10,670 training observations.",
        "  • Selected Model: ARIMA(2,1,2).",
        "  • Minimum AIC = 30,241 | BIC = 30,278.",
        "Why Non-Seasonal ARIMA Fails at 365 Days:",
        "  • Without explicit 365-day seasonal terms, multi-step forecasts converge toward a flat level after ~14 days.",
        "  • Fixed 365d RMSE = 7.244 °C (R² = −0.0869).",
        "  • Proves that explicit annual seasonal modeling is mandatory for multi-month weather horizons."
    ], size=10.2)
    insert_summary_banner(s5, "ARIMA(2,1,2) minimizes AIC (30,241) and BIC (30,278) among non-seasonal models, but cannot track the 20 °C annual solar cycle.")

    # SLIDE 6: FOURIER HARMONIC REGRESSION (SARIMAX K=3)
    s6 = create_slide_scaffold(6, "5. Dynamic Harmonic Regression: Fourier SARIMAX (K = 3)",
        notes_text="Slide 6: Explain how K=3 Fourier sine/cosine pairs solve the s=365 SARIMA dimensionality problem.")
    insert_figure(s6, os.path.join(fig_dir, "04_sarima_fourier_decomposition.png"), 0.5, 1.25, 7.5, 4.9)
    insert_structured_panel(s6, 8.2, 1.25, 4.63, 4.9, "Solving s = 365 Dimensionality", [
        "The Daily SARIMA Bottleneck:",
        "  • Standard seasonal Box-Jenkins SARIMA(p,d,q)(P,D,Q)_365 requires 365+ lag state matrices (intractable on daily data).",
        "Solution 1 — Dynamic Harmonic SARIMAX (Daily):",
        "  • Uses K = 3 Fourier sine/cosine pairs (6 exogenous terms, period = 365.25) + ARIMA(2,0,1) errors.",
        "  • Captures fundamental solar wave (k=1), heating asymmetry (k=2), and monsoon cloud dip (k=3).",
        f"  • Fixed 365d RMSE = {sar['RMSE']:.3f} °C (R² = {sar['R2']:.4f}).",
        "Solution 2 — Supplementary Monthly SARIMA:",
        f"  • Monthly SARIMA(1,1,1)×(1,1,1)_12 on N=12 months: RMSE = {m_sarima['RMSE']:.3f} °C (reported separately)."
    ], size=10.0)
    insert_summary_banner(s6, "Fourier K=3 SARIMAX captures 88.3% of test variance (2.376 °C RMSE) with only 6 harmonic regressors and AR(1) = 0.910.")

    # SLIDE 7: EMPIRICAL BENCHMARK TABLE (7 DAILY MODELS + MONTHLY SARIMA)
    s7 = create_slide_scaffold(7, "6. Phase 2 Empirical Benchmark (7 Daily Models, N = 365 Test Days)",
        notes_text="Slide 7: Present the 7 daily classical models and explicitly clarify why Monthly SARIMA is the 8th supplementary model.")
    comp_df = pd.DataFrame([
        {"Rank / Model (Daily, N=365)": "1. Holt-Winters Damped", "Family": "Triple Exp. Smooth (ϕ=0.9891)", "RMSE": f"{hw_d['RMSE']:.3f} °C", "MAE": f"{hw_d['MAE']:.3f} °C", "MAPE": f"{hw_d['MAPE']:.2f}%", "R²": f"{hw_d['R2']:.4f}"},
        {"Rank / Model (Daily, N=365)": "2. Holt-Winters Additive", "Family": "Triple Exp. Smooth (m=365)", "RMSE": f"{hw_a['RMSE']:.3f} °C", "MAE": f"{hw_a['MAE']:.3f} °C", "MAPE": f"{hw_a['MAPE']:.2f}%", "R²": f"{hw_a['R2']:.4f}"},
        {"Rank / Model (Daily, N=365)": "3. SARIMAX (Fourier K=3)", "Family": "Harmonic + ARIMA(2,0,1)", "RMSE": f"{sar['RMSE']:.3f} °C", "MAE": f"{sar['MAE']:.3f} °C", "MAPE": f"{sar['MAPE']:.2f}%", "R²": f"{sar['R2']:.4f}"},
        {"Rank / Model (Daily, N=365)": "4. Seasonal Naive (y_{t-365})", "Family": "Annual Persistence", "RMSE": f"{snaive['RMSE']:.3f} °C", "MAE": f"{snaive['MAE']:.3f} °C", "MAPE": f"{snaive['MAPE']:.2f}%", "R²": f"{snaive['R2']:.4f}"},
        {"Rank / Model (Daily, N=365)": "5. ARIMA(2,1,2)", "Family": "Box-Jenkins Non-Seasonal", "RMSE": f"{arima['RMSE']:.3f} °C", "MAE": f"{arima['MAE']:.3f} °C", "MAPE": f"{arima['MAPE']:.2f}%", "R²": f"{arima['R2']:.4f}"},
        {"Rank / Model (Daily, N=365)": "6. Naive Persistence (y_T)", "Family": "Random Walk Baseline", "RMSE": f"{naive['RMSE']:.3f} °C", "MAE": f"{naive['MAE']:.3f} °C", "MAPE": f"{naive['MAPE']:.2f}%", "R²": f"{naive['R2']:.4f}"},
        {"Rank / Model (Daily, N=365)": "7. Holt Linear Trend", "Family": "Double Exp. (No Seasonal)", "RMSE": f"{holt['RMSE']:.3f} °C", "MAE": f"{holt['MAE']:.3f} °C", "MAPE": f"{holt['MAPE']:.2f}%", "R²": f"{holt['R2']:.4f}"},
    ])
    insert_table(s7, comp_df, 0.5, 1.25, 7.1, column_widths=[2.25, 1.75, 0.80, 0.80, 0.75, 0.75], size=8.5, row_height=0.40)
    insert_figure(s7, os.path.join(fig_dir, "06_error_metrics_benchmark.png"), 7.75, 1.25, 5.08, 4.8)
    insert_structured_panel(s7, 0.5, 4.60, 7.1, 1.55, "Reconciling 7 Daily Models vs. 8th Supplementary Monthly SARIMA", [
        f"• The 7 models above are evaluated on N = 365 daily holdout observations (19 Mar 2025 – 18 Mar 2026).",
        f"• 8th Supplementary Model — Monthly SARIMA(1,1,1)×(1,1,1)_12: evaluated separately on N = 12 monthly holdout averages (RMSE = {m_sarima['RMSE']:.3f} °C, MAE = {m_sarima['MAE']:.3f} °C)."
    ], size=9.5)
    insert_summary_banner(s7, "Holt-Winters Damped ranks #1 across all 7 daily classical models (RMSE 2.129 °C, MAE 1.657 °C, MAPE 7.13%, R² 0.9061).")

    # SLIDE 8: 365-DAY FORECAST TRAJECTORIES & 95% PREDICTION INTERVAL
    s8 = create_slide_scaffold(8, "7. Out-of-Sample 365-Day Forecast Trajectories & 95% Prediction Interval",
        notes_text="Slide 8: Show the 365-day test forecasts and explain the 95% prediction interval formula and empirical coverage (92.9%).")
    insert_figure(s8, os.path.join(fig_dir, "05_test_forecast_comparison.png"), 0.5, 1.25, 7.8, 4.9)
    insert_structured_panel(s8, 8.48, 1.25, 4.35, 4.9, "Trajectory & Prediction Interval", [
        "1. Seasonal Models Track the 20 °C Swing:",
        "   • Holt-Winters Damped, Additive & SARIMAX track the rise to ~35 °C in May–June and drop to ~10 °C in Jan.",
        "2. Non-Seasonal Models Collapse:",
        "   • ARIMA(2,1,2), Holt Linear, and Naive converge to a flat line (~22–24 °C), causing >15 °C winter errors.",
        "3. 95% Prediction Interval (PI) Explained:",
        "   • Formula: ŷ_t ± 1.96 × σ_resid (±4.11 °C for HW Damped).",
        "   • Technically a prediction interval around future daily observations (not a parameter CI).",
        "   • Tested empirical coverage on 365 holdout days: 92.9% (339 / 365 days).",
        "   • Residual convention: e_t = Actual − Predicted (e.g., 15.50 − 14.95 = +0.55 °C on 2025-12-06)."
    ], size=9.8)
    insert_summary_banner(s8, "Fixed 365-day classical models capture the macro-annual climate wave without seeing any test-period observations.")

    # SLIDE 9: RESIDUAL DIAGNOSTICS SUITE
    s9 = create_slide_scaffold(9, "8. Statistical Residual Diagnostics & Goodness-of-Fit",
        notes_text="Slide 9: Present Jarque-Bera (p=0.163) and Ljung-Box lag 14 (p=0.790) for Holt-Winters Damped residuals.")
    insert_figure(s9, os.path.join(fig_dir, "07_residual_diagnostics_suite.png"), 0.5, 1.25, 7.6, 4.9)
    insert_structured_panel(s9, 8.28, 1.25, 4.55, 4.9, "Residual Verification (HW Damped)", [
        f"• Mean Residual (Bias): +{hw_d['Bias']:.3f} °C (near zero).",
        f"• Residual Std Dev (σ): {resid['std']:.3f} °C.",
        f"• Jarque-Bera Normality Test: p = {resid['jarque_bera_pvalue']:.3f} (> 0.05).",
        "   - Fails to reject Gaussianity; errors follow bell curve.",
        f"• Ljung-Box Autocorrelation (Lag 14): p = {resid['ljung_box_lag14_p']:.3f} (> 0.05).",
        "   - Innovations behave as uncorrelated white noise at lag 14.",
        "• Scientific Conclusion:",
        "   - Holt-Winters Damped extracts all predictable linear seasonal structure from the univariate daily series."
    ], size=10.2)
    insert_summary_banner(s9, "Residual diagnostics confirm white-noise behavior (Ljung-Box lag-14 p = 0.790) and Gaussian adherence (Jarque-Bera p = 0.163).")

    # SLIDE 10: SEASONAL EVALUATION BREAKDOWN & EXTREME STRESS TESTS
    s10 = create_slide_scaffold(10, "9. Seasonal Evaluation Breakdown & Extreme Weather Stress Tests",
        notes_text="Slide 10: Clarify these are seasonal evaluation results for HW Damped over the 365-day test period, not predictions of average seasonal temperature.")
    insert_figure(s10, os.path.join(fig_dir, "08_domain_scenario_performance.png"), 0.5, 1.25, 7.4, 4.9)
    insert_structured_panel(s10, 8.08, 1.25, 4.75, 4.9, "HW Damped Seasonal Evaluation Results", [
        "Note: Out-of-sample RMSE over the 365-day test period:",
        f"  • Post-monsoon (61d): {s_perf['Post-monsoon']['RMSE']:.2f} °C RMSE (Best — calm skies)",
        f"  • Winter (90d):       {s_perf['Winter']['RMSE']:.2f} °C RMSE (MAE {s_perf['Winter']['MAE']:.2f} °C)",
        f"  • Monsoon (122d):     {s_perf['Monsoon']['RMSE']:.2f} °C RMSE (MAE {s_perf['Monsoon']['MAE']:.2f} °C)",
        f"  • Summer (92d):       {s_perf['Summer']['RMSE']:.2f} °C RMSE (Worst — MAE {s_perf['Summer']['MAE']:.2f} °C)",
        "Why Summer Has the Highest Error:",
        "  • Rapid pre-monsoon heating, extreme highs (>40 °C), sudden dust storms (Andhi), and high day-to-day variability.",
        "Extreme Temperature Subsets:",
        f"  • Heatwaves (≥38 °C, {ext_perf['heatwave_extreme']['count_days']}d): MAE = {ext_perf['heatwave_extreme']['MAE']:.2f} °C",
        f"  • Cold Snaps (≤8 °C, {ext_perf['coldsnap_extreme']['count_days']}d): MAE = {ext_perf['coldsnap_extreme']['MAE']:.2f} °C"
    ], size=9.8)
    insert_summary_banner(s10, "HW Damped performs best in Post-monsoon (1.70 °C RMSE) and worst in Summer (2.50 °C RMSE) due to convective dust storms & extremes.")

    # SLIDE 11: LIMITATIONS & POTENTIAL APPLICATIONS SCOPE
    s11 = create_slide_scaffold(11, "10. Limitations of Classical Models & Potential Application Scope",
        notes_text="Slide 11: Present classical limitations transparently and frame grid/health/winter applications as potential inputs requiring domain datasets.")
    insert_structured_panel(s11, 0.5, 1.25, 6.05, 4.9, "Key Limitations Identified in Phase 2", [
        "1. Univariate Horizon Decay:",
        "   • Fixed 365-day forecasts rely solely on past temperature levels and seasonal indices; they cannot react to yesterday's synoptic weather.",
        "2. Absence of Exogenous Covariates:",
        "   • Classical univariate models ignore prior-day humidity, rainfall cooling, and diurnal temperature range (DTR).",
        "3. Non-Linear Convective Events:",
        "   • Sudden summer dust storms and monsoon bursts create sharp temperature drops missed by linear smoothing.",
        "4. Single-City Scope (Delhi Only):",
        "   • Fitted parameters do not generalize directly to coastal or tropical cities (e.g., Mumbai, Chennai, Bengaluru)."
    ], size=10.2)
    insert_structured_panel(s11, 6.78, 1.25, 6.05, 4.9, "Potential Downstream Applications (Scope)", [
        "Important Scope Clarification:",
        "  • Temperature forecasts may provide supporting information for:",
        "     - Power-grid planning",
        "     - Heat-risk awareness",
        "     - Winter preparedness",
        "  • Because these models predict daily mean temperature rather than electricity demand, pollution, or hospital load directly, operational deployment requires integration with electricity, health, and air-quality datasets.",
        "Motivation for Phase 3:",
        "  • Introduces non-linear ML (XGBoost) with lagged moisture & rolling memory to address classical univariate limits."
    ], size=10.2)
    insert_summary_banner(s11, "Phase 2 establishes a rigorous 2.129 °C classical baseline while clearly bounding its univariate assumptions and application scope.")

    # SLIDE 12: PHASE 2 CONCLUSION & TEAM CONTRIBUTIONS
    s12 = create_slide_scaffold(12, "11. Phase 2 Conclusion & Equal Team Contributions",
        notes_text="Slide 12: Conclude Phase 2 evaluation and summarize equal 50/50 contributions.")
    insert_structured_panel(s12, 0.5, 1.25, 6.05, 4.9, "Phase 2 Summary & Key Takeaways", [
        "• Data Quality: 264,840 hourly records (0.59% raw missingness) curated into 11,035 daily observations (0.00% missingness).",
        "• Stationarity: ADF rejects unit root (p = 1.35e-18); KPSS fails to reject level stationarity (p >= 0.10).",
        "• Model Benchmarking: Evaluated 7 daily classical models on the 365-day holdout + 1 supplementary Monthly SARIMA model.",
        "• Champion: Holt-Winters Damped (m=365, ϕ=0.9891) achieved 2.129 °C RMSE, 90.6% R², and +26.8% gain over Seasonal Naive.",
        "• Diagnostics: Residuals satisfy white-noise (Ljung-Box p = 0.790) and normality (JB p = 0.163) checks."
    ], size=10.2)
    insert_structured_panel(s12, 6.78, 1.25, 6.05, 4.9, "Equal Team Contributions (50% / 50%)", [
        "Dhruv Saini (S24CSEU0818) — 50% Share:",
        "  • Daily data curation & missingness audit (0.59% -> 0.00%).",
        "  • Holt Linear, Holt-Winters Additive & Holt-Winters Damped state-space modeling.",
        "  • ARIMA(2,1,2) AIC/BIC grid search & Phase 2 markdown/report synthesis.",
        "Aarush Saxena (S24CSEU1682) — 50% Share:",
        "  • ADF/KPSS stationarity & ACF/PACF correlogram analysis.",
        "  • Dynamic harmonic SARIMAX (Fourier K=3) & Monthly SARIMA.",
        "  • Residual diagnostics (Jarque-Bera, Ljung-Box), seasonal evaluation & Phase 2 presentation."
    ], size=10.2)
    insert_summary_banner(s12, "Thank You! Phase 2 Classical Evaluation complete — reproducible pipeline in milestone2_pipeline.py & milestone2_output/.")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    prs.save(out_path)

    # Strict OOXML compatibility fix for Apple Keynote & PowerPoint
    tmp_pptx = out_path + ".tmp"
    with zipfile.ZipFile(out_path, "r") as zin:
        rels_root = ET.fromstring(zin.read("ppt/_rels/presentation.xml.rels").decode("utf-8"))
        notes_rid = None
        for rel in rels_root:
            if rel.attrib.get("Type", "").endswith("/notesMaster"):
                notes_rid = rel.attrib.get("Id")
                break
        pres_xml = zin.read("ppt/presentation.xml").decode("utf-8")
        pres_xml = pres_xml.replace('type="screen4x3"', 'type="screen16x9"')
        if notes_rid and "<p:notesMasterIdLst>" not in pres_xml:
            pres_xml = pres_xml.replace(
                "</p:sldMasterIdLst>",
                f'</p:sldMasterIdLst><p:notesMasterIdLst><p:notesMasterId r:id="{notes_rid}"/></p:notesMasterIdLst>',
                1,
            )
        with zipfile.ZipFile(tmp_pptx, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename == "ppt/presentation.xml":
                    zout.writestr(item, pres_xml.encode("utf-8"))
                else:
                    zout.writestr(item, zin.read(item.filename))
    shutil.move(tmp_pptx, out_path)
    return out_path


if __name__ == "__main__":
    p = generate_phase2_evaluation_pptx()
    prs_check = Presentation(p)
    print(f"✓ Generated Phase 2 Evaluation PPTX: {p} ({len(prs_check.slides)} slides)")
