TODO


Накатить миграции
```
docker compose exec app alembic upgrade head
```

Добавить данные в базу данных
```
docker compose exec app docker/add_data.sh
```

Перечитать конфигурацию nginx для проверки на ошибки
```
docker exec nginx nginx -t
```

Перегрузка nginx
```
docker exec nginx nginx -s reload
```