FROM nginx:1.21-alpine

RUN rm /etc/nginx/conf.d/default.conf
RUN mkdir -pv /var/{log,run}/gunicorn/
COPY nginx.conf /etc/nginx/conf.d
