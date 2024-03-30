FROM node:21-alpine as build

WORKDIR /app

COPY package*.json ./

RUN npm ci
RUN npm install

COPY . .

RUN npm run build

FROM nginx:alpine as runetime

COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
