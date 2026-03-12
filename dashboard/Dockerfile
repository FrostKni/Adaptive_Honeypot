FROM nginx:alpine

# Copy dashboard files
COPY index.html /usr/share/nginx/html/

# Expose port
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
