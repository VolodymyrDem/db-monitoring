# 📊 Database Monitoring System

Система моніторингу бази даних з використанням Prometheus та Grafana для відстеження активності користувачів та навантаження на БД.

## 🚀 Швидкий старт

### Запуск системи
```bash
# Клонувати репозиторій
git clone <repository-url>
cd db-monitoring

# 🔄 Чистий запуск з обнуленням метрик (рекомендовано)
.\start-fresh.ps1

# 🚀 Або через Docker
docker-compose down -v && docker-compose up -d --build

# 📊 Перевірити статус
.\status.ps1
```

### 📋 Доступні скрипти

```powershell
.\start-fresh.ps1     # Чистий запуск з обнуленням всіх метрик
.\start-monitoring.ps1 # Звичайний запуск (зберігає дані)
.\status.ps1          # Статус системи та статистика
.\stop-monitoring.ps1 # Зупинка системи
```

### Доступ до сервісів
- **Grafana Dashboard**: http://localhost:3000 (admin/admin123)
- **Prometheus**: http://localhost:9090
- **Auth Service API**: http://localhost:8080
- **MySQL**: localhost:3307 (root/rootpassword)

## 📊 Що моніторимо

### 1. Реальні дії користувачів з MySQL
- **Створення** записів в таблиці `records` (CREATE)
- **Читання** записів з реальними даними (READ) 
- **Оновлення** існуючих записів (UPDATE)
- **Видалення** записів з бази даних (DELETE)

### 2. Аутентифікація користувачів
- **Успішні входи** в систему з JWT токенами
- **Помилки входу** (невірні паролі, неіснуючі користувачі)

### 3. MySQL база даних
- **Реальні SQL запити** до БД (696+ запитів)
- **Статус підключення** до MySQL сервера
- **Актуальна кількість записів** в таблицях

## 🏗️ Архітектура

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│             │    │             │    │             │
│ Auth        │───▶│ Prometheus  │───▶│ Grafana     │
│ Service     │    │             │    │ Dashboard   │
│             │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘
       │                                      ▲
       │                                      │
       ▼                                      │
┌─────────────┐                              │
│             │                              │
│ MySQL       │                              │
│ Database    │                              │
│             │                              │
└─────────────┘                              │
       ▲                                      │
       │                                      │
       └──────────────────────────────────────┘
```

### Компоненти

1. **Auth Service** - FastAPI додаток з метриками Prometheus
2. **MySQL** - База даних для зберігання користувачів
3. **Prometheus** - Збір та зберігання метрик
4. **Grafana** - Візуалізація дашбордів
5. **User Simulator** - Виконання реальних CRUD операцій з MySQL

## 💾 Реальні дані в MySQL

Система працює з реальною базою даних MySQL:

```sql
-- База даних: monitoring_db
-- Таблиці:
-- ├── users (id, username, password_hash, created_at, is_active)
-- └── records (id, title, record_type, description, created_by, created_at, updated_at, is_active)

-- Поточний стан системи:
SELECT COUNT(*) FROM records;  -- 43+ активних записів
SELECT COUNT(*) FROM users;    -- 5 користувачів (admin, user1, user2, developer, manager)
```

## 📈 Дашборд "Моніторинг системи"

Автоматично створюється дашборд з такими панелями:

### 🔢 Цифровий показник
- **Загальна кількість дій користувачів** - сума всіх реальних CRUD операцій

### 📊 Графіки
- **Дії користувачів по типам** - 4 лінії (створити, видалити, прочитати, оновити)
- **Спроби входу** - успішні vs помилки
- **Запити до БД** - загальне навантаження на базу даних

## � Поточні результати моніторингу

Система активно працює і збирає реальні метрики:

### 📈 Статистика операцій
- **Загальна кількість SQL запитів**: 696+
- **Створено записів**: 41
- **Видалено записів**: 34  
- **Поточних записів в БД**: 43
- **Операцій читання**: 129+
- **Операцій оновлення**: 46+

### 🔄 Активність користувачів
- **admin**: 10 створень, 38 читань, 14 оновлень, 8 видалень
- **user1**: 14 створень, 30 читань, 8 оновлень, 9 видалень  
- **user2**: 9 створень, 35 читань, 16 оновлень, 6 видалень
- **developer**: 6 створень, 26 читань, 8 оновлень, 6 видалень

## �🛠️ Технології

- **Backend**: Python, FastAPI
- **Database**: MySQL 8.0 з реальними таблицями
- **Monitoring**: Prometheus, Grafana
- **Metrics**: prometheus_client для збору метрик
- **Containerization**: Docker, Docker Compose
- **Authentication**: JWT tokens з bcrypt hashing
- **ORM**: SQLAlchemy з PyMySQL драйвером

## 👥 Тестові користувачі

Система автоматично створює тестових користувачів:

| Користувач | Пароль | Роль |
|------------|--------|------|
| admin | admin123 | Адміністратор |
| user1 | password123 | Користувач |
| user2 | password456 | Користувач |
| developer | dev123 | Користувач |

## 🔗 API Endpoints

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

## 📊 Prometheus метрики

| Метрика | Опис |
|---------|------|
| `user_actions_total` | Кількість дій користувачів за типами |
| `auth_login_attempts_total` | Спроби входу (успішні/помилкові) |
| `db_queries_total` | Загальна кількість запитів до БД |
| `mysql_connection_status_total` | Статус підключення до MySQL |

## 🧹 Корисні команди

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

## 🔧 Налаштування

### Prometheus
Конфігурація в `config/prometheus/prometheus.yml`:
- Збирає метрики кожні 15 секунд
- Моніторить auth-service на порту 8080

### Grafana
- Автоматично налаштований datasource для Prometheus
- Дашборд автоматично завантажується при старті
- Доступ: admin/admin123

### MySQL
- Порт: 3307 (щоб не конфліктувати з локальним MySQL)
- База даних: monitoring_db
- Користувач: dbuser/dbpassword

## 📚 Структура проекту

```
db-monitoring/
├── auth-service/          # FastAPI додаток з метриками
│   ├── app.py            # Основний код сервісу
│   ├── Dockerfile        # Docker образ
│   └── requirements.txt  # Python залежності
├── config/
│   ├── grafana/          # Конфігурація Grafana
│   │   └── provisioning/ # Автоматичні дашборди
│   ├── mysql/            # Конфігурація MySQL
│   └── prometheus/       # Конфігурація Prometheus
├── user-simulator/       # Симулятор активності
├── sql-scripts/          # SQL скрипти ініціалізації
├── docker-compose.yml    # Оркестрація сервісів
└── README.md            # Ця документація
```

## 🚨 Troubleshooting

### Сервіси не запускаються
```bash
# Перевірити статус
docker-compose ps

# Переглянути логи
docker-compose logs

# Перезапустити
docker-compose restart
```

### Grafana показує "No data"
1. Перевірте чи працює Prometheus: http://localhost:9090
2. Перевірте чи збираються метрики: http://localhost:8080/metrics
3. Перезапустіть Grafana: `docker-compose restart grafana`

### MySQL підключення
```bash
# Підключитися до MySQL
docker exec -it mysql_db mysql -uroot -prootpassword monitoring_db

# Перевірити таблиці
SHOW TABLES;
SELECT * FROM users;
```

## 📝 Ліцензія

Цей проект створений для навчальних цілей.