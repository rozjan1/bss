# Use a lightweight web server to serve static files
FROM nginx:stable-alpine

# Remove default nginx website
RUN rm -rf /usr/share/nginx/html/*

# Copy frontend files
COPY . /usr/share/nginx/html

# Expose port
EXPOSE 80

# Run nginx in foreground
CMD ["nginx", "-g", "daemon off;"]
