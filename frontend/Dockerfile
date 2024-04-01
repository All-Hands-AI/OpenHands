FROM node:20.10.0

WORKDIR /app

COPY package.json  /app
COPY package-lock.json /app

RUN npm install npm@latest -g && npm install

CMD ["npm", "start","--", "--port", "3001"]