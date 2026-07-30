# Build Stage
FROM node:20-alpine AS build

WORKDIR /app

# Accept build argument for Vite API base URL
ARG VITE_API_BASE_URL=http://localhost:5000/api/v1
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# Install dependencies first for efficient docker layer caching
COPY package*.json ./
RUN npm ci

# Copy source files and build production distribution bundle
COPY . .
RUN npm run build

# Production Nginx Stage
FROM nginx:alpine

# Copy built distribution files to Nginx web root
COPY --from=build /app/dist /usr/share/nginx/html

# Expose HTTP port 80
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
