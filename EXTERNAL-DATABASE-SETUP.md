# 🐘 External PostgreSQL Database Setup for DynaLinks

This guide shows how to set up the database schema on your existing PostgreSQL VPS server for the DynaLinks application.

## 📋 Prerequisites

- Existing PostgreSQL server (version 12+)
- Superuser or database creation privileges
- Network access from your Kubernetes cluster to the PostgreSQL server
- `psql` client installed (for setup)

## 🔧 Database Setup Steps

### Step 1: Create Database and User

Connect to your PostgreSQL server as superuser and run:

```sql
-- Create database
CREATE DATABASE dynalinks;

-- Create user with strong password
CREATE USER dynalinks_user WITH PASSWORD 'your-strong-password-here';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE dynalinks TO dynalinks_user;

-- Connect to the new database
\c dynalinks

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO dynalinks_user;
GRANT CREATE ON SCHEMA public TO dynalinks_user;

-- Grant default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO dynalinks_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO dynalinks_user;
```

### Step 2: Create Database Schema

Connect to the `dynalinks` database and create the required tables:

```sql
-- Switch to dynalinks database
\c dynalinks dynalinks_user

-- Create dynamic_links table
CREATE TABLE dynamic_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    short_code VARCHAR(10) UNIQUE NOT NULL,
    ios_url TEXT,
    android_url TEXT,
    fallback_url TEXT NOT NULL,
    desktop_url TEXT,
    title VARCHAR(255),
    description TEXT,
    image_url TEXT,
    social_title VARCHAR(255),
    social_description TEXT,
    social_image_url TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    expires_at TIMESTAMPTZ,
    creator_id VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    custom_parameters JSONB
);

-- Create analytics table
CREATE TABLE link_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    link_id UUID NOT NULL,
    short_code VARCHAR(10) NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    referer TEXT,
    platform VARCHAR(50),
    device_type VARCHAR(50),
    browser VARCHAR(100),
    os VARCHAR(100),
    country VARCHAR(2),
    region VARCHAR(100),
    city VARCHAR(100),
    redirected_to TEXT,
    redirect_type VARCHAR(20),
    clicked_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    custom_data JSONB
);

-- Create indexes for performance
CREATE INDEX idx_dynamic_links_short_code ON dynamic_links(short_code);
CREATE INDEX idx_dynamic_links_active ON dynamic_links(is_active);
CREATE INDEX idx_dynamic_links_expires ON dynamic_links(expires_at);
CREATE INDEX idx_link_analytics_link_id ON link_analytics(link_id);
CREATE INDEX idx_link_analytics_short_code ON link_analytics(short_code);
CREATE INDEX idx_link_analytics_clicked_at ON link_analytics(clicked_at);
CREATE INDEX idx_link_analytics_platform ON link_analytics(platform);
```

### Step 3: Test Database Connection

Verify the setup works correctly:

```sql
-- Test table creation
\dt

-- Expected output should show:
--                List of relations
--  Schema |      Name       | Type  |     Owner
-- --------+-----------------+-------+----------------
--  public | dynamic_links   | table | dynalinks_user
--  public | link_analytics  | table | dynalinks_user

-- Test insert
INSERT INTO dynamic_links (short_code, fallback_url) 
VALUES ('test123', 'https://example.com');

-- Test select
SELECT id, short_code, fallback_url, created_at FROM dynamic_links WHERE short_code = 'test123';

-- Clean up test data
DELETE FROM dynamic_links WHERE short_code = 'test123';
```

## 🔒 Security Configuration

### Step 4: Configure PostgreSQL for External Access

Edit your PostgreSQL configuration files:

#### postgresql.conf
```bash
# Edit the PostgreSQL config file
sudo nano /etc/postgresql/15/main/postgresql.conf

# Add or modify these lines:
listen_addresses = '*'  # or specific IPs: 'localhost,your-k8s-cluster-ip'
port = 5432

# Performance tuning (adjust based on your server specs)
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
max_connections = 100
```

#### pg_hba.conf
```bash
# Edit the client authentication file
sudo nano /etc/postgresql/15/main/pg_hba.conf

# Add entry for your Kubernetes cluster (adjust IP range as needed)
# TYPE  DATABASE        USER               ADDRESS                 METHOD
host    dynalinks       dynalinks_user     10.0.0.0/8              md5
host    dynalinks       dynalinks_user     172.16.0.0/12           md5
host    dynalinks       dynalinks_user     192.168.0.0/16          md5

# Or for specific IP ranges if you know your K8s cluster network:
host    dynalinks       dynalinks_user     your-k8s-cidr/24       md5
```

### Step 5: Restart PostgreSQL

```bash
# Restart PostgreSQL to apply configuration changes
sudo systemctl restart postgresql

# Verify it's running
sudo systemctl status postgresql

# Check if it's listening on the correct port
sudo netstat -tlnp | grep 5432
```

## 🔗 Update Kubernetes Configuration

### Step 6: Update k8s-manifests.yaml

Edit the ConfigMap in your `k8s-manifests.yaml`:

```yaml
# In dynalinks-config ConfigMap:
data:
  DATABASE_HOST: "your-postgres-server-ip-or-domain"  # Your VPS IP or domain
  DATABASE_PORT: "5432"
  DATABASE_NAME: "dynalinks"
  DATABASE_USER: "dynalinks_user"
```

Update the Secret with base64 encoded password:

```bash
# Generate base64 encoded password
echo -n "your-strong-password-here" | base64

# Update the secret in k8s-manifests.yaml:
# DATABASE_PASSWORD: "base64-encoded-password-here"
```

## 🧪 Testing Connection from Kubernetes

### Step 7: Test Database Connectivity

After deploying to Kubernetes, test the connection:

```bash
# Deploy a test pod with PostgreSQL client
kubectl run postgres-client --rm -it --restart=Never --image=postgres:15-alpine -- bash

# Inside the pod, test connection
psql -h your-postgres-server-ip -p 5432 -U dynalinks_user -d dynalinks

# Test query
SELECT version();
\dt
\q
exit
```

## 🔧 Performance Optimization

### Step 8: Database Tuning (Optional)

For better performance with analytics data:

```sql
-- Connect as dynalinks_user
\c dynalinks dynalinks_user

-- Create additional indexes for common queries
CREATE INDEX CONCURRENTLY idx_analytics_date_platform 
ON link_analytics(clicked_at, platform) 
WHERE clicked_at >= (NOW() - INTERVAL '30 days');

CREATE INDEX CONCURRENTLY idx_analytics_country 
ON link_analytics(country) 
WHERE country IS NOT NULL;

-- Enable auto-vacuum for better maintenance
ALTER TABLE dynamic_links SET (autovacuum_enabled = true);
ALTER TABLE link_analytics SET (autovacuum_enabled = true);
```

## 🔍 Monitoring and Maintenance

### Useful Monitoring Queries

```sql
-- Check database size
SELECT 
    pg_database.datname,
    pg_database_size(pg_database.datname) AS size_bytes,
    pg_size_pretty(pg_database_size(pg_database.datname)) AS size_pretty
FROM pg_database 
WHERE datname = 'dynalinks';

-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    pg_total_relation_size(schemaname||'.'||tablename) AS size_bytes
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY size_bytes DESC;

-- Check recent activity
SELECT COUNT(*) as total_links FROM dynamic_links;
SELECT COUNT(*) as total_clicks FROM link_analytics;
SELECT COUNT(*) as clicks_today FROM link_analytics WHERE clicked_at >= CURRENT_DATE;
```

### Backup Script

```bash
#!/bin/bash
# backup-dynalinks.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/dynalinks"
mkdir -p $BACKUP_DIR

# Create backup
pg_dump -h localhost -U dynalinks_user -d dynalinks > $BACKUP_DIR/dynalinks_backup_$DATE.sql

# Compress backup
gzip $BACKUP_DIR/dynalinks_backup_$DATE.sql

# Keep only last 7 days of backups
find $BACKUP_DIR -name "dynalinks_backup_*.sql.gz" -mtime +7 -delete

echo "Backup completed: dynalinks_backup_$DATE.sql.gz"
```

## 🆘 Troubleshooting

### Common Issues

#### Connection Refused
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Check if port is open
sudo netstat -tlnp | grep 5432

# Check firewall (Ubuntu/Debian)
sudo ufw status
sudo ufw allow 5432
```

#### Authentication Failed
```bash
# Verify user exists
sudo -u postgres psql -c "\du"

# Test local connection
sudo -u postgres psql -d dynalinks -c "SELECT current_user;"

# Check pg_hba.conf entries
sudo cat /etc/postgresql/15/main/pg_hba.conf | grep dynalinks
```

#### Permission Denied
```sql
-- Grant missing privileges
\c dynalinks postgres
GRANT ALL PRIVILEGES ON DATABASE dynalinks TO dynalinks_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO dynalinks_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO dynalinks_user;
```

---

## ✅ Verification Checklist

- [ ] Database `dynalinks` created
- [ ] User `dynalinks_user` created with strong password
- [ ] All tables created with proper indexes
- [ ] PostgreSQL configured for external access
- [ ] Firewall allows connections on port 5432
- [ ] Connection tested from external client
- [ ] Kubernetes ConfigMap updated with correct database details
- [ ] Kubernetes Secret updated with base64 encoded password
- [ ] Application can connect and create/read links

Your external PostgreSQL database is now ready for DynaLinks! 🎉
