# Скрипт для обновления развертывания приложения в Kubernetes (PowerShell)

Write-Host "Updating Restaurant Management System in Kubernetes..." -ForegroundColor Cyan

# Применяем обновленные манифесты
kubectl apply -f 05-backend-auth-deployment.yaml
kubectl apply -f 06-backend-api-deployment.yaml
kubectl apply -f 07-health-monitor-deployment.yaml

Write-Host "✅ Deployments updated" -ForegroundColor Green

# Перезапускаем деплойменты
Write-Host "Restarting deployments..." -ForegroundColor Cyan
kubectl rollout restart deployment/backend-auth -n restaurant
kubectl rollout restart deployment/backend-api -n restaurant
kubectl rollout restart deployment/health-monitor -n restaurant

Write-Host "✅ Rollout initiated" -ForegroundColor Green

Write-Host ""
Write-Host "Waiting for rollout to complete..." -ForegroundColor Cyan
kubectl rollout status deployment/backend-auth -n restaurant
kubectl rollout status deployment/backend-api -n restaurant
kubectl rollout status deployment/health-monitor -n restaurant

Write-Host ""
Write-Host "✅ Update complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Checking pod status..." -ForegroundColor Cyan
kubectl get pods -n restaurant

Write-Host ""
Write-Host "To watch pods:" -ForegroundColor Yellow
Write-Host "  kubectl get pods -n restaurant -w" -ForegroundColor White
Write-Host ""
Write-Host "To check logs:" -ForegroundColor Yellow
Write-Host "  kubectl logs -n restaurant deployment/backend-api --tail=50" -ForegroundColor White
Write-Host "  kubectl logs -n restaurant deployment/health-monitor --tail=50" -ForegroundColor White

