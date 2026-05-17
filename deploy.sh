#!/bin/bash

# deploy.sh
# Run this on your EC2 instance to deploy updates

echo "Starting deployment..."

# 1. Pull latest changes
git pull origin main

# 2. Build and restart Docker Compose containers
echo "Building and restarting Docker containers..."
sudo docker-compose -f aws-scripts/docker-compose.prod.yml down
sudo docker-compose -f aws-scripts/docker-compose.prod.yml up --build -d

echo "Cleaning up dangling images..."
sudo docker image prune -f

echo "Deployment complete! Application is now running."
