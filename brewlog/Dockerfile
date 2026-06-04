FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:1.27-alpine
ENV PORT=80
ENV BACKEND_URL=http://127.0.0.1:8000
ENV NGINX_ENVSUBST_FILTER="^(PORT|BACKEND_URL)$"
COPY nginx.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html
