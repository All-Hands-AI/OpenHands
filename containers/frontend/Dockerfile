FROM node:21.7.2-bookworm-slim AS builder

WORKDIR /app

COPY ./frontend/package.json ./frontend/package-lock.json ./
RUN npm install -g npm@10.5.1
RUN npm ci

COPY ./frontend ./
RUN npm run build

FROM nginx:1.25-alpine

# Copy nginx configuration
COPY ./containers/frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Copy built frontend files
COPY --from=builder /app/build /usr/share/nginx/html

# Add health check
HEALTHCHECK --interval=30s --timeout=3s CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
