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
    
    async def login_user(self, session, username, password):
        """Авторизація користувача та отримання токену"""
        try:
            url = f"{self.auth_service_url}/login"
            params = {"username": username, "password": password}
            
            async with session.post(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    self.tokens[username] = data["access_token"]
                    logger.info(f"✅ Користувач {username} увійшов в систему")
                    return True
                else:
                    logger.warning(f"❌ Помилка входу користувача {username}: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ Помилка при вході {username}: {e}")
            return False
    
    async def register_users(self, session):
        """Реєстрація тестових користувачів"""
        for user in self.users[1:]: 
            try:
                url = f"{self.auth_service_url}/register"
                data = {
                    "username": user["username"],
                    "email": f"{user['username']}@example.com",
                    "password": user["password"]
                }
                
                async with session.post(url, json=data) as response:
                    if response.status in [200, 201]:
                        logger.info(f"✅ Користувача {user['username']} зареєстровано")
                    elif response.status == 400:
                        logger.info(f"ℹ️ Користувач {user['username']} вже існує")
                    else:
                        logger.warning(f"❌ Помилка реєстрації {user['username']}: {response.status}")
            except Exception as e:
                logger.error(f"❌ Помилка реєстрації {user['username']}: {e}")
    
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
            await self.register_users(session)
            await asyncio.sleep(2)
            
            for user in self.users:
                await self.login_user(session, user["username"], user["password"])
                await asyncio.sleep(0.5)
            
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