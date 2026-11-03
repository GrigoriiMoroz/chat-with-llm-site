import os
import logging
import httpx
from pydantic import Field, field_validator, model_validator
from typing import Literal
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
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

# Подключение статических файлов (HTML, CSS, JavaScript)
app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static",
)

# ==================== МОДЕЛИ ДАННЫХ ====================

class HistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)

    @field_validator("content", mode="before")
    @classmethod
    def nonblank(cls, value):
        if isinstance(value, str):
            value = value.strip()
        return value


class ConversationContext(BaseModel):
    history: list[HistoryMessage] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def validate_history(self):
        if len(self.history) % 2:
            raise ValueError("History must contain complete exchanges")
        for index, message in enumerate(self.history):
            if message.role != ("user" if index % 2 == 0 else "assistant"):
                raise ValueError("History roles must alternate")
        if sum(len(m.content) for m in self.history) > 16000:
            raise ValueError("History is too long")
        return self


class ChatRequest(ConversationContext):
    """Модель для входящего запроса чата"""
    message: str


class ChatResponse(BaseModel):
    """Модель для исходящего ответа чата"""
    response: str


# ==================== ФУНКЦИЯ LLM ====================

class LLMError(Exception):
    """Безопасная ошибка провайдера, отдельно от успешного ответа."""
    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


async def call_llm(user_message: str, history: list[HistoryMessage] | None = None) -> str:
    """
    Генерация ответа с использованием Hugging Face Inference API.

    Args:
        user_message: Входящее сообщение пользователя

    Returns:
        Сгенерированный ответ LLM

    Raises:
        ValueError: Для ошибок, отображаемых пользователю (показываются в чате)
    """
    logger.info("Начата генерация ответа")

    headers = {
        "Authorization": f"Bearer {HUGGING_FACE_API_KEY}",
        "Content-Type": "application/json",
    }

    # Формат, совместимый с OpenAI
    payload = {
        "model": MODEL_NAME,
        "messages": [m.model_dump() for m in (history or [])] + [
            {"role": "user", "content": user_message}
        ],
        "max_tokens": 500,
        "temperature": 0.7,
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(API_URL, headers=headers, json=payload)
        if response.status_code != 200:
            status, code, message = {
                401: (502, "provider_auth", "Сервис модели недоступен. Обратитесь к администратору."),
                403: (502, "provider_access", "Сервис модели недоступен. Обратитесь к администратору."),
                429: (429, "rate_limited", "Слишком много запросов. Попробуйте позже."),
                503: (503, "provider_unavailable", "Модель временно недоступна. Попробуйте позже."),
            }.get(response.status_code, (502, "provider_error", "Не удалось получить ответ модели."))
            raise LLMError(status, code, message)
        try:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            if not isinstance(content, str) or not content.strip():
                raise ValueError("Empty content")
        except (ValueError, KeyError, IndexError, TypeError):
            raise LLMError(502, "invalid_response", "Модель вернула некорректный ответ.") from None
        return content.strip()
    except httpx.TimeoutException:
        raise LLMError(504, "provider_timeout", "Время ожидания ответа истекло. Попробуйте снова.") from None
    except httpx.RequestError:
        raise LLMError(502, "provider_connection", "Не удалось связаться с моделью.") from None
    except LLMError:
        raise
    except Exception:
        raise LLMError(502, "provider_error", "Не удалось получить ответ модели.") from None


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
    except LLMError as e:
        raise HTTPException(e.status_code, detail={"code": e.code, "message": e.message}) from None


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Эндпоинт чата — принимает сообщения пользователя и возвращает ответы LLM.
    """
    try:
        llm_response = await call_llm(request.message, request.history)
        return ChatResponse(response=llm_response)

    except LLMError as e:
        raise HTTPException(e.status_code, detail={"code": e.code, "message": e.message}) from None
    except Exception:
        logger.error("Неожиданная ошибка в эндпоинте чата")
        raise HTTPException(500, detail={"code": "internal_error", "message": "Произошла ошибка. Попробуйте снова."}) from None
