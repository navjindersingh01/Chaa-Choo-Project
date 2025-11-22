# Pre-Deployment Checklist for Hostinger VPS

## Before You Deploy

### 1. Domain Setup ✓
- [ ] Domain registered
- [ ] Domain points to VPS IP address
- [ ] DNS A record configured
- [ ] WWW CNAME record configured (optional)
- [ ] Domain propagation checked (24-48 hours)

### 2. VPS Setup ✓
- [ ] VPS created on Hostinger
- [ ] SSH access confirmed
- [ ] Root password changed
- [ ] SSH key setup (recommended)
- [ ] VPS specs noted (CPU, RAM, Storage)

### 3. Application Preparation ✓
- [ ] All code committed to git
- [ ] `.env.production` file created
- [ ] Database migrations tested
- [ ] All secrets removed from code
- [ ] requirements.txt updated
- [ ] Application tested locally
- [ ] Static files optimized

### 4. Configuration Files Ready ✓
- [ ] nginx.conf updated with domain name
- [ ] gunicorn_config.py configured
- [ ] chaa-choo.service created
- [ ] wsgi.py ready
- [ ] docker-compose.yml (if using Docker)
- [ ] Dockerfile (if using Docker)

### 5. Documentation Prepared ✓
- [ ] README.md completed
- [ ] DEPLOYMENT_GUIDE.md reviewed
- [ ] Admin credentials documented (securely)
- [ ] Backup procedures documented

## During Deployment

### Step 1: Initial Server Setup
- [ ] Connect via SSH
- [ ] Update system packages
- [ ] Install dependencies (Python, MySQL, Nginx)
- [ ] Set timezone
- [ ] Configure firewall

### Step 2: Application Setup
- [ ] Clone application from git
- [ ] Setup Python virtual environment
- [ ] Install Python dependencies
- [ ] Create application user
- [ ] Set correct file permissions

### Step 3: Database Setup
- [ ] Install MySQL Server
- [ ] Create database user
- [ ] Create database
- [ ] Run migrations
- [ ] Import initial data (if exists)
- [ ] Backup database

### Step 4: Web Server Setup
- [ ] Install Nginx
- [ ] Copy nginx.conf
- [ ] Update domain names in config
- [ ] Test Nginx configuration
- [ ] Enable Nginx service
- [ ] Test HTTP access

### Step 5: SSL Certificate
- [ ] Generate SSL certificate with Certbot
- [ ] Update nginx.conf with certificate paths
- [ ] Test HTTPS access
- [ ] Verify SSL rating (A+ on SSL Labs)
- [ ] Setup automatic renewal

### Step 6: Application Server Setup
- [ ] Install Gunicorn
- [ ] Copy gunicorn_config.py
- [ ] Create systemd service file
- [ ] Enable application service
- [ ] Start application
- [ ] Check application status

### Step 7: Final Testing
- [ ] Visit https://yourdomain.com
- [ ] Check homepage loads
- [ ] Test login functionality
- [ ] Test order creation
- [ ] Check all dashboards
- [ ] Verify database operations
- [ ] Check logs for errors

### Step 8: Monitoring & Logging
- [ ] Setup log rotation
- [ ] Configure monitoring alerts
- [ ] Test backup procedure
- [ ] Document backup location
- [ ] Setup daily backup cron job

## Post-Deployment

### Immediate (Day 1)
- [ ] Monitor application for errors
- [ ] Check SSL certificate validity
- [ ] Verify email notifications work
- [ ] Test all user roles
- [ ] Confirm database backups running
- [ ] Update status on domain registrar if needed

### Week 1
- [ ] Monitor traffic and errors
- [ ] Review access logs
- [ ] Check disk usage
- [ ] Verify backup integrity
- [ ] Load test the application
- [ ] Document any issues found

### Monthly
- [ ] Review system updates
- [ ] Test SSL renewal
- [ ] Verify backups complete
- [ ] Analyze performance metrics
- [ ] Review security logs
- [ ] Check certificate expiration (90 days from issue)

### Quarterly
- [ ] Full security audit
- [ ] Performance optimization review
- [ ] Database optimization
- [ ] Capacity planning check
- [ ] Disaster recovery drill

## Deployment Script Checklist

If using automated deployment script:

```bash
# Before running
- [ ] Update deploy.sh with your values
- [ ] Review all paths in deploy.sh
- [ ] Test script in staging environment
- [ ] Have rollback plan ready

# Running
- [ ] Run as root or with sudo
- [ ] Monitor output for errors
- [ ] Note any warnings
- [ ] Keep terminal open until complete

# After running
- [ ] Check all services running
- [ ] Verify website accessibility
- [ ] Review application logs
- [ ] Test critical features
```

## Docker Deployment Checklist

If using Docker:

```bash
- [ ] Docker installed and running
- [ ] docker-compose installed
- [ ] All .env variables set
- [ ] docker-compose.yml reviewed
- [ ] Sufficient disk space for images
- [ ] Port 80 and 443 available
- [ ] MySQL volume path exists
- [ ] Build images: docker-compose build
- [ ] Start services: docker-compose up -d
- [ ] Verify all containers running
- [ ] Check logs: docker-compose logs -f
```

## Security Checklist

- [ ] SSH key configured (not password login)
- [ ] Firewall enabled (UFW)
- [ ] Only necessary ports open (22, 80, 443)
- [ ] Fail2Ban installed and configured
- [ ] Regular security updates enabled
- [ ] Database password is strong
- [ ] SECRET_KEY is unique and long
- [ ] No default credentials used
- [ ] SSL/TLS configured (A+ rating)
- [ ] HTTP redirects to HTTPS
- [ ] Security headers configured in Nginx

## Performance Checklist

- [ ] Gzip compression enabled
- [ ] Caching headers set
- [ ] Static files optimized
- [ ] Database queries optimized
- [ ] Connection pooling configured
- [ ] Worker processes tuned
- [ ] Memory usage monitored
- [ ] Load balancing setup (if needed)

## Backup & Recovery Checklist

- [ ] Automated backups running
- [ ] Backup storage location verified
- [ ] Tested restore procedure
- [ ] Backup retention policy set
- [ ] Off-site backup configured (recommended)
- [ ] Disaster recovery plan documented

## Troubleshooting Quick Links

### Common Issues & Solutions

1. **Application won't start**
   - Check Python version: `python3 --version`
   - Check MySQL running: `systemctl status mysql`
   - View logs: `journalctl -u chaa-choo -f`

2. **SSL certificate issues**
   - Renew certificate: `certbot renew --force-renewal`
   - Check validity: `certbot certificates`
   - Reload Nginx: `systemctl reload nginx`

3. **Database connection failed**
   - Check MySQL running: `systemctl status mysql`
   - Verify credentials in .env
   - Test connection: `mysql -u cafe_user -p -h localhost`

4. **High CPU/Memory usage**
   - Check Gunicorn worker count
   - Monitor processes: `top` or `htop`
   - Review application logs

5. **Disk space full**
   - Check disk usage: `df -h`
   - Clear old logs: `journalctl --vacuum=30d`
   - Check database size: `du -sh /var/lib/mysql`

## Emergency Contacts

- Hosting Provider Support: [Hostinger Support]
- Domain Registrar: [Your Registrar]
- SSL Certificate: [Let's Encrypt Support]
- Application Owner: [Your Contact Info]

## Notes

Use this section to document deployment-specific information:

```
VPS IP: ___________________
Domain: ___________________
SSH Port: ___________________
Database Password: ___________________
Admin Username: ___________________
Backup Location: ___________________
Support Contact: ___________________
```

---

**Deployment Date:** ___________________

**Deployed By:** ___________________

**Reviewed By:** ___________________

**Sign-off Date:** ___________________
