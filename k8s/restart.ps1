# Скрипт для полного переразвертывания приложения в Kubernetes (PowerShell)

Write-Host "🔄 Full restart of Restaurant Management System..." -ForegroundColor Cyan

# Удаляем все deployments, но оставляем данные (PVC, ConfigMap, Secrets)
Write-Host "Deleting deployments..." -ForegroundColor Yellow
kubectl delete deployment backend-api backend-auth health-monitor frontend -n restaurant
kubectl delete deployment redis -n restaurant

Write-Host "✅ Deployments deleted" -ForegroundColor Green

# Ждем 5 секунд
Write-Host "Waiting 5 seconds..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Применяем манифесты заново
Write-Host "Redeploying services..." -ForegroundColor Cyan
kubectl apply -f 04-redis-deployment.yaml
kubectl apply -f 05-backend-auth-deployment.yaml
kubectl apply -f 06-backend-api-deployment.yaml
kubectl apply -f 07-health-monitor-deployment.yaml
kubectl apply -f 08-frontend-deployment.yaml

Write-Host "✅ Services redeployed" -ForegroundColor Green

Write-Host ""
Write-Host "Waiting for deployments to be ready..." -ForegroundColor Cyan
kubectl wait --for=condition=available --timeout=300s deployment/redis -n restaurant
kubectl wait --for=condition=available --timeout=300s deployment/backend-api -n restaurant
kubectl wait --for=condition=available --timeout=300s deployment/backend-auth -n restaurant
kubectl wait --for=condition=available --timeout=300s deployment/health-monitor -n restaurant
kubectl wait --for=condition=available --timeout=300s deployment/frontend -n restaurant

Write-Host ""
Write-Host "✅ Full restart complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Checking pod status..." -ForegroundColor Cyan
kubectl get pods -n restaurant

Write-Host ""
Write-Host "To check logs:" -ForegroundColor Yellow
Write-Host "  kubectl logs -n restaurant deployment/backend-api --tail=50" -ForegroundColor White
Write-Host "  kubectl logs -n restaurant deployment/health-monitor --tail=50" -ForegroundColor White

