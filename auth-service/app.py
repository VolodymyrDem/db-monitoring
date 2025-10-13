from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt
import os
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import time

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://dbuser:dbpassword@mysql:3306/monitoring_db")
JWT_SECRET = os.getenv("JWT_SECRET", "your_jwt_secret_key_here")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

app = FastAPI(title="Auth Service", description="Сервіс авторизації для системи моніторингу")

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

class Record(Base):
    __tablename__ = "records"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    record_type = Column(String(50), nullable=False) 
    description = Column(String(500))
    created_by = Column(String(50), nullable=False) 
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

Base.metadata.create_all(bind=engine)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

security = HTTPBearer()

login_attempts = Counter("auth_login_attempts_total", "Загальна кількість спроб входу", ["status"])
user_actions = Counter("user_actions_total", "Загальна кількість дій користувачів", ["action", "user"])
db_queries_total = Counter("db_queries_total", "Загальна кількість запитів до бази даних")
mysql_connection_status = Counter("mysql_connection_status_total", "Статус підключення до MySQL", ["status"])
request_duration = Histogram("auth_request_duration_seconds", "Тривалість обробки запитів")

def get_db():
    db = SessionLocal()
    db_queries_total.inc()
    try:
        db.execute(text("SELECT 1"))
        mysql_connection_status.labels(status="success").inc()
        yield db
    except Exception as e:
        mysql_connection_status.labels(status="failed").inc()
        raise e
    finally:
        db.close()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Невалідний токен")
        return username
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Невалідний токен")

@app.post("/register")
async def register(username: str, email: str, password: str, db: Session = Depends(get_db)):
    start_time = time.time()
    
    existing_user = db.query(User).filter((User.username == username) | (User.email == email)).first()
    if existing_user:
        request_duration.observe(time.time() - start_time)
        raise HTTPException(status_code=400, detail="Користувач з таким логіном або email вже існує")
    
    hashed_password = get_password_hash(password)
    user = User(username=username, email=email, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    
    request_duration.observe(time.time() - start_time)
    return {"message": "Користувач успішно зареєстрований", "user_id": user.id}

@app.post("/login")
async def login(username: str, password: str, db: Session = Depends(get_db)):
    start_time = time.time()
    db_queries_total.inc()
    
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        login_attempts.labels(status="failed").inc()
        request_duration.observe(time.time() - start_time)
        raise HTTPException(status_code=401, detail="Невірний логін або пароль")
    
    if not user.is_active:
        login_attempts.labels(status="inactive").inc()
        request_duration.observe(time.time() - start_time)
        raise HTTPException(status_code=401, detail="Акаунт деактивований")
    
    user.last_login = datetime.utcnow()
    db.commit()
    db_queries_total.inc()  
    
    access_token = create_access_token(data={"sub": user.username, "is_admin": user.is_admin})
    
    login_attempts.labels(status="success").inc()
    request_duration.observe(time.time() - start_time)
    
    return {"access_token": access_token, "token_type": "bearer", "is_admin": user.is_admin}

@app.get("/verify")
async def verify(username: str = Depends(verify_token), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Користувач не знайдений або деактивований")
    
    return {"username": user.username, "is_admin": user.is_admin, "email": user.email}

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/actions/create_record")
async def create_record(record_type: str, title: str, description: str = "", current_user: str = Depends(verify_token), db: Session = Depends(get_db)):
    """Створення реального запису в БД MySQL"""
    db_queries_total.inc() 
    
    new_record = Record(
        title=title,
        record_type=record_type,
        description=description,
        created_by=current_user
    )
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    db_queries_total.inc()
    
    user_actions.labels(action="create", user=current_user).inc()
    return {
        "message": f"Запис типу {record_type} створено", 
        "user": current_user,
        "record_id": new_record.id,
        "title": new_record.title
    }

@app.post("/actions/update_record")
async def update_record(record_id: int, title: str = None, description: str = None, current_user: str = Depends(verify_token), db: Session = Depends(get_db)):
    """Оновлення реального запису в БД MySQL"""
    db_queries_total.inc()
    
    record = db.query(Record).filter(Record.id == record_id, Record.is_active == True).first()
    if not record:
        raise HTTPException(status_code=404, detail="Запис не знайдено")
    
    if title:
        record.title = title
    if description:
        record.description = description
    record.updated_at = datetime.utcnow()
    
    db.commit()
    db_queries_total.inc()
    
    user_actions.labels(action="update", user=current_user).inc()
    return {
        "message": f"Запис ID {record_id} оновлено", 
        "user": current_user,
        "record_id": record.id,
        "title": record.title
    }

@app.delete("/actions/delete_record")
async def delete_record(record_id: int, current_user: str = Depends(verify_token), db: Session = Depends(get_db)):
    """Видалення реального запису з БД MySQL (soft delete)"""
    db_queries_total.inc() 
    
    record = db.query(Record).filter(Record.id == record_id, Record.is_active == True).first()
    if not record:
        raise HTTPException(status_code=404, detail="Запис не знайдено")
    
    record.is_active = False
    record.updated_at = datetime.utcnow()
    
    db.commit()
    db_queries_total.inc()
    
    user_actions.labels(action="delete", user=current_user).inc()
    return {
        "message": f"Запис ID {record_id} видалено", 
        "user": current_user,
        "record_id": record.id
    }

@app.get("/actions/read_records")
async def read_records(record_type: str = None, limit: int = 10, current_user: str = Depends(verify_token), db: Session = Depends(get_db)):
    """Читання реальних записів з БД MySQL"""
    db_queries_total.inc()
    
    query = db.query(Record).filter(Record.is_active == True)
    if record_type:
        query = query.filter(Record.record_type == record_type)
    
    records = query.limit(limit).all()
    
    user_actions.labels(action="read", user=current_user).inc()
    return {
        "message": "Записи прочитано", 
        "user": current_user, 
        "count": len(records),
        "records": [
            {
                "id": r.id,
                "title": r.title,
                "record_type": r.record_type,
                "created_by": r.created_by,
                "created_at": r.created_at.isoformat() if r.created_at else None
            } for r in records
        ]
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "auth-service"}

@app.get("/mysql/status")  
async def mysql_status():
    """Перевіряє статус підключення до MySQL"""
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        mysql_connection_status.labels(status="up").inc()
        return {"mysql_status": "up", "connection": "healthy"}
    except Exception as e:
        mysql_connection_status.labels(status="down").inc()
        return {"mysql_status": "down", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    db = SessionLocal()
    admin_user = db.query(User).filter(User.username == "admin").first()
    if not admin_user:
        admin_user = User(
            username="admin",
            email="admin@monitoring.local",
            hashed_password=get_password_hash("admin123"),
            is_admin=True
        )
        db.add(admin_user)
        db.commit()
        print("Створено адміністратора: admin/admin123")
    
    test_users = [
        {"username": "user1", "email": "user1@example.com", "password": "password123"},
        {"username": "user2", "email": "user2@example.com", "password": "password456"},
        {"username": "developer", "email": "developer@example.com", "password": "dev123"},
    ]
    
    for user_data in test_users:
        existing_user = db.query(User).filter(User.username == user_data["username"]).first()
        if not existing_user:
            test_user = User(
                username=user_data["username"],
                email=user_data["email"],
                hashed_password=get_password_hash(user_data["password"]),
                is_admin=False
            )
            db.add(test_user)
            db.commit()
            print(f"Створено користувача: {user_data['username']}/{user_data['password']}")
    
    db.close()
    
    uvicorn.run(app, host="0.0.0.0", port=8080)