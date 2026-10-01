import json, base64, os, urllib.request

PROM = {"type": "prometheus", "uid": "prometheus"}
LOKI = {"type": "loki", "uid": "P8E80F9AEF21F6940"}
ERR = 'sum(increase(http_requests_total{job="demo-app",code=~"5.."}[$__range]))'
TOT = 'sum(increase(http_requests_total{job="demo-app"}[$__range]))'

def stat(id, title, expr, x, unit, steps):
    return {"id": id, "type": "stat", "title": title, "datasource": PROM,
            "gridPos": {"h": 6, "w": 8, "x": x, "y": 0},
            "targets": [{"refId": "A", "expr": expr, "datasource": PROM}],
            "fieldConfig": {"defaults": {"unit": unit, "decimals": 2,
                "thresholds": {"mode": "absolute", "steps": steps}}, "overrides": []},
            "options": {"colorMode": "background", "reduceOptions": {"calcs": ["lastNotNull"]}}}

def ts(id, title, targets, x, y, unit="short"):
    return {"id": id, "type": "timeseries", "title": title, "datasource": PROM,
            "gridPos": {"h": 8, "w": 12, "x": x, "y": y},
            "targets": [dict(t, refId=chr(65+i), datasource=PROM) for i, t in enumerate(targets)],
            "fieldConfig": {"defaults": {"unit": unit}, "overrides": []}}

panels = [
  stat(1, "SLO compliance (target 99.5%)", f"(1 - {ERR} / {TOT}) * 100", 0, "percent",
       [{"color": "red", "value": None}, {"color": "orange", "value": 99}, {"color": "green", "value": 99.5}]),
  stat(2, "Error budget remaining", f"(1 - ({ERR} / {TOT}) / 0.005) * 100", 8, "percent",
       [{"color": "red", "value": None}, {"color": "orange", "value": 20}, {"color": "green", "value": 50}]),
  stat(3, "Current burn rate (5m)", "slo:http_error_ratio:rate5m / 0.005", 16, "none",
       [{"color": "green", "value": None}, {"color": "orange", "value": 6}, {"color": "red", "value": 14.4}]),
  ts(4, "Burn rate (alert at 14.4x fast / 6x slow)", [
       {"expr": "slo:http_error_ratio:rate5m / 0.005", "legendFormat": "5m"},
       {"expr": "slo:http_error_ratio:rate1h / 0.005", "legendFormat": "1h"},
       {"expr": "vector(14.4)", "legendFormat": "fast threshold"},
       {"expr": "vector(6)", "legendFormat": "slow threshold"}], 0, 6),
  ts(5, "Latency percentiles (SLO p95 < 300ms)", [
       {"expr": f'histogram_quantile({q}, sum by (le) (rate(http_request_duration_seconds_bucket{{job="demo-app"}}[5m])))',
        "legendFormat": f"p{int(q*100)}"} for q in (0.5, 0.95, 0.99)], 12, 6, "s"),
  ts(6, "Request rate by status code", [
       {"expr": 'sum by (code) (rate(http_requests_total{job="demo-app"}[1m]))', "legendFormat": "{{code}}"}], 0, 14, "reqps"),
  {"id": 7, "type": "logs", "title": "Error logs (Loki)", "datasource": LOKI,
   "gridPos": {"h": 8, "w": 12, "x": 12, "y": 14},
   "targets": [{"refId": "A", "datasource": LOKI,
                "expr": '{namespace="demo", app="demo-app"} | json | level="error"'}],
   "options": {"showTime": True, "wrapLogMessage": True, "sortOrder": "Descending"}},
]

dash = {"uid": "demo-app-slo", "title": "Demo App SLO", "tags": ["slo"],
        "timezone": "browser", "refresh": "30s", "schemaVersion": 39,
        "time": {"from": "now-3h", "to": "now"}, "panels": panels}

json.dump(dash, open("dashboards/slo.json", "w"), indent=2)

req = urllib.request.Request("http://localhost:3000/api/dashboards/db",
    data=json.dumps({"dashboard": dash, "overwrite": True}).encode(),
    headers={"Content-Type": "application/json",
             "Authorization": "Basic " + base64.b64encode(os.environ["GRAFANA_AUTH"].encode()).decode()})
print(urllib.request.urlopen(req).read().decode())
