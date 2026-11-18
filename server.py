#!/usr/bin/env python3
"""
Delhi Weather Forecasting — Unified Web & REST API Server (Port 8000)
Serves the interactive HTML5 dashboards (`index.html`, `phase3_output/index.html`, `milestone2_output/index.html`)
and provides REST API endpoints for the Multi-Year Future Forecast Lab (1 April 2026 – 31 March 2030):
  - GET  /api/future/status
  - GET  /api/future/forecast?model=hwd|rec|dir&start=YYYY-MM-DD&end=YYYY-MM-DD&freq=daily|monthly|yearly
  - POST /api/future/generate
  - GET  /api/future/monthly?model=hwd|rec|dir|all
  - GET  /api/future/yearly?model=hwd|rec|dir|all
  - GET  /api/future/seasonal?model=hwd|rec|dir|all
  - GET  /api/future/comparison
  - GET  /api/future/download?type=daily|monthly|yearly|all&model=hwd|rec|dir
"""

import os
import json
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

BUNDLE_PATH = os.path.join("phase3_output", "future_forecast", "future_forecast_bundle.json")
_BUNDLE_CACHE = None

MODEL_KEY_TO_NAME = {
    "hwd": "Holt-Winters Damped",
    "rec": "XGBoost Recursive",
    "dir": "XGBoost Direct Seasonal",
    "Holt-Winters Damped": "Holt-Winters Damped",
    "XGBoost Recursive": "XGBoost Recursive",
    "XGBoost Direct Seasonal": "XGBoost Direct Seasonal",
}
MODEL_NAME_TO_KEY = {
    "Holt-Winters Damped": "hwd",
    "XGBoost Recursive": "rec",
    "XGBoost Direct Seasonal": "dir",
}


def get_bundle(force_regenerate=False):
    global _BUNDLE_CACHE
    if _BUNDLE_CACHE is None or force_regenerate:
        if not force_regenerate and os.path.exists(BUNDLE_PATH):
            with open(BUNDLE_PATH, "r", encoding="utf-8") as f:
                _BUNDLE_CACHE = json.load(f)
        else:
            from future_forecast_lab import generate_multiyear_forecasts
            _BUNDLE_CACHE = generate_multiyear_forecasts(verbose=False)
    return _BUNDLE_CACHE


class ForecastAPIHandler(SimpleHTTPRequestHandler):
    def _send_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_csv(self, filename, csv_text, status=200):
        body = csv_text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/csv; charset=utf-8")
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)

        if not path.startswith("/api/future/"):
            return super().do_GET()

        bundle = get_bundle()

        if path == "/api/future/status":
            return self._send_json({
                "status": "ok",
                "metadata": bundle["metadata"],
                "validation_checks": bundle["validation_checks"],
                "models": list(bundle["models"].keys()),
            })

        if path == "/api/future/forecast":
            m_req = qs.get("model", ["hwd"])[0]
            start_dt = qs.get("start", ["2026-04-01"])[0]
            end_dt = qs.get("end", ["2030-03-31"])[0]
            freq = qs.get("freq", ["daily"])[0]

            if m_req not in MODEL_KEY_TO_NAME:
                return self._send_json({"error": f"Unknown model '{m_req}'"}, status=400)
            if start_dt > end_dt or start_dt < "2026-04-01" or end_dt > "2030-03-31":
                return self._send_json({"error": "Date range must be within 2026-04-01 to 2030-03-31"}, status=400)

            m_name = MODEL_KEY_TO_NAME[m_req]
            m_key = MODEL_NAME_TO_KEY[m_name]
            filtered = [r for r in bundle["daily"] if start_dt <= r["d"] <= end_dt]

            if freq == "daily":
                records = [
                    {
                        "date": r["d"],
                        "year": r["y"],
                        "month": r["m"],
                        "day": r["day"],
                        "season": r["s"],
                        "predicted_temperature": r[m_key],
                        "model_name": m_name,
                    }
                    for r in filtered
                ]
            elif freq == "monthly":
                records = [r for r in bundle["monthly_summary"] if r["model_name"] == m_name]
            elif freq == "yearly":
                records = [r for r in bundle["yearly_summary"] if r["model_name"] == m_name]
            else:
                return self._send_json({"error": f"Invalid frequency '{freq}'"}, status=400)

            return self._send_json({
                "status": "ok",
                "model_name": m_name,
                "frequency": freq,
                "start_date": start_dt,
                "end_date": end_dt,
                "historical_cutoff": bundle["metadata"]["historical_cutoff"],
                "count": len(records),
                "records": records,
            })

        if path == "/api/future/monthly":
            m_req = qs.get("model", ["all"])[0]
            rows = bundle["monthly_summary"]
            if m_req != "all" and m_req in MODEL_KEY_TO_NAME:
                rows = [r for r in rows if r["model_name"] == MODEL_KEY_TO_NAME[m_req]]
            return self._send_json({"status": "ok", "count": len(rows), "records": rows})

        if path == "/api/future/yearly":
            m_req = qs.get("model", ["all"])[0]
            rows = bundle["yearly_summary"]
            if m_req != "all" and m_req in MODEL_KEY_TO_NAME:
                rows = [r for r in rows if r["model_name"] == MODEL_KEY_TO_NAME[m_req]]
            return self._send_json({"status": "ok", "count": len(rows), "records": rows})

        if path == "/api/future/seasonal":
            m_req = qs.get("model", ["all"])[0]
            rows = bundle["seasonal_summary"]
            if m_req != "all" and m_req in MODEL_KEY_TO_NAME:
                rows = [r for r in rows if r["model_name"] == MODEL_KEY_TO_NAME[m_req]]
            return self._send_json({"status": "ok", "count": len(rows), "records": rows})

        if path == "/api/future/comparison":
            return self._send_json({
                "status": "ok",
                "note": "Long-range forecasts are uncertain. Differences between models illustrate sensitivity to forecasting assumptions and methodologies.",
                "disagreement_summary": bundle["disagreement_summary"],
            })

        if path == "/api/future/download":
            dl_type = qs.get("type", ["daily"])[0]
            m_req = qs.get("model", ["hwd"])[0]
            m_name = MODEL_KEY_TO_NAME.get(m_req, "Holt-Winters Damped")
            m_key = MODEL_NAME_TO_KEY[m_name]

            if dl_type == "daily":
                header = "date,year,month,day,season,predicted_temperature,model_name\n"
                lines = [
                    f"{r['d']},{r['y']},{r['m']},{r['day']},{r['s']},{r[m_key]:.3f},{m_name}"
                    for r in bundle["daily"]
                ]
                return self._send_csv(f"future_daily_{m_key}_2026_2030.csv", header + "\n".join(lines))
            elif dl_type == "monthly":
                header = "year,month,mean_predicted_temperature,minimum_predicted_temperature,maximum_predicted_temperature\n"
                rows = [r for r in bundle["monthly_summary"] if r["model_name"] == m_name]
                lines = [
                    f"{r['year']},{r['month']},{r['mean_predicted_temperature']:.3f},{r['minimum_predicted_temperature']:.3f},{r['maximum_predicted_temperature']:.3f}"
                    for r in rows
                ]
                return self._send_csv(f"future_monthly_{m_key}_2026_2030.csv", header + "\n".join(lines))
            elif dl_type == "yearly":
                header = "year,number_of_forecast_days,mean_predicted_temperature,minimum_predicted_temperature,maximum_predicted_temperature\n"
                rows = [r for r in bundle["yearly_summary"] if r["model_name"] == m_name]
                lines = [
                    f"{r['year']},{r['number_of_forecast_days']},{r['mean_predicted_temperature']:.3f},{r['minimum_predicted_temperature']:.3f},{r['maximum_predicted_temperature']:.3f}"
                    for r in rows
                ]
                return self._send_csv(f"future_yearly_{m_key}_2026_2030.csv", header + "\n".join(lines))

        return self._send_json({"error": "Endpoint not found"}, status=404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/future/generate":
            length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
            try:
                req = json.loads(raw_body)
            except Exception:
                req = {}
            regen = bool(req.get("force_retrain", False))
            bundle = get_bundle(force_regenerate=regen)
            return self._send_json({
                "status": "ok",
                "metadata": bundle["metadata"],
                "validation_checks": bundle["validation_checks"],
            })
        return self._send_json({"error": "POST endpoint not found"}, status=404)


if __name__ == "__main__":
    import argparse, socket, threading
    ap = argparse.ArgumentParser(description="Delhi Weather Forecasting & Future Forecast Lab Server")
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8080")))
    args = ap.parse_args()
    get_bundle()
    ThreadingHTTPServer.allow_reuse_address = True

    class ThreadingHTTPServerV6(ThreadingHTTPServer):
        address_family = socket.AF_INET6

    servers = []
    for p in (args.port, 8000, 8050):
        for cls, host in ((ThreadingHTTPServer, "127.0.0.1"), (ThreadingHTTPServerV6, "::1")):
            try:
                s = cls((host, p), ForecastAPIHandler)
                threading.Thread(target=s.serve_forever, daemon=True).start()
                servers.append((host, p))
            except OSError:
                pass

    print(f"🚀 Server active on: {', '.join(f'{h}:{p}' for h, p in servers)}", flush=True)
    threading.Event().wait()
