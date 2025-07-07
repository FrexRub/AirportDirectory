```
docker compose exec app alembic upgrade head
```

```
docker compose exec app docker/add_data.sh
```

Сертификат от Let's Encrypt для домена airportcards.ru 
```
docker run -it --rm --name certbot -v "/AirportDirectory/nginx/ssl:/etc/letsencrypt" -v "/AirportDirectory/nginx/well-known:/usr/share/nginx/html" certbot/certbot certonly --webroot --agree-tos --email frex@mail.ru --webroot-path /usr/share/nginx/html/ -d airportcards.ru -d www.airportcards.ru
```

Для продления сертификата используем команду:
```
docker run -it --rm --name certbot -v "/AirportDirectory/nginx/ssl:/etc/letsencrypt" -v "/AirportDirectory/nginx/well-known:/usr/share/nginx/html" certbot/certbot renew
```

Перечитать конфигурацию nginx для проверки на ошибки
```
docker exec nginx nginx -t
```

Перегрузка nginx
```
docker exec nginx nginx -s reload
```