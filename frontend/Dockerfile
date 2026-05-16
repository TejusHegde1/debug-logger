# Stage 1: Copy static assets (no build step needed for plain HTML/JS)
FROM node:20-alpine AS builder
WORKDIR /build
COPY src/ .

# Stage 2: Serve with Nginx
FROM nginx:alpine
COPY --from=builder /build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
