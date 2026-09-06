# KubePulse

KubePulse is a lightweight diagnostic and monitoring dashboard designed for containerized environments and Kubernetes clusters. It tracks runtime status, cluster/engine information, resource utilization, and health endpoints in real time.

---

## ⚡ Features

- **Runtime Identification:** Automatically detects and displays underlying runtime metadata (e.g., Azure Kubernetes Service, raw Kubernetes, Docker).
- **Cluster & Host Metrics:** Reports the host node name, pod name, CPU utilization, memory footprint, and uptime.
- **Engine Version Tracking:** Queries and renders active Kubernetes API and engine versions dynamically.
- **Live Health Probes:** Exposes built-in endpoints for container orchestrator readiness and liveness checks.
- **Chaos & Simulation Triggers:** Built-in actions to simulate CPU spikes or application crashes for disruption and autoscaling testing.

---

## 🔌 Diagnostic Endpoints

| Endpoint | Method | Purpose |
| :--- | :--- | :--- |
| `/` | `GET` | Main web UI dashboard |
| `/healthz` | `GET` | Liveness probe endpoint (checks service responsiveness) |
| `/ready` | `GET` | Readiness probe endpoint (verifies traffic-serving status) |
| `/burn` | `POST / GET` | Triggers a transient CPU load (5s) for metric testing |
| `/crash` | `POST / GET` | Triggers an application crash for restart behavior testing |

---

## ⚙️ Environment Configuration

| Variable | Description | Default |
| :--- | :--- | :--- |
| `PORT` | Listening port for the HTTP server | `8080` |
| `APP_VERSION` | Application release/build tag | `v1.0.0` |
| `NODE_NAME` | Name of the host node (injected via Downward API) | `unknown` |

---

## 🚀 Quick Run (Local Docker)

```bash
docker run -d -p 8080:8080 --name kubepulse sachinthokal/kubepulse-app:v1