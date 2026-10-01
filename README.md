# Centralized Observability Stack (k3s on AWS EC2)

Prometheus + Grafana + Loki + Alertmanager deployed with Helm on a single-node k3s cluster (AWS EC2 free tier).
App metrics and logs are centralized, with custom SLO dashboards and burn-rate alerts routed to AWS SNS (email).

## Architecture

    demo-app --/metrics--> Prometheus --> Alertmanager --> AWS SNS --> Email
       |                       |
       +--stdout--> Alloy --> Loki
                               |
                  Grafana <----+---- (SLO dashboards + logs)

## Components
- kube-prometheus-stack (Helm): Prometheus, Alertmanager, Grafana, node-exporter, kube-state-metrics
- Loki (SingleBinary, filesystem storage) + Grafana Alloy for pod log collection
- demo-app (Flask): http_requests_total, latency histogram, JSON logs
- AWS SNS + EC2 IAM role: alert delivery without static credentials

## SLOs
- Availability 99.5% (error budget 0.5%)
- Latency p95 < 300ms
- Multi-window burn-rate alerts: 14.4x (critical), 6x (warning), plus p95 latency alert

## Repo layout
- helm-values/: kube-prometheus-stack.yaml, loki.yaml, alloy.yaml
- apps/demo-app/: app.py, Dockerfile, k8s.yaml (with ServiceMonitor)
- slo/: slo-rules.yaml
- dashboards/: build_slo.py, slo.json

## Setup
1. EC2 (Ubuntu, 4GB RAM, 30GB+ disk) with IAM role allowing sns:Publish, IMDS hop limit 2.
2. Install k3s (--disable traefik) and Helm.
3. Replace CHANGE_ME (Grafana password) and ACCOUNT_ID (SNS topic ARN) in helm-values/kube-prometheus-stack.yaml.
4. Deploy with helm install for kps, loki, alloy; build and import the demo-app image; apply k8s.yaml and slo/slo-rules.yaml.
5. Run: GRAFANA_AUTH='admin:<password>' python3 dashboards/build_slo.py

## Failure demo
- kubectl -n demo set env deploy/demo-app ERROR_RATE=0.3 (inject 30% errors)
- About 15 min later ErrorBudgetBurnFast fires and an email [CRITICAL][FIRING] arrives
- kubectl -n demo set env deploy/demo-app ERROR_RATE=0.02 to recover, then [RESOLVED]

## Screenshots
See docs/ (dashboard during failure, healthy dashboard, firing alert, email).

## Notes
- Runs on k3s to stay within free tier. On EKS, only storage (S3) and IRSA would change.
- No secrets are committed. Alertmanager uses the EC2 instance role for SNS.
