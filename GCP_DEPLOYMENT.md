# Google Cloud Platform (GCP) Deployment Guide

Complete step-by-step guide for deploying the ELK Vision SaaS multi-container application to Google Cloud Platform with production-grade infrastructure.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Initial GCP Setup](#initial-gcp-setup)
4. [Networking Configuration](#networking-configuration)
5. [Secrets Management](#secrets-management)
6. [Database Setup](#database-setup)
7. [Container Deployment (GKE)](#container-deployment-gke)
8. [Load Balancing & Ingress](#load-balancing--ingress)
9. [Auto-Scaling Configuration](#auto-scaling-configuration)
10. [Backup & Disaster Recovery](#backup--disaster-recovery)
11. [Monitoring & Logging](#monitoring--logging)
12. [CI/CD Pipeline](#cicd-pipeline)
13. [Cost Optimization](#cost-optimization)

---

## Architecture Overview

### Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Cloud Load Balancer                      │
│                  (Global HTTPS Load Balancer)                │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
┌────────▼─────────┐           ┌────────▼─────────┐
│   GKE Cluster    │           │  Cloud CDN       │
│   (us-central1)  │           │  (Static Assets) │
└────────┬─────────┘           └──────────────────┘
         │
    ┌────┴─────┬─────────┬─────────┬──────────┐
    │          │         │         │          │
┌───▼───┐  ┌──▼──┐  ┌───▼───┐ ┌───▼───┐  ┌──▼──┐
│Backend│  │Front│  │Celery │ │Nginx  │  │Flower│
│Pods   │  │end  │  │Worker │ │       │  │      │
│(3)    │  │Pods │  │Pods   │ │       │  │      │
└───┬───┘  └─────┘  └───┬───┘ └───────┘  └──────┘
    │                   │
    └─────────┬─────────┘
              │
    ┌─────────┴──────────┬───────────────┬──────────────┐
    │                    │               │              │
┌───▼────────┐  ┌────────▼─────┐  ┌─────▼──────┐  ┌───▼────────┐
│Cloud SQL   │  │Memorystore   │  │GCS Bucket  │  │Elasticsearch│
│(PostgreSQL)│  │(Redis)       │  │(Storage)   │  │(self-hosted)│
│Multi-AZ    │  │Multi-AZ      │  │Multi-Region│  │Statefulset  │
└────────────┘  └──────────────┘  └────────────┘  └─────────────┘
```

### GCP Services Used

- **GKE (Google Kubernetes Engine)**: Container orchestration
- **Cloud SQL**: Managed PostgreSQL database
- **Memorystore**: Managed Redis cache
- **GCS (Cloud Storage)**: Static files, media, backups
- **Secret Manager**: Secrets and credentials
- **Cloud Load Balancing**: Global HTTPS load balancer
- **Cloud CDN**: Content delivery network
- **Cloud Build**: CI/CD pipeline
- **Cloud Monitoring**: Metrics and alerting
- **Cloud Logging**: Centralized logging
- **Cloud NAT**: Outbound internet access
- **VPC**: Private networking

---

## Prerequisites

### Required Tools

Install on your local machine:

```bash
# Google Cloud SDK
# Windows (PowerShell)
(New-Object Net.WebClient).DownloadFile("https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe", "$env:TEMP\GoogleCloudSDKInstaller.exe")
& $env:TEMP\GoogleCloudSDKInstaller.exe

# Or use Chocolatey
choco install gcloudsdk

# Verify installation
gcloud --version

# Install kubectl
gcloud components install kubectl

# Install other tools
choco install docker-desktop
choco install terraform  # Optional but recommended
```

### GCP Account Setup

1. **Create GCP Account**: https://console.cloud.google.com/
2. **Enable Billing**: Set up billing account
3. **Set up billing alerts** to avoid unexpected charges

### Estimated Costs

**Monthly estimate for production deployment:**

| Service | Configuration | Monthly Cost |
|---------|--------------|--------------|
| GKE Cluster | 3 nodes (e2-standard-4) | $300 |
| Cloud SQL | db-n1-standard-2 | $175 |
| Memorystore | Basic 5GB Redis | $50 |
| Cloud Storage | 500GB + egress | $35 |
| Load Balancer | Global HTTPS LB | $20 |
| Cloud NAT | Standard | $45 |
| Elasticsearch (self-hosted) | 3 nodes in GKE | $200 |
| Backups & Snapshots | 1TB | $25 |
| **Total** | | **~$850/month** |

---

## Initial GCP Setup

### Step 1: Create GCP Project

```powershell
# Set project variables
$PROJECT_ID = "elk-vision-prod"
$PROJECT_NAME = "ELK Vision SaaS"
$BILLING_ACCOUNT_ID = "YOUR-BILLING-ACCOUNT-ID"
$REGION = "us-central1"
$ZONE = "us-central1-a"

# Create project
gcloud projects create $PROJECT_ID --name="$PROJECT_NAME"

# Set as active project
gcloud config set project $PROJECT_ID

# Link billing account
gcloud billing projects link $PROJECT_ID --billing-account=$BILLING_ACCOUNT_ID

# Set default region and zone
gcloud config set compute/region $REGION
gcloud config set compute/zone $ZONE
```

### Step 2: Enable Required APIs

```powershell
# Enable all required GCP APIs
gcloud services enable `
  container.googleapis.com `
  compute.googleapis.com `
  sqladmin.googleapis.com `
  redis.googleapis.com `
  storage-api.googleapis.com `
  storage-component.googleapis.com `
  secretmanager.googleapis.com `
  cloudresourcemanager.googleapis.com `
  cloudbuild.googleapis.com `
  containerregistry.googleapis.com `
  logging.googleapis.com `
  monitoring.googleapis.com `
  dns.googleapis.com `
  servicenetworking.googleapis.com `
  vpcaccess.googleapis.com

# Verify APIs are enabled
gcloud services list --enabled
```

### Step 3: Set Up Service Accounts

```powershell
# Create service accounts
$SA_GKE = "gke-elk-vision-sa"
$SA_CLOUDSQL = "cloudsql-elk-vision-sa"
$SA_STORAGE = "storage-elk-vision-sa"

# GKE service account
gcloud iam service-accounts create $SA_GKE `
  --display-name="GKE Service Account"

# Cloud SQL service account
gcloud iam service-accounts create $SA_CLOUDSQL `
  --display-name="Cloud SQL Service Account"

# Storage service account
gcloud iam service-accounts create $SA_STORAGE `
  --display-name="Cloud Storage Service Account"

# Grant necessary permissions
$SA_GKE_EMAIL = "${SA_GKE}@${PROJECT_ID}.iam.gserviceaccount.com"
$SA_CLOUDSQL_EMAIL = "${SA_CLOUDSQL}@${PROJECT_ID}.iam.gserviceaccount.com"
$SA_STORAGE_EMAIL = "${SA_STORAGE}@${PROJECT_ID}.iam.gserviceaccount.com"

# GKE permissions
gcloud projects add-iam-policy-binding $PROJECT_ID `
  --member="serviceAccount:$SA_GKE_EMAIL" `
  --role="roles/logging.logWriter"

gcloud projects add-iam-policy-binding $PROJECT_ID `
  --member="serviceAccount:$SA_GKE_EMAIL" `
  --role="roles/monitoring.metricWriter"

# Cloud SQL permissions
gcloud projects add-iam-policy-binding $PROJECT_ID `
  --member="serviceAccount:$SA_CLOUDSQL_EMAIL" `
  --role="roles/cloudsql.client"

# Storage permissions
gcloud projects add-iam-policy-binding $PROJECT_ID `
  --member="serviceAccount:$SA_STORAGE_EMAIL" `
  --role="roles/storage.objectAdmin"
```

---

## Networking Configuration

### Step 1: Create VPC Network

```powershell
$VPC_NAME = "elk-vision-vpc"
$SUBNET_NAME = "elk-vision-subnet"
$SUBNET_RANGE = "10.0.0.0/24"
$PODS_RANGE = "10.1.0.0/16"
$SERVICES_RANGE = "10.2.0.0/16"

# Create VPC
gcloud compute networks create $VPC_NAME `
  --subnet-mode=custom `
  --bgp-routing-mode=regional

# Create subnet
gcloud compute networks subnets create $SUBNET_NAME `
  --network=$VPC_NAME `
  --region=$REGION `
  --range=$SUBNET_RANGE `
  --secondary-range="pods=$PODS_RANGE" `
  --secondary-range="services=$SERVICES_RANGE" `
  --enable-private-ip-google-access

# Create firewall rules
# Allow internal communication
gcloud compute firewall-rules create $VPC_NAME-allow-internal `
  --network=$VPC_NAME `
  --allow=tcp,udp,icmp `
  --source-ranges=$SUBNET_RANGE,$PODS_RANGE,$SERVICES_RANGE

# Allow SSH from specific IPs (replace with your IP)
gcloud compute firewall-rules create $VPC_NAME-allow-ssh `
  --network=$VPC_NAME `
  --allow=tcp:22 `
  --source-ranges=YOUR_IP_ADDRESS/32

# Allow health checks
gcloud compute firewall-rules create $VPC_NAME-allow-health-checks `
  --network=$VPC_NAME `
  --allow=tcp `
  --source-ranges=35.191.0.0/16,130.211.0.0/22
```

### Step 2: Reserve Static IP

```powershell
# Reserve global static IP for load balancer
gcloud compute addresses create elk-vision-lb-ip `
  --global `
  --ip-version=IPV4

# Get the IP address
$STATIC_IP = gcloud compute addresses describe elk-vision-lb-ip `
  --global `
  --format="get(address)"

Write-Host "Static IP: $STATIC_IP"
Write-Host "Add this to your DNS: yourdomain.com A $STATIC_IP"
```

### Step 3: Set Up Cloud NAT

```powershell
# Create Cloud Router
gcloud compute routers create elk-vision-router `
  --network=$VPC_NAME `
  --region=$REGION

# Create Cloud NAT
gcloud compute routers nats create elk-vision-nat `
  --router=elk-vision-router `
  --region=$REGION `
  --auto-allocate-nat-external-ips `
  --nat-all-subnet-ip-ranges
```

### Step 4: Configure Private Service Access (for Cloud SQL)

```powershell
# Allocate IP range for private services
gcloud compute addresses create google-managed-services-$VPC_NAME `
  --global `
  --purpose=VPC_PEERING `
  --prefix-length=16 `
  --network=$VPC_NAME

# Create private connection
gcloud services vpc-peerings connect `
  --service=servicenetworking.googleapis.com `
  --ranges=google-managed-services-$VPC_NAME `
  --network=$VPC_NAME
```

---

## Secrets Management

### Step 1: Create Secrets in Secret Manager

```powershell
# Generate secrets (use PowerShell to generate random strings)
function New-RandomPassword {
    $chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()"
    -join ((1..32) | ForEach-Object { $chars[(Get-Random -Maximum $chars.Length)] })
}

$DJANGO_SECRET = New-RandomPassword
$POSTGRES_PASSWORD = New-RandomPassword
$REDIS_PASSWORD = New-RandomPassword
$ELASTIC_PASSWORD = New-RandomPassword
$JWT_SECRET = New-RandomPassword
$GRAFANA_PASSWORD = New-RandomPassword

# Create secrets
echo $DJANGO_SECRET | gcloud secrets create django-secret-key --data-file=-
echo $POSTGRES_PASSWORD | gcloud secrets create postgres-password --data-file=-
echo $REDIS_PASSWORD | gcloud secrets create redis-password --data-file=-
echo $ELASTIC_PASSWORD | gcloud secrets create elasticsearch-password --data-file=-
echo $JWT_SECRET | gcloud secrets create jwt-secret-key --data-file=-
echo $GRAFANA_PASSWORD | gcloud secrets create grafana-admin-password --data-file=-

# Grant access to GKE service account
$SA_GKE_EMAIL = "${SA_GKE}@${PROJECT_ID}.iam.gserviceaccount.com"

@("django-secret-key", "postgres-password", "redis-password", 
  "elasticsearch-password", "jwt-secret-key", "grafana-admin-password") | ForEach-Object {
    gcloud secrets add-iam-policy-binding $_ `
      --member="serviceAccount:$SA_GKE_EMAIL" `
      --role="roles/secretmanager.secretAccessor"
}

# Verify secrets
gcloud secrets list
```

### Step 2: Install Secret Store CSI Driver on GKE (later step)

This will be done after GKE cluster creation.

---

## Database Setup

### Step 1: Create Cloud SQL Instance (PostgreSQL)

```powershell
$CLOUDSQL_INSTANCE = "elk-vision-postgres"
$DB_VERSION = "POSTGRES_15"
$DB_TIER = "db-n1-standard-2"  # 2 vCPU, 7.5GB RAM

# Create Cloud SQL instance
gcloud sql instances create $CLOUDSQL_INSTANCE `
  --database-version=$DB_VERSION `
  --tier=$DB_TIER `
  --region=$REGION `
  --network=$VPC_NAME `
  --no-assign-ip `
  --enable-bin-log `
  --backup-start-time=02:00 `
  --maintenance-window-day=SUN `
  --maintenance-window-hour=02 `
  --maintenance-release-channel=production `
  --availability-type=REGIONAL `
  --storage-type=SSD `
  --storage-size=100GB `
  --storage-auto-increase `
  --storage-auto-increase-limit=500GB

# Set root password
gcloud sql users set-password postgres `
  --instance=$CLOUDSQL_INSTANCE `
  --password=$POSTGRES_PASSWORD

# Create application database
gcloud sql databases create elk_vision_prod `
  --instance=$CLOUDSQL_INSTANCE

# Create application user
gcloud sql users create elk_admin `
  --instance=$CLOUDSQL_INSTANCE `
  --password=$POSTGRES_PASSWORD

# Get connection name
$CLOUDSQL_CONNECTION_NAME = gcloud sql instances describe $CLOUDSQL_INSTANCE `
  --format="get(connectionName)"

Write-Host "Cloud SQL Connection Name: $CLOUDSQL_CONNECTION_NAME"
```

### Step 2: Create Memorystore (Redis) Instance

```powershell
$REDIS_INSTANCE = "elk-vision-redis"
$REDIS_TIER = "STANDARD_HA"  # High availability
$REDIS_SIZE = 5  # 5GB

# Create Redis instance
gcloud redis instances create $REDIS_INSTANCE `
  --region=$REGION `
  --network=$VPC_NAME `
  --tier=$REDIS_TIER `
  --size=$REDIS_SIZE `
  --redis-version=redis_7_0 `
  --enable-auth

# Get Redis host and auth string
$REDIS_HOST = gcloud redis instances describe $REDIS_INSTANCE `
  --region=$REGION `
  --format="get(host)"

$REDIS_AUTH = gcloud redis instances get-auth-string $REDIS_INSTANCE `
  --region=$REGION

Write-Host "Redis Host: $REDIS_HOST"
Write-Host "Redis Auth: $REDIS_AUTH"

# Store Redis auth in Secret Manager
echo $REDIS_AUTH | gcloud secrets create redis-auth-string --data-file=-
```

### Step 3: Create Cloud Storage Buckets

```powershell
$BUCKET_NAME = "elk-vision-storage-prod"
$BACKUP_BUCKET = "elk-vision-backups-prod"
$STATIC_BUCKET = "elk-vision-static-prod"

# Create buckets
gcloud storage buckets create gs://$BUCKET_NAME `
  --location=$REGION `
  --uniform-bucket-level-access `
  --public-access-prevention

gcloud storage buckets create gs://$BACKUP_BUCKET `
  --location=$REGION `
  --uniform-bucket-level-access `
  --public-access-prevention

gcloud storage buckets create gs://$STATIC_BUCKET `
  --location=$REGION `
  --uniform-bucket-level-access

# Enable versioning for backups
gcloud storage buckets update gs://$BACKUP_BUCKET `
  --versioning

# Set lifecycle policies for backups (delete after 90 days)
$LIFECYCLE_CONFIG = @"
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 90}
      }
    ]
  }
}
"@

$LIFECYCLE_CONFIG | Out-File -FilePath lifecycle.json
gcloud storage buckets update gs://$BACKUP_BUCKET --lifecycle-file=lifecycle.json
Remove-Item lifecycle.json

# Grant access to service account
gcloud storage buckets add-iam-policy-binding gs://$BUCKET_NAME `
  --member="serviceAccount:$SA_STORAGE_EMAIL" `
  --role="roles/storage.objectAdmin"

gcloud storage buckets add-iam-policy-binding gs://$BACKUP_BUCKET `
  --member="serviceAccount:$SA_STORAGE_EMAIL" `
  --role="roles/storage.objectAdmin"

gcloud storage buckets add-iam-policy-binding gs://$STATIC_BUCKET `
  --member="serviceAccount:$SA_STORAGE_EMAIL" `
  --role="roles/storage.objectAdmin"
```

---

## Container Deployment (GKE)

### Step 1: Create GKE Cluster

```powershell
$CLUSTER_NAME = "elk-vision-cluster"
$CLUSTER_VERSION = "1.28"  # Latest stable
$MACHINE_TYPE = "e2-standard-4"  # 4 vCPU, 16GB RAM
$NUM_NODES = 3
$MIN_NODES = 2
$MAX_NODES = 10

# Create GKE cluster
gcloud container clusters create $CLUSTER_NAME `
  --region=$REGION `
  --cluster-version=$CLUSTER_VERSION `
  --machine-type=$MACHINE_TYPE `
  --num-nodes=$NUM_NODES `
  --network=$VPC_NAME `
  --subnetwork=$SUBNET_NAME `
  --cluster-secondary-range-name=pods `
  --services-secondary-range-name=services `
  --enable-ip-alias `
  --enable-cloud-logging `
  --enable-cloud-monitoring `
  --enable-autoscaling `
  --min-nodes=$MIN_NODES `
  --max-nodes=$MAX_NODES `
  --enable-autorepair `
  --enable-autoupgrade `
  --maintenance-window-start=2025-01-01T02:00:00Z `
  --maintenance-window-duration=4h `
  --maintenance-window-recurrence="FREQ=WEEKLY;BYDAY=SU" `
  --addons=HorizontalPodAutoscaling,HttpLoadBalancing,GcePersistentDiskCsiDriver `
  --workload-pool=$PROJECT_ID.svc.id.goog `
  --enable-shielded-nodes `
  --shielded-secure-boot `
  --shielded-integrity-monitoring `
  --service-account=$SA_GKE_EMAIL

# Get cluster credentials
gcloud container clusters get-credentials $CLUSTER_NAME --region=$REGION

# Verify cluster
kubectl cluster-info
kubectl get nodes
```

### Step 2: Install Workload Identity

```powershell
# Create Kubernetes service account
kubectl create namespace elk-vision
kubectl create serviceaccount elk-vision-ksa -n elk-vision

# Bind Kubernetes SA to GCP SA
gcloud iam service-accounts add-iam-policy-binding $SA_GKE_EMAIL `
  --role roles/iam.workloadIdentityUser `
  --member "serviceAccount:$PROJECT_ID.svc.id.goog[elk-vision/elk-vision-ksa]"

# Annotate Kubernetes service account
kubectl annotate serviceaccount elk-vision-ksa `
  -n elk-vision `
  iam.gke.io/gcp-service-account=$SA_GKE_EMAIL
```

### Step 3: Install Secret Store CSI Driver

```powershell
# Enable Secret Manager API access
kubectl apply -f - <<EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: secret-store-csi-driver
  namespace: kube-system
EOF

# Install Secrets Store CSI Driver
kubectl apply -f https://raw.githubusercontent.com/kubernetes-sigs/secrets-store-csi-driver/main/deploy/rbac-secretproviderclass.yaml
kubectl apply -f https://raw.githubusercontent.com/kubernetes-sigs/secrets-store-csi-driver/main/deploy/csidriver.yaml
kubectl apply -f https://raw.githubusercontent.com/kubernetes-sigs/secrets-store-csi-driver/main/deploy/secrets-store.csi.x-k8s.io_secretproviderclasses.yaml
kubectl apply -f https://raw.githubusercontent.com/kubernetes-sigs/secrets-store-csi-driver/main/deploy/secrets-store.csi.x-k8s.io_secretproviderclasspodstatuses.yaml
kubectl apply -f https://raw.githubusercontent.com/kubernetes-sigs/secrets-store-csi-driver/main/deploy/secrets-store-csi-driver.yaml

# Install GCP provider
kubectl apply -f https://raw.githubusercontent.com/GoogleCloudPlatform/secrets-store-csi-driver-provider-gcp/main/deploy/provider-gcp-plugin.yaml
```

### Step 4: Build and Push Container Images

```powershell
# Configure Docker to use gcloud as credential helper
gcloud auth configure-docker

# Set image names
$BACKEND_IMAGE = "gcr.io/$PROJECT_ID/elk-vision-backend:latest"
$FRONTEND_IMAGE = "gcr.io/$PROJECT_ID/elk-vision-frontend:latest"

# Build and push backend
cd backend
docker build -t $BACKEND_IMAGE -f Dockerfile --target production .
docker push $BACKEND_IMAGE

# Build and push frontend
cd ../frontend
docker build -t $FRONTEND_IMAGE -f Dockerfile --target production .
docker push $FRONTEND_IMAGE

cd ..

# Verify images
gcloud container images list
```

### Step 5: Create Kubernetes Manifests

Create `k8s/secret-provider.yaml`:

```yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: elk-vision-secrets
  namespace: elk-vision
spec:
  provider: gcp
  parameters:
    secrets: |
      - resourceName: "projects/PROJECT_ID/secrets/django-secret-key/versions/latest"
        path: "django-secret-key"
      - resourceName: "projects/PROJECT_ID/secrets/postgres-password/versions/latest"
        path: "postgres-password"
      - resourceName: "projects/PROJECT_ID/secrets/redis-password/versions/latest"
        path: "redis-password"
      - resourceName: "projects/PROJECT_ID/secrets/elasticsearch-password/versions/latest"
        path: "elasticsearch-password"
      - resourceName: "projects/PROJECT_ID/secrets/jwt-secret-key/versions/latest"
        path: "jwt-secret-key"
```

Create `k8s/configmap.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: elk-vision-config
  namespace: elk-vision
data:
  ENVIRONMENT: "production"
  DEBUG: "False"
  DOMAIN: "yourdomain.com"
  ALLOWED_HOSTS: "yourdomain.com,www.yourdomain.com"
  POSTGRES_HOST: "127.0.0.1"  # Cloud SQL proxy
  POSTGRES_PORT: "5432"
  POSTGRES_DB: "elk_vision_prod"
  POSTGRES_USER: "elk_admin"
  REDIS_HOST: "REDIS_HOST_FROM_MEMORYSTORE"
  REDIS_PORT: "6379"
  ELASTICSEARCH_HOST: "elasticsearch:9200"
  USE_S3: "True"
  AWS_STORAGE_BUCKET_NAME: "elk-vision-storage-prod"
```

Create `k8s/backend-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: elk-vision
  labels:
    app: backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      serviceAccountName: elk-vision-ksa
      containers:
      - name: backend
        image: gcr.io/PROJECT_ID/elk-vision-backend:latest
        ports:
        - containerPort: 8000
          name: http
        envFrom:
        - configMapRef:
            name: elk-vision-config
        env:
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: elk-vision-secrets
              key: django-secret-key
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: elk-vision-secrets
              key: postgres-password
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: elk-vision-secrets
              key: redis-password
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /api/health/
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/ready/
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
        volumeMounts:
        - name: secrets
          mountPath: "/secrets"
          readOnly: true
      
      # Cloud SQL Proxy sidecar
      - name: cloud-sql-proxy
        image: gcr.io/cloudsql-docker/gce-proxy:latest
        command:
        - "/cloud_sql_proxy"
        - "-instances=CLOUDSQL_CONNECTION_NAME=tcp:5432"
        - "-credential_file=/secrets/service-account-key.json"
        securityContext:
          runAsNonRoot: true
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "200m"
      
      volumes:
      - name: secrets
        csi:
          driver: secrets-store.csi.k8s.io
          readOnly: true
          volumeAttributes:
            secretProviderClass: "elk-vision-secrets"
---
apiVersion: v1
kind: Service
metadata:
  name: backend
  namespace: elk-vision
spec:
  type: ClusterIP
  ports:
  - port: 8000
    targetPort: 8000
    name: http
  selector:
    app: backend
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
  namespace: elk-vision
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

Create `k8s/frontend-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: elk-vision
  labels:
    app: frontend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      serviceAccountName: elk-vision-ksa
      containers:
      - name: frontend
        image: gcr.io/PROJECT_ID/elk-vision-frontend:latest
        ports:
        - containerPort: 3000
          name: http
        env:
        - name: NODE_ENV
          value: "production"
        - name: NEXT_PUBLIC_API_URL
          value: "https://yourdomain.com/api"
        - name: NEXT_PUBLIC_WS_URL
          value: "wss://yourdomain.com/ws"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /
            port: 3000
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: frontend
  namespace: elk-vision
spec:
  type: ClusterIP
  ports:
  - port: 3000
    targetPort: 3000
    name: http
  selector:
    app: frontend
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: frontend-hpa
  namespace: elk-vision
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: frontend
  minReplicas: 3
  maxReplicas: 15
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

Create `k8s/celery-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: celery-worker
  namespace: elk-vision
  labels:
    app: celery-worker
spec:
  replicas: 2
  selector:
    matchLabels:
      app: celery-worker
  template:
    metadata:
      labels:
        app: celery-worker
    spec:
      serviceAccountName: elk-vision-ksa
      containers:
      - name: celery-worker
        image: gcr.io/PROJECT_ID/elk-vision-backend:latest
        command: ["celery"]
        args:
        - "-A"
        - "config"
        - "worker"
        - "--loglevel=INFO"
        - "--concurrency=4"
        envFrom:
        - configMapRef:
            name: elk-vision-config
        env:
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: elk-vision-secrets
              key: redis-password
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: celery-worker-hpa
  namespace: elk-vision
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: celery-worker
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 75
```

### Step 6: Deploy to GKE

```powershell
# Replace placeholders in manifests
(Get-Content k8s/secret-provider.yaml) -replace 'PROJECT_ID', $PROJECT_ID | Set-Content k8s/secret-provider.yaml
(Get-Content k8s/backend-deployment.yaml) -replace 'PROJECT_ID', $PROJECT_ID | Set-Content k8s/backend-deployment.yaml
(Get-Content k8s/backend-deployment.yaml) -replace 'CLOUDSQL_CONNECTION_NAME', $CLOUDSQL_CONNECTION_NAME | Set-Content k8s/backend-deployment.yaml
(Get-Content k8s/frontend-deployment.yaml) -replace 'PROJECT_ID', $PROJECT_ID | Set-Content k8s/frontend-deployment.yaml
(Get-Content k8s/configmap.yaml) -replace 'REDIS_HOST_FROM_MEMORYSTORE', $REDIS_HOST | Set-Content k8s/configmap.yaml

# Apply manifests
kubectl apply -f k8s/secret-provider.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/celery-deployment.yaml

# Check deployment status
kubectl get pods -n elk-vision
kubectl get deployments -n elk-vision
kubectl get services -n elk-vision
kubectl get hpa -n elk-vision

# View logs
kubectl logs -f deployment/backend -n elk-vision
```

---

## Load Balancing & Ingress

### Step 1: Create Ingress with Google Cloud Load Balancer

Create `k8s/ingress.yaml`:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: elk-vision-ingress
  namespace: elk-vision
  annotations:
    kubernetes.io/ingress.class: "gce"
    kubernetes.io/ingress.global-static-ip-name: "elk-vision-lb-ip"
    networking.gke.io/managed-certificates: "elk-vision-cert"
    kubernetes.io/ingress.allow-http: "true"
spec:
  rules:
  - host: yourdomain.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: backend
            port:
              number: 8000
      - path: /ws
        pathType: Prefix
        backend:
          service:
            name: backend
            port:
              number: 8000
      - path: /admin
        pathType: Prefix
        backend:
          service:
            name: backend
            port:
              number: 8000
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 3000
```

### Step 2: Create Managed SSL Certificate

Create `k8s/managed-cert.yaml`:

```yaml
apiVersion: networking.gke.io/v1
kind: ManagedCertificate
metadata:
  name: elk-vision-cert
  namespace: elk-vision
spec:
  domains:
  - yourdomain.com
  - www.yourdomain.com
```

### Step 3: Deploy Ingress

```powershell
# Apply ingress and certificate
kubectl apply -f k8s/managed-cert.yaml
kubectl apply -f k8s/ingress.yaml

# Wait for ingress to be ready (may take 10-15 minutes)
kubectl describe ingress elk-vision-ingress -n elk-vision

# Check certificate status
kubectl describe managedcertificate elk-vision-cert -n elk-vision

# Get load balancer IP
kubectl get ingress elk-vision-ingress -n elk-vision
```

### Step 4: Configure Cloud CDN

```powershell
# Get backend service name from ingress
$BACKEND_SERVICE = kubectl get ingress elk-vision-ingress -n elk-vision -o json | ConvertFrom-Json | Select-Object -ExpandProperty metadata | Select-Object -ExpandProperty annotations | Select-Object -ExpandProperty "ingress.kubernetes.io/backends"

# Enable Cloud CDN on backend services
gcloud compute backend-services update $BACKEND_SERVICE `
  --enable-cdn `
  --cache-mode=CACHE_ALL_STATIC `
  --default-ttl=3600 `
  --max-ttl=86400 `
  --global
```

---

## Auto-Scaling Configuration

### Step 1: Cluster Autoscaling

Cluster autoscaling is already enabled during GKE creation. Verify:

```powershell
# Check autoscaling config
gcloud container clusters describe $CLUSTER_NAME --region=$REGION | Select-String "autoscaling"

# Update autoscaling settings if needed
gcloud container clusters update $CLUSTER_NAME `
  --region=$REGION `
  --enable-autoscaling `
  --min-nodes=2 `
  --max-nodes=10 `
  --autoscaling-profile=optimize-utilization
```

### Step 2: Horizontal Pod Autoscaling (HPA)

HPA is already configured in deployment manifests. Monitor:

```powershell
# Check HPA status
kubectl get hpa -n elk-vision -w

# Describe HPA
kubectl describe hpa backend-hpa -n elk-vision

# Test scaling
kubectl run load-generator --image=busybox --restart=Never -- /bin/sh -c "while true; do wget -q -O- http://backend.elk-vision:8000/api/health/; done"

# Watch pods scale
kubectl get pods -n elk-vision -w

# Delete load generator
kubectl delete pod load-generator
```

### Step 3: Vertical Pod Autoscaling (VPA)

```powershell
# Install VPA
kubectl apply -f https://raw.githubusercontent.com/kubernetes/autoscaler/master/vertical-pod-autoscaler/deploy/vpa-v1-crd-gen.yaml
kubectl apply -f https://raw.githubusercontent.com/kubernetes/autoscaler/master/vertical-pod-autoscaler/deploy/vpa-rbac.yaml
kubectl apply -f https://raw.githubusercontent.com/kubernetes/autoscaler/master/vertical-pod-autoscaler/deploy/recommender-deployment.yaml
kubectl apply -f https://raw.githubusercontent.com/kubernetes/autoscaler/master/vertical-pod-autoscaler/deploy/updater-deployment.yaml
kubectl apply -f https://raw.githubusercontent.com/kubernetes/autoscaler/master/vertical-pod-autoscaler/deploy/admission-controller-deployment.yaml
```

Create `k8s/vpa.yaml`:

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: backend-vpa
  namespace: elk-vision
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: backend
      minAllowed:
        cpu: 250m
        memory: 512Mi
      maxAllowed:
        cpu: 2000m
        memory: 4Gi
```

Apply VPA:

```powershell
kubectl apply -f k8s/vpa.yaml
```

---

## Backup & Disaster Recovery

### Step 1: Cloud SQL Automated Backups

Cloud SQL backups are already configured. Verify:

```powershell
# Check backup configuration
gcloud sql instances describe $CLOUDSQL_INSTANCE | Select-String "backup"

# List backups
gcloud sql backups list --instance=$CLOUDSQL_INSTANCE

# Create on-demand backup
gcloud sql backups create --instance=$CLOUDSQL_INSTANCE

# Restore from backup (example)
$BACKUP_ID = "backup-id-from-list"
gcloud sql backups restore $BACKUP_ID --backup-instance=$CLOUDSQL_INSTANCE --backup-id=$BACKUP_ID
```

### Step 2: Application Data Backup Script

Create `k8s/backup-cronjob.yaml`:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: backup-databases
  namespace: elk-vision
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: elk-vision-ksa
          containers:
          - name: backup
            image: gcr.io/PROJECT_ID/elk-vision-backend:latest
            command:
            - /bin/bash
            - -c
            - |
              #!/bin/bash
              set -e
              
              DATE=$(date +%Y%m%d_%H%M%S)
              BACKUP_DIR="/tmp/backup_${DATE}"
              mkdir -p $BACKUP_DIR
              
              # Backup PostgreSQL
              PGPASSWORD=$POSTGRES_PASSWORD pg_dump \
                -h $POSTGRES_HOST \
                -U $POSTGRES_USER \
                -d $POSTGRES_DB \
                -F c \
                -f $BACKUP_DIR/postgres_backup.dump
              
              # Backup MongoDB (if using)
              # mongodump commands here
              
              # Compress backup
              tar -czf /tmp/backup_${DATE}.tar.gz $BACKUP_DIR
              
              # Upload to GCS
              gsutil cp /tmp/backup_${DATE}.tar.gz gs://elk-vision-backups-prod/
              
              # Cleanup
              rm -rf $BACKUP_DIR /tmp/backup_${DATE}.tar.gz
              
              echo "Backup completed: backup_${DATE}.tar.gz"
            envFrom:
            - configMapRef:
                name: elk-vision-config
            env:
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: elk-vision-secrets
                  key: postgres-password
          restartPolicy: OnFailure
```

Apply backup CronJob:

```powershell
kubectl apply -f k8s/backup-cronjob.yaml

# Manually trigger backup job
kubectl create job --from=cronjob/backup-databases manual-backup-1 -n elk-vision

# Check job status
kubectl get jobs -n elk-vision
kubectl logs job/manual-backup-1 -n elk-vision
```

### Step 3: Disaster Recovery Plan

Create `k8s/restore-job.yaml`:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: restore-from-backup
  namespace: elk-vision
spec:
  template:
    spec:
      serviceAccountName: elk-vision-ksa
      containers:
      - name: restore
        image: gcr.io/PROJECT_ID/elk-vision-backend:latest
        command:
        - /bin/bash
        - -c
        - |
          #!/bin/bash
          set -e
          
          BACKUP_FILE=${1:-latest}
          
          # Download from GCS
          gsutil cp gs://elk-vision-backups-prod/backup_${BACKUP_FILE}.tar.gz /tmp/
          
          # Extract
          tar -xzf /tmp/backup_${BACKUP_FILE}.tar.gz -C /tmp/
          
          # Restore PostgreSQL
          PGPASSWORD=$POSTGRES_PASSWORD pg_restore \
            -h $POSTGRES_HOST \
            -U $POSTGRES_USER \
            -d $POSTGRES_DB \
            --clean \
            /tmp/backup_*/postgres_backup.dump
          
          echo "Restore completed"
        envFrom:
        - configMapRef:
            name: elk-vision-config
        env:
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: elk-vision-secrets
              key: postgres-password
      restartPolicy: Never
```

### Step 4: GKE Cluster Backup

```powershell
# Enable GKE Backup for Applications
gcloud container backup-restore backup-plans create elk-vision-backup-plan `
  --project=$PROJECT_ID `
  --location=$REGION `
  --cluster=projects/$PROJECT_ID/locations/$REGION/clusters/$CLUSTER_NAME `
  --all-namespaces `
  --include-secrets `
  --include-volume-data `
  --cron-schedule="0 2 * * *" `
  --retention-days=30

# List backups
gcloud container backup-restore backups list `
  --project=$PROJECT_ID `
  --location=$REGION `
  --backup-plan=elk-vision-backup-plan
```

---

## Monitoring & Logging

### Step 1: Cloud Monitoring Integration

Monitoring is already enabled on GKE. Create custom dashboards:

```powershell
# Install monitoring agent (if needed)
kubectl apply -f https://storage.googleapis.com/gke-release/monitoring/latest/gke-monitoring.yaml
```

### Step 2: Create Cloud Monitoring Dashboard

Use GCP Console to create dashboard, or use Terraform:

```hcl
# monitoring-dashboard.tf
resource "google_monitoring_dashboard" "elk_vision" {
  dashboard_json = jsonencode({
    displayName = "ELK Vision SaaS Dashboard"
    gridLayout = {
      widgets = [
        {
          title = "Pod CPU Usage"
          xyChart = {
            dataSets = [{
              timeSeriesQuery = {
                timeSeriesFilter = {
                  filter = "resource.type=\"k8s_pod\" AND resource.labels.namespace_name=\"elk-vision\""
                  aggregation = {
                    alignmentPeriod    = "60s"
                    perSeriesAligner   = "ALIGN_RATE"
                    crossSeriesReducer = "REDUCE_MEAN"
                  }
                }
              }
            }]
          }
        }
      ]
    }
  })
}
```

### Step 3: Set Up Alerts

```powershell
# Create alert policy for high CPU
gcloud alpha monitoring policies create `
  --notification-channels=CHANNEL_ID `
  --display-name="High Pod CPU Usage" `
  --condition-display-name="CPU over 80%" `
  --condition-threshold-value=0.8 `
  --condition-threshold-duration=300s `
  --condition-filter='resource.type="k8s_pod" AND resource.labels.namespace_name="elk-vision"' `
  --condition-comparison=COMPARISON_GT `
  --condition-aggregation-alignment-period=60s `
  --condition-aggregation-per-series-aligner=ALIGN_MEAN
```

### Step 4: Cloud Logging

```powershell
# View logs from GKE
gcloud logging read "resource.type=k8s_pod AND resource.labels.namespace_name=elk-vision" --limit=50 --format=json

# Create log sink to BigQuery
gcloud logging sinks create elk-vision-logs-sink `
  bigquery.googleapis.com/projects/$PROJECT_ID/datasets/elk_vision_logs `
  --log-filter='resource.type="k8s_pod" AND resource.labels.namespace_name="elk-vision"'

# Export logs to Cloud Storage
gcloud logging sinks create elk-vision-logs-archive `
  storage.googleapis.com/elk-vision-logs-archive `
  --log-filter='resource.type="k8s_pod" AND resource.labels.namespace_name="elk-vision"'
```

---

## CI/CD Pipeline

### Step 1: Set Up Cloud Build

Create `cloudbuild.yaml` in repository root:

```yaml
steps:
  # Build backend
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - 'gcr.io/$PROJECT_ID/elk-vision-backend:$SHORT_SHA'
      - '-t'
      - 'gcr.io/$PROJECT_ID/elk-vision-backend:latest'
      - '-f'
      - 'backend/Dockerfile'
      - '--target'
      - 'production'
      - 'backend/'
  
  # Build frontend
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - 'gcr.io/$PROJECT_ID/elk-vision-frontend:$SHORT_SHA'
      - '-t'
      - 'gcr.io/$PROJECT_ID/elk-vision-frontend:latest'
      - '-f'
      - 'frontend/Dockerfile'
      - '--target'
      - 'production'
      - 'frontend/'
  
  # Push images
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/elk-vision-backend:$SHORT_SHA']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/elk-vision-backend:latest']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/elk-vision-frontend:$SHORT_SHA']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/elk-vision-frontend:latest']
  
  # Deploy to GKE
  - name: 'gcr.io/cloud-builders/kubectl'
    args:
      - 'set'
      - 'image'
      - 'deployment/backend'
      - 'backend=gcr.io/$PROJECT_ID/elk-vision-backend:$SHORT_SHA'
      - '-n'
      - 'elk-vision'
    env:
      - 'CLOUDSDK_COMPUTE_REGION=us-central1'
      - 'CLOUDSDK_CONTAINER_CLUSTER=elk-vision-cluster'
  
  - name: 'gcr.io/cloud-builders/kubectl'
    args:
      - 'set'
      - 'image'
      - 'deployment/frontend'
      - 'frontend=gcr.io/$PROJECT_ID/elk-vision-frontend:$SHORT_SHA'
      - '-n'
      - 'elk-vision'
    env:
      - 'CLOUDSDK_COMPUTE_REGION=us-central1'
      - 'CLOUDSDK_CONTAINER_CLUSTER=elk-vision-cluster'
  
  # Wait for rollout
  - name: 'gcr.io/cloud-builders/kubectl'
    args:
      - 'rollout'
      - 'status'
      - 'deployment/backend'
      - '-n'
      - 'elk-vision'
    env:
      - 'CLOUDSDK_COMPUTE_REGION=us-central1'
      - 'CLOUDSDK_CONTAINER_CLUSTER=elk-vision-cluster'

images:
  - 'gcr.io/$PROJECT_ID/elk-vision-backend:$SHORT_SHA'
  - 'gcr.io/$PROJECT_ID/elk-vision-backend:latest'
  - 'gcr.io/$PROJECT_ID/elk-vision-frontend:$SHORT_SHA'
  - 'gcr.io/$PROJECT_ID/elk-vision-frontend:latest'

timeout: 1800s
options:
  machineType: 'N1_HIGHCPU_8'
```

### Step 2: Create Build Trigger

```powershell
# Connect repository (do this via GCP Console first)

# Create trigger
gcloud builds triggers create github `
  --repo-name=elk-vision-saas `
  --repo-owner=yourusername `
  --branch-pattern="^main$" `
  --build-config=cloudbuild.yaml `
  --description="Deploy to production on main branch"

# List triggers
gcloud builds triggers list
```

### Step 3: Manual Build

```powershell
# Trigger build manually
gcloud builds submit --config cloudbuild.yaml .

# View build history
gcloud builds list --limit=10

# View build logs
$BUILD_ID = "latest-build-id"
gcloud builds log $BUILD_ID
```

---

## Cost Optimization

### Step 1: Use Preemptible Nodes for Non-Critical Workloads

```powershell
# Create node pool with preemptible instances
gcloud container node-pools create preemptible-pool `
  --cluster=$CLUSTER_NAME `
  --region=$REGION `
  --machine-type=e2-standard-4 `
  --preemptible `
  --num-nodes=2 `
  --enable-autoscaling `
  --min-nodes=0 `
  --max-nodes=5

# Label preemptible nodes
kubectl label nodes -l cloud.google.com/gke-preemptible=true workload-type=preemptible

# Update Celery deployment to use preemptible nodes
kubectl patch deployment celery-worker -n elk-vision -p '
spec:
  template:
    spec:
      nodeSelector:
        workload-type: preemptible
      tolerations:
      - key: cloud.google.com/gke-preemptible
        operator: Equal
        value: "true"
        effect: NoSchedule
'
```

### Step 2: Committed Use Discounts

```powershell
# Purchase 1-year commitment for compute resources
gcloud compute commitments create elk-vision-commitment `
  --region=$REGION `
  --plan=12-month `
  --resources=vcpu=16,memory=64GB

# View commitments
gcloud compute commitments list
```

### Step 3: Set Up Budgets and Alerts

```powershell
# Create budget (requires billing account ID)
gcloud billing budgets create `
  --billing-account=$BILLING_ACCOUNT_ID `
  --display-name="ELK Vision Monthly Budget" `
  --budget-amount=1000USD `
  --threshold-rule=percent=50 `
  --threshold-rule=percent=90 `
  --threshold-rule=percent=100

# List budgets
gcloud billing budgets list --billing-account=$BILLING_ACCOUNT_ID
```

### Step 4: Cost Optimization Recommendations

```powershell
# Get cost optimization recommendations
gcloud recommender recommendations list `
  --project=$PROJECT_ID `
  --location=$REGION `
  --recommender=google.compute.instance.MachineTypeRecommender

# Get idle resource recommendations
gcloud recommender recommendations list `
  --project=$PROJECT_ID `
  --location=$REGION `
  --recommender=google.compute.instance.IdleResourceRecommender
```

---

## Post-Deployment Verification

### Step 1: Health Checks

```powershell
# Check all pods are running
kubectl get pods -n elk-vision

# Check services
kubectl get svc -n elk-vision

# Check ingress
kubectl get ingress -n elk-vision

# Test backend health
$EXTERNAL_IP = kubectl get ingress elk-vision-ingress -n elk-vision -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
curl "http://$EXTERNAL_IP/api/health/"

# Test frontend
curl "http://$EXTERNAL_IP/"
```

### Step 2: Load Testing

```powershell
# Install locust or use Cloud Load Testing
pip install locust

# Create locustfile.py
@"
from locust import HttpUser, task, between

class ELKVisionUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def health_check(self):
        self.client.get("/api/health/")
    
    @task
    def list_logs(self):
        self.client.get("/api/logs/")
"@ | Out-File -FilePath locustfile.py

# Run load test
locust -f locustfile.py --host=https://yourdomain.com --users=100 --spawn-rate=10
```

### Step 3: Security Scan

```powershell
# Scan container images for vulnerabilities
gcloud container images scan gcr.io/$PROJECT_ID/elk-vision-backend:latest

# View scan results
gcloud container images describe gcr.io/$PROJECT_ID/elk-vision-backend:latest --show-package-vulnerability

# Run security audit
kubectl auth can-i --list --namespace=elk-vision
```

---

## Maintenance & Operations

### Daily Tasks
- Review Cloud Monitoring dashboards
- Check application logs in Cloud Logging
- Verify backup completion
- Review cost reports

### Weekly Tasks
- Update container images with security patches
- Review and apply GCP recommendations
- Check SSL certificate status
- Review scaling metrics

### Monthly Tasks
- Rotate secrets and credentials
- Review and optimize costs
- Conduct security audit
- Test disaster recovery procedures
- Update documentation

---

## Troubleshooting Guide

### Common Issues

#### Pods Not Starting

```powershell
# Check pod status
kubectl describe pod <pod-name> -n elk-vision

# Check logs
kubectl logs <pod-name> -n elk-vision

# Check events
kubectl get events -n elk-vision --sort-by='.lastTimestamp'
```

#### Cloud SQL Connection Issues

```powershell
# Test Cloud SQL proxy
kubectl exec -it <backend-pod> -n elk-vision -c cloud-sql-proxy -- /bin/sh
nc -zv 127.0.0.1 5432

# Check Cloud SQL permissions
gcloud sql instances describe $CLOUDSQL_INSTANCE | Select-String "ipConfiguration"
```

#### Load Balancer Not Working

```powershell
# Check ingress status
kubectl describe ingress elk-vision-ingress -n elk-vision

# Check backend services
gcloud compute backend-services list

# Check firewall rules
gcloud compute firewall-rules list --filter="network:$VPC_NAME"
```

#### High Costs

```powershell
# Analyze costs
gcloud billing accounts describe $BILLING_ACCOUNT_ID

# Check resource usage
gcloud container clusters describe $CLUSTER_NAME --region=$REGION | Select-String "resourceUsageExportConfig"

# Get cost breakdown by SKU
gcloud billing accounts list

# Export billing data to BigQuery for analysis
gcloud beta billing projects link $PROJECT_ID --billing-account=$BILLING_ACCOUNT_ID
```

---

## Additional Resources

- **GCP Documentation**: https://cloud.google.com/docs
- **GKE Best Practices**: https://cloud.google.com/kubernetes-engine/docs/best-practices
- **Cloud SQL Best Practices**: https://cloud.google.com/sql/docs/postgres/best-practices
- **Cost Optimization**: https://cloud.google.com/architecture/framework/cost-optimization
- **Security Best Practices**: https://cloud.google.com/security/best-practices

---

## Support

For deployment issues:
1. Check GCP Console logs
2. Review this documentation
3. Consult GCP Support
4. Contact: devops@yourdomain.com

---

**Last Updated**: December 30, 2025  
**Version**: 1.0.0
**GCP Project**: elk-vision-prod
**Region**: us-central1
