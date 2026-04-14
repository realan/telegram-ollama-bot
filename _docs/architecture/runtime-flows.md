# Runtime Flows

## 1. Запуск приложения

Сценарий:

1. Процесс стартует через `python -m app.main`
2. Загружаются настройки из окружения
3. Проверяется корректность обязательных env-переменных
4. Проверяется наличие файла system prompt
5. Настраивается логирование
6. Создается Telegram bot и `Dispatcher`
7. Создается `OllamaClient`
8. Создается `ChatService`
9. `ChatService` кладется в `dispatcher` для доступа из handlers
10. Стартует polling

Точка отказа на старте:

- отсутствует `TELEGRAM_BOT_TOKEN`
- отсутствует `OLLAMA_MODEL`
- невалидный `OLLAMA_TIMEOUT_SECONDS`
- отсутствует файл system prompt

## 2. Обработка текстового сообщения

Сценарий:

1. Пользователь отправляет текст
2. `chat_handler` принимает update
3. В лог пишется метадата входящего сообщения
4. Handler вызывает `chat_service.handle_user_message(user_id, text)`
5. `ChatService` делает `strip()` и валидирует непустой текст
6. `ChatService` читает per-user историю из `ConversationStore`
7. При необходимости `ChatService` сначала запускает отдельный summarization call с `app/prompts/summarization_prompt.txt`, где prompt materialize-ится как первый `system` message
8. `ChatService` добавляет новое `user` message, trim-ит runtime history и materialize-ит основной system prompt первым элементом итогового контекста
9. `OllamaClient` приводит внутренний context к provider-facing `messages`
10. Перед LLM request клиент логирует `request_type`, `message_count`, `total_chars` и `estimated_tokens`
11. Если `LOG_MODEL_CONTEXT=true`, клиент логирует полный provider-facing context с базовой redaction типовых секретов
12. `OllamaClient` отправляет полный `messages` context в Ollama через `chat(messages=...)`
13. Если во внутреннем контексте есть роль `summary`, клиент адаптирует ее в совместимый provider-facing message
14. Возвращается строковый ответ модели
15. `ChatService` сохраняет пару `user`/`assistant` в per-user history
16. Handler режет ответ на части через `split_text(...)`
17. Каждая часть отправляется в Telegram отдельным сообщением

Инварианты:

- system prompt всегда идет первым message фактического model context
- reply prompt и summarization prompt разделены
- контекст собирается из per-user history
- observability не должна менять существующий reply flow
- ответ всегда возвращается как plain text
- Telegram limit обрабатывается до отправки

## 3. Обработка неподдерживаемого input

Сценарий:

1. Пользователь отправляет не текст
2. Сообщение не попадает в `F.text`
3. Срабатывает fallback handler
4. Пользователь получает сообщение о том, что MVP поддерживает только текст

## 4. Обработка ошибок Ollama

Сценарий:

1. `OllamaClient` ловит ошибку SDK или транспорта
2. Ошибка конвертируется в typed exception
3. `chat_handler` маппит ее в понятный пользовательский ответ

Основные cases:

- Ollama недоступна
- модель не найдена
- таймаут
- неожиданный формат ответа
- пустой ответ модели

Замечание:

Сейчас user-facing mapping покрывает не все typed exceptions отдельно. Часть сценариев уходит в generic error branch.

## 5. Завершение и очистка

При завершении polling:

1. управление выходит из `start_polling`
2. в `finally` закрывается `bot.session`

Это важно, чтобы не оставлять открытые сетевые ресурсы Telegram-клиента.

## Потенциальные узкие места

### Повторное чтение prompt-файла

Сейчас prompt читается на каждый пользовательский запрос. Для MVP это нормально, но при росте нагрузки можно будет:

- кешировать prompt в памяти
- добавить reload по сигналу или timestamp

### Последовательная отправка длинных ответов

Каждый chunk отправляется отдельным `message.answer(...)`. Это простая и надежная модель, но при очень длинных ответах растет число Telegram API вызовов.

### Один внешний LLM runtime

Вся полезность бота зависит от доступности локального Ollama и наличия модели в окружении.
