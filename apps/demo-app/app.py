import time, random, json, logging, sys, os
from flask import Flask, request, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)
REQS = Counter("http_requests_total", "Total requests", ["method", "path", "code"])
LAT = Histogram("http_request_duration_seconds", "Latency", ["path"],
                buckets=(.05, .1, .2, .3, .5, 1, 2))
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(message)s")
log = logging.getLogger("demo")

@app.before_request
def start(): request._t = time.time()

@app.after_request
def record(resp):
    if request.path not in ("/metrics", "/healthz"):
        d = time.time() - request._t
        REQS.labels(request.method, request.path, str(resp.status_code)).inc()
        LAT.labels(request.path).observe(d)
        log.info(json.dumps({"level": "error" if resp.status_code >= 500 else "info",
                             "method": request.method, "path": request.path,
                             "status": resp.status_code, "duration_ms": round(d*1000, 1)}))
    return resp

@app.route("/")
def index(): return {"status": "ok"}

@app.route("/healthz")
def health(): return "ok"

@app.route("/api/orders")
def orders():
    time.sleep(random.uniform(0.02, 0.4))
    if random.random() < float(os.getenv("ERROR_RATE", "0.02")):
        return {"error": "db timeout"}, 500
    return {"orders": [1, 2, 3]}

@app.route("/metrics")
def metrics(): return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)
