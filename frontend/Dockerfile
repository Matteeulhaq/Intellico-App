# Build stage
FROM node:20-alpine AS build
WORKDIR /app

# Copy only package files first for efficient caching
COPY my-app/package*.json ./
RUN npm ci

# Copy all app source
COPY my-app ./

# Environment variable for API URL
ARG REACT_APP_API_URL
ENV REACT_APP_API_URL=$REACT_APP_API_URL

# Build the Vite project
RUN npm run build

# Production stage
FROM nginx:stable-alpine
# Copy the built assets from the Vite build output
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
