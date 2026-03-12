# Aura — Deployment Guide (Kagent)

## Overview

Aura is deployed using [Kagent](https://kagent.dev) — the Cloud-Native Agentic AI framework for Kubernetes. Each agent in the squad is declared as an `Agent` Custom Resource Definition (CRD), enabling independent scaling and cross-cloud portability.

---

## Prerequisites

| Tool | Version | Install |
| :--- | :--- | :--- |
| `kubectl` | ≥ 1.28 | [docs](https://kubernetes.io/docs/tasks/tools/) |
| `kagent` CLI | latest | `brew install kagent-dev/tap/kagent` |
| Kubernetes cluster | ≥ 1.28 | GKE, kind, k3s, or any CNCF-conformant cluster |
| GCP credentials | - | `gcloud auth application-default login` |

---

## Step 1 — Install Kagent CRDs

```bash
kagent install
```

This installs the `kagent.dev/v1alpha2` CRDs into your cluster.

---

## Step 2 — Create GCP Credentials Secret

```bash
kubectl create secret generic gcp-credentials \
  --from-literal=project=ai-agent-labs-oslo-26-team-6 \
  --from-literal=location=us-central1
```

---

## Step 3 — Build and Push Container

```bash
# Build
docker build -t europe-north1-docker.pkg.dev/ai-agent-labs-oslo-26-team-6/aura/aura:latest .

# Push (requires Artifact Registry configured)
docker push europe-north1-docker.pkg.dev/ai-agent-labs-oslo-26-team-6/aura/aura:latest
```

---

## Step 4 — Deploy Agents

```bash
kubectl apply -f deploy/kagent.yaml
```

Verify all agents are running:

```bash
kubectl get agents -n aura
```

Expected output:

```
NAME         READY   MODEL                  AGE
architect    True    gemini-2.5-flash       30s
scout        True    gemini-2.5-flash       30s
sentinel     True    gemini-2.5-flash       30s
closer       True    gemini-2.5-flash       30s
```

---

## Step 5 — Test the Deployment

```bash
# Port-forward the Architect service
kubectl port-forward svc/aura-architect 8080:8080 -n aura

# Happy path
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{"message": "Buy 5 laptops from the best available vendor"}'

# Blocked path
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{"message": "Buy from ShadowHardware"}'
```

---

## Cloud-Agnostic Model Swap

Aura is designed to run on any cloud. To swap the model backend, update the `ModelConfig` in `kagent.yaml`:

### AWS Bedrock (Claude 3.5 Sonnet)

```yaml
modelConfig:
  provider: AmazonBedrock
  modelID: anthropic.claude-3-5-sonnet-20241022-v2:0
  region: eu-west-1
```

### Azure OpenAI

```yaml
modelConfig:
  provider: AzureOpenAI
  modelID: gpt-4o
  deploymentName: gpt-4o-deployment
  endpoint: https://<your-resource>.openai.azure.com
```

### Local Ollama (On-Premise)

```yaml
modelConfig:
  provider: Ollama
  modelID: llama3.2
  host: http://ollama.internal:11434
```

---

## Resource Limits

| Container | CPU Request | CPU Limit | Memory Request | Memory Limit |
| :--- | :--- | :--- | :--- | :--- |
| App (FastAPI) | 250m | 500m | 256Mi | 512Mi |
| LLM Sidecar | 500m | 2000m | 1Gi | 4Gi |

---

## Local Development (No Kubernetes)

```bash
# Use ADK's built-in dev UI
source .venv/bin/activate
adk web

# Or run FastAPI directly
uvicorn main:app --reload --port 8080
```
