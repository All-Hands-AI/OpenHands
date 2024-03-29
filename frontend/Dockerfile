# Stage 1: Build the Vue app
FROM node:21-alpine as build

WORKDIR /app

COPY . .

RUN npm ci
RUN npm run build

# Stage 2: Serve the built app using Nginx
FROM nginx:alpine as runetime

COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
