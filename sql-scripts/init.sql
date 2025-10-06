-- Ініціалізація бази даних для моніторингу
-- Створення користувача для експортера метрик

CREATE USER IF NOT EXISTS 'exporter'@'%' IDENTIFIED BY 'exporter_password';
GRANT PROCESS, REPLICATION CLIENT, SELECT ON *.* TO 'exporter'@'%';
FLUSH PRIVILEGES;

-- Створення індексів для оптимізації запитів
USE monitoring_db;

-- Налаштування для кращого моніторингу
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 2;
SET GLOBAL general_log = 'ON';

-- Інформація про налаштування
SELECT 
    'Database initialized for monitoring' as Status,
    NOW() as Timestamp;

-- Показати поточні налаштування
SHOW VARIABLES LIKE '%log%';
SHOW VARIABLES LIKE '%performance_schema%';