# Kubernetes Deployment для Restaurant Management System

## Архитектура

Приложение состоит из следующих компонентов:

- **PostgreSQL** (StatefulSet) - база данных
- **Redis** (Deployment) - кэш и rate limiting
- **Backend Auth** (Deployment) - сервис аутентификации
- **Backend API** (Deployment, 2 реплики) - основной API
- **Health Monitor** (Deployment) - мониторинг состояния сервисов
- **Frontend** (Deployment, 2 реплики) - веб-интерфейс

## Предварительные требования

1. Kubernetes кластер (Minikube, Kind, или облачный провайдер)
2. kubectl настроен и подключен к кластеру
3. Docker образы собраны и доступны:
   - `restaurant-backend:latest`
   - `restaurant-frontend:latest`

## Сборка Docker образов

### Backend
```bash
cd backend
docker build -t restaurant-backend:latest .
```

### Frontend
```bash
cd frontend
docker build -t restaurant-frontend:latest .
```

### Для Minikube
```bash
eval $(minikube docker-env)
docker build -t restaurant-backend:latest ./backend
docker build -t restaurant-frontend:latest ./frontend
```

## Развертывание

### 1. Применить все манифесты по порядку

```bash
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/01-configmap.yaml
kubectl apply -f k8s/02-postgres-pvc.yaml
kubectl apply -f k8s/03-postgres-statefulset.yaml
kubectl apply -f k8s/04-redis-deployment.yaml
kubectl apply -f k8s/05-backend-auth-deployment.yaml
kubectl apply -f k8s/06-backend-api-deployment.yaml
kubectl apply -f k8s/07-health-monitor-deployment.yaml
kubectl apply -f k8s/08-frontend-deployment.yaml
kubectl apply -f k8s/09-services.yaml
kubectl apply -f k8s/10-ingress.yaml
```

### 2. Или применить всё сразу

```bash
kubectl apply -f k8s/
```

## Проверка статуса развертывания

```bash
# Проверить все ресурсы в namespace restaurant
kubectl get all -n restaurant

# Проверить статус подов
kubectl get pods -n restaurant

# Просмотр логов конкретного пода
kubectl logs -n restaurant -l app=backend-api

# Проверка health monitor
kubectl logs -n restaurant -l app=health-monitor -f
```

## Доступ к приложению

### С LoadBalancer (облачные провайдеры)
```bash
kubectl get svc frontend -n restaurant
# Используй EXTERNAL-IP для доступа
```

### С NodePort (Minikube)
```bash
minikube service frontend -n restaurant
```

### С Ingress
```bash
# Для Minikube
minikube addons enable ingress

# Добавь в /etc/hosts (или C:\Windows\System32\drivers\etc\hosts)
<MINIKUBE_IP> restaurant.local

# Получить IP
minikube ip

# Доступ через браузер
http://restaurant.local
```

## Масштабирование

```bash
# Увеличить количество реплик backend-api
kubectl scale deployment backend-api -n restaurant --replicas=3

# Увеличить количество реплик frontend
kubectl scale deployment frontend -n restaurant --replicas=3
```

## Обновление приложения

### Обновление после изменения кода

```bash
# Для Minikube - переключись на Docker окружение Minikube
eval $(minikube docker-env)  # Linux/Mac
minikube docker-env | Invoke-Expression  # Windows PowerShell

# Пересобрать образы
docker build -t restaurant-backend:latest ./backend
docker build -t restaurant-frontend:latest ./frontend

# Перезапустить deployments (используй скрипт)
cd k8s
./redeploy.sh  # Linux/Mac
.\redeploy.ps1  # Windows PowerShell

# Или вручную:
kubectl rollout restart deployment/backend-api -n restaurant
kubectl rollout restart deployment/backend-auth -n restaurant
kubectl rollout restart deployment/health-monitor -n restaurant
kubectl rollout restart deployment/frontend -n restaurant
```

### Обновление с новой версией образа

```bash
# Пересобрать образ с тегом версии
docker build -t restaurant-backend:v2 ./backend

# Обновить deployment
kubectl set image deployment/backend-api backend-api=restaurant-backend:v2 -n restaurant

# Проверить статус обновления
kubectl rollout status deployment/backend-api -n restaurant

# Откатить обновление при необходимости
kubectl rollout undo deployment/backend-api -n restaurant
```

## Настройка ресурсов

Ресурсы настроены для небольшого окружения. Для production:

- **Postgres**: увеличь `storage` в PVC (по умолчанию 5Gi)
- **Backend**: настрой `replicas`, `resources` в соответствии с нагрузкой
- **Frontend**: можно увеличить до 3-5 реплик

## Мониторинг

### Логи всех сервисов
```bash
# Backend API
kubectl logs -f -n restaurant deployment/backend-api

# Backend Auth
kubectl logs -f -n restaurant deployment/backend-auth

# Health Monitor
kubectl logs -f -n restaurant deployment/health-monitor

# Frontend
kubectl logs -f -n restaurant deployment/frontend

# PostgreSQL
kubectl logs -f -n restaurant statefulset/postgres

# Redis
kubectl logs -f -n restaurant deployment/redis
```

### Метрики
```bash
# Использование ресурсов подами
kubectl top pods -n restaurant

# Использование ресурсов нодами
kubectl top nodes
```

## Troubleshooting

### Поды не запускаются или в CrashLoopBackOff
```bash
# Проверить события
kubectl get events -n restaurant --sort-by='.lastTimestamp'

# Описание пода для детальной информации
kubectl describe pod <POD_NAME> -n restaurant

# Проверить логи пода
kubectl logs -n restaurant <POD_NAME> --tail=100

# Если под перезапускается, посмотри логи предыдущего запуска
kubectl logs -n restaurant <POD_NAME> --previous

# Проверить, что PostgreSQL готов
kubectl get pods -n restaurant -l app=postgres

# Дождись, пока PostgreSQL станет Ready (1/1)
# Backend поды ожидают готовности PostgreSQL через initContainers
```

### Backend поды не могут подключиться к БД
```bash
# Проверь, что PostgreSQL под запущен и готов
kubectl get pods -n restaurant -l app=postgres

# Проверь логи PostgreSQL
kubectl logs -n restaurant statefulset/postgres --tail=50

# Проверь, что сервис PostgreSQL создан
kubectl get svc postgres -n restaurant

# Проверь connectivity к PostgreSQL из другого пода
kubectl run -it --rm debug --image=postgres:16-alpine -n restaurant -- \
  psql postgresql://postgres:password@postgres:5432/restaurant -c "SELECT 1;"
```

### Проблемы с БД
```bash
# Подключиться к PostgreSQL
kubectl exec -it postgres-0 -n restaurant -- psql -U postgres -d restaurant

# Проверить таблицы
\dt
```

### Проблемы с Redis
```bash
# Подключиться к Redis
kubectl exec -it deployment/redis -n restaurant -- redis-cli

# Проверить ключи
KEYS *
```

### Проблемы с сетью
```bash
# Проверить DNS
kubectl run -it --rm debug --image=busybox -n restaurant -- nslookup backend-api

# Проверить connectivity
kubectl run -it --rm debug --image=curlimages/curl -n restaurant -- curl http://backend-api:8000/health
```

## Удаление

```bash
# Удалить все ресурсы
kubectl delete namespace restaurant

# Или удалить отдельные компоненты
kubectl delete -f k8s/
```

## Безопасность

⚠️ **ВАЖНО для production:**

1. Измени пароль PostgreSQL в Secret (`k8s/01-configmap.yaml`)
2. Используй TLS/SSL для Ingress
3. Настрой NetworkPolicies для ограничения трафика между подами
4. Используй RBAC для ограничения доступа к ресурсам
5. Храни секреты в внешних хранилищах (HashiCorp Vault, AWS Secrets Manager)

## Backup и Restore

### Backup PostgreSQL
```bash
kubectl exec postgres-0 -n restaurant -- pg_dump -U postgres restaurant > backup.sql
```

### Restore PostgreSQL
```bash
cat backup.sql | kubectl exec -i postgres-0 -n restaurant -- psql -U postgres restaurant
```

## Дополнительные возможности

### Горизонтальное автомасштабирование (HPA)
```bash
kubectl autoscale deployment backend-api -n restaurant --cpu-percent=70 --min=2 --max=10
```

### Использование Persistent Volume для логов
Добавь volume mounts в deployments для централизованного хранения логов.

### Интеграция с Prometheus/Grafana
Добавь ServiceMonitor для мониторинга метрик приложения.

## Контакты и поддержка

Для вопросов и проблем создавайте issue в репозитории проекта.

