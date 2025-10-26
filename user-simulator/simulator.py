import asyncio
import aiohttp
import random
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserSimulator:
    def __init__(self):
        self.auth_service_url = "http://auth-service:8080"
        self.users = [
            {"username": "admin", "password": "admin123"},
            {"username": "user1", "password": "password123"},
            {"username": "user2", "password": "password456"},
            {"username": "developer", "password": "dev123"},
            {"username": "manager", "password": "mgr789"}
        ]
        self.actions = ["create_record", "update_record", "delete_record", "read_records"]
        self.record_types = ["user", "product", "order", "report", "config"]
        self.tokens = {}
    
    async def wait_for_auth_service(self, session, timeout_seconds: int = 60):
        """Очікування готовності auth-service по /health з ретраями."""
        url = f"{self.auth_service_url}/health"
        deadline = asyncio.get_event_loop().time() + timeout_seconds
        attempt = 0
        while True:
            attempt += 1
            try:
                async with session.get(url, timeout=5) as resp:
                    if resp.status == 200:
                        logger.info("✅ auth-service готовий (/health 200)")
                        return True
            except Exception as e:
                # ще не готовий — просто чекаємо
                pass
            if asyncio.get_event_loop().time() > deadline:
                logger.warning("⚠️ Очікування auth-service перевищило таймаут, продовжуємо спроби працювати")
                return False
            await asyncio.sleep(1)
    
    async def login_user(self, session, username, password, max_retries: int = 5, retry_delay: float = 1.0):
        """Авторизація користувача з ретраями."""
        url = f"{self.auth_service_url}/login"
        params = {"username": username, "password": password}
        last_status = None
        for attempt in range(1, max_retries + 1):
            try:
                async with session.post(url, params=params) as response:
                    last_status = response.status
                    if response.status == 200:
                        data = await response.json()
                        self.tokens[username] = data["access_token"]
                        logger.info(f"✅ Користувач {username} увійшов в систему")
                        return True
            except Exception as e:
                last_status = str(e)
            await asyncio.sleep(retry_delay)
        logger.warning(f"❌ Помилка входу користувача {username}: {last_status}")
        return False
    
    async def register_users(self, session, max_retries: int = 8, retry_delay: float = 1.0):
        """Реєстрація тестових користувачів (крім admin) з ретраями."""
        url = f"{self.auth_service_url}/register"
        for user in self.users[1:]:  # пропускаємо admin
            params = {
                "username": user["username"],
                "email": f"{user['username']}@example.com",
                "password": user["password"]
            }
            last_status = None
            for attempt in range(1, max_retries + 1):
                try:
                    async with session.post(url, params=params) as response:
                        last_status = response.status
                        if response.status in [200, 201]:
                            logger.info(f"✅ Користувача {user['username']} зареєстровано")
                            break
                        elif response.status == 400:
                            logger.info(f"ℹ️ Користувач {user['username']} вже існує")
                            break
                except Exception as e:
                    last_status = str(e)
                await asyncio.sleep(retry_delay)
            else:
                logger.warning(f"❌ Помилка реєстрації {user['username']}: {last_status}")
    
    async def perform_action(self, session, username, action):
        """Виконання дії користувача"""
        if username not in self.tokens:
            return False
        
        headers = {"Authorization": f"Bearer {self.tokens[username]}"}
        
        try:
            if action == "create_record":
                record_type = random.choice(self.record_types)
                title = f"{record_type.title()} #{random.randint(1000, 9999)}"
                description = f"Автоматично створений запис типу {record_type} користувачем {username}"
                url = f"{self.auth_service_url}/actions/create_record"
                params = {
                    "record_type": record_type, 
                    "title": title,
                    "description": description
                }
                async with session.post(url, headers=headers, params=params) as response:
                    success = response.status == 200
                    if success:
                        logger.info(f"📝 {username} створив запис '{title}' типу {record_type}")
                    return success
                    
            elif action == "update_record":
                url_read = f"{self.auth_service_url}/actions/read_records"
                async with session.get(url_read, headers=headers, params={"limit": 5}) as read_response:
                    if read_response.status == 200:
                        data = await read_response.json()
                        if data["records"]:
                            record = random.choice(data["records"])
                            record_id = record["id"]
                            new_title = f"Оновлений {record['title']} - {datetime.now().strftime('%H:%M:%S')}"
                            
                            url = f"{self.auth_service_url}/actions/update_record"
                            params = {
                                "record_id": record_id,
                                "title": new_title,
                                "description": f"Оновлено користувачем {username}"
                            }
                            async with session.post(url, headers=headers, params=params) as response:
                                success = response.status == 200
                                if success:
                                    logger.info(f"✏️ {username} оновив запис ID {record_id}")
                                return success
                return False
                    
            elif action == "delete_record":
                url_read = f"{self.auth_service_url}/actions/read_records"
                async with session.get(url_read, headers=headers, params={"limit": 3}) as read_response:
                    if read_response.status == 200:
                        data = await read_response.json()
                        if data["records"]:
                            record = random.choice(data["records"])
                            record_id = record["id"]
                            
                            url = f"{self.auth_service_url}/actions/delete_record"
                            params = {"record_id": record_id}
                            async with session.delete(url, headers=headers, params=params) as response:
                                success = response.status == 200
                                if success:
                                    logger.info(f"🗑️ {username} видалив запис ID {record_id}")
                                return success
                return False
                    
            elif action == "read_records":
                record_type = random.choice(self.record_types) if random.random() < 0.5 else None
                url = f"{self.auth_service_url}/actions/read_records"
                params = {"limit": random.randint(5, 15)}
                if record_type:
                    params["record_type"] = record_type
                async with session.get(url, headers=headers, params=params) as response:
                    success = response.status == 200
                    if success:
                        data = await response.json()
                        logger.info(f"📖 {username} прочитав {data['count']} записів")
                    return success
                    
        except Exception as e:
            logger.error(f"❌ Помилка виконання дії {action} користувачем {username}: {e}")
            return False
        
        return False
    
    async def simulate_user_activity(self, session):
        """Симуляція активності одного користувача"""
        user = random.choice(self.users)
        username = user["username"]
        
        if username not in self.tokens:
            await self.login_user(session, username, user["password"])
        
        action = random.choice(self.actions)
        await self.perform_action(session, username, action)
    
    async def continuous_simulation(self):
        """Безперервна симуляція активності користувачів"""
        logger.info("🚀 Запуск симулятора активності користувачів...")
        
        async with aiohttp.ClientSession() as session:
            # Дочекаємося готовності auth-service
            await self.wait_for_auth_service(session)

            # Реєстрація користувачів з ретраями
            await self.register_users(session)
            await asyncio.sleep(1)

            # Логіни з ретраями
            for user in self.users:
                await self.login_user(session, user["username"], user["password"]) 
                await asyncio.sleep(0.3)
            
            logger.info("✅ Симулятор готовий. Початок симуляції активності...")
            
            while True:
                num_actions = random.randint(1, 5)
                tasks = []
                
                for _ in range(num_actions):
                    task = self.simulate_user_activity(session)
                    tasks.append(task)
                
                await asyncio.gather(*tasks)
                
                delay = random.randint(1, 4)
                logger.info(f"⏱️ Пауза {delay} секунд до наступної хвилі активності...")
                await asyncio.sleep(delay)

async def main():
    simulator = UserSimulator()
    await simulator.continuous_simulation()

if __name__ == "__main__":
    asyncio.run(main())