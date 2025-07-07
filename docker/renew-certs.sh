#!/bin/bash

# Обновляем сертификаты
certbot renew --webroot -w /usr/share/nginx/html

# Копируем обновленные сертификаты (без симлинков)
cp -L /etc/letsencrypt/live/airportcards.ru/fullchain.pem /etc/nginx/ssl/
cp -L /etc/letsencrypt/live/airportcards.ru/privkey.pem /etc/nginx/ssl/

# Перезагружаем Nginx
nginx -s reload
