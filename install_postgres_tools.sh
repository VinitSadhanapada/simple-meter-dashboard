#!/bin/bash
# PostgreSQL Tools Installation Script

echo "Installing PostgreSQL GUI and CLI tools..."

# Update package list
sudo apt update

# Install enhanced CLI tools
echo "Installing pgcli..."
pip3 install pgcli

echo "Installing pspg (better pager for psql)..."
sudo apt install -y pspg

# Install DBeaver (Universal database tool)
echo "Installing DBeaver..."
sudo snap install dbeaver-ce

# Try to install pgAdmin 4 via snap
echo "Installing pgAdmin 4..."
if sudo snap install pgadmin4; then
    echo "✅ pgAdmin 4 installed via snap"
else
    echo "⚠️  pgAdmin 4 snap failed, trying official repository..."
    
    # Add official pgAdmin repository
    curl -fsSL https://www.pgadmin.org/static/packages_pgadmin_org.pub | sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/packages_pgadmin_org.gpg
    sudo sh -c 'echo "deb https://ftp.postgresql.org/pub/pgadmin/pgadmin4/apt/$(lsb_release -cs) pgadmin4 main" > /etc/apt/sources.list.d/pgadmin4.list'
    sudo apt update
    
    if sudo apt install -y pgadmin4; then
        echo "✅ pgAdmin 4 installed via repository"
    else
        echo "❌ pgAdmin 4 installation failed"
    fi
fi

# Install Adminer (lightweight web interface)
echo "Installing Adminer..."
wget https://www.adminer.org/latest.php -O /tmp/adminer.php
sudo mkdir -p /var/www/html/adminer
sudo mv /tmp/adminer.php /var/www/html/adminer/index.php

# Create database connection aliases
echo "Setting up database aliases..."
cat >> ~/.bashrc << 'EOF'

# PostgreSQL aliases
export PGUSER=mfmuser
export PGDATABASE=mfmdb
export PGHOST=localhost
export PAGER=pspg

# Quick database connection
alias pgdb='pgcli postgresql://mfmuser:devi@localhost:5432/mfmdb'
alias pgpsql='psql -U mfmuser -d mfmdb -h localhost'

EOF

echo ""
echo "🎉 Installation complete!"
echo ""
echo "Available tools:"
echo "1. DBeaver (GUI): Launch from applications menu"
echo "2. pgAdmin 4: Launch from applications menu or web interface"
echo "3. pgcli: Run 'pgdb' command for enhanced CLI"
echo "4. Adminer: http://localhost/adminer/ (if web server running)"
echo ""
echo "Reload your terminal or run: source ~/.bashrc"
echo ""
echo "Test connection with: pgdb"