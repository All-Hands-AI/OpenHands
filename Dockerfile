# Build stage
FROM node:18-alpine as builder

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY frontend/package*.json ./frontend/

# Install dependencies
RUN npm install
RUN cd frontend && npm install

# Copy source code
COPY . .

# Build frontend
RUN cd frontend && npm run build

# Production stage
FROM node:18-alpine

WORKDIR /app

# Copy built assets from builder
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/frontend/dist ./frontend/dist
COPY --from=builder /app/package*.json ./

# Install production dependencies
RUN npm ci --only=production

# Add runtime dependencies
RUN apk add --no-cache docker-cli python3 py3-pip

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install -r requirements.txt

EXPOSE 3000

CMD ["npm", "start"]
