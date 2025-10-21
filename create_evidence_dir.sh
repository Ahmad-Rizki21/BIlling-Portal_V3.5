#!/bin/bash

# Create evidence directory for trouble ticket system
echo "Creating evidence directory for trouble ticket system..."

# Create directories
mkdir -p /var/www/billing-system/static/uploads/evidence

# Set proper permissions
chmod 755 /var/www/billing-system/static/uploads/evidence

echo "Evidence directory created successfully!"
echo "Path: /var/www/billing-system/static/uploads/evidence"
echo "Permissions: $(ls -la /var/www/billing-system/static/uploads/evidence)"