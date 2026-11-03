# Проверки

Используйте Python 3.12 и отдельное виртуальное окружение.

```bash
python -m pip install -r requirements-dev.txt
python -m playwright install chromium
HUGGING_FACE_API_KEY=test-only-token python -m pytest -q
```

Тесты API подменяют провайдер: настоящий токен и платные вызовы не нужны.
Тесты интерфейса запускаются в headless Chromium. GitHub Actions выполняет
этот набор на PR и при push в main с правом только на чтение репозитория.
