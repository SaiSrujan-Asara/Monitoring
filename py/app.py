
from flask import Flask, Response, jsonify, request
from prometheus_client import Counter, Histogram, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST
import time

app = Flask(__name__)

# RED metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"]
)


@app.before_request
def start_timer():
    request.start_time = time.perf_counter()


@app.after_request
def record_metrics(response):
    # Avoid high-cardinality labels by using the route template.
    if request.path != "/metrics":
        route = request.url_rule.rule if request.url_rule else "unmatched"

        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=route,
            status=str(response.status_code)
        ).inc()

        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=route
        ).observe(time.perf_counter() - request.start_time)

    return response


@app.route("/")
def home():
    return jsonify(message="Hello from Flask!")


@app.route("/health")
def health():
    return jsonify(status="UP")


@app.route("/work")
def work():
    time.sleep(0.2)
    return jsonify(message="Work completed")


@app.route("/error")
def error():
    return jsonify(error="Simulated server error"), 500


@app.route("/metrics")
def metrics():
    return Response(
        generate_latest(),
        mimetype=CONTENT_TYPE_LATEST
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

