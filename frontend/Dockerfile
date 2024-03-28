FROM node:20.10.0

COPY package.json .

RUN npm install
WORKDIR /app
CMD ["npm", "start","--", "--port", "3001"]

