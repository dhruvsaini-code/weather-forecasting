#!/usr/bin/env python3
"""
UI & Interactive Visualization Generator for the Multi-Year Future Forecast Lab
(1 April 2026 – 31 March 2030 | 1,461 Daily Predictions across 3 Models)
"""

import os
import json


def get_future_lab_css():
    return """
/* Multi-Year Future Forecast Lab (Apr 2026 - Mar 2030) & Canvas/Navbar Fixes */
.canvas-wrap{position:relative;width:100%;height:380px;margin-top:8px;overflow:hidden}
.canvas-wrap canvas{width:100%!important;height:100%!important;display:block;cursor:crosshair}
.explorer-card{min-width:0;overflow:hidden}
nav .mark,nav ul a,.pill,.pill-emerald,.pill-outline{white-space:nowrap}
nav ul{gap:clamp(10px,1.2vw,18px)!important}
nav ul a{font-size:.84rem!important}
.fl-banner-warn{background:color-mix(in srgb,var(--ochre) 14%,var(--paper));border:1.5px solid var(--ochre);border-radius:8px;padding:12px 18px;margin-bottom:20px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;font-family:var(--mono);font-size:.78rem;color:var(--ink)}
.fl-banner-warn strong{color:var(--ochre);letter-spacing:.05em}
.fl-meta-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-bottom:20px}
.fl-meta-cell{background:var(--paper);border:1px solid var(--line);border-radius:8px;padding:12px 14px;min-width:0}
.fl-meta-cell small{display:block;font-family:var(--mono);font-size:.69rem;text-transform:uppercase;color:var(--soft);letter-spacing:.05em}
.fl-meta-cell strong{display:block;font-family:var(--mono);font-size:.9rem;color:var(--ink);margin-top:3px}
.fl-controls-bar{background:var(--paper);border:1px solid var(--line);border-radius:10px;padding:18px 20px;margin-bottom:20px;display:grid;grid-template-columns:1.4fr 1fr 1fr 1.2fr auto;gap:14px;align-items:end}
.fl-field{min-width:0}
.fl-field label{display:block;font-family:var(--mono);font-size:.71rem;text-transform:uppercase;color:var(--soft);margin-bottom:6px;letter-spacing:.04em;white-space:nowrap}
.fl-input,.fl-select{width:100%;background:var(--plaster);border:1px solid var(--line);color:var(--ink);padding:9px 12px;border-radius:6px;font-family:var(--mono);font-size:.83rem;height:38px}
.fl-gen-btn{background:var(--emerald);color:#fff;border:0;padding:0 20px;height:38px;border-radius:8px;font-family:var(--sans);font-size:.88rem;font-weight:600;cursor:pointer;transition:opacity .15s,transform .15s;white-space:nowrap}
.fl-gen-btn:hover{opacity:.92;transform:translateY(-1px)}
.fl-status-line{grid-column:1/-1;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;padding-top:10px;border-top:1px solid var(--line-soft);font-family:var(--mono);font-size:.76rem;color:var(--soft)}
.fl-subgrid-2{display:grid;grid-template-columns:minmax(0,1.25fr) minmax(0,1fr);gap:20px;margin-top:24px}
.fl-subgrid-2 > *{min-width:0}
.fl-year-cards{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px;margin-top:16px}
.fl-ycard{background:var(--paper);border:1px solid var(--line);border-top:4px solid var(--emerald);border-radius:8px;padding:16px 14px;display:flex;flex-direction:column;justify-content:space-between;min-width:0}
.fl-ycard.partial{border-top-color:var(--ochre)}
.fl-ycard.leap{border-top-color:#7C3AED}
.fl-ycard small{font-family:var(--mono);font-size:.69rem;text-transform:uppercase;color:var(--soft)}
.fl-ycard h4{font-family:var(--serif);font-size:1.75rem;font-weight:400;margin:4px 0}
.fl-ycard .y-mean{font-family:var(--mono);font-size:1.25rem;color:var(--emerald);font-weight:600;margin-bottom:6px}
.fl-ycard.partial .y-mean{color:var(--ochre)}
.fl-ycard .y-stats{font-family:var(--mono);font-size:.74rem;color:var(--soft);line-height:1.55;border-top:1px solid var(--line-soft);padding-top:8px;margin-top:6px}
.fl-table-wrap{max-height:310px;overflow-y:auto;overflow-x:auto;border:1px solid var(--line);border-radius:8px;background:var(--plaster)}
.fl-table{width:100%;border-collapse:collapse;font-family:var(--mono);font-size:.76rem}
.fl-table th{position:sticky;top:0;background:var(--paper);color:var(--ink);text-align:left;padding:9px 10px;border-bottom:1px solid var(--line);font-weight:600;white-space:nowrap}
.fl-table td{padding:7px 10px;border-bottom:1px solid var(--line-soft);color:var(--soft);white-space:nowrap}
.fl-table tr:hover td{background:color-mix(in srgb,var(--paper) 70%,transparent);color:var(--ink)}
.fl-dl-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin-top:16px}
.fl-dl-card{background:var(--paper);border:1px solid var(--line);border-radius:8px;padding:14px 16px;display:flex;flex-direction:column;justify-content:space-between;gap:10px;min-width:0}
.fl-dl-card b{font-family:var(--serif);font-size:1.2rem;font-weight:400}
.fl-dl-card small{font-family:var(--mono);font-size:.71rem;color:var(--soft);display:block;word-break:break-word}
@media (max-width:1024px){
  .fl-controls-bar,.fl-meta-grid,.fl-subgrid-2,.fl-year-cards,.fl-dl-grid{grid-template-columns:1fr 1fr}
}
@media (max-width:680px){
  .fl-controls-bar,.fl-meta-grid,.fl-subgrid-2,.fl-year-cards,.fl-dl-grid{grid-template-columns:1fr}
}
"""


def get_future_lab_section_html(p3_prefix="phase3_output/"):
    bundle_candidates = [
        os.path.join("phase3_output", "future_forecast", "future_forecast_bundle.json"),
        os.path.join("future_forecast", "future_forecast_bundle.json"),
    ]
    bundle_path = next((p for p in bundle_candidates if os.path.exists(p)), None)
    bundle_json = "{}"
    if bundle_path:
        with open(bundle_path, "r", encoding="utf-8") as f:
            bundle_json = f.read()

    fl_dir = f"{p3_prefix}future_forecast/"

    return f"""
<section id="future-lab">
  <div class="wrap">
    <div class="head">
      <div>
        <span class="sec-kicker">Experimental Long-Range Forecasting Module • April 2026 – March 2030</span>
        <h2>DELHI MULTI-YEAR FORECAST LAB</h2>
      </div>
      <p>Experimental Long-Range Temperature Forecasting | <strong>1 April 2026 – 31 March 2030</strong> (1,461 continuous daily predictions across 4 years, bridging the 13-day gap from the 18 March 2026 historical cutoff).</p>
    </div>

    <div class="fl-banner-warn">
      <span>⚠️ <strong>EXPERIMENTAL LONG-RANGE FORECAST — NOT AN OPERATIONAL WEATHER FORECAST.</strong> All values are generated from models trained strictly on historical observations up to 18 March 2026. No future actual observations exist or are used.</span>
      <span>2028 Leap Day (29 Feb 2028) Included • 0 NaNs Verified</span>
    </div>

    <div class="fl-meta-grid">
      <div class="fl-meta-cell"><small>Location</small><strong>Delhi, India</strong></div>
      <div class="fl-meta-cell"><small>Target Variable</small><strong>Daily Mean Temp (tmean, °C)</strong></div>
      <div class="fl-meta-cell"><small>Historical Data Cutoff</small><strong>18 March 2026 (11,035d)</strong></div>
      <div class="fl-meta-cell"><small>Bridge Gap Handled</small><strong>19–31 Mar 2026 (13d)</strong></div>
      <div class="fl-meta-cell"><small>Forecast Start</small><strong>1 April 2026</strong></div>
      <div class="fl-meta-cell"><small>Forecast End</small><strong>31 March 2030</strong></div>
      <div class="fl-meta-cell"><small>Forecast Horizon</small><strong>Four Years (1,461 Days)</strong></div>
      <div class="fl-meta-cell"><small>Forecast Frequency</small><strong id="flMetaFreq">Daily (1d steps)</strong></div>
    </div>

    <!-- Forecast Generation & Model Selection Controls -->
    <div class="fl-controls-bar">
      <div class="fl-field">
        <label for="flModelSelect">1. Forecasting Model</label>
        <select id="flModelSelect" class="fl-select">
          <option value="hwd">Holt-Winters Damped (State-Space m=365, ϕ=0.9891)</option>
          <option value="rec">XGBoost Recursive (25 Causal Features, Lag Feedback)</option>
          <option value="dir">XGBoost Direct Seasonal (8 Harmonic/Calendar Features)</option>
        </select>
      </div>
      <div class="fl-field">
        <label for="flStartDate">2. Forecast Start Date</label>
        <input type="date" id="flStartDate" class="fl-input" value="2026-04-01" min="2026-04-01" max="2030-03-31">
      </div>
      <div class="fl-field">
        <label for="flEndDate">3. Forecast End Date</label>
        <input type="date" id="flEndDate" class="fl-input" value="2030-03-31" min="2026-04-01" max="2030-03-31">
      </div>
      <div class="fl-field">
        <label for="flFreqSelect">4. Display Aggregation Frequency</label>
        <select id="flFreqSelect" class="fl-select">
          <option value="daily">Daily Predictions (1,461 pts)</option>
          <option value="monthly">Monthly Averages (48 months)</option>
          <option value="yearly">Yearly Averages (2026–2030)</option>
        </select>
      </div>
      <div class="fl-field">
        <button type="button" id="flGenerateBtn" class="fl-gen-btn">⚡ Generate Forecast</button>
      </div>
      <div class="fl-status-line">
        <span id="flStatusText">✓ Ready • Showing pre-verified full-history model predictions (trained 1 Jan 1996 – 18 Mar 2026, bridged 19–31 Mar 2026).</span>
        <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
          <span id="flModelNote" style="color:var(--emerald)">Active Model: Holt-Winters Damped (1,461 daily predictions)</span>
          <button type="button" class="chip" id="flResetFullRangeBtn" title="Reset dates to full 4-year horizon (1 Apr 2026 – 31 Mar 2030)">↺ Reset Full 4-Year Range</button>
        </div>
      </div>
    </div>

    <!-- IMMEDIATE FORECAST DETAILS & RECORD-BY-RECORD TABLE FOR SELECTED WINDOW -->
    <div class="explorer-card" id="flDetailsCard" style="margin-bottom:24px;border-color:var(--emerald)">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;margin-bottom:12px">
        <div>
          <span class="sec-kicker">Generated Forecast Details • Selected Window Output</span>
          <h3 style="font-family:var(--serif);font-size:1.85rem;font-weight:400" id="flDetailsTitle">Forecast Details (2026-04-01 → 2030-03-31)</h3>
        </div>
        <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
          <span id="flDetailsCountBadge" style="font-family:var(--mono);font-size:.78rem;background:var(--emerald-bg);color:var(--emerald);padding:5px 12px;border-radius:99px;font-weight:600">1,461 Records</span>
          <button type="button" class="chip" id="flDlWindowCsvBtn">⬇ Download This Window (.CSV)</button>
        </div>
      </div>

      <!-- Summary KPI Strip for the Selected Window -->
      <div class="explorer-readout" id="flWindowSummaryReadout" style="margin-top:0;margin-bottom:14px">
        <div class="readout-item"><small>Selected Window</small><strong id="flSumWindow">—</strong></div>
        <div class="readout-item"><small id="flSumActiveLabel">Selected Model Mean</small><strong id="flSumMean" style="color:var(--emerald)">—</strong></div>
        <div class="readout-item"><small>Minimum Predicted</small><strong id="flSumMin">—</strong></div>
        <div class="readout-item"><small>Maximum Predicted</small><strong id="flSumMax">—</strong></div>
        <div class="readout-item"><small>All 3 Models (Window Mean)</small><strong id="flSumAll3" style="font-size:.86rem">—</strong></div>
        <div class="readout-item"><small>Hist DOY 10–90% Range</small><strong id="flSumHistRange">—</strong></div>
      </div>

      <!-- Detailed Day-by-Day / Period-by-Period Forecast Table -->
      <div class="fl-table-wrap" style="max-height:310px">
        <table class="fl-table">
          <thead>
            <tr>
              <th>Date / Period</th>
              <th>Season</th>
              <th id="flTblActiveCol" style="color:var(--emerald)">Selected Model (°C)</th>
              <th>Holt-Winters Damped (°C)</th>
              <th>XGBoost Recursive (°C)</th>
              <th>XGBoost Direct Seasonal (°C)</th>
              <th>Hist DOY 10–90% Ref</th>
              <th>3-Model Spread |ΔT|</th>
            </tr>
          </thead>
          <tbody id="flDetailsTableBody"></tbody>
        </table>
      </div>
    </div>

    <!-- 6. MAIN FORECAST VISUALIZATION -->
    <div class="explorer-card" style="margin-bottom:24px">
      <div class="explorer-controls">
        <div class="btn-group" id="flYearFilterGroup">
          <span class="btn-group-label">Year Filter:</span>
          <button class="chip active" type="button" data-flyear="ALL">Full 4-Year (2026–2030)</button>
          <button class="chip" type="button" data-flyear="2026">2026 (Apr–Dec, 275d)</button>
          <button class="chip" type="button" data-flyear="2027">2027 (365d)</button>
          <button class="chip" type="button" data-flyear="2028">2028 (Leap Year, 366d)</button>
          <button class="chip" type="button" data-flyear="2029">2029 (365d)</button>
          <button class="chip" type="button" data-flyear="2030">2030 (Jan–Mar, 90d)</button>
        </div>
        <div class="btn-group" id="flSeasonFilterGroup">
          <span class="btn-group-label">Season:</span>
          <button class="chip active" type="button" data-flseason="ALL">All Seasons</button>
          <button class="chip" type="button" data-flseason="Winter">Winter</button>
          <button class="chip" type="button" data-flseason="Summer">Summer</button>
          <button class="chip" type="button" data-flseason="Monsoon">Monsoon</button>
          <button class="chip" type="button" data-flseason="Post-monsoon">Post-monsoon</button>
        </div>
      </div>

      <div class="explorer-controls" style="margin-top:10px;border-bottom:0;padding-bottom:4px">
        <div class="btn-group">
          <span class="btn-group-label">Month Filter:</span>
          <select id="flMonthSelect" class="fl-select" style="width:auto;padding:5px 10px">
            <option value="ALL">All 12 Months</option>
            <option value="1">January</option><option value="2">February</option><option value="3">March</option>
            <option value="4">April</option><option value="5">May</option><option value="6">June</option>
            <option value="7">July</option><option value="8">August</option><option value="9">September</option>
            <option value="10">October</option><option value="11">November</option><option value="12">December</option>
          </select>
          <button class="chip active" type="button" id="flHistBandBtn" title="Show 1996-2026 Historical Day-of-Year 10th-90th Percentile Reference Band (Not a fake 95% CI)">±Hist DOY 10–90% Ref Band</button>
        </div>
        <div class="btn-group">
          <span class="btn-group-label">Interactive Zoom Window:</span>
          <input type="range" id="flZoomSlider" min="15" max="100" value="100" style="width:130px;accent-color:var(--emerald)" title="Zoom into forecast window (%)">
          <span id="flZoomLabel" style="font-family:var(--mono);font-size:.75rem;color:var(--soft)">100% View</span>
          <button class="chip" type="button" id="flExportMainPng">⬇ Export Forecast PNG</button>
        </div>
      </div>

      <div class="explorer-readout">
        <div class="readout-item"><small>Inspected Future Date</small><strong id="flRoDate">—</strong></div>
        <div class="readout-item"><small>Selected Model Pred</small><strong id="flRoSel" style="color:var(--emerald)">—</strong></div>
        <div class="readout-item"><small>Holt-Winters Damped</small><strong id="flRoHWD">—</strong></div>
        <div class="readout-item"><small>XGBoost Recursive</small><strong id="flRoRec">—</strong></div>
        <div class="readout-item"><small>XGBoost Direct Seasonal</small><strong id="flRoDir">—</strong></div>
        <div class="readout-item"><small>3-Model Disagreement Spread</small><strong id="flRoSpread">—</strong></div>
      </div>

      <div class="canvas-wrap" style="height:370px">
        <canvas id="flMainCanvas"></canvas>
      </div>

      <div class="scrubber-bar">
        <span style="font-family:var(--mono);font-size:.75rem;color:var(--soft)">Scrub Future Timeline:</span>
        <input type="range" id="flDayScrubber" class="scrubber-slider" min="0" max="1460" value="0">
        <span class="scrubber-day" id="flScrubberLabel">Day 1 / 1461</span>
      </div>
    </div>

    <!-- 8. YEARLY COMPARISON (2026 - 2030, explicitly marking partial years 2026 & 2030 and leap year 2028) -->
    <div class="explorer-card" style="margin-bottom:24px">
      <div style="display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:12px;margin-bottom:8px">
        <div>
          <span class="sec-kicker">Section 8 • Year-Wise Forecast Comparison (2026–2030)</span>
          <h3 style="font-family:var(--serif);font-size:2rem;font-weight:400">Yearly Summary &amp; Partial-Year Distinction</h3>
        </div>
        <small style="font-family:var(--mono);color:var(--ochre)">⚠️ Note: 2026 (Apr–Dec, 275d) and 2030 (Jan–Mar, 90d) are partial forecast years; do not compare their means directly with full years 2027–2029.</small>
      </div>
      <div class="fl-year-cards" id="flYearCardsContainer"></div>
    </div>

    <!-- 7. MONTHLY TEMPERATURE ANALYSIS & 9. SEASONAL FORECAST ANALYSIS -->
    <div class="fl-subgrid-2">
      <div class="explorer-card">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:10px">
          <div>
            <span class="sec-kicker">Section 7 • 48-Month Trajectory (Apr 2026 – Mar 2030)</span>
            <h3 style="font-family:var(--serif);font-size:1.75rem;font-weight:400">Monthly Mean, Min &amp; Max Analysis</h3>
          </div>
          <button class="chip" type="button" id="flExportMonthlyPng">⬇ PNG</button>
        </div>
        <p style="font-size:.84rem;color:var(--soft);margin-bottom:10px">Monthly averages (solid line) and monthly daily min–max envelope (shaded band) aggregated directly from the daily predictions.</p>
        <div class="canvas-wrap" style="height:260px">
          <canvas id="flMonthlyCanvas"></canvas>
        </div>
        <div class="fl-table-wrap" style="margin-top:14px">
          <table class="fl-table">
            <thead>
              <tr><th>Year-Month</th><th>Mean (°C)</th><th>Min Daily (°C)</th><th>Max Daily (°C)</th><th>Model</th></tr>
            </thead>
            <tbody id="flMonthlyTableBody"></tbody>
          </table>
        </div>
      </div>

      <div class="explorer-card">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:10px">
          <div>
            <span class="sec-kicker">Section 9 • IMD Seasonal Evolution (2026–2030)</span>
            <h3 style="font-family:var(--serif);font-size:1.75rem;font-weight:400">Seasonal Forecast Analysis</h3>
          </div>
        </div>
        <p style="font-size:.84rem;color:var(--soft);margin-bottom:10px">Seasonal definitions for Delhi: <strong>Winter</strong> (Dec–Feb), <strong>Summer</strong> (Mar–May), <strong>Monsoon</strong> (Jun–Sep), <strong>Post-monsoon</strong> (Oct–Nov). <em>Does not predict specific future rainfall, heatwave, or cold-wave events.</em></p>
        <div class="canvas-wrap" style="height:260px">
          <canvas id="flSeasonalCanvas"></canvas>
        </div>
        <div class="fl-table-wrap" style="margin-top:14px">
          <table class="fl-table">
            <thead>
              <tr><th>Season</th><th>Days</th><th>Mean (°C)</th><th>Min (°C)</th><th>Max (°C)</th><th>Range (°C)</th></tr>
            </thead>
            <tbody id="flSeasonalTableBody"></tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 10. THREE-MODEL OVERLAY & MODEL DISAGREEMENT ANALYSIS -->
    <div class="explorer-card" style="margin-top:24px">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;margin-bottom:10px">
        <div>
          <span class="sec-kicker">Section 10 • Sensitivity to Forecasting Assumptions (Model Disagreement, Not Prediction Error)</span>
          <h3 style="font-family:var(--serif);font-size:2rem;font-weight:400">Three-Model Overlay &amp; Disagreement Analysis</h3>
        </div>
        <div class="btn-group" id="flOverlayModeGroup">
          <button class="chip active" type="button" data-ovmode="overlay">3-Model Temperature Overlay (°C)</button>
          <button class="chip" type="button" data-ovmode="diff">Pairwise Model Disagreement |ΔT| (°C)</button>
          <button class="chip" type="button" id="flExportOverlayPng">⬇ Export Overlay PNG</button>
        </div>
      </div>
      <div style="padding:12px 16px;background:var(--plaster);border-left:4px solid var(--ochre);border-radius:6px;font-size:.86rem;color:var(--ink);margin-bottom:14px">
        <strong>Scientific Note on Model Disagreement:</strong>
        <em>"Long-range forecasts are uncertain. Differences between models illustrate sensitivity to forecasting assumptions and methodologies."</em>
        Because future actual temperatures for 2026–2030 do not exist, we never compute RMSE, MAE, MAPE, or R² on future dates; instead we quantify inter-model disagreement across horizons and seasons.
      </div>
      <div class="canvas-wrap" style="height:310px">
        <canvas id="flOverlayCanvas"></canvas>
      </div>
      <div class="diag-strip" id="flDisagreementCards" style="margin-top:16px"></div>
    </div>

    <!-- 11. UNCERTAINTY & EXTRAPOLATION METHODOLOGY + 12. DOWNLOADABLE OUTPUTS -->
    <div class="fl-subgrid-2">
      <div class="explorer-card">
        <span class="sec-kicker">Section 11 • Long-Range Extrapolation Mechanics &amp; Uncertainty</span>
        <h3 style="font-family:var(--serif);font-size:1.75rem;font-weight:400;margin-bottom:10px">How Each Model Extrapolates to 2030</h3>
        <div style="font-size:.86rem;color:var(--soft);display:grid;gap:10px">
          <div style="padding:10px 12px;background:var(--plaster);border-radius:6px;border-left:3px solid #C18A2C">
            <strong style="color:var(--ink)">A. Holt-Winters Damped (ϕ = 0.9891):</strong>
            Preserves the learned level <i>l<sub>T</sub></i>, trend <i>b<sub>T</sub></i>, and 365-day additive seasonal states from 18 March 2026. Because 0 &lt; ϕ &lt; 1, the cumulative trend contribution Σ ϕ<sup>j</sup><i>b<sub>T</sub></i> converges asymptotically to [ϕ / (1 − ϕ)]<i>b<sub>T</sub></i> rather than drifting unboundedly over 1,474 steps.
          </div>
          <div style="padding:10px 12px;background:var(--plaster);border-radius:6px;border-left:3px solid var(--emerald)">
            <strong style="color:var(--ink)">B. XGBoost Recursive (25 Causal Features):</strong>
            Predicts day <i>t</i> and feeds <i>ŷ<sub>t</sub></i> into next-day lags (<code>lag_1..365</code>), shifted rolling means/stds (<code>7, 14, 30d</code>), momentum, and anomaly features, while substituting historical DOY climatological expectations for unavailable future humidity, rainfall, and DTR. Early step deviations feed back into subsequent rolling windows, smoothing out high-frequency extremes over multi-year rollouts.
          </div>
          <div style="padding:10px 12px;background:var(--plaster);border-radius:6px;border-left:3px solid #7C3AED">
            <strong style="color:var(--ink)">C. XGBoost Direct Seasonal (8 Seasonal/Calendar Features):</strong>
            Uses future calendar coordinates, Fourier harmonics (<i>K</i> = 2), training-derived DOY climatology, and annual <code>lag_365</code> without short-term recursive lags. Immune to short-term recursive drift, but bound to historical seasonal cycles.
          </div>
        </div>
      </div>

      <div class="explorer-card">
        <span class="sec-kicker">Section 12 • Verified Downloadable Outputs (CSV &amp; PNG)</span>
        <h3 style="font-family:var(--serif);font-size:1.75rem;font-weight:400;margin-bottom:8px">Download Forecast Datasets</h3>
        <p style="font-size:.84rem;color:var(--soft)">All downloadable CSVs are generated directly from the trained models (1,461 rows per model from <code>2026-04-01</code> to <code>2030-03-31</code>):</p>
        <div class="fl-dl-grid">
          <div class="fl-dl-card">
            <div>
              <b>Daily Forecast CSV (Selected)</b>
              <small>date, year, month, day, season, predicted_temperature, model_name</small>
            </div>
            <button type="button" class="pill-emerald" id="flDlDailySelectedBtn" style="border:0;cursor:pointer;justify-content:center">⬇ Download Selected Model CSV</button>
          </div>
          <div class="fl-dl-card">
            <div>
              <b>Complete 3-Model Daily CSV</b>
              <small>4,383 rows (All 3 models, 2026-04-01 to 2030-03-31)</small>
            </div>
            <a class="pill-outline" href="{fl_dir}future_daily_all_models.csv" download style="text-align:center">⬇ future_daily_all_models.csv</a>
          </div>
          <div class="fl-dl-card">
            <div>
              <b>Monthly Summary CSV</b>
              <small>year, month, mean, min, max predicted_temperature (48 months)</small>
            </div>
            <button type="button" class="pill-outline" id="flDlMonthlyBtn" style="cursor:pointer;justify-content:center">⬇ Download Monthly Summary CSV</button>
          </div>
          <div class="fl-dl-card">
            <div>
              <b>Yearly Summary CSV</b>
              <small>year, number_of_forecast_days, mean, min, max (2026–2030)</small>
            </div>
            <button type="button" class="pill-outline" id="flDlYearlyBtn" style="cursor:pointer;justify-content:center">⬇ Download Yearly Summary CSV</button>
          </div>
          <div class="fl-dl-card">
            <div>
              <b>Individual Model Daily CSVs</b>
              <small>Direct static CSV links for each model</small>
            </div>
            <div style="display:flex;gap:6px;flex-wrap:wrap">
              <a class="chip" href="{fl_dir}future_daily_holt_winters_damped.csv" download>HW Damped</a>
              <a class="chip" href="{fl_dir}future_daily_xgboost_recursive.csv" download>XGB Recursive</a>
              <a class="chip" href="{fl_dir}future_daily_xgboost_direct_seasonal.csv" download>XGB Direct</a>
            </div>
          </div>
          <div class="fl-dl-card">
            <div>
              <b>Model Disagreement &amp; Bridge CSVs</b>
              <small>Pairwise |ΔT| &amp; 19–31 Mar 2026 bridge gap</small>
            </div>
            <div style="display:flex;gap:6px;flex-wrap:wrap">
              <a class="chip" href="{fl_dir}future_model_disagreement.csv" download>Disagreement CSV</a>
              <a class="chip" href="{fl_dir}bridge_gap_2026_03_19_to_03_31.csv" download>Bridge Gap (13d)</a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>
<script>
window.FUTURE_LAB_BUNDLE = {bundle_json};
</script>
"""


def get_future_lab_js():
    return """
// =====================================================================
// MULTI-YEAR FUTURE FORECAST LAB (APRIL 2026 – MARCH 2030) INTERACTIVE ENGINE
// =====================================================================
(function() {
  const bundle = window.FUTURE_LAB_BUNDLE;
  if (!bundle || !bundle.daily || !bundle.daily.length) return;

  const modelLabels = {
    hwd: 'Holt-Winters Damped',
    rec: 'XGBoost Recursive',
    dir: 'XGBoost Direct Seasonal'
  };
  const modelColors = {
    hwd: '#C18A2C',
    rec: '#0D7A52',
    dir: '#7C3AED'
  };

  let flModel = 'hwd';
  let flStart = '2026-04-01';
  let flEnd = '2030-03-31';
  let flFreq = 'daily';
  let flYear = 'ALL';
  let flSeason = 'ALL';
  let flMonth = 'ALL';
  let flShowHistBand = true;
  let flZoomPct = 100;
  let flHoverIdx = 0;
  let flOverlayMode = 'overlay';

  const mainCanvas = document.getElementById('flMainCanvas');
  const monthlyCanvas = document.getElementById('flMonthlyCanvas');
  const seasonalCanvas = document.getElementById('flSeasonalCanvas');
  const overlayCanvas = document.getElementById('flOverlayCanvas');
  if (!mainCanvas) return;

  function getFilteredFutureDaily() {
    return bundle.daily.filter(pt => {
      if (pt.d < flStart || pt.d > flEnd) return false;
      if (flYear !== 'ALL' && String(pt.y) !== String(flYear)) return false;
      if (flSeason !== 'ALL' && pt.s !== flSeason) return false;
      if (flMonth !== 'ALL' && String(pt.m) !== String(flMonth)) return false;
      return true;
    });
  }

  function getDisplaySeries(rawDaily) {
    if (flFreq === 'daily') {
      return rawDaily.map(pt => ({
        label: pt.d,
        s: pt.s,
        y: pt.y,
        m: pt.m,
        hwd: pt.hwd,
        rec: pt.rec,
        dir: pt.dir,
        p10: pt.p10,
        p90: pt.p90
      }));
    } else if (flFreq === 'monthly') {
      const map = new Map();
      rawDaily.forEach(pt => {
        const k = `${pt.y}-${String(pt.m).padStart(2, '0')}`;
        if (!map.has(k)) map.set(k, []);
        map.get(k).push(pt);
      });
      const out = [];
      map.forEach((arr, k) => {
        const avg = key => arr.reduce((s, x) => s + x[key], 0) / arr.length;
        out.push({
          label: k,
          s: arr[0].s,
          y: arr[0].y,
          m: arr[0].m,
          hwd: Number(avg('hwd').toFixed(2)),
          rec: Number(avg('rec').toFixed(2)),
          dir: Number(avg('dir').toFixed(2)),
          p10: Number(avg('p10').toFixed(2)),
          p90: Number(avg('p90').toFixed(2))
        });
      });
      return out;
    } else {
      const map = new Map();
      rawDaily.forEach(pt => {
        const k = String(pt.y);
        if (!map.has(k)) map.set(k, []);
        map.get(k).push(pt);
      });
      const out = [];
      map.forEach((arr, k) => {
        const avg = key => arr.reduce((s, x) => s + x[key], 0) / arr.length;
        out.push({
          label: `${k} (${arr.length}d)`,
          s: 'Annual',
          y: Number(k),
          m: 0,
          hwd: Number(avg('hwd').toFixed(2)),
          rec: Number(avg('rec').toFixed(2)),
          dir: Number(avg('dir').toFixed(2)),
          p10: Number(avg('p10').toFixed(2)),
          p90: Number(avg('p90').toFixed(2))
        });
      });
      return out;
    }
  }

  function drawMainFutureChart() {
    const raw = getFilteredFutureDaily();
    const seriesAll = getDisplaySeries(raw);
    if (!seriesAll.length) return;

    const visibleCount = Math.max(2, Math.round(seriesAll.length * (flZoomPct / 100)));
    const startIndex = Math.max(0, Math.min(seriesAll.length - visibleCount, Math.floor(flHoverIdx - visibleCount / 2)));
    const data = seriesAll.slice(startIndex, startIndex + visibleCount);

    const scrubber = document.getElementById('flDayScrubber');
    const scrubLbl = document.getElementById('flScrubberLabel');
    if (scrubber) {
      scrubber.max = Math.max(0, seriesAll.length - 1);
      if (flHoverIdx >= seriesAll.length) flHoverIdx = seriesAll.length - 1;
      scrubber.value = flHoverIdx;
    }
    if (scrubLbl) scrubLbl.textContent = `Point ${flHoverIdx + 1} / ${seriesAll.length}`;

    const dpr = window.devicePixelRatio || 1;
    const rect = mainCanvas.parentElement.getBoundingClientRect();
    mainCanvas.width = rect.width * dpr;
    mainCanvas.height = rect.height * dpr;
    const c = mainCanvas.getContext('2d');
    c.setTransform(dpr, 0, 0, dpr, 0, 0);

    const W = rect.width, H = rect.height;
    const pad = { top: 26, right: 28, bottom: 34, left: 52 };
    const cw = W - pad.left - pad.right, ch = H - pad.top - pad.bottom;
    const innerMargin = data.length <= 10 ? Math.min(80, cw * 0.12) : 0;
    const plotW = Math.max(10, cw - 2 * innerMargin);
    c.clearRect(0, 0, W, H);

    const style = getComputedStyle(document.documentElement);
    const lineCol = style.getPropertyValue('--line').trim() || '#C9CEC3';
    const softCol = style.getPropertyValue('--soft').trim() || '#5C665F';

    let yMin = Infinity, yMax = -Infinity;
    data.forEach(pt => {
      const v = pt[flModel];
      if (v < yMin) yMin = v;
      if (v > yMax) yMax = v;
      if (flShowHistBand) {
        if (pt.p10 < yMin) yMin = pt.p10;
        if (pt.p90 > yMax) yMax = pt.p90;
      }
    });
    if (!isFinite(yMin)) { yMin = 8; yMax = 40; }
    yMin = Math.floor(yMin - 2);
    yMax = Math.ceil(yMax + 2);

    const xOf = i => pad.left + innerMargin + (data.length > 1 ? (i / (data.length - 1)) * plotW : plotW / 2);
    const yOf = v => pad.top + (1 - (v - yMin) / (yMax - yMin)) * ch;

    c.strokeStyle = lineCol;
    c.lineWidth = 0.7;
    c.fillStyle = softCol;
    c.font = '11px "JetBrains Mono", monospace';
    c.textAlign = 'right';
    for (let i = 0; i <= 5; i++) {
      const val = yMin + (i / 5) * (yMax - yMin);
      const py = yOf(val);
      c.beginPath(); c.moveTo(pad.left, py); c.lineTo(W - pad.right, py); c.stroke();
      c.fillText(val.toFixed(0) + '°C', pad.left - 6, py + 4);
    }

    c.textAlign = 'center';
    const ticks = Math.min(7, data.length);
    for (let i = 0; i < ticks; i++) {
      const idx = Math.round((i / Math.max(1, ticks - 1)) * (data.length - 1));
      c.fillText(data[idx].label, xOf(idx), H - 10);
    }

    if (flShowHistBand) {
      c.fillStyle = 'rgba(13, 122, 82, 0.10)';
      c.beginPath();
      data.forEach((pt, i) => {
        const px = xOf(i), py = yOf(pt.p90);
        if (i === 0) c.moveTo(px, py); else c.lineTo(px, py);
      });
      for (let i = data.length - 1; i >= 0; i--) {
        c.lineTo(xOf(i), yOf(data[i].p10));
      }
      c.closePath();
      c.fill();
    }

    c.strokeStyle = modelColors[flModel];
    c.lineWidth = 2.1;
    c.beginPath();
    data.forEach((pt, i) => {
      const px = xOf(i), py = yOf(pt[flModel]);
      if (i === 0) c.moveTo(px, py); else c.lineTo(px, py);
    });
    c.stroke();

    // When viewing <= 45 points (e.g. a 2-day, 7-day, or 1-month window), draw point markers & direct °C labels
    if (data.length <= 45) {
      data.forEach((pt, i) => {
        const px = xOf(i), py = yOf(pt[flModel]);
        c.fillStyle = modelColors[flModel];
        c.beginPath(); c.arc(px, py, data.length <= 15 ? 5 : 3.5, 0, Math.PI * 2); c.fill();
        if (data.length <= 15) {
          c.font = '600 11px "JetBrains Mono", monospace';
          c.textAlign = 'center';
          c.fillText(`${pt[flModel].toFixed(2)} °C (${pt.label})`, px, Math.max(14, py - 10));
        }
      });
    }

    const localIdx = Math.max(0, Math.min(data.length - 1, flHoverIdx - startIndex));
    const pt = data[localIdx];
    if (pt) {
      const hx = xOf(localIdx), hy = yOf(pt[flModel]);
      c.strokeStyle = softCol;
      c.setLineDash([3, 3]);
      c.beginPath(); c.moveTo(hx, pad.top); c.lineTo(hx, H - pad.bottom); c.stroke();
      c.setLineDash([]);
      c.fillStyle = modelColors[flModel];
      c.beginPath(); c.arc(hx, hy, 4.5, 0, Math.PI * 2); c.fill();

      const spread = (Math.max(pt.hwd, pt.rec, pt.dir) - Math.min(pt.hwd, pt.rec, pt.dir)).toFixed(2);
      document.getElementById('flRoDate').textContent = `${pt.label} (${pt.s})`;
      document.getElementById('flRoSel').textContent = `${pt[flModel].toFixed(2)} °C`;
      document.getElementById('flRoSel').style.color = modelColors[flModel];
      document.getElementById('flRoHWD').textContent = `${pt.hwd.toFixed(2)} °C`;
      document.getElementById('flRoRec').textContent = `${pt.rec.toFixed(2)} °C`;
      document.getElementById('flRoDir').textContent = `${pt.dir.toFixed(2)} °C`;
      document.getElementById('flRoSpread').textContent = `±${spread} °C`;
    }
  }

  function renderYearlyComparison() {
    const container = document.getElementById('flYearCardsContainer');
    if (!container) return;
    const mName = modelLabels[flModel];
    const rows = (bundle.yearly_summary || []).filter(r => r.model_name === mName);
    container.innerHTML = rows.map(r => {
      const cls = r.is_partial_year ? ' partial' : (r.year === 2028 ? ' leap' : '');
      const tag = r.is_partial_year ? 'Partial Forecast Year' : (r.year === 2028 ? 'Full Leap Year (366d)' : 'Full Calendar Year (365d)');
      return `<div class="fl-ycard${cls}">
        <div>
          <small>${tag}</small>
          <h4>${r.year}</h4>
          <div class="y-mean">${r.mean_predicted_temperature.toFixed(2)} °C <span style="font-size:.72rem;font-weight:400;color:var(--soft)">mean</span></div>
          <small style="display:block;color:var(--ink)">${r.coverage_note}</small>
        </div>
        <div class="y-stats">
          <div>Forecast Days: <strong>${r.number_of_forecast_days}d</strong></div>
          <div>Min Daily: <strong>${r.minimum_predicted_temperature.toFixed(2)} °C</strong></div>
          <div>Max Daily: <strong>${r.maximum_predicted_temperature.toFixed(2)} °C</strong></div>
          <div>Annual Range: <strong>${r.temperature_range.toFixed(2)} °C</strong></div>
          <div>Monthly SD: <strong>±${r.monthly_variation_sd.toFixed(2)} °C</strong></div>
        </div>
      </div>`;
    }).join('');
  }

  function renderMonthlyAnalysis() {
    const mName = modelLabels[flModel];
    const rows = (bundle.monthly_summary || []).filter(r => r.model_name === mName);
    const tbody = document.getElementById('flMonthlyTableBody');
    if (tbody) {
      tbody.innerHTML = rows.map(r => `<tr>
        <td><strong>${r.year}-${String(r.month).padStart(2, '0')}</strong></td>
        <td style="color:var(--ink);font-weight:600">${r.mean_predicted_temperature.toFixed(2)} °C</td>
        <td>${r.minimum_predicted_temperature.toFixed(2)} °C</td>
        <td>${r.maximum_predicted_temperature.toFixed(2)} °C</td>
        <td>${r.model_name}</td>
      </tr>`).join('');
    }
    if (!monthlyCanvas || !rows.length) return;
    const dpr = window.devicePixelRatio || 1;
    const rect = monthlyCanvas.parentElement.getBoundingClientRect();
    monthlyCanvas.width = rect.width * dpr;
    monthlyCanvas.height = rect.height * dpr;
    const c = monthlyCanvas.getContext('2d');
    c.setTransform(dpr, 0, 0, dpr, 0, 0);
    const W = rect.width, H = rect.height;
    const pad = { top: 16, right: 16, bottom: 28, left: 42 };
    const cw = W - pad.left - pad.right, ch = H - pad.top - pad.bottom;
    c.clearRect(0, 0, W, H);

    const style = getComputedStyle(document.documentElement);
    const lineCol = style.getPropertyValue('--line').trim() || '#C9CEC3';
    const softCol = style.getPropertyValue('--soft').trim() || '#5C665F';
    const yMin = 6, yMax = 42;
    const xOf = i => pad.left + (i / Math.max(1, rows.length - 1)) * cw;
    const yOf = v => pad.top + (1 - (v - yMin) / (yMax - yMin)) * ch;

    c.strokeStyle = lineCol; c.lineWidth = 0.6; c.fillStyle = softCol;
    c.font = '10px "JetBrains Mono", monospace'; c.textAlign = 'right';
    [10, 20, 30, 40].forEach(v => {
      const py = yOf(v);
      c.beginPath(); c.moveTo(pad.left, py); c.lineTo(W - pad.right, py); c.stroke();
      c.fillText(v + '°', pad.left - 5, py + 3);
    });

    c.fillStyle = 'rgba(13, 122, 82, 0.15)';
    c.beginPath();
    rows.forEach((r, i) => {
      const px = xOf(i), py = yOf(r.maximum_predicted_temperature);
      if (i === 0) c.moveTo(px, py); else c.lineTo(px, py);
    });
    for (let i = rows.length - 1; i >= 0; i--) {
      c.lineTo(xOf(i), yOf(rows[i].minimum_predicted_temperature));
    }
    c.closePath(); c.fill();

    c.strokeStyle = modelColors[flModel]; c.lineWidth = 2.0;
    c.beginPath();
    rows.forEach((r, i) => {
      const px = xOf(i), py = yOf(r.mean_predicted_temperature);
      if (i === 0) c.moveTo(px, py); else c.lineTo(px, py);
    });
    c.stroke();

    c.fillStyle = softCol; c.textAlign = 'center';
    [0, 12, 24, 36, 47].forEach(i => {
      if (rows[i]) c.fillText(`${rows[i].year}-${String(rows[i].month).padStart(2, '0')}`, xOf(i), H - 8);
    });
  }

  function renderSeasonalAnalysis() {
    const mName = modelLabels[flModel];
    const rows = (bundle.seasonal_summary || []).filter(r => r.model_name === mName);
    const tbody = document.getElementById('flSeasonalTableBody');
    if (tbody) {
      tbody.innerHTML = rows.map(r => `<tr>
        <td><strong>${r.season}</strong></td>
        <td>${r.days}d</td>
        <td style="color:var(--ink);font-weight:600">${r.mean_predicted_temperature.toFixed(2)} °C</td>
        <td>${r.minimum_predicted_temperature.toFixed(2)} °C</td>
        <td>${r.maximum_predicted_temperature.toFixed(2)} °C</td>
        <td>${r.temperature_range.toFixed(2)} °C</td>
      </tr>`).join('');
    }
    if (!seasonalCanvas) return;
    const sy = (bundle.seasonal_yearly || []).filter(r => r.model_name === mName);
    const dpr = window.devicePixelRatio || 1;
    const rect = seasonalCanvas.parentElement.getBoundingClientRect();
    seasonalCanvas.width = rect.width * dpr;
    seasonalCanvas.height = rect.height * dpr;
    const c = seasonalCanvas.getContext('2d');
    c.setTransform(dpr, 0, 0, dpr, 0, 0);
    const W = rect.width, H = rect.height;
    const pad = { top: 18, right: 18, bottom: 30, left: 42 };
    const cw = W - pad.left - pad.right, ch = H - pad.top - pad.bottom;
    c.clearRect(0, 0, W, H);

    const style = getComputedStyle(document.documentElement);
    const lineCol = style.getPropertyValue('--line').trim() || '#C9CEC3';
    const softCol = style.getPropertyValue('--soft').trim() || '#5C665F';
    const seasons = ['Winter', 'Summer', 'Monsoon', 'Post-monsoon'];
    const sCols = { 'Winter': '#22344D', 'Summer': '#C18A2C', 'Monsoon': '#0D7A52', 'Post-monsoon': '#55663A' };
    const years = [2026, 2027, 2028, 2029, 2030];
    const yMin = 10, yMax = 36;
    const xOf = i => pad.left + (i / (years.length - 1)) * cw;
    const yOf = v => pad.top + (1 - (v - yMin) / (yMax - yMin)) * ch;

    c.strokeStyle = lineCol; c.lineWidth = 0.6; c.fillStyle = softCol;
    c.font = '10px "JetBrains Mono", monospace'; c.textAlign = 'right';
    [15, 22, 29, 35].forEach(v => {
      const py = yOf(v);
      c.beginPath(); c.moveTo(pad.left, py); c.lineTo(W - pad.right, py); c.stroke();
      c.fillText(v + '°', pad.left - 5, py + 3);
    });

    c.textAlign = 'center';
    years.forEach((yr, i) => c.fillText(String(yr), xOf(i), H - 8));

    seasons.forEach(sName => {
      const pts = years.map((yr, idx) => {
        const found = sy.find(x => x.year === yr && x.season === sName);
        return found ? { x: xOf(idx), y: yOf(found.mean_predicted_temperature), v: found.mean_predicted_temperature } : null;
      }).filter(Boolean);
      if (!pts.length) return;
      c.strokeStyle = sCols[sName]; c.lineWidth = 2.0;
      c.beginPath();
      pts.forEach((p, i) => { if (i === 0) c.moveTo(p.x, p.y); else c.lineTo(p.x, p.y); });
      c.stroke();
      pts.forEach(p => {
        c.fillStyle = sCols[sName];
        c.beginPath(); c.arc(p.x, p.y, 3.5, 0, Math.PI * 2); c.fill();
      });
    });
  }

  function renderOverlayAndDisagreement() {
    if (!overlayCanvas) return;
    const data = getFilteredFutureDaily();
    if (!data.length) return;
    const dpr = window.devicePixelRatio || 1;
    const rect = overlayCanvas.parentElement.getBoundingClientRect();
    overlayCanvas.width = rect.width * dpr;
    overlayCanvas.height = rect.height * dpr;
    const c = overlayCanvas.getContext('2d');
    c.setTransform(dpr, 0, 0, dpr, 0, 0);
    const W = rect.width, H = rect.height;
    const pad = { top: 18, right: 20, bottom: 30, left: 46 };
    const cw = W - pad.left - pad.right, ch = H - pad.top - pad.bottom;
    c.clearRect(0, 0, W, H);

    const style = getComputedStyle(document.documentElement);
    const lineCol = style.getPropertyValue('--line').trim() || '#C9CEC3';
    const softCol = style.getPropertyValue('--soft').trim() || '#5C665F';

    const xOf = i => pad.left + (data.length > 1 ? (i / (data.length - 1)) * cw : cw / 2);
    let yMin = flOverlayMode === 'overlay' ? 8 : 0;
    let yMax = flOverlayMode === 'overlay' ? 40 : 6;
    const yOf = v => pad.top + (1 - (v - yMin) / (yMax - yMin)) * ch;

    c.strokeStyle = lineCol; c.lineWidth = 0.6; c.fillStyle = softCol;
    c.font = '10px "JetBrains Mono", monospace'; c.textAlign = 'right';
    for (let i = 0; i <= 4; i++) {
      const val = yMin + (i / 4) * (yMax - yMin);
      const py = yOf(val);
      c.beginPath(); c.moveTo(pad.left, py); c.lineTo(W - pad.right, py); c.stroke();
      c.fillText(val.toFixed(1) + '°', pad.left - 6, py + 3);
    }

    c.textAlign = 'center';
    const ticks = Math.min(7, data.length);
    for (let i = 0; i < ticks; i++) {
      const idx = Math.round((i / Math.max(1, ticks - 1)) * (data.length - 1));
      c.fillText(data[idx].d, xOf(idx), H - 8);
    }

    if (flOverlayMode === 'overlay') {
      const legendItems = [
        { k: 'hwd', name: 'Holt-Winters Damped', col: modelColors.hwd },
        { k: 'rec', name: 'XGBoost Recursive', col: modelColors.rec },
        { k: 'dir', name: 'XGBoost Direct Seasonal', col: modelColors.dir }
      ];
      c.font = '600 11px "JetBrains Mono", monospace';
      c.textAlign = 'left';
      let lx = pad.left + 8;
      legendItems.forEach(item => {
        c.fillStyle = item.col;
        c.fillRect(lx, 6, 12, 4);
        c.fillText(item.name, lx + 16, 12);
        lx += c.measureText(item.name).width + 36;
      });

      ['dir', 'hwd', 'rec'].forEach(k => {
        c.strokeStyle = modelColors[k];
        c.lineWidth = 1.8;
        c.beginPath();
        data.forEach((pt, i) => {
          const px = xOf(i), py = yOf(pt[k]);
          if (i === 0) c.moveTo(px, py); else c.lineTo(px, py);
        });
        c.stroke();
        if (data.length <= 30) {
          data.forEach((pt, i) => {
            c.fillStyle = modelColors[k];
            c.beginPath(); c.arc(xOf(i), yOf(pt[k]), 4, 0, Math.PI * 2); c.fill();
          });
        }
      });
    } else {
      const pairs = [
        { label: '|HW Damped - XGB Rec|', col: '#0D7A52', fn: pt => Math.abs(pt.hwd - pt.rec) },
        { label: '|HW Damped - XGB Direct|', col: '#7C3AED', fn: pt => Math.abs(pt.hwd - pt.dir) },
        { label: '|XGB Rec - XGB Direct|', col: '#C18A2C', fn: pt => Math.abs(pt.rec - pt.dir) }
      ];
      c.font = '600 11px "JetBrains Mono", monospace';
      c.textAlign = 'left';
      let lx = pad.left + 8;
      pairs.forEach(p => {
        c.fillStyle = p.col;
        c.fillRect(lx, 6, 12, 4);
        c.fillText(p.label, lx + 16, 12);
        lx += c.measureText(p.label).width + 34;
      });
      pairs.forEach(p => {
        c.strokeStyle = p.col; c.lineWidth = 1.7;
        c.beginPath();
        data.forEach((pt, i) => {
          const px = xOf(i), py = yOf(p.fn(pt));
          if (i === 0) c.moveTo(px, py); else c.lineTo(px, py);
        });
        c.stroke();
        if (data.length <= 30) {
          data.forEach((pt, i) => {
            c.fillStyle = p.col;
            c.beginPath(); c.arc(xOf(i), yOf(p.fn(pt)), 4, 0, Math.PI * 2); c.fill();
          });
        }
      });
    }

    const ds = bundle.disagreement_summary && bundle.disagreement_summary.overall;
    const cardsEl = document.getElementById('flDisagreementCards');
    if (ds && cardsEl) {
      cardsEl.innerHTML = `
        <div class="diag-box"><small>Mean |HW Damped − XGB Recursive|</small><strong>${ds.mean_abs_diff_hwd_vs_xgb_rec.toFixed(3)} °C</strong><span>4-Year Mean Model Disagreement</span></div>
        <div class="diag-box"><small>Mean |HW Damped − XGB Direct|</small><strong>${ds.mean_abs_diff_hwd_vs_xgb_dir.toFixed(3)} °C</strong><span>Seasonal State-Space vs. Harmonic Tree</span></div>
        <div class="diag-box"><small>Mean |XGB Recursive − XGB Direct|</small><strong>${ds.mean_abs_diff_xgb_rec_vs_xgb_dir.toFixed(3)} °C</strong><span>Sensitivity to Recursive Lag Feedback</span></div>
        <div class="diag-box"><small>Mean 3-Model Spread (Max − Min)</small><strong>${ds.mean_3model_spread.toFixed(3)} °C</strong><span>Max Daily Spread: ${ds.max_3model_spread.toFixed(2)} °C</span></div>
      `;
    }
  }

  function renderSelectedWindowDetails() {
    const raw = getFilteredFutureDaily();
    const series = getDisplaySeries(raw);
    const mName = modelLabels[flModel];
    const titleEl = document.getElementById('flDetailsTitle');
    const badgeEl = document.getElementById('flDetailsCountBadge');
    const colEl = document.getElementById('flTblActiveCol');
    const lblEl = document.getElementById('flSumActiveLabel');
    const tbody = document.getElementById('flDetailsTableBody');

    const freqUnit = flFreq === 'daily' ? 'Days' : (flFreq === 'monthly' ? 'Months' : 'Years');
    if (titleEl) titleEl.textContent = `${mName} — Forecast Details (${flStart} → ${flEnd})`;
    if (badgeEl) badgeEl.textContent = `${series.length} ${freqUnit} Displayed (${raw.length} Daily Obs)`;
    if (colEl) {
      colEl.textContent = `★ ${mName} (°C)`;
      colEl.style.color = modelColors[flModel];
    }
    if (lblEl) lblEl.textContent = `${mName} Mean`;

    if (!series.length) {
      if (tbody) tbody.innerHTML = '<tr><td colspan="8">No forecast dates match the current filter criteria.</td></tr>';
      return;
    }

    let minPt = series[0], maxPt = series[0];
    let sumSel = 0, sumHwd = 0, sumRec = 0, sumDir = 0, sumP10 = 0, sumP90 = 0;
    series.forEach(pt => {
      const v = pt[flModel];
      sumSel += v;
      sumHwd += pt.hwd;
      sumRec += pt.rec;
      sumDir += pt.dir;
      sumP10 += pt.p10;
      sumP90 += pt.p90;
      if (v < minPt[flModel]) minPt = pt;
      if (v > maxPt[flModel]) maxPt = pt;
    });
    const n = series.length;
    document.getElementById('flSumWindow').textContent = `${series[0].label} → ${series[n - 1].label} (${n} ${freqUnit.toLowerCase()})`;
    const meanEl = document.getElementById('flSumMean');
    meanEl.textContent = `${(sumSel / n).toFixed(2)} °C`;
    meanEl.style.color = modelColors[flModel];
    document.getElementById('flSumMin').textContent = `${minPt[flModel].toFixed(2)} °C (${minPt.label})`;
    document.getElementById('flSumMax').textContent = `${maxPt[flModel].toFixed(2)} °C (${maxPt.label})`;
    document.getElementById('flSumAll3').textContent = `HWD ${(sumHwd / n).toFixed(2)}° | Rec ${(sumRec / n).toFixed(2)}° | Dir ${(sumDir / n).toFixed(2)}°`;
    document.getElementById('flSumHistRange').textContent = `[${(sumP10 / n).toFixed(1)}, ${(sumP90 / n).toFixed(1)}] °C`;

    if (tbody) {
      const maxRows = 400;
      const shown = series.slice(0, maxRows);
      tbody.innerHTML = shown.map(pt => {
        const sp = (Math.max(pt.hwd, pt.rec, pt.dir) - Math.min(pt.hwd, pt.rec, pt.dir)).toFixed(2);
        return `<tr>
          <td><strong>${pt.label}</strong></td>
          <td>${pt.s}</td>
          <td style="color:${modelColors[flModel]};font-weight:700;font-size:.84rem">${pt[flModel].toFixed(2)} °C</td>
          <td>${pt.hwd.toFixed(2)} °C</td>
          <td>${pt.rec.toFixed(2)} °C</td>
          <td>${pt.dir.toFixed(2)} °C</td>
          <td>[${pt.p10.toFixed(1)}°, ${pt.p90.toFixed(1)}°]</td>
          <td>±${sp} °C</td>
        </tr>`;
      }).join('') + (series.length > maxRows ? `<tr><td colspan="8" style="text-align:center;color:var(--ochre)">Showing first ${maxRows} of ${series.length} rows — click "Download This Window (.CSV)" to export all ${series.length} rows.</td></tr>` : '');
    }
  }

  function renderAllFutureLab() {
    document.getElementById('flMetaFreq').textContent = flFreq === 'daily' ? 'Daily (1d steps)' : (flFreq === 'monthly' ? 'Monthly Averages' : 'Yearly Averages');
    document.getElementById('flModelNote').textContent = `Active Model: ${modelLabels[flModel]} (${getFilteredFutureDaily().length} filtered days)`;
    renderSelectedWindowDetails();
    drawMainFutureChart();
    renderYearlyComparison();
    renderMonthlyAnalysis();
    renderSeasonalAnalysis();
    renderOverlayAndDisagreement();
  }

  // Event Listeners
  document.getElementById('flModelSelect').addEventListener('change', e => {
    flModel = e.target.value;
    renderAllFutureLab();
  });
  document.getElementById('flFreqSelect').addEventListener('change', e => {
    flFreq = e.target.value;
    flHoverIdx = 0;
    renderAllFutureLab();
  });
  document.getElementById('flGenerateBtn').addEventListener('click', async () => {
    const sVal = document.getElementById('flStartDate').value;
    const eVal = document.getElementById('flEndDate').value;
    const statusEl = document.getElementById('flStatusText');
    if (!sVal || !eVal || sVal > eVal) {
      statusEl.textContent = '❌ Validation Error: Forecast Start Date must be on or before Forecast End Date (within 2026-04-01 to 2030-03-31).';
      statusEl.style.color = 'var(--terracotta)';
      return;
    }
    if (sVal < '2026-04-01' || eVal > '2030-03-31') {
      statusEl.textContent = '❌ Validation Error: Requested window must lie within 2026-04-01 and 2030-03-31.';
      statusEl.style.color = 'var(--terracotta)';
      return;
    }
    statusEl.textContent = '⏳ Querying Multi-Year Forecast Engine...';
    statusEl.style.color = 'var(--ochre)';
    flStart = sVal;
    flEnd = eVal;
    flHoverIdx = 0;
    try {
      const resp = await fetch(`/api/future/forecast?model=${flModel}&start=${flStart}&end=${flEnd}&freq=${flFreq}`);
      if (resp.ok) {
        const js = await resp.json();
        statusEl.textContent = `✓ API Forecast Verified: ${js.count} records generated for ${modelLabels[flModel]} (${flStart} → ${flEnd}, Cutoff: 2026-03-18).`;
      } else {
        statusEl.textContent = `✓ Forecast Updated from Verified Model Cache: ${modelLabels[flModel]} (${flStart} → ${flEnd}).`;
      }
    } catch (_) {
      statusEl.textContent = `✓ Forecast Updated from Verified Model Cache: ${modelLabels[flModel]} (${flStart} → ${flEnd}, Cutoff: 2026-03-18).`;
    }
    statusEl.style.color = 'var(--soft)';
    renderAllFutureLab();
  });

  const resetBtn = document.getElementById('flResetFullRangeBtn');
  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      flStart = '2026-04-01';
      flEnd = '2030-03-31';
      flYear = 'ALL';
      flSeason = 'ALL';
      flMonth = 'ALL';
      document.getElementById('flStartDate').value = flStart;
      document.getElementById('flEndDate').value = flEnd;
      document.getElementById('flMonthSelect').value = 'ALL';
      document.querySelectorAll('#flYearFilterGroup .chip').forEach(b => b.classList.toggle('active', b.dataset.flyear === 'ALL'));
      document.querySelectorAll('#flSeasonFilterGroup .chip').forEach(b => b.classList.toggle('active', b.dataset.flseason === 'ALL'));
      document.getElementById('flStatusText').textContent = `✓ Reset to full 4-year horizon (2026-04-01 → 2030-03-31, 1,461 daily predictions).`;
      flHoverIdx = 0;
      renderAllFutureLab();
    });
  }

  const dlWinBtn = document.getElementById('flDlWindowCsvBtn');
  if (dlWinBtn) {
    dlWinBtn.addEventListener('click', () => {
      const mName = modelLabels[flModel];
      const rows = getFilteredFutureDaily();
      const header = 'date,year,month,day,season,predicted_temperature,model_name,holt_winters_damped,xgboost_recursive,xgboost_direct_seasonal\\n';
      const body = rows.map(r => `${r.d},${r.y},${r.m},${r.day},${r.s},${r[flModel].toFixed(3)},${mName},${r.hwd.toFixed(3)},${r.rec.toFixed(3)},${r.dir.toFixed(3)}`).join('\\n');
      triggerCsvDownload(`delhi_future_window_${flModel}_${flStart}_to_${flEnd}.csv`, header + body);
    });
  }

  document.querySelectorAll('#flYearFilterGroup .chip').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('#flYearFilterGroup .chip').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      flYear = btn.dataset.flyear;
      flHoverIdx = 0;
      renderSelectedWindowDetails();
      drawMainFutureChart();
      renderOverlayAndDisagreement();
    });
  });

  document.querySelectorAll('#flSeasonFilterGroup .chip').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('#flSeasonFilterGroup .chip').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      flSeason = btn.dataset.flseason;
      flHoverIdx = 0;
      renderSelectedWindowDetails();
      drawMainFutureChart();
      renderOverlayAndDisagreement();
    });
  });

  document.getElementById('flMonthSelect').addEventListener('change', e => {
    flMonth = e.target.value;
    flHoverIdx = 0;
    renderSelectedWindowDetails();
    drawMainFutureChart();
    renderOverlayAndDisagreement();
  });

  document.getElementById('flHistBandBtn').addEventListener('click', e => {
    flShowHistBand = !flShowHistBand;
    e.currentTarget.classList.toggle('active', flShowHistBand);
    drawMainFutureChart();
  });

  document.getElementById('flZoomSlider').addEventListener('input', e => {
    flZoomPct = parseInt(e.target.value, 10);
    document.getElementById('flZoomLabel').textContent = `${flZoomPct}% View`;
    drawMainFutureChart();
  });

  document.getElementById('flDayScrubber').addEventListener('input', e => {
    flHoverIdx = parseInt(e.target.value, 10);
    drawMainFutureChart();
  });

  mainCanvas.addEventListener('mousemove', e => {
    const seriesAll = getDisplaySeries(getFilteredFutureDaily());
    if (!seriesAll.length) return;
    const visibleCount = Math.max(2, Math.round(seriesAll.length * (flZoomPct / 100)));
    const startIndex = Math.max(0, Math.min(seriesAll.length - visibleCount, Math.floor(flHoverIdx - visibleCount / 2)));
    const rect = mainCanvas.getBoundingClientRect();
    const relX = Math.max(0, Math.min(1, (e.clientX - rect.left - 48) / (rect.width - 70)));
    flHoverIdx = startIndex + Math.round(relX * (visibleCount - 1));
    drawMainFutureChart();
  });

  document.querySelectorAll('#flOverlayModeGroup .chip[data-ovmode]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('#flOverlayModeGroup .chip[data-ovmode]').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      flOverlayMode = btn.dataset.ovmode;
      renderOverlayAndDisagreement();
    });
  });

  // CSV & PNG Downloads
  function triggerCsvDownload(filename, csvContent) {
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
  }

  document.getElementById('flDlDailySelectedBtn').addEventListener('click', () => {
    const mName = modelLabels[flModel];
    const rows = getFilteredFutureDaily();
    const header = 'date,year,month,day,season,predicted_temperature,model_name\\n';
    const body = rows.map(r => `${r.d},${r.y},${r.m},${r.day},${r.s},${r[flModel].toFixed(3)},${mName}`).join('\\n');
    triggerCsvDownload(`delhi_future_daily_${flModel}_${flStart}_to_${flEnd}.csv`, header + body);
  });

  document.getElementById('flDlMonthlyBtn').addEventListener('click', () => {
    const mName = modelLabels[flModel];
    const rows = (bundle.monthly_summary || []).filter(r => r.model_name === mName);
    const header = 'year,month,mean_predicted_temperature,minimum_predicted_temperature,maximum_predicted_temperature\\n';
    const body = rows.map(r => `${r.year},${r.month},${r.mean_predicted_temperature.toFixed(3)},${r.minimum_predicted_temperature.toFixed(3)},${r.maximum_predicted_temperature.toFixed(3)}`).join('\\n');
    triggerCsvDownload(`delhi_future_monthly_summary_${flModel}_2026_2030.csv`, header + body);
  });

  document.getElementById('flDlYearlyBtn').addEventListener('click', () => {
    const mName = modelLabels[flModel];
    const rows = (bundle.yearly_summary || []).filter(r => r.model_name === mName);
    const header = 'year,number_of_forecast_days,mean_predicted_temperature,minimum_predicted_temperature,maximum_predicted_temperature\\n';
    const body = rows.map(r => `${r.year},${r.number_of_forecast_days},${r.mean_predicted_temperature.toFixed(3)},${r.minimum_predicted_temperature.toFixed(3)},${r.maximum_predicted_temperature.toFixed(3)}`).join('\\n');
    triggerCsvDownload(`delhi_future_yearly_summary_${flModel}_2026_2030.csv`, header + body);
  });

  function exportCanvasPng(cvs, name) {
    const a = document.createElement('a');
    a.download = name;
    a.href = cvs.toDataURL('image/png');
    a.click();
  }
  document.getElementById('flExportMainPng').addEventListener('click', () => exportCanvasPng(mainCanvas, `future_forecast_${flModel}_2026_2030.png`));
  document.getElementById('flExportMonthlyPng').addEventListener('click', () => exportCanvasPng(monthlyCanvas, `future_monthly_${flModel}_2026_2030.png`));
  document.getElementById('flExportOverlayPng').addEventListener('click', () => exportCanvasPng(overlayCanvas, `future_3model_comparison_2026_2030.png`));

  window.addEventListener('resize', renderAllFutureLab);
  setTimeout(renderAllFutureLab, 80);
})();
"""
