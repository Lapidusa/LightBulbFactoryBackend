# LightBulb Factory Backend

Backend интернет-магазина завода лампочек на FastAPI, PostgreSQL и Docker Compose. Архитектура разнесена на три отдельных микросервиса.

## Структура

```text
services/
  product_service/
    Dockerfile
    main.py
    models.py
    schemas.py
  order_service/
    Dockerfile
    main.py
    models.py
    schemas.py
  admin_service/
    Dockerfile
    main.py
    models.py
    schemas.py
shared/
docker-compose.yml
pyproject.toml
```

## Сервисы

- Product Service: каталог, категории, карточки товаров, изображения и остатки.
- Order Service: создание заказов, позиции заказа, статусы и история статусов.
- Admin Service: авторизация администратора, сессии, dashboard и маршрутизация admin API.

У каждого сервиса свой FastAPI app, свой Dockerfile и свой PostgreSQL:

- `product_service` -> `product_db`
- `order_service` -> `order_db`
- `admin_service` -> `admin_db`

Order Service не читает БД каталога напрямую. При создании заказа он обращается в Product Service по HTTP и сохраняет snapshot товара. Admin Service не ходит напрямую в таблицы товаров и заказов, а проксирует admin-запросы в Product/Order Service по HTTP с внутренним токеном.

## Запуск

```powershell
docker compose up --build
```

Swagger:

- Product Service: http://127.0.0.1:18001/docs
- Order Service: http://127.0.0.1:18002/docs
- Admin Service: http://127.0.0.1:18003/docs

PostgreSQL снаружи доступен на портах:

- Product DB: `localhost:15433`
- Order DB: `localhost:15434`
- Admin DB: `localhost:15435`

## Доступ администратора

```text
login: admin
password: admin123
```

## Основные endpoint

Product Service, внешний порт `18001`, внутренний порт `8001`:

- `GET /api/v1/categories`
- `GET /api/v1/products`
- `GET /api/v1/products/{product_id}`

Order Service, внешний порт `18002`, внутренний порт `8002`:

- `POST /api/v1/orders`
- `GET /api/v1/orders/{order_number}`

Admin Service, внешний порт `18003`, внутренний порт `8003`:

- `POST /api/v1/admin/auth/login`
- `POST /api/v1/admin/auth/logout`
- `POST /api/v1/admin/auth/refresh`
- `GET /api/v1/admin/me`
- `GET /api/v1/admin/dashboard/summary`
- `GET /api/v1/admin/products`
- `POST /api/v1/admin/products`
- `PUT /api/v1/admin/products/{product_id}`
- `PATCH /api/v1/admin/products/{product_id}`
- `DELETE /api/v1/admin/products/{product_id}`
- `PATCH /api/v1/admin/products/{product_id}/status`
- `POST /api/v1/admin/products/{product_id}/images`
- `GET /api/v1/admin/orders`
- `GET /api/v1/admin/orders/{order_id}`
- `PATCH /api/v1/admin/orders/{order_id}/status`
- `PATCH /api/v1/admin/orders/{order_id}/comment`

Для admin endpoint нужен заголовок:

```text
Authorization: Bearer <access_token>
```

## Формат ответов

Успех:

```json
{
  "success": true,
  "data": {},
  "meta": {}
}
```

Ошибка:

```json
{
  "success": false,
  "error": {
    "code": "validation_error",
    "message": "Request validation failed",
    "details": []
  }
}
```

## Postman

Коллекция: [postman/lightbulb_factory_backend.postman_collection.json](postman/lightbulb_factory_backend.postman_collection.json).

Переменные:

- `productUrl`: `http://127.0.0.1:18001`
- `orderUrl`: `http://127.0.0.1:18002`
- `adminUrl`: `http://127.0.0.1:18003`
- `authToken`: токен из `POST /api/v1/admin/auth/login`
- `productId`: id товара из Product Service
- `orderId`: id заказа из Admin Service
- `orderNumber`: номер созданного заказа
