FROM nginx:alpine

# Copy static site into nginx html dir
COPY . /usr/share/nginx/html/

# Ensure permissions (nginx user serves files)
RUN chown -R nginx:nginx /usr/share/nginx/html || true

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
