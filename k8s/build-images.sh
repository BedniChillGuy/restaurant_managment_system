#!/bin/bash
# Скрипт для сборки Docker образов

echo "Building Restaurant Management System Docker images..."

# Переходим в корневую директорию проекта
cd "$(dirname "$0")/.."

# Сборка backend образа
echo "Building backend image..."
docker build -t restaurant-backend:latest ./backend
if [ $? -eq 0 ]; then
    echo "✅ Backend image built successfully"
else
    echo "❌ Failed to build backend image"
    exit 1
fi

# Сборка frontend образа
echo "Building frontend image..."
docker build -t restaurant-frontend:latest ./frontend
if [ $? -eq 0 ]; then
    echo "✅ Frontend image built successfully"
else
    echo "❌ Failed to build frontend image"
    exit 1
fi

echo ""
echo "✅ All images built successfully!"
echo ""
echo "Images:"
docker images | grep restaurant

echo ""
echo "To use with Minikube, run:"
echo "eval \$(minikube docker-env)"
echo "Then run this script again."

