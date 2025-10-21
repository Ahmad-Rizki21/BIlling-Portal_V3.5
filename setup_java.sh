#!/bin/bash

# Script untuk install Java OpenJDK 17 dan setup JAVA_HOME

echo "Installing Java OpenJDK 17..."

# Update package list
sudo apt update

# Install OpenJDK 17
sudo apt install -y openjdk-17-jdk openjdk-17-jre

# Verify installation
echo "Verifying Java installation..."
java -version

# Set JAVA_HOME environment variable
JAVA_HOME=$(dirname $(dirname $(readlink -f $(which java)))
echo "export JAVA_HOME=$JAVA_HOME" >> ~/.bashrc
echo "export PATH=\$JAVA_HOME/bin:\$PATH" >> ~/.bashrc

# Reload bashrc
source ~/.bashrc

echo "JAVA_HOME set to: $JAVA_HOME"
echo "Java version:"
java -version

echo "Setup completed! Please restart your terminal or run: source ~/.bashrc"