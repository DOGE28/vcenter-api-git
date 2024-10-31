#!/bin/bash

set -e

# Function to display messages
function echo_message() {
    echo
    echo "----------------------"
    echo $1
    echo "----------------------"
    echo
}

cd
mkdir VMware-Alerts && cd VMware-Alerts


# Update and install system dependencies

echo_message "Updating and installing system dependencies"
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip

echo "System dependencies have been updated and installed successfully"

# Install the required Python packages

echo_message "Installing the required Python packages..."
pip install --upgrade pip
pip install -r requirements.txt
echo
echo "Python dependencies have been installed successfully"

# Prompt user for Keycloak and SMTP configurations

echo_message "Please provide the following configurations:"
echo

read -p "Keycloak Client Secret: " keycloak_client_secret
read -p "SMTP Address: " smtp_address
read -p "SMTP Port: " smtp_port
read -p "SMTP Sender: " smtp_sender
read -p "SMTP Receiver: " smtp_receiver
read -p "Threshold Percent (default: 90) " threshold
read -p "Interval in minutes (default: 10): " interval

# Create .env file

echo_message "Creating .env file..."

cat <<EOL > .env
keycloak_client_id=$keycloak_client_id
keycloak_client_secret=$keycloak_client_secret
smtp_address=$smtp_address
smtp_port=$smtp_port
smtp_sender=$smtp_sender
smtp_receiver=$smtp_receiver
threshold=$threshold
interval=$interval
EOL

echo
echo ".env file has been created successfully"
echo

# Create systemd service



echo_message "Creating systemd service..."

PWD=$(pwd)

echo "[Unit]
Description=Zerto Alerts Service
After=network.target

[Service]
ExecStart=/bin/bash $PWD/run.sh
Restart=always
RestartSec=5
User=zadmin
WorkingDirectory=$PWD

StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target" | sudo tee /etc/systemd/system/zerto-alerts.service > /dev/null

echo
echo "Systemd service has been created successfully"

# Start and enable the systemd service

echo_message "Starting and enabling the systemd service..."

sudo systemctl daemon-reload
sudo systemctl start zerto-alerts
sudo systemctl enable zerto-alerts

echo

echo "Systemd service has been started and enabled successfully"

echo_message "Installation has been completed successfully. The Zerto Alerts service is now running."
