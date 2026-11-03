import os
import logging
import secrets
import time
from collections import deque
from fastapi import Request
from fastapi.responses import JSONResponse
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# ==================== НАСТРОЙКА ====================

# Настройка логирования для отслеживания процессов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения из файла .env
load_dotenv()

# Получение API ключа из переменных окружения
HUGGING_FACE_API_KEY = os.getenv("HUGGING_FACE_API_KEY")
if not HUGGING_FACE_API_KEY:
    raise ValueError("HUGGING_FACE_API_KEY не найден в переменных окружения!")

# Модель для чата - используем meta-llama (оригинальный выбор)
MODEL_NAME = "meta-llama/Llama-3.1-8B-Instruct"
# Endpoint роутера - OpenAI-совместимый API для chat completions
API_URL = "https://router.huggingface.co/v1/chat/completions"

# ==================== НАСТРОЙКА ПРИЛОЖЕНИЯ ====================

# Создание экземпляра FastAPI приложения
app = FastAPI()

# Для локального использования ключ необязателен. Для публичного запуска задайте его.
API_ACCESS_KEY = os.getenv("API_ACCESS_KEY", "")
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "10"))
RATE_LIMIT_WINDOW = 60
MAX_RATE_LIMIT_CLIENTS = 10000
if RATE_LIMIT_REQUESTS < 1:
    raise ValueError("RATE_LIMIT_REQUESTS должен быть положительным")
request_windows: dict[str, deque] = {}


@app.middleware("http")
async def protect_inference(request: Request, call_next):
    if (request.method, request.url.path) not in {("POST", "/chat"), ("GET", "/test-api")}:
        return await call_next(request)
    if API_ACCESS_KEY and not secrets.compare_digest(
        request.headers.get("Authorization", "").encode(),
        ("Bearer " + API_ACCESS_KEY).encode(),
    ):
        return JSONResponse(status_code=401, content={"detail": {"code": "unauthorized", "message": "Нужен ключ доступа к чату."}}, headers={"WWW-Authenticate": "Bearer"})
    now = time.monotonic()
    # Не доверяем X-Forwarded-For: прокси настраивается отдельно на уровне ASGI-сервера.
    client = request.client.host if request.client else "unknown"
    for host in list(request_windows):
        window = request_windows[host]
        while window and window[0] <= now - RATE_LIMIT_WINDOW:
            window.popleft()
        if not window:
            del request_windows[host]
    if client not in request_windows:
        if len(request_windows) >= MAX_RATE_LIMIT_CLIENTS:
            return JSONResponse(status_code=503, content={"detail": {"code": "limiter_capacity", "message": "Сервис занят. Попробуйте позже."}})
        request_windows[client] = deque()
    window = request_windows[client]
    if len(window) >= RATE_LIMIT_REQUESTS:
        retry_after = max(1, int(RATE_LIMIT_WINDOW - (now - window[0])) + 1)
        return JSONResponse(status_code=429, content={"detail": {"code": "rate_limited", "message": "Слишком много запросов. Попробуйте позже."}}, headers={"Retry-After": str(retry_after)})
    window.append(now)
    return await call_next(request)


# Подключение статических файлов (HTML, CSS, JavaScript)
app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static",
)

# ==================== МОДЕЛИ ДАННЫХ ====================

class ChatRequest(BaseModel):
    """Модель для входящего запроса чата"""
    message: str


class ChatResponse(BaseModel):
    """Модель для исходящего ответа чата"""
    response: str


# ==================== ФУНКЦИЯ LLM ====================

async def call_llm(user_message: str) -> str:
    """
    Генерация ответа с использованием Hugging Face Inference API.

    Args:
        user_message: Входящее сообщение пользователя

    Returns:
        Сгенерированный ответ LLM

    Raises:
        ValueError: Для ошибок, отображаемых пользователю (показываются в чате)
    """
    logger.info(f"Генерация ответа для: {user_message[:50]}...")

    headers = {
        "Authorization": f"Bearer {HUGGING_FACE_API_KEY}",
        "Content-Type": "application/json",
    }

    # Формат, совместимый с OpenAI
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": user_message}
        ],
        "max_tokens": 500,
        "temperature": 0.7,
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            logger.info(f"Calling Hugging Face API at {API_URL}")
            response = await client.post(API_URL, headers=headers, json=payload)

            logger.info(f"Response status: {response.status_code}")

            if response.status_code == 503:
                logger.warning("Model is loading")
                raise ValueError(
                    "⏳ The model is loading (can take 20-60 seconds on first use). "
                    "Please try again in a moment!"
                )

            if response.status_code == 403:
                logger.error("Access forbidden")
                raise ValueError(
                    f"Access denied. You may need to accept the model license at "
                    f"https://huggingface.co/{MODEL_NAME}"
                )

            if response.status_code == 401:
                logger.error("Authentication failed")
                raise ValueError("Invalid or missing Hugging Face API token")

            if response.status_code != 200:
                error_text = response.text
                logger.error(f"API error: Status={response.status_code}, Body={error_text}")
                logger.error(f"Request URL: {API_URL}")
                logger.error(f"Request headers: {headers}")
                logger.error(f"Request payload: {payload}")
                raise ValueError(f"API error ({response.status_code}): {error_text}")

            result = response.json()
            logger.info(f"Исходный ответ: {result}")

            # Парсинг ответа в OpenAI-совместимом формате
            # Структура ответа: {"choices": [{"message": {"content": "..."}}]}
            if "choices" in result and len(result["choices"]) > 0:
                generated_text = result["choices"][0]["message"]["content"]
            else:
                # Запасной вариант для неожиданного формата
                logger.warning(f"Неожиданный формат ответа: {result}")
                generated_text = str(result)

            logger.info("Ответ успешно сгенерирован")
            return generated_text.strip()

    except httpx.TimeoutException:
        logger.error("Превышено время ожидания запроса")
        raise ValueError("Превышено время ожидания запроса. Модель может загружаться. Попробуйте снова.")

    except ValueError:
        # Повторный вброс ValueError (наши пользовательские ошибки)
        raise

    except Exception as e:
        import traceback
        logger.error(f"Неожиданная ошибка: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise ValueError(f"Произошла неожиданная ошибка: {str(e)}")


# ==================== ЭНДПОИНТЫ ====================

@app.get("/")
def read_root():
    """Отдача UI интерфейса чата"""
    return FileResponse("static/index.html")


@app.get("/hello")
def hello():
    """Тестовый эндпоинт для проверки работы сервера"""
    return {"message": "Hello, World!"}


@app.get("/test-api")
async def test_api():
    """
    Тестовый эндпоинт для проверки соединения с Hugging Face.
    Посетите: http://localhost:8000/test-api

    Это полезно для отладки - он точно покажет, что не так!
    """
    try:
        result = await call_llm("Say hello!")
        return {"success": True, "response": result}
    except ValueError as e:
        return {"success": False, "error": str(e)}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Эндпоинт чата — принимает сообщения пользователя и возвращает ответы LLM.
    """
    try:
        llm_response = await call_llm(request.message)
        return ChatResponse(response=llm_response)

    except ValueError as e:
        # Возврат понятного пользователю сообщения об ошибке в чат
        return ChatResponse(response=str(e))

    except Exception as e:
        logger.error(f"Неожиданная ошибка в эндпоинте чата: {e}")
        return ChatResponse(response="Произошла неожиданная ошибка. Попробуйте снова.")
