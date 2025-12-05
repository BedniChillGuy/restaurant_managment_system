#!/bin/bash
# Скрипт для развертывания приложения в Kubernetes

echo "Deploying Restaurant Management System to Kubernetes..."

# Применяем манифесты по порядку
kubectl apply -f 00-namespace.yaml
echo "✅ Namespace created"

kubectl apply -f 01-configmap.yaml
echo "✅ ConfigMap and Secrets created"

kubectl apply -f 02-postgres-pvc.yaml
echo "✅ PostgreSQL PVC created"

kubectl apply -f 03-postgres-statefulset.yaml
echo "✅ PostgreSQL StatefulSet created"

kubectl apply -f 04-redis-deployment.yaml
echo "✅ Redis Deployment created"

kubectl apply -f 05-backend-auth-deployment.yaml
echo "✅ Backend Auth Deployment created"

kubectl apply -f 06-backend-api-deployment.yaml
echo "✅ Backend API Deployment created"

kubectl apply -f 07-health-monitor-deployment.yaml
echo "✅ Health Monitor Deployment created"

kubectl apply -f 08-frontend-deployment.yaml
echo "✅ Frontend Deployment created"

kubectl apply -f 09-services.yaml
echo "✅ Services created"

kubectl apply -f 10-ingress.yaml
echo "✅ Ingress created"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Checking pod status..."
kubectl get pods -n restaurant

echo ""
echo "To watch pods starting:"
echo "  kubectl get pods -n restaurant -w"
echo ""
echo "To access the application:"
echo "  minikube service frontend -n restaurant"
echo ""
echo "Or with Ingress:"
echo "  Add to /etc/hosts: \$(minikube ip) restaurant.local"
echo "  Then visit: http://restaurant.local"

