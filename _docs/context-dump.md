# Context Dump

Last updated after: `phase-7-tests`
Current status: `mvp-with-regression-tests`
Roadmap status source: [_docs/roadmap.yaml](/Users/user/projects/hw1/_docs/roadmap.yaml)

## Project Summary

Это учебный проект: MVP Telegram-бота на Python, который принимает текстовые сообщения, отправляет каждое сообщение в локальную LLM через Ollama и возвращает пользователю ответ.

Базовые ограничения текущей версии:

- бот работает через `polling`
- история хранится только в памяти процесса
- база данных не используется
- поддерживаются только текстовые сообщения

Проект соответствует исходной задаче из [CODEX_TASK.md](/Users/user/projects/hw1/CODEX_TASK.md) и [task.yaml](/Users/user/projects/hw1/task.yaml): простой бот без RAG, tools, voice, image и других расширений.

## Current State

Сейчас в проекте уже есть:

- `/start` с кратким описанием поведения бота
- `/help` со справкой и ограничениями
- обработка текстовых сообщений
- user-facing обработка ошибок Ollama
- разбиение длинных ответов по лимиту Telegram
- загрузка system prompt из файла и включение его в model context
- per-user in-memory history
- логирование model context, типа вызова и size metrics перед каждым LLM request
- детерминированные regression-тесты на memory, trimming, summary, system prompt и logging без реального Ollama

Текущий стек:

- Python 3.11+
- `aiogram` 3.x
- `ollama` Python SDK
- `python-dotenv`
- `pytest`
- `pytest-asyncio`

Архитектурно это небольшой модульный монолит с разделением на:

1. Telegram layer
2. Service layer
3. Client layer
4. Utility layer

## Implemented Phases

- `mvp-baseline` — done
  Результат: реализован минимальный Telegram-бот без памяти, БД и дополнительных режимов работы.
- `phase-1-design` — done
  Результат: зафиксированы messages context contract, memory abstraction и context policy для следующих фаз.
- `phase-2-memory` — done
  Результат: добавлена per-user in-memory история в формате `messages` с сохранением `user` и `assistant` сообщений.
- `phase-3-context-limits` — done
  Результат: добавлены конфигурируемые лимиты истории и trimming старых сообщений перед вызовом модели.
- `phase-4-summarization` — done
  Результат: добавлен workflow сжатия старого префикса истории в одно `summary`-сообщение.
- `phase-5-system-prompt` — done
  Результат: system prompt стал явной частью model context, а клиент переведен на полный messages contract.
- `phase-6-observability` — done
  Результат: перед LLM-вызовом логируются provider-facing context, тип вызова и size metrics.
- `phase-7-tests` — done
  Результат: добавлены детерминированные regression-тесты для memory, trimming, summary, system prompt и observability-логов.

## Architecture Snapshot

Ключевые текущие решения:

- логика Telegram вынесена в `app/bot/handlers/*`
- orchestration пользовательского запроса сосредоточен в `app/services/chat_service.py`
- интеграция с Ollama изолирована в `app/clients/ollama_client.py`
- per-user history вынесена в `app/memory/`
- конфигурация загружается централизованно через `app/config.py`
- system prompt хранится во внешнем файле `app/prompts/system_prompt.txt`
- summarization prompt хранится отдельно в `app/prompts/summarization_prompt.txt`
- длинные ответы режутся через `app/utils/telegram_text.py`
- runtime history trim-ится в `ChatService` перед отправкой в модель
- при переполнении старой истории `ChatService` обновляет store через `replace_after_summary(...)`
- итоговый вызов модели собирается как ordered `messages` context, где `system` message идет первым
- provider-facing вызов в Ollama выполняется через chat API, а внутренняя роль `summary` materialize-ится в совместимый message
- перед каждым provider-facing LLM call пишется observability log с `request_type`, `message_count`, `total_chars` и `estimated_tokens`
- полный context log можно отключить через `LOG_MODEL_CONTEXT=false`

Зафиксированные проектные решения после `phase-1-design`:

- внутренний runtime context должен собираться как ordered `messages` array с полями `role` и `content`
- допустимые внутренние роли: `system`, `user`, `assistant`, `summary`
- `system prompt` не должен храниться в per-user history и должен материализоваться первым элементом фактического context модели
- `summary` должен жить в той же истории, что и обычные сообщения, но как отдельная внутренняя роль
- для хранения истории выбран abstraction `ConversationStore` с сегрегацией по `user_id`
- базовая context policy: primary limit по числу сообщений, secondary limit по суммарной длине текста

Важные модули:

- `app/main.py`
- `app/config.py`
- `app/bot/router.py`
- `app/bot/handlers/chat.py`
- `app/services/chat_service.py`
- `app/clients/ollama_client.py`
- `app/utils/exceptions.py`
- `app/utils/telegram_text.py`

Связанные архитектурные документы:

- [_docs/architecture/system-overview.md](/Users/user/projects/hw1/_docs/architecture/system-overview.md)
- [_docs/architecture/components.md](/Users/user/projects/hw1/_docs/architecture/components.md)
- [_docs/architecture/runtime-flows.md](/Users/user/projects/hw1/_docs/architecture/runtime-flows.md)
- [_docs/architecture/evolution-guidelines.md](/Users/user/projects/hw1/_docs/architecture/evolution-guidelines.md)

## Current Behavior

Сейчас система работает так:

1. Пользователь отправляет текст в Telegram.
2. `aiogram` получает update через polling.
3. `app/bot/handlers/chat.py` принимает сообщение.
4. Handler вызывает `ChatService.handle_user_message(user_id, text)`.
5. `ChatService` валидирует текст и читает per-user историю из `ConversationStore`.
6. Если накопленная history превышает `SUMMARY_TRIGGER_MESSAGES`, `ChatService` выделяет старый префикс и отправляет его в отдельный LLM-call с summarization prompt.
7. Полученное summary нормализуется, ограничивается по длине и заменяет старую часть истории в store.
8. `ChatService` добавляет новый `user` message в runtime context и trim-ит оставшийся контекст по обычным лимитам.
9. `ChatService` читает основной system prompt из файла и добавляет его первым элементом фактического model context.
10. `OllamaClient.generate_reply(...)` логирует тип вызова, размер контекста и при включенном флаге полный provider-facing `messages` context.
11. `OllamaClient.generate_reply(...)` отправляет полный `messages` context в локальный Ollama через chat API.
12. Если в message content встречаются типовые секреты, они редактируются в context log.
13. После успешного ответа `ChatService` сохраняет пару `user`/`assistant` в per-user history.
14. Ответ модели при необходимости режется на части через `split_text(...)`.
15. Бот отправляет ответ пользователю.

Для нетекстовых сообщений есть fallback-обработчик: бот сообщает, что в MVP поддерживается только текст.

## Configuration

Обязательные env:

- `TELEGRAM_BOT_TOKEN`
- `OLLAMA_MODEL`

Необязательные env с дефолтами:

- `OLLAMA_BASE_URL=http://localhost:11434`
- `OLLAMA_TIMEOUT_SECONDS=120`
- `APP_LOG_LEVEL=INFO`
- `SYSTEM_PROMPT_PATH=app/prompts/system_prompt.txt`
- `SUMMARIZATION_PROMPT_PATH=app/prompts/summarization_prompt.txt`
- `MAX_HISTORY_MESSAGES=10`
- `MAX_CONTEXT_CHARS=4000`
- `SUMMARY_TRIGGER_MESSAGES=5`
- `SUMMARY_MAX_CHARS=800`
- `LOG_MODEL_CONTEXT=true`

В [app/config.py](/Users/user/projects/hw1/app/config.py) уже есть валидация обязательных параметров, таймаута, существования файлов prompt, лимитов контекста и порога summary.

## Context Limits

Фактически реализованная trimming policy:

- primary limit: `MAX_HISTORY_MESSAGES`, по умолчанию `10`
- secondary safeguard: `MAX_CONTEXT_CHARS`, по умолчанию `4000`
- trimming применяется к runtime history перед вызовом модели, но с учетом длины основного system prompt в фактическом reply context
- самые старые сообщения удаляются первыми
- новый `user` message всегда остается в контексте
- если в истории уже есть `summary`, он удерживается раньше свежего хвоста и удаляется только после исчерпания обычных старых сообщений
- порядок оставшихся сообщений всегда сохраняется
- storage backend и сохраненный per-user history после phase-4 меняются только через controlled summary replacement

## Summary Behavior

Фактически реализованная summary policy:

- trigger: `SUMMARY_TRIGGER_MESSAGES`, по умолчанию `5`
- старый префикс истории выделяется отдельно от свежего хвоста и отправляется в модель с отдельным summarization prompt, тоже как явный первый `system` message
- результат сохраняется как одно сообщение с ролью `summary`
- в store поддерживается один актуальный summary-сегмент в начале истории
- свежий хвост истории сохраняется без сжатия и имеет приоритет над summary
- повторная суммаризация разрешена только после того, как после текущего summary снова накопится достаточный объём обычных сообщений
- длина summary ограничивается `SUMMARY_MAX_CHARS`, по умолчанию `800`

## Known Limitations

- память in-memory не переживает рестарт процесса
- нет точного tokenizer-based подсчета токенов
- нет БД и персистентного storage
- нет стриминга ответа
- `pytest` не установлен в текущем локальном окружении, поэтому полный прогон набора в этой среде не подтвержден
- summary может терять нюансы старых сообщений, потому что качество сжатия полностью зависит от модели
- summarization вызывается inline перед обычным ответом и увеличивает latency при длинной истории
- token count сейчас оценочный, а не точный tokenizer-based
- полное логирование контекста остается чувствительным для production, даже с базовой redaction типовых секретов

## Test Coverage Snapshot

Фактически покрыто автотестами:

- изоляция per-user history и сохранение user/assistant сообщений
- trimming по количеству сообщений и по суммарной длине контекста
- сохранение порядка сообщений и инварианта нового user message
- summary workflow: trigger, замена старого префикса summary-сообщением, повторное использование существующего summary и ограничение длины summary
- включение system prompt первым элементом runtime context и разделение reply/summarization prompt
- observability в `OllamaClient`: `request_type`, `message_count`, `total_chars`, `estimated_tokens`, full context logging, redaction секретов и отключение полного context log

Покрытие остается детерминированным:

- используются stub/fake-клиенты и in-memory store
- тесты не зависят от Telegram API и реального Ollama runtime

## Open Risks / Technical Debt

- В постановке и `task.yaml` упоминается `.env.example`, но в репозитории такого файла нет.
- `README.md` сейчас больше похож на рабочие заметки, чем на полноценный пользовательский README.
- Текущая in-memory память не переживает рестарт процесса.
- Логирование контекста уже включает пользовательские сообщения и требует осторожности в production.
- Redaction в логах намеренно базовая и не гарантирует удаление всех возможных секретов из свободного текста.

## Next Relevant Phase

Следующая фаза в roadmap пока не зафиксирована.

Ближайший практический шаг:

- обеспечить среду с установленным `pytest` и прогнать полный regression-набор
