# Chaa Choo - Docker Deployment Guide

## What is Docker?

Docker allows you to package your application with all its dependencies into a container that can run on any machine. This is ideal for VPS hosting as it ensures consistency between development and production.

## Prerequisites

- Docker Engine (18.09+)
- Docker Compose (1.25+)
- Your domain name pointing to VPS IP

## Quick Start with Docker (Recommended)

### 1. Install Docker on Hostinger VPS

```bash
# SSH into your VPS
ssh root@your_vps_ip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add your user to docker group (optional, for non-root usage)
sudo usermod -aG docker $USER
```

### 2. Prepare Your Project

```bash
# On your local machine
# Ensure these files are in your project root:
# - Dockerfile
# - docker-compose.yml
# - app.py
# - requirements.txt
# - .env.production
# - nginx.conf

# Copy to VPS
scp -r ~/chaa-choo root@your_vps_ip:/home/chaa-choo
```

### 3. Update Configuration

```bash
# SSH to VPS
ssh root@your_vps_ip
cd /home/chaa-choo

# Edit environment variables
nano .env.production

# Update:
# - DB_PASSWORD: Strong password
# - SECRET_KEY: Generate with: python3 -c 'import secrets; print(secrets.token_hex(32))'
# - DOMAIN: Your actual domain
```

### 4. Update docker-compose.yml

```bash
# Edit docker-compose.yml
nano docker-compose.yml

# Update MySQL passwords:
MYSQL_ROOT_PASSWORD=your_strong_root_password
MYSQL_PASSWORD=your_strong_user_password

# Update nginx.conf path if needed
```

### 5. Setup SSL Certificate

```bash
# Create directories for SSL
mkdir -p /etc/letsencrypt /var/www/certbot

# Generate SSL certificate using Certbot
docker run -it --rm -v /etc/letsencrypt:/etc/letsencrypt \
  -v /var/www/certbot:/var/www/certbot \
  certbot/certbot certonly --standalone \
  -d yourdomain.com -d www.yourdomain.com
```

### 6. Start Application with Docker Compose

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Verify all services are running
docker-compose ps
```

### 7. Initial Setup

```bash
# Run database migrations
docker-compose exec web python setup_db.py

# Create admin user
docker-compose exec web python set_passwords_and_roles.py

# Check application is running
curl https://yourdomain.com
```

## Docker Commands

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f mysql
docker-compose logs -f nginx
```

### Managing Services

```bash
# Stop all services
docker-compose stop

# Start all services
docker-compose start

# Restart all services
docker-compose restart

# Remove all containers (but keep volumes)
docker-compose down

# Remove everything including volumes
docker-compose down -v
```

### Backup and Restore

```bash
# Backup MySQL database
docker-compose exec mysql mysqldump -u cafe_user -p cafe_ca3 > backup.sql

# Restore from backup
docker-compose exec -T mysql mysql -u cafe_user -p cafe_ca3 < backup.sql
```

### Accessing Services

```bash
# Execute commands in web container
docker-compose exec web bash
docker-compose exec web python script.py

# Access MySQL directly
docker-compose exec mysql mysql -u root -p

# Access Nginx logs
docker-compose exec nginx tail -f /var/log/nginx/access.log
```

## Health Checks

```bash
# Check if application is healthy
docker-compose ps

# Check specific service
docker-compose exec web curl http://localhost:5000/health

# Monitor container resource usage
docker stats
```

## Troubleshooting

### Port Already in Use

```bash
# Find what's using the port
lsof -i :80
lsof -i :443
lsof -i :5000
lsof -i :3306

# Kill the process
kill -9 <PID>
```

### Database Connection Error

```bash
# Check MySQL logs
docker-compose logs mysql

# Check if MySQL is ready
docker-compose exec mysql mysqladmin ping -u root -p
```

### Nginx SSL Errors

```bash
# Verify SSL certificates exist
ls -la /etc/letsencrypt/live/yourdomain.com/

# Test Nginx configuration
docker-compose exec nginx nginx -t

# Check Nginx logs
docker-compose logs nginx
```

### Application Not Starting

```bash
# Check application logs
docker-compose logs web

# Rebuild without cache
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Update Application

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d

# Or use docker-compose up --build to do both at once
docker-compose up --build -d
```

## Scaling

For higher traffic, you can run multiple instances:

```yaml
# In docker-compose.yml, modify web service:
services:
  web:
    # ... existing config ...
    deploy:
      replicas: 3
```

## Production Security Best Practices

1. **Never commit secrets to git**
   ```bash
   # Add to .gitignore
   .env.production
   .env
   ```

2. **Use strong passwords**
   ```bash
   # Generate secure password
   python3 -c 'import secrets; print(secrets.token_urlsafe(32))'
   ```

3. **Keep images updated**
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

4. **Monitor and log everything**
   ```bash
   docker-compose logs -f --tail=100
   ```

5. **Regular backups**
   ```bash
   # Daily backup script
   #!/bin/bash
   DATE=$(date +%Y%m%d_%H%M%S)
   docker-compose exec -T mysql mysqldump -u cafe_user -p'password' cafe_ca3 > /backups/cafe_ca3_$DATE.sql
   ```

## Cron Job for Automatic Backups

```bash
# Add to crontab
crontab -e

# Add this line for daily backups at 2 AM
0 2 * * * cd /home/chaa-choo && docker-compose exec -T mysql mysqldump -u cafe_user -p'your_password' cafe_ca3 > /backups/cafe_ca3_$(date +\%Y\%m\%d_\%H\%M\%S).sql
```

## SSL Certificate Renewal

```bash
# Manual renewal
docker run -it --rm -v /etc/letsencrypt:/etc/letsencrypt certbot/certbot renew

# Or add to crontab for automatic renewal
0 3 1 * * docker run -it --rm -v /etc/letsencrypt:/etc/letsencrypt certbot/certbot renew --quiet
```

## Useful Docker Compose Aliases

Add to your .bashrc or .zshrc:

```bash
alias dc='docker-compose'
alias dcup='docker-compose up -d'
alias dcdown='docker-compose down'
alias dclogs='docker-compose logs -f'
alias dcexec='docker-compose exec'
alias dcps='docker-compose ps'
```

Then use:
```bash
dc ps
dcup
dclogs web
dcexec web bash
```

## When to Use Docker vs Traditional Deployment

**Use Docker when:**
- You want consistent development and production environments
- You plan to scale the application
- You want easy rollback capabilities
- You're using a managed container service

**Use Traditional Deployment when:**
- You prefer direct system access
- You have specific hardware requirements
- You want minimal abstraction layers
- Your team is not familiar with Docker

## Support

For Docker-specific issues, visit:
- Docker documentation: https://docs.docker.com
- Docker Compose: https://docs.docker.com/compose
- Hosting Docker on VPS: Check your VPS provider's documentation
