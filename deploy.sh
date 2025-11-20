#!/bin/bash

# Chaa Choo Deployment Script for Hostinger VPS
# This script automates the deployment process
# Usage: bash deploy.sh

set -e  # Exit on error

echo "================================================"
echo "Chaa Choo Deployment Script"
echo "================================================"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="chaa-choo"
APP_DIR="/home/chaa-choo"
DOMAIN="yourdomain.com"
DB_NAME="cafe_ca3"
DB_USER="cafe_user"
PYTHON_VERSION="python3.11"

# Check if running as root or with sudo
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}This script must be run as root${NC}"
   exit 1
fi

echo -e "${YELLOW}Step 1: Update system packages${NC}"
apt update && apt upgrade -y

echo -e "${YELLOW}Step 2: Install system dependencies${NC}"
apt install -y \
    curl wget git \
    python3.11 python3.11-venv python3.11-dev \
    mysql-server mysql-client \
    nginx \
    certbot python3-certbot-nginx \
    supervisor \
    fail2ban \
    ufw

echo -e "${YELLOW}Step 3: Create application user${NC}"
if ! id -u www-data > /dev/null 2>&1; then
    useradd -m -s /bin/bash www-data
fi

echo -e "${YELLOW}Step 4: Setup application directory${NC}"
if [ ! -d "$APP_DIR" ]; then
    mkdir -p "$APP_DIR"
fi
chown -R www-data:www-data "$APP_DIR"
chmod -R 755 "$APP_DIR"

echo -e "${YELLOW}Step 5: Copy application files${NC}"
# Copy all application files to APP_DIR (done manually or via git)
echo "Please copy your application files to $APP_DIR"

echo -e "${YELLOW}Step 6: Create Python virtual environment${NC}"
cd "$APP_DIR"
$PYTHON_VERSION -m venv venv
source venv/bin/activate

echo -e "${YELLOW}Step 7: Install Python dependencies${NC}"
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install gunicorn python-dotenv

echo -e "${YELLOW}Step 8: Setup MySQL database${NC}"
echo "Creating database user..."
mysql -u root -p"" <<EOF
CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY 'your_secure_password';
CREATE DATABASE IF NOT EXISTS $DB_NAME;
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';
FLUSH PRIVILEGES;
EOF

echo -e "${YELLOW}Step 9: Create log directories${NC}"
mkdir -p /var/log/gunicorn
mkdir -p /var/log/nginx
chown -R www-data:www-data /var/log/gunicorn

echo -e "${YELLOW}Step 10: Setup Nginx${NC}"
cp "$APP_DIR/nginx.conf" /etc/nginx/sites-available/$APP_NAME
ln -sf /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/$APP_NAME
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
nginx -t

echo -e "${YELLOW}Step 11: Setup SSL with Let's Encrypt${NC}"
certbot certonly --nginx -d "$DOMAIN" -d "www.$DOMAIN" --non-interactive --agree-tos

echo -e "${YELLOW}Step 12: Setup systemd service${NC}"
cp "$APP_DIR/chaa-choo.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable chaa-choo.service

echo -e "${YELLOW}Step 13: Setup firewall${NC}"
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
echo "y" | ufw enable

echo -e "${YELLOW}Step 14: Start services${NC}"
systemctl start mysql
systemctl start nginx
systemctl start chaa-choo

echo -e "${YELLOW}Step 15: Setup automatic certificate renewal${NC}"
# Create a timer for certificate renewal
cat > /etc/systemd/system/certbot-renew.timer <<'EOF'
[Unit]
Description=Certbot Renewal Timer

[Timer]
OnCalendar=daily
OnBootSec=12h
Persistent=true

[Install]
WantedBy=timers.target
EOF

cat > /etc/systemd/system/certbot-renew.service <<'EOF'
[Unit]
Description=Certbot Renewal

[Service]
Type=oneshot
ExecStart=/usr/bin/certbot renew --quiet --agree-tos
ExecPostStart=/bin/systemctl reload nginx
EOF

systemctl daemon-reload
systemctl enable certbot-renew.timer
systemctl start certbot-renew.timer

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Next steps:"
echo "1. Update the domain name in nginx.conf"
echo "2. Update database credentials in .env.production"
echo "3. Verify the application is running: systemctl status chaa-choo"
echo "4. Check logs: journalctl -u chaa-choo -f"
echo "5. Test website: https://$DOMAIN"
echo ""
echo "Important commands:"
echo "  View logs: journalctl -u chaa-choo -f"
echo "  Restart app: systemctl restart chaa-choo"
echo "  Reload nginx: systemctl reload nginx"
echo "  Check app status: systemctl status chaa-choo"
