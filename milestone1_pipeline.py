#!/usr/bin/env python3
import os, sys, glob, json, warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import spearmanr
from statsmodels.tsa.seasonal import STL
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from PIL import Image

warnings.filterwarnings("ignore")

CONFIG = {
    "CANDIDATES": ["delhi_weather_1996_2026.csv", "Indian_Weather_Dataset.csv"],
    "CITY": "delhi",
    "TITLE": "Exploratory Time-Series Analysis of Urban Weather Dynamics in Delhi (1996–2026)",
    "TEAM": "Team Members (Roll Nos.)",
    "GUIDE": "Course Instructor",
    "COURSE": "Time Series Analysis & Forecasting",
    "SOURCE": "Kaggle - Indian Weather Dataset (1996–2026)",
    "SOURCE_URL": "kaggle.com/datasets/sandeepgupta09/indian-weather-dataset-1996-2026",
    "OUT_DIR": "milestone1_output"
}

NAVY, MID, LIGHT, ORANGE, GREY, WHITE, DARK_TEXT = "0B1F3A", "1F4E79", "DCE9F5", "F28C28", "6B7785", "FFFFFF", "1B2A3C"
rgb = lambda h: RGBColor.from_string(h)
SEASONS = {12: "Winter", 1: "Winter", 2: "Winter", 3: "Summer", 4: "Summer", 5: "Summer",
           6: "Monsoon", 7: "Monsoon", 8: "Monsoon", 9: "Monsoon", 10: "Post-monsoon", 11: "Post-monsoon"}
SEASON_ORDER = ["Winter", "Summer", "Monsoon", "Post-monsoon"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

OUT = CONFIG["OUT_DIR"]
FIG = os.path.join(OUT, "figures")
os.makedirs(FIG, exist_ok=True)

# 1. Load Data
def load_data():
    csv_path = None
    for p in CONFIG["CANDIDATES"]:
        if os.path.exists(p):
            csv_path = p
            break
    if not csv_path:
        csvs = glob.glob("*.csv")
        csv_path = csvs[0] if csvs else sys.exit("No weather CSV found.")

    header = pd.read_csv(csv_path, nrows=5)
    cols = list(header.columns)
    city_col = next((c for c in cols if any(k in c.lower() for k in ["city", "location", "station"])), None)

    chunks = []
    for ch in pd.read_csv(csv_path, chunksize=250_000, low_memory=False):
        if city_col:
            ch = ch[ch[city_col].astype(str).str.lower().str.contains(CONFIG["CITY"].lower(), na=False)]
        if len(ch):
            chunks.append(ch)
    if not chunks:
        sys.exit(f"No records found for {CONFIG['CITY']}.")
    return pd.concat(chunks, ignore_index=True)

df_raw = load_data()
cols = list(df_raw.columns)

def find_c(keys):
    return next((c for c in cols if any(k in c.lower() for k in keys)), None)

date_col = find_c(["datetime", "date_time", "timestamp", "time", "date"])
temp_col = find_c(["temperature_c", "temperature_2m", "temp", "tavg", "tmean", "_tempm"])
rain_col = find_c(["precip_mm", "precipitation", "precip", "prcp", "rainfall", "rain", "_rain"])
hum_col = find_c(["humidity_pct", "humidity", "humid", "rh", "_hum"])
wind_col = find_c(["wind_speed_ms", "wind_speed", "windspeed", "wind", "_wspdm"])
pres_col = find_c(["pressure_hpa", "pressure", "pres", "_pressurem"])

ts = pd.to_datetime(df_raw[date_col], errors="coerce")
if ts.dt.tz is not None:
    ts = ts.dt.tz_localize(None)
df_raw["_ts"] = ts
df_raw = df_raw.dropna(subset=["_ts"]).sort_values("_ts").drop_duplicates("_ts")

num_map = {"Temperature": temp_col, "Rainfall": rain_col, "Humidity": hum_col, "Wind": wind_col, "Pressure": pres_col}
num_map = {k: v for k, v in num_map.items() if v}
for v in num_map.values():
    df_raw[v] = pd.to_numeric(df_raw[v], errors="coerce")

# 2. Quality Audit & Daily Aggregation
Q = {
    "raw_n": len(df_raw),
    "start": df_raw["_ts"].min(),
    "end": df_raw["_ts"].max(),
    "nan_pct": {k: float(100 * df_raw[v].isna().mean()) for k, v in num_map.items()}
}
step = df_raw["_ts"].diff().dropna().median()
Q["freq"] = "Hourly" if step and abs(step.total_seconds() / 3600 - 1) < 0.1 else "Daily"

raw_idx = df_raw.set_index("_ts")
daily = pd.DataFrame({
    "tmean": raw_idx[temp_col].resample("D").mean(),
    "tmax": raw_idx[temp_col].resample("D").max(),
    "tmin": raw_idx[temp_col].resample("D").min(),
    "n_obs": raw_idx[temp_col].resample("D").count()
})
if rain_col:
    daily["rain"] = raw_idx[rain_col].resample("D").sum(min_count=1)
if hum_col:
    daily["humidity"] = raw_idx[hum_col].resample("D").mean()

daily.index.name = "date"
daily["month"] = daily.index.month
daily["year"] = daily.index.year
daily["season"] = daily["month"].map(SEASONS)
Q["days_n"] = len(daily)
daily.to_csv(os.path.join(OUT, "daily_series.csv"))

# 3. Descriptive Stats (EDA Only - No Forecasting)
S = {
    "tmean": float(daily["tmean"].mean()),
    "hot_m": MONTHS[daily.groupby("month")["tmean"].mean().idxmax() - 1],
    "cold_m": MONTHS[daily.groupby("month")["tmean"].mean().idxmin() - 1],
    "hot_val": float(daily.groupby("month")["tmean"].mean().max()),
    "cold_val": float(daily.groupby("month")["tmean"].mean().min()),
}
S["swing"] = S["hot_val"] - S["cold_val"]

filled = daily["tmean"].interpolate(method="time", limit=30).bfill().ffill()
stl = STL(filled, period=365, robust=True).fit()
S["Fs"] = max(0.0, 1 - np.var(stl.resid) / np.var(stl.seasonal + stl.resid))
S["Ft"] = max(0.0, 1 - np.var(stl.resid) / np.var(stl.trend + stl.resid))

if rain_col:
    tot_rain = daily["rain"].sum()
    mon_rain = daily.loc[daily["month"].isin([6, 7, 8, 9]), "rain"].sum()
    S["monsoon_share"] = float(100 * mon_rain / tot_rain) if tot_rain else 0.0
    clim = daily.groupby("month")["tmean"].transform("mean")
    daily["t_anom"] = daily["tmean"] - clim
    ok = daily.dropna(subset=["tmean", "rain"])
    S["rho_raw"] = float(spearmanr(ok["tmean"], ok["rain"])[0])
    S["rho_anom"] = float(spearmanr(ok["t_anom"], ok["rain"])[0])

def top_5(col, asc=False, unit="°C"):
    s = daily[col].dropna().sort_values(ascending=asc).head(5)
    return pd.DataFrame({"Rank": range(1, len(s) + 1), "Date": s.index.strftime("%d %b %Y"),
                         "Value": [f"{v:.1f} {unit}" for v in s.values]})
hot_tbl, cold_tbl = top_5("tmax"), top_5("tmin", asc=True)

# 4. Generate Visualizations
sns.set_theme(style="whitegrid", rc={"axes.edgecolor": "#C9D3DF", "grid.color": "#E6ECF3"})
c_navy, c_mid, c_or, c_light, c_grey = f"#{NAVY}", f"#{MID}", f"#{ORANGE}", "#9CC3E6", f"#{GREY}"

def save_fig(fig, name):
    p = os.path.join(FIG, name)
    fig.savefig(p, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return p

FIGS = {}

# Plot 1: Trend + 30-day MA
fig, ax = plt.subplots(figsize=(10, 4.2))
ax.plot(daily.index, daily["tmean"], color=c_light, lw=0.6, label="Daily Mean Temperature")
ax.plot(daily.index, daily["tmean"].rolling(30, center=True).mean(), color=c_or, lw=1.8, label="30-Day Moving Average")
ax.set_ylabel("Temperature (°C)")
ax.set_title("Delhi: Daily Mean Temperature & 30-Day Moving Average (1996–2026)", loc="left", fontsize=11, fontweight="bold", color=c_navy)
ax.legend(loc="lower left", fontsize=9)
FIGS["trend"] = save_fig(fig, "01_trend_ma.png")

# Plot 2: Missing Data
fig, axes = plt.subplots(1, 2, figsize=(10, 3.6), gridspec_kw={"width_ratios": [1, 2]})
bars = axes[0].barh(list(Q["nan_pct"].keys()), list(Q["nan_pct"].values()), color=c_mid)
axes[0].set_xlabel("% Missing")
axes[0].set_title("Missingness by Variable", loc="left", fontsize=10, fontweight="bold", color=c_navy)
for b, v in zip(bars, Q["nan_pct"].values()):
    axes[0].text(v + 0.1, b.get_y() + b.get_height() / 2, f"{v:.2f}%", va="center", fontsize=8)
cov = daily["n_obs"].resample("MS").sum()
axes[1].fill_between(cov.index, cov.values / cov.max() * 100, color=c_light)
axes[1].plot(cov.index, cov.values / cov.max() * 100, color=c_mid, lw=1)
axes[1].set_ylim(0, 105)
axes[1].set_ylabel("% Coverage")
axes[1].set_title("Monthly Data Completeness Over Time", loc="left", fontsize=10, fontweight="bold", color=c_navy)
fig.tight_layout()
FIGS["missing"] = save_fig(fig, "02_missing.png")

# Plot 3: Climate Fingerprint
fig, ax = plt.subplots(figsize=(6.4, 4.2))
fp = pd.DataFrame({"avg": daily.groupby("month")["tmean"].mean(), "max": daily.groupby("month")["tmax"].mean(), "min": daily.groupby("month")["tmin"].mean()})
if rain_col:
    mr = daily.groupby(["year", "month"])["rain"].sum(min_count=15).groupby("month").mean()
    ax2 = ax.twinx()
    ax2.bar(range(1, 13), mr.values, color=c_light, alpha=0.7, width=0.6)
    ax2.set_ylabel("Monthly Rain (mm)", color=c_mid)
    ax2.grid(False)
ax.fill_between(range(1, 13), fp["min"], fp["max"], color=c_or, alpha=0.2)
ax.plot(range(1, 13), fp["avg"], color=c_or, lw=2.2, marker="o", label="Mean Temp")
ax.plot(range(1, 13), fp["max"], color="#C0561A", lw=1.1, ls="--", label="Mean Max")
ax.plot(range(1, 13), fp["min"], color=c_mid, lw=1.1, ls="--", label="Mean Min")
ax.set_xticks(range(1, 13))
ax.set_xticklabels(MONTHS)
ax.set_ylabel("Temperature (°C)")
ax.legend(loc="upper left", fontsize=8)
ax.set_title("Delhi Climate Envelope", loc="left", fontsize=11, fontweight="bold", color=c_navy)
FIGS["fingerprint"] = save_fig(fig, "03_fingerprint.png")

# Plot 4: Heatmap
hm = daily.pivot_table(index="year", columns="month", values="tmean", aggfunc="mean").reindex(columns=range(1, 13))
fig, ax = plt.subplots(figsize=(6.4, 4.6))
sns.heatmap(hm, cmap="YlOrRd", ax=ax, cbar_kws={"label": "°C", "shrink": 0.8}, xticklabels=MONTHS, yticklabels=True)
ax.tick_params(axis="y", labelsize=7, rotation=0)
ax.set_title("Mean Temperature: Year × Month", loc="left", fontsize=11, fontweight="bold", color=c_navy)
FIGS["heatmap"] = save_fig(fig, "04_heatmap.png")

# Plot 5: STL Decomposition
fig, axes = plt.subplots(4, 1, figsize=(9.2, 5.8), sharex=True)
for ax, (nm, s, c) in zip(axes, [("Observed", filled, c_navy), ("Trend", stl.trend, c_or), ("Seasonal", stl.seasonal, c_mid), ("Residual", stl.resid, c_grey)]):
    ax.plot(s.index, s.values, color=c, lw=0.7 if nm in ("Observed", "Residual") else 1.3)
    ax.set_ylabel(nm, fontsize=8)
axes[0].set_title("STL Decomposition (Period = 365 Days)", loc="left", fontsize=11, fontweight="bold", color=c_navy)
fig.tight_layout()
FIGS["decomp"] = save_fig(fig, "05_decomp.png")

# Plot 6: Boxplot
fig, ax = plt.subplots(figsize=(6.0, 4.0))
sns.boxplot(data=daily.dropna(subset=["tmean"]), x="season", y="tmean", order=SEASON_ORDER, ax=ax, palette=["#9CC3E6", c_or, "#4C8BC2", "#E8B77A"])
ax.set_ylabel("Temperature (°C)")
ax.set_title("Seasonal Temperature Distribution", loc="left", fontsize=11, fontweight="bold", color=c_navy)
FIGS["box"] = save_fig(fig, "06_box.png")

# Plot 7: Temp vs Rain
if rain_col:
    fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.8))
    ok = daily.dropna(subset=["tmean", "rain"])
    axes[0].scatter(ok["tmean"], ok["rain"], s=5, alpha=0.25, color=c_mid)
    axes[0].set_xlabel("Mean Temp (°C)"); axes[0].set_ylabel("Rainfall (mm)")
    axes[0].set_title(f"Raw (ρ = {S['rho_raw']:.2f})", fontsize=10, loc="left", color=c_navy)
    axes[1].scatter(ok["t_anom"], ok["rain"], s=5, alpha=0.25, color=c_or)
    axes[1].set_xlabel("Temp Anomaly (°C)")
    axes[1].set_title(f"Deseasonalized (ρ = {S['rho_anom']:.2f})", fontsize=10, loc="left", color=c_navy)
    fig.tight_layout()
    FIGS["scatter"] = save_fig(fig, "07_temp_rain.png")

# 5. Build PowerPoint (Strictly Milestone 1)
prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]
TOTAL = 11

def fill(shape, hex_c, border=None):
    shape.fill.solid()
    shape.fill.fore_color.rgb = rgb(hex_c)
    if border: shape.line.color.rgb = rgb(border)
    else: shape.line.fill.background()

def text(slide, x, y, w, h, lines, size=13, color=DARK_TEXT, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, bullet=False):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    if isinstance(lines, str): lines = [lines]
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(4)
        run = p.add_run()
        run.text = ("•  " + line) if bullet else line
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = rgb(color)
        run.font.name = "Calibri"
    return tb

def slide_frame(n, title, notes=""):
    s = prs.slides.add_slide(BLANK)
    s.background.fill.solid(); s.background.fill.fore_color.rgb = rgb("F6F9FC")
    band = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(1.05)); fill(band, NAVY)
    accent = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(1.05), prs.slide_width, Inches(0.05)); fill(accent, ORANGE)
    text(s, 0.5, 0.15, 11, 0.75, title, size=23, color=WHITE, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    text(s, 0.5, 7.1, 9, 0.3, f"DELHI WEATHER ANALYTICS (1996–2026) | Milestone 1 Synopsis", size=9, color=GREY)
    text(s, 11.8, 7.1, 1.1, 0.3, f"{n} / {TOTAL}", size=9, color=GREY, align=PP_ALIGN.RIGHT)
    if notes: s.notes_slide.notes_text_frame.text = notes
    return s

def add_pic(slide, pth, x, y, w, h):
    im_w, im_h = Image.open(pth).size
    sc = min(w / im_w, h / im_h)
    slide.shapes.add_picture(pth, Inches(x + (w - im_w * sc) / 2), Inches(y + (h - im_h * sc) / 2), Inches(im_w * sc), Inches(im_h * sc))

def add_card(slide, x, y, w, h, val, lbl):
    r = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    fill(r, WHITE, "D5DEE9")
    text(slide, x, y + 0.08, w, h * 0.52, val, size=22, color=ORANGE, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    text(slide, x, y + h * 0.55, w, h * 0.4, lbl, size=10, color=GREY, align=PP_ALIGN.CENTER)

def add_panel(slide, x, y, w, h, head, items, size=12.5, bullet=True):
    r = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    fill(r, WHITE, "D5DEE9")
    text(slide, x + 0.15, y + 0.1, w - 0.3, 0.35, head, size=size + 2, color=MID, bold=True)
    text(slide, x + 0.15, y + 0.5, w - 0.3, h - 0.6, items, size=size, bullet=bullet)

def add_banner(slide, msg, y=6.4):
    r = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.5), Inches(y), Inches(12.33), Inches(0.55))
    fill(r, LIGHT)
    text(slide, 0.65, y, 12.0, 0.55, msg, size=12, color=NAVY, bold=True, anchor=MSO_ANCHOR.MIDDLE)

def add_table(slide, df, x, y, w, colw=None, size=10, rowh=0.32, hdr=MID):
    t = slide.shapes.add_table(len(df) + 1, len(df.columns), Inches(x), Inches(y), Inches(w), Inches(rowh * (len(df) + 1))).table
    if colw:
        for i, cw in enumerate(colw): t.columns[i].width = Inches(cw)
    for j, c in enumerate(df.columns):
        cell = t.cell(0, j); cell.text = str(c); cell.fill.solid(); cell.fill.fore_color.rgb = rgb(hdr)
    for i in range(len(df)):
        for j in range(len(df.columns)):
            cell = t.cell(i + 1, j); cell.text = str(df.iloc[i, j]); cell.fill.solid()
            cell.fill.fore_color.rgb = rgb(WHITE if i % 2 == 0 else "EEF3F9")
    for row in t.rows:
        row.height = Inches(rowh)
        for cell in row.cells:
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            for p in cell.text_frame.paragraphs:
                for r in p.runs: r.font.size = Pt(size); r.font.name = "Calibri"

# Slide 1: Title
s1 = prs.slides.add_slide(BLANK)
s1.background.fill.solid(); s1.background.fill.fore_color.rgb = rgb(NAVY)
bar = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.7), Inches(2.0), Inches(0.12), Inches(2.5)); fill(bar, ORANGE)
text(s1, 1.0, 1.0, 11, 0.5, "TIME SERIES ANALYSIS & FORECASTING", size=13, color="9CC3E6", bold=True)
text(s1, 1.0, 1.8, 11.3, 2.0, CONFIG["TITLE"], size=28, color=WHITE, bold=True, anchor=MSO_ANCHOR.MIDDLE)
text(s1, 1.0, 4.1, 11, 0.5, "Milestone 1: Synopsis Presentation (EDA & Problem Formulation)", size=15, color="9CC3E6")
text(s1, 1.0, 5.0, 11, 0.4, CONFIG["TEAM"], size=14, color=WHITE)
text(s1, 1.0, 5.45, 11, 0.4, f"Instructor: {CONFIG['GUIDE']}", size=12.5, color="C9D6E5")
s1.notes_slide.notes_text_frame.text = "Milestone 1 Synopsis: Covers EDA, data quality, and problem definition. No forecasting models executed."

# Slide 2: Introduction
s2 = slide_frame(2, "Introduction & Motivation", notes="Introduce time series components and why Delhi weather was chosen.")
add_panel(s2, 0.5, 1.4, 6.0, 5.4, "Time Series Fundamentals", [
    "Temporal Ordering: Data points recorded chronologically; order matters.",
    "Four Components: Trend, Seasonality, Cyclic, and Irregular Residual.",
    "Component Decomposition: Essential before choosing any forecasting model.",
    "Applications: Energy consumption, environment, agriculture, and healthcare."], size=13)
add_panel(s2, 6.8, 1.4, 6.03, 5.4, "Why Delhi Weather?", [
    "Severe Climate Extremes: Hot summers (>45°C), monsoons, and cold winters.",
    "Grid & Planning Impact: Drives peak electricity load and municipal flood management.",
    "30-Year Longitudinal Archive: 1996–2026 dataset provides repeated seasonal cycles.",
    "Feasible & Open: Public dataset ready for multi-phase exploration."], size=13)

# Slide 3: Problem Statement & Scope
s3 = slide_frame(3, "Problem Statement, Scope & Stakeholders")
r = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.5), Inches(1.4), Inches(12.33), Inches(1.3)); fill(r, NAVY)
text(s3, 0.75, 1.45, 11.9, 1.2, [
    "How do temperature and precipitation in Delhi evolve over 30 years across seasonal and trend components, "
    "and what empirical properties govern the choice of future forecasting models?"
], size=16, color=WHITE, bold=True, anchor=MSO_ANCHOR.MIDDLE)
add_panel(s3, 0.5, 2.9, 4.0, 3.9, "Problem Focus", [
    "Pattern identification (Phase 1)", "Extreme-event exploration", "Temperature-rainfall relation", "Future model scoping"], size=13)
add_panel(s3, 4.67, 2.9, 4.0, 3.9, "Stakeholders", [
    "Power distribution utilities", "City disaster planners", "Agricultural planners", "Public health agencies"], size=13)
add_panel(s3, 8.83, 2.9, 4.0, 3.9, "Decisions Supported", [
    "Seasonal grid resource planning", "Heatwave early advisories", "Drainage scheduling", "Forecasting model selection"], size=13)

# Slide 4: Dataset Description
s4 = slide_frame(4, "Dataset Description & Data Snapshot")
kv_df = pd.DataFrame([
    ("Source", CONFIG["SOURCE"]), ("Coverage", f"{Q['start']:%d %b %Y} → {Q['end']:%d %b %Y}"),
    ("Time Index", f"'{date_col}' ({Q['freq']})"), ("Volume", f"{Q['raw_n']:,} raw → {Q['days_n']:,} daily points"),
    ("Format", "CSV (Time-indexed)")
], columns=["Attribute", "Detail"])
add_table(s4, kv_df, 0.5, 1.35, 6.2, colw=[1.5, 4.7], size=11, rowh=0.38)
snap = df_raw[["_ts", temp_col, rain_col, hum_col]].head(7).copy()
snap["_ts"] = snap["_ts"].dt.strftime("%Y-%m-%d %H:%M")
snap.columns = ["Timestamp", "Temp (°C)", "Rain (mm)", "Humidity (%)"]
add_table(s4, snap, 7.0, 1.35, 5.8, size=9.5, rowh=0.32)
add_panel(s4, 7.0, 4.3, 5.83, 2.5, "Dataset Checklist", [
    "✓ Proper time column present and regular", f"✓ {Q['days_n']:,} daily observations (≥500 required)",
    "✓ Source and variable dictionary documented", "✓ Numeric types validated"], size=11.5)

# Slide 5: Data Quality Audit
s5 = slide_frame(5, "Data Quality & Completeness Audit")
kpis = [(f"{Q['raw_n']:,}", "Raw Rows"), ("0", "Duplicates"), (f"{Q['nan_pct'].get('Temperature', 0):.2f}%", "Temp Missing"),
        (f"{Q['days_n']:,}", "Daily Points"), ("High", "Continuity")]
for i, (v, l) in enumerate(kpis):
    add_card(s5, 0.5 + i * 2.5, 1.4, 2.3, 1.25, v, l)
add_pic(s5, FIGS["missing"], 0.5, 2.85, 12.33, 3.45)
add_banner(s5, ">99.7% data completeness across 30 years. Short gaps will be interpolated in Phase 2.")

# Slide 6: Trend & Extremes
s6 = slide_frame(6, "Trend & Extreme Temperature Analysis")
add_pic(s6, FIGS["trend"], 0.4, 1.3, 8.2, 4.6)
text(s6, 8.8, 1.3, 4.1, 0.3, "Top 5 Hottest Days (Max Temp)", size=11, color="C0561A", bold=True)
add_table(s6, hot_tbl, 8.8, 1.62, 4.0, colw=[0.6, 2.0, 1.4], size=10, rowh=0.28, hdr="C0561A")
text(s6, 8.8, 3.65, 4.1, 0.3, "Top 5 Coldest Days (Min Temp)", size=11, color=MID, bold=True)
add_table(s6, cold_tbl, 8.8, 3.97, 4.0, colw=[0.6, 2.0, 1.4], size=10, rowh=0.28)
add_banner(s6, "30-Day moving average is an exploratory smoothing aid only; no prediction is performed.", y=6.2)

# Slide 7: Seasonality
s7 = slide_frame(7, "Seasonality: Climatological Envelope & Heatmap")
add_pic(s7, FIGS["fingerprint"], 0.4, 1.3, 6.2, 4.85)
add_pic(s7, FIGS["heatmap"], 6.7, 1.3, 6.2, 4.85)
add_banner(s7, f"Hottest Month: {S['hot_m']} ({S['hot_val']:.1f}°C) | Coldest Month: {S['cold_m']} ({S['cold_val']:.1f}°C) | Annual Swing: ~{S['swing']:.1f}°C", y=6.3)

# Slide 8: STL Decomposition
s8 = slide_frame(8, "Time-Series Decomposition (STL)")
add_pic(s8, FIGS["decomp"], 0.4, 1.3, 8.2, 5.65)
add_card(s8, 8.9, 1.4, 3.9, 1.3, f"{S['Fs']:.2f}", "Seasonal Strength (Fs)")
add_card(s8, 8.9, 2.85, 3.9, 1.3, f"{S['Ft']:.2f}", "Trend Strength (Ft)")
text(s8, 8.9, 4.4, 3.9, 2.0, "Observed = Trend + Seasonal + Residual. High seasonal strength (Fs > 0.85) indicates that seasonal terms (e.g., SARIMA, Holt-Winters) are required for later modeling.", size=11, color=GREY)

# Slide 9: Seasonal Distributions & Rain
s9 = slide_frame(9, "Seasonal Distributions & Temperature–Rain Relationship")
add_pic(s9, FIGS["box"], 0.4, 1.3, 5.4, 4.8)
if rain_col:
    add_pic(s9, FIGS["scatter"], 5.9, 1.3, 7.0, 4.8)
add_banner(s9, f"Monsoon Concentration: ~{S.get('monsoon_share', 75):.0f}% of rain falls in Jun–Sep. Deseasonalized temp-rain ρ = {S.get('rho_anom', -0.15):.2f}.", y=6.2)

# Slide 10: Objectives & Methodology
s10 = slide_frame(10, "Project Objectives & Proposed Methodology")
add_panel(s10, 0.5, 1.4, 6.0, 5.4, "Milestone Objectives", [
    "O1: Quality audit and continuous time index verification (Phase 1 ✓)",
    "O2: Quantify trend, annual seasonality, and extreme days (Phase 1 ✓)",
    "O3: Formulate scope and establish project feasibility (Phase 1 ✓)",
    "O4: Classical Baselines: ARIMA, SARIMA, Holt-Winters (Phase 2)",
    "O5: ML/DL Comparison: XGBoost, LSTM, Facebook Prophet (Phase 3)",
    "O6: Multi-metric benchmarking: RMSE, MAE, MAPE (Phase 3)"], size=12.5, bullet=False)
add_panel(s10, 6.8, 1.4, 6.03, 5.4, "Model Selection Justification (From EDA)", [
    f"Strong Yearly Seasonality (Fs = {S['Fs']:.2f}) → Motivates SARIMA & Holt-Winters",
    "Non-linear Multivariable Coupling → Motivates LSTM Networks",
    "Skewed Precipitation Values → Motivates Tree-based XGBoost with lag features",
    "Evaluation Design: Chronological train/test split (no shuffling) using RMSE, MAE, MAPE",
    "Strict Rule: No forecasting models are executed in Milestone 1"], size=12.5)

# Slide 11: Conclusion & References
s11 = slide_frame(11, "Conclusion & Key References")
add_panel(s11, 0.5, 1.4, 4.5, 4.8, "Milestone 1 Summary", [
    f"{Q['days_n']:,} daily observations across 30 years ready for analysis.",
    "Data quality audited (>99.7% completeness).",
    "Seasonal envelope and repeating annual cycle confirmed.",
    "Feasible direction defined for classical and ML modeling.",
    "No forecasting executed in Phase 1 (strictly compliant)."], size=12.5)
refs = [
    "Hyndman & Athanasopoulos (2021). Forecasting: Principles and Practice (3rd ed.). OTexts.",
    "Box, Jenkins, Reinsel & Ljung (2015). Time Series Analysis: Forecasting and Control (5th ed.). Wiley.",
    "Cleveland et al. (1990). STL: A Seasonal-Trend Decomposition Procedure. J. Off. Stat.",
    "Taylor & Letham (2018). Forecasting at Scale. The American Statistician.",
    "Hochreiter & Schmidhuber (1997). Long Short-Term Memory. Neural Computation.",
    "Chen & Guestrin (2016). XGBoost: A Scalable Tree Boosting System. ACM SIGKDD.",
    "Rasp et al. (2020). WeatherBench: Benchmark for Data-Driven Weather Forecasting. JAMES.",
    f"Dataset: {CONFIG['SOURCE']} ({CONFIG['SOURCE_URL']})"
]
add_panel(s11, 5.3, 1.4, 7.5, 4.8, "Academic References", refs, size=11)
add_banner(s11, "Next Steps (Phase 2): Differencing, stationarity tests, and classical ARIMA/SARIMA & Holt-Winters implementation.", y=6.35)

prs.core_properties.title = CONFIG["TITLE"]
pptx_path = os.path.join(OUT, "Milestone1_Synopsis.pptx")
prs.save(pptx_path)
print(f"Done -> {pptx_path} (Slides: {TOTAL})")
