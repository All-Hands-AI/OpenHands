FROM node:21-alpine3.18

ENV BACKEND_HOST=localhost
ENV FRONTEND_PORT=3001

WORKDIR /usr/src/app

COPY package*.json .
RUN corepack enable && pnpm install && pnpm run make-i18n
COPY . .

EXPOSE 3001

CMD ["pnpm", "run", "start"]
