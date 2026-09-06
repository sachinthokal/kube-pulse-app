import os
import sys
import socket
import platform
import logging
import time
from datetime import datetime, timezone, timedelta
import psutil
from flask import Flask, render_template, jsonify, request
from kubernetes import client, config

# --- IST Timezone Helper ---
IST = timezone(timedelta(hours=5, minutes=30))

class ISTFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(record.created, tz=IST)
        return dt.strftime("%Y-%m-%d %H:%M:%S IST")

# --- Logger Configuration ---
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(ISTFormatter('[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s'))

logger = logging.getLogger("kubepulse")
logger.setLevel(logging.INFO)
logger.addHandler(handler)
logger.propagate = False

# Flask चे डीफॉल्ट विस्कळीत werkzeug लॉग्ज बंद करा
werkzeug_logger = logging.getLogger("werkzeug")
werkzeug_logger.setLevel(logging.ERROR)

app = Flask(__name__)

APP_VERSION = os.getenv("APP_VERSION", "v1.0.0")
APP_START_TIME = time.time()

# --- Request Logging Middleware ---
@app.before_request
def start_timer():
    request._start_time = time.time()

@app.after_request
def log_request(response):
    # Favicon चे फालतू लॉग्ज वगळा
    if request.path == "/favicon.ico":
        return response
    
    latency = round((time.time() - request._start_time) * 1000, 2)
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    
    logger.info(
        f"METHOD={request.method} | PATH={request.path} | STATUS={response.status_code} | "
        f"LATENCY={latency}ms | IP={client_ip}"
    )
    return response

# --- Environment Detection ---
def detect_runtime_environment():
    if os.path.exists("/var/run/secrets/kubernetes.io/serviceaccount"):
        managed_by = os.getenv("DEPLOYED_BY", "").lower()
        if managed_by == "helm" or os.getenv("HELM_RELEASE_NAME"):
            return "Kubernetes (Deployed via Helm)"
        return "Kubernetes (AKS / Raw Manifest)"
    if os.path.exists("/.dockerenv"):
        if os.getenv("COMPOSE_PROJECT_NAME") or os.getenv("DOCKER_COMPOSE"):
            return "Docker Compose"
        return "Standalone Docker Container"
    return f"Local Development ({platform.system()} - {socket.gethostname()})"

def fetch_platform_details():
    env = detect_runtime_environment()
    node_name = platform.node()
    pod_or_host = socket.gethostname()
    cluster_version = f"OS: {platform.system()} {platform.release()}"
    status_tag = "Standalone"

    if "Kubernetes" in env:
        status_tag = "Cluster Ready"
        node_name = os.getenv("NODE_NAME", "k8s-node-pending")
        pod_or_host = os.getenv("HOSTNAME", pod_or_host)
        try:
            config.load_incluster_config()
            v_api = client.VersionApi()
            k8s_ver = v_api.get_code()
            cluster_version = f"v{k8s_ver.major}.{k8s_ver.minor} ({k8s_ver.git_version})"
        except Exception as e:
            logger.warning(f"K8s API Restricted: {str(e)}")
            cluster_version = "K8s API Restricted (Add RBAC)"
    elif "Docker" in env:
        status_tag = "Containerized"
        cluster_version = "Docker Engine (No Cluster)"
    else:
        status_tag = "Baremetal / Local"

    return {
        "env": env,
        "cluster_version": cluster_version,
        "node_name": node_name,
        "pod_name": pod_or_host,
        "status_tag": status_tag
    }

# --- Routes ---
@app.route("/")
def dashboard():
    info = fetch_platform_details()
    sys_stats = {
        "cpu_usage": f"{psutil.cpu_percent()}%",
        "memory_usage": f"{psutil.virtual_memory().percent}%",
        "uptime": f"{int(time.time() - APP_START_TIME)}s"
    }
    history = [
        {
            "version": APP_VERSION,
            "target": info["cluster_version"],
            "runtime": info["env"],
            "timestamp": datetime.now(tz=IST).strftime("%Y-%m-%d %H:%M:%S IST")
        }
    ]
    return render_template("index.html", app_version=APP_VERSION, info=info, stats=sys_stats, history=history)

@app.route("/healthz")
def liveness():
    return jsonify(status="healthy", uptime_sec=int(time.time() - APP_START_TIME)), 200

@app.route("/ready")
def readiness():
    return jsonify(status="ready", env=detect_runtime_environment()), 200

@app.route("/api/burn-cpu")
def burn_cpu():
    duration = int(request.args.get("seconds", 5))
    logger.warning(f"Triggering artificial CPU spike for {duration} seconds!")
    start = time.time()
    while time.time() - start < duration:
        _ = 234234 * 234234
    return jsonify(message=f"Burned CPU for {duration} seconds"), 200

@app.route("/api/crash")
def crash():
    logger.critical("Crash triggered manually via /api/crash endpoint! Terminating process...")
    sys.exit(1)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    logger.info(f"Starting KubePulse server on port {port} (Timezone: IST)...")
    app.run(host="0.0.0.0", port=port)