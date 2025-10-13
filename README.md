# Database Monitoring System

Система моніторингу бази даних з використанням Prometheus та Grafana для відстеження активності користувачів та навантаження на БД.

## Швидкий старт

### Запуск системи
```bash
docker-compose down -v && docker-compose up -d --build
```

### Доступ до сервісів
- **Grafana Dashboard**: http://localhost:3000 (admin/admin123)
- **Prometheus**: http://localhost:9090
- **Auth Service**: http://localhost:8080
- **MySQL**: localhost:3307 (root/rootpassword)

### Компоненти
1. **Auth Service** - FastAPI додаток з метриками Prometheus
2. **MySQL** - База даних для зберігання користувачів
3. **Prometheus** - Збір та зберігання метрик
4. **Grafana** - Візуалізація дашбордів
5. **User Simulator** - Виконання реальних CRUD операцій з MySQL

### Аутентифікація
- `POST /login` - Вхід в систему
- `POST /register` - Реєстрація користувача
- `GET /verify` - Перевірка токену

### CRUD операції (потрібен JWT токен)
- `POST /actions/create_record` - Створити запис
- `GET /actions/read_records` - Читати записи
- `POST /actions/update_record` - Оновити запис
- `DELETE /actions/delete_record` - Видалити запис

### Моніторинг
- `GET /metrics` - Prometheus метрики
- `GET /health` - Health check

## Команди

### Повне очищення системи
```bash
# Зупинити та видалити все (включно з даними)
docker-compose down -v

# Видалити образи
docker rmi db-monitoring-auth-service db-monitoring-user-simulator -f

# Запустити заново
docker-compose build
docker-compose up -d
```

### Перегляд логів
```bash
# Логи всіх сервісів
docker-compose logs -f

# Логи конкретного сервіса
docker-compose logs -f auth-service
docker-compose logs -f user-simulator
docker-compose logs -f grafna
docker-compose logs -f mysql_db
docker-compose logs -f prometheus

```

### Перевірка метрик
```bash
# Метрики auth-service
curl http://localhost:8080/metrics

# Статус Prometheus
curl http://localhost:9090/-/healthy

# Статус Grafana
curl http://localhost:3000/api/health
```