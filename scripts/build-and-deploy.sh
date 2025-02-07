#!/bin/bash

# Exit on error
set -e

# Default values
ENVIRONMENT="dev"
REGISTRY="localhost:5000"
VERSION=$(git describe --tags --always)

# Parse arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -e|--environment)
            ENVIRONMENT="$2"
            shift
            shift
            ;;
        -r|--registry)
            REGISTRY="$2"
            shift
            shift
            ;;
        -v|--version)
            VERSION="$2"
            shift
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|prod)$ ]]; then
    echo "Invalid environment. Must be 'dev' or 'prod'"
    exit 1
fi

# Build images
echo "Building Docker images..."
docker build -t $REGISTRY/jenkins-agent-webhook:$VERSION -f docker/webhook/Dockerfile .
docker build -t $REGISTRY/jenkins-agent-notifier:$VERSION -f docker/notifier/Dockerfile .
docker build -t $REGISTRY/jenkins-agent-agent:$VERSION -f docker/agent/Dockerfile .
docker build -t $REGISTRY/jenkins-agent-monitor:$VERSION -f docker/monitor/Dockerfile .

# Push images
echo "Pushing Docker images..."
docker push $REGISTRY/jenkins-agent-webhook:$VERSION
docker push $REGISTRY/jenkins-agent-notifier:$VERSION
docker push $REGISTRY/jenkins-agent-agent:$VERSION
docker push $REGISTRY/jenkins-agent-monitor:$VERSION

# Update kustomization
echo "Updating kustomization..."
cd k8s/overlays/$ENVIRONMENT
kustomize edit set image \
    jenkins-agent-webhook=$REGISTRY/jenkins-agent-webhook:$VERSION \
    jenkins-agent-notifier=$REGISTRY/jenkins-agent-notifier:$VERSION \
    jenkins-agent-agent=$REGISTRY/jenkins-agent-agent:$VERSION \
    jenkins-agent-monitor=$REGISTRY/jenkins-agent-monitor:$VERSION

# Deploy
echo "Deploying to $ENVIRONMENT..."
kustomize build . | kubectl apply -f -

# Wait for rollout
echo "Waiting for rollout..."
kubectl -n jenkins-agent-$ENVIRONMENT rollout status deployment/webhook
kubectl -n jenkins-agent-$ENVIRONMENT rollout status deployment/notifier
kubectl -n jenkins-agent-$ENVIRONMENT rollout status deployment/build-manager
kubectl -n jenkins-agent-$ENVIRONMENT rollout status deployment/log-analyzer
kubectl -n jenkins-agent-$ENVIRONMENT rollout status deployment/pipeline-manager
kubectl -n jenkins-agent-$ENVIRONMENT rollout status deployment/plugin-manager
kubectl -n jenkins-agent-$ENVIRONMENT rollout status deployment/monitor

echo "Deployment complete!"