#!/bin/bash
# Скрипт для обновления развертывания приложения в Kubernetes

echo "Updating Restaurant Management System in Kubernetes..."

# Применяем обновленные манифесты
kubectl apply -f 05-backend-auth-deployment.yaml
kubectl apply -f 06-backend-api-deployment.yaml
kubectl apply -f 07-health-monitor-deployment.yaml

echo "✅ Deployments updated"

# Перезапускаем деплойменты
echo "Restarting deployments..."
kubectl rollout restart deployment/backend-auth -n restaurant
kubectl rollout restart deployment/backend-api -n restaurant
kubectl rollout restart deployment/health-monitor -n restaurant

echo "✅ Rollout initiated"

echo ""
echo "Waiting for rollout to complete..."
kubectl rollout status deployment/backend-auth -n restaurant
kubectl rollout status deployment/backend-api -n restaurant
kubectl rollout status deployment/health-monitor -n restaurant

echo ""
echo "✅ Update complete!"
echo ""
echo "Checking pod status..."
kubectl get pods -n restaurant

echo ""
echo "To watch pods:"
echo "  kubectl get pods -n restaurant -w"
echo ""
echo "To check logs:"
echo "  kubectl logs -n restaurant deployment/backend-api --tail=50"
echo "  kubectl logs -n restaurant deployment/health-monitor --tail=50"

