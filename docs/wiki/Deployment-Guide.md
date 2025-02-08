# Deployment Guide

This guide provides detailed instructions for deploying the Jenkins Agent system in various environments.

## 🚀 Quick Start

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- Kubernetes 1.20+ (for k8s deployment)
- Helm 3.0+ (for k8s deployment)

### Environment Setup
```bash
# Clone repository
git clone https://github.com/samschim/jenkins-agent.git
cd jenkins-agent

# Copy environment template
cp .env.template .env

# Edit configuration
vim .env
```

## 🐳 Docker Deployment

### Local Development
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production Deployment
```bash
# Build production images
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# Start production stack
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scale web service
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --scale web=3
```

### Environment Variables
```env
# Jenkins Configuration
JENKINS_URL=http://jenkins:8080
JENKINS_USER=admin
JENKINS_ADMIN_PASSWORD=your-secure-password
JENKINS_API_TOKEN=your-api-token

# OpenAI Configuration
OPENAI_API_KEY=your-api-key
OPENAI_API_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4

# GitHub Configuration
GITHUB_TOKEN=your-github-token
GITHUB_USERNAME=your-username

# Database Configuration
MONGODB_URL=mongodb://mongodb:27017
REDIS_URL=redis://redis:6379

# Web Configuration
WEB_PORT=8000
WEB_HOST=0.0.0.0
```

## ☸️ Kubernetes Deployment

### Using Kustomize

1. Development Environment
```bash
# Create namespace
kubectl create namespace jenkins-agent-dev

# Deploy development environment
kubectl apply -k k8s/overlays/dev

# Verify deployment
kubectl -n jenkins-agent-dev get pods
```

2. Production Environment
```bash
# Create namespace
kubectl create namespace jenkins-agent-prod

# Deploy production environment
kubectl apply -k k8s/overlays/prod

# Verify deployment
kubectl -n jenkins-agent-prod get pods
```

### Resource Requirements

#### Development
```yaml
resources:
  jenkins:
    limits:
      cpu: 2
      memory: 4Gi
    requests:
      cpu: 1
      memory: 2Gi
  web:
    limits:
      cpu: 1
      memory: 2Gi
    requests:
      cpu: 500m
      memory: 1Gi
  monitoring:
    limits:
      cpu: 1
      memory: 2Gi
    requests:
      cpu: 500m
      memory: 1Gi
```

#### Production
```yaml
resources:
  jenkins:
    limits:
      cpu: 4
      memory: 8Gi
    requests:
      cpu: 2
      memory: 4Gi
  web:
    limits:
      cpu: 2
      memory: 4Gi
    requests:
      cpu: 1
      memory: 2Gi
  monitoring:
    limits:
      cpu: 2
      memory: 4Gi
    requests:
      cpu: 1
      memory: 2Gi
```

## 📊 Monitoring Setup

### Prometheus Configuration
```yaml
# k8s/base/monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'jenkins'
    static_configs:
      - targets: ['jenkins:8080']
  - job_name: 'web'
    static_configs:
      - targets: ['web:8000']
```

### Grafana Dashboards
1. Import provided dashboards:
   - Jenkins Performance (ID: 9964)
   - System Resources (ID: 1860)
   - Application Metrics (ID: 9852)

2. Configure data sources:
   - Prometheus: `http://prometheus:9090`
   - Loki: `http://loki:3100`

## 🔒 Security Configuration

### TLS Setup
```yaml
# k8s/base/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: jenkins-agent
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - jenkins.example.com
    secretName: jenkins-tls
  rules:
  - host: jenkins.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web
            port:
              number: 80
```

### Network Policies
```yaml
# k8s/base/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: jenkins-agent
spec:
  podSelector:
    matchLabels:
      app: jenkins-agent
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: jenkins-agent
    ports:
    - protocol: TCP
      port: 8000
```

## 📝 Logging Configuration

### Logging Levels
```yaml
# k8s/base/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: logging-config
data:
  log_level: INFO
  log_format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
```

### Log Aggregation
1. Install Loki stack:
```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
helm install loki grafana/loki-stack
```

2. Configure Promtail:
```yaml
# k8s/base/monitoring/promtail.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: promtail-config
data:
  promtail.yaml: |
    clients:
      - url: http://loki:3100/loki/api/v1/push
    scrape_configs:
      - job_name: kubernetes-pods
        kubernetes_sd_configs:
          - role: pod
```

## 🔄 Backup Configuration

### Jenkins Backup
```yaml
# k8s/base/cronjob.yaml
apiVersion: batch/v1beta1
kind: CronJob
metadata:
  name: jenkins-backup
spec:
  schedule: "0 2 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: jenkins-agent-backup:latest
            volumeMounts:
            - name: jenkins-home
              mountPath: /var/jenkins_home
            - name: backup
              mountPath: /backup
```

### Database Backup
```yaml
# k8s/base/cronjob.yaml
apiVersion: batch/v1beta1
kind: CronJob
metadata:
  name: db-backup
spec:
  schedule: "0 3 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: mongodb:6
            command:
            - mongodump
            - --uri=$(MONGODB_URL)
            - --archive=/backup/db-$(date +%Y%m%d).gz
            - --gzip
```

## 🔧 Maintenance

### Health Checks
```bash
# Check service health
kubectl -n jenkins-agent exec deploy/web -- curl -f http://localhost:8000/health

# Check Jenkins status
kubectl -n jenkins-agent exec deploy/jenkins -- curl -f http://localhost:8080/login
```

### Scaling
```bash
# Scale web service
kubectl -n jenkins-agent scale deployment web --replicas=5

# Scale Jenkins agents
kubectl -n jenkins-agent scale statefulset jenkins --replicas=3
```

### Updates
```bash
# Update images
kubectl -n jenkins-agent set image deployment/web web=jenkins-agent-web:new-version

# Rolling restart
kubectl -n jenkins-agent rollout restart deployment web
```

## 🔍 Troubleshooting

### Common Issues

1. Jenkins Connection Issues
```bash
# Check Jenkins logs
kubectl -n jenkins-agent logs deploy/jenkins

# Check network connectivity
kubectl -n jenkins-agent exec deploy/web -- curl -v http://jenkins:8080
```

2. Database Connection Issues
```bash
# Check MongoDB status
kubectl -n jenkins-agent exec deploy/mongodb -- mongosh --eval "db.adminCommand('ping')"

# Check Redis status
kubectl -n jenkins-agent exec deploy/redis -- redis-cli ping
```

3. Resource Issues
```bash
# Check resource usage
kubectl -n jenkins-agent top pods

# Check events
kubectl -n jenkins-agent get events --sort-by='.lastTimestamp'
```

### Debug Mode
```bash
# Enable debug logging
kubectl -n jenkins-agent set env deployment/web LOG_LEVEL=DEBUG

# Start debug pod
kubectl -n jenkins-agent run debug --rm -i --tty --image=jenkins-agent-web:latest -- bash
```

## 📈 Performance Tuning

### JVM Settings
```yaml
# k8s/base/jenkins.yaml
env:
- name: JAVA_OPTS
  value: >-
    -Xmx4g
    -Xms2g
    -XX:+UseG1GC
    -XX:+ExplicitGCInvokesConcurrent
    -XX:+ParallelRefProcEnabled
    -XX:+UseStringDeduplication
    -XX:+UnlockExperimentalVMOptions
    -XX:G1NewSizePercent=20
    -XX:+UnlockDiagnosticVMOptions
    -XX:G1SummarizeRSetStatsPeriod=1
```

### Web Service Tuning
```yaml
# k8s/base/web.yaml
env:
- name: WEB_CONCURRENCY
  value: "4"
- name: MAX_WORKERS
  value: "8"
- name: KEEP_ALIVE
  value: "75"
```

### Cache Configuration
```yaml
# k8s/base/redis.yaml
args:
- --maxmemory 2gb
- --maxmemory-policy allkeys-lru
- --save 900 1
- --save 300 10
- --save 60 10000
```

## 🔐 Secret Management

### Using Sealed Secrets
```bash
# Install sealed-secrets
helm install sealed-secrets sealed-secrets/sealed-secrets

# Create sealed secret
kubeseal -o yaml < secret.yaml > sealed-secret.yaml
```

### Vault Integration
```yaml
# k8s/base/vault.yaml
apiVersion: secrets.hashicorp.com/v1beta1
kind: VaultSecret
metadata:
  name: jenkins-secrets
spec:
  vaultRole: jenkins-agent
  path: secret/jenkins-agent
  type: Opaque
```

## 🌐 DNS and SSL

### DNS Configuration
```yaml
# k8s/base/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: jenkins-agent
  annotations:
    external-dns.alpha.kubernetes.io/hostname: jenkins.example.com
spec:
  rules:
  - host: jenkins.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web
            port:
              number: 80
```

### SSL Certificate
```yaml
# k8s/base/certificate.yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: jenkins-tls
spec:
  secretName: jenkins-tls
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - jenkins.example.com
```

## 📚 Additional Resources

1. [Jenkins Documentation](https://www.jenkins.io/doc/)
2. [Kubernetes Documentation](https://kubernetes.io/docs/)
3. [Prometheus Documentation](https://prometheus.io/docs/)
4. [Grafana Documentation](https://grafana.com/docs/)