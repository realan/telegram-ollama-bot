# CODEX TASK — Telegram Bot + Ollama (MVP)

## 🎯 Цель

Реализовать Telegram-бота на Python, который:

- принимает текстовые сообщения
- отправляет их в локальную LLM через Ollama
- возвращает ответ пользователю

---

## ⚙️ Жесткие ограничения (обязательно)

- Использовать **polling**, НЕ webhook
- Каждое сообщение обрабатывается **независимо**
- **НЕ хранить историю диалога**
- **НЕ использовать БД**
- Только **текстовые сообщения**
- Без RAG, tools, voice, image

---

## 🧱 Стек

- Python 3.11+
- aiogram
- Ollama (локально)
- python-dotenv

---

## 📁 Структура проекта

```
app/
  main.py
  config.py
  logging_config.py

  bot/
    router.py
    handlers/
      start.py
      help.py
      chat.py

  services/
    chat_service.py

  clients/
    ollama_client.py

  utils/
    telegram_text.py
    exceptions.py

  prompts/
    system_prompt.txt

tests/

.env.example
requirements.txt
README.md
```

---

## 🔁 Основной flow

1. Telegram → сообщение
2. handler → ChatService
3. ChatService → OllamaClient
4. Ollama → ответ
5. ответ → Telegram

---

## 🔑 ENV переменные

```
TELEGRAM_BOT_TOKEN=
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
OLLAMA_TIMEOUT_SECONDS=120
APP_LOG_LEVEL=INFO
SYSTEM_PROMPT_PATH=app/prompts/system_prompt.txt
```

---

## 🤖 Ollama client

Реализовать класс:

```
OllamaClient.generate_reply(user_message: str, system_prompt: str | None) -> str
```

Требования:

- использовать модель из env
- учитывать timeout
- обрабатывать ошибки:
  - нет Ollama
  - модель не найдена
  - пустой ответ

- НЕ хранить контекст

---

## 🧠 ChatService

```
handle_user_message(text: str) -> str
```

Должен:

- валидировать вход
- загрузить system prompt
- вызвать OllamaClient
- вернуть строку ответа
- НЕ хранить историю

---

## 🤖 Telegram handlers

### /start

Приветствие

### /help

Список возможностей

### текст

- вызвать ChatService
- вернуть ответ
- обработать ошибки

---

## ✂️ Ограничение Telegram

Реализовать util:

```
split_text(text: str) -> list[str]
```

Требования:

- учитывать лимит Telegram (~4096 символов)
- разбивать аккуратно (по словам)
- сохранять порядок

---

## ❗ Ошибки (user-facing)

- Ollama недоступна
- модель не найдена
- таймаут
- общая ошибка

Сообщения должны быть понятны пользователю.

---

## 🪵 Логирование

Логировать:

- запуск приложения
- старт polling
- ошибки Ollama
- ошибки Telegram

НЕ логировать секреты

---

## 🚀 Запуск

README должен содержать:

1. Установка Ollama
2. `ollama pull <model>`
3. создание `.env`
4. `pip install -r requirements.txt`
5. запуск:

```
python -m app.main
```

---

## 🧪 Минимальные тесты

- config загружается
- split_text работает
- ChatService обрабатывает ошибки

---

## ✅ Acceptance criteria

- бот запускается
- /start работает
- /help работает
- сообщение → ответ от Ollama
- каждое сообщение независимое
- нет хранения истории
- длинные ответы корректно отправляются

---

## 🚫 НЕ ДЕЛАТЬ

- webhook
- БД
- Redis
- Docker
- streaming
- RAG
- memory
- голос / изображения

---

## 📦 Ожидаемый результат

Codex должен выдать:

- полный рабочий код проекта
- requirements.txt
- .env.example
- README.md
- базовые тесты

---

## 🧭 Принцип реализации

Сначала сделать **простой рабочий MVP**,
без усложнений и лишней архитектуры.

Главное — чтобы работало стабильно и понятно.
