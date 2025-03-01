FROM nginx:alpine

# Remove default nginx config and copy custom config
RUN rm /etc/nginx/conf.d/default.conf
COPY ./nginx/default.conf /etc/nginx/conf.d/

# Expose HTTP and HTTPS ports
EXPOSE 80 443
