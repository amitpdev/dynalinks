# 🚀 DynaLinks Kubernetes Deployment Summary

## 📦 Required Services

Your DynaLinks deployment consists of **2 Kubernetes services** + **1 external service**:

### 1. 🐍 **DynaLinks API Application** 
- **Type**: Deployment (3+ replicas for HA)
- **Image**: `your-registry/dynalinks:latest`
- **Port**: 8000
- **Resources**: 256Mi-1Gi memory, 250m-1000m CPU
- **Features**: Auto-scaling, health checks, graceful shutdown

### 2. 🔴 **Redis Cache**
- **Type**: Deployment (1 replica)
- **Image**: `redis:7-alpine`
- **Port**: 6379
- **Resources**: 128Mi-512Mi memory, 100m-500m CPU
- **Features**: LRU eviction, persistence optional

### 3. 🐘 **PostgreSQL Database** (External)
- **Type**: External VPS server (your existing PostgreSQL)
- **Setup**: Manual database creation required
- **Connection**: Network access from Kubernetes cluster
- **Guide**: See `EXTERNAL-DATABASE-SETUP.md`

## ⚡ Quick Deployment

### Prerequisites Checklist
- [ ] Kubernetes cluster (v1.20+)
- [ ] kubectl configured
- [ ] Docker image built and pushed
- [ ] **External PostgreSQL database setup** (see `EXTERNAL-DATABASE-SETUP.md`)
- [ ] Network access from K8s cluster to PostgreSQL VPS
- [ ] Domains configured (dl.yourdomain.com, api.yourdomain.com)
- [ ] Ingress controller installed (NGINX recommended)

### Quick Deployment Steps
```bash
# 1. Setup external database (IMPORTANT - do this first!)
# Follow EXTERNAL-DATABASE-SETUP.md to create database schema on your VPS

# 2. Build and push image
docker build -f Dockerfile.prod -t your-registry/dynalinks:latest .
docker push your-registry/dynalinks:latest

# 3. Update configuration in k8s-manifests.yaml
# - Update image: your-registry/dynalinks:latest
# - Update DATABASE_HOST: your-postgres-vps-ip-or-domain
# - Update domains: dl.yourdomain.com, api.yourdomain.com
# - Update secrets (base64 encoded)

# 4. Deploy to Kubernetes
kubectl apply -f k8s-manifests.yaml

# 5. Wait for deployment
kubectl get pods -n dynalinks -w
```

## 🔧 Configuration Required

### Update These Values
```yaml
# In k8s-manifests.yaml:

# ConfigMap - dynalinks-config:
BASE_DOMAIN: "https://yourdomain.com"                    # ← YOUR DOMAIN
SHORT_DOMAIN: "https://dl.yourdomain.com"                # ← YOUR SHORT DOMAIN
DATABASE_HOST: "your-postgres-vps-ip-or-domain"         # ← YOUR POSTGRESQL VPS

# Deployment - dynalinks-app:
image: your-registry/dynalinks:latest                    # ← YOUR IMAGE

# Secret - dynalinks-secrets (base64 encoded):
SECRET_KEY: "base64-encoded-secret"                      # ← GENERATE: openssl rand -base64 32 | base64
DATABASE_PASSWORD: "base64-encoded-password"             # ← YOUR DB PASSWORD (base64)

# Ingress - dynalinks-ingress:
- host: dl.yourdomain.com                                # ← YOUR SHORT DOMAIN
- host: api.yourdomain.com                               # ← YOUR API DOMAIN
```

## 📊 Resource Requirements

### Kubernetes Cluster Requirements
#### Minimum Resources
- **Total CPU**: ~1 core (app + redis)
- **Total Memory**: ~1Gi
- **Storage**: Minimal (only Redis temp data)

#### Production Recommended
- **Total CPU**: ~4 cores (with auto-scaling)
- **Total Memory**: ~4Gi
- **Storage**: Minimal for K8s services

### External PostgreSQL Server
- **Recommended**: 2+ CPU cores, 4Gi+ RAM, 100Gi+ SSD storage
- **Network**: Reliable connection to Kubernetes cluster

## 🔍 Verification Commands

```bash
# Check Kubernetes services running (should only see app + redis)
kubectl get pods -n dynalinks

# Test external database connection from K8s
kubectl run postgres-client --rm -it --restart=Never --image=postgres:15-alpine -- \
  psql -h your-postgres-vps-ip -U dynalinks_user -d dynalinks

# Test API health
curl https://api.yourdomain.com/api/v1/health

# Test link creation
curl -X POST "https://api.yourdomain.com/api/v1/links/" \
  -H "Content-Type: application/json" \
  -d '{"fallback_url": "https://google.com"}'

# Test redirect
curl -I https://dl.yourdomain.com/{shortcode}
```

## 🎯 What You Get

### ✅ Production-Ready Features
- **High Availability**: 3+ app replicas across nodes
- **Auto-Scaling**: Scales 3-10 replicas based on CPU/memory
- **External Database**: Uses your existing PostgreSQL VPS
- **Caching**: Redis for high-performance link lookups
- **Security**: Network policies, non-root containers, secrets management
- **Monitoring**: Health checks, liveness/readiness probes
- **SSL**: Automatic HTTPS with ingress controller

### ✅ Operational Features
- **Zero-downtime deployments**: Rolling updates
- **External Database**: Manual schema setup (one-time)
- **Graceful shutdown**: Proper SIGTERM handling
- **Resource limits**: Prevents resource exhaustion
- **Pod disruption budgets**: Maintains availability during cluster operations

## 🆘 Quick Troubleshooting

### If Pods Not Starting
```bash
kubectl describe pod <pod-name> -n dynalinks
kubectl logs <pod-name> -n dynalinks
```

### If External Database Issues
```bash
# Test connection from Kubernetes
kubectl run postgres-client --rm -it --restart=Never --image=postgres:15-alpine -- \
  psql -h your-postgres-vps-ip -U dynalinks_user -d dynalinks

# Check app logs for database errors
kubectl logs deployment/dynalinks-app -n dynalinks | grep -i database
```

### If Ingress Not Working
```bash
kubectl describe ingress dynalinks-ingress -n dynalinks
```

## 📋 Deployment Checklist

### Pre-Deployment
- [ ] **External PostgreSQL database setup** (follow `EXTERNAL-DATABASE-SETUP.md`)
- [ ] Network connectivity from K8s cluster to PostgreSQL VPS
- [ ] Docker image built with production Dockerfile
- [ ] Image pushed to accessible registry
- [ ] Domains pointing to Kubernetes cluster
- [ ] SSL certificates configured (or cert-manager setup)
- [ ] Ingress controller installed and configured

### Configuration
- [ ] Updated image reference in manifests
- [ ] Updated DATABASE_HOST with your PostgreSQL VPS IP/domain
- [ ] Updated domain names in ConfigMap and Ingress
- [ ] Generated and encoded database password in secrets
- [ ] Generated and encoded SECRET_KEY
- [ ] Adjusted resource limits based on cluster capacity

### Deployment
- [ ] Applied all Kubernetes manifests
- [ ] All pods running (3x app, 1x redis - no postgres pod)
- [ ] External database connection working
- [ ] Services accessible internally
- [ ] Ingress routing traffic correctly

### Verification
- [ ] Health endpoint responding: `/api/v1/health`
- [ ] API documentation accessible: `/docs`
- [ ] Can create links via API
- [ ] Short link redirects working
- [ ] Analytics being recorded
- [ ] Logs showing no errors

### Post-Deployment
- [ ] Monitor resource usage
- [ ] Set up external monitoring (Prometheus/Grafana)
- [ ] Configure alerting
- [ ] Set up backup procedures
- [ ] Document operational procedures

---

## 🎉 Success Criteria

Your deployment is successful when:
1. All pods are in `Running` state
2. Health checks are passing
3. You can create links via API
4. Short links redirect correctly
5. No error logs in application

**Total deployment time: ~5-10 minutes** ⚡

For detailed instructions, see `KUBERNETES-DEPLOYMENT.md`
