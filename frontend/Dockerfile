# Используем минимальный образ nginx
FROM nginx:alpine

# Копируем кастомную конфигурацию nginx
COPY nginx.conf /etc/nginx/nginx.conf

# Копируем весь фронтенд (HTML, JS, CSS и т.п.)
COPY . /usr/share/nginx/html

# Открываем порт 80 для HTTP
EXPOSE 80

# Запускаем nginx в foreground-режиме (контейнер не завершается)
CMD ["nginx", "-g", "daemon off;"]