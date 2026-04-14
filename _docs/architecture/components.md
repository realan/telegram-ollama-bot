# Components

## Карта модулей

### `app/main.py`

Роль:

- точка входа приложения
- загрузка настроек
- настройка логирования
- создание `Bot`, `Dispatcher`, `OllamaClient`, `ChatService`
- запуск polling

Зависимости:

- `app.config`
- `app.logging_config`
- `app.bot.router`
- `app.clients.ollama_client`
- `app.services.chat_service`

### `app/config.py`

Роль:

- чтение `.env`
- сборка `Settings`
- валидация обязательных параметров
- валидация пути к system prompt

Зависимости:

- `python-dotenv`
- `app.utils.exceptions`

### `app/logging_config.py`

Роль:

- настройка стандартного `logging`
- выбор уровня логирования
- вывод логов в `stdout`

### `app/bot/router.py`

Роль:

- сборка root router
- подключение feature-handlers

### `app/bot/handlers/start.py`

Роль:

- обработка `/start`
- возврат короткого описания назначения бота

### `app/bot/handlers/help.py`

Роль:

- обработка `/help`
- возврат списка возможностей и ограничений

### `app/bot/handlers/chat.py`

Роль:

- обработка обычных текстовых сообщений
- вызов `ChatService`
- маппинг прикладных ошибок в user-facing тексты
- отправка длинного ответа частями
- fallback для unsupported input

Особенность:

- это boundary между Telegram transport и внутренней логикой приложения

### `app/services/chat_service.py`

Роль:

- нормализация и валидация входного текста
- загрузка system и summarization prompt
- сборка фактического `messages` context
- orchestration запроса в `OllamaClient`

Принцип:

- сервис не зависит от Telegram API

### `app/clients/ollama_client.py`

Роль:

- работа с Ollama SDK
- формирование вызова `chat(messages=...)`
- materialization внутренней роли `summary` в совместимый provider-facing message
- логирование provider-facing context, типа вызова и size metrics перед LLM request
- преобразование ошибок транспорта и ответа в typed exceptions

Принцип:

- клиент изолирует инфраструктурные детали интеграции с моделью

### `app/utils/telegram_text.py`

Роль:

- разбиение длинного текста на сообщения с учетом лимита Telegram

### `app/utils/exceptions.py`

Роль:

- единый набор исключений приложения
- стабильный контракт между слоями

### `app/prompts/system_prompt.txt`

Роль:

- внешний текстовый prompt, влияющий на стиль и формат ответа модели

### `app/prompts/summarization_prompt.txt`

Роль:

- отдельный внешний prompt для summarization workflow

## Зависимости между модулями

Упрощенно зависимость выглядит так:

```text
Telegram Update
  -> handlers
  -> ChatService
  -> OllamaClient
  -> Ollama
  -> handlers
  -> Telegram response
```

Более формально:

```text
main
  -> config
  -> logging_config
  -> router
  -> ChatService
  -> OllamaClient

router
  -> handlers/*

handlers/chat
  -> ChatService
  -> telegram_text
  -> exceptions

ChatService
  -> OllamaClient

OllamaClient
  -> exceptions
  -> ollama SDK
  -> httpx
```

## Правила зависимостей

- `handlers` не должны напрямую обращаться к Ollama SDK
- `services` не должны зависеть от `aiogram`
- `clients` не должны знать про Telegram message objects
- `utils` не должны зависеть от feature-модулей
- конфиг читается централизованно, а не по месту использования

## Что вероятно появится дальше

При росте проекта сюда логично добавить:

- `app/domain/` для доменных сущностей и правил, если появится память, профили или сценарии
- `app/repositories/` при появлении БД
- `app/integrations/` или дополнительные `clients/` для внешних сервисов
- `app/observability/` для метрик, healthcheck и tracing

## Зафиксированные расширения после `phase-1-design`

В рамках проектной фазы зафиксированы ближайшие изменения модульной карты.

### `app/memory/`

Целевая роль:

- новый пакет для `ConversationStore`
- хранение истории по `user_id`
- in-memory реализация как первый шаг

Ограничения:

- пакет не должен зависеть от `aiogram`
- пакет не должен заниматься trimming policy или формированием prompt

### `app/services/chat_service.py`

Целевая эволюция:

- собирать внутренний `messages context`
- материализовать `system` message первым элементом фактического context
- читать историю через `ConversationStore`
- применять context policy перед вызовом model client

Ограничения:

- сервис по-прежнему не должен знать детали Telegram API
- сервис не должен хранить историю в собственных ad-hoc структурах

### `app/clients/ollama_client.py`

Целевая эволюция:

- принимать provider-facing messages context вместо одиночного `prompt`
- вызывать Ollama через chat API
- выполнять materialization внутренней роли `summary` для
  совместимости с внешним API

### `app/config.py`

Целевая эволюция:

- хранить настройки `max_history_messages`
- хранить настройки `max_context_chars`
- хранить порог активации summary
- хранить feature-flag для full context logging

### `app/prompts/`

Целевая эволюция:

- сохранить основной system prompt
- добавить отдельный prompt для summarization workflow
- не смешивать reply prompt и summarization prompt в одном контракте
