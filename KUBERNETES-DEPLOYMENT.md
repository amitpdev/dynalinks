# 🚀 Kubernetes Deployment Guide for DynaLinks

This guide provides step-by-step instructions for deploying DynaLinks on your existing Kubernetes cluster.

## 📋 Prerequisites

- Kubernetes cluster (v1.20+)
- kubectl configured for your cluster
- Docker registry access (Docker Hub, GCR, ECR, etc.)
- Ingress controller (NGINX recommended)
- cert-manager (optional, for SSL certificates)

## 🏗️ Services Overview

DynaLinks requires 3 main services:

1. **🐘 PostgreSQL Database** - StatefulSet with persistent storage
2. **🔴 Redis Cache** - Deployment for high-performance caching
3. **🐍 DynaLinks API** - FastAPI application with auto-scaling

## 🔧 Pre-Deployment Setup

### 1. Build and Push Docker Image

```bash
# Build the Docker image
docker build -t your-registry/dynalinks:latest .

# Push to your registry
docker push your-registry/dynalinks:latest
```

### 2. Update Configuration

Edit the `k8s-manifests.yaml` file and update these values:

```yaml
# In dynalinks-config ConfigMap:
BASE_DOMAIN: "https://yourdomain.com"      # Your main domain
SHORT_DOMAIN: "https://dl.yourdomain.com"  # Your short link domain

# In dynalinks-secrets Secret (base64 encoded):
SECRET_KEY: "base64-encoded-secret-key"     # Generate with: openssl rand -base64 32 | base64
DATABASE_PASSWORD: "base64-encoded-password"

# In dynalinks-app Deployment:
image: your-registry/dynalinks:latest       # Your actual image

# In dynalinks-ingress Ingress:
- host: dl.yourdomain.com                   # Your short link domain
- host: api.yourdomain.com                  # Your API domain
```

### 3. Generate Secrets

```bash
# Generate a strong secret key
SECRET_KEY=$(openssl rand -base64 32)
echo -n "$SECRET_KEY" | base64

# Generate database password
DB_PASSWORD=$(openssl rand -base64 24)
echo -n "$DB_PASSWORD" | base64
```

## 🚀 Deployment Steps

### Step 1: Deploy All Resources

```bash
# Apply all Kubernetes manifests
kubectl apply -f k8s-manifests.yaml

# Verify namespace creation
kubectl get namespace dynalinks
```

### Step 2: Monitor Deployment Progress

```bash
# Watch all pods come online
kubectl get pods -n dynalinks -w

# Check deployment status
kubectl get deployments -n dynalinks
kubectl get statefulsets -n dynalinks
kubectl get services -n dynalinks
```

### Step 3: Verify Database Initialization

```bash
# Check database migration job
kubectl get jobs -n dynalinks
kubectl logs job/db-migration -n dynalinks

# Verify database connection
kubectl exec -it postgres-0 -n dynalinks -- psql -U dynalinks_user -d dynalinks -c "\dt"
```

### Step 4: Test Application Health

```bash
# Check application logs
kubectl logs -f deployment/dynalinks-app -n dynalinks

# Port forward to test locally (optional)
kubectl port-forward service/dynalinks-service 8080:80 -n dynalinks

# Test health endpoint
curl http://localhost:8080/api/v1/health
```

### Step 5: Configure DNS and SSL

```bash
# Check ingress status
kubectl get ingress -n dynalinks
kubectl describe ingress dynalinks-ingress -n dynalinks

# If using cert-manager, check certificate
kubectl get certificates -n dynalinks
```

## 🔍 Verification Checklist

### ✅ Services Running
```bash
# All pods should be Running
kubectl get pods -n dynalinks

# Expected output:
# NAME                             READY   STATUS    RESTARTS   AGE
# dynalinks-app-xxx-xxx            1/1     Running   0          5m
# dynalinks-app-xxx-yyy            1/1     Running   0          5m
# dynalinks-app-xxx-zzz            1/1     Running   0          5m
# postgres-0                       1/1     Running   0          10m
# redis-xxx-xxx                    1/1     Running   0          10m
```

### ✅ Database Schema Loaded
```bash
# Connect to database and verify tables
kubectl exec -it postgres-0 -n dynalinks -- psql -U dynalinks_user -d dynalinks
\dt  -- Should show dynamic_links and link_analytics tables
\q
```

### ✅ API Endpoints Working
```bash
# Test health endpoint
curl https://api.yourdomain.com/api/v1/health

# Test API documentation
curl https://api.yourdomain.com/docs

# Create a test link
curl -X POST "https://api.yourdomain.com/api/v1/links/" \
  -H "Content-Type: application/json" \
  -d '{"fallback_url": "https://google.com"}'
```

### ✅ Redirects Working
```bash
# Test redirect (replace 'shortcode' with actual code from above)
curl -I https://dl.yourdomain.com/shortcode
```

## 📊 Monitoring and Scaling

### View Resource Usage
```bash
# Check resource consumption
kubectl top pods -n dynalinks
kubectl top nodes

# View HPA status
kubectl get hpa -n dynalinks
```

### Scale Manually (if needed)
```bash
# Scale application pods
kubectl scale deployment dynalinks-app --replicas=5 -n dynalinks

# Check scaling status
kubectl get deployment dynalinks-app -n dynalinks
```

### View Logs
```bash
# Application logs
kubectl logs -f deployment/dynalinks-app -n dynalinks

# Database logs
kubectl logs -f postgres-0 -n dynalinks

# Redis logs
kubectl logs -f deployment/redis -n dynalinks
```

## 🔧 Configuration Updates

### Update Application Configuration
```bash
# Edit ConfigMap
kubectl edit configmap dynalinks-config -n dynalinks

# Restart application to pick up changes
kubectl rollout restart deployment/dynalinks-app -n dynalinks
```

### Update Application Image
```bash
# Update deployment with new image
kubectl set image deployment/dynalinks-app dynalinks-app=your-registry/dynalinks:v1.1.0 -n dynalinks

# Check rollout status
kubectl rollout status deployment/dynalinks-app -n dynalinks
```

## 🔒 Security Considerations

### Network Policies
The deployment includes NetworkPolicy for pod-to-pod communication security. Verify it's working:
```bash
kubectl get networkpolicy -n dynalinks
kubectl describe networkpolicy dynalinks-network-policy -n dynalinks
```

### RBAC (Optional)
Create a service account with minimal permissions:
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: dynalinks-sa
  namespace: dynalinks
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: dynalinks-role
  namespace: dynalinks
rules: []  # No additional permissions needed
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: dynalinks-rolebinding
  namespace: dynalinks
subjects:
- kind: ServiceAccount
  name: dynalinks-sa
  namespace: dynalinks
roleRef:
  kind: Role
  name: dynalinks-role
  apiGroup: rbac.authorization.k8s.io
```

## 🆘 Troubleshooting

### Common Issues

#### Pods Not Starting
```bash
# Check pod status and events
kubectl describe pod <pod-name> -n dynalinks
kubectl get events -n dynalinks --sort-by='.lastTimestamp'
```

#### Database Connection Issues
```bash
# Check database connectivity
kubectl exec -it deployment/dynalinks-app -n dynalinks -- \
  sh -c 'ping postgres-service.dynalinks.svc.cluster.local'

# Verify database credentials
kubectl get secret dynalinks-secrets -n dynalinks -o yaml
```

#### Ingress Not Working
```bash
# Check ingress controller
kubectl get pods -n ingress-nginx  # Adjust namespace as needed

# Verify ingress configuration
kubectl describe ingress dynalinks-ingress -n dynalinks
```

#### Application Errors
```bash
# Check application logs for errors
kubectl logs deployment/dynalinks-app -n dynalinks --tail=100

# Check application configuration
kubectl exec -it deployment/dynalinks-app -n dynalinks -- env | grep -E "(DATABASE|REDIS|SECRET)"
```

### Performance Tuning

#### Database Optimization
```bash
# Connect to database and check performance
kubectl exec -it postgres-0 -n dynalinks -- psql -U dynalinks_user -d dynalinks

# Check slow queries (PostgreSQL)
SELECT query, mean_time, calls FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;
```

#### Redis Monitoring
```bash
# Connect to Redis and check stats
kubectl exec -it deployment/redis -n dynalinks -- redis-cli INFO memory
kubectl exec -it deployment/redis -n dynalinks -- redis-cli INFO stats
```

## 🔄 Backup and Recovery

### Database Backup
```bash
# Create database backup
kubectl exec postgres-0 -n dynalinks -- pg_dump -U dynalinks_user dynalinks > backup.sql

# Restore from backup
kubectl exec -i postgres-0 -n dynalinks -- psql -U dynalinks_user dynalinks < backup.sql
```

### Persistent Volume Backup
```bash
# List persistent volumes
kubectl get pv

# Create volume snapshot (if supported by your storage class)
kubectl create -f volume-snapshot.yaml
```

## 📈 Production Recommendations

### Resource Limits
- **Application**: 3-10 replicas, 256Mi-1Gi memory, 250m-1000m CPU
- **PostgreSQL**: 1 replica, 1-4Gi memory, 500m-2000m CPU, 20-100Gi storage
- **Redis**: 1 replica, 128Mi-512Mi memory, 100m-500m CPU

### High Availability
- Use multiple availability zones
- Consider PostgreSQL replica for read queries
- Implement proper backup strategy
- Monitor with Prometheus/Grafana

### Security
- Enable Pod Security Standards
- Use network policies
- Regular security updates
- Rotate secrets periodically

---

## 🎉 Success!

Your DynaLinks service should now be running on Kubernetes with:

- ✅ High availability (3+ app replicas)
- ✅ Auto-scaling (HPA configured)
- ✅ Persistent database storage
- ✅ Redis caching for performance
- ✅ SSL termination at ingress
- ✅ Network security policies
- ✅ Health checks and monitoring

**Test your deployment:**
1. Visit https://api.yourdomain.com/docs for API documentation
2. Create a test link via the API
3. Test the redirect at https://dl.yourdomain.com/shortcode

For support, check the logs and troubleshooting section above.
