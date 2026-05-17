#!/bin/bash

# ec2-backend-setup.sh
# Run this script on your fresh Ubuntu EC2 instance

# 1. Update packages
sudo apt update && sudo apt upgrade -y

# 2. Install Docker & Docker Compose
sudo apt install docker.io docker-compose -y
sudo systemctl enable docker
sudo systemctl start docker

# 3. Add current user to docker group (requires logout/login or newgrp)
sudo usermod -aG docker $USER

# 4. Install Nginx and Certbot (for SSL)
sudo apt install nginx certbot python3-certbot-nginx -y

# 5. Clone repository (Replace with your actual repo URL)
# git clone https://github.com/yourusername/NexusAI.git
# cd NexusAI

echo "========================================================="
echo "Setup Complete!"
echo "Next Steps:"
echo "1. Clone your repository onto the EC2 instance."
echo "2. Populate your .env file in the backend directory."
echo "3. Run: sudo docker-compose -f docker-compose.prod.yml up -d"
echo "4. Configure Nginx reverse proxy and run certbot for SSL."
echo "========================================================="
