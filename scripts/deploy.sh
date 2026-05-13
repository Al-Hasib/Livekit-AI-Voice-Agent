#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Deploying Voice Agent..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV="${1:-production}"

echo "Environment: $ENV"

# ── Build and push images ──────────────────────────────────────
build_and_push() {
    local name=$1
    local dockerfile=$2
    local context=$3
    local tag="${name}:latest"

    echo "📦 Building $name..."
    docker build -f "$dockerfile" -t "$tag" "$context"

    # Push to registry if configured
    if [ -n "${DOCKER_REGISTRY:-}" ]; then
        local remote_tag="${DOCKER_REGISTRY}/${name}:latest"
        docker tag "$tag" "$remote_tag"
        docker push "$remote_tag"
        echo "✅ Pushed $remote_tag"
    else
        echo "✅ Built $tag (local only)"
    fi
}

build_and_push "voice-agent/backend" "$PROJECT_ROOT/backend/Dockerfile" "$PROJECT_ROOT/backend"
build_and_push "voice-agent/agent" "$PROJECT_ROOT/backend/Dockerfile" "$PROJECT_ROOT/backend"
build_and_push "voice-agent/frontend" "$PROJECT_ROOT/frontend/Dockerfile" "$PROJECT_ROOT/frontend"

# ── Deploy to Kubernetes ───────────────────────────────────────
if command -v kubectl &>/dev/null; then
    echo ""
    echo "☸️  Deploying to Kubernetes..."

    kubectl apply -f "$PROJECT_ROOT/infra/k8s/namespace.yaml"

    # Create secrets if they don't exist
    if ! kubectl get secret voice-agent-secrets -n voice-agent &>/dev/null; then
        echo "⚠️  Create secrets first: kubectl apply -f infra/k8s/secrets.yaml"
        exit 1
    fi

    kubectl apply -f "$PROJECT_ROOT/infra/k8s/backend/configmap.yaml"
    kubectl apply -f "$PROJECT_ROOT/infra/k8s/secrets.yaml"
    kubectl apply -f "$PROJECT_ROOT/infra/k8s/redis/"
    kubectl apply -f "$PROJECT_ROOT/infra/k8s/qdrant/"
    kubectl apply -f "$PROJECT_ROOT/infra/k8s/backend/"
    kubectl apply -f "$PROJECT_ROOT/infra/k8s/frontend/"
    kubectl apply -f "$PROJECT_ROOT/infra/k8s/ingress.yaml"

    echo ""
    echo "⏳ Waiting for rollouts..."
    kubectl rollout status deployment/backend -n voice-agent --timeout=120s
    kubectl rollout status deployment/agent-worker -n voice-agent --timeout=120s
    kubectl rollout status deployment/frontend -n voice-agent --timeout=120s

    echo ""
    echo "🎉 Deployment complete!"
    echo ""
    kubectl get pods -n voice-agent
else
    echo "⚠️  kubectl not found, skipping K8s deployment"
    echo "   Use docker-compose for local deployment:"
    echo "   cd infra/docker && docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d"
fi