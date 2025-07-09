FROM --platform=linux/amd64 node:20-bullseye AS builder

# Устанавливаем рабочий каталог контейнера
WORKDIR /usr/src/app

# Позволяет запускать vite и другие инструменты напрямую
ENV PATH /app/node_modules/.bin:$PATH
ENV NODE_OPTIONS=--trace-deprecation

# Внедряем все переменные окружения, которые нам понадобятся
ARG VITE_AUTH_URL
ARG VITE_LOGGING

# Предоставлем переменную готовому контейнеру
ENV VITE_AUTH_URL=$VITE_AUTH_URL
ENV VITE_LOGGING=$VITE_LOGGING

# Копируем файлы пакетов в контейнер и устанавливаем их
COPY app/package.json ./
RUN npm install

# Копируем все файлы фронтенда
COPY app ./

FROM builder AS dev
CMD ["npm", "run", "dev", "--", "--host"]

FROM builder AS prod-builder
RUN npm run build

FROM nginx:latest AS prod

RUN apt update && apt install -y certbot python3-certbot-nginx
RUN mkdir -p /var/www/certbot

COPY --from=prod-builder /usr/src/app/dist /usr/share/nginx/html

CMD ["nginx", "-g", "daemon off;"]